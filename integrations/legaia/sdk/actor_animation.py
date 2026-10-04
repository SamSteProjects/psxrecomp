"""Reviewed initial MAN clip selection from exact observed model bindings.

The witness remains an imported actor; this module never rewrites evidence or
retargets AnimationChannels. MAN byte patching is owned by the existing decoder.
"""
from copy import deepcopy
import re

from importer.core import ImportError as RetailImportError
from .asset_references import source_key
from .project import ProjectError, digest

_HASH = re.compile(r'[0-9a-f]{64}\Z')
_FIELDS = {'donor_entity_id', 'animation_asset_id', 'source_record_sha256'}
LIMITATIONS = [
    'Initial MAN animation header only; scripts can later change the model or clip.',
    'Choices have an observed binding to the exact inherited model and object mapping.',
    'Playback cadence, looping, script behavior and visual suitability remain unverified.',
    'AnimationChannels continue to edit their imported shared clip and are not retargeted.',
    'Global banks, zero-animation actors, unobserved pairings and new clips are unsupported.',
]


def _subject(project, identifier):
    if not isinstance(identifier, str) or not identifier or len(identifier) > 1024:
        raise ProjectError('Initial animation requires an imported actor identity')
    actor = project._actor(identifier)
    documents = [(scene, document) for scene, document in project.imports.items()
                 if any(row['semantic_id'] == identifier for row in document['actors'])]
    if len(documents) != 1:
        raise ProjectError('Initial animation actor has ambiguous scene evidence')
    scene, document = documents[0]
    return scene, document, actor


def _local_asset(document, actor):
    reference = actor.get('model_reference', {})
    model = reference.get('model_index')
    animation = actor.get('placement_fields', {}).get('animation_id')
    if (type(model) is not int or not 0 <= model < 0xf0 or
            type(animation) is not int or not 1 <= animation <= 255):
        raise ProjectError('Initial animation requires an existing local scene model and nonzero clip')
    assets = [asset for asset in document['assets']['models']
              if asset['semantic_id'] == reference.get('asset_semantic_id')]
    if len(assets) != 1 or assets[0].get('asset_kind') != 'tmd_model':
        raise ProjectError('Initial animation model has no exact imported TMD source')
    source = assets[0].get('source_record')
    if (not isinstance(source, dict) or type(source.get('object_count')) is not int or
            not 1 <= source['object_count'] <= 1024):
        raise ProjectError('Initial animation model has no bounded object count')
    return assets[0]


def _same_model(document, base, witness):
    first, second = _local_asset(document, base), _local_asset(document, witness)
    return (base['model_reference']['model_index'] == witness['model_reference']['model_index'] and
            first['semantic_id'] == second['semantic_id'] and
            first['source_record'] == second['source_record'])


def validate(project, entity_id, value, verify_disc=False):
    """Validate a portable component; optionally prove its current retail bytes."""
    if (not isinstance(value, dict) or set(value) != _FIELDS or
            not isinstance(value.get('donor_entity_id'), str) or
            not isinstance(value.get('animation_asset_id'), str) or
            not isinstance(value.get('source_record_sha256'), str) or
            not _HASH.fullmatch(value['source_record_sha256'])):
        raise ProjectError('ActorAnimation requires an exact witness, stable clip identity and source SHA-256')
    scene, document, actor = _subject(project, entity_id)
    _local_asset(document, actor)
    base = project.appearance_source_actor(entity_id, verify_disc=False)
    witness = next((row for row in document['actors']
                    if row['semantic_id'] == value['donor_entity_id']), None)
    if witness is None or not _same_model(document, base, witness):
        raise ProjectError('ActorAnimation witness must have the exact inherited scene model source')
    expected = f"animation://{document['scene']['name']}/scene-anm/{witness['placement_fields']['animation_id'] - 1:04d}"
    if value['animation_asset_id'] != expected:
        raise ProjectError('ActorAnimation clip identity differs from its imported witness')
    if verify_disc and not any(choice['value'] == value for choice in options(project, entity_id)['choices']):
        raise ProjectError('ActorAnimation witness or source digest differs from current verified choices')
    return witness


