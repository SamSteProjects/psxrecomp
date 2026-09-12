"""Experimental saved-draft serialization; not the playable project build path."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import re
from importer.core import find_scene_bundle, decompress_lzs
from importer.pipeline import _disc_context, _bounded_scene_range, import_scene
from importer.man_actor_structure import append_actor_candidates
from importer.man_assignments import load_man_assignment_context
from importer.dialogue_authoring import load_dialogue_authoring_context
from importer.prot_layout import locate_physical_span
from importer.prot_rebuild import rebuild_man_entry
from importer.serialization import patch_man_positions
from .project import ProjectError, digest
from .build import authored_state_key
from .project import atomic_write, canonical


def prepare_draft_archive(project, draft_id: str) -> tuple[bytes, dict]:
    """Serialize all drafts in the selected draft's scene; reject omitted scenes."""
    if not isinstance(draft_id,str) or draft_id not in project.actor_drafts:
        raise ProjectError('Select an existing NPC draft')
    input_key=authored_state_key(project)
    if project.texture_overrides or project.model_overrides:
        raise ProjectError('Experimental draft serialization cannot yet compose other authored overrides')
    overrides=deepcopy(project.overrides)
    if not project.disc_path:
        raise ProjectError('Draft serialization requires the verified source disc')
    drafts=deepcopy(project.actor_drafts)
    draft=drafts[draft_id]
    for identifier,item in drafts.items():
        project._validate_actor_draft(identifier,item)
        if item['scene_id']!=draft['scene_id']:
            raise ProjectError('Experimental draft serialization cannot yet combine multiple scenes')
    document=deepcopy(project.imports[draft['scene_id']])
    scene=document['scene']['name']
    if digest(import_scene(project.disc_path,scene))!=digest(document):
        raise ProjectError('Draft donor evidence differs from the source disc')
    actors={a['semantic_id']:a for a in document['actors']}
    edits={}
    assignments={}
    assignment_donors={}
    dialogues={}
    for identifier,components in overrides.items():
        p2=isinstance(identifier,str) and re.fullmatch(re.escape(f'scene://{scene}/scripts/man-p2/')+r'[0-9]{4}',identifier) is not None
        allowed={'Dialogue'} if p2 else {'Transform','ActorAppearance','Dialogue'}
        if (identifier not in actors and not p2) or not isinstance(components,dict) or not components or set(components)-allowed:
            raise ProjectError('Draft serialization currently composes only same-scene actor positions, appearances and dialogue')
        record=int(identifier.rsplit('/',1)[1]) if p2 else actors[identifier]['source_record']['record_index']
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
    context=load_man_assignment_context(project.disc_path,scene) if assignments else None
    dialogue_context=load_dialogue_authoring_context(project.disc_path,scene) if dialogues else None
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
        candidate,actor_audit=append_actor_candidates(source,sha256(source).hexdigest(),requests)
        appearance_audit=[]
        if context:
            candidate,appearance_audit=context.patch_appended(candidate,assignments)
            for change in appearance_audit:
                change['donor_entity_id']=assignment_donors[change['record_index']]
        candidate,placement_audit=patch_man_positions(candidate,scene,edits)
        dialogue_audit=[]
        if dialogue_context:
            candidate,dialogue_audit=dialogue_context.patch_appended(candidate,dialogue_edits)
            for change in dialogue_audit:
                change['semantic_id']=dialogue_owners[change['run_id']]
        absolute=archive.entry(bundle.entry_index).start_lba*2048+bundle.table_offset
        span=locate_physical_span(archive,absolute)
        prot=archive.image.read_user(archive.node.extent_lba,0,archive.node.size,archive.node.size)
        prot_hash=sha256(prot).hexdigest()
        rebuilt,container_audit=rebuild_man_entry(prot,prot_hash,span['entry_index'],
            span['offset_within_span'],sha256(source).hexdigest(),candidate,header_offset=archive.header_offset)
    if authored_state_key(project)!=input_key:
        raise ProjectError('Project build inputs changed during draft serialization')
    return rebuilt,dict(schema_version='legaia.authored-draft-archive.v2',
        selected_draft_id=draft_id,drafts=drafts,scene_id=draft['scene_id'],
        authored_state_key=input_key,
        imported_document_sha256=digest(document),source_disc_sha256=disc_hash,
        source_prot_sha256=prot_hash,result_prot_sha256=sha256(rebuilt).hexdigest(),
        actor=actor_audit,existing_actor_placement_changes=placement_audit,
        existing_actor_appearance_changes=appearance_audit,
        existing_actor_dialogue_changes=dialogue_audit,
        final_man_sha256=sha256(candidate).hexdigest(),
        container=container_audit,gameplay_verified=False)


def export_draft_disc(project, draft_id: str, output_directory: Path) -> dict:
    """Write a new experimental disc and audit; never launch or replace a build.

    Failed exports retain their private directory for diagnosis. Only a completed
    report identifies a verified export; a BIN alone is not a successful build.
    """
    from importer.disc_rebuild import write_grown_prot_disc
    directory=Path(output_directory).resolve()
    if directory.exists():
        raise ProjectError('Draft export requires a new output directory')
    archive,audit=prepare_draft_archive(project,draft_id)
    if authored_state_key(project)!=audit['authored_state_key']:
        raise ProjectError('Project changed before draft disc export')
    directory.mkdir(parents=True,exist_ok=False)
    result=write_grown_prot_disc(project.disc_path,audit['source_disc_sha256'],archive,
                                 audit['source_prot_sha256'],directory/'draft.bin')
    if authored_state_key(project)!=audit['authored_state_key']:
        raise ProjectError('Project changed during draft disc export; output has no completed report')
    report=dict(schema_version='legaia.experimental-draft-export.v1',
                archive=audit,disc=result,gameplay_verified=False,
                limitations=['Experimental donor append; incomplete script and scheduling acceptance',
                             'Not integrated with the editor Play workflow'])
    atomic_write(directory/'report.json',canonical(report))
    return report


if __name__ == '__main__':
    import argparse
    from .project import ProjectService
    parser=argparse.ArgumentParser(description='Export experimental NPC drafts without launching the game')
    parser.add_argument('--project',type=Path,required=True)
    parser.add_argument('--draft',required=True,help='Saved authored-actor UUID identity')
    parser.add_argument('--output',type=Path,required=True,help='New output directory')
    args=parser.parse_args()
    export_draft_disc(ProjectService.open(args.project),args.draft,args.output)
    print(str(args.output.resolve()/'report.json'))
