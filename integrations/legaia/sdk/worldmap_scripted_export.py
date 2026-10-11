"""Private Current scripted World scene exports; no game or project mutation."""
from base64 import b64decode,b64encode
import json
from importer.export import write_encoded_glb
from importer.worldmap_export import encode_worldmap_glb,MAX_WORLDMAP_GLB_BYTES
from importer.worldmap_scripted_export import qualify_source
from .project import ProjectError
from .worldmap_authoring import state_key
from .worldmap_scripted_placement_scene import inspect
from .worldmap_export import MAX_RESPONSE_BYTES


def export(project,scene,key,scope,entity_id=None):
    if scope not in ('source-scene','ground','selected') or (scope=='selected')!=(entity_id is not None):
        raise ProjectError('Choose scene, ground or selected Current scripted export')
    result=inspect(project,scene,key)
    metadata=qualify_source(result,key)
    # Inspection transports pixels as base64; the shared native exporter consumes
    # verified byte pixels and rechecks dimensions, attributes and export budgets.
    previews=[result['preview']]+[a['preview'] for a in result['scene_graph']['assets']]
    seen=set()
    for preview in previews:
        if id(preview) in seen:continue
        seen.add(id(preview))
        for texture in preview.get('textures',[]):
            for name in ('rgba','stp'):
                if name+'_base64' in texture:texture[name]=b64decode(texture.pop(name+'_base64'),validate=True)
    raw,audit=encode_worldmap_glb(result,key,scope,entity_id,placement_authoring=metadata)
    response=dict(schema_version='legaia.worldmap-scripted-export-response.v1',scene=scene,source_key=key,
        representation=result['representation'],scope=scope,entity_id=entity_id,gameplay_verified=False,project_changed=False,
        glb_base64=b64encode(raw).decode('ascii'))
    if len(raw)>MAX_WORLDMAP_GLB_BYTES or len(json.dumps(dict(response,audit=audit),allow_nan=False).encode())+65536>MAX_RESPONSE_BYTES:
        raise ProjectError('Scripted World export exceeds its download budget')
    if project.mode!='edit' or state_key(project)!=key:raise ProjectError('Scripted World export source changed')
    return {**write_encoded_glb(raw,audit,project.root/'Exports',prefix='scene'),**response}
