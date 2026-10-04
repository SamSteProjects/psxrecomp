"""Reinsert deleted stable faces from qualified ledger preimages.

This pure codec grows owned primitive streams and rebases existing tables.
It does not publish assets or create a restoration ledger operation.
"""
from copy import deepcopy
from hashlib import sha256
import struct
from .assets import MAX_MODEL_BYTES
from .core import ImportError
from .model_primitives import _qualified_model
from .model_face_removal import _groups
from .model_face_ledger import _replay_face_ledger, _source_faces, _operations


def reinsert_ledger_faces(original,ledger,face_ids):
    current,audit,deleted=_replay_face_ledger(original,ledger,capture=True)
    if (not isinstance(face_ids,list) or not 0<len(face_ids)<=4096
            or any(not isinstance(identity,str) or identity not in deleted for identity in face_ids)
            or len(set(face_ids))!=len(face_ids)):
        raise ImportError('Face reinsertion requires unique recorded deleted identities')
    initial=_source_faces(original,sha256(original).hexdigest())
    origins={identity:(face['object_index'],face['group_index']) for identity,face in initial.items()}
    ranks={identity:index for index,identity in enumerate(initial)}
    for operation in _operations(ledger):
        if operation['kind']=='add_faces':
            for request in operation['additions']:
                origins[request['face_id']]=origins[request['donor_face_id']]
                ranks[request['face_id']]=len(ranks)
    inspection,_=_qualified_model(current)
    active={face['face_id']:deepcopy(face) for face in audit['faces']}
    groups={};object_groups={}
    for owner,start,count,stride,first in _groups(current,inspection):
        group=len(object_groups.setdefault(owner,[]))
        item=(start,count,stride,first)
        groups[owner,group]=item;object_groups[owner].append(item)
    descriptors={};packets={}
    for identity,face in active.items():
        owner=face['object_index'];origin=origins[identity]
        start,count,stride,first=groups[owner,face['group_index']]
        at=start+8+(face['current_primitive_index']-first)*stride
        descriptors[origin]=(current[start:start+8],current[start+8+count*stride:start+8+(count+1)*stride])
        packets.setdefault(origin,[]).append((ranks[identity],identity,current[at:at+stride]))
    # For an absent group use its last recorded descriptor/footer, including ABE.
    for record in deleted.values():
        identity=record['face']['face_id'];origin=origins[identity]
        if origin not in packets:
            descriptors[origin]=(record['descriptor'],record['footer'])
    for identity in face_ids:
        record=deleted[identity];origin=origins[identity]
        packets.setdefault(origin,[]).append((ranks[identity],identity,record['packet']))
        active[identity]=deepcopy(record['face'])
    replacements=[];selected_owners={active[identity]['object_index'] for identity in face_ids}
    for owner in sorted(selected_owners):
        start=12+struct.unpack_from('<I',current,12+owner*28+16)[0]
        existing=object_groups.get(owner,[])
        terminal=(existing[-1][0]+8+(existing[-1][1]+1)*existing[-1][2]) if existing else start
        end=terminal+4;payload=bytearray();primitive=0
        for group,origin in enumerate(sorted(identity for identity in packets if identity[0]==owner)):
            descriptor,footer=descriptors[origin];rows=sorted(packets[origin])
            stride=descriptor[5]*4
            if not rows or len(rows)>65535 or len(footer)!=stride or any(len(packet)!=stride for _,_,packet in rows):
                raise ImportError('Restored group packet layout or count conflicts')
            header=bytearray(descriptor);struct.pack_into('<H',header,0,len(rows));payload.extend(header)
            for _,identity,packet in rows:
                payload.extend(packet);active[identity].update(group_index=group,current_primitive_index=primitive);primitive+=1
            payload.extend(footer)
        payload.extend(current[terminal:end])
        if len(payload)<=end-start:
            raise ImportError('Restoration did not grow its owned primitive stream')
        replacements.append((start,end,bytes(payload),owner,primitive))
    replacements.sort()
    if any(left[1]>right[0] for left,right in zip(replacements,replacements[1:])):
        raise ImportError('Restored primitive streams overlap')
    growth=sum(len(payload)-(end-start) for start,end,payload,_,_ in replacements)
    if len(current)+growth>MAX_MODEL_BYTES:
        raise ImportError('Restored model exceeds its byte budget')
    def relocate(offset,primitive=False):
        delta=0
        for start,end,payload,_,_ in replacements:
            if start<=offset<end:
                if primitive and offset==start:return start+delta
                raise ImportError('Restoration overlaps an existing table pointer')
            if offset>=end:delta+=len(payload)-(end-start)
        return offset+delta
    candidate=bytearray();position=0
    for start,end,payload,_,_ in replacements:
        candidate.extend(current[position:start]);candidate.extend(payload);position=end
    candidate.extend(current[position:]);pointers=[]
    for obj in inspection['objects']:
        owner=obj['object_index'];header=12+owner*28
        for field in (0,8,16):
            old=struct.unpack_from('<I',current,header+field)[0]
            used=field==16 or struct.unpack_from('<I',current,header+field+4)[0]!=0
            new=relocate(old+12,field==16)-12 if used else old
            struct.pack_into('<I',candidate,header+field,new)
            pointers.append(dict(object_index=owner,table_field_offset=field,source_offset=old,current_offset=new))
    for _,_,_,owner,count in replacements:struct.pack_into('<I',candidate,12+owner*28+20,count)
    candidate=bytes(candidate);_qualified_model(candidate)
    return candidate,dict(source_sha256=sha256(current).hexdigest(),proposed_sha256=sha256(candidate).hexdigest(),
        source_byte_length=len(current),proposed_byte_length=len(candidate),growth_bytes=growth,
        restored_face_ids=deepcopy(face_ids),faces=[active[identity] for identity in sorted(active,key=ranks.get)],
        pointer_relocations=pointers)
