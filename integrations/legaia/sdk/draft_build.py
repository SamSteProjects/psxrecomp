"""Experimental saved-draft serialization; not the playable project build path."""
from copy import deepcopy, copy
from hashlib import sha256
from pathlib import Path
import re
from importer.core import find_scene_bundle, decompress_lzs
from importer.pipeline import _disc_context, _bounded_scene_range, import_scene
from importer.man_actor_structure import append_actor_candidates
from importer.man_assignments import load_man_assignment_context
from importer.dialogue_authoring import load_dialogue_authoring_context
from importer.transition_authoring import load_transition_authoring_context
from importer.prot_layout import locate_physical_span
from importer.prot_rebuild import rebuild_man_entry, rebuild_man_entries, patch_archive_spans
from importer.serialization import patch_man_positions
from .project import ProjectError, digest
from .build import authored_state_key
from .project import atomic_write, canonical
from .actor_capacity import actor_pool_assessment


def prepare_draft_archive(project, draft_id: str | None = None) -> tuple[bytes, dict]:
    """Compose draft-bearing scenes without omitting authored input."""
    if 'worldmap://legaia/menu' in project.overrides:
        raise ProjectError('Experimental Export disc does not support global world-map landmarks; use normal Build')
    if draft_id is not None and (not isinstance(draft_id,str) or draft_id not in project.actor_drafts):
        raise ProjectError('Select an existing NPC draft')
    scene_ids={item['scene_id'] for item in project.actor_drafts.values()}
    for binding in list(project.texture_overrides.values())+list(project.model_overrides.values()):
        if not isinstance(binding,dict) or binding.get('source_scene_id') not in project.imports:
            raise ProjectError('Asset export requires an imported source scene')
        scene_ids.add(binding['source_scene_id'])
    for identifier in project.overrides:
        matches=[scene for scene in project.imports if identifier==scene or identifier.startswith(scene+'/')]
        if len(matches)!=1:
            raise ProjectError('Draft export has edits outside its imported scenes')
        scene_ids.add(matches[0])
    if not scene_ids:
        raise ProjectError('Experimental export requires authored scene edits or NPC drafts')
    if len(scene_ids)==1 and draft_id is not None:
        document = project.imports[next(iter(scene_ids))]
        streaming = any(a.get('source_record', {}).get('scene_bundle', {}).get('kind') == 'raw_streaming_man'
                        for a in document.get('actors', []))
        if not streaming:
            return _prepare_draft_scene(project,draft_id)
    input_key=authored_state_key(project)
    scoped={scene:{} for scene in scene_ids}
    for identifier,value in project.overrides.items():
        matches=[scene for scene in scene_ids if identifier==scene or identifier.startswith(scene+'/')]
        if len(matches)!=1:
            raise ProjectError('Draft export has edits outside its draft-bearing scenes')
        scoped[matches[0]][identifier]=deepcopy(value)
    requests,scenes=[],{}
    asset_patches=[]
    source_prot=None
    for scene in sorted(scene_ids):
        view=copy(project)
        view.overrides=scoped[scene]
        view.model_overrides={key:deepcopy(value) for key,value in project.model_overrides.items() if value['source_scene_id']==scene}
        view.texture_overrides={key:deepcopy(value) for key,value in project.texture_overrides.items() if value['source_scene_id']==scene}
        view.actor_drafts={key:deepcopy(item) for key,item in project.actor_drafts.items() if item['scene_id']==scene}
        selected=sorted(view.actor_drafts)[0] if view.actor_drafts else None
        prot,audit=_prepare_draft_scene(view,selected,defer_rebuild=True,scene_id=scene)
        if source_prot is not None and prot!=source_prot:
            raise ProjectError('Draft scenes disagree on source archive')
        source_prot=prot
        requests.append(audit.pop('_rebuild_request'))
        asset_patches.extend(audit.pop('_asset_patches',[]))
        if scenes and audit['source_disc_sha256']!=next(iter(scenes.values()))['source_disc_sha256']:
            raise ProjectError('Draft scenes disagree on source disc identity')
        audit.pop('result_prot_sha256',None)
        audit.pop('container',None)
        audit['stage']='prepared_scene_man'
        scenes[scene]=audit
    source_hash=sha256(source_prot).hexdigest()
    composed,asset_audit=patch_archive_spans(source_prot,source_hash,asset_patches)
    rebuilt,container=rebuild_man_entries(composed,sha256(composed).hexdigest(),requests)
    from .map_build import verify_rebuilt_maps
    map_audits=[audit['map_changes'] for audit in scenes.values() if audit.get('map_changes')]
    if map_audits:
        verify_rebuilt_maps(rebuilt,map_audits)
    for audit in scenes.values():
        if audit.get('animation_changes'):
            verify_rebuilt_maps(rebuilt,audit['animation_changes']['carriers'])
        if audit.get('model_changes'):
            verify_rebuilt_maps(rebuilt,audit['model_changes']['carriers'])
        texture=audit.get('texture_changes')
        if texture:
            verify_rebuilt_maps(rebuilt,texture['carriers'])
    if authored_state_key(project)!=input_key:
        raise ProjectError('Project build inputs changed during draft serialization')
    return rebuilt,dict(schema_version='legaia.authored-draft-archive.v3',
        selected_draft_id=draft_id,drafts=deepcopy(project.actor_drafts),scenes=scenes,
        authored_state_key=input_key,source_disc_sha256=next(iter(scenes.values()))['source_disc_sha256'],
        source_prot_sha256=source_hash,result_prot_sha256=sha256(rebuilt).hexdigest(),
        container=container,archive_asset_changes=asset_audit,gameplay_verified=False)


