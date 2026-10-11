"""Compose fixed instruction writers against one immutable source record.

Writers retain responsibility for typed arguments and supported instruction
ownership. This layer checks their byte/audit contract and the combined graph.
It neither resolves animation identities nor evaluates visual effects.
"""
from hashlib import sha256
from .core import ImportError
from .script_inspection import inspect_record


def compose_script_operands(record, entry_pc, requests, *, base_offset=0):
    """Each request is (writer, pc, values); every writer sees Retail bytes.

    Audit spans, including unchanged bytes inside an edited operand, must be
    disjoint. Identical overlapping proposals are refused as ambiguous owners.
    """
    if not isinstance(record, bytes) or type(base_offset) is not int or base_offset < 0:
        raise ImportError('Script composition requires immutable source bytes and a nonnegative offset')
    if not isinstance(requests, (list, tuple)) or len(requests) > 1024:
        raise ImportError('Script composition requires at most 1024 fixed operand requests')
    result=bytearray(record); audit=[]; occupied=set(); source_hash=sha256(record).hexdigest()
    for writer,pc,values in requests:
        candidate,changes=writer(record,entry_pc,pc,values,base_offset=base_offset)
        if not isinstance(candidate,bytes) or len(candidate)!=len(record) or not isinstance(changes,list):
            raise ImportError('Script operand writer changed source extent or audit shape')
        witnessed=bytearray(record); local=set()
        for change in changes:
            relative=change.get('record_relative_byte_offset'); length=change.get('byte_length')
            if type(relative) is not int or type(length) is not int or length<=0 or relative<0 or relative+length>len(record):
                raise ImportError('Script operand audit exceeds its source record')
            if change.get('decoded_byte_offset')!=base_offset+relative or change.get('source_record_sha256')!=source_hash or change.get('pc')!=pc:
                raise ImportError('Script operand audit differs from its source ownership')
            span=set(range(relative,relative+length))
            if span & (occupied|local):raise ImportError('Script operand audit spans overlap')
            before=record[relative:relative+length]; after=candidate[relative:relative+length]
            if change.get('before_hex')!=before.hex() or change.get('after_hex')!=after.hex() or before==after:
                raise ImportError('Script operand audit differs from its exact byte patch')
            witnessed[relative:relative+length]=after; local.update(span)
        if bytes(witnessed)!=candidate:
            raise ImportError('Script operand writer changed bytes outside its audit')
        for relative in local:result[relative]=candidate[relative]
        occupied.update(local); audit.extend(changes)
    result=bytes(result)
    if audit:
        before=inspect_record(record,entry_pc); after=inspect_record(result,entry_pc)
        shape=lambda graph:[(n['pc'],n['mnemonic'],n['length'],n['target_context'],n['successors']) for n in graph['instructions']]
        if before['stops'] or after['stops'] or shape(before)!=shape(after):
            raise ImportError('Composed script operands changed source control flow')
    return result,sorted(audit,key=lambda change:change['decoded_byte_offset'])
