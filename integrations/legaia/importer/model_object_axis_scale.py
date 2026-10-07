"""Scale Current object geometry and inverse-transpose its stored normals."""
from hashlib import sha256
from math import isqrt
import json
from .core import ImportError
from .model_authoring import replace_model_content
from .model_json import export_shape_json, import_shape_json
from rotation_math import round_half_away


def scale_normal_axes(row, percents):
    """Preserve source magnitude; exact square comparisons round halves away."""
    length2 = sum(v*v for v in row)
    if not length2:
        return [0, 0, 0]
    weights = [row[a]*percents[(a+1)%3]*percents[(a+2)%3] for a in range(3)]
    denominator = sum(v*v for v in weights)
    result = []
    for value in weights:
        numerator = value*value*length2
        magnitude = isqrt(numerator//denominator)
        if 4*numerator >= denominator*(2*magnitude+1)**2:
            magnitude += 1
        result.append(-magnitude if value < 0 else magnitude)
    return result


def scale_object_axes(original, effective, expected_sha256, object_index, percents, pivot):
    if sha256(effective).hexdigest() != expected_sha256:
        raise ImportError('Model changed since object inspection')
    if not isinstance(percents, list) or len(percents) != 3 or any(type(v) is not int or not 1 <= v <= 1000 for v in percents) or pivot not in ('origin', 'center'):
        raise ImportError('Object axis scale requires three integer percents1..1000 and origin or center pivot')
    source_hash = sha256(original).hexdigest()
    replace_model_content(original, source_hash, effective, allow_normal_references=True)
    document = json.loads(export_shape_json(effective))
    if type(object_index) is not int or not 0 <= object_index < len(document['objects']):
        raise ImportError('Choose an existing model object')
    obj = document['objects'][object_index]
    if not 1 <= len(obj['vertices']) <= 8192 or len(obj['normals']) > 8192:
        raise ImportError('Object axis scale requires1..8192 vertices and at most8192 stored normals')
    center2 = [0, 0, 0] if pivot == 'origin' else [min(v[a] for v in obj['vertices'])+max(v[a] for v in obj['vertices']) for a in range(3)]
    obj['vertices'] = [[round_half_away((2*v-center2[a])*percents[a]+100*center2[a], 200) for a, v in enumerate(row)] for row in obj['vertices']]
    obj['normals'] = [scale_normal_axes(row, percents) for row in obj['normals']]
    if any(not -32768 <= v <= 32767 for kind in ('vertices', 'normals') for row in obj[kind] for v in row):
        raise ImportError('Object axis scale exceeds signed16; nothing was applied')
    replacement = import_shape_json(effective, expected_sha256, json.dumps(document).encode())[0]
    return replace_model_content(original, source_hash, replacement, allow_normal_references=True)[0]
