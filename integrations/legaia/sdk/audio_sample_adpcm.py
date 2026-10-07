"""Private, source-qualified native ADPCM bytes for bounded editor audition."""
from hashlib import sha256
import base64
from .project import ProjectError
from .audio_authoring import source_key
from .audio_sample_authoring import _current
from importer.audio_waveform import inspect_waveform


def preview(project,asset_id,expected_entry_sha256,sample_index,expected_authoring_key,layer,expected_sample_sha256):
    if layer not in ('retail','current') or expected_authoring_key!=source_key(project):
        raise ProjectError('Native ADPCM preview requires a fresh Retail or Current sample layer')
    _,current,_,record,row,position,raw,_=_current(project,asset_id,expected_entry_sha256,sample_index)
    selected=raw if layer=='retail' else current[position:position+row['size_bytes']]
    if not 16<=len(selected)<=65536 or sha256(selected).hexdigest()!=expected_sample_sha256:
        raise ProjectError('Native ADPCM sample extent or selected layer hash changed')
    wave=inspect_waveform(selected)
    starts=[m for m in wave['markers'] if m['flags']&4]
    if (wave['termination']['reason']!='encoded-end' or (wave['markers'][-1]['flags']&2 and not starts)
            or any(m['encoded_shift']>12 for m in wave['markers'])):
        raise ProjectError('Native ADPCM audition requires a complete standard-shift sample; repeats require an explicit loop start')
    if expected_authoring_key!=source_key(project):
        raise ProjectError('Native ADPCM inputs changed during source qualification')
    return dict(schema_version='legaia.audio-sample-adpcm.v1',asset_id=asset_id,sample_index=sample_index,
        authoring_key=expected_authoring_key,layer=layer,source_record=record,
        current_entry_sha256=sha256(current).hexdigest(),sample_sha256=expected_sample_sha256,waveform=wave,
        format='psx-spu-adpcm-blocks',adpcm_base64=base64.b64encode(selected).decode('ascii'),
        project_changed=False,runtime_state='not_observed')
