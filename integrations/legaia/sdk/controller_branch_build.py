"""Independent complete-word receipts for controller branch Build composition."""
from copy import deepcopy
from hashlib import sha256
from importer.controller_branches import ControllerBranchAuthoringContext
from importer.scene_controller import controller_record


def compose_branches(selectors,owner,components,working,previous=(),*,appended=False):
    from .build import BuildError
    context=ControllerBranchAuthoringContext(selectors._source,system_selectors=components.get('ControllerSystemFlags',{}).get('entries',{}))
    entries=components['ControllerBranches']['entries'];options={t['semantic_id']:t for t in context.options(owner)['targets']}
    if set(entries)-set(options):raise BuildError('Controller Build branch is not qualified by Retail source')
    source_offset,record,entry=selectors._source.verified_record(owner)
    if appended:offset,current_record,current_entry=controller_record(working,selectors._source.scene)
    else:offset,current_record,current_entry=source_offset,working[source_offset:source_offset+len(record)],entry
    if current_entry!=entry or len(current_record)!=len(record):raise BuildError('Controller branch Build record extent changed')
    expected={key:dict(options[key],decoded_byte_offset=offset+options[key]['operand_pc'],requested_values=fields) for key,fields in entries.items()}
    patched,changes=context.patch_appended(working,entries) if appended else context.patch_composed(working,entries)
    if not isinstance(patched,bytes) or len(patched)!=len(working):raise BuildError('Controller branch serializer changed MAN length')
    occupied={i for c in previous for i in range(c['decoded_byte_offset'],c['decoded_byte_offset']+c.get('byte_length',1))}
    allowed=set();desired={}
    for key,target in expected.items():
        at=target['decoded_byte_offset'];source_at=source_offset+target['operand_pc'];span={at,at+1}
        if type(at) is not int or not 0<=at<=len(working)-2 or span&(occupied|allowed) or working[at:at+2]!=selectors._man[source_at:source_at+2]:
            raise BuildError('Controller branch overlaps an authored span or changed source preimage')
        allowed.update(span);desired[key]=((target['requested_values']['target_pc']-target['operand_pc'])&65535).to_bytes(2,'little')
    seen=set();audited=set()
    for receipt in changes:
        key=receipt.get('branch_id');target=expected.get(key)
        if target is None or key in seen:raise BuildError('Controller branch audit has missing or duplicate identity')
        at=target['decoded_byte_offset'];source_at=source_offset+target['operand_pc'];before=working[at:at+2];after=desired[key]
        integer_fields=['pc','decoded_byte_offset','record_relative_byte_offset','byte_length','before_target_pc','before_value','after_target_pc','after_value']+(['source_decoded_byte_offset'] if appended else [])
        if (any(type(receipt.get(field)) is not int for field in integer_fields) or receipt.get('owner_id')!=owner or receipt.get('pc')!=target['pc'] or receipt.get('mnemonic')!=target['mnemonic']
            or receipt.get('target_context')!=target['target_context'] or type(receipt.get('target_context')) is not type(target['target_context'])
            or receipt.get('condition')!=target['condition'] or receipt.get('encoding')!=target['encoding']
            or receipt.get('field')!='script.branch_target' or receipt.get('scope')!='script-branch-target-only'
            or receipt.get('decoded_byte_offset')!=at or receipt.get('record_relative_byte_offset')!=target['operand_pc'] or receipt.get('byte_length')!=2
            or receipt.get('before_target_pc')!=target['target_pc'] or receipt.get('before_value')!=target['target_pc']
            or receipt.get('after_target_pc')!=target['requested_values']['target_pc'] or receipt.get('after_value')!=target['requested_values']['target_pc']
            or receipt.get('before_hex')!=before.hex() or receipt.get('after_hex')!=after.hex() or patched[at:at+2]!=after
            or receipt.get('source_record_sha256')!=sha256(record).hexdigest() or receipt.get('effective_record_sha256')!=sha256(current_record).hexdigest()
            or receipt.get('candidate_record_sha256')!=sha256(patched[offset:offset+len(record)]).hexdigest()
            or receipt.get('source_decoded_man_sha256')!=sha256(selectors._man).hexdigest()
            or appended and (receipt.get('source_decoded_byte_offset')!=source_at or receipt.get('appended_man_sha256')!=sha256(working).hexdigest())
            or before==after):raise BuildError('Controller branch receipt differs from its source or requested word')
        byte_changes=[dict(decoded_byte_offset=at+i,before_byte=a,after_byte=b) for i,(a,b) in enumerate(zip(before,after)) if a!=b]
        if receipt.get('changed_bytes')!=byte_changes or any(type(value) is not int for row in receipt.get('changed_bytes',[]) for value in row.values()):raise BuildError('Controller branch byte receipt differs from literal output')
        seen.add(key);audited.update((at,at+1))
    for key,target in expected.items():
        at=target['decoded_byte_offset']
        if patched[at:at+2]!=desired[key] or desired[key]!=working[at:at+2] and key not in seen:
            raise BuildError('Controller requested branch is missing from its complete audit')
    if any(a!=b and i not in audited for i,(a,b) in enumerate(zip(working,patched))):raise BuildError('Controller branch changed an unaudited MAN byte')
    from importer.man_layout import read_man_layout
    if read_man_layout(working)!=read_man_layout(patched):raise BuildError('Controller branch changed MAN layout')
    changes=deepcopy(changes)
    for receipt in changes:receipt.update(semantic_id=owner,record_index=0,owner_kind='scene_controller')
    return patched,changes
