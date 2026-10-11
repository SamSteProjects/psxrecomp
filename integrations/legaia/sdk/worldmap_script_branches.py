"""World branch project binding and reviewed branch-last MAN composition."""
from base64 import b64encode
from copy import deepcopy
from hashlib import sha256
import re
import json

from importer.worldmap_branch_authoring import branch_record_options,patch_branch_record
from importer.branch_authoring import validate_branch_values
from importer.serialization import serialize_lzs_decoded
from .project import ProjectError,digest

COMPONENT='WorldScriptBranches'

def _finish(project,key,result):
    from .worldmap_script_operands import _fresh
    if len(json.dumps(result,allow_nan=False).encode('utf-8'))>32*1024*1024:raise ProjectError('World branch response exceeds its private budget')
    _fresh(project,key)
    return result

def owner(scene):
    from .worldmap_script_operands import owner as operand_owner
    operand_owner(scene)
    return 'worldmap://'+scene+'/script-branches'

def validate(project,identifier,binding):
    scene=next((s for s in ('map01','map02','map03') if owner(s)==identifier),None)
    if scene is None or not isinstance(binding,dict) or set(binding)!={'source_disc_sha256','source_man_sha256','entries'}:
        raise ProjectError('World branch binding requires its dedicated source owner')
    for name in ('source_disc_sha256','source_man_sha256'):
        if not isinstance(binding[name],str) or not re.fullmatch('[0-9a-f]{64}',binding[name]):raise ProjectError('World branch source digest is invalid')
    if {d['source']['disc_identity'] for d in project.imports.values()}!={'sha256:'+binding['source_disc_sha256']}:
        raise ProjectError('World branch binding differs from imported disc provenance')
    entries=binding['entries']
    if not isinstance(entries,dict) or not 1<=len(entries)<=512:raise ProjectError('World branches require bounded nonempty source entries')
    count=0
    for script,entry in entries.items():
        if not isinstance(script,str) or not re.fullmatch('script://'+scene+'/worldmap/man-p0/[0-9]{4}',script) or not isinstance(entry,dict) or set(entry)!={'source_record_sha256','shared_record','branches'}:
            raise ProjectError('World branch source entry is invalid')
        if not isinstance(entry['source_record_sha256'],str) or not re.fullmatch('[0-9a-f]{64}',entry['source_record_sha256']) or type(entry['shared_record']) is not bool:
            raise ProjectError('World branch record provenance or consent is invalid')
        if not isinstance(entry['branches'],dict) or not entry['branches']:raise ProjectError('World branch record requires destination edits')
        count+=len(entry['branches'])
        if count>1024:raise ProjectError('World branch binding exceeds its instruction budget')
        for pc,values in entry['branches'].items():
            if not isinstance(pc,str) or not re.fullmatch('[0-9a-f]{4}',pc):raise ProjectError('World branch PC must be a source hexadecimal offset')
            validate_branch_values(values)
    return deepcopy(binding)

def compose(man,rows,fixed,binding):
    if not binding:return fixed,[]
    result=bytearray(fixed);audit=[]
    for script,edit in sorted(binding['entries'].items()):
        row=rows.get(script)
        if row is None or row['source_record']['sha256']!=edit['source_record_sha256']:raise ProjectError('World branch source record is unavailable')
        if len(row['source_instance_ids'])>1 and edit['shared_record'] is not True:raise ProjectError('Shared World branches require consent for every source object')
        at=row['source_record']['byte_offset'];end=at+row['source_record']['byte_length']
        candidate,changes,_=patch_branch_record(man[at:end],row['entry_pc'],{int(pc,16):v for pc,v in edit['branches'].items()},operand_record=fixed[at:end],base_offset=at)
        result[at:end]=candidate
        audit.extend(dict(change,semantic_id=script,scene=row['source_scene'],affected_source_entities=deepcopy(row['source_instance_ids'])) for change in changes)
    return bytes(result),audit

def compose_project(project,scene,man,rows,provenance,fixed):
    components=project.overrides.get(owner(scene),{})
    if components and set(components)!={COMPONENT}:raise ProjectError('World branch owner accepts only its dedicated component')
    binding=components.get(COMPONENT)
    if binding:
        validate(project,owner(scene),binding)
        if any(binding[k]!=v for k,v in provenance.items()):raise ProjectError('World branch source changed under authored targets')
    return compose(man,rows,fixed,binding)

def _inputs(project,script,key):
    from .worldmap_script_operands import _fresh,_scene,context,compose as fixed_compose
    _fresh(project,key);scene=_scene(script);inputs=context(project,scene)
    man,rows,provenance,_,_,_,_,operand_binding,_,_=inputs
    row=rows.get(script)
    if row is None:raise ProjectError('World branch source has no registered record')
    fixed,_=fixed_compose(man,rows,operand_binding)
    binding=project.overrides.get(owner(scene),{}).get(COMPONENT)
    return scene,inputs,row,fixed,binding

