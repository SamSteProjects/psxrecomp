"""Bounded positive model scale with affine positions and normal directions."""
from dataclasses import dataclass
import math

from .animation_glb import (_nodes, _hierarchy_order, _rotate_vector,
                            _multiply_quaternions, _vector)
from .core import ImportError

MIN_SCALE = 1 / 1024
MAX_SCALE = 1024


def _scale(value):
    if not math.isfinite(value) or not MIN_SCALE <= value <= MAX_SCALE:
        raise ImportError('Model GLB local axes and composed scale bounds must be 1/1024..1024')
    return value


def _apply(matrix, value):
    return [sum(a*b for a,b in zip(row, value)) for row in matrix]


def _multiply(a, b):
    return tuple(tuple(sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)) for i in range(3))


def _cofactor(matrix):
    # inverse-transpose times positive determinant: the common factor cancels
    # when restoring the original raw normal magnitude.
    (a,b,c),(d,e,f),(g,h,i) = matrix
    result = ((e*i-f*h, f*g-d*i, d*h-e*g),
              (c*h-b*i, a*i-c*g, b*g-a*h),
              (b*f-c*e, c*d-a*f, a*e-b*d))
    determinant = a*result[0][0]+b*result[0][1]+c*result[0][2]
    if not math.isfinite(determinant) or determinant <= 0:
        raise ImportError('Model GLB composed transform is singular or reflected')
    return result


@dataclass(frozen=True)
class ModelPose:
    translation: tuple
    linear: tuple
    normal_matrix: tuple
    uniform_rotation: tuple | None
    scale_bounds: tuple

    def position(self, value):
        return [v+t for v,t in zip(_apply(self.linear, value), self.translation)]

    def normal(self, value):
        if self.uniform_rotation is not None:
            return _rotate_vector(self.uniform_rotation, value)
        magnitude = math.hypot(*value)
        if magnitude == 0:
            return [0, 0, 0]
        transformed = _apply(self.normal_matrix, value)
        length = math.hypot(*transformed)
        if not math.isfinite(length) or length == 0:
            raise ImportError('Model GLB inverse-transpose produced an invalid normal')
        return [v * (magnitude / length) for v in transformed]


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
            scale = [_scale(length) for length in lengths]
            for start, factor in zip((0, 4, 8), scale):
                for axis in range(3): matrix[start+axis] /= factor
            node['matrix'] = matrix
        else:
            vector = _vector(node.get('scale', [1, 1, 1]), 3, 'model node scale')
            scale = [_scale(value) for value in vector]
            if 'scale' in node: node['scale'] = [1, 1, 1]
        scales[index] = scale
    mapping, static, parents = _nodes(normalized, object_count)
    poses = {}
    for index in _hierarchy_order(mapping, parents, 1):
        translation, rotation = static[index]
        scale = scales[index]
        columns = [_rotate_vector(rotation, [scale[j] if axis == j else 0 for axis in range(3)]) for j in range(3)]
        linear = tuple(tuple(columns[j][i] for j in range(3)) for i in range(3))
        bounds = (min(scale), max(scale))
        uniform = tuple(rotation) if scale[0] == scale[1] == scale[2] else None
        parent = parents.get(index)
        if parent is not None:
            parent_pose = poses[parent]
            translated = _apply(parent_pose.linear, translation)
            translation = [a+b for a,b in zip(parent_pose.translation, translated)]
            if any(not math.isfinite(v) for v in translation):
                raise ImportError('Model GLB hierarchy produced a nonfinite translation')
            linear = _multiply(parent_pose.linear, linear)
            bounds = (_scale(bounds[0]*parent_pose.scale_bounds[0]),
                      _scale(bounds[1]*parent_pose.scale_bounds[1]))
            uniform = tuple(_multiply_quaternions(parent_pose.uniform_rotation, rotation)) if uniform is not None and parent_pose.uniform_rotation is not None else None
        poses[index] = ModelPose(tuple(translation), linear, _cofactor(linear), uniform, bounds)
    return mapping, poses
