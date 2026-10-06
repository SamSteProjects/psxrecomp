"""Stable Current object donors and complete cloned face/group identities."""
from copy import deepcopy
from hashlib import sha256
from .core import ImportError
from .model_face_addition import MAX_NEW_FACES
from .model_object_allocation import allocate_model_objects,MAX_NEW_OBJECTS
from .model_group_allocation import _identity,MAX_NEW_GROUPS
from .model_primitives import _qualified_model
from .model_face_removal import _groups


def source_objects(original):
    inspection,_=_qualified_model(original);key=sha256(original).hexdigest()
    return {f'object://source/{key}/{obj["object_index"]}':dict(
        object_id=f'object://source/{key}/{obj["object_index"]}',origin='source',
        object_index=obj['object_index'],source_object_index=obj['object_index'])
        for obj in inspection['objects']}


def apply_object_allocation(current,faces,objects,requests,reserved_faces,reserved_groups,reserved_objects):
    if not isinstance(requests,list) or not 1<=len(requests)<=MAX_NEW_OBJECTS:
        raise ImportError('Object ledger requires bounded Current donor requests')
    inspection,_=_qualified_model(current);native_groups={owner:[] for owner in range(len(inspection['objects']))}
    for owner,start,count,stride,first in _groups(current,inspection):
        native_groups[owner].append((start,count,stride,first))
    object_ids=set(reserved_objects);group_ids=set(reserved_groups);face_ids=set(reserved_faces)|set(faces)
    native=[];clones=[]
    for request in requests:
        if (not isinstance(request,dict) or set(request)!={'object_id','donor_object_id','groups'}
                or not isinstance(request['donor_object_id'],str) or request['donor_object_id'] not in objects):
            raise ImportError('Object ledger requires exact stable object and donor identities')
        _identity(request['object_id'],'object://authored/',object_ids)
        owner=objects[request['donor_object_id']]['object_index'];groups=native_groups[owner]
        if not isinstance(request['groups'],list) or len(request['groups'])!=len(groups):
            raise ImportError('Object ledger requires complete Current donor group ownership')
        for group,(start,count,stride,first) in zip(request['groups'],groups):
            if (not count or not isinstance(group,dict) or set(group)!={'group_id','faces'}
                    or not isinstance(group['faces'],list) or len(group['faces'])!=count):
                raise ImportError('Object ledger requires nonempty native groups and all donor faces')
            _identity(group['group_id'],'group://authored/',group_ids)
            for index,face in enumerate(group['faces']):
                if not isinstance(face,dict) or set(face)!={'face_id','donor_face_id'}:
                    raise ImportError('Cloned object face requires exact identity and stable donor')
                _identity(face['face_id'],'face://authored/',face_ids)
                donor=faces.get(face['donor_face_id']) if isinstance(face['donor_face_id'],str) else None
                if not donor or donor['object_index']!=owner or donor['current_primitive_index']!=first+index:
                    raise ImportError('Cloned object faces must match the complete Current donor order')
        native.append(dict(object_id=request['object_id'],donor_object_index=owner))
        clones.append((request,groups))
    if sum(len(group['faces']) for request in requests for group in request['groups'])>MAX_NEW_FACES or sum(len(request['groups']) for request in requests)>MAX_NEW_GROUPS:
        raise ImportError('Object ledger exceeds cloned face/group budgets')
    candidate,audit=allocate_model_objects(current,sha256(current).hexdigest(),native)
    updated=deepcopy(faces);new_objects=deepcopy(objects);new_groups=[]
    for (request,groups),allocation in zip(clones,audit['new_objects']):
        owner=allocation['object_index']
        new_objects[request['object_id']]=dict(object_id=request['object_id'],origin='authored',
            object_index=owner,donor_object_id=request['donor_object_id'])
        for ordinal,(group,(start,count,stride,first)) in enumerate(zip(request['groups'],groups)):
            new_groups.append(dict(group_id=group['group_id'],object_index=owner,origin_group_index=ordinal,
                donor_face_id=group['faces'][0]['donor_face_id'],
                flags=int.from_bytes(current[start+2:start+4],'little'),mode=current[start+7]))
            for index,face in enumerate(group['faces']):
                updated[face['face_id']]=dict(face_id=face['face_id'],origin='authored',object_index=owner,
                    group_index=ordinal,current_primitive_index=first+index,donor_face_id=face['donor_face_id'])
    audit['allocated_groups']=new_groups
    return candidate,updated,new_objects,audit
