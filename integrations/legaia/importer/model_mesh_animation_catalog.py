"""Source names and bounded ownership only; clip payloads are not sampled."""
from hashlib import sha256
from .animation_glb import _read_glb
from .core import ImportError
from .model_mesh_sources import _dynamic_targets

def inspect_mesh_animations(content):
    doc,_=_read_glb(content);nodes=doc.get('nodes')
    if not isinstance(nodes,list) or not 1<=len(nodes)<=64 or any(not isinstance(node,dict) for node in nodes):raise ImportError('Mesh animation catalog requires bounded source nodes')
    _dynamic_targets(doc,len(nodes));clips=[]
    for index,animation in enumerate(doc.get('animations',[])):
        name=animation.get('name')
        if name is not None and (not isinstance(name,str) or len(name)>512):raise ImportError('Mesh animation clip name exceeds its source label budget')
        channels=animation['channels']
        clips.append(dict(animation_index=index,name=name,channel_count=len(channels),sampler_count=len(animation['samplers']),target_nodes=sorted({c['target']['node'] for c in channels}),target_paths=sorted({c['target']['path'] for c in channels})))
    return dict(schema_version='legaia.model-mesh-animation-catalog.v1',glb_sha256=sha256(content).hexdigest(),byte_length=len(content),node_count=len(nodes),clips=clips,payloads_decoded=False,sampling_qualified=False,project_changed=False)
