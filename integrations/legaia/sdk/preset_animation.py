"""Compose frozen preset components before proving an initial clip assignment."""
from copy import copy, deepcopy

from .project import ProjectError

ANIMATED_SCOPE = 'authored-actor-preset-v2'
COMBINED_SCOPES = {'authored-actor-preset-v1', ANIMATED_SCOPE}


def detached(project, entity_id, components):
    view = copy(project)
    view.overrides = deepcopy(project.overrides)
    view.overrides[entity_id] = deepcopy(components)
    return view


def validate_frozen(project, template, verify_disc=False):
    """A saved clip belongs to imported evidence, never mutable source overrides."""
    from .actor_animation import validate
    component = template['components'].get('ActorAnimation')
    if component is None:
        return
    source = template['source']
    document = project.imports.get(source['scene_id'])
    if not document or not any(a['semantic_id'] == source['entity_id'] for a in document['actors']):
        raise ProjectError('Animation preset requires its imported source scene and actor')
    if not isinstance(component, dict):
        raise ProjectError('Animation preset requires an exact imported clip witness')
    witness = component.get('donor_entity_id')
    if not any(a['semantic_id'] == witness for a in document['actors']):
        raise ProjectError('Animation preset witness must belong to its source scene')
    # Without a captured appearance the clip is portable within its proven model;
    # a target's final appearance is checked separately during proposal review.
    subject = source['entity_id'] if 'ActorAppearance' in template['components'] else witness
    frozen = {key: deepcopy(value) for key, value in template['components'].items()
              if key in {'ActorAppearance', 'ActorAnimation'}}
    view = detached(project, subject, frozen)
    validate(view, subject, component, verify_disc=verify_disc)


def compose(project, entity_id, captured, verify_disc=False):
    """Return one coherent proposal, preserving every omitted component."""
    from .actor_animation import options, validate
    before = deepcopy(project.overrides.get(entity_id))
    after = deepcopy(before or {})
    if 'Transform' in captured:
        after.setdefault('Transform', {}).setdefault('position', {}).update(captured['Transform']['position'])
    for key in ('ActorAppearance', 'ActorAnimation'):
        if key in captured:
            after[key] = deepcopy(captured[key])
    if 'ActorAppearance' in after:
        project._appearance_binding(entity_id, after['ActorAppearance'])
    view = detached(project, entity_id, after)
    if 'ActorAnimation' in after:
        validate(view, entity_id, after['ActorAnimation'])
    animation = None
    if verify_disc and ('ActorAnimation' in captured or 'ActorAnimation' in after):
        final = options(view, entity_id)
        if not final['supported']:
            raise ProjectError(final['reason'] or 'Preset initial animation is unsupported')
        # Captured inheritance is explicit replacement. Omitted animation remains
        # untouched, including a qualified noncanonical witness.
        if ('ActorAnimation' in captured and
                captured['ActorAnimation']['animation_asset_id'] == final['base']['semantic_id']):
            after.pop('ActorAnimation', None)
            proposed = deepcopy(final['base'])
        else:
            proposed = deepcopy(final['effective'])
        current = options(project, entity_id)
        document = project.imports[final['scene_id']]
        witness = next(a for a in document['actors'] if a['semantic_id'] == proposed['actor_semantic_id'])
        animation = dict(imported=deepcopy(final['imported']), base=deepcopy(final['base']),
                         effective=deepcopy(current['effective']), proposed=proposed,
                         authored=deepcopy((before or {}).get('ActorAnimation')),
                         after=deepcopy(after.get('ActorAnimation')),
                         witness=dict(entity_id=witness['semantic_id'], source_record=deepcopy(witness['source_record']),
                                      model_reference=deepcopy(witness['model_reference'])))
    return after or None, animation
