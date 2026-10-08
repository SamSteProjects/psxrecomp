"""Read-only full MIDI sequence candidate review before writable integration."""
from copy import deepcopy
from hashlib import sha256
from .audio_authoring import _current,source_key
from .audio_sequence_midi import decode_upload
from .project import ProjectError
from importer.audio_sequence_replacement import replace_midi


def review(project,asset_id,expected_entry_sha256,expected_authoring_key,midi_base64):
    if project.mode!='edit' or source_key(project)!=expected_authoring_key:
        raise ProjectError('Replacement review requires fresh Edit mode sources')
    raw=decode_upload(midi_base64)
    _,current,_,record,_=_current(project,asset_id,expected_entry_sha256)
    candidate,sequence,audit=replace_midi(current,raw,expected_current_sha256=sha256(current).hexdigest())
    _,fresh,_,fresh_record,_=_current(project,asset_id,expected_entry_sha256)
    if fresh!=current or fresh_record!=record:raise ProjectError('Replacement native sources changed during review')
    if source_key(project)!=expected_authoring_key:raise ProjectError('Replacement sources changed during review')
    return deepcopy(dict(schema_version='legaia.sequence-replacement-review.v1',asset_id=asset_id,authoring_key=expected_authoring_key,
        source_record=record,midi_sha256=sha256(raw).hexdigest(),byte_length=len(raw),audit=audit,sequence=sequence,
        input_retained=False,project_changed=False,runtime_state='not_observed',writable=False))
