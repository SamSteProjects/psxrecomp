"""Bake one saved glTF morph pose before skin or node transforms."""
import math
from .core import ImportError
from .model_mesh_sparse import morph_delta

MAX_TARGETS=8


def morph_binding(mesh,node):
    counts=[]
    for primitive in mesh['primitives']:
        if not isinstance(primitive,dict):raise ImportError('Mesh primitive is malformed')
        targets=primitive.get('targets',[])
        if not isinstance(targets,list) or ('targets' in primitive and not targets) or len(targets)>MAX_TARGETS:
            raise ImportError('Static morph pose requires 1 through 8 targets per primitive')
        counts.append(len(targets))
    if len(set(counts))!=1:raise ImportError('Mesh primitives must have the same morph target count and order')
    count=counts[0]
    for owner in (mesh,node):
        if 'weights' in owner and (not isinstance(owner['weights'],list) or len(owner['weights'])!=count or not count
                or any(type(w) not in (int,float) or not math.isfinite(w) or abs(w)>1e6 for w in owner['weights'])):
            raise ImportError('Static morph weights must match the target count and be finite within -1000000..1000000')
    if not count:return None
    source='node' if 'weights' in node else 'mesh' if 'weights' in mesh else 'zero'
    weights=node['weights'] if source=='node' else mesh['weights'] if source=='mesh' else [0]*count
    return dict(target_count=count,weight_source=source,weights=list(weights))


def bake_morph(reader,source,attrs,positions,normals):
    binding=source.get('morph_bake')
    if binding is None:return positions,normals,()
    if len(positions)>8192:raise ImportError('Static morph source exceeds 8192 vertices')
    positions=[list(row) for row in positions]
    normals=None if normals is None else [list(row) for row in normals]
    position_owners=[]
    for target,weight in zip(source['primitive']['targets'],binding['weights']):
        if (not isinstance(target,dict) or not target or not set(target)<={'POSITION','NORMAL','TANGENT'}
                or not set(target)<=set(attrs)):
            raise ImportError('Static morph targets require existing POSITION, NORMAL or TANGENT base attributes only')
        position_owners.append(target.get('POSITION'))
        for name,index in target.items():
            delta=morph_delta(reader,index,len(positions))
            if len(delta)!=len(positions):raise ImportError('Static morph target attribute counts differ from the base mesh')
            values=positions if name=='POSITION' else normals if name=='NORMAL' else None
            # Tangents have no native packet representation; still qualify their deltas.
            if values is None:continue
            for row,offset in zip(values,delta):
                for axis in range(3):
                    row[axis]+=weight*offset[axis]
                    if not math.isfinite(row[axis]):raise ImportError('Static morph pose exceeds finite coordinates')
    return positions,normals,tuple(position_owners)