def options(project,script,key):
    scene,inputs,row,fixed,binding=_inputs(project,script,key);man=inputs[0];at=row['source_record']['byte_offset'];end=at+row['source_record']['byte_length']
    edits=(binding or {}).get('entries',{}).get(script,{}).get('branches',{})
    current,_,graph=patch_branch_record(man[at:end],row['entry_pc'],{int(pc,16):v for pc,v in edits.items()},operand_record=fixed[at:end])
    result=dict(schema_version='legaia.world-script-branches.v1',project_path=str(project.root),source_key=key,script_id=script,
        source_record=deepcopy(row['source_record']),entry_pc=row['entry_pc'],source_instance_ids=deepcopy(row['source_instance_ids']),
        retail_record_base64=b64encode(man[at:end]).decode(),fixed_record_base64=b64encode(fixed[at:end]).decode(),current_record_base64=b64encode(current).decode(),
        branch_options=branch_record_options(man[at:end],row['entry_pc']),authored_targets=deepcopy(edits),current_graph=graph,
        graph_offset_scope='source_record_relative',project_changed=False,gameplay_verified=False)
    return _finish(project,key,result)

def review(project,script,key,pc,values,shared):
    scene,inputs,row,fixed,binding=_inputs(project,script,key)
    man,rows,provenance,_,_,slot,carrier,_,current,_=inputs
    if type(pc) is not int or type(shared) is not bool or len(row['source_instance_ids'])>1 and not shared:raise ProjectError('World branch review requires exact source PC and shared consent')
    target=validate_branch_values(values);at=row['source_record']['byte_offset'];end=at+row['source_record']['byte_length']
    original=branch_record_options(man[at:end],row['entry_pc']);source_target=next((t for t in original['targets'] if t['pc']==pc),None)
    if source_target is None:raise ProjectError('Choose an original supported World branch')
    after=deepcopy(binding or dict(provenance,entries={}));entry=after['entries'].setdefault(script,dict(source_record_sha256=row['source_record']['sha256'],shared_record=shared,branches={}))
    entry['shared_record']=shared;pc_key=f'{pc:04x}'
    if target==source_target['target_pc']:entry['branches'].pop(pc_key,None)
    else:entry['branches'][pc_key]=deepcopy(values)
    if not entry['branches']:after['entries'].pop(script,None)
    if not after['entries']:after=None
    candidate,audit=compose(man,rows,fixed,after)
    # Validate a reset as well: invalid destinations cannot be disguised as
    # removals, and retained source anchors remain available in the receipt.
    edits=(after or {}).get('entries',{}).get(script,{}).get('branches',{})
    _,_,graph=patch_branch_record(man[at:end],row['entry_pc'],{int(k,16):v for k,v in edits.items()},operand_record=fixed[at:end])
    _,compression=serialize_lzs_decoded(carrier[slot['compressed_stream_offset']:slot['compressed_stream_offset']+slot['compressed_bytes_consumed']],len(man),candidate,scene+' World branch MAN')
    result=dict(schema_version='legaia.world-script-branch-review.v1',project_path=str(project.root),source_key=key,script_id=script,pc=pc,
        retail_values={'target_pc':source_target['target_pc']},current_values=deepcopy((binding or {}).get('entries',{}).get(script,{}).get('branches',{}).get(pc_key,{'target_pc':source_target['target_pc']})),
        proposed_values=deepcopy(values),source_instance_ids=deepcopy(row['source_instance_ids']),shared=shared,
        current_man_sha256=sha256(current).hexdigest(),candidate_man_sha256=sha256(candidate).hexdigest(),candidate_record_base64=b64encode(candidate[at:end]).decode(),
        changes=[dict(decoded_byte_offset=i,before_byte=a,after_byte=b) for i,(a,b) in enumerate(zip(current,candidate)) if a!=b],
        compression=compression,candidate_graph=graph,graph_offset_scope='source_record_relative',no_op=current==candidate,project_changed=False,gameplay_verified=False)
    _finish(project,key,result);result['review_key']=digest(result);return result,after

def apply(project,command):
    if set(command)!={'type','script_id','source_key','pc','values','shared','review_key'}:raise ProjectError('World branch Apply requires the exact reviewed scope')
    report,binding=review(project,command['script_id'],command['source_key'],command['pc'],command['values'],command['shared'])
    if report['no_op'] or command['review_key']!=report['review_key']:raise ProjectError('World branch review is stale or makes no change')
    from .worldmap_script_operands import _scene
    identifier=owner(_scene(command['script_id']));before=deepcopy(project.overrides.get(identifier));after={COMPONENT:binding} if binding else None
    if after:project.overrides[identifier]=after
    else:project.overrides.pop(identifier,None)
    project.undo_stack.append(dict(entity_id=identifier,before=before,after=deepcopy(after)));project.redo_stack.clear()
