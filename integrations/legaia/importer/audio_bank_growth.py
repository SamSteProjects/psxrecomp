"""Whole physical audio owner allocation; no source disc or runtime mutation."""
from hashlib import sha256
from .core import ImportError
from .audio_bank import bank_from_entry,inspect_bank,MAX_ENTRY_BYTES
from .model_pack_archive import _archive
from .prot_layout import locate_physical_span
from .prot_rebuild import replace_physical_entry

def rebuild_audio_bank_entry(source,expected_sha256,entry_index,expected_entry_sha256,candidate,*,header_offset=0):
    if (not isinstance(source,bytes) or not 0<len(source)<=256*1024*1024
            or sha256(source).hexdigest()!=expected_sha256 or type(entry_index) is not int
            or not isinstance(candidate,bytes) or not 32<=len(candidate)<=MAX_ENTRY_BYTES):
        raise ImportError('Audio archive allocation requires bounded hashed immutable inputs')
    archive=_archive(source)
    if archive.header_offset!=header_offset:raise ImportError('Audio archive header locator changed')
    entry=archive.entry(entry_index);span=locate_physical_span(archive,entry.start_lba*2048)
    if span['entry_index']!=entry_index or span['offset_within_span']!=0:
        raise ImportError('Audio allocation requires a unique consecutive physical owner')
    original=source[span['byte_offset']:span['byte_offset']+span['byte_length']]
    if len(original)>MAX_ENTRY_BYTES or sha256(original).hexdigest()!=expected_entry_sha256:
        raise ImportError('Audio physical source extent or hash changed')
    bank,_,kind=bank_from_entry(original);rebuilt,_,new_kind=bank_from_entry(candidate)
    before=inspect_bank(bank);after=inspect_bank(rebuilt)
    if (kind!=new_kind or before['sections']!=after['sections']
            or before['header']['sample_count']!=after['header']['sample_count']):
        raise ImportError('Audio allocation changed native carrier, fixed tables or sample ordinals')
    # Sample/carrier shrinking keeps the old physical allocation. Growth adds
    # whole sectors; every byte of the caller-qualified carrier is retained.
    padded=candidate+bytes(max(len(original),len(candidate)+(-len(candidate)%2048))-len(candidate))
    output,audit=replace_physical_entry(source,expected_sha256,entry_index,padded,header_offset=header_offset)
    reopened=_archive(output);target=reopened.entry(entry_index)
    new_span=locate_physical_span(reopened,target.start_lba*2048)
    raw=output[new_span['byte_offset']:new_span['byte_offset']+new_span['byte_length']]
    if raw!=padded or bank_from_entry(raw)[0]!=rebuilt:
        raise ImportError('Audio archive allocation failed whole physical owner/bank readback')
    return output,dict(kind='audio-sample-bank',entry_index=entry_index,archive=audit,
        source_entry_sha256=expected_entry_sha256,candidate_entry_sha256=sha256(candidate).hexdigest(),
        candidate_size_bytes=len(candidate),source_physical_size_bytes=len(original),
        proposed_physical_size_bytes=len(padded),padding_bytes=len(padded)-len(candidate),
        bank_sha256=sha256(rebuilt).hexdigest(),reopened_audio_bank_verified=True,
        build_ready=False,gameplay_verified=False)


def rebuild_audio_sequence_entry(source,expected_sha256,entry_index,expected_entry_sha256,candidate,*,header_offset=0):
    if (not isinstance(source,bytes) or not 0<len(source)<=256*1024*1024
            or sha256(source).hexdigest()!=expected_sha256 or type(entry_index) is not int
            or not isinstance(candidate,bytes) or not 13<=len(candidate)<=MAX_ENTRY_BYTES):
        raise ImportError('Audio archive allocation requires bounded hashed immutable inputs')
    archive=_archive(source)
    if archive.header_offset!=header_offset:raise ImportError('Audio archive header locator changed')
    entry=archive.entry(entry_index);span=locate_physical_span(archive,entry.start_lba*2048)
    if span['entry_index']!=entry_index or span['offset_within_span']!=0:
        raise ImportError('Audio allocation requires a unique consecutive physical owner')
    original=source[span['byte_offset']:span['byte_offset']+span['byte_length']]
    if len(original)>MAX_ENTRY_BYTES or sha256(original).hexdigest()!=expected_entry_sha256:
        raise ImportError('Audio physical source extent or hash changed')
    from .audio_catalog import decode_audio_entry
    from .audio_sequence import inspect_sequence
    from .audio_sequence_replacement import sequence_span
    before=decode_audio_entry(original);after=decode_audio_entry(candidate)
    if before['format']!=after['format'] or before['sequence'] is None or after['sequence'] is None or before['sequence']['header_variant']!=after['sequence']['header_variant']:
        raise ImportError('Sequence allocation changed native carrier/header ownership')
    at,size=sequence_span(candidate)
    if not inspect_sequence(candidate[at:at+size])['complete']:raise ImportError('Sequence allocation candidate is incomplete')
    if before['bank'] is not None:
        bank=bank_from_entry(original)[0];rebuilt=bank_from_entry(candidate)[0]
        prior=inspect_bank(bank);now=inspect_bank(rebuilt)
        if prior['sections']!=now['sections'] or prior['header']['sample_count']!=now['header']['sample_count']:
            raise ImportError('Sequence allocation changed fixed bank tables/sample ordinals')
    # Sample/carrier shrinking keeps the old physical allocation. Growth adds
    # whole sectors; every byte of the caller-qualified carrier is retained.
    padded=candidate+bytes(max(len(original),len(candidate)+(-len(candidate)%2048))-len(candidate))
    output,audit=replace_physical_entry(source,expected_sha256,entry_index,padded,header_offset=header_offset)
    reopened=_archive(output);target=reopened.entry(entry_index)
    new_span=locate_physical_span(reopened,target.start_lba*2048)
    raw=output[new_span['byte_offset']:new_span['byte_offset']+new_span['byte_length']]
    if raw!=padded or decode_audio_entry(raw)['format']!=after['format']:
        raise ImportError('Audio archive allocation failed whole physical owner/bank readback')
    return output,dict(kind='audio-sequence',entry_index=entry_index,archive=audit,
        source_entry_sha256=expected_entry_sha256,candidate_entry_sha256=sha256(candidate).hexdigest(),
        candidate_size_bytes=len(candidate),source_physical_size_bytes=len(original),
        proposed_physical_size_bytes=len(padded),padding_bytes=len(padded)-len(candidate),
        sequence_sha256=sha256(candidate[at:at+size]).hexdigest(),reopened_audio_sequence_verified=True,
        build_ready=False,gameplay_verified=False)
