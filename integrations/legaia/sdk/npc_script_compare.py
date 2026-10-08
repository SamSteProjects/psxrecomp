"""Exact donor/generated record byte comparison; no behavioral equivalence claim."""
from hashlib import sha256
from .project import ProjectError
from .project_copy import source_key
from .npc_build_script import inspect as inspect_build
from .npc_donor_script import inspect as inspect_donor
from .build_history import _load,verify_build

def authored_spans(metadata,entity_id,retail,generated,draft):
    """Qualify receipt rows against both exact records; unexplained bytes stay so."""
    a,b=(bytes.fromhex(r['raw_hex']) for r in (retail,generated))
    qualification_record=b;branch_graph=None
    selector_baseline=bytearray(a)
    if 'system_flags' in draft:
        from importer.system_flag_authoring import patch_system_flag_selector
        from importer.core import ImportError as NativeError
        prefix='script://'+draft['donor_entity_id'].removeprefix('scene://')+'/system-flag/'
        value=draft['system_flags']
        if value.get('donor_entity_id')!=draft['donor_entity_id']:
            raise ProjectError('NPC system selector comparison donor differs')
        for identity,fields in value['entries'].items():
            try:
                if not isinstance(identity,str) or not identity.startswith(prefix) or len(identity)!=len(prefix)+4:
                    raise NativeError('Foreign system selector identity')
                pc=int(identity.removeprefix(prefix),16)
                changed,_=patch_system_flag_selector(a,retail['script_offset'],pc,fields)
                selector_baseline[pc:pc+2]=changed[pc:pc+2]
            except (ValueError,NativeError) as error:
                raise ProjectError('NPC system selector comparison is not source-qualified') from error
    selector_baseline=bytes(selector_baseline)
    if 'branches' in draft:
        from importer.branch_authoring import _graph_candidate,_branch
        from importer.script_inspection import inspect_record
        from importer.core import ImportError as NativeError
        try:
            source_graph=inspect_record(a,retail['script_offset'])
            branch_graph=_graph_candidate(a,b,retail['script_offset'],source_graph,selector_baseline)
            restored=bytearray(b)
            for node in source_graph['instructions']:
                word=_branch(a,node)
                if word is not None:
                    at=word['operand_pc'];restored[at:at+2]=a[at:at+2]
            qualification_record=bytes(restored)
            _graph_candidate(a,qualification_record,retail['script_offset'],source_graph,selector_baseline)
        except NativeError as error:raise ProjectError('NPC branch comparison graph is not source-qualified') from error
    spans=[];occupied=set();movement_expected={};facing_expected={};flags_expected={};selectors_expected={};colors_expected={};animation_expected={};prefix='script://'+draft['donor_entity_id'].removeprefix('scene://')+'/'
    for key,category in [('npc_appearance_changes','initial_appearance'),('npc_dialogue_changes','own_dialogue'),('npc_wait_changes','own_wait'),('npc_movement_changes','own_movement'),('npc_facing_changes','own_facing'),('npc_flags_changes','own_flag'),('npc_system_flags_changes','own_system_flag'),('npc_branches_changes','own_branch'),('npc_model_selectors_changes','own_model_selector'),('npc_effect_colors_changes','own_effect_color'),('npc_transitions_changes','own_transition'),('npc_animation_operands_changes','own_animation_operand')]:
        value=metadata.get(key)
        if value is None:continue
        if not isinstance(value,dict) or not isinstance(value.get('changes'),list) or len(value['changes'])>8192:
            raise ProjectError('NPC authored comparison audit exceeds its bounds')
        for row in value['changes']:
            if not isinstance(row,dict):raise ProjectError('NPC authored comparison audit row is invalid')
            if row.get('draft_id')!=entity_id:continue
            if type(row.get('record_index')) is not int or row['record_index']!=generated['record_index']:
                raise ProjectError('NPC authored comparison allocation differs')
            source_at,target_at=row.get('source_decoded_byte_offset'),row.get('decoded_byte_offset')
            if type(source_at) is not int or type(target_at) is not int:
                raise ProjectError('NPC authored comparison requires source/generated offsets')
            relative=target_at-generated['byte_offset']
            if relative!=source_at-retail['byte_offset']:
                raise ProjectError('NPC authored comparison has inconsistent relative offsets')
            movement_field=None
            if category=='own_movement':
                from importer.movement_authoring import patch_movement_target
                from importer.core import ImportError as NativeError
                owner=row.get('movement_id');pc=row.get('pc');movement_field=row.get('field')
                if (type(pc) is not int or not 0<=pc<=65535 or owner!=prefix+f'movement/{pc:04x}' or
                    row.get('donor_entity_id')!=draft['donor_entity_id'] or
                    draft.get('movement',{}).get('donor_entity_id')!=draft['donor_entity_id']):
                    raise ProjectError('NPC movement comparison differs from its source owner')
                requested=draft.get('movement',{}).get('entries',{}).get(owner)
                if owner not in movement_expected:
                    try:_,movement_expected[owner]=patch_movement_target(a,retail['script_offset'],pc,requested,base_offset=retail['byte_offset'])
                    except NativeError as error:raise ProjectError('NPC movement comparison target is not qualified') from error
                qualified=movement_expected[owner]
                expected=next((r for r in qualified if r['field']==movement_field),None)
                if expected is None or any(type(row.get(k)) is not type(v) or row[k]!=v for k,v in expected.items() if k!='decoded_byte_offset') or source_at!=expected['decoded_byte_offset']:
                    raise ProjectError('NPC movement comparison differs from its decoded source operand')
                before,after=bytes([expected['before_byte']]),bytes([expected['after_byte']])
            elif category=='own_facing':
                from importer.facing_authoring import patch_facing_sector
                from importer.core import ImportError as NativeError
                owner=row.get('facing_id');pc=row.get('pc')
                if (type(pc) is not int or not 0<=pc<=65535 or owner!=prefix+f'facing/{pc:04x}' or
                    row.get('donor_entity_id')!=draft['donor_entity_id'] or
                    draft.get('facing',{}).get('donor_entity_id')!=draft['donor_entity_id']):
                    raise ProjectError('NPC facing comparison differs from its source owner')
                requested=draft.get('facing',{}).get('entries',{}).get(owner)
                if owner not in facing_expected:
                    try:
                        _,facing_expected[owner]=patch_facing_sector(a,retail['script_offset'],pc,requested,base_offset=retail['byte_offset'])
                        # The generated target must remain supported after own movement.
                        patch_facing_sector(qualification_record,generated['script_offset'],pc,requested)
                    except NativeError as error:raise ProjectError('NPC facing comparison target is not qualified') from error
                expected=next(iter(facing_expected[owner]),None)
                if expected is None or any(type(row.get(k)) is not type(v) or row[k]!=v for k,v in expected.items() if k!='decoded_byte_offset') or source_at!=expected['decoded_byte_offset']:
                    raise ProjectError('NPC facing comparison differs from its decoded source operand')
                header_end=pc+(2 if expected['target_context'] is not None else 1)+(expected['mnemonic']=='NPC_RUN')
                if a[pc:header_end]!=b[pc:header_end] or (expected['mnemonic']=='CAM_CFG' and a[relative+1]!=b[relative+1]):
                    raise ProjectError('NPC facing comparison dispatch or CAM_CFG mode differs')
                before,after=bytes([expected['before_byte']]),bytes([expected['after_byte']])
            elif category=='own_flag':
                from importer.flag_authoring import patch_flag_bit
                from importer.core import ImportError as NativeError
                owner=row.get('flag_id');pc=row.get('pc')
                if (type(pc) is not int or not 0<=pc<=65535 or owner!=prefix+f'flag-bit/{pc:04x}' or
                    row.get('donor_entity_id')!=draft['donor_entity_id'] or
                    draft.get('flags',{}).get('donor_entity_id')!=draft['donor_entity_id']):
                    raise ProjectError('NPC flag comparison differs from its source owner')
                requested=draft.get('flags',{}).get('entries',{}).get(owner)
                if owner not in flags_expected:
                    try:
                        _,flags_expected[owner]=patch_flag_bit(a,retail['script_offset'],pc,requested,base_offset=retail['byte_offset'])
                        patch_flag_bit(qualification_record,generated['script_offset'],pc,requested)
                    except NativeError as error:raise ProjectError('NPC flag comparison target is not qualified') from error
                expected=next(iter(flags_expected[owner]),None)
                if expected is None or any(type(row.get(k)) is not type(v) or row[k]!=v for k,v in expected.items() if k!='decoded_byte_offset') or source_at!=expected['decoded_byte_offset']:
                    raise ProjectError('NPC flag comparison differs from its decoded source operand')
                header_end=pc+(2 if expected['target_context'] is not None else 1)
                if a[pc:header_end]!=b[pc:header_end]:
                    raise ProjectError('NPC flag comparison dispatch differs')
                before,after=bytes([expected['before_byte']]),bytes([expected['after_byte']])
            elif category=='own_model_selector':
                from importer.model_selector_authoring import patch_model_selector_target
                from importer.core import ImportError as NativeError
                owner=row.get('model_selector_id');pc=row.get('pc')
                if (type(pc) is not int or not 0<=pc<=65535 or owner!=prefix+f'model-selector/{pc:04x}' or
                    row.get('donor_entity_id')!=draft['donor_entity_id'] or
                    draft.get('model_selectors',{}).get('donor_entity_id')!=draft['donor_entity_id']):
                    raise ProjectError('NPC model selector comparison differs from its source owner')
                requested=draft.get('model_selectors',{}).get('entries',{}).get(owner)
                if owner not in selectors_expected:
                    try:
                        _,selectors_expected[owner]=patch_model_selector_target(a,retail['script_offset'],pc,requested,base_offset=retail['byte_offset'])
                        patch_model_selector_target(qualification_record,generated['script_offset'],pc,requested)
                    except NativeError as error:raise ProjectError('NPC model selector comparison target is not qualified') from error
                expected=next(iter(selectors_expected[owner]),None)
                if expected is None or any(type(row.get(k)) is not type(v) or row[k]!=v for k,v in expected.items() if k!='decoded_byte_offset') or source_at!=expected['decoded_byte_offset']:
                    raise ProjectError('NPC model selector comparison differs from its decoded source operand')
                header_end=pc+(3 if expected['target_context'] is not None else 2)
                if a[pc:header_end]!=b[pc:header_end]:raise ProjectError('NPC model selector comparison dispatch or sub-op differs')
                before,after=bytes.fromhex(expected['before_hex']),bytes.fromhex(expected['after_hex'])
            elif category=='own_effect_color':
                from importer.effect_color_authoring import patch_effect_color_target
                from importer.core import ImportError as NativeError
                owner=row.get('effect_color_id');pc=row.get('pc')
                if (type(pc) is not int or not 0<=pc<=65535 or owner!=prefix+f'effect-color/{pc:04x}' or
                    row.get('donor_entity_id')!=draft['donor_entity_id'] or
                    draft.get('effect_colors',{}).get('donor_entity_id')!=draft['donor_entity_id']):
                    raise ProjectError('NPC effect color comparison differs from its source owner')
                requested=draft.get('effect_colors',{}).get('entries',{}).get(owner)
                if owner not in colors_expected:
                    try:
                        _,colors_expected[owner]=patch_effect_color_target(a,retail['script_offset'],pc,requested,base_offset=retail['byte_offset'])
                        patch_effect_color_target(qualification_record,generated['script_offset'],pc,requested)
                    except NativeError as error:raise ProjectError('NPC effect color comparison target is not qualified') from error
                expected=next(iter(colors_expected[owner]),None)
                if expected is None or any(type(row.get(k)) is not type(v) or row[k]!=v for k,v in expected.items() if k!='decoded_byte_offset') or source_at!=expected['decoded_byte_offset']:
                    raise ProjectError('NPC effect color comparison differs from its decoded source operand')
                header_end=pc+(3 if expected['target_context'] is not None else 2)
                if a[pc:header_end]!=b[pc:header_end]:raise ProjectError('NPC effect color comparison dispatch or sub-op differs')
                before,after=bytes.fromhex(expected['before_hex']),bytes.fromhex(expected['after_hex'])
            elif category=='own_animation_operand':
                from importer.animation_operand_authoring import patch_animation_operands_target
                from importer.core import ImportError as NativeError
                owner=row.get('animation_operand_id');pc=row.get('pc')
                if (type(pc) is not int or not 0<=pc<=65535 or owner!=prefix+f'animation-operands/{pc:04x}' or
                    row.get('donor_entity_id')!=draft['donor_entity_id'] or
                    draft.get('animation_operands',{}).get('donor_entity_id')!=draft['donor_entity_id']):
                    raise ProjectError('NPC animation comparison differs from its source owner')
                requested=draft.get('animation_operands',{}).get('entries',{}).get(owner)
                if owner not in animation_expected:
                    try:
                        _,animation_expected[owner]=patch_animation_operands_target(a,retail['script_offset'],pc,requested,base_offset=retail['byte_offset'])
                        patch_animation_operands_target(qualification_record,generated['script_offset'],pc,requested)
                    except NativeError as error:raise ProjectError('NPC animation comparison target is not qualified') from error
                expected=next((r for r in animation_expected[owner] if r['field']==row.get('field')),None)
                if expected is None or any(type(row.get(k)) is not type(v) or row[k]!=v for k,v in expected.items() if k!='decoded_byte_offset') or source_at!=expected['decoded_byte_offset']:
                    raise ProjectError('NPC animation comparison differs from its decoded source operand')
                header_end=pc+(3 if expected['target_context'] is not None else 2)
                if a[pc:header_end]!=b[pc:header_end]:raise ProjectError('NPC animation comparison dispatch or selector differs')
                before,after=bytes.fromhex(expected['before_hex']),bytes.fromhex(expected['after_hex'])
            elif category=='own_transition':
                from importer.transition_authoring import patch_transition_entry
                from importer.core import ImportError as NativeError
                owner=row.get('transition_id');pc=row.get('pc')
                if (type(pc) is not int or not 0<=pc<=65535 or owner!=prefix+f'transition/{pc:04x}' or
                    row.get('donor_entity_id')!=draft['donor_entity_id'] or
                    draft.get('transitions',{}).get('donor_entity_id')!=draft['donor_entity_id']):
                    raise ProjectError('NPC transition comparison differs from its source owner')
                requested=draft.get('transitions',{}).get('entries',{}).get(owner)
                try:
                    _,changes=patch_transition_entry(a,retail['script_offset'],pc,requested,base_offset=retail['byte_offset'])
                    patch_transition_entry(qualification_record,generated['script_offset'],pc,requested)
                except NativeError as error:raise ProjectError('NPC transition comparison target is not qualified') from error
                expected=next((c for c in changes if c['field']==row.get('field')),None)
                if expected is None or any(type(row.get(k)) is not type(v) or row[k]!=v for k,v in expected.items() if k!='decoded_byte_offset') or source_at!=expected['decoded_byte_offset']:
                    raise ProjectError('NPC transition comparison differs from its decoded source operand')
                before,after=bytes([expected['before_byte']]),bytes([expected['after_byte']])
            elif category=='own_system_flag':
                from importer.system_flag_authoring import patch_system_flag_selector
                from importer.core import ImportError as NativeError
                owner=row.get('system_flag_id');pc=row.get('pc')
                if (type(pc) is not int or not 0<=pc<=65535 or owner!=prefix+f'system-flag/{pc:04x}' or
                        row.get('donor_entity_id')!=draft['donor_entity_id'] or
                        draft.get('system_flags',{}).get('donor_entity_id')!=draft['donor_entity_id']):
                    raise ProjectError('NPC system selector comparison differs from its source owner')
                requested=draft.get('system_flags',{}).get('entries',{}).get(owner)
                try:
                    _,changes=patch_system_flag_selector(a,retail['script_offset'],pc,requested,base_offset=retail['byte_offset'])
                    patch_system_flag_selector(qualification_record,generated['script_offset'],pc,requested)
                except NativeError as error:
                    raise ProjectError('NPC system selector comparison target is not qualified') from error
                expected=next(iter(changes),None)
                if expected is None or any(type(row.get(k)) is not type(v) or row[k]!=v for k,v in expected.items() if k!='decoded_byte_offset') or source_at!=expected['decoded_byte_offset']:
                    raise ProjectError('NPC system selector comparison differs from its decoded source operand')
                before,after=bytes.fromhex(expected['before_hex']),bytes.fromhex(expected['after_hex'])
            elif category=='own_branch':
                from importer.branch_authoring import _branch,validate_branch_values
                from importer.script_inspection import _instruction,inspect_record
                from importer.core import ImportError as NativeError
                owner=row.get('branch_id');pc=row.get('pc')
                if (branch_graph is None or type(pc) is not int or not retail['script_offset']<=pc<=32767 or owner!=prefix+f'branch/{pc:04x}' or
                    row.get('donor_entity_id')!=draft['donor_entity_id'] or row.get('owner_id')!=draft['donor_entity_id'] or
                    draft.get('branches',{}).get('donor_entity_id')!=draft['donor_entity_id']):
                    raise ProjectError('NPC branch comparison differs from its source owner')
                try:
                    target=validate_branch_values(draft['branches']['entries'].get(owner))
                    source_node=_instruction(a,pc);word=_branch(a,source_node)
                    if word is None or not retail['script_offset']<=word['target_pc']<=32767 or not retail['script_offset']<=target<=32767 or pc not in {r['pc'] for r in source_graph['instructions']} or target not in {r['pc'] for r in source_graph['instructions']+source_graph['dialogues']}:
                        raise NativeError('Branch target is not an original source boundary')
                except NativeError as error:raise ProjectError('NPC branch comparison target is not qualified') from error
                operand=word['operand_pc'];before=a[operand:operand+2];after=((target-operand)&65535).to_bytes(2,'little')
                expected=dict(pc=pc,mnemonic=source_node['mnemonic'],target_context=source_node['target_context'],condition=word['condition'],encoding=word['encoding'],field='script.branch_target',before_value=word['target_pc'],after_value=target,before_target_pc=word['target_pc'],after_target_pc=target,record_relative_byte_offset=operand,byte_length=2,before_hex=before.hex(),after_hex=after.hex(),source_record_sha256=sha256(a).hexdigest(),effective_record_sha256=sha256(qualification_record).hexdigest(),candidate_record_sha256=sha256(b).hexdigest(),current_successors=source_node['successors'],proposed_successors=_instruction(b,pc)['successors'],unreachable_source_pcs=branch_graph['unreachable_source_pcs'],scope='script-branch-target-only')
                if before==after or any(type(row.get(k)) is not type(v) or row[k]!=v for k,v in expected.items()) or source_at!=retail['byte_offset']+operand:
                    raise ProjectError('NPC branch comparison differs from its exact source/composed instruction')
                expected_bytes=[dict(decoded_byte_offset=generated['byte_offset']+operand+i,source_decoded_byte_offset=retail['byte_offset']+operand+i,before_byte=x,after_byte=y) for i,(x,y) in enumerate(zip(before,after)) if x!=y]
                if row.get('changed_bytes')!=expected_bytes or any(any(type(r.get(k)) is not type(v) for k,v in expected.items()) for r,expected in zip(row.get('changed_bytes',[]),expected_bytes)):raise ProjectError('NPC branch comparison changed-byte audit differs')
            elif category=='initial_appearance':
                if 'appearance' not in draft:raise ProjectError('NPC appearance comparison has no authored binding')
                if row.get('field') not in ('model_index','animation_id') or any(type(row.get(k)) is not int or not 0<=row[k]<=255 for k in ('before_byte','after_byte')):
                    raise ProjectError('NPC appearance comparison requires exact header bytes')
                before,after=bytes([row['before_byte']]),bytes([row['after_byte']]);owner=row['field']
                if relative!=1+a[0]*2+(row['field']=='animation_id'):
                    raise ProjectError('NPC appearance comparison escaped its initial header')
            else:
                try:before,after=(bytes.fromhex(row[k]) for k in ('before_hex','after_hex'))
                except (ValueError,KeyError,TypeError) as error:raise ProjectError('NPC authored comparison requires exact span bytes') from error
                owner=row.get('run_id' if category=='own_dialogue' else 'wait_id')
                if not isinstance(owner,str) or not owner.startswith(prefix) or len(owner)>256:
                    raise ProjectError('NPC authored comparison source operand is unavailable')
                if category=='own_wait' and (row.get('mnemonic')!='WAIT_FRAMES' or len(before)!=2):
                    raise ProjectError('NPC wait comparison requires a two-byte target')
            size=len(before);span=set(range(relative,relative+size))
            if not 1<=size<=4096 or len(after)!=size or row.get('byte_length',size)!=size or not 0<=relative<=min(len(a),len(b))-size or span&occupied or a[relative:relative+size]!=before or b[relative:relative+size]!=after:
                raise ProjectError('NPC authored comparison span/preimage differs from saved and retail records')
            if category=='own_wait':
                requested=draft.get('waits',{}).get('entries',{}).get(owner)
                if requested is None or int.from_bytes(after,'little')!=requested['duration_ticks']:raise ProjectError('NPC wait comparison differs from its authored target')
            if category=='own_dialogue':
                requested=draft.get('dialogue',{}).get('runs',{}).get(owner)
                if requested is None or requested.ljust(size).encode('ascii')!=after:raise ProjectError('NPC dialogue comparison differs from its authored text')
            if len(spans)>=8192:raise ProjectError('NPC authored comparison spans exceed their bounds')
            occupied.update(span)
            spans.append(dict(category=category,source_operand_id=owner,relative_offset=relative,byte_length=size,before_hex=before.hex(),after_hex=after.hex(),**({'movement_field':movement_field} if category=='own_movement' else {})))
    return sorted(spans,key=lambda r:r['relative_offset'])

