"""Explicit authored MIDI source usage, separate from historical byte matches."""
from copy import copy,deepcopy
from hashlib import sha256
from .project import ProjectError,digest
from .audio_authoring import _current
from importer.audio_sequence_replacement import sequence_span


def current(project,snapshot,asset_id=None):
    rows=[]
    for midi_id,bindings in sorted(snapshot.get('replacement_bindings',{}).items()):
        if asset_id is not None and midi_id!=asset_id:continue
        for row in bindings:
            native,b=row['native_asset_id'],row['binding']
            if project.audio_sequence_replacements.get(native)!=b:raise ProjectError('MIDI replacement source binding changed')
            view=copy(project);view.active_scene=b['source_scene_id']
            _,body,_,record,_=_current(view,native,b['source_record']['entry_sha256'])
            at,size=sequence_span(body);h=sha256(body[at:at+size]).hexdigest()
            if record!=b['source_record'] or h!=b['candidate_sequence_sha256']:raise ProjectError('Current native MIDI replacement differs from its qualified recipe')
            rows.append(dict(native_asset_id=native,midi_asset_id=midi_id,binding_scene_id=b['source_scene_id'],binding_sha256=digest(b),binding=deepcopy(b),
                current_entry_sha256=sha256(body).hexdigest(),current_entry_size=len(body),current_sequence_sha256=h,current_sequence_offset=at,sequence_size_bytes=size,
                input_usage='current_authored_sequence_replacement',runtime_binding='not_asserted'))
    return deepcopy(rows)
