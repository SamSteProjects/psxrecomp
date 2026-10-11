"""World P0 fixed operands through source-owned Review/Apply/Build."""
from base64 import b64encode
from copy import deepcopy
from hashlib import sha256
import re
import json
from importer.pipeline import _disc_context
from importer.worldmap_geometry import KINGDOM_BASES, _kingdom_table, _slot
from importer.worldmap_behavior_catalog import load_worldmap_behavior_catalog
from importer.animation_operand_authoring import SPECS, validate_animation_operand_values, patch_animation_operands_target
from importer.effect_color_authoring import validate_effect_color_values, patch_effect_color_target
from importer.model_selector_authoring import validate_model_selector_values, patch_model_selector_target
from importer.flag_authoring import validate_flag_values, patch_flag_bit
from importer.system_flag_authoring import validate_system_flag_values, patch_system_flag_selector
from importer.movement_authoring import validate_movement_values, patch_movement_target
from importer.core import ImportError
from importer.script_inspection import inspect_record
from importer.script_operand_composition import compose_script_operands
from importer.serialization import serialize_lzs_decoded
from .project import ProjectError, digest
from .worldmap_authoring import state_key

COMPONENT='WorldScriptOperands'
LEGACY_COMPONENT='WorldScriptAnimationOperands'
COMPONENTS={COMPONENT,LEGACY_COMPONENT}
COLOR='EFFECT_COLOR_INTENSITY'
MODEL='SET_ACTOR_MODEL'
FLAGS=tuple(f'{bank}_{operation}' for bank in ('LFLAG','GFLAG','CFLAG') for operation in ('SET','CLEAR','TEST'))
SYSTEM_FLAGS=('SYSFLAG_SET','SYSFLAG_CLEAR','SYSFLAG_TEST')
MOVEMENT='MOVE_TO'

def validate_world_movement(values):
    if not isinstance(values,dict) or set(values)!={'x','z'} or any(type(v) is not int for v in values.values()):
        raise ImportError('World MOVE_TO requires integer source-grid X and Z arguments')
    return validate_movement_values(values)

def patch_world_movement(record,entry,pc,values,*,base_offset=0):
    validate_world_movement(values)
    if next((n['mnemonic'] for n in inspect_record(record,entry)['instructions'] if n['pc']==pc),None)!=MOVEMENT:
        raise ImportError('World movement authoring requires a reached MOVE_TO instruction')
    candidate,changes=patch_movement_target(record,entry,pc,values,base_offset=base_offset)
    return candidate,[dict(change,byte_length=1,before_hex=bytes([change['before_byte']]).hex(),after_hex=bytes([change['after_byte']]).hex()) for change in changes]
def patch_world_flag(record,entry,pc,values,*,base_offset=0):
    candidate,changes=patch_flag_bit(record,entry,pc,values,base_offset=base_offset)
    return candidate,[dict(change,byte_length=1,before_hex=bytes([change['before_byte']]).hex(),after_hex=bytes([change['after_byte']]).hex()) for change in changes]
ARGUMENTS={m:dict(fields=tuple(k for k,_ in spec),writer=patch_animation_operands_target,
    validator=lambda values,m=m:validate_animation_operand_values(m,values),scope='world-script-animation-operands-only') for m,spec in SPECS.items()}
ARGUMENTS[COLOR]=dict(fields=('red','green','blue','intensity'),writer=patch_effect_color_target,validator=validate_effect_color_values,scope='world-script-effect-color-operands-only')
ARGUMENTS[MODEL]=dict(fields=('model_selector_signed',),writer=patch_model_selector_target,validator=validate_model_selector_values,scope='world-script-model-selector-only')
for mnemonic in FLAGS:ARGUMENTS[mnemonic]=dict(fields=('bit',),writer=patch_world_flag,validator=validate_flag_values,scope='world-script-flag-bit-only')
for mnemonic in SYSTEM_FLAGS:ARGUMENTS[mnemonic]=dict(fields=('index',),writer=patch_system_flag_selector,validator=validate_system_flag_values,scope='world-script-system-flag-only')
ARGUMENTS[MOVEMENT]=dict(fields=('x','z'),writer=patch_world_movement,validator=validate_world_movement,scope='world-script-movement-only')
def mnemonic_for(values):
    return next((m for m,spec in ARGUMENTS.items() if isinstance(values,dict) and set(values)==set(spec['fields'])),None)
