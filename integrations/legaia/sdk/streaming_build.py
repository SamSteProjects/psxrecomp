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
    if import_scene(project.disc_path, scene) != document:
        raise ProjectError('Streaming imported evidence differs from the source disc')
    actors = {a['semantic_id']: a for a in document['actors']}
    requests = []
    for identifier, draft in deepcopy(project.actor_drafts).items():
        project._validate_actor_draft(identifier, draft)
        if draft['scene_id'] != scene_id or draft['donor_entity_id'] not in actors:
            raise ProjectError('Streaming NPC requires an imported donor in its source scene')
        requests.append(dict(id=identifier, donor_record_index=actors[draft['donor_entity_id']]['source_record']['record_index'],
                             position=draft['position']))
    edits, dialogue_edits, transition_edits, map_components = {}, {}, {}, None
    assignments, assignment_donors, animations = {}, {}, {}
    movement_edits = {}
    flag_edits = {}
    wait_edits = {}
    for identifier, components in deepcopy(project.overrides).items():
        if identifier == scene_id:
            map_components = components
            continue
        p2 = isinstance(identifier, str) and re.fullmatch(re.escape(scene_id) + r'/scripts/man-p2/[0-9]{4}', identifier) is not None
        allowed = {'Dialogue', 'Transitions', 'ScriptMovement', 'ScriptFlags', 'ScriptWaits'} if p2 else {'Transform', 'ActorAppearance', 'Dialogue', 'Transitions', 'ScriptMovement', 'ScriptFlags', 'ScriptWaits', 'AnimationChannels'}
        if (identifier not in actors and not p2) or not isinstance(components, dict) or not components or set(components) - allowed:
            raise ProjectError('Streaming export currently supports actor positions, donor appearance, dialogue, transition entries, animation channels, scenery and collision; other authored components require further serialization support')
        if 'AnimationChannels' in components:
            project._validate_animation_override(identifier, components['AnimationChannels'])
            animations[identifier] = components['AnimationChannels']
        if 'ActorAppearance' in components:
            appearance = components['ActorAppearance']
            if (not isinstance(appearance, dict) or set(appearance) != {'donor_entity_id'} or
                    not isinstance(appearance['donor_entity_id'], str) or appearance['donor_entity_id'] not in actors):
                raise ProjectError('Streaming appearance requires a same-scene imported donor')
            record = actors[identifier]['source_record']['record_index']
            donor = actors[appearance['donor_entity_id']]
            assignments[record] = dict(model_index=donor['model_reference']['model_index'],
                                       animation_id=donor['placement_fields']['animation_id'])
            assignment_donors[record] = appearance['donor_entity_id']
        if 'ScriptMovement' in components:
            project._validate_movements(identifier, components['ScriptMovement'])
            movement_edits.update(components['ScriptMovement']['entries'])
        if 'ScriptFlags' in components:
            project._validate_flags(identifier,components['ScriptFlags'])
            flag_edits.update(components['ScriptFlags']['entries'])
        if 'ScriptWaits' in components:
            project._validate_waits(identifier,components['ScriptWaits'])
            wait_edits.update(components['ScriptWaits']['entries'])
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
        actor_audit = None
        if requests:
            from importer.man_actor_structure import append_actor_candidates
            candidate, actor_audit = append_actor_candidates(carrier.payload, sha256(carrier.payload).hexdigest(), requests)
        if dialogue_edits:
            from importer.dialogue_authoring import load_dialogue_authoring_context
            context = load_dialogue_authoring_context(project.disc_path, scene)
            context.patch(dialogue_edits, original=carrier.payload)
            candidate, dialogue_changes = context.patch_appended(candidate, dialogue_edits)
        appearance_changes = []
        if assignments:
            from importer.man_assignments import load_man_assignment_context
            context = load_man_assignment_context(project.disc_path, scene)
            context.patch(assignments, original=carrier.payload)
            candidate, appearance_changes = context.patch_appended(candidate, assignments)
            for change in appearance_changes:
                change['donor_entity_id'] = assignment_donors[change['record_index']]
        candidate, placements = patch_man_positions(candidate, scene, edits)
        transition_changes = []
        if transition_edits:
            from importer.transition_authoring import load_transition_authoring_context
            context = load_transition_authoring_context(project.disc_path, scene)
            context.patch(transition_edits, original=carrier.payload)
            candidate, transition_changes = context.patch_appended(candidate, transition_edits)
        movement_changes = []
        if movement_edits:
            from importer.movement_authoring import load_movement_authoring_context
            context = load_movement_authoring_context(project.disc_path, scene)
            context.patch(movement_edits, original=carrier.payload)
            candidate, movement_changes = context.patch_appended(candidate, movement_edits)
        flag_changes = []
        if flag_edits:
            from importer.flag_authoring import load_flag_authoring_context
            context = load_flag_authoring_context(project.disc_path,scene)
            context.patch(flag_edits,original=carrier.payload)
            candidate,flag_changes=context.patch_appended(candidate,flag_edits)
        wait_changes = []
        if wait_edits:
            from importer.wait_authoring import load_wait_authoring_context
            context = load_wait_authoring_context(project.disc_path,scene)
            context.patch(wait_edits,original=carrier.payload)
            candidate,wait_changes=context.patch_appended(candidate,wait_edits)
        # The raw loader advances by words. Pad only after all MAN edits so
        # record rebasing uses the original structural append result.
        padding = (-len(candidate)) % 4
        candidate += bytes(padding)
        patches, map_audit, animation_audit = [], None, None
        if animations:
            from .animation_build import prepare_animation_patches
            animation_patches, animation_audit = prepare_animation_patches(project, scene_id, animations, archive)
            patches.extend(animation_patches)
        if map_components:
            from .map_build import prepare_map_patch
            patch, map_audit = prepare_map_patch(project, scene_id, map_components, archive)
            patches.append(patch)
        model_audit = None
        if project.model_overrides:
            from .model_build import prepare_model_patches
            model_patches, model_audit = prepare_model_patches(project, scene_id, project.model_overrides, archive)
            patches.extend(model_patches)
        texture_audit = None
        if project.texture_overrides:
            from .texture_build import prepare_texture_patches
            texture_patches, texture_audit = prepare_texture_patches(project, scene_id, project.texture_overrides, archive)
            patches.extend(texture_patches)
        if archive.header_offset != 0:
            raise ProjectError('Streaming scene composition requires the primary PROT header')
        prot = archive.image.read_user(archive.node.extent_lba, 0, archive.node.size, archive.node.size)
    if authored_state_key(project) != key:
        raise ProjectError('Streaming export inputs changed during preparation')
    return prot, dict(schema_version='legaia.streaming-scene-preparation.v1', scene_id=scene_id,
        source_disc_sha256=disc_hash, source_prot_sha256=sha256(prot).hexdigest(),
        authored_state_key=key, imported_document_sha256=digest(document),
        existing_actor_placement_changes=placements, existing_actor_dialogue_changes=dialogue_changes, map_changes=map_audit,
        model_changes=model_audit, texture_changes=texture_audit, animation_changes=animation_audit, transition_changes=transition_changes, movement_changes=movement_changes, flag_changes=flag_changes, wait_changes=wait_changes, existing_actor_appearance_changes=appearance_changes,
        actor_changes=actor_audit, man_padding_bytes=padding,
        final_man_sha256=sha256(candidate).hexdigest(), gameplay_verified=False,
        _asset_patches=patches,
        _rebuild_request=dict(entry_index=carrier.entry_index, chunk_header_offset=carrier.chunk_header_offset,
                              source_man_sha256=sha256(carrier.payload).hexdigest(), candidate=candidate))
