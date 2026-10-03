"""Retarget only existing stored normal operands in one qualified object."""
from hashlib import sha256
from .core import ImportError
from .model_authoring import replace_model_content
from .model_normal_references import normal_users
from .model_primitives import inspect_model_primitives, patch_model_primitives


def retarget_object_normals(original,effective,expected_sha256,object_index,from_index,to_index):
    if sha256(effective).hexdigest()!=expected_sha256:
        raise ImportError('Model changed since normal reference inspection')
    replace_model_content(original,sha256(original).hexdigest(),effective,allow_normal_references=True)
    inspection=inspect_model_primitives(effective,include_normal_references=True)
    if type(object_index) is not int or not 0<=object_index<len(inspection['objects']):
        raise ImportError('Choose an existing model object')
    obj=inspection['objects'][object_index]
    if any(type(index) is not int or not 0<=index<min(obj['normal_count'],8192) for index in [from_index,to_index]):
        raise ImportError('Choose existing object normals representable by source reference words')
    users=normal_users(effective,object_index,from_index)
    if from_index==to_index or not users:return effective
    primitives={row['primitive_index'] for row in users}
    edits=[dict(object_index=object_index,primitive_index=row['primitive_index'],normal_indices=[to_index if index==from_index else index for index in row['normal_indices']]) for row in obj['primitives'] if row['primitive_index'] in primitives]
    replacement=patch_model_primitives(effective,expected_sha256,edits)[0]
    return replace_model_content(original,sha256(original).hexdigest(),replacement,allow_normal_references=True)[0]