def validate_values(mnemonic,values):
    if mnemonic not in ARGUMENTS:raise ProjectError('World instruction arguments have unsupported typed fields')
    return ARGUMENTS[mnemonic]['validator'](values)
def writer_for(values):
    mnemonic=mnemonic_for(values)
    if mnemonic not in ARGUMENTS:raise ProjectError('World instruction arguments have no supported writer')
    return ARGUMENTS[mnemonic]['writer']
LIMITATIONS=[
    'Only reached supported fixed instruction arguments without source decoder stops are writable.',
    'Flag bits preserve the upper operand bits; local bits16..31 and context SET8/CLEAR10 side effects remain unsupported.',
    'Flag bit indices and normal system selectors are encoded arguments, not observed live values or named story variables.',
    'System selectors use opcode low4 and the following byte; the operation/high nibble and TEST delta stay fixed. Extended system addressing remains unsupported.',
    'Encoded system selector range0..4095 does not establish native bank capacity or valid runtime addressing.',
    'RGB are encoded bytes and intensity is signed16; visual color space and rendering remain unverified.',
    'Encoded model/effect IDs are arguments, not resolved model or animation asset references.',
    'MOVE_TO X/Z are source-grid arguments, exactly representable multiples of64 from64 to16384; World actor binding, Y, collision and live destination coordinates remain unverified.',
    'Signed model selectors do not establish model-pool ownership, restaging or visible models.',
    'Operation, dispatch context, record length, header, branch topology and unrelated MAN bytes remain fixed; only system-selector opcode low bits are authored.',
    'All source objects sharing a script record receive the same authored operands; shared consent is required.',
    'Current script bytes are authored data, not observed execution, timing, activation or gameplay acceptance.',
    'Build uses the existing bounded LZS span; incompatible overlapping MAN edits and compressed growth refuse.'
]

def owner(scene):
    if scene not in KINGDOM_BASES:raise ProjectError('World script authoring requires a supported kingdom')
    return 'worldmap://'+scene+'/script-operands'

def _scene(script):
    match=re.fullmatch(r'script://(map0[123])/worldmap/man-p0/([0-9]{4})',script or '') if isinstance(script,str) else None
    if not match:raise ProjectError('World script identity must name a registered source P0 record')
    return match[1]

def validate(project,identifier,binding,component=COMPONENT):
    scene=next((s for s in KINGDOM_BASES if identifier==owner(s)),None)
    if scene is None or not isinstance(binding,dict) or set(binding)!={'source_disc_sha256','source_man_sha256','entries'} or any(not isinstance(binding[k],str) or not re.fullmatch('[0-9a-f]{64}',binding[k]) for k in ('source_disc_sha256','source_man_sha256')) or not isinstance(binding['entries'],dict) or not 1<=len(binding['entries'])<=512:
        raise ProjectError('World script operands require a bounded source-bound entry mapping')
    discs={doc['source']['disc_identity'] for doc in project.imports.values()}
    if discs!={'sha256:'+binding['source_disc_sha256']}:raise ProjectError('World script binding differs from the imported disc')
    count=0
    for script,row in binding['entries'].items():
        if _scene(script)!=scene or not isinstance(row,dict) or set(row)!={'source_record_sha256','operands','shared_record'} or type(row['shared_record']) is not bool or not isinstance(row['source_record_sha256'],str) or not re.fullmatch('[0-9a-f]{64}',row['source_record_sha256']) or not isinstance(row['operands'],dict) or not row['operands']:
            raise ProjectError('World script operand owner or source record is invalid')
        for pc,values in row['operands'].items():
            count+=1
            if count>1024 or not isinstance(pc,str) or not re.fullmatch('[0-9a-f]{4}',pc):raise ProjectError('World script operand PCs exceed their bounded scope')
            mnemonic=mnemonic_for(values)
            if component==LEGACY_COMPONENT and mnemonic not in SPECS:raise ProjectError('Legacy World animation component cannot contain other instruction families')
            validate_values(mnemonic,values)
    return deepcopy(binding)

