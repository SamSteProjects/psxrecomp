"""Existing object-local vertex reference ownership and complete retargeting."""
from hashlib import sha256
from .core import ImportError
from .model_authoring import replace_model_content
from .model_primitives import inspect_model_primitives, patch_model_primitives, _primitive_field_locations

MAX_VERTEX_USERS = 4096


def vertex_users(data, object_index, vertex_index):
    inspection = inspect_model_primitives(data)
    if type(object_index) is not int or not 0 <= object_index < len(inspection['objects']):
        raise ImportError('Choose an existing source model object')
    obj = inspection['objects'][object_index]
    if type(vertex_index) is not int or not 0 <= vertex_index < min(obj['vertex_count'], 8192):
        raise ImportError('Choose an existing source vertex representable by a reference word')
    result = []
    for owner, _width in _primitive_field_locations(inspection):
        if owner['object_index'] != object_index or owner['field'] != 'vertex_index':
            continue
        primitive = obj['primitives'][owner['primitive_index']]
        if primitive['vertices'][owner['corner_index']] == vertex_index:
            result.append(dict(owner, vertex_index=vertex_index, corner_count=primitive['corner_count'],
                               sharing='vertex_corner', affected_corners=[owner['corner_index']]))
            if len(result) > MAX_VERTEX_USERS:
                raise ImportError('Selected vertex exceeds 4096 stored reference users')
    return result


def retarget_object_vertices(original, effective, expected_sha256, object_index, from_index, to_index):
    if not isinstance(effective, bytes) or sha256(effective).hexdigest() != expected_sha256:
        raise ImportError('Model changed since vertex reference inspection')
    replace_model_content(original, sha256(original).hexdigest(), effective, allow_normal_references=True)
    users = vertex_users(effective, object_index, from_index)
    obj = inspect_model_primitives(effective)['objects'][object_index]
    if type(to_index) is not int or not 0 <= to_index < min(obj['vertex_count'], 8192):
        raise ImportError('Choose an existing target vertex representable by a reference word')
    if from_index == to_index or not users:
        return effective
    owners = {row['primitive_index'] for row in users}
    edits = [dict(object_index=object_index, primitive_index=row['primitive_index'],
                  vertices=[to_index if index == from_index else index for index in row['vertices']])
             for row in obj['primitives'] if row['primitive_index'] in owners]
    replacement = patch_model_primitives(effective, expected_sha256, edits)[0]
    return replace_model_content(original, sha256(original).hexdigest(), replacement,
                                 allow_normal_references=True)[0]
