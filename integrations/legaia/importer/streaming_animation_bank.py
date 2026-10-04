"""Qualified raw type-5 ANM growth in terminated DATA_FIELD chunk chains.

Uses the existing streaming parser's Retail word traversal. No compression,
timing, pointer rewrite or runtime allocation is inferred by this transform.
"""
from hashlib import sha256
import struct

from .core import ImportError
from .streaming_man import streaming_chunks
from .animation_bank_growth import qualify_animation_bank
from .model_pack_archive import _archive
from .prot_layout import locate_physical_span
from .prot_rebuild import replace_physical_entry


def grow_streaming_animation_bank(source,expected_sha256,chunk_header_offset,expected_bank_sha256,bank):
    if not isinstance(source,bytes) or sha256(source).hexdigest()!=expected_sha256:
        raise ImportError('Streaming ANM carrier preimage changed')
    if type(chunk_header_offset) is not int or chunk_header_offset<0 or chunk_header_offset%4 or not isinstance(bank,bytes):
        raise ImportError('Streaming ANM requires a typed word-aligned chunk locator and immutable bank')
    chunks,terminated=streaming_chunks(source)
    if not terminated:raise ImportError('Streaming ANM growth requires a complete terminated chunk chain')
    target=next((row for row in chunks if row['header_offset']==chunk_header_offset),None)
    if target is None or target['type_byte']!=5:raise ImportError('Streaming ANM locator must target a type-5 chunk')
    old_size=target['size'];new_size=len(bank)
    if old_size%4 or new_size%4 or not 0<old_size<=new_size<=4*1024*1024:
        raise ImportError('Streaming ANM requires bounded word-aligned bank sizes without shrinkage')
    start,end=chunk_header_offset+4,chunk_header_offset+4+old_size
    original=source[start:end]
    if sha256(original).hexdigest()!=expected_bank_sha256:raise ImportError('Streaming ANM bank preimage changed')
    qualification=qualify_animation_bank(original,bank);growth=new_size-old_size
    if len(source)+growth>16*1024*1024:raise ImportError('Streaming ANM carrier growth exceeds its byte bound')
    candidate=source[:chunk_header_offset]+struct.pack('<I',(5<<24)|new_size)+bank+source[end:]
    expected=[dict(row,size=new_size) if row['header_offset']==chunk_header_offset else
        dict(row,header_offset=row['header_offset']+growth) if row['header_offset']>chunk_header_offset else dict(row)
        for row in chunks]
    if streaming_chunks(candidate)!=(expected,True) or candidate[:chunk_header_offset]!=source[:chunk_header_offset] or candidate[end+growth:]!=source[end:]:
        raise ImportError('Streaming ANM growth changed the qualified chunk chain or opaque neighbors')
    # Truncated word traversal can make a preceding odd-sized declared payload
    # overlap this header. Preserve its declared bytes too, or reject the edit.
    for before,after in zip(chunks,expected):
        if before['header_offset']==chunk_header_offset:continue
        a,b=before['header_offset'],after['header_offset'];length=4+before['size']
        if source[a:a+length]!=candidate[b:b+length]:
            raise ImportError('Streaming ANM growth changed an overlapping opaque neighbor payload')
    if candidate[start:start+new_size]!=bank:raise ImportError('Streaming ANM emitted bank failed readback')
    return candidate,dict(schema_version='legaia.streaming-animation-bank-growth.v1',
        source_sha256=expected_sha256,proposed_sha256=sha256(candidate).hexdigest(),chunk_header_offset=chunk_header_offset,
        payload_offset=start,source_payload_size=old_size,proposed_payload_size=new_size,growth_bytes=growth,
        bank_audit=qualification,relocated_chunks=[dict(before=row['header_offset'],after=row['header_offset']+growth,
            type_byte=row['type_byte'],byte_length=row['size']) for row in chunks if row['header_offset']>chunk_header_offset],
        opaque_neighbors_preserved=True,terminated_chain_verified=True,archive_relocation_verified=False,
        build_ready=False,gameplay_verified=False)


def rebuild_streaming_animation_bank_entry(source,expected_sha256,entry_index,chunk_header_offset,
                                          expected_bank_sha256,bank,*,header_offset=0):
    """Relocate the unique physical PROT owner and verify the reopened raw ANM."""
    if not isinstance(source,bytes) or sha256(source).hexdigest()!=expected_sha256 or len(source)%2048:
        raise ImportError('Streaming ANM archive preimage or sector alignment changed')
    if type(entry_index) is not int or type(header_offset) is not int or header_offset not in (0,2048):
        raise ImportError('Streaming ANM archive requires typed entry and header locators')
    archive=_archive(source)
    if archive.header_offset!=header_offset:raise ImportError('Streaming ANM archive header locator changed')
    entry=archive.entry(entry_index);span=locate_physical_span(archive,entry.start_lba*2048)
    if span['entry_index']!=entry_index or span['offset_within_span']!=0:
        raise ImportError('Streaming ANM requires a unique consecutive physical owner')
    start,length=span['byte_offset'],span['byte_length'];carrier=source[start:start+length]
    changed,report=grow_streaming_animation_bank(carrier,sha256(carrier).hexdigest(),chunk_header_offset,expected_bank_sha256,bank)
    padded=changed+bytes(-len(changed)%2048)
    result,audit=replace_physical_entry(source,expected_sha256,entry_index,padded,header_offset=header_offset)
    reopened=_archive(result);new_entry=reopened.entry(entry_index);physical=locate_physical_span(reopened,new_entry.start_lba*2048)
    raw=result[physical['byte_offset']:physical['byte_offset']+physical['byte_length']]
    if physical['entry_index']!=entry_index or raw!=padded or streaming_chunks(raw)!=streaming_chunks(changed) or [e.index for e in reopened.entries]!=[e.index for e in archive.entries]:
        raise ImportError('Streaming ANM archive relocation failed physical/chunk readback')
    report['archive_relocation_verified']=True
    return result,dict(entry_index=entry_index,carrier=report,archive=audit,
        reopened_bank_verified=True,physical_neighbors_preserved=True,disc_relocation_required=audit['disc_relocation_required'],
        build_ready=False,gameplay_verified=False)