def compare_records(retail,generated):
    def payload(record):
        try:data=bytes.fromhex(record['raw_hex'])
        except (TypeError,ValueError,KeyError) as error:raise ProjectError('Script comparison requires exact record bytes') from error
        if not 0<len(data)<=65536 or len(data)!=record.get('byte_length') or sha256(data).hexdigest()!=record.get('sha256') or type(record.get('script_offset')) is not int or not 0<=record['script_offset']<=len(data):raise ProjectError('Script comparison record hash, length or entry differs')
        return data
    a,b=payload(retail),payload(generated);boundary=min(retail['script_offset'],generated['script_offset']);changes=[]
    for offset in range(max(len(a),len(b))):
        left=a[offset] if offset<len(a) else None;right=b[offset] if offset<len(b) else None
        if left!=right:changes.append(dict(relative_offset=offset,retail_byte=left,generated_byte=right,scope='record_header' if offset<boundary else 'script_or_remaining_record_bytes'))
    return dict(comparison_scope='same_relative_record_byte_offsets',retail_length=len(a),generated_length=len(b),changed_byte_count=len(changes),unchanged_common_byte_count=sum(a[i]==b[i] for i in range(min(len(a),len(b)))),record_bytes_equal=a==b,script_tail_bytes_equal=a[retail['script_offset']:]==b[generated['script_offset']:],changes=changes)

