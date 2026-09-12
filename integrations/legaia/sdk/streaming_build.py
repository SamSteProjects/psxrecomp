"""Source-bound streaming scene preparation for the shared experimental exporter."""
from copy import deepcopy
from hashlib import sha256
import re
from importer.pipeline import _disc_context, _bounded_scene_range, import_scene
from importer.man_source import read_man_source
from importer.serialization import patch_man_positions
from .project import ProjectError, digest
from .build import authored_state_key


def prepare_streaming_scene(project, scene_id):
    key = authored_state_key(project)
    document = deepcopy(project.imports[scene_id])
    scene = document['scene']['name']
    if project.actor_drafts or project.model_overrides or project.texture_overrides:
        raise ProjectError('Streaming export does not yet support NPC additions or model/texture replacements')
    if import_scene(project.disc_path, scene) != document:
        raise ProjectError('Streaming imported evidence differs from the source disc')
    actors = {a['semantic_id']: a for a in document['actors']}
    edits, dialogue_edits, transition_edits, map_components = {}, {}, {}, None
    for identifier, components in deepcopy(project.overrides).items():
        if identifier == scene_id:
            map_components = components
            continue
        p2 = isinstance(identifier, str) and re.fullmatch(re.escape(scene_id) + r'/scripts/man-p2/[0-9]{4}', identifier) is not None
        allowed = {'Dialogue', 'Transitions'} if p2 else {'Transform', 'Dialogue', 'Transitions'}
        if (identifier not in actors and not p2) or not isinstance(components, dict) or not components or set(components) - allowed:
            raise ProjectError('Streaming export currently supports actor positions, dialogue, transition entries, scenery and collision; other authored components require further serialization support')
        if 'Transitions' in components:
            project._validate_transitions(identifier, components['Transitions'])
            transition_edits.update(components['Transitions']['entries'])
        if 'Dialogue' in components:
            project._validate_dialogue(identifier, components['Dialogue'])
            dialogue_edits.update(components['Dialogue']['runs'])
        if 'Transform' in components:
            transform = components['Transform']
            if not isinstance(transform, dict) or set(transform) != {'position'}:
                raise ProjectError('Streaming actor edits require exact position fields')
            edits[actors[identifier]['source_record']['record_index']] = transform['position']
    with _disc_context(project.disc_path) as (_, disc_hash, mapping, archive):
        start, end = _bounded_scene_range(archive, mapping, scene)
        carrier = read_man_source(archive, start, end, scene)
        if carrier.kind != 'raw_streaming_man':
            raise ProjectError('Streaming source kind changed during preparation')
        candidate, dialogue_changes = carrier.payload, []
        if dialogue_edits:
            from importer.dialogue_authoring import load_dialogue_authoring_context
            candidate, dialogue_changes = load_dialogue_authoring_context(project.disc_path, scene).patch(dialogue_edits, original=carrier.payload)
        candidate, placements = patch_man_positions(candidate, scene, edits)
        transition_changes = []
        if transition_edits:
            from importer.transition_authoring import load_transition_authoring_context
            context = load_transition_authoring_context(project.disc_path, scene)
            context.patch(transition_edits, original=carrier.payload)
            candidate, transition_changes = context.patch_appended(candidate, transition_edits)
        patches, map_audit = [], None
        if map_components:
            from .map_build import prepare_map_patch
            patch, map_audit = prepare_map_patch(project, scene_id, map_components, archive)
            patches.append(patch)
        if archive.header_offset != 0:
            raise ProjectError('Streaming scene composition requires the primary PROT header')
        prot = archive.image.read_user(archive.node.extent_lba, 0, archive.node.size, archive.node.size)
    if authored_state_key(project) != key:
        raise ProjectError('Streaming export inputs changed during preparation')
    return prot, dict(schema_version='legaia.streaming-scene-preparation.v1', scene_id=scene_id,
        source_disc_sha256=disc_hash, source_prot_sha256=sha256(prot).hexdigest(),
        authored_state_key=key, imported_document_sha256=digest(document),
        existing_actor_placement_changes=placements, existing_actor_dialogue_changes=dialogue_changes, map_changes=map_audit,
        transition_changes=transition_changes,
        final_man_sha256=sha256(candidate).hexdigest(), gameplay_verified=False,
        _asset_patches=patches,
        _rebuild_request=dict(entry_index=carrier.entry_index, chunk_header_offset=carrier.chunk_header_offset,
                              source_man_sha256=sha256(carrier.payload).hexdigest(), candidate=candidate))
