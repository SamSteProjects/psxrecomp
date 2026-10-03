"""Reviewed source-record transforms, never evaluated world-map resting state."""
from copy import deepcopy
from hashlib import sha256
import re
import struct

from .project import ProjectError, digest
from .worldmap_authoring import state_key

COMPONENT = 'WorldMapPlacements'
SCENES = ('map01', 'map02', 'map03')
FIELDS = ('offset.x', 'offset.y', 'offset.z', 'yaw_units')

def owner(scene):
    if scene not in SCENES:
        raise ProjectError('Choose a qualified walk kingdom')
    return f'worldmap://{scene}/placements'

def values(value):
    if (not isinstance(value, dict) or set(value) != {'offset', 'yaw_units'} or
            not isinstance(value['offset'], dict) or set(value['offset']) != {'x','y','z'} or
            any(type(n) is not int or not -32768 <= n <= 32767 for n in value['offset'].values()) or
            type(value['yaw_units']) is not int or not 0 <= value['yaw_units'] < 4096):
        raise ProjectError('World source transform requires signed16 offsets and yaw0..4095')
    return deepcopy(value)

def validate(project, identifier, binding):
    scene = next((s for s in SCENES if identifier == owner(s)), None)
    if (scene is None or not isinstance(binding, dict) or set(binding) != {
            'scene','source_disc_sha256','source_map_sha256','source_floor_lut_sha256','entries'} or
            binding['scene'] != scene or any(not isinstance(binding[k], str) or not re.fullmatch('[0-9a-f]{64}', binding[k])
            for k in ('source_disc_sha256','source_map_sha256','source_floor_lut_sha256')) or
            not isinstance(binding['entries'], dict) or not 1 <= len(binding['entries']) <= 512):
        raise ProjectError('World source placement binding lacks bounded immutable source identity')
    if {doc['source']['disc_identity'] for doc in project.imports.values()} != {'sha256:'+binding['source_disc_sha256']}:
        raise ProjectError('World source placement belongs to another imported disc')
    for key, entry in binding['entries'].items():
        if (not isinstance(key, str) or not re.fullmatch(r'[0-9]{4}', key) or int(key) >= 512 or
                not isinstance(entry, dict) or set(entry) != {'values','source_record_sha256','shared_record'} or
                type(entry['shared_record']) is not bool or not isinstance(entry['source_record_sha256'], str) or
                not re.fullmatch('[0-9a-f]{64}', entry['source_record_sha256'])):
            raise ProjectError('World placement requires original bounded record identity and shared scope')
        values(entry['values'])
    return deepcopy(binding)

def source(project, scene):
    owner(scene)
    if not project.disc_path or not project.imports:
        raise ProjectError('World placements require the imported user-owned disc')
    from importer.pipeline import _disc_context, _bounded_scene_range
    from importer.worldmap_geometry import KINGDOM_BASES, _kingdom_table, _slot
    from importer.worldmap_placements import decode_worldmap_placements
    with _disc_context(project.disc_path) as (_, disc_hash, mapping, archive):
        if {doc['source']['disc_identity'] for doc in project.imports.values()} != {'sha256:'+disc_hash}:
            raise ProjectError('World placement source differs from the imported retail identity')
        start,end = _bounded_scene_range(archive,mapping,scene)
        base=KINGDOM_BASES[scene]
        if start != base-2 or not start <= base < base+1 < end:
            raise ProjectError('World placement carrier differs from the qualified kingdom range')
        entry=archive.entry(base-2)
        raw=archive.read_entry(entry,extended=True)
        if len(raw) != 0x12000 or entry.size_sectors*2048 != len(raw):
            raise ProjectError('World source placement MAP must retain its complete source footprint')
        _,_,_,table,carrier=_kingdom_table(archive,base)
        man,_=_slot(table,carrier,2)
        floor=list(struct.unpack_from('<16h',man,2))
        decoded=decode_worldmap_placements(raw,floor,scene=scene)
        provenance=dict(scene=scene,source_disc_sha256=disc_hash,source_map_sha256=sha256(raw).hexdigest(),
            source_floor_lut_sha256=sha256(man[2:34]).hexdigest())
        offset=archive.node.extent_lba*2048+entry.start_lba*2048
    records={}
    for seed in decoded['placements']:
        index=seed['object_record_index'];key=f'{index:04d}';at=index*32
        if key not in records:
            x,y,z=struct.unpack_from('<3h',raw,at);yaw=struct.unpack_from('<H',raw,at+10)[0]&4095
            refs=[i for i in range(16384) if struct.unpack_from('<H',raw,0x8000+i*2)[0]&511 == index]
            qualified=[s for s in decoded['placements'] if s['object_record_index']==index]
            writable=len(refs)==len(qualified)
            records[key]=dict(record_id=key,object_record_index=index,source_record_sha256=sha256(raw[at:at+32]).hexdigest(),
                retail_values=dict(offset=dict(x=x,y=y,z=z),yaw_units=yaw),source_cell_count=len(refs),
                placements=deepcopy(qualified),writable=writable,
                reason=None if writable else 'Record also serves unresolved or excluded source cells; transform authoring is unavailable')
    return raw,provenance,records,offset,floor

