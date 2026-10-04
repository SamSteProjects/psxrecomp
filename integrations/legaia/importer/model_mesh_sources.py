"""Stable depth-first source order for a static glTF scene forest."""
from .core import ImportError
from .model_mesh_scene import scene_source
from .model_mesh_transform import node_transform,compose_node_transform


def _dynamic_targets(doc,node_count):
    """Resolve activity ownership only; excluded animation payloads are not decoded."""
    animations,skins=(doc.get(key,[]) for key in ('animations','skins'))
    if any(not isinstance(rows,list) or len(rows)>64 for rows in (animations,skins)):
        raise ImportError('Mesh scene animation/skin inventories exceed their bounded slots')
    if any(not isinstance(skin,dict) for skin in skins):
        raise ImportError('Mesh scene excluded skin inventory is malformed')
    targets=set();count=0
    for animation in animations:
        if not isinstance(animation,dict) or 'extensions' in animation:
            raise ImportError('Mesh scene animation activity cannot be resolved')
        channels,samplers=(animation.get(key) for key in ('channels','samplers'))
        if any(not isinstance(rows,list) or not 1<=len(rows)<=256 for rows in (channels,samplers)):
            raise ImportError('Mesh scene animation activity exceeds its bounded channels')
        count+=len(channels)
        if count>256 or any(not isinstance(sampler,dict) for sampler in samplers):
            raise ImportError('Mesh scene animation activity exceeds its bounded channels')
        for channel in channels:
            if not isinstance(channel,dict) or 'extensions' in channel:
                raise ImportError('Mesh scene animation channel ownership cannot be resolved')
            target=channel.get('target');sampler=channel.get('sampler')
            if (type(sampler) is not int or not 0<=sampler<len(samplers)
                    or not isinstance(target,dict) or 'extensions' in target
                    or type(target.get('node')) is not int or not 0<=target['node']<node_count
                    or target.get('path') not in ('translation','rotation','scale','weights')):
                raise ImportError('Mesh scene animation target ownership cannot be resolved')
            targets.add(target['node'])
    return targets,len(animations),len(skins)


def mesh_sources(doc,scene_index=None,*,allow_empty=False,with_scope=False):
    nodes,meshes,scenes=(doc.get(key) for key in ('nodes','meshes','scenes'))
    if any(not isinstance(rows,list) or not 1<=len(rows)<=64 for rows in (nodes,meshes)) :
        raise ImportError('Mesh append requires bounded static mesh nodes')
    animated,animation_count,skin_count=_dynamic_targets(doc,len(nodes))
    selection=scene_source(doc,scene_index)
    roots=selection['scenes'][selection['scene_index']]['roots']
    if not isinstance(roots,list) or not (0 if allow_empty else 1)<=len(roots)<=64 or any(type(index) is not int or not 0<=index<len(nodes) for index in roots) or len(set(roots))!=len(roots):
        raise ImportError('Mesh append requires unique existing static scene roots')
    children=[];parents={}
    for index,node in enumerate(nodes):
        if not isinstance(node,dict):raise ImportError('Mesh scene node is malformed')
        row=node.get('children',[])
        if not isinstance(row,list) or len(row)>64 or any(type(child) is not int or not 0<=child<len(nodes) for child in row) or len(set(row))!=len(row):
            raise ImportError('Mesh scene child identities are invalid or duplicated')
        for child in row:
            if child in parents:raise ImportError('Mesh scene nodes must have one parent')
            parents[child]=index
        children.append(row)
    colors=[0]*len(nodes)
    def check(index):
        if colors[index]==1:raise ImportError('Mesh scene hierarchy contains a cycle')
        if colors[index]==2:return
        colors[index]=1
        for child in children[index]:check(child)
        colors[index]=2
    for index in range(len(nodes)):check(index)
    if any(root in parents for root in roots):raise ImportError('Mesh scene roots cannot also be children')
    sources=[];selected_nodes=[]
    def visit(node_index,path,parent=None):
        node=nodes[node_index]
        selected_nodes.append(node_index)
        if node_index in animated:
            raise ImportError(f'Selected mesh scene node {node_index} is animated; choose a static scene')
        if any(key in node for key in ('skin','weights','extensions')):
            raise ImportError('Mesh scene hierarchy must remain static and unskinned')
        local=node_transform(node);transform=local if parent is None else compose_node_transform(parent,local)
        path=path+[node_index]
        if 'mesh' in node:append_mesh(node_index,path,transform)
        for child in children[node_index]:visit(child,path,transform)
    def append_mesh(node_index,path,transform):
        node=nodes[node_index]
        if type(node['mesh']) is not int or not 0<=node['mesh']<len(meshes):raise ImportError('Mesh scene node references an unavailable mesh')
        mesh_index=node['mesh'];mesh=meshes[mesh_index]
        if not isinstance(mesh,dict) or any(key in mesh for key in ('weights','extensions')):
            raise ImportError('Mesh append cannot import morph weights or mesh extensions')
        primitives=mesh.get('primitives')
        if not isinstance(primitives,list) or not 1<=len(primitives)<=128 or len(sources)+len(primitives)>128:
            raise ImportError('Mesh append source sections exceed the native face budget')
        for primitive_index,primitive in enumerate(primitives):
            sources.append(dict(primitive_index=len(sources),node_index=node_index,mesh_index=mesh_index,
                mesh_primitive_index=primitive_index,node_transform=transform,primitive=primitive,
                **({'node_path':path} if len(path)>1 else {})))
    for root in roots:visit(root,[])
    if not sources and not allow_empty:raise ImportError('Mesh scene contains no selected static mesh sections')
    result=(sources,len(nodes)==len(meshes)==1 and roots==[0])
    scope=(dict(selected_nodes=selected_nodes,animated_nodes=sorted(animated),
                animation_count=animation_count,skin_count=skin_count)
           if animation_count or skin_count else None)
    return (*result,scope) if with_scope else result


def source_binding(source):
    return {key:value for key,value in source.items() if key!='primitive'}
