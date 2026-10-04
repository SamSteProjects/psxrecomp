"""Bake one static glTF node's TRS/column-major matrix into native mesh input.

glTF 2.0 node transformations: https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#transformations
"""
import math
from .core import ImportError

IDENTITY=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]


def node_transform(node,*,allow_shear=False):
    def values(key,default):
        value=node.get(key,default)
        if not isinstance(value,list) or len(value)!=len(default) or any(type(v) not in (int,float) or not math.isfinite(v) or abs(v)>1e9 for v in value):
            raise ImportError('Mesh node transform requires bounded finite numeric vectors')
        return value
    if 'matrix' in node:
        if any(key in node for key in ('translation','rotation','scale')):
            raise ImportError('Mesh node cannot combine matrix and TRS')
        matrix=values('matrix',IDENTITY)
        if any(matrix[i]!=0 for i in (3,7,11)) or matrix[15]!=1:
            raise ImportError('Mesh node matrix must be affine')
    else:
        translation=values('translation',[0,0,0]);scale=values('scale',[1,1,1]);quaternion=values('rotation',[0,0,0,1])
        length=math.hypot(*quaternion)
        if abs(length-1)>1e-5:raise ImportError('Mesh node rotation must be a unit quaternion')
        x,y,z,w=[v/length for v in quaternion]
        rotation=[[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                  [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                  [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]]
        matrix=[rotation[row][col]*scale[col] if row<3 else 0 for col in range(3) for row in range(4)]+translation+[1]
    columns=[[matrix[col*4+row] for row in range(3)] for col in range(3)]
    lengths=[math.hypot(*column) for column in columns]
    if any(length<1e-9 for length in lengths):raise ImportError('Mesh node scale must be nonsingular')
    if not allow_shear and any(abs(sum(a*b for a,b in zip(columns[i],columns[j])))>1e-6*lengths[i]*lengths[j] for i in range(3) for j in range(i)):
        raise ImportError('Mesh node matrix must decompose into TRS without shear')
    a,b,c=matrix[0],matrix[4],matrix[8];d,e,f=matrix[1],matrix[5],matrix[9];g,h,i=matrix[2],matrix[6],matrix[10]
    cofactors=[[e*i-f*h,f*g-d*i,d*h-e*g],[c*h-b*i,a*i-c*g,b*g-a*h],[b*f-c*e,c*d-a*f,a*e-b*d]]
    determinant=a*cofactors[0][0]+b*cofactors[0][1]+c*cofactors[0][2]
    if not math.isfinite(determinant) or determinant==0:raise ImportError('Mesh node transform is singular')
    normal_matrix=[[v/determinant for v in row] for row in cofactors]
    return dict(matrix=matrix,normal_matrix=normal_matrix,determinant=determinant,winding_reversed=determinant>0)


def compose_node_transform(parent,local):
    a,b=parent['matrix'],local['matrix']
    matrix=[sum(a[k*4+row]*b[col*4+k] for k in range(4)) for col in range(4) for row in range(4)]
    # TRS-valid ancestors can compose into a sheared world matrix. Baking uses
    # its full inverse transpose instead of discarding or decomposing the shear.
    return node_transform({'matrix':matrix},allow_shear=True)


def transform_point(transform,point):
    matrix=transform['matrix']
    result=[sum(matrix[col*4+row]*point[col] for col in range(3))+matrix[12+row] for row in range(3)]
    if any(not math.isfinite(v) for v in result):raise ImportError('Transformed mesh position is not finite')
    return result


def transform_normal(transform,normal):
    result=[sum(a*b for a,b in zip(row,normal)) for row in transform['normal_matrix']]
    if any(not math.isfinite(v) for v in result):raise ImportError('Transformed mesh normal is not finite')
    return result
