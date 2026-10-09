"""Shared metadata projection of existing initial actor model/clip bindings."""
from copy import deepcopy


def initial_animation_identity(document, source):
    number = source['placement_fields'].get('animation_id')
    local = source['model_reference'].get('model_index')
    return dict(animation_asset_id=f"animation://{document['scene']['name']}/scene-anm/{number-1:04d}"
                if type(number) is int and 1 <= number <= 255 and type(local) is int and 0 <= local < 240 else None,
                initial_animation_id=number, donor_entity_id=source['semantic_id'])


def components(project, actor, document):
    from .actor_animation import source_actor
    identifier = actor['semantic_id']
    model = actor['model_reference']
    appearance = deepcopy(project.overrides.get(identifier, {}).get('ActorAppearance', {}))
    donor = project.appearance_source_actor(identifier)
    original_pair = dict(asset_id=model.get('asset_semantic_id'), animation_id=actor['placement_fields'].get('animation_id'))
    effective_pair = dict(asset_id=donor['model_reference'].get('asset_semantic_id'), animation_id=donor['placement_fields'].get('animation_id'))
    if appearance:
        effective_pair['donor_entity_id'] = donor['semantic_id']

    animation_actor = source_actor(project, identifier)
    allocated = project.overrides.get(identifier, {}).get('ActorAllocatedAnimation')
    effective_animation = (dict(animation_asset_id=f"animation://{document['scene']['name']}/authored-record/{allocated['record_id']}",
                                initial_animation_id=None, source_kind='allocated_record', record_id=allocated['record_id'])
                           if allocated else initial_animation_identity(document, animation_actor))
    return {
        'ActorAppearance': dict(imported=original_pair, authored=appearance, effective=effective_pair,
                                limitations=['Initial model/animation pair only; scripts may replace it. Script and gameplay compatibility remain unverified.']),
        'ModelRenderer': dict(asset_id=model.get('asset_semantic_id'), resolution_status=model.get('resolution_status')),
        'ActorAnimation': dict(imported=initial_animation_identity(document, actor), base=initial_animation_identity(document, donor),
                               authored=deepcopy(project.overrides.get(identifier, {}).get('ActorAnimation', {})), effective=effective_animation),
    }
