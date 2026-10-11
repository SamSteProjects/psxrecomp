"""World P0 fixed animation operands through source-owned Review/Apply/Build."""
from base64 import b64encode
from copy import deepcopy
from hashlib import sha256
import re
from importer.pipeline import _disc_context
from importer.worldmap_geometry import KINGDOM_BASES, _kingdom_table, _slot
from importer.worldmap_behavior_catalog import load_worldmap_behavior_catalog
from importer.animation_operand_authoring import SPECS, validate_animation_operand_values, patch_animation_operands_target
from importer.script_inspection import inspect_record
from importer.serialization import serialize_lzs_decoded
from .project import ProjectError, digest
from .worldmap_authoring import state_key

COMPONENT='WorldScriptAnimationOperands'
LIMITATIONS=[
    'Only reached fixed SET_MODEL_ANIMATION and EFFECT_ANIMATION_TRIGGER operands without source decoder stops are writable.',
    'Encoded model/effect IDs are arguments, not resolved model or animation asset references.',
    'Opcode, dispatch context, record length, header, branch topology and unrelated MAN bytes remain fixed.',
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

def validate(project,identifier,binding):
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
            mnemonic=next((m for m,spec in SPECS.items() if isinstance(values,dict) and set(values)=={k for k,_ in spec}),None)
            validate_animation_operand_values(mnemonic,values)
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
        if row is None or row['source_record']['sha256']!=edit['source_record_sha256'] or len(row['source_instance_ids'])>1 and edit['shared_record'] is not True:raise ProjectError('World script authored source identity is unavailable')
        at=row['source_record']['byte_offset'];end=at+row['source_record']['byte_length'];record=man[at:end]
        patches={}
        for pc,values in sorted(edit['operands'].items()):
            changed,changes=patch_animation_operands_target(record,row['entry_pc'],int(pc,16),values,base_offset=at)
            for n,(a,b) in enumerate(zip(record,changed)):
                if a!=b:
                    if n in patches and patches[n]!=b:raise ProjectError('World script operands overlap')
                    patches[n]=b
            audit.extend(dict(change,semantic_id=script,scene=row['source_scene'],scope='world-script-animation-operands-only',affected_source_entities=row['source_instance_ids']) for change in changes)
        for n,b in patches.items():result[at+n]=b
        candidate=bytes(result[at:end]);before=inspect_record(record,row['entry_pc']);after=inspect_record(candidate,row['entry_pc'])
        shape=lambda g:[(n['pc'],n['mnemonic'],n['length'],n['target_context'],n['successors']) for n in g['instructions']]
        if before['stops']!=after['stops'] or shape(before)!=shape(after):raise ProjectError('Composed World operands changed source control flow')
    return bytes(result),audit

def context(project,scene):
    man,rows,provenance,index,offset,slot,carrier=source(project,scene)
    components=project.overrides.get(owner(scene),{})
    if components and set(components)!={COMPONENT}:raise ProjectError('World script owner accepts only its dedicated component')
    binding=components.get(COMPONENT)
    if binding:
        validate(project,owner(scene),binding)
        if any(binding[k]!=v for k,v in provenance.items()):raise ProjectError('World script source changed under authored operands')
    current,audit=compose(man,rows,binding)
    return man,rows,provenance,index,offset,slot,carrier,binding,current,audit

def _fresh(project,key):
    if project.mode!='edit' or key!=state_key(project):raise ProjectError('World script authoring requires fresh Edit project inputs')

def options(project,script,key):
    _fresh(project,key);scene=_scene(script)
    man,rows,_,_,_,_,_,binding,current,_=context(project,scene);row=rows.get(script)
    if row is None:raise ProjectError('World script has no registered source binding')
    at=row['source_record']['byte_offset'];end=at+row['source_record']['byte_length'];record=man[at:end];graph=inspect_record(record,row['entry_pc']);targets=[]
    authored=(binding or {}).get('entries',{}).get(script,{}).get('operands',{})
    if not graph['stops']:
        for node in graph['instructions']:
            if node['mnemonic'] not in SPECS:continue
            values={k:node['operands'][k] for k,_ in SPECS[node['mnemonic']]}
            patch_animation_operands_target(record,row['entry_pc'],node['pc'],values)
            targets.append(dict(pc=node['pc'],mnemonic=node['mnemonic'],target_context=node['target_context'],retail_values=values,authored_values=deepcopy(authored.get(f'{node["pc"]:04x}')),current_values=deepcopy(authored.get(f'{node["pc"]:04x}',values))))
    result=dict(schema_version='legaia.world-script-animation-operands.v1',project_path=str(project.root),source_key=key,script_id=script,source_record=deepcopy(row['source_record']),entry_pc=row['entry_pc'],source_instance_ids=deepcopy(row['source_instance_ids']),record_base64=b64encode(record).decode(),current_record_base64=b64encode(current[at:end]).decode(),targets=targets,limitations=list(LIMITATIONS),project_changed=False,gameplay_verified=False)
    _fresh(project,key);return result

def review(project,script,key,pc,values,shared):
    report=options(project,script,key);target=next((t for t in report['targets'] if type(pc) is int and t['pc']==pc),None)
    if target is None:raise ProjectError('Choose a reached supported World animation instruction')
    if type(shared) is not bool or len(report['source_instance_ids'])>1 and not shared:raise ProjectError('Shared World script edits require consent for all source objects')
    validate_animation_operand_values(target['mnemonic'],values)
    scene=_scene(script);man,rows,provenance,_,_,slot,carrier,binding,current,_=context(project,scene)
    after=deepcopy(binding or dict(provenance,entries={}));entries=after['entries'];edit=entries.setdefault(script,dict(source_record_sha256=report['source_record']['sha256'],operands={},shared_record=shared));edit['shared_record']=shared
    pc_key=f'{pc:04x}'
    if values==target['retail_values']:edit['operands'].pop(pc_key,None)
    else:edit['operands'][pc_key]=deepcopy(values)
    if not edit['operands']:entries.pop(script,None)
    if not entries:after=None
    candidate,audit=compose(man,rows,after)
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
    for scene in KINGDOM_BASES:
        if COMPONENT not in project.overrides.get(owner(scene),{}):continue
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
