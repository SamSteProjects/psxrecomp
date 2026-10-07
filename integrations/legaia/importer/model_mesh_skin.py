"""Bounded glTF static linear-blend skin pose; no runtime skin or animation.

Khronos glTF 2.0 sections 3.7.3 and 5.28 define joint/weight ownership.
"""
import math
from .core import ImportError
from .model_mesh_transform import IDENTITY,node_transform,compose_node_transform


def skin_binding(doc,node,world,parents,selected):
    index=node.get('skin');skins=doc.get('skins',[])
    if type(index) is not int or not 0<=index<len(skins):raise ImportError('Static skin references an unavailable skin')
    skin=skins[index]
    if not isinstance(skin,dict) or 'extensions' in skin:raise ImportError('Static skin extensions are unsupported')
    joints=skin.get('joints')
    if not isinstance(joints,list) or not 1<=len(joints)<=64 or any(type(j) is not int or j not in selected for j in joints) or len(set(joints))!=len(joints):raise ImportError('Static skin requires unique joints in the selected static scene')
    def ancestry(j):
        result=[j]
        while j in parents:j=parents[j];result.append(j)
        return result
    common=set(ancestry(joints[0]))
    for joint in joints[1:]:common.intersection_update(ancestry(joint))
    if not common:raise ImportError('Static skin joints require a common scene root')
    skeleton=skin.get('skeleton')
    if 'skeleton' in skin and (type(skeleton) is not int or skeleton not in common):raise ImportError('Static skin skeleton must be a common joint ancestor')
    accessor=skin.get('inverseBindMatrices')
    if 'inverseBindMatrices' in skin and (type(accessor) is not int or accessor<0):raise ImportError('Static skin inverse-bind accessor is invalid')
    return dict(skin_index=index,joint_nodes=list(joints),inverse_bind_accessor=accessor),[world[j] for j in joints]


def skin_vertex_transforms(reader,source,attrs,count):
    binding=source.get('skin_bake')
    keys={key for key in attrs if key.startswith(('JOINTS_','WEIGHTS_'))}
    if binding is None:
        if keys:raise ImportError('Skin attributes require a selected static skin owner')
        return None
    if count>8192:raise ImportError('Static skin POSITION count exceeds the bounded 8192-vertex bake')
    sets=[i for i in range(8) if f'JOINTS_{i}' in attrs]
    if not sets or sets!=list(range(len(sets))) or keys!={f'{kind}_{i}' for i in sets for kind in ('JOINTS','WEIGHTS')}:raise ImportError('Static skin requires consecutive paired JOINTS/WEIGHTS sets (0..7)')
    joints=binding['joint_nodes'];matrices=[IDENTITY]*len(joints)
    if binding['inverse_bind_accessor'] is not None:
        matrices=reader.read(binding['inverse_bind_accessor'],16,'skin inverse-bind matrices',matrix=True)
        if len(matrices)<len(joints):raise ImportError('Static skin inverse-bind count is shorter than its joints')
    transforms=[]
    for world,matrix in zip(source['_skin_world'],matrices):
        inverse=node_transform({'matrix':list(matrix)},allow_shear=True)
        transforms.append(compose_node_transform(world,inverse)['matrix'])
    influences=[[] for _ in range(count)]
    for index in sets:
        rows=[]
        for kind in ('JOINTS','WEIGHTS'):
            accessor=attrs[f'{kind}_{index}']
            if type(accessor) is not int or not 0<=accessor<len(reader.accessors) or not isinstance(reader.accessors[accessor],dict):raise ImportError('Static skin attribute accessor is invalid')
            spec=reader.accessors[accessor];component=spec.get('componentType');normalized=spec.get('normalized',False)
            view=spec.get('bufferView')
            if type(view) is not int or not 0<=view<len(reader.views) or not isinstance(reader.views[view],dict):raise ImportError('Static skin vertex buffer view is invalid')
            offsets=[reader.views[view].get('byteOffset',0),spec.get('byteOffset',0)]
            if any(type(offset) is not int or offset<0 for offset in offsets) or sum(offsets)%4:raise ImportError('Static skin vertex attributes require four-byte alignment')
            if kind=='JOINTS':
                if component not in (5121,5123) or normalized is not False:raise ImportError('Skin JOINTS require unnormalized unsigned byte/short components')
                values=reader.read(accessor,4,'skin joints',unsigned=True)
            else:
                if not (component==5126 and normalized is False or component in (5121,5123) and normalized is True):raise ImportError('Skin WEIGHTS require floats or normalized unsigned byte/short components')
                values=reader.read(accessor,4,'skin weights',normalized=normalized)
            if len(values)!=count:raise ImportError('Static skin attributes must match POSITION count')
            rows.append(values)
        for vertex,(ids,weights) in enumerate(zip(*rows)):
            if any(not 0<=j<len(joints) for j in ids) or any(not 0<=w<=1 for w in weights):raise ImportError('Static skin joint index or weight exceeds its range')
            influences[vertex].extend((j,w) for j,w in zip(ids,weights) if w)
    result=[]
    for row in influences:
        total=math.fsum(w for _,w in row)
        if not row or len({j for j,_ in row})!=len(row) or abs(total-1)>2e-7*len(row):raise ImportError('Static skin weights must sum to one with unique nonzero joint owners')
        # Renormalize permitted float/normalized-component error before translations.
        matrix=[math.fsum(transforms[j][i]*w/total for j,w in row) for i in range(16)]
        matrix[3]=matrix[7]=matrix[11]=0;matrix[15]=1
        result.append(node_transform({'matrix':matrix},allow_shear=True))
    return result
