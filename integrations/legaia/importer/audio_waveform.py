"""Bounded source SPU-ADPCM waveform inspection, without pitch or playback."""
from hashlib import sha256
from .core import ImportError
from .audio_bank import bank_from_entry, read_audio_bank, MAX_ENTRY_BYTES
from .pipeline import _disc_context

MAX_BLOCKS = 4096
MAX_BINS = 512
COEFFICIENTS = ((0, 0), (60, 0), (115, -52), (98, -55), (122, -60))


def inspect_waveform(body):
    if not isinstance(body, bytes) or len(body) > MAX_ENTRY_BYTES:
        raise ImportError('Waveform requires bounded immutable sample bytes')
    pcm = []; markers = []; previous = older = 0; stopped = None; consumed = 0
    for offset in range(0, min(len(body), MAX_BLOCKS * 16), 16):
        block = body[offset:offset + 16]
        if len(block) != 16:
            stopped = dict(reason='incomplete-block', byte_offset=offset); break
        header, flags = block[:2]; predictor = header >> 4; shift = header & 15
        if predictor > 4 or flags & ~7:
            stopped = dict(reason='unknown-predictor' if predictor > 4 else 'unknown-flag-bits', byte_offset=offset); break
        effective_shift = shift if shift <= 12 else 9
        if flags or shift > 12:
            markers.append(dict(block_index=offset // 16, frame_offset=len(pcm), flags=flags,
                                encoded_shift=shift, effective_shift=effective_shift))
        first, second = COEFFICIENTS[predictor]
        for byte in block[2:]:
            for nibble in (byte & 15, byte >> 4):
                signed = nibble if nibble < 8 else nibble - 16
                value = (signed << (12 - effective_shift)) + ((previous * first + older * second + 32) >> 6)
                value = max(-32768, min(32767, value)); pcm.append(value); older, previous = previous, value
        consumed = offset + 16
        if flags & 1:
            stopped = dict(reason='encoded-end', byte_offset=offset); break
    if stopped is None:
        stopped = dict(reason='preview-budget' if len(body) > consumed else 'source-span-exhausted', byte_offset=consumed)
    width = max(1, (len(pcm) + MAX_BINS - 1) // MAX_BINS)
    bins = [dict(frame_offset=i, frame_count=len(pcm[i:i + width]), minimum=min(pcm[i:i + width]), maximum=max(pcm[i:i + width]))
            for i in range(0, len(pcm), width)]
    return dict(decoder='psx-spu-adpcm-integer-v1', history='zero-initialized', source_size_bytes=len(body),
                source_sha256=sha256(body).hexdigest(), decoded_blocks=consumed // 16, decoded_frames=len(pcm),
                consumed_bytes=consumed, remaining_bytes=len(body) - consumed, termination=stopped,
                markers=markers, bins=bins, frame_limit=MAX_BLOCKS * 28, sample_rate=None,
                limitations=['Frames use zero initial predictor history and stop at the first encoded end; loops are not replayed.',
                             'Reserved shift values 13–15 use effective shift 9, following pinned SPU decoder evidence.',
                             'No sample rate, pitch, audible duration, instrument assignment or runtime playback is inferred.'])


def read_audio_waveform(disc, asset_id, expected_entry_sha256, expected_bank_sha256, sample_index, expected_sample_sha256):
    if type(sample_index) is not int or not 0 <= sample_index <= 254:
        raise ImportError('Choose a bounded source sample index')
    report = read_audio_bank(disc, asset_id, expected_entry_sha256)
    if report['bank_sha256'] != expected_bank_sha256 or sample_index >= len(report['samples']):
        raise ImportError('Waveform bank or sample identity changed')
    sample = report['samples'][sample_index]
    if sample['source_sha256'] != expected_sample_sha256:
        raise ImportError('Waveform sample differs from its reviewed hash')
    with _disc_context(disc) as (image, disc_hash, mapping, archive):
        source = report['source_record']; body = image.read_user(archive.node.extent_lba, source['entry_byte_offset'], source['entry_size_bytes'], archive.node.size)
        if sha256(body).hexdigest() != expected_entry_sha256:
            raise ImportError('Waveform carrier changed during inspection')
        bank, pieces, carrier = bank_from_entry(body)
        if sha256(bank).hexdigest() != expected_bank_sha256:
            raise ImportError('Waveform bank changed during inspection')
        raw = bank[sample['offset']:sample['offset'] + sample['size_bytes']]
        if sha256(raw).hexdigest() != expected_sample_sha256:
            raise ImportError('Waveform sample changed during inspection')
    return dict(source_record=report['source_record'], reference_commit=report['reference_commit'],
                bank_sha256=expected_bank_sha256, sample=sample, **inspect_waveform(raw))
