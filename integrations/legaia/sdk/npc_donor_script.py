"""Retail donor script inspection for an authored NPC; never generated/live code."""
from copy import deepcopy
from .project import ProjectError
from .project_copy import source_key

def inspect(project,entity_id):
    draft=project.actor_drafts.get(entity_id) if isinstance(entity_id,str) else None
    if not isinstance(draft,dict) or draft.get('scene_id')!=project.active_scene:
        raise ProjectError('Choose an authored NPC in the active imported scene')
    project._validate_actor_draft(entity_id,draft)
    if not project.disc_path:raise ProjectError('NPC donor script inspection requires the project retail disc')
    key=source_key(project);captured=deepcopy(draft)
    donor=next((a for a in project.imports[project.active_scene]['actors'] if a['semantic_id']==draft['donor_entity_id']),None)
    if donor is None:raise ProjectError('NPC retail donor is unavailable')
    from importer.script_inspection import inspect_actor_script
    inspection=inspect_actor_script(project.disc_path,project.imports[project.active_scene]['scene']['name'],donor)
    if source_key(project)!=key:raise ProjectError('Project changed during NPC donor script inspection')
    return dict(schema_version='legaia.npc-donor-script.v1',project_source_key=key,scene_id=project.active_scene,entity_id=entity_id,draft=captured,donor_entity_id=donor['semantic_id'],donor_source_record=deepcopy(donor['source_record']),inspection=inspection,representation='retail_donor_source',generated_code=False,runtime_binding='not_asserted',gameplay_verified=False)
