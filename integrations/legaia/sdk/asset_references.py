"""Recorded asset relationships, never runtime residency or gameplay reachability."""
from copy import deepcopy
from .project import ProjectError,digest

def source_key(project):
    from .project_inputs import identity
    # Scene-scoped references retain their navigation identity, while every
    # persisted input shares the same project-wide freshness boundary.
    return digest(dict(project_inputs=identity(project),active_scene=project.active_scene))

def _trigger_script_evidence(record,source_scripts,scene,document,*,target_index=None):
    """Qualify a source gate-1 MAP row and its Retail or authored P2 target."""
    encoded=record.get('encoded',{})
    if record.get('table_kind')!=1 or not isinstance(encoded,dict) or encoded.get('gate')!=1:return None
    from hashlib import sha256
    from importer.pipeline import REFERENCE_COMMIT
    def reject(reason):raise ProjectError('Invalid field trigger script reference '+reason)
    def integer(value,minimum,maximum):return type(value) is int and minimum<=value<=maximum
    def hash_value(value):return isinstance(value,str) and len(value)==64 and all(c in '0123456789abcdef' for c in value)
    name=scene.removeprefix('scene://');table=record.get('table_source');row=record.get('record_index')
    index=encoded.get('record_index');source=record.get('source_record');reference=record.get('script_reference')
    if (not scene.startswith('scene://') or table not in ('primary','fallback') or not integer(row,0,2042) or
            type(record.get('table_kind')) is not int or
            set(encoded)!={'tile_x','tile_z','record_index','gate'} or
            any(not integer(encoded[key],0,255) for key in encoded) or
            record.get('kind')!='trigger' or record.get('asset_kind')!='trigger' or
            record.get('id')!=f'trigger://{name}/field-map/{table}/kind-1/{row:04d}' or
            record.get('semantic_id')!=record['id'] or record.get('scene_id',scene)!=scene or
            record.get('collision_id')!=f'collision://{name}/field-map' or
            record.get('reference_commit')!=REFERENCE_COMMIT or record.get('trigger_type')!='partition_2_trigger' or
            not isinstance(reference,dict) or set(reference)!={'partition','record_index','status','index_space'} or
            reference['index_space']!='partition_local' or
            type(reference['partition']) is not int or reference['partition']!=2 or reference['record_index']!=index or
            type(reference['record_index']) is not int or reference['status']!='unresolved_source_reference'):
        reject('identity or encoded row')
    if not isinstance(source,dict):reject('missing trigger source')
    disc=source.get('disc');base=0x10000 if table=='primary' else 0
    if (not isinstance(disc,dict) or set(disc)!={'sha256','serial'} or not hash_value(disc['sha256']) or disc['serial']!='SCUS-94254' or
            source.get('iso_file')!='PROT.DAT' or source.get('prot_entry_name')!=name or
            not integer(source.get('prot_entry_index'),0,0xffffffff) or not integer(source.get('prot_start_lba'),0,0xffffffff) or
            source.get('byte_coordinate_space')!='prot_entry' or type(source.get('byte_length')) is not int or source['byte_length']!=4 or
            source.get('table_source')!=table or type(source.get('table_kind')) is not int or source['table_kind']!=1 or
            type(source.get('record_index')) is not int or source['record_index']!=row or
            not integer(source.get('byte_offset'),base+18+row*4,base+0x2000-4) or
            type(source.get('containing_span_byte_offset')) is not int or source['containing_span_byte_offset']!=base or
            type(source.get('containing_span_byte_length')) is not int or source['containing_span_byte_length']!=0x2000 or
            not hash_value(source.get('containing_span_sha256')) or
            source.get('sha256')!=sha256(bytes(encoded[key] for key in ('tile_x','tile_z','record_index','gate'))).hexdigest()):
        reject('trigger provenance or row hash')
    imported_disc=document.get('source',{}).get('disc_identity')
    if isinstance(imported_disc,str) and imported_disc.startswith('sha256:') and imported_disc!='sha256:'+disc['sha256']:
        reject('trigger disc differs from imported scene')
    if target_index is not None:
        if table != 'primary' or not integer(target_index,0,255):reject('authored target scope')
        index=target_index
    target=f'script://{name}/scripts/man-p2/{index:04d}';scripts=source_scripts.get(target,[])
    # Missing, multiply recorded and aliased P2 targets stay unresolved. The row
    # retains its source identity, with no guessed script or runtime dispatch.
    if len(scripts)!=1:return None
    script=scripts[0];script_source=script.get('source_record')
    if (script.get('kind')!='script' or script.get('asset_kind')!='script' or script.get('semantic_id')!=target or
            script.get('script_id')!=target or script.get('scene_id',scene)!=scene or
            type(script.get('partition')) is not int or script['partition']!=2 or
            script.get('owner_semantic_id')!='scene://'+target.removeprefix('script://') or script.get('actor_semantic_id') is not None or
            script.get('reference_commit')!=REFERENCE_COMMIT or not isinstance(script_source,dict) or
            script_source.get('disc')!=disc or script_source.get('iso_file')!='PROT.DAT' or
            type(script_source.get('partition')) is not int or script_source['partition']!=2 or
            type(script_source.get('record_index')) is not int or script_source['record_index']!=index or
            not integer(script_source.get('prot_entry_index'),0,0xffffffff) or
            script_source.get('prot_entry_name',name)!=name or
            script_source.get('byte_coordinate_space') not in ('decoded_lzs_descriptor','raw_man_payload')):
        reject('P2 identity or provenance')
    if script_source.get('record_alias_count') is None or script_source.get('byte_offset') is None or script_source.get('sha256') is None:
        if script.get('status')=='unavailable':return None
        reject('missing bounded P2 record')
    if (not integer(script_source.get('record_alias_count'),1,512) or not hash_value(script_source.get('sha256')) or
            not integer(script_source.get('byte_offset'),0,4*1024*1024) or
            not integer(script_source.get('byte_length'),1,4*1024*1024-script_source['byte_offset'])):
        reject('P2 bounds or record hash')
    if script_source['record_alias_count']!=1:return None
    return target,dict(trigger_source_record_sha256=source['sha256'],script_source_record_sha256=script_source['sha256'],
                       table_source=table,table_kind=1,trigger_row_index=row,partition_two_record_index=index,
                       gate=1,reachability='not_evaluated')

