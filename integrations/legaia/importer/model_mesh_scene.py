"""Qualified scene selection inside a static GLB source file."""
from .core import ImportError
from hashlib import sha256
from .animation_glb import _read_glb


def scene_source(doc,selected=None):
    scenes=doc.get('scenes');nodes=doc.get('nodes')
    if not isinstance(scenes,list) or not 1<=len(scenes)<=64 or not isinstance(nodes,list) or len(nodes)>64:
        raise ImportError('Mesh append requires bounded static source scenes')
    default=doc.get('scene',0)
    if type(default) is not int or not 0<=default<len(scenes):
        raise ImportError('Mesh source default scene is unavailable')
    index=default if selected is None else selected
    if type(index) is not int or not 0<=index<len(scenes):
        raise ImportError('Choose an existing GLB source scene')
    rows=[]
    for ordinal,scene in enumerate(scenes):
        if not isinstance(scene,dict):raise ImportError('Mesh source scene is malformed')
        roots=scene.get('nodes',[]);name=scene.get('name')
        if (not isinstance(roots,list) or len(roots)>64
                or any(type(root) is not int or not 0<=root<len(nodes) for root in roots) or len(set(roots))!=len(roots)):
            raise ImportError('Mesh source scene roots are invalid or duplicated')
        if name is not None and (not isinstance(name,str) or len(name)>256 or any(ord(c)<32 for c in name)):
            raise ImportError('Mesh source scene name is invalid')
        if scene.get('extensions'):raise ImportError('Mesh source scene extensions are unsupported')
        rows.append(dict(scene_index=ordinal,name=name,roots=roots))
    return dict(scene_index=index,default_scene_index=default,scenes=rows)


def inspect_source_scenes(content):
    """Scene labels/roots only; unsupported geometry must not trap file selection."""
    doc,_=_read_glb(content)
    return dict(schema_version='legaia.model-mesh-scenes.v1',glb_sha256=sha256(content).hexdigest(),
        scene_source=scene_source(doc),read_only=True,geometry_qualified=False)
