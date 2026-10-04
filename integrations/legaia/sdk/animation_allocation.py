"""Source-bound review of new rigid clips; persistence/delivery remain separate."""
from copy import deepcopy
from hashlib import sha256
from uuid import UUID

from importer.animation_allocation import append_animation_records
from importer.pipeline import _disc_context
from importer.scene_animation import load_scene_actor_animation_catalog
from .project import ProjectError, digest
from .scene_preview import source_key


def prepare_record_allocation(project, entity_id, source_frame_indices, edits,
                              expected_source_key):
    """Resolve a donor through actor/model evidence and review one new record.

    Current shared channel contributions are composed before copying frames.
    The preview neither publishes a component nor allocates files/history.
    """
    if project.mode != 'edit':
        raise ProjectError('Animation record allocation review requires Edit mode')
    document = project.imports.get(project.active_scene)
    actor = next((item for item in (document or {}).get('actors', [])
                  if item['semantic_id'] == entity_id), None)
    if actor is None:
        raise ProjectError('Animation allocation requires an imported actor in the active scene')
    key = source_key(project)
    if not key or expected_source_key != key:
        raise ProjectError('Animation allocation source is stale; review the current scene')
    with _disc_context(project.disc_path):
        model_source = actor
        if any(name in project.overrides.get(entity_id, {}) for name in ('ActorAppearance', 'ActorAnimation')):
            from .actor_animation import source_actor
            model_source = project.appearance_source_actor(entity_id, verify_disc=True)
            actor = source_actor(project, entity_id, verify_disc=True)
        options = project.animation_authoring_options(actor['semantic_id'])
        binding = options['binding']
        catalog = load_scene_actor_animation_catalog(project.disc_path, document['scene']['name'])
        retail, provenance = catalog.source_bank()
        owners = {item['semantic_id']: deepcopy(project.overrides[item['semantic_id']]['AnimationChannels'])
                  for item in document['actors']
                  if 'AnimationChannels' in project.overrides.get(item['semantic_id'], {})}
        effective, _ = catalog.authored_bank(owners)
        identity_hash = digest(dict(project_source_key=key, entity_id=entity_id,
            donor_animation_id=binding['semantic_id'], source_frame_indices=source_frame_indices, edits=edits))
        record_id = str(UUID(bytes=bytes.fromhex(identity_hash)[:16], version=4))
        candidate, allocation = append_animation_records(effective, sha256(effective).hexdigest(), [dict(
            record_id=record_id, donor_record_index=binding['source_record']['record_index'],
            source_frame_indices=source_frame_indices, edits=edits)])
    if source_key(project) != key:
        raise ProjectError('Project changed while verifying animation allocation')
    report = dict(schema_version='legaia.animation-record-allocation-review.v1',
        entity_id=entity_id, scene_id=project.active_scene, project_source_key=key,
        animation_id=f"animation://{document['scene']['name']}/authored-record/{record_id}",
        donor_animation_id=binding['semantic_id'],
        channel_owner_entity_id=actor['semantic_id'], model_source_entity_id=model_source['semantic_id'],
        donor_asset_id=binding['asset_semantic_id'], source_bank=deepcopy(provenance),
        retail_bank_sha256=sha256(retail).hexdigest(), effective_bank_sha256=sha256(effective).hexdigest(),
        candidate_bank_sha256=sha256(candidate).hexdigest(), allocation=allocation,
        project_changed=False, gameplay_verified=False,
        capabilities=dict(review=True, apply=False, build=False, actor_assignment=False),
        limitations=['Native bank proposal only; project ledger and carrier relocation are not implemented.',
                     'The frame sequence has no verified retail rate or runtime clip-selection evidence.',
                     'Existing shared clip edits are copied into the new record; existing records remain unchanged.'])
    report['review_key'] = digest(report)
    return candidate, report


def preview_record_allocation(project, entity_id, source_frame_indices, edits, expected_source_key):
    return prepare_record_allocation(project, entity_id, source_frame_indices, edits, expected_source_key)[1]