def _reference_clip_evidence(record,model_records):
    """Validate an explicit pinned catalog association, never an actor assignment."""
    if record.get('association_kind')!='reference_pinned_global_model_clip':return None
    from importer.animation import MAX_BUNDLE_BYTES,MAX_FRAMES,animation_capabilities
    from importer.pipeline import REFERENCE_COMMIT,REFERENCE_REPOSITORY
    def reject(reason):raise ProjectError('Invalid reference-pinned model/clip '+reason)
    def integer(value,minimum,maximum):return type(value) is int and minimum<=value<=maximum
    preview=record.get('preview')
    if (record.get('kind')!='animation' or record.get('asset_kind')!='animation' or record.get('scope')!='global-field' or
        record.get('reference_commit')!=REFERENCE_COMMIT or not isinstance(preview,dict) or set(preview)!={'asset_id','clip_id'} or
        record.get('bindings')!=[] or record.get('actor_semantic_ids',[])!=[] or record.get('runtime_state')!='not_observed'):
        reject('association metadata')
    models=tuple(f'asset://legaia/models/global-special/{0xf0+slot:04x}' for slot in range(5))
    model=preview['asset_id'];clip=preview['clip_id']
    if model not in models or record.get('asset_semantic_ids')!=[model]:reject('model identity')
    slot=models.index(model)
    if clip not in (('idle','walk') if slot<3 else ('loop',)):reject('clip identity')
    index=slot*7+(1 if clip=='idle' else 0) if slot<3 else slot+18
    identity=f'animation://legaia/field-locomotion/{index:04d}'
    if record.get('id')!=identity or record.get('semantic_id')!=identity or not integer(record.get('record_index'),0,22) or record['record_index']!=index:
        reject('record identity')
    frames=record.get('frame_count');channels=record.get('channel_count')
    expected_channels=10 if slot<3 else 3 if slot==3 else 2
    if not integer(frames,1,MAX_FRAMES) or not integer(channels,1,64) or channels!=expected_channels or type(record.get('bone_count')) is not int or record['bone_count']!=channels:
        reject('decoded counts')
    source=record.get('source_record')
    source_keys={'disc','iso_file','prot_entry_index','container_section','compressed_stream_offset','compressed_bytes_consumed',
                 'record_index','byte_offset','byte_length','byte_coordinate_space','containing_size'}
    if not isinstance(source,dict) or set(source)!=source_keys:reject('source metadata')
    disc=source['disc']
    if (not isinstance(disc,dict) or set(disc)!={'sha256','serial'} or disc['serial']!='SCUS-94254' or
        not isinstance(disc['sha256'],str) or len(disc['sha256'])!=64 or any(c not in '0123456789abcdef' for c in disc['sha256'])):
        reject('disc identity')
    if (source['iso_file']!='PROT.DAT' or type(source['prot_entry_index']) is not int or source['prot_entry_index']!=874 or
        type(source['container_section']) is not int or source['container_section']!=1 or
        source['byte_coordinate_space']!='decoded_lzs_section' or not integer(source['record_index'],0,22) or source['record_index']!=index):
        reject('source locator')
    if (not integer(source['compressed_stream_offset'],0,0xffffffff) or not integer(source['compressed_bytes_consumed'],1,0xffffffff) or
        source['compressed_stream_offset']+source['compressed_bytes_consumed']>0xffffffff or
        not integer(source['containing_size'],96,MAX_BUNDLE_BYTES) or not integer(source['byte_offset'],96,MAX_BUNDLE_BYTES) or
        not integer(source['byte_length'],16,MAX_BUNDLE_BYTES) or source['byte_length']!=16+frames*channels*8 or
        source['byte_offset']+source['byte_length']>source['containing_size']):
        reject('source bounds')
    for imported_model in model_records.get(model,[]):
        model_source=imported_model.get('source_record',{})
        if (not animation_capabilities(imported_model)['supported'] or model_source.get('disc')!=disc or
            model_source.get('iso_file')!='PROT.DAT' or any(type(model_source.get(key)) is not int for key in ('prot_entry_index','container_section','pack_slot')) or
            ('reference_commit' in imported_model and imported_model['reference_commit']!=REFERENCE_COMMIT)):
            reject('imported model provenance')
        # The importer records its reference pin in claim evidence, not a model
        # top-level field. Fresh verification remains the caller's responsibility.
        for claim in imported_model.get('claims',[]):
            if claim.get('property')!='source_record':continue
            proofs=[proof for proof in claim.get('evidence',[]) if proof.get('source')==REFERENCE_REPOSITORY]
            if (claim.get('confidence')!='confirmed' or claim.get('value')!=model_source or claim.get('source')!=model_source or
                not proofs or any(proof.get('commit')!=REFERENCE_COMMIT for proof in proofs)):
                reject('imported model reference pin')
    return dict(reference_commit=REFERENCE_COMMIT,model_id=model,clip_id=clip,record_index=index,
                frame_count=frames,channel_count=channels,source_record=deepcopy(source))