def source(project,scene):
    owner(scene)
    if not project.disc_path or not project.imports:raise ProjectError('World script authoring requires an imported user-owned disc')
    with _disc_context(project.disc_path) as (_,disc_hash,_,archive):
        if {d['source']['disc_identity'] for d in project.imports.values()}!={'sha256:'+disc_hash}:raise ProjectError('World script source differs from imported provenance')
        catalog=load_worldmap_behavior_catalog(project.disc_path,scene)
        _,index,offset,bundle,carrier=_kingdom_table(archive,KINGDOM_BASES[scene]);man,slot=_slot(bundle,carrier,2)
        rows={r['semantic_id']:r for r in catalog['assets'] if r['kind']=='script'}
        for r in rows.values():
            s=r['source_record'];at=s['byte_offset'];end=at+s['byte_length']
            if s['disc_sha256']!=disc_hash or s['prot_entry_index']!=index or s['table_offset']!=offset or s['man_slot']!=slot or sha256(man[at:end]).hexdigest()!=s['sha256']:
                raise ProjectError('World script record differs from its verified carrier')
        provenance=dict(source_disc_sha256=disc_hash,source_man_sha256=sha256(man).hexdigest())
        return man,rows,provenance,index,offset,slot,carrier

def compose(man,rows,binding):
    result=bytearray(man);audit=[]
    if not binding:return man,audit
    for script,edit in sorted(binding['entries'].items()):
        row=rows.get(script)
        if row is None or row['source_record']['sha256']!=edit['source_record_sha256']:raise ProjectError('World script authored source identity is unavailable')
        if len(row['source_instance_ids'])>1 and edit['shared_record'] is not True:raise ProjectError('Shared World script operands lack consent for every source object')
        at=row['source_record']['byte_offset'];end=at+row['source_record']['byte_length'];record=man[at:end]
        candidate,changes=compose_script_operands(record,row['entry_pc'],[
            (writer_for(values),int(pc,16),values)
            for pc,values in sorted(edit['operands'].items())],base_offset=at)
        result[at:end]=candidate
        audit.extend(dict(change,semantic_id=script,scene=row['source_scene'],scope=ARGUMENTS[change['mnemonic']]['scope'],affected_source_entities=row['source_instance_ids']) for change in changes)
    return bytes(result),audit

def context(project,scene):
    man,rows,provenance,index,offset,slot,carrier=source(project,scene)
    components=project.overrides.get(owner(scene),{})
    if components and (len(components)!=1 or not set(components)<=COMPONENTS):raise ProjectError('World script owner accepts only one dedicated component')
    component=next(iter(components),COMPONENT);binding=components.get(component)
    if binding:
        validate(project,owner(scene),binding,component)
        if any(binding[k]!=v for k,v in provenance.items()):raise ProjectError('World script source changed under authored operands')
    current,audit=compose(man,rows,binding)
    from .worldmap_script_branches import compose_project
    current,branch_audit=compose_project(project,scene,man,rows,provenance,current)
    audit.extend(branch_audit)
    return man,rows,provenance,index,offset,slot,carrier,binding,current,audit

def _fresh(project,key):
    if project.mode!='edit' or key!=state_key(project):raise ProjectError('World script authoring requires fresh Edit project inputs')

def options(project,script,key):
    _fresh(project,key);scene=_scene(script)
    return _options(project,script,key,context(project,scene))