def source_actor(project, entity_id, verify_disc=False):
    """Resolve one imported pose witness without changing target identity/position."""
    components = project.overrides.get(entity_id, {})
    if 'ActorAnimation' in components:
        return validate(project, entity_id, components['ActorAnimation'], verify_disc=verify_disc)
    return project.appearance_source_actor(entity_id, verify_disc=verify_disc)


def options(project, entity_id):
    """Fresh, bounded, read-only clip choices for the current appearance model."""
    from importer.pipeline import _disc_context, import_scene
    from importer.scene_animation import load_scene_actor_animation_catalog
    from importer.man_assignments import load_man_assignment_context

    scene, document, actor = _subject(project, entity_id)
    if 'ActorAllocatedAnimation' in project.overrides.get(entity_id,{}):
        raise ProjectError('Clear the allocated initial clip assignment before choosing an imported clip')
    if not project.disc_path:
        raise ProjectError('Initial animation choices require the project user-owned disc')
    before = source_key(project)
    components = project.overrides.get(entity_id, {})
    authored = deepcopy(components.get('ActorAnimation'))
    result = dict(schema_version='legaia.actor-animation-options.v1', entity_id=entity_id,
                  scene_id=scene, source_key=before, supported=False, reason=None,
                  imported=None, base=None, effective=None, authored=authored,
                  choices=[], limitations=list(LIMITATIONS))
    with _disc_context(project.disc_path):
        if digest(import_scene(project.disc_path, document['scene']['name'])) != digest(document):
            raise ProjectError('Initial animation source differs from freshly verified imported evidence')
        base = project.appearance_source_actor(entity_id, verify_disc=True)
        try:
            _local_asset(document, actor)
            _local_asset(document, base)
            catalog = load_scene_actor_animation_catalog(project.disc_path, document['scene']['name'])
            metadata = catalog.referenced_animation_metadata()
            bindings = {row['actor_semantic_id']: row for row in metadata['bindings']}
            result['imported'] = deepcopy(bindings.get(entity_id))
            result['base'] = deepcopy(bindings.get(base['semantic_id']))
            result['effective'] = deepcopy(result['base'])
            if result['imported'] is None or result['base'] is None:
                raise RetailImportError('Actor has no verified imported rigid animation binding')
            context = load_man_assignment_context(project.disc_path, document['scene']['name'])
            support = context.options(actor['source_record']['record_index'])
            if not support['supported']:
                raise RetailImportError(support['reason'])
            pairs = {(pair['model_index'], pair['animation_id']): set(pair['donor_records'])
                     for pair in support['pairs']}
            base_mapping = result['base']['association']
            candidates = {}
            for witness in document['actors']:
                try:
                    exact_model = _same_model(document, base, witness)
                except ProjectError:
                    continue
                binding = bindings.get(witness['semantic_id'])
                if not exact_model or binding is None:
                    continue
                pair = (witness['model_reference']['model_index'], witness['placement_fields']['animation_id'])
                association = binding['association']
                if (witness['source_record']['record_index'] not in pairs.get(pair, set()) or
                        any(association[key] != base_mapping[key] for key in
                            ('active_object_indices', 'excluded_object_indices'))):
                    continue
                value = dict(donor_entity_id=witness['semantic_id'], animation_asset_id=binding['semantic_id'],
                             source_record_sha256=binding['source_record']['record_sha256'])
                # Keep a saved, still-qualified witness stable across compatible
                # appearance changes; canonicalization must not orphan its proof.
                rank = (not (authored and value == authored),
                        witness['semantic_id'] != base['semantic_id'], witness['semantic_id'])
                existing = candidates.get(binding['semantic_id'])
                if existing is None or rank < existing[0]:
                    candidates[binding['semantic_id']] = (rank, value, binding)
            for _, (_, value, binding) in sorted(candidates.items()):
                result['choices'].append(dict(value=deepcopy(value), binding=deepcopy(binding),
                    label=f"Initial animation {binding['association']['animation_id']} · {binding['frame_count']} frames · witness {value['donor_entity_id'].rsplit('/', 1)[-1]}"))
            if not any(choice['binding']['semantic_id'] == result['base']['semantic_id']
                       for choice in result['choices']):
                raise RetailImportError('Inherited clip has no supported non-aliased equal-count MAN assignment')
            if 'ActorAnimation' in components:
                validate(project, entity_id, authored)
                selected = next((choice for choice in result['choices'] if choice['value'] == authored), None)
                if selected is None:
                    raise ProjectError('ActorAnimation witness or source digest differs from current verified choices')
                result['effective'] = deepcopy(selected['binding'])
            result['supported'] = True
        except RetailImportError as exc:
            result['reason'] = str(exc)
            result['choices'] = []
        except ProjectError as exc:
            if 'ActorAnimation' in components:
                raise
            result['reason'] = str(exc)
            result['choices'] = []
    if source_key(project) != before:
        raise ProjectError('Project changed while resolving initial animation choices')
    return result


