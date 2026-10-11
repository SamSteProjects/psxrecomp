"""Fresh World object bind to private source script graph, without execution."""
from base64 import b64decode
import json
from importer.pipeline import _disc_context
from importer.actor_runtime_capacity import qualify_actor_pool
from importer.worldmap_object_script import inspect_object_script
from .worldmap_object_bind import inspect as inspect_bind
from .worldmap_placement_allocation import _fresh
from .project import ProjectError


def inspect(project,scene,key,entity_id):
    binding=inspect_bind(project,scene,key,entity_id)
    with _disc_context(project.disc_path) as (image,digest,_,archive):
        if digest!=binding['man_source']['disc_sha256']:
            raise ProjectError('World object script executable belongs to another disc')
        proof=qualify_actor_pool(image.read_file(image.find('SCUS_942.54')))
    consumer=next(w for w in proof['functions'] if w['address']=='0x8003A55C')
    result=dict(schema_version='legaia.worldmap-object-script.v1',project_path=str(project.root),
        scene=scene,source_key=key,entity_id=entity_id,binding=binding,
        consumer=dict(executable_sha256=proof['executable_sha256'],function=consumer,
            script_base_store='0x8003A8AC',script_pc_store='0x8003A8B4'),
        inspection=inspect_object_script(binding['bind'],b64decode(binding['source_witness']['man_base64']),scene),
        read_only=True,project_changed=False,gameplay_verified=False)
    if len(json.dumps(result,allow_nan=False).encode('utf-8'))>32*1024*1024:
        raise ProjectError('World object script graph exceeds its private response budget')
    _fresh(project,key)
    return result