def assemble(project,catalog,identifier,materials=None,*,_full_graph=False,_audio_snapshot=None):
    """Adapt explicit imported/derived references; callers verify retail sources first."""
    if not isinstance(identifier,str) or not identifier or len(identifier)>1024:raise ProjectError('Invalid asset reference identity')
    nodes={};edges={};unresolved=0;memberships={};navigation={};model_records={}
    from .audio_reference_snapshot import AudioReferenceSnapshot
    own_audio_snapshot=_audio_snapshot is None
    audio_snapshot=AudioReferenceSnapshot(project) if own_audio_snapshot else _audio_snapshot
    audio_snapshot.check_owner(project)
    wav_inputs=audio_snapshot.inputs()
    midi_inputs=audio_snapshot.midi_inputs()
    import_digests={scene:digest(document) for scene,document in project.imports.items()}
    def node(identifier,kind,scene,label=None,available=True):
        if not isinstance(identifier,str) or not identifier or len(identifier)>1024:raise ProjectError('Invalid asset reference identity')
        value=dict(id=identifier,kind=kind,scene_id=scene,label=label or identifier,available=available)
        memberships.setdefault(identifier,set()).add(scene)
        if available and scene in project.imports:navigation.setdefault(identifier,set()).add(scene)
        if identifier in nodes:
            if nodes[identifier]['kind']!=kind:raise ProjectError('Conflicting asset reference type')
            if available:nodes[identifier]['available']=True
        else:nodes[identifier]=value
        if len(nodes)>16384:raise ProjectError('Asset reference node limit exceeded')
    def edge(source,target,kind,scene,layer='imported',pc=None,evidence=None,animation_evidence=None,reference_clip_evidence=None,flag_evidence=None,transition_evidence=None,trigger_evidence=None,trigger_binding_evidence=None,flag_binding_evidence=None,allocated_evidence=None,retained_evidence=None,wav_evidence=None,current_wav_evidence=None,npc_script_evidence=None,npc_flag_evidence=None,npc_transition_evidence=None,midi_evidence=None,current_midi_evidence=None,controller_evidence=None):
        if source not in nodes or target not in nodes:raise ProjectError('Asset reference has an unavailable structural endpoint')
        value=dict(source_id=source,target_id=target,kind=kind,scene_id=scene,layer=layer,runtime_binding='not_asserted')
        if pc is not None:value['pc']=pc
        value['source_import_sha256']=import_digests[scene]
        if layer=='decoded':value['source_catalog_key']=catalog['source_key']
        if evidence is not None:
            value['material_evidence']=deepcopy(evidence)
            if layer=='effective':value['source_catalog_key']=catalog['source_key']
        if animation_evidence is not None:
            value['effective_animation_evidence']=deepcopy(animation_evidence)
            value['source_catalog_key']=catalog['source_key']
        if reference_clip_evidence is not None:value['reference_clip_evidence']=deepcopy(reference_clip_evidence)
        if flag_evidence is not None:value['flag_reference_evidence']=deepcopy(flag_evidence)
        if flag_binding_evidence is not None:
            value['flag_binding_evidence']=deepcopy(flag_binding_evidence)
            value['source_catalog_key']=catalog['source_key']
        if transition_evidence is not None:value['transition_reference_evidence']=deepcopy(transition_evidence)
        if trigger_evidence is not None:value['trigger_reference_evidence']=deepcopy(trigger_evidence)
        if trigger_binding_evidence is not None:
            value['trigger_binding_evidence']=deepcopy(trigger_binding_evidence)
            value['source_catalog_key']=catalog['source_key']
        if allocated_evidence is not None:
            value['allocated_animation_evidence']=deepcopy(allocated_evidence)
            value['source_catalog_key']=catalog['source_key']
        if retained_evidence is not None:
            value['retained_capture_evidence']=deepcopy(retained_evidence)
            value['source_catalog_key']=catalog['source_key']
        if current_midi_evidence is not None:value['current_midi_binding_evidence']=deepcopy(current_midi_evidence)
        if midi_evidence is not None:value['midi_input_evidence']=deepcopy(midi_evidence)
        if wav_evidence is not None:value['wav_input_evidence']=deepcopy(wav_evidence)
        if current_wav_evidence is not None:value['current_wav_binding_evidence']=deepcopy(current_wav_evidence)
        if npc_script_evidence is not None:
            value['npc_script_donor_evidence']=deepcopy(npc_script_evidence)
            value['source_catalog_key']=catalog['source_key']
        if npc_flag_evidence is not None:
            value['npc_flag_operand_evidence']=deepcopy(npc_flag_evidence)
            value['source_catalog_key']=catalog['source_key']
        if npc_transition_evidence is not None:
            value['npc_transition_arrival_evidence']=deepcopy(npc_transition_evidence)
            value['source_catalog_key']=catalog['source_key']
        if controller_evidence is not None:value['controller_source_evidence']=deepcopy(controller_evidence)
        value['id']=digest(value);edges[value['id']]=value
        if len(edges)>32768:raise ProjectError('Asset reference edge limit exceeded')
    for scene,document in sorted(project.imports.items()):
        node(scene,'scene',scene,document['scene']['name'])
        for actor in document['actors']:
            node(actor['semantic_id'],'actor',scene,'Actor '+actor['semantic_id'].rsplit('/',1)[-1]);edge(scene,actor['semantic_id'],'scene_actor',scene)
        for model in document['assets'].get('models',[]):
            model_records.setdefault(model['semantic_id'],[]).append(model)
            node(model['semantic_id'],'model',scene,model.get('name') or 'Model '+model['semantic_id'].rsplit('/',1)[-1]);edge(scene,model['semantic_id'],'scene_model_catalog',scene)
    for identifier_draft,draft in sorted(project.actor_drafts.items()):
        node(identifier_draft,'actor',draft['scene_id'],draft['name']);edge(identifier_draft,draft['donor_entity_id'],'draft_donor',draft['scene_id'],'authored')
    for actor_id,components in sorted(project.overrides.items()):
        donor=components.get('ActorAppearance',{}).get('donor_entity_id')
        if donor and donor!=actor_id:
            if actor_id in nodes and donor in nodes:edge(actor_id,donor,'appearance_donor',nodes[actor_id]['scene_id'],'authored')
            else:unresolved+=1
    model_references=project.model_references()
    effective_bindings={}
    for ref in model_references:
        if ref['effective'] and not project.overrides.get(ref['source_id'],{}).get('ActorAllocatedAnimation'):
            donor=ref['effective_donor_id']
            if project.overrides.get(ref['source_id'],{}).get('ActorAnimation'):
                from .actor_animation import source_actor
                donor=source_actor(project,ref['source_id'])['semantic_id']
            effective_bindings.setdefault((ref['scene_id'],donor,ref['target_id']),[]).append(ref)
        if ref['target_id'] not in nodes:unresolved+=1;continue
        if ref['imported']:edge(ref['source_id'],ref['target_id'],'initial_model',ref['scene_id'])
        if ref['effective']:edge(ref['source_id'],ref['target_id'],'effective_initial_model',ref['scene_id'],'effective')
    scene=project.active_scene
    reference_clips={};source_scripts={};transition_ids=set();trigger_ids=set();controller_ids=set()
    for record in catalog['records']:
        if record['kind']=='controller':
            if record['id'] in controller_ids:raise ProjectError('Duplicate scene controller source ownership')
            controller_ids.add(record['id'])
        if record['kind']=='script':source_scripts.setdefault(record['id'],[]).append(record)
        if record['kind']=='transition':
            if record['id'] in transition_ids:raise ProjectError('Duplicate transition reference identity')
            transition_ids.add(record['id'])
        if record['kind']=='trigger':
            if record['id'] in trigger_ids:raise ProjectError('Duplicate field trigger reference identity')
            trigger_ids.add(record['id'])
        evidence=_reference_clip_evidence(record,model_records)
        if evidence is not None:reference_clips[record['id']]=evidence
        node(record['id'],record['kind'],scene,record.get('name'))
        if record.get('scope')=='authored-retained':
            model=record['model_asset_id'];row=record['retained_record']
            if model not in nodes:raise ProjectError('Retained clip capture lacks an imported model endpoint')
            proof={**record['source_record'],'model_id':model,'channel_owner_entity_id':row['channel_owner_entity_id'],
                   'model_source_entity_id':row['model_source_entity_id'],'frame_count':row['frame_count'],
                   'object_count':row['object_count'],'active':row['active']}
            edge(record['id'],model,'retained_model_capture',scene,'authored',retained_evidence=proof)

    # An authored clone retains a recorded retail source; it is not the
    # generated script, and a relationship cannot establish live execution.
    from .npc_script_references import evidence as npc_script_evidence
    npc_flag_owners={};npc_flag_sites=set();npc_flag_consumed={};npc_arrival_owners={};npc_arrival_consumed={}
    for owner,draft in sorted(project.actor_drafts.items()):
        if draft['scene_id']!=scene:continue
        target='script://'+draft['donor_entity_id'].removeprefix('scene://')
        records=source_scripts.get(target,[])
        if not records:
            unresolved+=1;continue
        if len(records)!=1:raise ProjectError('NPC script donor has duplicate source records')
        proof=npc_script_evidence(draft,records[0],scene)
        if proof is None:unresolved+=1;continue
        edge(owner,target,'draft_script_donor',scene,'authored',npc_script_evidence=proof)
        if any(r['kind']=='transition' and r.get('owner_id')==draft['donor_entity_id'] for r in catalog['records']) and project.disc_path:
            from .npc_transition_references import targets
            context,qualified=targets(project,draft)
            npc_arrival_owners.setdefault(draft['donor_entity_id'],[]).append((owner,draft,proof,context,qualified))
        if 'flags' in draft:
            from .npc_flags import validate as validate_npc_flags
            validate_npc_flags(project,draft)
        targets={row['semantic_id']:row for row in project._flag_context(draft['donor_entity_id']).options(draft['donor_entity_id'])['targets']} if 'flags' in draft else {}
        if 'system_flags' in draft:
            from .npc_system_flags import qualify, context_for
            qualify(project,draft)
            targets.update({row['semantic_id']:row for row in context_for(project,draft['donor_entity_id']).options(draft['donor_entity_id'])['targets']})
        npc_flag_owners.setdefault(draft['donor_entity_id'],[]).append((owner,draft,proof,records[0],targets))

    # These are historical capture targets, not Current native assignments.
    audio_records={r['id']:r for r in catalog['records'] if r['kind']=='audio'}
    for identity,rows in wav_inputs['receipts'].items():
        for receipt in rows:
            if receipt['source_scene_id']!=scene:continue
            target=receipt['asset_id'];native=audio_records.get(target)
            if native is not None and native.get('source_record',{}).get('sha256')!=receipt['source_record']['entry_sha256']:
                raise ProjectError('Historical WAV target differs from its qualified native catalog entry')
            node(identity,'audio',scene,wav_inputs['assets'][identity]['name'])
            node(target,'audio',scene,'Historical capture target '+target,available=native is not None)
            proof={key:deepcopy(receipt[key]) for key in ('receipt_key','wav_sha256','sample_index','source_scene_id','bank_sha256','source_sample_sha256')}
            proof.update(native_asset_id=target,disc_sha256=receipt['source_record']['disc_sha256'],entry_sha256=receipt['source_record']['entry_sha256'],relationship='historical_capture_target')
            edge(target,identity,'retained_wav_sample_input',scene,'authored',wav_evidence=proof)

    for identity,rows in midi_inputs['receipts'].items():
        for receipt in rows:
            if receipt['source_scene_id']!=scene:continue
            target=receipt['asset_id'];native=audio_records.get(target)
            if native is not None and native.get('source_record',{}).get('sha256')!=receipt['source_record']['entry_sha256']:
                raise ProjectError('Historical MIDI target differs from its qualified native catalog entry')
            node(identity,'audio',scene,midi_inputs['assets'][identity]['name'])
            node(target,'audio',scene,'Historical capture target '+target,available=native is not None)
            proof={key:deepcopy(receipt[key]) for key in ('receipt_key','midi_sha256','source_scene_id','candidate_sequence_sha256')}
            proof.update(native_asset_id=target,disc_sha256=receipt['source_record']['disc_sha256'],entry_sha256=receipt['source_record']['entry_sha256'],sequence_sha256=receipt['source_record']['sequence_sha256'],relationship='historical_capture_target',input_usage='not_asserted')
            edge(target,identity,'retained_midi_sequence_input',scene,'authored',midi_evidence=proof)

    for proof in audio_snapshot.midi_bindings():
        if proof['binding_scene_id']!=scene:continue
        native_id,midi_id=proof['native_asset_id'],proof['midi_asset_id'];native=audio_records.get(native_id)
        if native is not None and native.get('source_record',{}).get('sha256')!=proof['binding']['source_record']['entry_sha256']:
            raise ProjectError('Current MIDI replacement differs from its qualified native catalog entry')
        node(native_id,'audio',scene,available=native is not None)
        node(midi_id,'audio',scene,midi_inputs['assets'][midi_id]['name'])
        edge(native_id,midi_id,'current_native_sequence_midi_binding',scene,'effective',current_midi_evidence=proof)

    for proof in audio_snapshot.bindings():
        if proof['binding_scene_id']!=scene:continue
        native_id,wav_id=proof['native_asset_id'],proof['wav_asset_id']
        native=audio_records.get(native_id)
        if native is not None and native.get('source_record',{}).get('sha256')!=proof['retail_entry_sha256']:
            raise ProjectError('Current WAV binding differs from its qualified native catalog entry')
        node(native_id,'audio',scene,available=native is not None)
        node(wav_id,'audio',scene,wav_inputs['assets'][wav_id]['name'])
        edge(native_id,wav_id,'current_native_sample_wav_binding',scene,'effective',current_wav_evidence=proof)

    from .allocated_animation_references import bindings as allocated_bindings
    for retained in allocated_bindings(project,scene) if catalog.get('source_key') else []:
        owner,clip,model=retained['owner_id'],retained['animation_id'],retained['model_id']
        if owner not in nodes or model not in nodes:raise ProjectError('Allocated clip reference lacks an imported actor/model endpoint')
        node(clip,'animation',scene,'Retained clip '+retained['proof']['record_id'],available=False)
        edge(owner,clip,'allocated_initial_animation_binding',scene,'effective',allocated_evidence=retained['assignment_proof'])
        edge(clip,model,'allocated_model_clip_binding',scene,'authored',allocated_evidence=retained['proof'])
    trigger_binding=project.overrides.get(scene,{}).get('TriggerScripts')
    trigger_assignments={}
    if trigger_binding is not None and catalog['records']:
        if project._validate_trigger_scripts(scene,trigger_binding) != trigger_binding:
            raise ProjectError('Authored trigger reference binding is not canonical')
        from importer.trigger_authoring import trigger_authoring_options
        from hashlib import sha256
        trigger_map=project._environment_source(scene)
        if sha256(trigger_map).hexdigest()!=trigger_binding['source_sha256']:
            raise ProjectError('Authored trigger reference MAP source changed')
        trigger_source_rows={r['trigger_id']:r for r in trigger_authoring_options(trigger_map,project.imports[scene]['scene']['name'])['records']}
        trigger_assignments={row['trigger_id']:row for row in trigger_binding['edits']}
        if set(trigger_assignments)-trigger_ids:
            raise ProjectError('Authored trigger reference is absent from the verified catalog')
    for record in catalog['records']:
        identity=record['id'];kind=record['kind']
        if kind=='controller':
            from .controller_references import controller_source_evidence
            proof=controller_source_evidence(record,scene,project.imports[scene])
            edge(scene,identity,'scene_entry_controller_source',scene,'decoded',controller_evidence=proof)
        elif kind=='script':
            actor=record.get('actor_semantic_id')
            if actor in nodes:edge(actor,identity,'actor_script_record',scene,'decoded')
            elif actor is not None:unresolved+=1
            for transition in record.get('transitions',[]):
                name=transition.get('target_scene_name')
                if name:
                    target='scene://'+name;node(target,'scene',target,name,target in project.imports);edge(identity,target,'encoded_scene_change',scene,'decoded',transition['pc'])
                else:unresolved+=1
            # Model pool selectors explicitly have unresolved runtime pool bases.
            unresolved+=len(record.get('model_selection_references',[]))
        elif kind=='dialogue':
            target=record.get('script_id')
            if target in nodes:edge(target,identity,'script_dialogue_segment',scene,'decoded',record.get('pc'))
            else:unresolved+=1
        elif kind=='flag':
            from .flag_assets import validate_flag_asset
            validate_flag_asset(record)
            target=record['script_id']
            if 'controller_source_evidence' in record:
                controller=next((row for row in catalog['records'] if row['id']==target and row['kind']=='controller'),None)
                from .controller_references import controller_source_evidence
                if controller is None or controller_source_evidence(controller,scene,project.imports[scene])!=record['controller_source_evidence']:
                    raise ProjectError('Controller flag group differs from its source controller')
                from .controller_flag_assets import REFERENCE_FIELDS
                expected=[row for row in controller['flag_references'] if row['bank']==record['bank'] and row['index']==record['index'] and row['extended_target']==record['extended_target']]
                if [{key:row[key] for key in REFERENCE_FIELDS} for row in record['references']]!=expected:
                    raise ProjectError('Controller flag group omits or changes decoded source operands')
                from .controller_system_flags import COMPONENT,validate,validate_components
                components=project.overrides.get(record['owner_id'],{})
                if components:
                    validate_components(project,record['owner_id'],components)
                    if any(value['source_record_sha256']!=record['source_record']['sha256'] for value in components.values()):
                        raise ProjectError('Controller flag graph differs from saved source ownership')
                system=record['bank']=='system'
                if not system:
                    from .controller_flag_bits import COMPONENT,validate
                component=components.get(COMPONENT)
                if component is not None:
                    validate(project,record['owner_id'],component)
                entries=component['entries'] if component else {}
                for reference in record['references']:
                    family='system-flag' if system else 'flag-bit';field='index' if system else 'bit'
                    operand=target+f"/{family}/{reference['pc']:04x}"
                    saved=entries.get(operand)
                    if reference['authored_index']!=(saved[field] if saved else None):
                        raise ProjectError('Controller flag graph differs from authored project selector')
                    proof={key:deepcopy(record[key]) for key in ('bank','index','scope','extended_target','grouping_layer')}
                    proof.update(operation=reference['operation'],mnemonic=reference['mnemonic'])
                    edge(target,identity,'controller_flag_reference',scene,'decoded',reference['pc'],flag_evidence=proof,controller_evidence=record['controller_source_evidence'])
                    if saved is not None:
                        binding=dict(operand_id=operand,retail_index=reference['retail_index'],effective_index=reference['effective_index'],
                            source_record_sha256=record['source_record']['sha256'],component_sha256=digest(component),
                            native_operand_qualification=deepcopy(reference['authored_qualification']))
                        edge(target,identity,'effective_controller_flag_reference',scene,'effective',reference['pc'],
                            flag_evidence=proof,flag_binding_evidence=binding,controller_evidence=record['controller_source_evidence'])
                continue
            if target not in nodes or nodes[target]['kind']!='script':
                raise ProjectError('Flag reference has no verified source script')
            scripts=source_scripts.get(target,[])
            if len(scripts)!=1 or scripts[0].get('source_record')!=record['source_record']:
                raise ProjectError('Flag reference differs from its unique source script or record hash')
            system=record['bank']=='system'
            component=project.overrides.get(record['owner_id'],{}).get('ScriptSystemFlags' if system else 'ScriptFlags')
            if component is not None:
                if system:
                    from .system_flags import validate
                    validate(project,record['owner_id'],component)
                else:project._validate_flags(record['owner_id'],component)
            entries=component.get('entries',{}) if component is not None else {}
            for reference in record['references']:
                operand=reference['flag_operand_id']
                authored=entries.get(operand)
                if reference['authored_index'] != (authored['index' if system else 'bit'] if authored is not None else None):
                    raise ProjectError('Flag reference differs from its authored operand binding')
                proof={key:deepcopy(record[key]) for key in ('bank','index','scope','extended_target','grouping_layer')}
                proof.update(operation=reference['operation'],mnemonic=reference['mnemonic'])
                edge(target,identity,'script_flag_reference',scene,'decoded',reference['pc'],flag_evidence=proof)
                from .npc_flag_references import binding as npc_flag_binding
                for owner,draft,donor_proof,script,targets in npc_flag_owners.get(record['owner_id'],[]):
                    site=(owner,reference['pc'])
                    if site in npc_flag_sites:raise ProjectError('Duplicate NPC flag instruction ownership')
                    npc_flag_sites.add(site)
                    npc_operand='script://'+record['owner_id'][8:]+f"/system-flag/{reference['pc']:04x}" if system else operand
                    if system and npc_operand not in draft.get('system_flags',{}).get('entries',{}):npc_operand=None
                    npc_reference=dict(reference,flag_operand_id=npc_operand)
                    binding=npc_flag_binding(draft,donor_proof,record,npc_reference,script,targets.get(npc_operand))
                    if binding['authored_index'] is not None:npc_flag_consumed.setdefault(owner,set()).add(binding['operand_id'])
                    edge(owner,identity,'npc_script_flag_operand',scene,'authored',reference['pc'],flag_evidence=proof,npc_flag_evidence=binding)
                if authored is not None:
                    binding=dict(operand_id=operand,retail_index=reference['retail_index'],
                                 effective_index=reference['effective_index'],
                                 source_record_sha256=record['source_record']['sha256'],
                                 component_sha256=digest(component))
                    if 'authored_qualification' in reference:binding['native_operand_qualification']=deepcopy(reference['authored_qualification'])
                    edge(target,identity,'effective_script_flag_reference',scene,'effective',reference['pc'],
                         flag_evidence=proof,flag_binding_evidence=binding)
        elif kind=='transition':
            from .transition_assets import validate_transition_asset
            validate_transition_asset(record)
            if record['source']!=scene:raise ProjectError('Transition reference belongs to another resource scene')
            scripts=source_scripts.get(record['script_id'],[])
            if len(scripts)!=1 or nodes[record['script_id']]['kind']!='script':
                raise ProjectError('Transition reference has no unique verified source script')
            script=scripts[0];source=script.get('source_record')
            if (source!=record['source_record'] or script.get('semantic_id',script['id'])!=record['script_id'] or
                    (script.get('owner_semantic_id') or script.get('actor_semantic_id'))!=record['owner_id'] or
                    script.get('status')!=record['script_status'] or script.get('name')!=record['script_name']):
                raise ProjectError('Transition reference differs from its source script or record hash')
            stops=script.get('stops');stop_count=script.get('stop_count',len(stops) if isinstance(stops,list) else None)
            if (stops is not None and not isinstance(stops,list) or type(stop_count) is not int or stop_count<0 or
                    stops is not None and stop_count!=len(stops) or stop_count!=record['script_stop_count']):
                raise ProjectError('Transition inspection stops differ from its verified source script')
            reference=record['reference'];matches=[row for row in script.get('transitions',[]) if row.get('pc')==reference['pc']]
            if len(matches)!=1 or matches[0]!=reference:
                raise ProjectError('Transition destination or instruction differs from its verified source script')
            name=reference['target_scene_name'];destination='scene://'+name if name is not None else None
            proof=dict(transition_id=record['entry_layers']['transition_id'],source_record_sha256=record['source_record']['sha256'],
                       destination_scene_id=destination,extended_target=reference['extended_target'],name_sha256=reference['name_sha256'],
                       status=reference['status'],reachability='not_evaluated')
            edge(record['script_id'],identity,'script_transition_reference',scene,'decoded',reference['pc'],transition_evidence=proof)
            if destination is not None:
                node(destination,'scene',destination,name,destination in project.imports)
                edge(identity,destination,'transition_destination_source',scene,'decoded',reference['pc'],transition_evidence=proof)
            from .npc_transition_references import binding as arrival_binding
            for owner,draft,donor,context,qualified in npc_arrival_owners.get(record['owner_id'],[]):
                arrival=arrival_binding(draft,donor,record,script,context,qualified)
                if arrival is None:continue
                edge(owner,identity,'npc_script_transition_arrival',scene,'authored',reference['pc'],npc_transition_evidence=arrival)
                if arrival['authored_values'] is not None:npc_arrival_consumed.setdefault(owner,set()).add(arrival['operand_id'])
            # The source-script pass already counts each unresolved name once.
        elif kind=='animation':
            if identity in reference_clips:
                evidence=reference_clips[identity];model=evidence['model_id']
                if model in model_records and model in nodes and nodes[model]['kind']=='model':
                    edge(identity,model,'reference_pinned_model_clip',scene,'decoded',reference_clip_evidence=evidence)
                else:unresolved+=1
            for binding in record.get('bindings',[]):
                actor=binding.get('actor_semantic_id');model=binding.get('model_asset_semantic_id')
                if actor in nodes:edge(actor,identity,'initial_animation_binding',scene,'decoded')
                else:unresolved+=1
                if model in nodes:edge(identity,model,'recorded_model_clip_binding',scene,'decoded')
                else:unresolved+=1
                for ref in effective_bindings.get((scene,actor,model),[]):
                    draft=ref['kind']=='draft_initial_model_assignment'
                    edge(ref['source_id'],identity,'draft_initial_animation_binding' if draft else 'effective_initial_animation_binding',scene,'authored' if draft else 'effective',
                         animation_evidence=dict(donor_entity_id=actor,model_id=model,initial_animation_id=binding['initial_animation_id']))
        elif kind in ('trigger','region'):
            target=record.get('collision_id')
            if target in nodes:edge(identity,target,'field_map_table_source',scene,'decoded')
            else:unresolved+=1
            if record.get('script_reference'):
                relation=_trigger_script_evidence(record,source_scripts,scene,project.imports[scene]) if kind=='trigger' else None
                if relation is None:unresolved+=1
                else:edge(identity,relation[0],'field_trigger_script_reference',scene,'decoded',trigger_evidence=relation[1])
            if identity in trigger_assignments:
                authored=trigger_assignments[identity]
                original_row=trigger_source_rows.get(identity)
                if original_row is None or original_row['encoded']!=record.get('encoded') or original_row['sha256']!=record.get('source_record',{}).get('sha256') or original_row['byte_offset']!=record.get('source_record',{}).get('byte_offset'):
                    raise ProjectError('Authored trigger reference catalog differs from the actual MAP row')
                relation=_trigger_script_evidence(record,source_scripts,scene,project.imports[scene],target_index=int(authored['script_id'].rsplit('/',1)[1]))
                if relation is None or relation[0]!=authored['script_id'] or relation[1]['script_source_record_sha256']!=authored['script_sha256']:
                    raise ProjectError('Authored trigger reference target differs from the verified catalog')
                proof=dict(map_source_sha256=trigger_binding['source_sha256'],component_sha256=digest(trigger_binding),
                           imported_partition_two_record_index=record['encoded']['record_index'],
                           target_byte_offset=record['source_record']['byte_offset']+2)
                edge(identity,relation[0],'effective_field_trigger_script_reference',scene,'effective',trigger_evidence=relation[1],trigger_binding_evidence=proof)
        elif kind=='worldmap':
            name=record.get('destination_source_label')
            if name:
                target='scene://'+name;node(target,'scene',target,name,target in project.imports);edge(identity,target,'landmark_destination_source',scene,'decoded')
            else:unresolved+=1
    if materials is not None:
        unresolved+=materials['unresolved_reference_count']
        for model in materials['models']:
            for material in model['materials']:
                if material['status']!='address_match':continue
                evidence={key:deepcopy(material[key]) for key in ('material_index','tpage','clut','uv_bounds','evidence')}
                evidence['model_source_sha256']=model['source_sha256']
                for target in material['source_ids']:
                    node(target,'texture',scene,available=target in nodes)
                    edge(model['model_id'],target,'static_material_texture_source',scene,'decoded',evidence=evidence)
        for model in materials.get('current_models',[]):
            for material in model['materials']:
                if material['status']!='address_match':continue
                evidence={key:deepcopy(material[key]) for key in ('material_index','tpage','clut','uv_bounds','evidence')}
                evidence.update(model_source_sha256=model['retail_sha256'],model_current_sha256=model['source_sha256'],
                                authored_materials_sha256=materials['current_state_key'])
                for target in material['source_ids']:
                    node(target,'texture',scene,available=target in nodes)
                    edge(model['model_id'],target,'effective_material_texture_source',scene,'effective',evidence=evidence)
    for owners in npc_flag_owners.values():
        for owner,draft,_,_,_ in owners:
            for family in ('flags','system_flags'):
                unresolved+=len(set(draft.get(family,{}).get('entries',{}))-npc_flag_consumed.get(owner,set()))
    for owner,draft in project.actor_drafts.items():
        if draft['scene_id']==scene:unresolved+=len(set(draft.get('transitions',{}).get('entries',{}))-npc_arrival_consumed.get(owner,set()))
    if own_audio_snapshot:audio_snapshot.verify(project)
    if _full_graph:
        for identity,value in nodes.items():
            value['scene_ids']=sorted(memberships[identity]);value['_navigation_scene_ids']=sorted(navigation.get(identity,set()))
        return dict(nodes=nodes,edges=edges,unresolved_reference_count=unresolved)
    if identifier not in nodes:raise ProjectError('Asset is outside imported project records and the active resource catalog')
    incoming=sorted((e for e in edges.values() if e['target_id']==identifier),key=lambda e:(e['kind'],e['source_id'],e.get('pc',-1)))
    outgoing=sorted((e for e in edges.values() if e['source_id']==identifier),key=lambda e:(e['kind'],e['target_id'],e.get('pc',-1)))
    if len(incoming)+len(outgoing)>4096:raise ProjectError('Asset reference neighborhood exceeds4096 edges')
    neighbors={identifier}|{e['source_id'] for e in incoming}|{e['target_id'] for e in outgoing}
    return deepcopy(dict(schema_version='legaia.asset-references.v1',asset_id=identifier,source_key=source_key(project),read_only=True,
                         nodes=[nodes[key] for key in sorted(neighbors)],incoming=incoming,outgoing=outgoing,
                         coverage=dict(verified_scene_ids=sorted(project.imports),resource_scene_id=scene,unresolved_reference_count=unresolved),
                         material_diagnostics=deepcopy(next((row for row in (materials or {}).get('models',[]) if row['model_id']==identifier),None)),
                         current_material_diagnostics=deepcopy(next((row for row in (materials or {}).get('current_models',[]) if row['model_id']==identifier),None)),
                         limitations=['Imported scene/model membership and initial assignments are project-wide. Derived resources cover the active scene only.',
                                      'Script model pools, field trigger dispatch and live animation state are not resolved here.',
                                      'Edges describe recorded references, not runtime residency, successful scheduling or gameplay reachability.',
                                      'Retained clips are navigable when registered in the verified scene animation catalog; their actor Inspector manages assignments.',*(materials or {}).get('limitations',['Material source relationships were not requested.']),*catalog.get('limitations',[])]))

