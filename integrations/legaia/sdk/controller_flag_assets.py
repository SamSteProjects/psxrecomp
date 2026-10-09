"""Retail controller flag groups with independently qualified Current selectors."""
from copy import deepcopy
from .project import ProjectError
from .controller_references import controller_source_evidence

REFERENCE_FIELDS={'pc','byte_offset','mnemonic','bank','operation','index','scope','extended_target',
                  'context_resolution','index_semantics','status','runtime_value'}


def validate_controller_flag_asset(record):
    from .flag_assets import _ASSET_FIELDS, _WRAPPER_FIELDS, _SCOPES, _coverage, _metadata
    def reject():raise ProjectError('Controller flag asset differs from its read-only source ownership')
    integer=lambda value,low,high:type(value) is int and low<=value<=high
    if not isinstance(record,dict) or not _ASSET_FIELDS|{'controller_source_evidence'} <= set(record) or set(record)-_ASSET_FIELDS-_WRAPPER_FIELDS-{'controller_source_evidence'}:reject()
    script=record['script_id'];scene=script.split('/controllers/man-p1/')[0].replace('script://','scene://',1) if isinstance(script,str) else ''
    if not scene.startswith('scene://') or script!='script://'+scene[8:]+'/controllers/man-p1/0000':reject()
    proof=record['controller_source_evidence'];source=record['source_record']
    if not isinstance(proof,dict) or set(proof)!={'source_record','entry_pc','local_count','reference_commit','relationship','execution'} or proof.get('source_record')!=source:reject()
    metadata=dict(id=script,semantic_id=script,kind='controller',asset_kind='controller',scene_id=scene,owner_scene_id=scene,
        read_only=True,runtime_binding='not_asserted',source_record=source,entry_pc=proof['entry_pc'],local_count=proof['local_count'],reference_commit=proof['reference_commit'])
    document=dict(scene=dict(semantic_id=scene,name=scene[8:]),source=dict(disc_identity=source.get('disc_identity') if isinstance(source,dict) else None))
    if controller_source_evidence(metadata,scene,document)!=proof:reject()
    bank=record['bank'];index=record['index'];target=record['extended_target'];context='current' if target is None else f'extended-{target}'
    identity=script.replace('script://','flag-reference://',1)+f'/{context}/{bank}/{index}'
    if (not isinstance(bank,str) or bank not in _SCOPES or record['scope']!=_SCOPES[bank] or not integer(index,0,65535 if bank=='system' else 31)
        or not (target is None or integer(target,0,255)) or record['id']!=identity or record['semantic_id']!=identity
        or record['owner_id']!=script.replace('script://','scene://',1) or type(record['partition']) is not int or record['partition']!=1
        or record['asset_kind']!='flag' or record.get('kind','flag')!='flag' or record.get('layer','derived')!='derived'
        or record.get('scene_id',scene)!=scene or record['read_only'] is not True or record['grouping_layer']!='retail'
        or record['runtime_binding']!='unresolved' or record['runtime_value'] is not None
        or record['script_status'] not in ('decoded_supported_paths','partial')
        or not all(isinstance(record[key],str) and 0<len(record[key])<=8192 for key in ('name','script_name'))):reject()
    refs=record['references']
    if not isinstance(refs,list) or not 1<=len(refs)<=4096:reject()
    sites=set()
    for row in refs:
        if not isinstance(row,dict) or set(row)-{'authored_qualification'}!=REFERENCE_FIELDS|{'retail_index','authored_index','effective_index','flag_operand_id'}:reject()
        pc=row['pc'];prefix={'local':'LFLAG','context':'CFLAG','global':'GFLAG','system':'SYSFLAG'}.get(bank)
        if (not integer(pc,proof['entry_pc'],source['byte_length']-1) or pc in sites or type(row['byte_offset']) is not int
            or row['byte_offset']!=source['byte_offset']+pc or row['bank']!=bank or type(row['index']) is not int or row['index']!=index
            or row['scope']!=record['scope'] or row['extended_target']!=target or type(row['extended_target']) is not type(target)
            or row['runtime_value'] is not None
            or type(row['retail_index']) is not int or row['retail_index']!=index or type(row['effective_index']) is not int or row['effective_index']!=(row['authored_index'] if row['authored_index'] is not None else index)
            or row['context_resolution']!=('current_script_context' if target is None else 'extended_target_unresolved')
            or row['index_semantics']!=('encoded_selector_not_resolved_runtime_bit' if bank=='system' else 'operand_masked_to_five_bits')
            or row['status']!=('bank_width_unresolved' if bank=='local' and index>=16 else 'encoded_reference')
            or not (prefix and row['operation'] in ('set','clear','test') and row['mnemonic']==prefix+'_'+row['operation'].upper()
                    or row['operation']=='test' and (row['mnemonic']=='FLAG_WORD_BRANCH' and bank in ('local','global','context') or row['mnemonic']=='COND_JMP' and bank=='extra'))):reject()
        authored=row['authored_index']
        if authored is None:
            if row['flag_operand_id'] is not None or 'authored_qualification' in row:reject()
        else:
            from .flag_qualification import validate
            operand=script+f'/system-flag/{pc:04x}'
            if bank!='system' or target is not None or row['flag_operand_id']!=operand:reject()
            validate(row.get('authored_qualification'),record['owner_id'],operand,source['sha256'],pc,row['mnemonic'],target,index,authored,controller=True)
        sites.add(pc)
    if type(record['reference_count']) is not int or record['reference_count']!=len(refs) or type(record['authored_reference_count']) is not int or record['authored_reference_count']!=sum(row['authored_index'] is not None for row in refs):reject()
    _coverage(record['coverage'])
    if not isinstance(record['limitations'],list) or len(record['limitations'])>256 or any(not isinstance(row,str) or not 0<len(row)<=8192 for row in record['limitations']):reject()
    _metadata(record)
    return record


