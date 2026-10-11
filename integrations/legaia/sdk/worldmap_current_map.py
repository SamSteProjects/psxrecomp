"""Full native MAP/coauthor witnesses for scripted scene admission."""
from base64 import b64encode
from copy import deepcopy
from hashlib import sha256
import json
from .worldmap_scripted_placement_allocation import _inputs,_fresh
from .worldmap_scripted_placement_binding import compose,owner,COMPONENT,read_base
from .worldmap_placements import owner as transform_owner,COMPONENT as TRANSFORM
from .worldmap_placement_allocation_binding import owner as decoration_owner,COMPONENT as DECORATION
from .project import ProjectError

MAP_COMPONENTS=('Environment','Collision','FloorTiers','RegionBounds','TriggerCells','TriggerScripts')


def inspect(project,scene,key):
    _fresh(project,key)
    raw,provenance,floor,normal,_,fallback,man,current_man,_,_=_inputs(project,scene,key,include_scripted=False)
    current,_=compose(project,scene,provenance,normal,fallback,man,current_man,floor)
    binding=project.overrides.get(owner(scene),{}).get(COMPONENT)
    encode=lambda data:b64encode(data).decode('ascii')
    result=dict(schema_version='legaia.worldmap-current-map.v1',scene=scene,source_key=key,project_path=str(project.root),source_record=provenance,
        retail_map_base64=encode(raw),normal_map_base64=encode(normal),current_map_base64=encode(current),
        normal_map_sha256=sha256(normal).hexdigest(),current_map_sha256=sha256(current).hexdigest(),
        fallback_base64=encode(fallback),source_man_sha256=sha256(man).hexdigest(),current_man_sha256=sha256(current_man).hexdigest(),
        scene_components={k:deepcopy(v) for k,v in project.overrides.get('scene://'+scene,{}).items() if k in MAP_COMPONENTS},
        transform_binding=deepcopy(project.overrides.get(transform_owner(scene),{}).get(TRANSFORM)),
        decoration_binding=deepcopy(project.overrides.get(decoration_owner(scene),{}).get(DECORATION)),
        scripted_binding=deepcopy(binding),retained_base_map_base64=encode(read_base(project,binding)) if binding else None,
        read_only=True,project_changed=False,gameplay_verified=False)
    _fresh(project,key)
    if len(json.dumps(result,allow_nan=False).encode('utf-8'))>4*1024*1024:raise ProjectError('Current MAP witness exceeds its response budget')
    return result
