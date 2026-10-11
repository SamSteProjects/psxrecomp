"""Compose donor-derived placed records, init anchors and P0 binds.

Native serialization only: shared scripts are not executed or cloned, actor
pool demand is not simulated, and relocation zero-space runtime ownership
remains unverified. No existing decoration allocation behavior is changed.
"""
from copy import deepcopy
from hashlib import sha256
import re
import struct

from .core import ImportError
from .worldmap_placement_allocation import inventory
from .worldmap_placements import decode_worldmap_placements
from .worldmap_object_bind_allocation import allocate_object_bind_rows, _catalog
from .worldmap_object_binds import resolve_object_bind


def allocate_scripted_placements(data,fallback,man,floor,scene,requests,*,relocation_offset=None):
    if not isinstance(fallback,bytes) or len(fallback)!=0x2000 or not isinstance(man,bytes) or not 0x2b<=len(man)<=4*1024*1024:
        raise ImportError('Scripted World allocation requires immutable bounded fallback and MAN inputs')
    source=inventory(data,floor,scene)
    if not isinstance(requests,list) or not 1<=len(requests)<=32:
        raise ImportError('Scripted World allocation requires one to thirty-two requests')
    if len(source['current_placements'])+len(requests)>511:
        raise ImportError('Scripted World allocation exceeds the source entity budget')
    catalog=_catalog(data[0x10000:],fallback,scene)
    donors={p['source_cell']:p for p in source['current_placements']
        if p['source_layer']=='placed' and p['source_bind_owner']=='init_bind' and p['model_pool_index']!=0}
    free=set(source['free_record_indices']);targets=set(source['target_cells'])
    ids=set();records=set();cells=set();result=bytearray(data);allocations=[];binds=[]
    for request in requests:
        if not isinstance(request,dict) or set(request)!={'placement_id','donor_cell','target_cell','record_index','values','shared_script'} or request['shared_script'] is not True:
            raise ImportError('Scripted World clone requires exact ownership and explicit shared-script scope')
        identifier=request['placement_id']
        if not isinstance(identifier,str) or not re.fullmatch(r'placement://authored/[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}',identifier) or identifier in ids:
            raise ImportError('Scripted World clone requires a distinct authored UUID')
        donor_cell,cell,record=(request[k] for k in ('donor_cell','target_cell','record_index'))
        if any(type(v) is not int for v in (donor_cell,cell,record)) or donor_cell not in donors or cell not in targets or record not in free or record in records:
            raise ImportError('Scripted World donor, empty cell or unused zero record is unavailable')
        value=request['values']
        if not isinstance(value,dict) or set(value)!={'offset','yaw_units'} or not isinstance(value['offset'],dict) or set(value['offset'])!={'x','y','z'} or any(type(v) is not int or not -32768<=v<=32767 for v in value['offset'].values()) or type(value['yaw_units']) is not int or not 0<=value['yaw_units']<4096:
            raise ImportError('Scripted World clone requires signed16 offsets and yaw0..4095')
        donor=donors[donor_cell];donor_at=donor['object_record_index']*32
        dc,dr=struct.unpack_from('<2b',data,donor_at+6)
        col,row=cell%128+dc,cell//128+dr
        if not 0<=col<128 or not 0<=row<128:
            raise ImportError('Scripted World footprint anchor is outside the native grid')
        anchor=row*128+col
        if anchor not in targets or {cell,anchor}&cells:
            raise ImportError('Scripted World footprint or anchor has another source/allocation owner')
        anchor_word=struct.unpack_from('<H',data,0x8000+anchor*2)[0]
        if anchor_word&0x400:
            raise ImportError('Scripted World target anchor already has init ownership')
        resolved=resolve_object_bind(catalog,man,donor['source_anchor']['col'],donor['source_anchor']['row'])
        if resolved['status']!='resolved_source_header' or resolved['trigger']['table_source']!='primary':
            raise ImportError('Scripted World donor requires an effective primary P0 bind')
        if resolve_object_bind(catalog,man,col,row)['status']!='no_source_bind':
            raise ImportError('Scripted World target anchor already has a source bind')
        bind_id=identifier.replace('placement://','bind://',1)
        binds.append(dict(bind_id=bind_id,donor_index=resolved['trigger']['record_index'],tile_x=col,tile_z=row))
        cell_at=0x8000+cell*2;word=struct.unpack_from('<H',data,cell_at)[0]
        previous_at=(word&511)*32;at=record*32
        payload=bytearray(data[donor_at:donor_at+32])
        payload[20:24]=data[previous_at+20:previous_at+24]
        struct.pack_into('<3h',payload,0,*(value['offset'][axis] for axis in ('x','y','z')))
        yaw=struct.unpack_from('<H',payload,10)[0]
        struct.pack_into('<H',payload,10,(yaw&0xf000)|value['yaw_units'])
        result[at:at+32]=payload
        struct.pack_into('<H',result,cell_at,(word&~511)|record)
        anchor_at=0x8000+anchor*2
        struct.pack_into('<H',result,anchor_at,struct.unpack_from('<H',result,anchor_at)[0]|0x400)
        ids.add(identifier);records.add(record);cells.update((cell,anchor))
        allocations.append(dict(placement_id=identifier,bind_id=bind_id,donor_cell=donor_cell,target_cell=cell,
            anchor_cell=anchor,record_index=record,donor_record_sha256=sha256(data[donor_at:donor_at+32]).hexdigest(),
            allocated_record_sha256=sha256(payload).hexdigest(),shared_script=True,
            script_id=f'script://{scene}/worldmap/man-p0/{resolved["man_record"]["record_index"]:04d}'))
    candidate,bind_audit=allocate_object_bind_rows(bytes(result),fallback,man,scene,binds,relocation_offset=relocation_offset)
    decoded=decode_worldmap_placements(candidate,floor,scene=scene)
    before=decode_worldmap_placements(data,floor,scene=scene)
    originals={p['source_cell']:p for p in before['placements']};after={p['source_cell']:p for p in decoded['placements']}
    if set(after)!=set(originals)|{a['target_cell'] for a in allocations} or any(after[c]!=p for c,p in originals.items()) or decoded['unresolved']!=before['unresolved'] or decoded['coverage']['excluded']!=before['coverage']['excluded']:
        raise ImportError('Scripted World allocation changed existing source coverage')
    for allocation in allocations:
        seed=after[allocation['target_cell']]
        if seed['source_layer']!='placed' or seed['source_bind_owner']!='init_bind' or seed['object_record_index']!=allocation['record_index']:
            raise ImportError('Scripted World allocation failed placed/anchor ownership readback')
        allocation['native_seed']=deepcopy(seed)
    allowed={r*32+n for r in records for n in range(32)}
    allowed.update(0x8000+c*2+n for c in cells for n in (0,1))
    allowed.update(r['byte_offset'] for r in bind_audit['changed_bytes'])
    changes=[dict(byte_offset=i,before_byte=a,after_byte=b) for i,(a,b) in enumerate(zip(data,candidate)) if a!=b]
    if any(r['byte_offset'] not in allowed for r in changes):
        raise ImportError('Scripted World allocation changed unrelated MAP bytes')
    return candidate,dict(scope='scripted-world-placement-allocation',source_sha256=sha256(data).hexdigest(),
        proposed_sha256=sha256(candidate).hexdigest(),allocations=allocations,bind_allocation=bind_audit,
        changed_bytes=changes,original_placement_count=len(originals),proposed_placement_count=len(after),
        gameplay_verified=False,runtime_pool_demand='not_evaluated',opaque_zero_runtime_ownership='not_verified')
