"""Rescale existing signed source normal words without changing table ownership."""
from hashlib import sha256
import json
from math import isqrt

from .core import ImportError
from .model_authoring import replace_model_content
from .model_json import export_shape_json, import_shape_json


def rescale_normal(vector, length):
    """Nearest integer, exact midpoint comparison, halves away from zero."""
    squared = sum(value * value for value in vector)
    if not squared:
        return [0, 0, 0]
    result = []
    for value in vector:
        product = abs(value) * length
        magnitude = isqrt(product * product // squared)
        if 4 * product * product >= squared * (2 * magnitude + 1) ** 2:
            magnitude += 1
        result.append(-magnitude if value < 0 else magnitude)
    return result


def rescale_object_normals(original, effective, expected_sha256, object_index, length):
    if sha256(effective).hexdigest() != expected_sha256:
        raise ImportError('Model changed since object inspection; reopen the vector editor')
    if type(length) is not int or not 1 <= length <= 32767:
        raise ImportError('Normal length requires an integer1..32767')
    source_hash = sha256(original).hexdigest()
    replace_model_content(original, source_hash, effective, allow_normal_references=True)
    document = json.loads(export_shape_json(effective))
    if type(object_index) is not int or not 0 <= object_index < len(document['objects']):
        raise ImportError('Choose an existing model object')
    obj = document['objects'][object_index]
    if not obj['normals']:
        raise ImportError('The selected object has no stored normals')
    obj['normals'] = [rescale_normal(vector, length) for vector in obj['normals']]
    replacement = import_shape_json(effective, expected_sha256, json.dumps(document).encode())[0]
    return replace_model_content(original, source_hash, replacement, allow_normal_references=True)[0]