def _prepare_draft_scene(project, draft_id: str | None, *, defer_rebuild=False, scene_id=None) -> tuple[bytes, dict]:
    """Serialize all drafts in the selected draft's scene; reject omitted scenes."""
    if draft_id is None and defer_rebuild and scene_id in project.imports:
        pass
    elif not isinstance(draft_id,str) or draft_id not in project.actor_drafts:
        raise ProjectError('Select an existing NPC draft')
    input_key=authored_state_key(project)
    overrides=deepcopy(project.overrides)
    if not project.disc_path:
        raise ProjectError('Draft serialization requires the verified source disc')
    drafts=deepcopy(project.actor_drafts)
    draft=drafts[draft_id] if draft_id is not None else {'scene_id':scene_id}
    for identifier,item in drafts.items():
        project._validate_actor_draft(identifier,item)
        if item['scene_id']!=draft['scene_id']:
            raise ProjectError('Experimental draft serialization cannot yet combine multiple scenes')
    document=deepcopy(project.imports[draft['scene_id']])
    scene=document['scene']['name']
    map_components=overrides.pop(draft['scene_id'],None)
    if digest(import_scene(project.disc_path,scene))!=digest(document):
        raise ProjectError('Draft donor evidence differs from the source disc')
    if any(a.get('source_record', {}).get('scene_bundle', {}).get('kind') == 'raw_streaming_man' for a in document['actors']):
        if not defer_rebuild:
            raise ProjectError('Streaming NPC additions require further serialization support')
        from .streaming_build import prepare_streaming_scene
        return prepare_streaming_scene(project, draft['scene_id'])
    actors={a['semantic_id']:a for a in document['actors']}
    edits={}
    assignments={}
    assignment_donors={}
    dialogues={}
    animations={}
    transitions={}
    movements={}
    flags={}
    waits={}
    model_selectors={}
    facing={}
    branches={}
    for identifier,components in overrides.items():
        p2=isinstance(identifier,str) and re.fullmatch(re.escape(f'scene://{scene}/scripts/man-p2/')+r'[0-9]{4}',identifier) is not None
        allowed={'Dialogue','Transitions','ScriptMovement','ScriptFlags','ScriptWaits','ScriptModelSelectors','ScriptFacing','ScriptBranches'} if p2 else {'Transform','ActorAppearance','ActorAnimation','Dialogue','Transitions','ScriptMovement','ScriptFlags','ScriptWaits','ScriptModelSelectors','ScriptFacing','ScriptBranches','AnimationChannels'}
        if (identifier not in actors and not p2) or not isinstance(components,dict) or not components or set(components)-allowed:
            raise ProjectError('Draft serialization requires supported same-scene actor or script components; unsupported authored families cannot be omitted')
        record=int(identifier.rsplit('/',1)[1]) if p2 else actors[identifier]['source_record']['record_index']
        if 'AnimationChannels' in components:
            project._validate_animation_override(identifier,components['AnimationChannels'])
            animations[identifier]=components['AnimationChannels']
        if 'ScriptBranches' in components:
            project._validate_branches(identifier, components['ScriptBranches'])
            branches.update(components['ScriptBranches']['entries'])
        if 'ScriptMovement' in components:
            project._validate_movements(identifier,components['ScriptMovement'])
            movements.update(components['ScriptMovement']['entries'])
        if 'ScriptFlags' in components:
            project._validate_flags(identifier,components['ScriptFlags'])
            flags.update(components['ScriptFlags']['entries'])
        if 'ScriptWaits' in components:
            project._validate_waits(identifier,components['ScriptWaits'])
            waits.update(components['ScriptWaits']['entries'])
        if 'ScriptFacing' in components:
            project._validate_facing(identifier,components['ScriptFacing'])
            facing.update(components['ScriptFacing']['entries'])
        if 'ScriptModelSelectors' in components:
            project._validate_model_selectors(identifier,components['ScriptModelSelectors'])
            model_selectors.update(components['ScriptModelSelectors']['entries'])
        if 'Transitions' in components:
            value=components['Transitions']
            if not isinstance(value,dict) or set(value)!={'entries'} or not isinstance(value['entries'],dict) or not value['entries']:
                raise ProjectError('Draft transitions require a nonempty entries mapping')
            transitions[identifier]=value['entries']
        if 'Dialogue' in components:
            value=components['Dialogue']
            if not isinstance(value,dict) or set(value)!={'runs'} or not isinstance(value['runs'],dict) or not value['runs']:
                raise ProjectError('Draft dialogue requires a nonempty runs mapping')
            dialogues[identifier]=value['runs']
        if 'Transform' in components:
            transform=components['Transform']
            if not isinstance(transform,dict) or set(transform)!={'position'}:
                raise ProjectError('Draft serialization requires exact position overrides')
            edits[record]=transform['position']
        if 'ActorAppearance' in components:
            appearance=components['ActorAppearance']
            if (not isinstance(appearance,dict) or set(appearance)!={'donor_entity_id'} or
                    not isinstance(appearance['donor_entity_id'],str) or appearance['donor_entity_id'] not in actors):
                raise ProjectError('Draft appearance requires a same-scene imported donor')
            donor=actors[appearance['donor_entity_id']]
            assignments[record]=dict(model_index=donor['model_reference']['model_index'],
                                     animation_id=donor['placement_fields']['animation_id'])
            assignment_donors[record]=appearance['donor_entity_id']
        if 'ActorAnimation' in components:
            from .actor_animation import validate
            witness=validate(project,identifier,components['ActorAnimation'],verify_disc=True)
            assignments[record]=dict(model_index=witness['model_reference']['model_index'],
                                     animation_id=witness['placement_fields']['animation_id'])
            assignment_donors[record]=witness['semantic_id']
    context=load_man_assignment_context(project.disc_path,scene) if assignments else None
    dialogue_context=load_dialogue_authoring_context(project.disc_path,scene) if dialogues else None
    transition_context=load_transition_authoring_context(project.disc_path,scene) if transitions else None
    from importer.movement_authoring import load_movement_authoring_context
    movement_context=load_movement_authoring_context(project.disc_path,scene) if movements else None
    from importer.flag_authoring import load_flag_authoring_context
    flag_context=load_flag_authoring_context(project.disc_path,scene) if flags else None
    from importer.wait_authoring import load_wait_authoring_context
    wait_context=load_wait_authoring_context(project.disc_path,scene) if waits else None
    from importer.model_selector_authoring import load_model_selector_authoring_context
    model_selector_context=load_model_selector_authoring_context(project.disc_path,scene) if model_selectors else None
    from importer.facing_authoring import load_facing_authoring_context
    facing_context=load_facing_authoring_context(project.disc_path,scene) if facing else None
    transition_edits={}
    for identifier,entries in transitions.items():
        allowed={item['semantic_id'] for item in transition_context.options(identifier)['transitions']}
        for entry,values in entries.items():
            if entry not in allowed or entry in transition_edits:
                raise ProjectError('Draft transition does not belong to its specified owner')
            transition_edits[entry]=values
    dialogue_edits={}
    dialogue_owners={}
    for identifier,runs in dialogues.items():
        allowed={run['semantic_id']:run for run in dialogue_context.options(identifier)['runs']}
        for run_id,text in runs.items():
            if run_id not in allowed or allowed[run_id]['actor_id']!=identifier or run_id in dialogue_edits:
                raise ProjectError('Draft dialogue run does not belong to the specified actor')
            dialogue_edits[run_id]=text
            dialogue_owners[run_id]=identifier
    if context:
        for record,pair in assignments.items():
            donor_record=actors[assignment_donors[record]]['source_record']['record_index']
            if not any(option['model_index']==pair['model_index'] and option['animation_id']==pair['animation_id']
                       and donor_record in option['donor_records'] for option in context.options(record)['pairs']):
                raise ProjectError('Draft composition has an unsupported appearance donor')
    requests=[dict(id=identifier,donor_record_index=actors[item['donor_entity_id']]['source_record']['record_index'],
                   position=item['position']) for identifier,item in drafts.items()]
    with _disc_context(project.disc_path) as (_,disc_hash,mapping,archive):
        map_patches=[]
        map_audit=None
        if map_components is not None:
            from .map_build import prepare_map_patch
            map_patch,map_audit=prepare_map_patch(project,draft['scene_id'],map_components,archive)
            map_patches.append(map_patch)
        animation_audit=[]
        if animations:
            from .animation_build import prepare_animation_patches
            animation_patches,animation_audit=prepare_animation_patches(project,draft['scene_id'],animations,archive)
            map_patches.extend(animation_patches)
        model_audit=[]
        if project.model_overrides:
            from .model_build import prepare_model_patches
            model_patches,model_audit=prepare_model_patches(project,draft['scene_id'],project.model_overrides,archive)
            map_patches.extend(model_patches)
        texture_audit=[]
        if project.texture_overrides:
            from .texture_build import prepare_texture_patches
            texture_patches,texture_audit=prepare_texture_patches(project,draft['scene_id'],project.texture_overrides,archive)
            map_patches.extend(texture_patches)
        bundle,raw=find_scene_bundle(archive,*_bounded_scene_range(archive,mapping,scene))
        descriptors=[d for d in bundle.descriptors if d.type_byte==3 and d.size]
        if len(descriptors)!=1:
            raise ProjectError('Draft scene requires exactly one MAN descriptor')
        descriptor=descriptors[0]
        source,_=decompress_lzs(raw[bundle.table_offset+descriptor.data_offset:],descriptor.size)
        if context:
            context.patch(assignments,original=source)
        if dialogue_context:
            dialogue_context.patch(dialogue_edits,original=source)
        if transition_context:
            transition_context.patch(transition_edits,original=source)
        if movement_context:
            movement_context.patch(movements,original=source)
        if flag_context:
            flag_context.patch(flags,original=source)
        if wait_context:
            wait_context.patch(waits,original=source)
        if model_selector_context:
            model_selector_context.patch(model_selectors,original=source)
        if facing_context:
            facing_context.patch(facing,original=source)
        if requests:
            candidate,actor_audit=append_actor_candidates(source,sha256(source).hexdigest(),requests)
        else:
            candidate=source
            actor_audit=dict(drafts=[],source_sha256=sha256(source).hexdigest(),
                            result_sha256=sha256(source).hexdigest(),build_ready=False)
        appearance_audit=[]
        if context:
            candidate,appearance_audit=context.patch_appended(candidate,assignments)
            for change in appearance_audit:
                change['donor_entity_id']=assignment_donors[change['record_index']]
                target=f'scene://{scene}/actors/man-p1/{change["record_index"]:04d}'
                animation=overrides.get(target,{}).get('ActorAnimation')
                if animation:
                    change.update(assignment_kind='ActorAnimation',animation_asset_id=animation['animation_asset_id'],
                                  assignment_source_record_sha256=animation['source_record_sha256'])
        candidate,placement_audit=patch_man_positions(candidate,scene,edits)
        dialogue_audit=[]
        if dialogue_context:
            candidate,dialogue_audit=dialogue_context.patch_appended(candidate,dialogue_edits)
            for change in dialogue_audit:
                change['semantic_id']=dialogue_owners[change['run_id']]
        transition_audit=[]
        if transition_context:
            candidate,transition_audit=transition_context.patch_appended(candidate,transition_edits)
        movement_audit=[]
        if movement_context:
            candidate,movement_audit=movement_context.patch_appended(candidate,movements)
        flag_audit=[]
        if flag_context:
            candidate,flag_audit=flag_context.patch_appended(candidate,flags)
        wait_audit=[]
        if wait_context:
            candidate,wait_audit=wait_context.patch_appended(candidate,waits)
        model_selector_audit=[]
        if model_selector_context:
            candidate,model_selector_audit=model_selector_context.patch_appended(candidate,model_selectors)
        facing_audit=[]
        if facing_context:
            candidate,facing_audit=facing_context.patch_appended(candidate,facing)
        branch_audit=[]
        if branches:
            from importer.branch_authoring import load_branch_authoring_context
            branch_context=load_branch_authoring_context(project.disc_path,scene)
            branch_context.patch(branches,original=source)
            candidate,branch_audit=branch_context.patch_appended(candidate,branches)
        # Check the final MAN before reading/repacking the archive. Existing-only
        # edits retain their prior executable compatibility; appended actors need
        # the same qualified native lower bound as ordinary NPC packages.
        pool_evidence = actor_pool_assessment(archive, candidate) if requests else None
        absolute=archive.entry(bundle.entry_index).start_lba*2048+bundle.table_offset
        span=locate_physical_span(archive,absolute)
        prot=archive.image.read_user(archive.node.extent_lba,0,archive.node.size,archive.node.size)
        prot_hash=sha256(prot).hexdigest()
        request=dict(entry_index=span['entry_index'],table_offset=span['offset_within_span'],
                     source_man_sha256=sha256(source).hexdigest(),candidate=candidate)
        if defer_rebuild:
            if archive.header_offset!=0:
                raise ProjectError('Multi-scene draft export requires the primary PROT header')
            rebuilt,container_audit=prot,None
        else:
            composed,_=patch_archive_spans(prot,prot_hash,map_patches)
            rebuilt,container_audit=rebuild_man_entry(composed,sha256(composed).hexdigest(),**request,header_offset=archive.header_offset)
            if map_audit:
                from .map_build import verify_rebuilt_maps
                verify_rebuilt_maps(rebuilt,[map_audit])
            if animation_audit:
                from .map_build import verify_rebuilt_maps
                verify_rebuilt_maps(rebuilt,animation_audit['carriers'])
            if model_audit:
                from .map_build import verify_rebuilt_maps
                verify_rebuilt_maps(rebuilt,model_audit['carriers'])
            if texture_audit:
                from .map_build import verify_rebuilt_maps
                verify_rebuilt_maps(rebuilt,texture_audit['carriers'])
    if authored_state_key(project)!=input_key:
        raise ProjectError('Project build inputs changed during draft serialization')
    return rebuilt,dict(schema_version='legaia.authored-draft-archive.v2',
        selected_draft_id=draft_id,drafts=drafts,scene_id=draft['scene_id'],
        **({'_rebuild_request':request,'_asset_patches':map_patches} if defer_rebuild else {}),
        map_changes=map_audit,
        texture_changes=texture_audit,model_changes=model_audit,animation_changes=animation_audit,
        authored_state_key=input_key,
        imported_document_sha256=digest(document),source_disc_sha256=disc_hash,
        source_prot_sha256=prot_hash,result_prot_sha256=sha256(rebuilt).hexdigest(),
        actor=actor_audit,actor_pool_evidence=pool_evidence,existing_actor_placement_changes=placement_audit,
        existing_actor_appearance_changes=appearance_audit,
        existing_actor_dialogue_changes=dialogue_audit,
        branch_changes=branch_audit, transition_changes=transition_audit, movement_changes=movement_audit, flag_changes=flag_audit, wait_changes=wait_audit, model_selector_changes=model_selector_audit, facing_changes=facing_audit,
        final_man_sha256=sha256(candidate).hexdigest(),
        container=container_audit,gameplay_verified=False)


