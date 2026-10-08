"""Bounded sequential vertex edits; intermediate native words stay detached."""
from hashlib import sha256
from .core import ImportError
from .model_json import (translate_shape_vertices, align_shape_vertices,
                         distribute_shape_vertices, scale_shape_vertices,
                         scale_shape_vertices_axes, rotate_shape_vertices,
                         rotate_shape_vertices_angle)
from .model_vertex_grid import snap_shape_vertices

OPERATIONS = {
    'translation': (translate_shape_vertices, ('offset',)),
    'alignment': (align_shape_vertices, ('axis', 'anchor')),
    'distribution': (distribute_shape_vertices, ('axis',)),
    'scaling': (scale_shape_vertices, ('percent', 'pivot')),
    'axis_scaling': (scale_shape_vertices_axes, ('percents', 'pivot')),
    'rotation': (rotate_shape_vertices, ('axis', 'quarter_turns', 'pivot')),
    'rotation_angle': (rotate_shape_vertices_angle, ('axis', 'angle_units', 'pivot')),
    'grid': (snap_shape_vertices, ('axes', 'spacing')),
}


def transform_shape_vertices_sequence(original, effective, expected_sha256,
                                      object_index, indices, steps):
    """Apply 1..16 operations to one selection, rounding at each native step."""
    if not isinstance(steps, list) or not 1 <= len(steps) <= 16:
        raise ImportError('Vertex transform sequence requires 1..16 steps')
    for step in steps:
        if (not isinstance(step, dict) or set(step) != {'operation', 'values'} or
                not isinstance(step['operation'], str) or step['operation'] not in OPERATIONS or
                not isinstance(step['values'], dict) or
                set(step['values']) != set(OPERATIONS[step['operation']][1])):
            raise ImportError('Vertex transform step requires a supported operation and exact values')
    candidate = translate_shape_vertices(original, effective, expected_sha256,
                                         object_index, indices, [0, 0, 0])
    for step in steps:
        operation, fields = OPERATIONS[step['operation']]
        candidate = operation(original, candidate, sha256(candidate).hexdigest(),
                              object_index, indices, *(step['values'][field] for field in fields))
    return candidate
