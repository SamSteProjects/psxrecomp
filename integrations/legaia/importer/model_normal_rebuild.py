"""Area-weighted native face normals, retaining existing reference ownership."""
from hashlib import sha256
from math import isqrt
import json
from .core import ImportError
from .model_authoring import replace_model_content
from .model_json import export_shape_json, import_shape_json
from .model_primitives import inspect_model_primitives


def rebuild_words(vertices, normals, primitives, direction):
    if direction not in ('winding', 'reverse'):
        raise ImportError('Choose winding or reverse normal direction')
    if not 1 <= len(vertices) <= 8192 or not 1 <= len(normals) <= 8192 or len(primitives) > 4096:
        raise ImportError('Normal rebuild requires bounded existing vectors and faces')
    sums = {}
    for face in primitives:
        refs = face['normal_indices']
        if refs is None:
            continue
        for corners in ((0, 1, 2), (1, 3, 2)) if face['corner_count'] == 4 else ((0, 1, 2),):
            a, b, c = [vertices[face['vertices'][i]] for i in corners]
            u, v = ([b[i]-a[i] for i in range(3)], [c[i]-a[i] for i in range(3)])
            cross = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
            if not any(cross):
                raise ImportError('Normal rebuild refuses degenerate lit triangles; nothing was applied')
            # Each triangle contributes once per distinct stored normal slot.
            for index in set(refs[i] for i in corners) if face['gouraud'] else {refs[0]}:
                total = sums.setdefault(index, [0, 0, 0])
                for axis in range(3):
                    total[axis] += cross[axis]
    if not sums:
        raise ImportError('Normal rebuild requires existing lit face references')
    result = [list(row) for row in normals]
    for index, total in sums.items():
        squared = sum(v*v for v in total)
        if not squared:
            raise ImportError('Normal rebuild refuses cancelling face directions; nothing was applied')
        row = []
        for value in total:
            numerator = abs(value)*4096
            word = isqrt(numerator*numerator // squared)
            if 4*numerator*numerator >= (2*word+1)**2*squared:
                word += 1
            row.append(word * (-1 if value < 0 else 1) * (-1 if direction == 'reverse' else 1))
        result[index] = row
    return result


def rebuild_object_normals(original, effective, expected_sha256, object_index, direction):
    if sha256(effective).hexdigest() != expected_sha256:
        raise ImportError('Model changed since normal inspection')
    source_hash = sha256(original).hexdigest()
    replace_model_content(original, source_hash, effective, allow_normal_references=True)
    document = json.loads(export_shape_json(effective))
    if type(object_index) is not int or not 0 <= object_index < len(document['objects']):
        raise ImportError('Choose an existing model object')
    obj = document['objects'][object_index]
    faces = inspect_model_primitives(effective, include_normal_references=True)['objects'][object_index]['primitives']
    obj['normals'] = rebuild_words(obj['vertices'], obj['normals'], faces, direction)
    candidate = import_shape_json(effective, expected_sha256, json.dumps(document).encode())[0]
    return replace_model_content(original, source_hash, candidate, allow_normal_references=True)[0]
