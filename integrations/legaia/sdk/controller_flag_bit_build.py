"""Independent source-bound one-byte receipts for controller flag-bit Build delivery."""
from copy import deepcopy
from hashlib import sha256
from importer.controller_flag_bits import ControllerFlagBitAuthoringContext
from importer.flag_authoring import _target,validate_flag_values
from importer.scene_controller import controller_record
from importer.man_layout import read_man_layout


def compose_flag_bits(selectors,owner,components,working,previous=(),*,appended=False):
    from .build import BuildError
    context=ControllerFlagBitAuthoringContext(selectors._source)
    entries=components['ControllerFlagBits']['entries']
    options={t['semantic_id']:t for t in context.options(owner)['targets']}
    if set(entries)-set(options):raise BuildError('Controller flag-bit Build target is not qualified by Retail source')
    source_offset,record,entry=selectors._source.verified_record(owner)
    if appended:offset,current_record,current_entry=controller_record(working,selectors._source.scene)
    else:offset,current_record,current_entry=source_offset,working[source_offset:source_offset+len(record)],entry
    if current_entry!=entry or len(current_record)!=len(record):raise BuildError('Controller flag-bit Build record extent changed')
    patched,changes=context.patch(entries,original=selectors._man)
    if not isinstance(patched,bytes) or len(patched)!=len(selectors._man):raise BuildError('Controller flag-bit serializer changed MAN extent')
    occupied={i for c in previous for i in range(c['decoded_byte_offset'],c['decoded_byte_offset']+c.get('byte_length',1))}
    expected={};allowed=set()
    for identity,values in entries.items():
        target=options[identity];bit=validate_flag_values(values)
        node,relative,_=_target(record,entry,target['pc'],bit)
        source_at=source_offset+relative;at=offset+relative
        # Check the current instruction directly; branch edits may alter reachability.
        from importer.script_inspection import _instruction
        current_node=_instruction(current_record,target['pc'])
        if (not 0<=at<len(working) or at in occupied|allowed or
            current_record[target['pc']:relative]!=record[target['pc']:relative] or
            current_node['mnemonic']!=node['mnemonic'] or current_node['length']!=node['length'] or
            current_node['successors']!=node['successors'] or working[at]!=record[relative]):
            raise BuildError('Controller flag-bit Build overlaps an authored span or changed source preimage')
        allowed.add(at);expected[identity]=(target,relative,source_at,at,(record[relative]&224)|bit)
    seen=set();source_audited=set();output=bytearray(working);audit=[]
    for receipt in changes:
        identity=receipt.get('flag_id')
        if identity not in expected or identity in seen:raise BuildError('Controller flag-bit audit has missing or duplicate identity')
        target,relative,source_at,at,after=expected[identity];before=record[relative]
        exact=dict(field='bit',pc=target['pc'],mnemonic=target['mnemonic'],target_context=target['target_context'],
            record_relative_byte_offset=relative,decoded_byte_offset=source_at,before_byte=before,after_byte=after,
            before_bit=before&31,after_bit=entries[identity]['bit'],source_record_sha256=sha256(record).hexdigest(),
            flag_id=identity,owner_id=owner,source_decoded_man_sha256=sha256(selectors._man).hexdigest(),bit_mask=31,preserved_bits=before&224)
        if (receipt!=exact or any(type(receipt[k]) is not type(v) for k,v in exact.items()) or before==after or patched[source_at]!=after):
            raise BuildError('Controller flag-bit receipt differs from its source or requested bytes')
        seen.add(identity);source_audited.add(source_at);output[at]=after
        checked=deepcopy(receipt);checked.update(decoded_byte_offset=at,byte_length=1,semantic_id=owner,record_index=0,owner_kind='scene_controller',
            field='script.flag_bit',scope='controller-flag-bit-only',before_hex=bytes([before]).hex(),after_hex=bytes([after]).hex(),
            before_values=dict(bit=before&31),after_values=deepcopy(entries[identity]),effective_record_sha256=sha256(current_record).hexdigest(),
            changed_bytes=[dict(decoded_byte_offset=at,before_byte=before,after_byte=after)])
        if appended:checked.update(source_decoded_byte_offset=source_at,appended_man_sha256=sha256(working).hexdigest())
        audit.append(checked)
    for identity,(_,relative,source_at,at,after) in expected.items():
        if patched[source_at]!=after or record[relative]!=after and identity not in seen:
            raise BuildError('Controller flag-bit request is missing from its complete audit')
    if any(a!=b and i not in source_audited for i,(a,b) in enumerate(zip(selectors._man,patched))):raise BuildError('Controller flag-bit serializer changed an unaudited MAN byte')
    result=bytes(output)
    if read_man_layout(working)!=read_man_layout(result):raise BuildError('Controller flag-bit Build changed MAN layout')
    for receipt in audit:receipt['candidate_record_sha256']=sha256(result[offset:offset+len(record)]).hexdigest()
    return result,audit