def _options(project,script,key,inputs):
    man,rows,_,_,_,_,_,binding,current,_=inputs;row=rows.get(script)
    if row is None:raise ProjectError('World script has no registered source binding')
    at=row['source_record']['byte_offset'];end=at+row['source_record']['byte_length'];record=man[at:end];graph=inspect_record(record,row['entry_pc']);targets=[]
    authored=(binding or {}).get('entries',{}).get(script,{}).get('operands',{})
    if not graph['stops']:
        for node in graph['instructions']:
            if node['mnemonic'] not in ARGUMENTS:continue
            if node['mnemonic']==COLOR:values=dict(zip(('red','green','blue'),node['operands']['rgb']),intensity=node['operands']['intensity'])
            elif node['mnemonic']==MOVEMENT:values={k:node['operands']['target_position'][k] for k in ('x','z')}
            else:values={k:node['operands'][k] for k in ARGUMENTS[node['mnemonic']]['fields']}
            try:writer_for(values)(record,row['entry_pc'],node['pc'],values)
            except ImportError:
                if node['mnemonic'] in FLAGS or node['mnemonic'] in SYSTEM_FLAGS:continue
                raise
            targets.append(dict(pc=node['pc'],mnemonic=node['mnemonic'],target_context=node['target_context'],retail_values=values,authored_values=deepcopy(authored.get(f'{node["pc"]:04x}')),current_values=deepcopy(authored.get(f'{node["pc"]:04x}',values))))
    result=dict(schema_version='legaia.world-script-animation-operands.v1',project_path=str(project.root),source_key=key,script_id=script,source_record=deepcopy(row['source_record']),entry_pc=row['entry_pc'],source_instance_ids=deepcopy(row['source_instance_ids']),record_base64=b64encode(record).decode(),current_record_base64=b64encode(current[at:end]).decode(),targets=targets,limitations=list(LIMITATIONS),project_changed=False,gameplay_verified=False)
    from .worldmap_script_branches import owner as branch_owner,COMPONENT as BRANCH_COMPONENT
    branch_edits=project.overrides.get(branch_owner(row['source_scene']),{}).get(BRANCH_COMPONENT,{}).get('entries',{}).get(script,{}).get('branches',{})
    if branch_edits:
        from importer.worldmap_branch_authoring import branch_record_options
        branch_options=branch_record_options(record,row['entry_pc']);source_targets={t['pc']:t for t in branch_options['targets']}
        changes=[dict(pc=int(pc,16),mnemonic=source_targets[int(pc,16)]['mnemonic'],target_context=source_targets[int(pc,16)]['target_context'],operand_pc=source_targets[int(pc,16)]['operand_pc'],condition=source_targets[int(pc,16)]['condition'],retail_target_pc=source_targets[int(pc,16)]['target_pc'],authored_target_pc=values['target_pc']) for pc,values in sorted(branch_edits.items()) if values['target_pc']!=source_targets[int(pc,16)]['target_pc']]
        if changes:
            result.update(schema_version='legaia.world-script-operands.v2',branch_source_graph=inspect_record(record,row['entry_pc'],base_offset=at),branch_destinations=branch_options['destinations'],branch_changes=changes)
    _fresh(project,key);return result

def inspection(project,script,key):
    """Read-only static Retail/Current analysis from one qualified MAN context."""
    _fresh(project,key);inputs=context(project,_scene(script));source_report=_options(project,script,key,inputs)
    man,rows,_,_,_,_,_,_,current,_=inputs;row=rows[script];at=row['source_record']['byte_offset'];end=at+row['source_record']['byte_length']
    result=dict(schema_version='legaia.world-script-inspection.v1',source=source_report,
        retail_graph=inspect_record(man[at:end],row['entry_pc'],semantic_id=script,base_offset=at),
        current_graph=inspect_record(current[at:end],row['entry_pc'],semantic_id=script,base_offset=at),
        read_only=True,project_changed=False,gameplay_verified=False)
    if len(json.dumps(result,allow_nan=False).encode('utf-8'))>32*1024*1024:raise ProjectError('World script inspection exceeds its private response budget')
    _fresh(project,key);return result

