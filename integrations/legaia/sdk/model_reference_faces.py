"""Qualified Current/Retail face identities for read-only vector references."""
from hashlib import sha256
from importer.model_authoring import replace_model_content
from importer.model_face_removal import qualify_face_removal, FORMAT
from importer.model_primitives import inspect_model_primitives
from .project import ProjectError


def mapping(retail, effective, binding, object_index):
    removed = binding.get('removed_faces', []) if binding and binding.get('format') == FORMAT else []
    if binding and binding.get('format') == FORMAT:
        qualify_face_removal(retail, sha256(retail).hexdigest(), effective, removed)
    else:
        replace_model_content(retail, sha256(retail).hexdigest(), effective, allow_normal_references=True)
    source = inspect_model_primitives(retail)['objects']
    current = inspect_model_primitives(effective)['objects']
    if type(object_index) is not int or not 0 <= object_index < len(source):
        raise ProjectError('Reference face mapping requires an existing object')
    omitted = {(row['object_index'], row['primitive_index']) for row in removed}
    result = []
    index = 0
    for row in source[object_index]['primitives']:
        primitive = row['primitive_index']
        gone = (object_index, primitive) in omitted
        result.append(dict(retail_index=primitive, current_index=None if gone else index))
        if not gone:
            if index >= len(current[object_index]['primitives']) or current[object_index]['primitives'][index]['corner_count'] != row['corner_count']:
                raise ProjectError('Reference face mapping differs from qualified Current topology')
            index += 1
    if index != len(current[object_index]['primitives']):
        raise ProjectError('Reference face mapping has unowned Current faces')
    return result


def addition_mapping(project, asset_id, retail, effective, binding):
    from .model_face_addition import base_content
    from importer.model_face_ledger import qualify_face_ledger
    base=base_content(project,asset_id,retail,binding)
    audit=qualify_face_ledger(base,binding['ledger'],effective)
    objects=inspect_model_primitives(retail)['objects'];maps=[];authored=[]
    for obj in objects:
        owner=obj['object_index'];base_map=mapping(retail,base,binding['base_binding'],owner)
        retained={face['source_primitive_index']:face['current_primitive_index'] for face in audit['faces']
                  if face['object_index']==owner and face['origin']=='source'}
        maps.append([dict(retail_index=row['retail_index'],current_index=retained.get(row['current_index'])) for row in base_map])
        authored.append([dict(face_id=face['face_id'],current_index=face['current_primitive_index']) for face in audit['faces']
                         if face['object_index']==owner and face['origin']=='authored'])
    return maps,authored


def addition_group_mapping(project, asset_id, retail, effective, binding):
    """Retain original packet-group ownership through deleted donor faces."""
    from .model_face_addition import base_content
    from importer.model_face_ledger import qualify_face_ledger, _operations
    base=base_content(project,asset_id,retail,binding)
    audit=qualify_face_ledger(base,binding['ledger'],effective)
    source=inspect_model_primitives(retail)['objects']
    initial=inspect_model_primitives(base)['objects'];origins={}
    base_hash=sha256(base).hexdigest()
    for obj in initial:
        owner=obj['object_index'];faces=mapping(retail,base,binding['base_binding'],owner)
        inverse={row['current_index']:row['retail_index'] for row in faces if row['current_index'] is not None}
        for face in obj['primitives']:
            index=face['primitive_index'];original=source[owner]['primitives'][inverse[index]]
            origins[f'face://source/{base_hash}/{owner}/{index}']=(owner,original['group_index'])
    for operation in _operations(binding['ledger']):
        if operation['kind']=='add_faces':
            for request in operation['additions']:
                origins[request['face_id']]=origins[request['donor_face_id']]
    current=inspect_model_primitives(effective)['objects'];groups=[{} for _ in current]
    for face in audit['faces']:
        owner=face['object_index'];origin_owner,original=origins[face['face_id']]
        group=face['group_index']
        if owner!=origin_owner or group in groups[owner] and groups[owner][group]!=original:
            raise ProjectError('Current group has conflicting retained Retail ownership')
        groups[owner][group]=original
    result=[]
    for obj,owned in zip(current,groups):
        count=len({row['group_index'] for row in obj['primitives']})
        if set(owned)!=set(range(count)):
            raise ProjectError('Current group has no qualified original packet owner')
        result.append([owned[index] for index in range(count)])
    return result