def inspect(project,identifier):
    from importer.pipeline import _disc_context
    from .resources import _verify,refresh_resource_catalog
    if not isinstance(identifier,str) or not identifier or len(identifier)>1024:raise ProjectError('Invalid asset reference identity')
    if not project.disc_path or not project.active_scene or not 1<=len(project.imports)<=64:raise ProjectError('Asset references require an active scene, user-owned disc and at most64 imported scenes')
    key=source_key(project)
    with _disc_context(project.disc_path):
        for document in project.imports.values():_verify(project,document)
        from .material_references import verified_catalog,with_current
        catalog=refresh_resource_catalog(project);materials=with_current(project,verified_catalog(project));result=assemble(project,catalog,identifier,materials)
    if key!=source_key(project):raise ProjectError('Asset reference source changed during discovery')
    return result


def _reference_limitations(rows):
    if not isinstance(rows,list) or len(rows)>256 or any(not isinstance(row,str) or len(row)>8192 for row in rows):
        raise ProjectError('Asset reference limitations exceed the bounded metadata format')
    return rows


def _project_graph(project,catalog,identifier,materials=None,*,_audio_snapshot=None):
    try:
        graph=assemble(project,catalog,identifier,materials,_full_graph=True,_audio_snapshot=_audio_snapshot)
        from .project import canonical
        if len(canonical(graph))>8*1024*1024:raise ProjectError('Asset reference scene graph exceeds8 MiB')
        return graph
    except (KeyError,TypeError,IndexError) as error:
        raise ProjectError('Invalid project reference decoded metadata') from error


