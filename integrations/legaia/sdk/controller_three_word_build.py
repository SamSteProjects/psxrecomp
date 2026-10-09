"""Independent six-byte receipts for controller three-word Build composition."""
from copy import deepcopy
from hashlib import sha256
import struct
from importer.core import ImportError as RetailImportError
from importer.controller_three_words import ControllerThreeWordAuthoringContext,validate_three_word_values
from importer.scene_controller import controller_record
from importer.script_inspection import _instruction
from importer.man_layout import read_man_layout


def _qualified_values(value):
    try:validate_three_word_values(value)
    except RetailImportError:return False
    return True


def compose_three_words(selectors,owner,components,working,previous=(),*,appended=False):
    from .build import BuildError
    context=ControllerThreeWordAuthoringContext(selectors._source)
    entries=components['ControllerThreeWords']['entries'];options={t['semantic_id']:t for t in context.options(owner)['targets']}
    if set(entries)-set(options):raise BuildError('Controller three-word Build target is not qualified by Retail source')
    source_offset,record,entry=selectors._source.verified_record(owner)
    if appended:offset,current_record,current_entry=controller_record(working,selectors._source.scene)
    else:offset,current_record,current_entry=source_offset,working[source_offset:source_offset+len(record)],entry
    if current_entry!=entry or len(current_record)!=len(record):raise BuildError('Controller three-word Build record extent changed')
    patched,changes=context.patch(entries,original=selectors._man)
    if not isinstance(patched,bytes) or len(patched)!=len(selectors._man):raise BuildError('Controller three-word serializer changed MAN length')
    occupied={i for c in previous for i in range(c['decoded_byte_offset'],c['decoded_byte_offset']+c.get('byte_length',1))}
    expected={};allowed=set()
    for key,values in entries.items():
        target=options[key];node=_instruction(record,target['pc']);relative=target['pc']+(2 if node['target_context'] is not None else 1)+1
        source_at=source_offset+relative;at=offset+relative;span=set(range(at,at+6))
        current_node=_instruction(current_record,target['pc'])
        if (type(at) is not int or not 0<=at<=len(working)-6 or span&(occupied|allowed) or
                current_record[target['pc']:relative]!=record[target['pc']:relative] or
                current_node['mnemonic']!=node['mnemonic'] or current_node['length']!=node['length'] or current_node['successors']!=node['successors'] or
                working[at:at+6]!=record[relative:relative+6]):
            raise BuildError('Controller three-word Build overlaps an authored span or changed source preimage')
        allowed.update(span);expected[key]=(target,relative,source_at,at,validate_three_word_values(values))
    seen=set();source_audited=set();output=bytearray(working);audit=[]
    for receipt in changes:
        key=receipt.get('three_word_id')
        if key not in expected or key in seen:raise BuildError('Controller three-word audit has missing or duplicate identity')
        target,relative,source_at,at,after=expected[key];before=record[relative:relative+6]
        if (any(type(receipt.get(field)) is not int for field in ('pc','decoded_byte_offset','record_relative_byte_offset','byte_length')) or
                receipt.get('owner_id')!=owner or receipt.get('pc')!=target['pc'] or receipt.get('mnemonic')!='FIELD_THREE_WORD_REQUEST' or
                receipt.get('sub_op')!=target['sub_op'] or type(receipt.get('sub_op')) is not int or
                receipt.get('target_context')!=target['target_context'] or type(receipt.get('target_context')) is not type(target['target_context']) or
                receipt.get('decoded_byte_offset')!=source_at or receipt.get('record_relative_byte_offset')!=relative or receipt.get('byte_length')!=6 or
                receipt.get('before_hex')!=before.hex() or receipt.get('after_hex')!=after.hex() or before==after or
                receipt.get('before_values')!=dict(signed_words=list(struct.unpack('<hhh',before))) or receipt.get('after_values')!=entries[key] or
                not _qualified_values(receipt.get('before_values')) or not _qualified_values(receipt.get('after_values')) or
                receipt.get('source_record_sha256')!=sha256(record).hexdigest() or receipt.get('source_decoded_man_sha256')!=sha256(selectors._man).hexdigest() or
                patched[source_at:source_at+6]!=after):raise BuildError('Controller three-word receipt differs from its source or requested bytes')
        seen.add(key);source_audited.update(range(source_at,source_at+6));output[at:at+6]=after
        checked=deepcopy(receipt);checked.update(decoded_byte_offset=at,semantic_id=owner,record_index=0,owner_kind='scene_controller',
            field='script.three_word_operands',scope='controller-three-word-operands-only',
            effective_record_sha256=sha256(current_record).hexdigest(),changed_bytes=[dict(decoded_byte_offset=at+i,before_byte=a,after_byte=b) for i,(a,b) in enumerate(zip(before,after)) if a!=b])
        if appended:checked.update(source_decoded_byte_offset=source_at,appended_man_sha256=sha256(working).hexdigest())
        audit.append(checked)
    for key,(_,relative,source_at,at,after) in expected.items():
        if patched[source_at:source_at+6]!=after or record[relative:relative+6]!=after and key not in seen:
            raise BuildError('Controller three-word request is missing from its complete audit')
    if any(a!=b and i not in source_audited for i,(a,b) in enumerate(zip(selectors._man,patched))):raise BuildError('Controller three-word serializer changed an unaudited MAN byte')
    result=bytes(output)
    if read_man_layout(working)!=read_man_layout(result):raise BuildError('Controller three-word Build changed MAN layout')
    for receipt in audit:receipt['candidate_record_sha256']=sha256(result[offset:offset+len(record)]).hexdigest()
    return result,audit
