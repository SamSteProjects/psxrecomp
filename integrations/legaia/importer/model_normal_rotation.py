"""Rotate an existing object's stored normal words independently of geometry."""
from hashlib import sha256
import json
from .core import ImportError
from .model_authoring import replace_model_content
from .model_json import export_shape_json,import_shape_json
from rotation_math import Q30,sin_cos_q30,round_half_away


def rotate_object_normals(original,effective,expected_sha256,object_index,axis,angle_units):
    if sha256(effective).hexdigest()!=expected_sha256:
        raise ImportError('Model changed since normal inspection')
    if axis not in ('x','y','z') or type(angle_units) is not int or not 0<=angle_units<=4095:
        raise ImportError('Normal rotation requires X/Y/Z and integer angle units0..4095')
    source_hash=sha256(original).hexdigest()
    replace_model_content(original,source_hash,effective,allow_normal_references=True)
    document=json.loads(export_shape_json(effective))
    if type(object_index) is not int or not 0<=object_index<len(document['objects']):
        raise ImportError('Choose an existing model object')
    normals=document['objects'][object_index]['normals']
    if not 1<=len(normals)<=8192:
        raise ImportError('Normal rotation requires1..8192 existing stored normals')
    sine,cosine=sin_cos_q30(angle_units)
    for i,(x,y,z) in enumerate(normals):
        numerators=(x*Q30,y*cosine-z*sine,z*cosine+y*sine) if axis=='x' else (x*cosine+z*sine,y*Q30,z*cosine-x*sine) if axis=='y' else (x*cosine-y*sine,y*cosine+x*sine,z*Q30)
        rotated=[round_half_away(value,Q30) for value in numerators]
        if any(not -32768<=value<=32767 for value in rotated):
            raise ImportError('Normal rotation exceeds signed16; nothing was applied')
        normals[i]=rotated
    replacement=import_shape_json(effective,expected_sha256,json.dumps(document).encode())[0]
    return replace_model_content(original,source_hash,replacement,allow_normal_references=True)[0]