def patch(raw, records, entries, *, scene, floor):
    from importer.worldmap_placements import decode_worldmap_placements
    result=bytearray(raw);edits=[]
    for key,entry in sorted(entries.items()):
        row=records.get(key)
        if row is None or not row['writable'] or row['source_record_sha256'] != entry['source_record_sha256']:
            raise ProjectError('World placement record is unavailable or its immutable owner changed')
        if row['source_cell_count']>1 and not entry['shared_record']:
            raise ProjectError('Shared world placement record requires explicit shared-record scope')
        value=values(entry['values']);at=row['object_record_index']*32
        struct.pack_into('<3h',result,at,*(value['offset'][axis] for axis in ('x','y','z')))
        old=struct.unpack_from('<H',raw,at+10)[0]
        struct.pack_into('<H',result,at+10,(old&0xf000)|value['yaw_units'])
        for field in FIELDS:
            before=_field(row['retail_values'],field);after=_field(value,field)
            if before!=after:
                edits.append(dict(scene=scene,semantic_id=f'{owner(scene)}/records/{key}',field='world_placement.'+field,
                    before_value=before,after_value=after,scope='worldmap-source-record-transform-only',
                    affected_source_entities=[s['entity_id'] for s in row['placements']],record_index=int(key)))
    reopened=decode_worldmap_placements(bytes(result),floor,scene=scene)
    if {p['entity_id'] for p in reopened['placements']} != {p['entity_id'] for row in records.values() for p in row['placements']}:
        raise ProjectError('World placement transform changed source selection or placement coverage')
    allowed={int(key)*32+n for key in entries for n in (0,1,2,3,4,5,10,11)}
    if len(result)!=len(raw) or any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(raw,result))):
        raise ProjectError('World placement serializer altered unrelated source bytes')
    return bytes(result),edits,reopened['placements']

def _field(value, field):
    for part in field.split('.'):
        value=value[part]
    return value

def context(project,scene):
    raw,provenance,records,offset,floor=source(project,scene)
    components=project.overrides.get(owner(scene),{})
    if components and set(components)!={COMPONENT}:
        raise ProjectError('World placement owner accepts only its dedicated transform component')
    binding=components.get(COMPONENT)
    if binding:
        validate(project,owner(scene),binding)
        if any(binding[k]!=provenance[k] for k in provenance):
            raise ProjectError('World placement source changed; restore the bound disc before building')
    entries=deepcopy((binding or {}).get('entries',{}))
    current,_,placements=patch(raw,records,entries,scene=scene,floor=floor)
    for key,row in records.items():
        row['authored_values']=deepcopy(entries.get(key,{}).get('values'))
        row['current_values']=deepcopy(row['authored_values'] or row['retail_values'])
    return raw,provenance,records,offset,floor,binding,current,placements

def snapshot(project,scene,expected_key):
    if project.mode!='edit' or expected_key!=state_key(project):
        raise ProjectError('World placement source inputs changed or Edit mode is unavailable')
    _,provenance,records,_,_,_,current,placements=context(project,scene)
    if expected_key!=state_key(project):
        raise ProjectError('World placement inputs changed during source preparation')
    return dict(schema_version='legaia.worldmap-placement-authoring.v1',scene=scene,source_key=expected_key,
        source_record=provenance,current_map_sha256=sha256(current).hexdigest(),records=list(records.values()),
        current_placements=placements,gameplay_verified=False,project_changed=False,
        limitations=['Transforms are source spawn seeds; scripts may move or hide them.',
            'Shared object records affect every bound source cell. Cell ownership, anchors and model selectors stay unchanged.',
            'Native visibility, collision, script binding and resting positions require gameplay verification.'])

