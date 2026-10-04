"""Stable source order for static root mesh nodes in one glTF scene."""
from .core import ImportError
from .model_mesh_transform import node_transform


def mesh_sources(doc):
    if doc.get('animations') or doc.get('skins'):
        raise ImportError('Mesh append requires static geometry without skinning or animation')
    nodes,meshes,scenes=(doc.get(key) for key in ('nodes','meshes','scenes'))
    if any(not isinstance(rows,list) or not 1<=len(rows)<=64 for rows in (nodes,meshes)) or not isinstance(scenes,list) or len(scenes)!=1:
        raise ImportError('Mesh append requires one scene and bounded static mesh nodes')
    if not isinstance(scenes[0],dict) or type(doc.get('scene',0)) is not int or doc.get('scene',0)!=0:
        raise ImportError('Mesh append requires its sole default scene')
    roots=scenes[0].get('nodes')
    if not isinstance(roots,list) or not 1<=len(roots)<=64 or any(type(index) is not int or not 0<=index<len(nodes) for index in roots) or len(set(roots))!=len(roots):
        raise ImportError('Mesh append requires unique existing static scene roots')
    sources=[]
    for node_index in roots:
        node=nodes[node_index]
        if not isinstance(node,dict) or type(node.get('mesh')) is not int or not 0<=node['mesh']<len(meshes) or any(key in node for key in ('skin','weights','children','extensions')):
            raise ImportError('Mesh append root must own an unskinned mesh without children')
        mesh_index=node['mesh'];mesh=meshes[mesh_index]
        if not isinstance(mesh,dict) or any(key in mesh for key in ('weights','extensions')):
            raise ImportError('Mesh append cannot import morph weights or mesh extensions')
        primitives=mesh.get('primitives')
        if not isinstance(primitives,list) or not 1<=len(primitives)<=128 or len(sources)+len(primitives)>128:
            raise ImportError('Mesh append source sections exceed the native face budget')
        transform=node_transform(node)
        for primitive_index,primitive in enumerate(primitives):
            sources.append(dict(primitive_index=len(sources),node_index=node_index,mesh_index=mesh_index,
                mesh_primitive_index=primitive_index,node_transform=transform,primitive=primitive))
    return sources,len(nodes)==len(meshes)==1 and roots==[0]


def source_binding(source):
    return {key:value for key,value in source.items() if key!='primitive'}
