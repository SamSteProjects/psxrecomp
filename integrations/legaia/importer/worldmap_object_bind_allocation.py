"""Append donor-derived primary kind-1 binds without relocating source tables.

Pinned field_objects.rs / field_env.rs: init-managed placed objects resolve
their anchor through kind-1 lookup and a flat MAN partition-0 header. This
writer changes no placement, MAN record, gate meaning or runtime state.
"""
from hashlib import sha256
import re
import struct

from .core import ImportError
from .field_map import _table_rows
from .worldmap_object_binds import resolve_object_bind


def _tables(block):
    tables={};occupied=[]
    for kind in range(4):
        stride=8 if kind==3 else 4;offset,rows=_table_rows(block,kind,stride)
        end=offset+len(rows)*stride
        if rows and any(offset<hi and lo<end for lo,hi in occupied):
            raise ImportError('Object bind allocation source tables overlap')
        if rows:occupied.append((offset,end))
        tables[kind]=(offset,rows)
    return tables,occupied


def _catalog(primary,fallback,scene):
    assets=[]
    for name,block in [('primary',primary),('fallback',fallback)]:
        tables,_=_tables(block)
        for index,row in enumerate(tables[1][1]):
            x,z,record,gate=row
            assets.append(dict(semantic_id=f'trigger://{scene}/field-map/{name}/kind-1/{index:04d}',
                table_source=name,table_kind=1,record_index=index,
                encoded=dict(tile_x=x,tile_z=z,record_index=record,gate=gate)))
    return dict(assets=assets)


def allocate_object_bind_rows(original,fallback,man,scene,requests):
    """Copy existing primary P0 bind records into verified zero append space.

    Callers must qualify these complete immutable MAP/fallback/MAN inputs.
    New coordinates must be absent from both lookup tables. Requests carry
    only an authored UUID, original donor row and new native anchor tile.
    Placement/anchor flags, project persistence and Build are separate stages.
    """
    if scene not in ('map01','map02','map03') or not isinstance(original,bytes) or len(original)!=0x12000 or not isinstance(fallback,bytes) or len(fallback)!=0x2000:
        raise ImportError('Object bind allocation requires complete kingdom MAP and fallback bytes')
    if not isinstance(requests,list) or not 1<=len(requests)<=32:
        raise ImportError('Object bind allocation requires one to thirty-two donor requests')
    primary=original[0x10000:];tables,occupied=_tables(primary);catalog=_catalog(primary,fallback,scene)
    offset,rows=tables[1];count=len(rows);start=offset+4*count;end=start+4*len(requests)
    if not count or end>len(primary) or count+len(requests)>32767 or any(start<hi and lo<end for lo,hi in occupied) or primary[start:end]!=bytes(end-start):
        raise ImportError('Object bind table has no verified zero append capacity')
    used={(r['encoded']['tile_x'],r['encoded']['tile_z']) for r in catalog['assets']};ids=set();result=bytearray(original);allocations=[]
    for index,request in enumerate(requests):
        if not isinstance(request,dict) or set(request)!={'bind_id','donor_index','tile_x','tile_z'}:
            raise ImportError('Object bind allocation requires exact donor and anchor fields')
        identifier=request['bind_id'];donor=request['donor_index'];x=request['tile_x'];z=request['tile_z']
        if not isinstance(identifier,str) or not re.fullmatch(r'bind://authored/[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}',identifier) or identifier in ids:
            raise ImportError('Object bind allocation requires distinct authored UUIDs')
        if type(donor) is not int or not 0<=donor<count or any(type(v) is not int or not 0<=v<128 for v in (x,z)) or (x,z) in used:
            raise ImportError('Object bind donor or unclaimed native anchor is unavailable')
        source=rows[donor];resolved=resolve_object_bind(catalog,man,source[0],source[1])
        if resolved['status']!='resolved_source_header' or resolved['trigger']['table_source']!='primary' or resolved['trigger']['record_index']!=donor:
            raise ImportError('Object bind donor must be an effective original primary partition-0 bind')
        at=0x10000+start+4*index;payload=bytes([x,z])+source[2:]
        result[at:at+4]=payload;ids.add(identifier);used.add((x,z))
        allocations.append(dict(bind_id=identifier,donor_index=donor,record_index=count+index,
            byte_offset=at,byte_length=4,before_hex='00000000',after_hex=payload.hex(),
            donor_sha256=sha256(source).hexdigest(),flat_man_record_index=source[2],gate_byte=source[3],
            script_id=f'script://{scene}/worldmap/man-p0/{resolved["man_record"]["record_index"]:04d}',
            man_record_sha256=resolved['man_record']['sha256'],encoded_animation_selector=resolved['encoded_animation_selector']))
    struct.pack_into('<h',result,0x10008,count+len(requests));candidate=bytes(result)
    after_tables,_=_tables(candidate[0x10000:])
    if any(after_tables[k][0]!=tables[k][0] or after_tables[k][1][:len(tables[k][1])]!=tables[k][1] or k!=1 and after_tables[k][1]!=tables[k][1] for k in range(4)):
        raise ImportError('Object bind allocation changed original table ownership')
    after_catalog=_catalog(candidate[0x10000:],fallback,scene)
    for request,audit in zip(requests,allocations):
        resolved=resolve_object_bind(after_catalog,man,request['tile_x'],request['tile_z'])
        if resolved['status']!='resolved_source_header' or resolved['trigger']['record_index']!=audit['record_index'] or resolved['man_record']['sha256']!=audit['man_record_sha256']:
            raise ImportError('Object bind allocation failed independent anchor/MAN readback')
    allowed={0x10008,0x10009,*range(0x10000+start,0x10000+end)}
    changes=[dict(byte_offset=i,before_byte=a,after_byte=b) for i,(a,b) in enumerate(zip(original,candidate)) if a!=b]
    if any(r['byte_offset'] not in allowed for r in changes):raise ImportError('Object bind allocation changed unaudited MAP bytes')
    return candidate,dict(scope='primary-kind-1-bind-row-allocation',scene=scene,source_sha256=sha256(original).hexdigest(),
        proposed_sha256=sha256(candidate).hexdigest(),fallback_sha256=sha256(fallback).hexdigest(),man_sha256=sha256(man).hexdigest(),
        original_row_count=count,proposed_row_count=count+len(requests),allocations=allocations,changed_bytes=changes,
        gameplay_verified=False,placement_allocated=False)