def build_controller_flag_assets(controller,document,edits=None,qualifications=None):
    edits=edits or {};qualifications=qualifications or {};used=set()
    scene=document['scene']['semantic_id'];script=controller['semantic_id']
    proof=controller_source_evidence(dict(controller,id=script,scene_id=scene),scene,document)
    rows=controller['flag_references']
    if not isinstance(rows,list) or len(rows)>4096 or type(controller['flag_reference_count']) is not int or len(rows)!=controller['flag_reference_count']:raise ProjectError('Controller flag catalog exceeds source coverage')
    groups={}
    for reference in rows:
        target=reference['extended_target'];context='current' if target is None else f'extended-{target}'
        identity=script.replace('script://','flag-reference://',1)+f"/{context}/{reference['bank']}/{reference['index']}"
        group=groups.setdefault(identity,dict(id=identity,semantic_id=identity,asset_kind='flag',script_id=script,
            script_name=controller['name'],owner_id=script.replace('script://','scene://',1),partition=1,
            script_status=controller['inspection_status'],source_record=deepcopy(controller['source_record']),
            bank=reference['bank'],index=reference['index'],scope=reference['scope'],extended_target=target,
            runtime_binding='unresolved',runtime_value=None,references=[],read_only=True,grouping_layer='retail',
            name=f"{reference['bank'].title()} {reference['index']} · {context} · Scene Entry Controller",
            authored_reference_count=0,coverage=dict(script_count=1,partial_script_count=int(controller['inspection_status']=='partial'),unavailable_script_count=0),
            limitations=['Retail controller source only; runtime values and dispatch target bindings remain unresolved.','Only independently source-qualified normal controller system selectors expose authored values.'],controller_source_evidence=deepcopy(proof)))
        row=dict(deepcopy(reference),retail_index=reference['index'],authored_index=None,effective_index=reference['index'],flag_operand_id=None)
        operand=script+f"/system-flag/{reference['pc']:04x}"
        if operand in edits:
            row.update(authored_index=edits[operand]['index'],effective_index=edits[operand]['index'],flag_operand_id=operand,authored_qualification=deepcopy(qualifications.get(operand)))
            group['authored_reference_count']+=1;used.add(operand)
        group['references'].append(row)
    if used!=set(edits):raise ProjectError('Controller authored selector is absent from Retail flag discovery')
    for group in groups.values():
        group['reference_count']=len(group['references']);group['references'].sort(key=lambda row:row['pc']);validate_controller_flag_asset(group)
    return [groups[key] for key in sorted(groups)]


def qualified_controller_flag_assets(project,controller,document):
    """Recompose native selectors before exposing annotations; works for any imported scene."""
    owner=controller['semantic_id'].replace('script://','scene://',1)
    components=deepcopy(project.overrides.get(owner,{}))
    if not components:return build_controller_flag_assets(controller,document)
    from .controller_system_flags import COMPONENT,validate,validate_components
    from .flag_qualification import from_target
    from importer.controller_system_flags import load_controller_system_flag_context
    from importer.core import ImportError as RetailImportError
    from hashlib import sha256
    validate_components(project,owner,components)
    if any(value['source_record_sha256']!=controller['source_record']['sha256'] for value in components.values()):
        raise ProjectError('Controller flag annotations require unchanged Retail source ownership')
    if COMPONENT not in components:return build_controller_flag_assets(controller,document)
    value=validate(project,owner,components[COMPONENT]);entries=value['entries']
    try:
        context=load_controller_system_flag_context(project.disc_path,document['scene']['name'])
        _,record,_=context._source.verified_record(owner)
        if sha256(record).hexdigest()!=value['source_record_sha256'] or value['source_record_sha256']!=controller['source_record']['sha256']:
            raise ProjectError('Controller flag annotations require unchanged Retail source')
        context.patch(entries)
        targets={row['semantic_id']:row for row in context.options(owner)['targets']}
        if set(entries)-set(targets):raise ProjectError('Controller selector lacks native operand qualification')
        proofs={key:from_target(targets[key],fields,controller=True) for key,fields in entries.items()}
    except RetailImportError as exc:raise ProjectError('Controller flag source verification failed: '+str(exc)) from exc
    return build_controller_flag_assets(controller,document,entries,proofs)
