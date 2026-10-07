"""Native object reflection with coupled winding and corner attributes."""
from hashlib import sha256
import json
from .core import ImportError
from .model_authoring import replace_model_content
from .model_json import export_shape_json,import_shape_json
from .model_primitives import _qualified_model,_primitive_field_locations
from .model_normal_references import _normal_field_locations


def mirror_object(original,effective,expected_sha256,object_index,axis,pivot):
    if sha256(effective).hexdigest()!=expected_sha256:
        raise ImportError('Model changed since object inspection')
    if axis not in ('x','y','z') or pivot not in ('origin','center'):
        raise ImportError('Object mirror requires X/Y/Z and origin or center pivot')
    source_hash=sha256(original).hexdigest()
    replace_model_content(original,source_hash,effective,allow_normal_references=True)
    document=json.loads(export_shape_json(effective));inspection,_=_qualified_model(effective)
    if type(object_index) is not int or not 0<=object_index<len(document['objects']):
        raise ImportError('Choose an existing model object')
    obj=document['objects'][object_index]
    if not 1<=len(obj['vertices'])<=8192 or len(obj['normals'])>8192 or len(inspection['objects'][object_index]['primitives'])>4096:
        raise ImportError('Object mirror exceeds bounded vectors or primitives')
    a='xyz'.index(axis);center2=0 if pivot=='origin' else min(v[a] for v in obj['vertices'])+max(v[a] for v in obj['vertices'])
    for kind,center in [('vertices',center2),('normals',0)]:
        for row in obj[kind]:
            row[a]=center-row[a]
            if not -32768<=row[a]<=32767:
                raise ImportError('Object mirror exceeds signed16; nothing was applied')
    result=bytearray(import_shape_json(effective,expected_sha256,json.dumps(document).encode())[0])
    fields=[(f,w) for f,w in [*_primitive_field_locations(inspection),*_normal_field_locations(effective,inspection)] if f['object_index']==object_index]
    if len(fields)>65536:raise ImportError('Object mirror corner fields exceed65536')
    key=lambda f:(f['primitive_index'],f['field'],f.get('axis'),f['corner_index'])
    locations={key(f):(f['byte_offset'],w) for f,w in fields}
    for field,width in fields:
        if field['corner_index'] not in (1,2):continue
        paired={**field,'corner_index':3-field['corner_index']};start,other_width=locations[key(paired)]
        if other_width!=width:raise ImportError('Object mirror corner ownership differs')
        at=field['byte_offset'];result[at:at+width]=effective[start:start+width]
    return replace_model_content(original,source_hash,bytes(result),allow_normal_references=True)[0]
