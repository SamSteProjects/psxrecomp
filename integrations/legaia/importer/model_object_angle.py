"""Source-bound object rotation: geometry about a pivot, normals about zero."""
from hashlib import sha256
import json
from .core import ImportError
from .model_authoring import replace_model_content
from .model_json import export_shape_json,import_shape_json
from rotation_math import Q30,sin_cos_q30,round_half_away


def rotate_object_angle(original,effective,expected_sha256,object_index,axis,angle_units,pivot):
    if sha256(effective).hexdigest()!=expected_sha256:
        raise ImportError('Model changed since object inspection')
    if axis not in ('x','y','z') or type(angle_units) is not int or not 0<=angle_units<=4095 or pivot not in ('origin','center'):
        raise ImportError('Object rotation requires X/Y/Z, integer angle units0..4095 and origin or center pivot')
    source_hash=sha256(original).hexdigest()
    replace_model_content(original,source_hash,effective,allow_normal_references=True)
    document=json.loads(export_shape_json(effective))
    if type(object_index) is not int or not 0<=object_index<len(document['objects']):
        raise ImportError('Choose an existing model object')
    obj=document['objects'][object_index]
    if not 1<=len(obj['vertices'])<=8192 or len(obj['normals'])>8192:
        raise ImportError('Object rotation requires1..8192 vertices and at most8192 stored normals')
    pivot2=[0,0,0] if pivot=='origin' else [min(v[a] for v in obj['vertices'])+max(v[a] for v in obj['vertices']) for a in range(3)]
    sine,cosine=sin_cos_q30(angle_units)
    for kind,center2 in [('vertices',pivot2),('normals',[0,0,0])]:
        for i,row in enumerate(obj[kind]):
            x,y,z=[2*v-center2[a] for a,v in enumerate(row)]
            numerators=(x*Q30,y*cosine-z*sine,z*cosine+y*sine) if axis=='x' else (x*cosine+z*sine,y*Q30,z*cosine-x*sine) if axis=='y' else (x*cosine-y*sine,y*cosine+x*sine,z*Q30)
            rotated=[round_half_away(n+center2[a]*Q30,2*Q30) for a,n in enumerate(numerators)]
            if any(not -32768<=v<=32767 for v in rotated):
                raise ImportError('Object rotation exceeds signed16; nothing was applied')
            obj[kind][i]=rotated
    replacement=import_shape_json(effective,expected_sha256,json.dumps(document).encode())[0]
    return replace_model_content(original,source_hash,replacement,allow_normal_references=True)[0]
