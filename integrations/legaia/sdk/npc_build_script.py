"""Inspect emitted NPC script records from an intact, current saved normal Build."""
from copy import deepcopy
from hashlib import sha256
import zipfile
from .project import ProjectError
from .project_copy import source_key
from .build import authored_state_key
from .build_history import verify_build,_load,_path
from .build_inventory import MAX_RELOCATION
from importer.pipeline import _bounded_scene_range
from importer.pipeline import _disc_context
from importer.man_source import read_man_source
from importer.model_pack_archive import _archive
from importer.disc_relocation_package import decode_relocation_package
from importer.script_inspection import inspect_record,MAX_RECORD_BYTES,REFERENCE_COMMIT

def _member(archive,name,size,maximum):
    if type(size) is not int or not 0<size<=maximum or archive.getinfo(name).file_size!=size:raise ProjectError('Saved package payload size differs from its bounded receipt')
    with archive.open(name) as stream:data=stream.read(size+1)
    if len(data)!=size:raise ProjectError('Saved package payload grew or was truncated')
    return data

def emitted_prot(source,base_offset,archive,audit):
    relocation=audit.get('relocation_payload')
    if relocation:
        payload=_member(archive,relocation['file'],relocation['size'],MAX_RELOCATION)
        if len(payload)>MAX_RELOCATION or sha256(payload).hexdigest()!=relocation['sha256']:raise ProjectError('Saved relocation payload changed')
        decoded=decode_relocation_package(payload,relocation['sha256'])
        if decoded['prot_lba']*2048!=base_offset or not len(source)<=decoded['source_prot_sectors']*2048<len(source)+2048:raise ProjectError('Saved relocation PROT origin differs from the retail source')
        return decoded['replacement'],'relocated_PROT'
    working=bytearray(source);ranges=[]
    for overlay in audit['overlays']:
        start=overlay['offset']-base_offset;end=start+overlay['size']
        if end<=0 or start>=len(source):continue
        if start<0 or end>len(source) or any(start<b and end>a for a,b in ranges):raise ProjectError('Saved overlays have an ambiguous PROT span')
        payload=_member(archive,overlay['file'],overlay['size'],64*1024*1024)
        if len(payload)!=overlay['size'] or sha256(payload).hexdigest()!=overlay['sha256'] or sha256(source[start:end]).hexdigest()!=overlay['expected_sha256']:raise ProjectError('Saved PROT overlay differs from its source or receipt')
        working[start:end]=payload;ranges.append((start,end))
    return bytes(working),'fixed_span_PROT_overlays'

def actor_allocations(metadata):
    """Select the allocation family from the qualified saved carrier receipt."""
    if not isinstance(metadata,dict):raise ProjectError('Saved NPC allocation metadata is invalid')
    key={'legaia.npc-fixed-span-build.v1':'actor','legaia.npc-compressed-growth-build.v1':'actor','legaia.npc-streaming-growth-build.v1':'actor_changes'}.get(metadata.get('schema_version'))
    audit=metadata.get('draft_audit')
    if key is None or not isinstance(audit,dict) or ('actor' if key=='actor_changes' else 'actor_changes') in audit:
        raise ProjectError('Saved NPC allocation carrier is unsupported or ambiguous')
    allocation=audit.get(key);rows=allocation.get('drafts') if isinstance(allocation,dict) else None
    if not isinstance(rows,list) or not 1<=len(rows)<=128 or any(not isinstance(row,dict) for row in rows):
        raise ProjectError('Saved NPC allocation rows are missing or exceed their bounds')
    return deepcopy(rows)