def review(project,script,key,pc,values,shared):
    report=options(project,script,key);target=next((t for t in report['targets'] if type(pc) is int and t['pc']==pc),None)
    if target is None:raise ProjectError('Choose a reached supported World instruction')
    if type(shared) is not bool or len(report['source_instance_ids'])>1 and not shared:raise ProjectError('Shared World script edits require consent for all source objects')
    validate_values(target['mnemonic'],values)
    scene=_scene(script);man,rows,provenance,_,_,slot,carrier,binding,current,_=context(project,scene)
    after=deepcopy(binding or dict(provenance,entries={}));entries=after['entries'];edit=entries.setdefault(script,dict(source_record_sha256=report['source_record']['sha256'],operands={},shared_record=shared));edit['shared_record']=shared
    pc_key=f'{pc:04x}'
    if values==target['retail_values']:edit['operands'].pop(pc_key,None)
    else:edit['operands'][pc_key]=deepcopy(values)
    if not edit['operands']:entries.pop(script,None)
    if not entries:after=None
    candidate,audit=compose(man,rows,after)
    from .worldmap_script_branches import compose_project
    candidate,_=compose_project(project,scene,man,rows,provenance,candidate)
    start=slot['compressed_stream_offset'];consumed=slot['compressed_bytes_consumed']
    _,compression=serialize_lzs_decoded(carrier[start:start+consumed],len(man),candidate,scene+' World script MAN')
    result=dict(schema_version='legaia.world-script-animation-review.v1',project_path=str(project.root),source_key=key,script_id=script,pc=pc,mnemonic=target['mnemonic'],retail_values=target['retail_values'],current_values=target['current_values'],proposed_values=deepcopy(values),source_instance_ids=report['source_instance_ids'],shared=shared,current_man_sha256=sha256(current).hexdigest(),candidate_man_sha256=sha256(candidate).hexdigest(),changes=[dict(decoded_byte_offset=i,before_byte=a,after_byte=b) for i,(a,b) in enumerate(zip(current,candidate)) if a!=b],compression=compression,no_op=candidate==current,project_changed=False,gameplay_verified=False)
    _fresh(project,key);result['review_key']=digest(result);return result,after

def apply(project,command):
    if set(command)!={'type','script_id','source_key','pc','values','shared','review_key'}:raise ProjectError('World script Apply requires the exact reviewed source scope')
    report,binding=review(project,command['script_id'],command['source_key'],command['pc'],command['values'],command['shared'])
    if command['review_key']!=report['review_key'] or report['no_op']:raise ProjectError('World script review is stale or makes no change')
    identifier=owner(_scene(command['script_id']));before=deepcopy(project.overrides.get(identifier));after={COMPONENT:binding} if binding else None
    if after:project.overrides[identifier]=after
    else:project.overrides.pop(identifier,None)
    project.undo_stack.append(dict(entity_id=identifier,before=before,after=deepcopy(after)));project.redo_stack.clear()

def build(project,archive):
    from .texture_build import archive_overlay_patches
    from importer.prot_layout import locate_physical_span
    overlays=[];changes=[]
    from .worldmap_script_branches import owner as branch_owner,COMPONENT as BRANCH_COMPONENT
    for scene in KINGDOM_BASES:
        if not COMPONENTS.intersection(project.overrides.get(owner(scene),{})) and BRANCH_COMPONENT not in project.overrides.get(branch_owner(scene),{}):continue
        man,rows,_,index,offset,slot,carrier,_,current,audit=context(project,scene)
        if not audit:continue
        entry=archive.entry(index);start=slot['compressed_stream_offset'];consumed=slot['compressed_bytes_consumed'];before=carrier[start:start+consumed]
        replacement,compression=serialize_lzs_decoded(before,len(man),current,scene+' World script MAN')
        patches,carriers=archive_overlay_patches(archive,[dict(offset=(archive.node.extent_lba+entry.start_lba)*2048+start,payload=replacement,expected_sha256=sha256(before).hexdigest())])
        table=locate_physical_span(archive,entry.start_lba*2048+offset)
        for patch,provenance in zip(patches,carriers):
            if provenance['map_entry_index']!=table['entry_index']:raise ProjectError('World script descriptor and MAN have different carrier ownership')
            provenance['descriptor_binding']=dict(table_offset=table['offset_within_span'],index=2,type=3)
            payload=patch['payload'];overlays.append(dict(scene=scene,offset=archive.node.extent_lba*2048+patch['offset'],size=len(payload),file=f'assets/{scene}-world-script-man.lzs',payload=payload,sha256=sha256(payload).hexdigest(),expected_sha256=patch['expected_sha256'],carrier=provenance,decoded_before_sha256=sha256(man).hexdigest(),decoded_after_sha256=sha256(current).hexdigest(),compression=compression))
        changes.extend(audit)
    return overlays,changes
