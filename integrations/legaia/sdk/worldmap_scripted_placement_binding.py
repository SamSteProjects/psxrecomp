"""Bounded retained scripted-placement replay and Current ownership merge.

The caller qualifies and retains the base MAP; no files or project state are
written here. This is not yet a registered project component or Build route.
"""
from copy import deepcopy
from hashlib import sha256
import re

from importer.worldmap_object_bind_allocation import _tables
from importer.worldmap_scripted_placement_allocation import allocate_scripted_placements
from importer.worldmap_placements import decode_worldmap_placements
from .project import ProjectError

COMPONENT='WorldMapScriptedPlacementAllocations'
SCHEMA='legaia.worldmap-scripted-placement-ledger.v1'
HASH=re.compile('[0-9a-f]{64}')
PROVENANCE={'scene','source_disc_sha256','source_map_sha256','source_floor_lut_sha256','source_man_sha256','fallback_sha256'}


def owner(scene):
    if scene not in ('map01','map02','map03'):raise ProjectError('Scripted placement owner requires a supported kingdom')
    return f'worldmap://{scene}/scripted-placement-allocations'


def base_path(project,binding):
    digest=binding.get('base_map_sha256')
    if not isinstance(digest,str) or not HASH.fullmatch(digest):
        raise ProjectError('Scripted placement retained base has no valid content identity')
    path=project.root/'Authored'/'WorldMapBases'/(digest+'.map')
    if not path.resolve().is_relative_to(project.root.resolve()):
        raise ProjectError('Scripted placement retained base escapes the project')
    return path


def read_base(project,binding):
    path=base_path(project,binding)
    try:
        if not path.is_file() or path.stat().st_size!=0x12000:
            raise ProjectError('Scripted placement retained base is missing or has an invalid size')
        data=path.read_bytes()
    except OSError as error:
        raise ProjectError('Scripted placement retained base cannot be read') from error
    if len(data)!=0x12000 or sha256(data).hexdigest()!=binding['base_map_sha256']:
        raise ProjectError('Scripted placement retained base changed')
    return data


def compose(project,scene,provenance,normal,fallback,original_man,current_man,floor):
    components=project.overrides.get(owner(scene),{})
    if components and set(components)!={COMPONENT}:
        raise ProjectError('Scripted placement owner accepts only its dedicated component')
    binding=components.get(COMPONENT)
    if binding is None:return normal,[]
    validate(project,owner(scene),binding)
    expected=dict(provenance,source_man_sha256=sha256(original_man).hexdigest(),fallback_sha256=sha256(fallback).hexdigest())
    if any(binding[k]!=v for k,v in expected.items()):
        raise ProjectError('Scripted placement immutable source changed')
    base=read_base(project,binding)
    allocated,audits=replay(base,fallback,current_man,floor,binding)
    merged=merge_current(base,allocated,normal,floor,scene,audits)
    return merged,[deepcopy(a) for audit in audits for a in audit['allocations']]


