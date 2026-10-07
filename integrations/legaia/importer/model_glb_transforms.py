"""Bounded signed model scale with affine positions and normal directions."""
from dataclasses import dataclass
import math

from .animation_glb import (_nodes, _hierarchy_order, _rotate_vector,
                            _multiply_quaternions, _vector)
from .core import ImportError

MIN_SCALE = 1 / 1024
MAX_SCALE = 1024


def _scale(value):
    if not math.isfinite(value) or not MIN_SCALE <= abs(value) <= MAX_SCALE:
        raise ImportError('Model GLB local axis magnitudes and composed scale bounds must be 1/1024..1024')
    return value


def _apply(matrix, value):
    return [sum(a*b for a,b in zip(row, value)) for row in matrix]


def _multiply(a, b):
    return tuple(tuple(sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)) for i in range(3))


def _composed_bounds(matrix):
    # One-sided Jacobi SVD works directly on columns, avoiding the cancellation
    # in eigenvalues of A^T A for strongly anisotropic transforms. Only singular
    # values are needed; the original matrix remains untouched.
    columns = [[matrix[i][j] for i in range(3)] for j in range(3)]
    if any(not math.isfinite(v) for column in columns for v in column):
        raise ImportError('Model GLB composed transform is nonfinite')
    for _ in range(32):
        changed = False
        for p, q in ((0, 1), (0, 2), (1, 2)):
            a, b = columns[p], columns[q]
            alpha = sum(v*v for v in a)
            beta = sum(v*v for v in b)
            gamma = sum(x*y for x, y in zip(a, b))
            if alpha == 0 or beta == 0:
                raise ImportError('Model GLB composed transform is singular')
            if abs(gamma) <= 1e-14 * math.sqrt(alpha) * math.sqrt(beta):
                continue
            tau = (beta - alpha) / (2 * gamma)
            tangent = math.copysign(1, tau) / (abs(tau) + math.hypot(1, tau))
            cosine = 1 / math.hypot(1, tangent)
            sine = cosine * tangent
            columns[p] = [cosine*x - sine*y for x, y in zip(a, b)]
            columns[q] = [sine*x + cosine*y for x, y in zip(a, b)]
            changed = True
        if not changed:
            break
    else:
        raise ImportError('Model GLB composed scale measurement did not converge')
    lengths = [math.hypot(*column) for column in columns]
    # Permit only floating-point boundary noise, not a wider authoring budget.
    # Absolute error follows the largest singular value, not the smallest;
    # a relative epsilon on the small axis falsely rejects rotated endpoints.
    tolerance = 64 * math.ulp(max(lengths))
    if min(lengths) < MIN_SCALE-tolerance or max(lengths) > MAX_SCALE+tolerance:
        raise ImportError('Model GLB composed singular scales must be 1/1024..1024')
    return (max(MIN_SCALE, min(lengths)), min(MAX_SCALE, max(lengths)))


def _cofactor(matrix):
    # inverse-transpose times absolute determinant: retain its sign when
    # restoring the original raw normal magnitude, including reflections.
    (a,b,c),(d,e,f),(g,h,i) = matrix
    result = ((e*i-f*h, f*g-d*i, d*h-e*g),
              (c*h-b*i, a*i-c*g, b*g-a*h),
              (b*f-c*e, c*d-a*f, a*e-b*d))
    determinant = a*result[0][0]+b*result[0][1]+c*result[0][2]
    if not math.isfinite(determinant) or determinant == 0:
        raise ImportError('Model GLB composed transform is singular')
    reflected = determinant < 0
    return (tuple(tuple(-v for v in row) for row in result) if reflected else result), reflected


@dataclass(frozen=True)
class ModelPose:
    translation: tuple
    linear: tuple
    normal_matrix: tuple
    uniform_rotation: tuple | None
    scale_bounds: tuple
    reflected: bool

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


def static_model_hierarchy(doc, object_count, object_node_indices=None):
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
            # Factor an odd reflection into the first signed scale so the
            # shared rigid matrix decoder still receives a proper rotation.
            linear = tuple(tuple(matrix[j*4+i] for j in range(3)) for i in range(3))
            _, reflected = _cofactor(linear)
            if reflected:
                scale[0] = -scale[0]
                for axis in range(3): matrix[axis] = -matrix[axis]
            node['matrix'] = matrix
        else:
            vector = _vector(node.get('scale', [1, 1, 1]), 3, 'model node scale')
            scale = [_scale(value) for value in vector]
            if 'scale' in node: node['scale'] = [1, 1, 1]
        scales[index] = scale
    mapping, static, parents, _rig = _nodes(normalized, object_count, object_node_indices)
    poses = {}
    for index in _hierarchy_order(mapping, parents, 1):
        translation, rotation = static[index]
        scale = scales[index]
        columns = [_rotate_vector(rotation, [scale[j] if axis == j else 0 for axis in range(3)]) for j in range(3)]
        linear = tuple(tuple(columns[j][i] for j in range(3)) for i in range(3))
        bounds = (min(abs(v) for v in scale), max(abs(v) for v in scale))
        uniform = tuple(rotation) if scale[0] == scale[1] == scale[2] and scale[0] > 0 else None
        parent = parents.get(index)
        if parent is not None:
            parent_pose = poses[parent]
            translated = _apply(parent_pose.linear, translation)
            translation = [a+b for a,b in zip(parent_pose.translation, translated)]
            if any(not math.isfinite(v) for v in translation):
                raise ImportError('Model GLB hierarchy produced a nonfinite translation')
            linear = _multiply(parent_pose.linear, linear)
            bounds = _composed_bounds(linear)
            uniform = tuple(_multiply_quaternions(parent_pose.uniform_rotation, rotation)) if uniform is not None and parent_pose.uniform_rotation is not None else None
        normal_matrix, reflected = _cofactor(linear)
        poses[index] = ModelPose(tuple(translation), linear, normal_matrix, uniform, bounds, reflected)
    return mapping, poses