def assemble_project(project,catalogs,identifier,materials_by_scene=None,scene_coverage=None,*,_full_graph=False):
    """Merge complete scene graphs before selecting a project-wide neighborhood."""
    from copy import copy
    from .project import canonical
    if not isinstance(identifier,str) or not identifier or len(identifier)>1024:
        raise ProjectError('Invalid asset reference identity')
    if not isinstance(catalogs,dict) or not 1<=len(project.imports)<=64 or project.active_scene not in project.imports:
        raise ProjectError('Project references require an active imported scene and at most64 imported scenes')
    if set(catalogs)-set(project.imports):raise ProjectError('Resource catalog is outside imported project scenes')
    materials_by_scene={} if materials_by_scene is None else materials_by_scene
    if not isinstance(materials_by_scene,dict) or set(materials_by_scene)-set(catalogs):
        raise ProjectError('Material catalog is outside verified resource scenes')
    if len(canonical(dict(catalogs=catalogs,materials=materials_by_scene)))>32*1024*1024:
        raise ProjectError('Project reference decoded metadata exceeds32 MiB')
    supplied={} if scene_coverage is None else scene_coverage
    if not isinstance(supplied,dict) or set(supplied)-set(project.imports):raise ProjectError('Invalid project reference coverage')
    nodes={};edges={};memberships={};navigation={};unresolved=0;coverage=[];limitations=[]
    from .audio_reference_snapshot import AudioReferenceSnapshot
    audio_snapshot=AudioReferenceSnapshot(project)
    # A placeholder is only a graph adapter for imported membership, never evidence
    # that an unavailable scene has decoded resources.
    for scene in sorted(project.imports):
        catalog=catalogs.get(scene)
        if catalog is not None:
            if not isinstance(catalog,dict) or not isinstance(catalog.get('source_key'),str) or len(catalog['source_key'])!=64 or any(c not in '0123456789abcdef' for c in catalog['source_key']):
                raise ProjectError('Invalid project reference resource source key')
            if catalog.get('scene_id',scene)!=scene or not isinstance(catalog.get('records'),list):
                raise ProjectError('Invalid project reference resource catalog')
            for record in catalog['records']:
                if not isinstance(record,dict) or record.get('kind') not in ('audio','texture','animation','script','controller','dialogue','collision','trigger','region','worldmap','flag','transition'):
                    raise ProjectError('Invalid project reference resource type')
                if record.get('name') is not None and (not isinstance(record['name'],str) or len(record['name'])>8192):
                    raise ProjectError('Invalid project reference resource label')
        status='available' if catalog is not None else 'unavailable'
        details=supplied.get(scene,{})
        if not isinstance(details,dict) or details.get('status',status)!=status:
            raise ProjectError('Project reference coverage differs from resource evidence')
        expected_key=catalog['source_key'] if catalog else None
        if details.get('source_import_sha256',digest(project.imports[scene]))!=digest(project.imports[scene]) or details.get('resource_source_key',expected_key)!=expected_key:
            raise ProjectError('Project reference coverage differs from source provenance')
        if status=='available' and details.get('reason') is not None:
            raise ProjectError('Available resource scene cannot have an unavailable reason')
        reason=details.get('reason') if status=='unavailable' else None
        if status=='unavailable' and (not isinstance(reason,str) or not reason or len(reason)>8192):
            raise ProjectError('Unavailable resource scene requires an explicit reason')
        local_limitations=_reference_limitations((catalog or {}).get('limitations',[]))
        coverage.append(dict(scene_id=scene,source_import_sha256=digest(project.imports[scene]),status=status,
                             resource_source_key=catalog['source_key'] if catalog else None,reason=reason,limitations=local_limitations))
        limitations.extend(scene+': '+row for row in local_limitations)
        if reason:limitations.append(scene+': Derived resources unavailable: '+reason)
        view=copy(project);view.active_scene=scene
        graph=_project_graph(view,catalog or dict(source_key=None,records=[],limitations=[]),identifier,materials_by_scene.get(scene),_audio_snapshot=audio_snapshot)
        # Imported/effective edges are repeated by every adapter; exact edge IDs
        # deduplicate them. Unresolved imported references likewise count once.
        imported_graph=_project_graph(view,dict(source_key=None,records=[],limitations=[]),identifier,_audio_snapshot=audio_snapshot)
        unresolved+=graph['unresolved_reference_count']-imported_graph['unresolved_reference_count']
        if scene==sorted(project.imports)[0]:unresolved+=imported_graph['unresolved_reference_count']
        for identity,value in graph['nodes'].items():
            memberships.setdefault(identity,set()).update(value.pop('scene_ids'))
            navigation.setdefault(identity,set()).update(value.pop('_navigation_scene_ids'))
            if identity in nodes:
                if nodes[identity]['kind']!=value['kind']:raise ProjectError('Conflicting asset reference type')
                nodes[identity]['available']=nodes[identity]['available'] or value['available']
            else:nodes[identity]=value
        edges.update(graph['edges'])
        if len(nodes)>16384:raise ProjectError('Asset reference node limit exceeded')
        if len(edges)>32768:raise ProjectError('Asset reference edge limit exceeded')
        if len(canonical(dict(nodes=nodes,edges=edges)))>32*1024*1024:
            raise ProjectError('Project reference graph exceeds32 MiB')
    if identifier not in nodes:raise ProjectError('Asset is outside imported project records and verified resource catalogs')
    for identity,value in nodes.items():
        if len(memberships[identity])>64:raise ProjectError('Asset reference scene membership limit exceeded')
        value['scene_ids']=sorted(memberships[identity])
        value['navigable_scene_ids']=sorted(navigation[identity])
        value['available']=bool(navigation[identity])
        value['scene_id']=min(navigation[identity] or memberships[identity])
    incoming=sorted((e for e in edges.values() if e['target_id']==identifier),key=lambda e:(e['kind'],e['scene_id'],e['source_id'],e.get('pc',-1),e['id']))
    outgoing=sorted((e for e in edges.values() if e['source_id']==identifier),key=lambda e:(e['kind'],e['scene_id'],e['target_id'],e.get('pc',-1),e['id']))
    if len(incoming)+len(outgoing)>4096:raise ProjectError('Asset reference neighborhood exceeds4096 edges')
    neighbors={identifier}|{e['source_id'] for e in incoming}|{e['target_id'] for e in outgoing}
    diagnostics=next((row for scene in sorted(materials_by_scene) for row in materials_by_scene[scene].get('models',[]) if row['model_id']==identifier),None)
    current_diagnostics=next((row for scene in sorted(materials_by_scene) for row in materials_by_scene[scene].get('current_models',[]) if row['model_id']==identifier),None)
    for scene,materials in sorted(materials_by_scene.items()):
        limitations.extend(scene+': '+row for row in _reference_limitations(materials.get('limitations',[])))
    result=dict(schema_version='legaia.project-asset-references.v1',asset_id=identifier,source_key=source_key(project),read_only=True,
                nodes=[nodes[key] for key in sorted(neighbors)],incoming=incoming,outgoing=outgoing,
                coverage=dict(verified_scene_ids=sorted(project.imports),resource_scene_id=project.active_scene,
                              unresolved_reference_count=unresolved,scenes=coverage),material_diagnostics=deepcopy(diagnostics),current_material_diagnostics=deepcopy(current_diagnostics),
                limitations=['Derived resource discovery covers every imported scene with explicit per-scene availability.',
                             'Edges describe recorded references, not runtime residency, successful scheduling or gameplay reachability.',
                             'Retained clips are navigable when registered in the verified scene animation catalog; their actor Inspector manages assignments.',
                             'Script model pools, field trigger dispatch and live animation state are not resolved here.',*list(dict.fromkeys(limitations))])
    _reference_limitations(result['limitations'])
    if _full_graph:
        result['nodes']=[nodes[key] for key in sorted(nodes)]
        result['edges']=[edges[key] for key in sorted(edges)]
    if len(canonical(result))>(32 if _full_graph else 8)*1024*1024:raise ProjectError('Project reference response exceeds metadata budget')
    audio_snapshot.verify(project)
    return deepcopy(result)


