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