def review(project, entity_id, animation_asset_id, expected_source_key=None):
    """Prepare a source-qualified component change without authoring it."""
    if project.mode != 'edit':
        raise ProjectError('Initial animation review requires Edit mode')
    scene, _, _ = _subject(project, entity_id)
    if scene != project.active_scene:
        raise ProjectError('Initial animation review requires an actor in the active scene')
    if animation_asset_id is not None and (not isinstance(animation_asset_id, str) or
                                          not animation_asset_id or len(animation_asset_id) > 1024):
        raise ProjectError('Initial animation review requires an existing stable clip identity or null')
    if expected_source_key is not None and (not isinstance(expected_source_key, str) or
                                          not _HASH.fullmatch(expected_source_key) or
                                          source_key(project) != expected_source_key):
        raise ProjectError('Initial animation project source changed since the request')
    choices = options(project, entity_id)
    if not choices['supported']:
        raise ProjectError(choices['reason'] or 'Initial animation assignment is unsupported')
    base = choices['base']
    selected = next((choice for choice in choices['choices']
                     if choice['binding']['semantic_id'] == (animation_asset_id or base['semantic_id'])), None)
    if selected is None:
        raise ProjectError('Initial animation is not an observed compatible clip for the inherited model')
    after = None if selected['binding']['semantic_id'] == base['semantic_id'] else deepcopy(selected['value'])
    result = dict(schema_version='legaia.actor-animation-review.v1', entity_id=entity_id,
                  scene_id=scene, source_key=choices['source_key'], animation_asset_id=animation_asset_id,
                  before=deepcopy(choices['authored']), after=after, imported=deepcopy(choices['imported']),
                  base=deepcopy(base), effective=deepcopy(choices['effective']),
                  proposed=deepcopy(base if after is None else selected['binding']), project_change=choices['authored'] != after,
                  limitations=list(LIMITATIONS))
    result['review_key'] = digest(result)
    if source_key(project) != choices['source_key']:
        raise ProjectError('Project changed while reviewing initial animation')
    return result


def apply(project, command):
    """Freshly prove the review and append one standard component Undo entry."""
    if (not isinstance(command, dict) or set(command) !=
            {'type', 'entity_id', 'animation_asset_id', 'source_key', 'review_key'} or
            command['type'] != 'set_actor_animation' or
            not isinstance(command['source_key'], str) or not _HASH.fullmatch(command['source_key']) or
            not isinstance(command['review_key'], str) or not _HASH.fullmatch(command['review_key'])):
        raise ProjectError('Initial animation Apply requires exact actor, clip, source and review identities')
    result = review(project, command['entity_id'], command['animation_asset_id'], command['source_key'])
    if result['review_key'] != command['review_key']:
        raise ProjectError('Initial animation inputs or evidence changed since review')
    if not result['project_change']:
        return result
    before = deepcopy(project.overrides.get(command['entity_id']))
    after = deepcopy(before or {})
    if result['after'] is None:
        after.pop('ActorAnimation', None)
    else:
        after['ActorAnimation'] = deepcopy(result['after'])
    after = after or None
    entry = dict(entity_id=command['entity_id'], before=before, after=deepcopy(after))
    if after is None:
        project.overrides.pop(command['entity_id'], None)
    else:
        project.overrides[command['entity_id']] = after
    project.undo_stack.append(entry)
    project.redo_stack.clear()
    return result
