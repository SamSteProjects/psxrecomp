"""Project-wide recorded initial clip assignments, never runtime residency."""
from copy import deepcopy
from .actor_asset_bindings import components, initial_animation_identity
from .npc_appearance import appearance_donor


def references(project):
    result=[]
    for scene,document in project.imports.items():
        for actor in document['actors']:
            identifier=actor['semantic_id'];bindings=components(project,actor,document)
            animation=bindings['ActorAnimation'];appearance=bindings['ActorAppearance']
            imported=animation['imported']['animation_asset_id'];effective=animation['effective']['animation_asset_id']
            for clip in dict.fromkeys((imported,effective)):
                if clip is None:continue
                result.append(dict(source_id=identifier,source_name='Actor '+identifier.rsplit('/',1)[-1],
                    target_id=clip,scene_id=scene,kind='initial_animation_assignment',
                    imported=clip==imported,effective=clip==effective,
                    imported_model_id=appearance['imported']['asset_id'] if clip==imported else None,
                    effective_model_id=appearance['effective']['asset_id'] if clip==effective else None,
                    effective_source=deepcopy(animation['effective']) if clip==effective else None,
                    runtime_binding='not_asserted'))
        actors={actor['semantic_id']:actor for actor in document['actors']}
        for identifier,draft in project.actor_drafts.items():
            if draft['scene_id']!=scene:continue
            donor=actors[appearance_donor(draft)];binding=initial_animation_identity(document,donor)
            if binding['animation_asset_id'] is None:continue
            result.append(dict(source_id=identifier,source_name=draft['name'],target_id=binding['animation_asset_id'],
                scene_id=scene,kind='draft_initial_animation_assignment',imported=False,effective=True,
                imported_model_id=None,effective_model_id=donor['model_reference'].get('asset_semantic_id'),
                effective_source=deepcopy(binding),runtime_binding='not_asserted'))
    return result
