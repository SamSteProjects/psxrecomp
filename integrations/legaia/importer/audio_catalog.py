"""Bounded source audio discovery; no playback or scene-use inference.

Format evidence: pinned Andrew reference sound_pack.rs, vab/src/lib.rs and
seq/src/lib.rs. Only leading signatures are recognized; no interior magic scan.
"""
from hashlib import sha256
import struct
from .core import ImportError, validate_metadata_only
from .pipeline import REFERENCE_COMMIT, _disc_context

MAX_ENTRY_BYTES = 4 * 1024 * 1024
MAX_TOTAL_BYTES = 32 * 1024 * 1024
LIMITATIONS = [
    'Leading VAB/SEQ signatures and supported three-chunk sound packs only; other audio containers, XA and interior resources are outside this catalog.',
    'Global source inventory is visible from each imported scene; catalog membership does not establish a scene playback assignment.',
    'Headers and container bounds are decoded; sequence events, waveform tables, sample playback, duration and runtime residency are not validated.',
    'Audio authoring and native audio replacement are not supported by this catalog.',
]


def _bank(body):
    if len(body) < 32 or body[:4] != b'pBAV':
        raise ImportError('VAB header is truncated or has an invalid signature')
    version, bank_id, size = struct.unpack_from('<III', body, 4)
    programs, tones, samples = struct.unpack_from('<HHH', body, 18)
    if version > 10 or not 1 <= programs <= 128 or tones > 2048 or not 1 <= samples <= 255 or not 32 <= size <= MAX_ENTRY_BYTES:
        raise ImportError('VAB declared header fields exceed supported bounds')
    return dict(version=version, bank_id=bank_id, declared_size=size,
                program_count=programs, tone_count=tones, sample_count=samples)


def _sequence(body):
    if len(body) < 13 or body[:4] != b'pQES':
        raise ImportError('SEQ header is truncated or has an invalid signature')
    legaia = int.from_bytes(body[4:8], 'big') == 1
    offset = 8 if legaia else 6
    header_size = 15 if legaia else 13
    if len(body) < header_size:
        raise ImportError('SEQ header variant is truncated')
    version = 1 if legaia else int.from_bytes(body[4:6], 'big')
    ppqn = int.from_bytes(body[offset:offset+2], 'big')
    tempo = int.from_bytes(body[offset+2:offset+5], 'big')
    numerator, denominator = body[offset+5:offset+7]
    if version != 1 or ppqn == 0 or tempo == 0 or numerator == 0 or denominator > 7:
        raise ImportError('SEQ declared timing header exceeds supported bounds')
    return dict(header_variant='legaia-u32-version' if legaia else 'psyq-u16-version',
                header_size=header_size, version=version, ppqn=ppqn,
                initial_tempo_us_per_quarter=tempo, time_signature_numerator=numerator,
                time_signature_denominator_power=denominator, event_stream_validated=False)


def decode_audio_entry(body):
    """Decode supported leading structures, preserving partial header-only status."""
    if not isinstance(body, bytes) or not 4 <= len(body) <= MAX_ENTRY_BYTES:
        raise ImportError('Audio entry exceeds supported immutable input bounds')
    if body[:4] == b'pBAV':
        bank = _bank(body)
        return dict(format='VAB', bank=bank, sequence=None, chunks=[],
                    declared_bank_complete=bank['declared_size'] <= len(body))
    if body[:4] == b'pQES':
        return dict(format='SEQ', bank=None, sequence=_sequence(body), chunks=[], declared_bank_complete=None)
    if len(body) < 8 or body[3] != 0 or body[4:8] != b'pBAV':
        raise ImportError('No supported leading audio signature')
    chunks, offset = [], 0
    for expected in (0, 1, 2):
        if offset + 4 > len(body):
            raise ImportError('Sound pack chunk header is truncated')
        word = struct.unpack_from('<I', body, offset)[0]
        kind, size = word >> 24, word & 0xffffff
        # Retail walker advances by floor(size/4) words. Do not reinterpret an
        # unaligned declaration as rounded-up storage or borrow a neighbor.
        if kind != expected or size == 0 or size % 4 or offset + 4 + size > len(body):
            raise ImportError('Sound pack requires bounded aligned header/sample/SEQ chunks')
        chunks.append(dict(kind=kind, header_offset=offset, payload_offset=offset+4,
                           size_bytes=size, sha256=sha256(body[offset+4:offset+4+size]).hexdigest()))
        offset += 4 + size
    header, samples, seq = chunks
    bank = _bank(body[header['payload_offset']:header['payload_offset']+header['size_bytes']])
    sequence = _sequence(body[seq['payload_offset']:seq['payload_offset']+seq['size_bytes']])
    return dict(format='VAB+SEQ sound pack', bank=bank, sequence=sequence, chunks=chunks,
                declared_bank_complete=bank['declared_size'] == header['size_bytes']+samples['size_bytes'])


