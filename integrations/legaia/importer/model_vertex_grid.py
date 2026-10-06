"""Native object-local vertex grid authoring over the qualified vector writer."""
from hashlib import sha256
import json
from .core import ImportError
from .model_json import translate_shape_vertices, export_shape_json, import_shape_json
from .model_authoring import replace_model_content


def snap_shape_vertices(original, effective, expected_sha256, object_index, indices, axes, spacing):
    if (not isinstance(axes, list) or not 1 <= len(axes) <= 3 or
            any(axis not in ('x','y','z') for axis in axes) or len(set(axes)) != len(axes) or
            type(spacing) is not int or not 1 <= spacing <= 32768):
        raise ImportError('Vertex grid requires unique X/Y/Z axes and integer spacing1..32768')
    qualified = translate_shape_vertices(original, effective, expected_sha256, object_index, indices, [0,0,0])
    document = json.loads(export_shape_json(qualified)); vertices = document['objects'][object_index]['vertices']
    for index in indices:
        for axis in axes:
            a = ('x','y','z').index(axis); value = vertices[index][a]
            snapped = ((2 * abs(value) + spacing) // (2 * spacing)) * spacing * (-1 if value < 0 else 1)
            if not -32768 <= snapped <= 32767:
                raise ImportError('Vertex grid exceeds signed16; nothing was applied')
            vertices[index][a] = snapped
    candidate = import_shape_json(effective, expected_sha256, json.dumps(document).encode())[0]
    return replace_model_content(original, sha256(original).hexdigest(), candidate, allow_normal_references=True)[0]