def review(project,scene,expected_key,record_id,value,shared_record):
    if type(shared_record) is not bool:
        raise ProjectError('Shared-record choice must be explicit')
    report=snapshot(project,scene,expected_key)
    raw,provenance,records,_,floor,binding,current,_=context(project,scene)
    if record_id not in records or not records[record_id]['writable']:
        raise ProjectError('Select a writable qualified source record')
    row=records[record_id]
    proposed=values(value) if value is not None else row['retail_values']
    entries=deepcopy((binding or {}).get('entries',{}))
    if proposed==row['retail_values']:entries.pop(record_id,None)
    else:entries[record_id]=dict(values=proposed,source_record_sha256=row['source_record_sha256'],shared_record=shared_record)
    candidate,_,placements=patch(raw,records,entries,scene=scene,floor=floor)
    after=dict(provenance,entries=entries) if entries else None
    proof=dict(source_key=expected_key,record_id=record_id,values=value,shared_record=shared_record,
        current_map_sha256=sha256(current).hexdigest(),candidate_map_sha256=sha256(candidate).hexdigest(),component=after)
    if state_key(project)!=expected_key or project.mode!='edit':
        raise ProjectError('World placement inputs changed during review')
    changes=[dict(byte_offset=i,before_byte=a,after_byte=b) for i,(a,b) in enumerate(zip(current,candidate)) if a!=b]
    report['review']=dict(review_key=digest(proof),record_id=record_id,values=deepcopy(value),shared_record=shared_record,
        no_op=binding==after,proposed_values=deepcopy(proposed),candidate_map_sha256=sha256(candidate).hexdigest(),
        changed_bytes=changes,affected_source_entities=[s['entity_id'] for s in row['placements']],
        proposed_placements=[p for p in placements if p['object_record_index']==int(record_id)])
    return report,after

def apply(project,command):
    if set(command)!={'type','scene','source_key','record_id','values','shared_record','review_key'}:
        raise ProjectError('World placement Apply accepts only reviewed source record, values and scope')
    report,binding=review(project,command['scene'],command['source_key'],command['record_id'],command['values'],command['shared_record'])
    if command['review_key']!=report['review']['review_key'] or report['review']['no_op']:
        raise ProjectError('World placement review is stale or makes no authored change')
    identifier=owner(command['scene']);before=deepcopy(project.overrides.get(identifier))
    after={COMPONENT:binding} if binding else None
    if after:project.overrides[identifier]=after
    else:project.overrides.pop(identifier,None)
    project.undo_stack.append(dict(entity_id=identifier,before=before,after=deepcopy(after)))
    project.redo_stack.clear()

def build(project,overlays):
    changes=[]
    for scene in SCENES:
        if COMPONENT not in project.overrides.get(owner(scene),{}):continue
        raw,_,records,offset,floor,binding,_,_=context(project,scene)
        candidate,edits,_=patch(raw,records,binding['entries'],scene=scene,floor=floor)
        changes.extend(edits)
        if candidate==raw:continue
        matching=[o for o in overlays if o['offset']==offset and o['size']==len(raw)]
        if len(matching)>1:raise ProjectError('World placement MAP has ambiguous authored overlay ownership')
        if matching:
            target=matching[0]
            if target['expected_sha256']!=sha256(raw).hexdigest():raise ProjectError('World placement MAP overlay has different source identity')
            merged=bytearray(target['payload'])
            for i,(old,new) in enumerate(zip(raw,candidate)):
                if old==new:continue
                if merged[i] not in (old,new):raise ProjectError('World placement transform conflicts with another authored MAP field')
                merged[i]=new
            target.update(payload=bytes(merged),sha256=sha256(merged).hexdigest())
        else:
            overlays.append(dict(scene=scene,offset=offset,size=len(raw),payload=candidate,file=f'assets/{scene}-world-placements.map',
                expected_sha256=sha256(raw).hexdigest(),sha256=sha256(candidate).hexdigest()))
    return changes