def load_audio_asset_catalog(disc, scene):
    if not isinstance(scene, str) or not scene or len(scene) > 128 or any(not (c.isascii() and (c.isalnum() or c in '_-')) for c in scene):
        raise ImportError('Audio catalog requires a structural scene name')
    records, unavailable, total, partial = [], [], 0, 0
    with _disc_context(disc) as (image, disc_hash, mapping, archive):
        if len(archive.entries) > 4096:
            raise ImportError('Audio archive entry count exceeds the discovery budget')
        for entry in archive.entries:
            index = entry.index
            start, end = archive.toc[index+2:index+4]
            size, offset = (end-start)*2048, start*2048
            if not 0 < size or offset + size > archive.node.size:
                raise ImportError('Audio discovery requires a bounded physical PROT entry')
            lead = image.read_user(archive.node.extent_lba, offset, min(8,size), archive.node.size)
            if not (lead[:4] in (b'pBAV',b'pQES') or len(lead)==8 and lead[3]==0 and lead[4:8]==b'pBAV'):
                continue
            if size > MAX_ENTRY_BYTES or total + size > MAX_TOTAL_BYTES:
                raise ImportError('Recognized audio entries exceed the bounded read budget')
            total += size
            body = image.read_user(archive.node.extent_lba, offset, size, archive.node.size)
            try:
                decoded = decode_audio_entry(body)
                decoded.update(container_validated=True, structural_limitations=[])
            except ImportError as exc:
                # A qualified leading VAB header remains evidence even when
                # the rest of the container is unsupported. Do not invent a
                # sequence or mark the waveform bank complete in that case.
                try:
                    header_size = struct.unpack_from('<I', body)[0] & 0xffffff
                    bank = (_bank(body[4:4+header_size]) if body[3] == 0 and body[4:8] == b'pBAV'
                            and 32 <= header_size <= len(body)-4 else None)
                except ImportError:
                    bank = None
                if bank is None:
                    unavailable.append(dict(prot_entry_index=index, reason=str(exc)))
                    continue
                decoded = dict(format='VAB header in unresolved container', bank=bank,
                               sequence=None, chunks=[], declared_bank_complete=None,
                               container_validated=False, structural_limitations=[str(exc)])
                partial += 1
            from .audio_bank import bank_from_entry, inspect_bank
            try:
                bank_bytes, bank_pieces, bank_carrier = bank_from_entry(body)
                bank_report = inspect_bank(bank_bytes)
                bank_inspection = dict(status='available', reason=None, bank_sha256=bank_report['bank_sha256'],
                    carrier=bank_carrier, tone_page_count=bank_report['header']['program_count'],
                    sample_count=len(bank_report['samples']))
            except ImportError as exc:
                bank_inspection = dict(status='unavailable', reason=str(exc))
            records.append(dict(semantic_id=f'audio://legaia/prot/{index:04d}', asset_kind='audio', kind='audio',
                name=f"{decoded['format']} PROT {index:04d}", scope='global-source-audio',
                source_record=dict(disc=dict(sha256=disc_hash,serial='SCUS-94254'),iso_file='PROT.DAT',
                    prot_entry_index=index,prot_entry_name=mapping.get(index),byte_offset=offset,size_bytes=size,
                    sha256=sha256(body).hexdigest(),boundary='physical-next-TOC-entry'),
                reference_commit=REFERENCE_COMMIT, confidence='partial', status='partial',
                playback_assignment='unknown', preview_supported=False, bank_inspection=bank_inspection, **decoded, limitations=list(LIMITATIONS)))
        result=dict(schema_version='legaia.audio-asset-catalog.v1', scene=scene,
                    reference_commit=REFERENCE_COMMIT, assets=records, asset_count=len(records),
                    unavailable_entries=unavailable, scanned_entry_count=len(archive.entries),
                    recognized_entry_count=len(records)+len(unavailable), partial_container_count=partial, read_bytes=total,
                    metadata_only=True, runtime_state='not_observed', limitations=list(LIMITATIONS))
        result['limitations'].append(f'{partial} records have qualified headers in unresolved containers; per-record structural_limitations retain the reason.')
        if unavailable:
            result['limitations'].append(f'{len(unavailable)} leading-signature entries have unavailable headers; unavailable_entries retains their source indices and reasons.')
        validate_metadata_only(result)
        return result


def read_audio_sequence(disc, asset_id, expected_entry_sha256):
    """Re-read one physical entry and qualify its complete supported SEQ carrier."""
    import re
    if not isinstance(asset_id,str) or re.fullmatch(r'audio://legaia/prot/[0-9]{4}',asset_id) is None:
        raise ImportError('Choose a structural source audio identity')
    if not isinstance(expected_entry_sha256,str) or re.fullmatch(r'[0-9a-f]{64}',expected_entry_sha256) is None:
        raise ImportError('Audio inspection requires its reviewed entry hash')
    index=int(asset_id.rsplit('/',1)[1])
    with _disc_context(disc) as (image,disc_hash,mapping,archive):
        archive.entry(index)
        start,end=archive.toc[index+2:index+4];offset=start*2048;size=(end-start)*2048
        if not 0<size<=MAX_ENTRY_BYTES or offset+size>archive.node.size:
            raise ImportError('Audio sequence carrier exceeds physical entry bounds')
        body=image.read_user(archive.node.extent_lba,offset,size,archive.node.size)
        if sha256(body).hexdigest()!=expected_entry_sha256:
            raise ImportError('Audio entry differs from its reviewed source hash')
        decoded=decode_audio_entry(body)
        if decoded['sequence'] is None:raise ImportError('This audio resource has no supported sequence carrier')
        if decoded['format']=='SEQ':sequence_offset=0;sequence_size=len(body)
        else:chunk=decoded['chunks'][2];sequence_offset=chunk['payload_offset'];sequence_size=chunk['size_bytes']
        sequence=body[sequence_offset:sequence_offset+sequence_size]
        return sequence,dict(disc_sha256=disc_hash,iso_file='PROT.DAT',prot_entry_index=index,
                    entry_sha256=expected_entry_sha256,entry_byte_offset=offset,entry_size_bytes=size,
                    sequence_offset=sequence_offset,sequence_size_bytes=sequence_size,sequence_sha256=sha256(sequence).hexdigest())