def validate(project,identifier,binding):
    if not isinstance(binding,dict) or set(binding)!=PROVENANCE|{'schema_version','base_map_sha256','operations'} or binding['schema_version']!=SCHEMA:
        raise ProjectError('Scripted placement ledger requires exact source and retained-base identity')
    if identifier!=owner(binding['scene']) or any(not isinstance(binding[k],str) or not HASH.fullmatch(binding[k]) for k in (PROVENANCE-{'scene'})|{'base_map_sha256'}):
        raise ProjectError('Scripted placement ledger source identity is malformed')
    if {d['source']['disc_identity'] for d in project.imports.values()}!={'sha256:'+binding['source_disc_sha256']}:
        raise ProjectError('Scripted placement ledger belongs to another imported disc')
    operations=binding['operations']
    if not isinstance(operations,list) or not 1<=len(operations)<=32:
        raise ProjectError('Scripted placement ledger requires bounded ordered operations')
    ids=set();records=set();total=0
    for operation in operations:
        if not isinstance(operation,dict) or set(operation)!={'requests','relocation_offset','proposed_map_sha256'} or not isinstance(operation['proposed_map_sha256'],str) or not HASH.fullmatch(operation['proposed_map_sha256']):
            raise ProjectError('Scripted placement operation lacks exact native replay identity')
        at=operation['relocation_offset']
        if type(at) is not int or not 0x12<=at<0x2000 or at%2:
            raise ProjectError('Scripted placement operation has an invalid relocation offset')
        requests=operation['requests']
        if not isinstance(requests,list) or not 1<=len(requests)<=32:
            raise ProjectError('Scripted placement operation has invalid request capacity')
        total+=len(requests)
        for request in requests:
            if not isinstance(request,dict) or set(request)!={'placement_id','donor_cell','target_cell','record_index','values','shared_script'} or request['shared_script'] is not True:
                raise ProjectError('Scripted placement operation requires exact requests and shared-script scope')
            identifier=request['placement_id'];record=request['record_index']
            if not isinstance(identifier,str) or not re.fullmatch(r'placement://authored/[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}',identifier) or identifier in ids or type(record) is not int or not 4<=record<512 or record in records:
                raise ProjectError('Scripted placement ledger repeats or loses native authored identity')
            if any(type(request[k]) is not int or not 0<=request[k]<16384 for k in ('donor_cell','target_cell')):
                raise ProjectError('Scripted placement ledger cell ownership is invalid')
            from .worldmap_placements import values
            values(request['values']);ids.add(identifier);records.add(record)
    if total>32:raise ProjectError('Scripted placement ledger exceeds its total creation budget')
    return deepcopy(binding)


def replay(base,fallback,man,floor,binding):
    if not isinstance(base,bytes) or len(base)!=0x12000 or sha256(base).hexdigest()!=binding['base_map_sha256']:
        raise ProjectError('Scripted placement retained base MAP changed')
    if sha256(fallback).hexdigest()!=binding['fallback_sha256']:
        raise ProjectError('Scripted placement fallback source changed')
    current=base;audits=[]
    for operation in binding['operations']:
        current,audit=allocate_scripted_placements(current,fallback,man,floor,binding['scene'],operation['requests'],relocation_offset=operation['relocation_offset'])
        if sha256(current).hexdigest()!=operation['proposed_map_sha256']:
            raise ProjectError('Scripted placement operation differs from complete retained replay')
        audits.append(audit)
    return current,audits


def merge_current(base,allocated,current,floor,scene,audits):
    if any(not isinstance(data,bytes) or len(data)!=0x12000 for data in (base,allocated,current)):
        raise ProjectError('Scripted placement merge requires complete native MAPs')
    before_tables,_=_tables(base[0x10000:]);current_tables,_=_tables(current[0x10000:])
    if before_tables[1]!=current_tables[1]:
        raise ProjectError('Current bind table changed after scripted placement retention; review its ownership again')
    owned=set();new_cells=set()
    for audit in audits:
        for allocation in audit['allocations']:
            owned.update(range(allocation['record_index']*32,allocation['record_index']*32+32))
            for cell in (allocation['target_cell'],allocation['anchor_cell']):owned.update((0x8000+cell*2,0x8001+cell*2))
            new_cells.add(allocation['target_cell'])
        binds=audit['bind_allocation'];at=0x10000+binds['proposed_table_offset']
        owned.update(range(at,at+4*binds['proposed_row_count']));owned.update(range(0x10006,0x1000a))
    merged=bytearray(allocated)
    for i,(old,new) in enumerate(zip(base,current)):
        if old==new:continue
        if i in owned and new!=allocated[i]:
            raise ProjectError('Current MAP edit conflicts with retained scripted placement ownership')
        merged[i]=new
    result=bytes(merged);_tables(result[0x10000:])
    before=decode_worldmap_placements(current,floor,scene=scene);after=decode_worldmap_placements(result,floor,scene=scene)
    original={p['source_cell']:p for p in before['placements']};proposed={p['source_cell']:p for p in after['placements']}
    if set(proposed)!=set(original)|new_cells or any(proposed[c]!=p for c,p in original.items()) or after['unresolved']!=before['unresolved'] or after['coverage']['excluded']!=before['coverage']['excluded']:
        raise ProjectError('Scripted placement merge changed Current source coverage')
    if any(proposed[c]['source_layer']!='placed' or proposed[c]['source_bind_owner']!='init_bind' for c in new_cells):
        raise ProjectError('Scripted placement merge lost its native init ownership')
    return result