def inspect(project,entity_id,build_id):
    draft=project.actor_drafts.get(entity_id) if isinstance(entity_id,str) else None
    if not isinstance(draft,dict) or draft.get('scene_id')!=project.active_scene:raise ProjectError('Choose an NPC draft in the active scene')
    project._validate_actor_draft(entity_id,draft)
    if not project.disc_path:raise ProjectError('Saved NPC Build script inspection requires the retail disc')
    key=source_key(project);input_key=authored_state_key(project);captured=deepcopy(draft)
    verified=verify_build(project,build_id)
    if not verified['matches_current_inputs']:raise ProjectError('Saved Build differs from current inputs; Build the current project first')
    receipt,audit=_load(project,build_id);metadata=audit.get('npc_candidates',{}).get(draft['scene_id'],{})
    rows=[row for row in actor_allocations(metadata) if row.get('draft_id')==entity_id]
    if len(rows)!=1:raise ProjectError('Saved Build has no unique emitted record for this NPC')
    allocation=rows[0];index=allocation.get('record_index')
    if type(index) is not int or not 0<=index<32768:raise ProjectError('Saved NPC allocation record index is invalid')
    scene=project.imports[draft['scene_id']]['scene']['name']
    with _disc_context(project.disc_path) as (_,disc_hash,mapping,source_archive):
        if disc_hash!=receipt['source_disc_sha256'] or project.imports[draft['scene_id']]['source']['disc_identity']!='sha256:'+disc_hash:raise ProjectError('Saved NPC Build source disc differs from the project')
        if not 0<source_archive.node.size<=MAX_RELOCATION:raise ProjectError('Source PROT exceeds the saved Build inspection budget')
        source=source_archive.image.read_user(source_archive.node.extent_lba,0,source_archive.node.size,source_archive.node.size)
        with zipfile.ZipFile(_path(project,build_id,receipt['archive_file'])) as package:
            prot,delivery=emitted_prot(source,source_archive.node.extent_lba*2048,package,audit)
        if not 0<len(prot)<=MAX_RELOCATION:raise ProjectError('Emitted PROT exceeds the inspection budget')
        archive=_archive(prot);start,end=_bounded_scene_range(archive,mapping,scene);carrier=read_man_source(archive,start,end,scene)
        actors=[actor for actor in carrier.parsed.actors if actor.record_index==index]
        if len(actors)!=1:raise ProjectError('Saved NPC record is absent or ambiguous in emitted MAN')
        actor=actors[0];donor=allocation['donor']
        if 'appearance' in draft:
            witness=next(a for a in project.imports[draft['scene_id']]['actors'] if a['semantic_id']==draft['appearance']['donor_entity_id'])
            original=read_man_source(source_archive,*_bounded_scene_range(source_archive,mapping,scene),scene)
            donor_actor=next(a for a in original.parsed.actors if a.record_index==witness['source_record']['record_index'])
            donor=dict(model_index=donor_actor.model_index,animation_id=donor_actor.animation_id)
        if (actor.world_x,actor.world_z)!=(draft['position']['x'],draft['position']['z']) or actor.model_index!=donor['model_index'] or actor.animation_id!=donor['animation_id']:raise ProjectError('Saved NPC placement or initial donor binding differs from allocation evidence')
        if not 0<actor.byte_length<=MAX_RECORD_BYTES:raise ProjectError('Saved NPC script exceeds record bounds')
        data=carrier.payload[actor.byte_offset:actor.byte_offset+actor.byte_length];entry=1+data[0]*2+4
        identity='script://generated-npc/'+entity_id.removeprefix('authored-actor://')+'/'+build_id
        source_record=dict(build_id=build_id,archive_sha256=receipt['archive_sha256'],man_sha256=sha256(carrier.payload).hexdigest(),record_index=index,byte_offset=actor.byte_offset,byte_length=len(data),byte_coordinate_space='generated_decoded_MAN')
        report=dict(schema_version='legaia.actor-script-inspection.v1',read_only=True,semantic_id=identity,actor_semantic_id=entity_id,reference_commit=REFERENCE_COMMIT,source_record=source_record,record=dict(record_index=index,byte_offset=actor.byte_offset,byte_length=len(data),script_offset=entry,local_count=data[0],raw_hex=data.hex(),sha256=sha256(data).hexdigest()),**inspect_record(data,entry,semantic_id=identity,base_offset=actor.byte_offset))
        provenance=carrier.provenance()
    if source_key(project)!=key or authored_state_key(project)!=input_key or verify_build(project,build_id)['receipt']!=receipt:raise ProjectError('Project or saved Build changed during NPC script inspection')
    return dict(schema_version='legaia.npc-build-script.v1',entity_id=entity_id,scene_id=draft['scene_id'],project_source_key=key,build_input_key=input_key,draft=captured,donor_entity_id=draft['donor_entity_id'],representation='saved_build',generated_code=True,runtime_binding='not_asserted',gameplay_verified=False,build=dict(id=build_id,archive_sha256=receipt['archive_sha256'],integrity='verified',matches_current_inputs=True,source_disc_integrity='verified',source_disc_sha256=receipt['source_disc_sha256'],delivery=delivery),man_source=provenance,inspection=report)