def compare(project,entity_id,build_id):
    key=source_key(project);generated=inspect_build(project,entity_id,build_id);retail=inspect_donor(project,entity_id)
    if source_key(project)!=key or generated['project_source_key']!=key or retail['project_source_key']!=key or generated['draft']!=retail['draft']:raise ProjectError('Project or NPC donor changed during script comparison')
    difference=compare_records(retail['inspection']['record'],generated['inspection']['record'])
    _,audit=_load(project,build_id);metadata=audit.get('npc_candidates',{}).get(project.active_scene,{}).get('draft_audit',{})
    spans=authored_spans(metadata,entity_id,retail['inspection']['record'],generated['inspection']['record'],generated['draft'])
    current=verify_build(project,build_id)
    if source_key(project)!=key or not current['matches_current_inputs'] or current['receipt']['archive_sha256']!=generated['build']['archive_sha256']:raise ProjectError('Project or saved Build changed during authored script comparison')
    return dict(schema_version='legaia.npc-script-comparison.v1',project_source_key=key,entity_id=entity_id,scene_id=project.active_scene,read_only=True,gameplay_verified=False,runtime_binding='not_asserted',retail=retail,generated=generated,difference=difference,authored_spans=spans,limitations=['Relative byte alignment only; different offsets are not instruction or branch equivalence.', 'Source-qualified authored spans account only for their exact bytes. Other differences remain unexplained, including append rebasing and opaque data.', 'Script tails include opaque and unvisited data. Equal bytes do not establish equal runtime behavior.', 'Retail offsets and generated MAN offsets are separate. Runtime allocation, scheduling and execution remain unverified.'])
