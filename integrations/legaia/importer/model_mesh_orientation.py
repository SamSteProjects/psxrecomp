"""Explicit editor import orientation in native coordinates; no rig inference."""
import math
from .core import ImportError

def mesh_source_rotation(value):
    if (not isinstance(value,(list,tuple)) or len(value)!=3 or
            any(type(n) not in (int,float) or not -360<=n<=360 or not math.isfinite(n) for n in value)):
        raise ImportError('Native mesh rotation requires three finite XYZ degree values from -360 through 360')
    return [float(n) for n in value]

def rotation_matrix(rotation):
    """Active right-handed native-axis rotation: X, then Y, then Z (Rz Ry Rx)."""
    def trig(value):
        result=[math.cos(math.radians(value)),math.sin(math.radians(value))]
        return [0.0 if abs(n)<1e-15 else (1.0 if abs(n-1)<1e-15 else (-1.0 if abs(n+1)<1e-15 else n)) for n in result]
    (cx,sx),(cy,sy),(cz,sz)=[trig(value) for value in rotation]
    return [[cz*cy,cz*sy*sx-sz*cx,cz*sy*cx+sz*sx],
            [sz*cy,sz*sy*sx+cz*cx,sz*sy*cx-cz*sx],
            [-sy,cy*sx,cy*cx]]

def rotate_native(matrix,point):
    return [sum(row[a]*point[a] for a in range(3)) for row in matrix]
