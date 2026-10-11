"""Complete Current kingdom MAN witnesses for placement scene admission."""
from base64 import b64encode
from copy import deepcopy
from hashlib import sha256
import json
from importer.script_inspection import inspect_record
from .project import ProjectError
from .worldmap_script_operands import context,_options,_fresh,owner,COMPONENTS
from .worldmap_script_branches import owner as branch_owner,COMPONENT as BRANCH_COMPONENT


def inspect(project,scene,key):
    _fresh(project,key)
    inputs=context(project,scene)
    man,rows,provenance,_,_,_,_,_,current,_=inputs
    components=deepcopy(project.overrides.get(owner(scene),{}))
    branches=deepcopy(project.overrides.get(branch_owner(scene),{}))
    heights=deepcopy(project.overrides.get('scene://'+scene,{}).get('FloorHeights'))
    if heights:
        project._validate_floor_heights('scene://'+scene,heights)
        from .floor_heights import compose
        current,_=compose(project,'scene://'+scene,man,current)
    scripts=set()
    for name,binding in components.items():
        if name not in COMPONENTS:raise ProjectError('Current MAN has an unsupported script component')
        scripts.update(binding['entries'])
    if branches:scripts.update(branches[BRANCH_COMPONENT]['entries'])
    witnesses=[]
    for script in sorted(scripts):
        row=rows[script];s=row['source_record'];record=man[s['byte_offset']:s['byte_offset']+s['byte_length']]
        witnesses.append(dict(record=dict(id=script,kind='script',source_record=deepcopy(s),entry_pc=row['entry_pc'],source_instance_ids=deepcopy(row['source_instance_ids'])),
            source=_options(project,script,key,inputs),retail_graph=inspect_record(record,row['entry_pc'],base_offset=s['byte_offset'])))
    result=dict(schema_version='legaia.worldmap-current-man.v1',scene=scene,source_key=key,project_path=str(project.root),
        source_record=provenance,retail_man_base64=b64encode(man).decode('ascii'),current_man_base64=b64encode(current).decode('ascii'),
        current_man_sha256=sha256(current).hexdigest(),script_components=components,branch_components=branches,
        floor_heights=heights,records=witnesses,read_only=True,project_changed=False,gameplay_verified=False)
    _fresh(project,key)
    if len(json.dumps(result,allow_nan=False).encode('utf-8'))>16*1024*1024:
        raise ProjectError('Current MAN witness exceeds its response budget')
    return result