def inspect_project(project,identifier,*,_full_graph=False):
    """Fresh verified discovery using detached project state and private catalogs."""
    from importer.pipeline import _disc_context
    from importer.core import ImportError as RetailImportError
    from .resources import _verify,refresh_resource_catalog
    from .material_references import verified_catalog,with_current
    from .project import AssetDatabase
    if not isinstance(identifier,str) or not identifier or len(identifier)>1024:
        raise ProjectError('Invalid asset reference identity')
    if not project.disc_path or project.active_scene not in project.imports or not 1<=len(project.imports)<=64:
        raise ProjectError('Project references require an active scene, user-owned disc and at most64 imported scenes')
    key=source_key(project)
    from copy import copy
    active_scene=project.active_scene
    view=copy(project)
    for name,value in vars(project).items():
        if name!='assets':setattr(view,name,deepcopy(value))
    view.assets=AssetDatabase()
    # Catalog registration stays isolated. Source-keyed material metadata is safe
    # to share only after the complete snapshot's fresh Retail verification below;
    # Current reuse additionally requalifies owned assets in with_current.
    view.assets.material_reference_catalogs=project.assets.material_reference_catalogs
    view.assets.current_material_reference_catalogs=project.assets.current_material_reference_catalogs
    catalogs={};materials={};coverage={};metadata_bytes=0
    with _disc_context(view.disc_path):
        # Verify the complete snapshot before any derived decoding or reuse.
        for scene in sorted(view.imports):_verify(view,view.imports[scene])
        for scene in sorted(view.imports):
            view.active_scene=scene
            try:
                catalog=refresh_resource_catalog(view)
                material=with_current(view,verified_catalog(view))
            except RetailImportError as error:
                coverage[scene]=dict(status='unavailable',reason=str(error))
                continue
            from .project import canonical
            metadata_bytes+=len(canonical(dict(catalog=catalog,materials=material)))
            if metadata_bytes>32*1024*1024:raise ProjectError('Project reference decoded metadata exceeds32 MiB')
            catalogs[scene]=catalog;materials[scene]=material
    view.active_scene=active_scene
    if key!=source_key(project) or key!=source_key(view):raise ProjectError('Asset reference source changed during discovery')
    result=assemble_project(view,catalogs,identifier,materials,coverage,_full_graph=_full_graph)
    if key!=source_key(project):raise ProjectError('Asset reference source changed during discovery')
    return result