def export_draft_disc(project, draft_id: str | None, output_directory: Path) -> dict:
    """Write a new experimental disc and audit; never launch or replace a build.

    Failed exports retain their private directory for diagnosis. Only a completed
    report identifies a verified export; a BIN alone is not a successful build.
    """
    from importer.disc_rebuild import write_grown_prot_disc
    from .export_snapshot import capture_export_inputs, write_export_inputs
    directory=Path(output_directory).resolve()
    if directory.exists():
        raise ProjectError('Draft export requires a new output directory')
    input_key,input_files=capture_export_inputs(project)
    archive,audit=prepare_draft_archive(project,draft_id)
    if authored_state_key(project)!=audit['authored_state_key'] or input_key!=audit['authored_state_key']:
        raise ProjectError('Project changed before draft disc export')
    directory.mkdir(parents=True,exist_ok=False)
    input_snapshot=write_export_inputs(directory,input_key,input_files)
    result=write_grown_prot_disc(project.disc_path,audit['source_disc_sha256'],archive,
                                 audit['source_prot_sha256'],directory/'draft.bin')
    if authored_state_key(project)!=audit['authored_state_key']:
        raise ProjectError('Project changed during draft disc export; output has no completed report')
    report=dict(schema_version='legaia.experimental-draft-export.v1',
                archive=audit,disc=result,input_snapshot=input_snapshot,gameplay_verified=False,
                limitations=['Experimental archive/disc rebuild; gameplay acceptance incomplete',
                             'Not integrated with the editor Play workflow']+
                            (['Experimental donor append; incomplete script and scheduling acceptance'] if audit.get('drafts') else []))
    atomic_write(directory/'report.json',canonical(report))
    return report


if __name__ == '__main__':
    import argparse
    from .project import ProjectService
    parser=argparse.ArgumentParser(description='Export experimental NPC drafts without launching the game')
    parser.add_argument('--project',type=Path,required=True)
    parser.add_argument('--draft',help='Optional saved authored-actor UUID; omission exports all authored scenes')
    parser.add_argument('--output',type=Path,required=True,help='New output directory')
    args=parser.parse_args()
    export_draft_disc(ProjectService.open(args.project),args.draft,args.output)
    print(str(args.output.resolve()/'report.json'))
