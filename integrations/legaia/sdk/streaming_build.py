"""Source-bound streaming scene preparation for the shared experimental exporter."""
from copy import deepcopy
from hashlib import sha256
import re
from importer.pipeline import _disc_context, _bounded_scene_range, import_scene
from importer.man_source import read_man_source
from importer.serialization import patch_man_positions
from .project import ProjectError, digest
from .build import authored_state_key


def prepare_streaming_scene(project, scene_id, *,animation_growth_managed=False):
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
    allocated_assignments={}
    movement_edits = {}
    flag_edits = {}
    wait_edits = {}
    model_selector_edits = {}
    facing_edits = {}
    branch_edits = {}
    for identifier, components in deepcopy(project.overrides).items():
        if identifier == scene_id:
            if 'AnimationRecords' in components:
                if not animation_growth_managed:raise ProjectError('Streaming animation allocation requires managed bank delivery')
                components={key:value for key,value in components.items() if key!='AnimationRecords'}
            map_components = components or None
            continue
        p2 = isinstance(identifier, str) and re.fullmatch(re.escape(scene_id) + r'/scripts/man-p2/[0-9]{4}', identifier) is not None
        allowed = {'Dialogue', 'Transitions', 'ScriptMovement', 'ScriptFlags', 'ScriptWaits', 'ScriptModelSelectors', 'ScriptFacing', 'ScriptBranches'} if p2 else {'Transform', 'ActorAppearance', 'ActorAnimation','ActorAllocatedAnimation', 'Dialogue', 'Transitions', 'ScriptMovement', 'ScriptFlags', 'ScriptWaits', 'ScriptModelSelectors', 'ScriptFacing', 'ScriptBranches', 'AnimationChannels'}
        if (identifier not in actors and not p2) or not isinstance(components, dict) or not components or set(components) - allowed:
            raise ProjectError('Streaming export requires supported same-scene actor or script components; unsupported authored families cannot be omitted')
        if 'AnimationChannels' in components:
            project._validate_animation_override(identifier, components['AnimationChannels'])
            animations[identifier] = components['AnimationChannels']
        if 'ActorAllocatedAnimation' in components:
            if not animation_growth_managed:raise ProjectError('Streaming allocated assignment requires managed bank delivery')
            allocated_assignments[identifier]=components['ActorAllocatedAnimation']
        if 'ActorAppearance' in components and 'ActorAllocatedAnimation' not in components:
            appearance = components['ActorAppearance']
            if (not isinstance(appearance, dict) or set(appearance) != {'donor_entity_id'} or
                    not isinstance(appearance['donor_entity_id'], str) or appearance['donor_entity_id'] not in actors):
                raise ProjectError('Streaming appearance requires a same-scene imported donor')
            record = actors[identifier]['source_record']['record_index']
            donor = actors[appearance['donor_entity_id']]
            assignments[record] = dict(model_index=donor['model_reference']['model_index'],
                                       animation_id=donor['placement_fields']['animation_id'])
            assignment_donors[record] = appearance['donor_entity_id']
        if 'ActorAnimation' in components:
            from .actor_animation import validate
            witness = validate(project, identifier, components['ActorAnimation'], verify_disc=True)
            record = actors[identifier]['source_record']['record_index']
            assignments[record] = dict(model_index=witness['model_reference']['model_index'],
                                       animation_id=witness['placement_fields']['animation_id'])
            assignment_donors[record] = witness['semantic_id']
        if 'ScriptBranches' in components:
            project._validate_branches(identifier, components['ScriptBranches'])
            branch_edits.update(components['ScriptBranches']['entries'])
        if 'ScriptMovement' in components:
            project._validate_movements(identifier, components['ScriptMovement'])
            movement_edits.update(components['ScriptMovement']['entries'])
        if 'ScriptFlags' in components:
            project._validate_flags(identifier,components['ScriptFlags'])
            flag_edits.update(components['ScriptFlags']['entries'])
        if 'ScriptWaits' in components:
            project._validate_waits(identifier,components['ScriptWaits'])
            wait_edits.update(components['ScriptWaits']['entries'])
        if 'ScriptFacing' in components:
            project._validate_facing(identifier,components['ScriptFacing'])
            facing_edits.update(components['ScriptFacing']['entries'])
        if 'ScriptModelSelectors' in components:
            project._validate_model_selectors(identifier,components['ScriptModelSelectors'])
            model_selector_edits.update(components['ScriptModelSelectors']['entries'])
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
        npc_dialogue_audit=None
        if any(item.get('dialogue') for item in project.actor_drafts.values() if item['scene_id']==scene_id):
            from .npc_dialogue import patch_clones
            from importer.dialogue_authoring import load_dialogue_authoring_context
            npc_context=load_dialogue_authoring_context(project.disc_path,scene)
            candidate,npc_dialogue_audit=patch_clones(project,scene_id,npc_context,candidate,actor_audit)
        if dialogue_edits:
            from importer.dialogue_authoring import load_dialogue_authoring_context
            context = load_dialogue_authoring_context(project.disc_path, scene)
            context.patch(dialogue_edits, original=carrier.payload)
            candidate, dialogue_changes = context.patch_appended(candidate, dialogue_edits)
        npc_movement_audit=None
        if any('movement' in item for item in project.actor_drafts.values() if item['scene_id']==scene_id):
            from .npc_movement import patch_project as patch_npc_movements
            from importer.movement_authoring import load_movement_authoring_context
            npc_movement_context=load_movement_authoring_context(project.disc_path,scene)
            candidate,npc_movement_audit=patch_npc_movements(project,scene_id,npc_movement_context,candidate,actor_audit)
        npc_facing_audit=None
        if any('facing' in item for item in project.actor_drafts.values() if item['scene_id']==scene_id):
            from .npc_facing import patch_project as patch_npc_facing
            from importer.facing_authoring import load_facing_authoring_context
            npc_facing_context=load_facing_authoring_context(project.disc_path,scene)
            candidate,npc_facing_audit=patch_npc_facing(project,scene_id,npc_facing_context,candidate,actor_audit)
        npc_flags_audit=None
        if any('flags' in item for item in project.actor_drafts.values() if item['scene_id']==scene_id):
            from .npc_flags import patch_project as patch_npc_flags
            from importer.flag_authoring import load_flag_authoring_context
            npc_flags_context=load_flag_authoring_context(project.disc_path,scene)
            candidate,npc_flags_audit=patch_npc_flags(project,scene_id,npc_flags_context,candidate,actor_audit)
        npc_wait_audit=None
        if any('waits' in item for item in project.actor_drafts.values() if item['scene_id']==scene_id):
            from .npc_waits import patch_project as patch_npc_waits
            from importer.wait_authoring import load_wait_authoring_context
            npc_wait_context=load_wait_authoring_context(project.disc_path,scene)
            candidate,npc_wait_audit=patch_npc_waits(project,scene_id,npc_wait_context,candidate,actor_audit)
        npc_appearance_audit=None
        if any('appearance' in item for item in project.actor_drafts.values()):
            from .npc_appearance import patch_project
            from importer.man_assignments import load_man_assignment_context
            npc_context=load_man_assignment_context(project.disc_path,scene)
            candidate,npc_appearance_audit=patch_project(project,scene_id,npc_context,candidate,actor_audit)
        npc_branches_audit=None
        if any('branches' in item for item in project.actor_drafts.values() if item['scene_id']==scene_id):
            from .npc_branches import patch_project as patch_npc_branches
            from importer.branch_authoring import load_branch_authoring_context
            npc_branches_context=load_branch_authoring_context(project.disc_path,scene)
            candidate,npc_branches_audit=patch_npc_branches(project,scene_id,npc_branches_context,candidate,actor_audit)
        appearance_changes = []
        if assignments:
            from importer.man_assignments import load_man_assignment_context
            context = load_man_assignment_context(project.disc_path, scene)
            context.patch(assignments, original=carrier.payload)
            candidate, appearance_changes = context.patch_appended(candidate, assignments)
            for change in appearance_changes:
                change['donor_entity_id'] = assignment_donors[change['record_index']]
                target = f'{scene_id}/actors/man-p1/{change["record_index"]:04d}'
                animation = project.overrides.get(target, {}).get('ActorAnimation')
                if animation:
                    change.update(assignment_kind='ActorAnimation', animation_asset_id=animation['animation_asset_id'],
                                  assignment_source_record_sha256=animation['source_record_sha256'])
        allocated_changes=[]
        if allocated_assignments:
            from .allocated_animation_build import patch_assignments
            candidate,allocated_changes=patch_assignments(project,scene_id,allocated_assignments,carrier.payload,candidate,appended=bool(requests))
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
        model_selector_changes = []
        if model_selector_edits:
            from importer.model_selector_authoring import load_model_selector_authoring_context
            context = load_model_selector_authoring_context(project.disc_path,scene)
            context.patch(model_selector_edits,original=carrier.payload)
            candidate,model_selector_changes=context.patch_appended(candidate,model_selector_edits)
        facing_changes = []
        if facing_edits:
            from importer.facing_authoring import load_facing_authoring_context
            context = load_facing_authoring_context(project.disc_path,scene)
            context.patch(facing_edits,original=carrier.payload)
            candidate,facing_changes=context.patch_appended(candidate,facing_edits)
        branch_changes = []
        if branch_edits:
            from importer.branch_authoring import load_branch_authoring_context
            context = load_branch_authoring_context(project.disc_path, scene)
            context.patch(branch_edits, original=carrier.payload)
            candidate, branch_changes = context.patch_appended(candidate, branch_edits)
        from .actor_capacity import actor_pool_assessment
        pool_evidence = actor_pool_assessment(archive, candidate) if requests else None
        # The raw loader advances by words. Pad only after all MAN edits so
        # record rebasing uses the original structural append result.
        padding = (-len(candidate)) % 4
        candidate += bytes(padding)
        patches, map_audit, animation_audit = [], None, None
        if animations and not (animation_growth_managed and 'AnimationRecords' in project.overrides.get(scene_id,{})):
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
        model_changes=model_audit, texture_changes=texture_audit, animation_changes=animation_audit, branch_changes=branch_changes, transition_changes=transition_changes, movement_changes=movement_changes, flag_changes=flag_changes, wait_changes=wait_changes, model_selector_changes=model_selector_changes, facing_changes=facing_changes, existing_actor_appearance_changes=appearance_changes,
        actor_changes=actor_audit, actor_pool_evidence=pool_evidence, man_padding_bytes=padding,
        existing_actor_allocated_animation_changes=allocated_changes,npc_dialogue_changes=npc_dialogue_audit,npc_appearance_changes=npc_appearance_audit,npc_wait_changes=npc_wait_audit,npc_movement_changes=npc_movement_audit,npc_facing_changes=npc_facing_audit,npc_flags_changes=npc_flags_audit,npc_branches_changes=npc_branches_audit,
        final_man_sha256=sha256(candidate).hexdigest(), gameplay_verified=False,
        _asset_patches=patches,
        _rebuild_request=dict(entry_index=carrier.entry_index, chunk_header_offset=carrier.chunk_header_offset,
                              source_man_sha256=sha256(carrier.payload).hexdigest(), candidate=candidate))
