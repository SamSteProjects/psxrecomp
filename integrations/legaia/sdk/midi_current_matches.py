"""Compare native content; equal bytes do not establish input-file usage."""
from copy import copy,deepcopy
from hashlib import sha256
from .audio_authoring import _current,_layout
from .project import ProjectError


def compare(project,receipts):
    if not isinstance(receipts,list) or not 1<=len(receipts)<=32:
        raise ProjectError('MIDI comparison requires bounded qualified receipts')
    cache={};rows=[]
    for r in receipts:
        key=(r['asset_id'],r['source_scene_id'],r['source_record']['entry_sha256'])
        if key not in cache:
            # Global audio composition does not depend on the editor's active
            # scene. Capture context requalifies the original retail ownership.
            view=copy(project);view.active_scene=r['source_scene_id']
            source,current,_,record,_=_current(view,r['asset_id'],r['source_record']['entry_sha256'])
            if record!=r['source_record']:raise ProjectError('Current MIDI target retail ownership changed')
            start,size=_layout(source,current,record)
            cache[key]=(sha256(current).hexdigest(),sha256(current[start:start+size]).hexdigest(),start,size)
        entry_hash,sequence_hash,start,size=cache[key]
        rows.append(dict(native_asset_id=r['asset_id'],receipt_key=r['receipt_key'],
            capture_scene_id=r['source_scene_id'],retail_entry_sha256=r['source_record']['entry_sha256'],
            retail_sequence_sha256=r['source_record']['sequence_sha256'],current_entry_sha256=entry_hash,
            current_sequence_sha256=sequence_hash,candidate_sequence_sha256=r['candidate_sequence_sha256'],
            current_sequence_offset=start,sequence_size_bytes=size,
            matches_candidate=sequence_hash==r['candidate_sequence_sha256'],input_usage='not_asserted'))
    return deepcopy(rows)
