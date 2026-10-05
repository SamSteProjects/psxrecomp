"""Readonly retained initial-clip relationships, using the native assignment verifier."""
from copy import copy, deepcopy
from .project import ProjectError, digest

def bindings(project, scene):
    from .allocated_animation_assignment import validate_binding, review
    from .scene_preview import source_key
    ledger=project.overrides.get(scene,{}).get('AnimationRecords')
    result=[]
    for owner,components in sorted(project.overrides.items()):
        value=components.get('ActorAllocatedAnimation')
        if value is None or value.get('scene_id')!=scene:continue
        entry=validate_binding(project,owner,value)
        # The review is readonly. Its Edit prerequisite is for authoring UX;
        # use a separate view to qualify the same source in observation mode.
        view=copy(project);view.active_scene=scene;view.mode='edit'
        checked=review(view,owner,value['record_id'],source_key(view))
        if checked['proposed_component']!=value or checked['record_id']!=entry['record_id']:
            raise ProjectError('Allocated animation reference differs from current verified assignment')
        proof=dict(record_id=entry['record_id'],record_sha256=entry['record_sha256'],ledger_sha256=digest(ledger),
                   bank_sha256=checked['effective_bank_sha256'],model_id=entry['donor_asset_id'],
                   model_source_entity_id=entry['model_source_entity_id'],channel_owner_entity_id=entry['channel_owner_entity_id'],
                   native_record_index=checked['native_record_index'],native_animation_id=checked['native_animation_id'],
                   frame_count=checked['frame_count'],object_count=checked['object_count'])
        result.append(dict(owner_id=owner,animation_id=checked['animation_id'],model_id=entry['donor_asset_id'],proof=proof,
                           assignment_proof={**deepcopy(proof),'assignment_owner_id':owner,'assignment_sha256':digest(value)}))
    return result
