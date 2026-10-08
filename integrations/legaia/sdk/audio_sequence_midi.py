"""Read-only MIDI upload review against fresh native Current source bytes."""
import base64
from copy import deepcopy
from hashlib import sha256

from importer.audio_sequence_midi import MAX_MIDI_BYTES, midi_operand_edits
from .audio_authoring import _current, _layout, review as review_operands, source_key
from .project import ProjectError


def decode_upload(value):
    if not isinstance(value, str) or len(value) > ((MAX_MIDI_BYTES+2)//3)*4:
        raise ProjectError('MIDI upload exceeds its byte budget')
    try:
        raw = base64.b64decode(value, validate=True)
    except (ValueError, TypeError) as exc:
        raise ProjectError('MIDI upload requires strict base64') from exc
    if not 26 <= len(raw) <= MAX_MIDI_BYTES:
        raise ProjectError('MIDI upload exceeds its complete-track extent')
    return raw


def review(project, asset_id, expected_entry_sha256, expected_authoring_key, midi_base64):
    if project.mode != 'edit' or expected_authoring_key != source_key(project):
        raise ProjectError('MIDI source context changed or is not in Edit mode')
    raw = decode_upload(midi_base64)
    body, current, _, record, _ = _current(project, asset_id, expected_entry_sha256)
    start, size = _layout(body, current, record)
    edits = midi_operand_edits(raw, current[start:start+size])
    native = review_operands(project, asset_id, expected_entry_sha256,
                            expected_authoring_key, edits) if edits else None
    if source_key(project) != expected_authoring_key:
        raise ProjectError('MIDI source context changed during native review')
    return deepcopy(dict(schema_version='legaia.audio-sequence-midi-review.v1',
        asset_id=asset_id, authoring_key=expected_authoring_key,
        source_record=record, current_entry_sha256=sha256(current).hexdigest(),
        midi_sha256=sha256(raw).hexdigest(), byte_length=len(raw), edits=edits,
        native_review=native, input_retained=False, project_changed=False,
        runtime_state='not_observed'))
