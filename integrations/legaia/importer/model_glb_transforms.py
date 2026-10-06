"""Bounded positive uniform model scale, composed with shared rigid GLB math."""
import math

from .animation_glb import (_nodes, _hierarchy_order, _rotate_vector,
                            _multiply_quaternions, _vector)
from .core import ImportError

MIN_SCALE = 1 / 1024
MAX_SCALE = 1024


def _scale(value):
    if not math.isfinite(value) or not MIN_SCALE <= value <= MAX_SCALE:
        raise ImportError('Model GLB local and composed uniform scale must be 1/1024..1024')
    return value


def static_model_hierarchy(doc, object_count):
    # Copy only nodes that are normalized here; source metadata remains immutable.
    normalized = dict(doc)
    normalized['nodes'] = [dict(node) for node in doc['nodes']]
    scales = {}
    for index, node in enumerate(normalized['nodes']):
        if 'matrix' in node:
            if any(key in node for key in ('translation', 'rotation', 'scale')):
                raise ImportError('Model GLB node matrices cannot be combined with TRS properties')
            matrix = _vector(node['matrix'], 16, 'model node matrix')
            lengths = [math.hypot(*matrix[start:start+3]) for start in (0, 4, 8)]
            scale = _scale(sum(lengths) / 3)
            if any(abs(length / scale - 1) > 1e-5 for length in lengths):
                raise ImportError('Model GLB requires positive uniform scale; nonuniform scale rejects')
            for start in (0, 4, 8):
                for axis in range(3): matrix[start+axis] /= scale
            node['matrix'] = matrix
        else:
            vector = _vector(node.get('scale', [1, 1, 1]), 3, 'model node scale')
            if vector[0] != vector[1] or vector[0] != vector[2]:
                raise ImportError('Model GLB requires positive uniform scale; nonuniform scale rejects')
            scale = _scale(vector[0])
            if 'scale' in node: node['scale'] = [1, 1, 1]
        scales[index] = scale
    mapping, static, parents = _nodes(normalized, object_count)
    poses = {}
    for index in _hierarchy_order(mapping, parents, 1):
        translation, rotation = static[index]
        scale = scales[index]
        parent = parents.get(index)
        if parent is not None:
            parent_t, parent_q, parent_s = poses[parent]
            scaled = [v * parent_s for v in translation]
            translated = _rotate_vector(parent_q, scaled)
            translation = [a+b for a,b in zip(parent_t, translated)]
            if any(not math.isfinite(v) for v in translation):
                raise ImportError('Model GLB hierarchy produced a nonfinite translation')
            rotation = _multiply_quaternions(parent_q, rotation)
            scale = _scale(scale * parent_s)
        poses[index] = (translation, rotation, scale)
    return mapping, poses
