"""Equal-layout kingdom type-5 ANM channel edits; no timing/selector inference."""
from hashlib import sha256
from copy import deepcopy
from .animation import animation_record_ranges
from .animation_authoring import patch_animation_channels
from .core import ImportError


def patch_world_animation_bank(bank,expected_sha256,record_index,record_sha256,edits):
    if not isinstance(bank,bytes) or sha256(bank).hexdigest()!=expected_sha256:
        raise ImportError('World animation bank differs from its immutable source hash')
    ranges=animation_record_ranges(bank)
    if type(record_index) is not int or not 0<=record_index<len(ranges):
        raise ImportError('World animation record index exceeds its native bank')
    start,end=ranges[record_index];record=bank[start:end]
    replacement,channels=patch_animation_channels(record,record_sha256,edits)
    if (replacement[:8]!=record[:8] or replacement[-8:]!=record[-8:]
            or any((replacement[i]&0xf0)!=(record[i]&0xf0) for i in range(12,len(record)-8,8))):
        raise ImportError('World animation edit changed opaque header, trailer or channel bits')
    proposed=bank[:start]+replacement+bank[end:]
    # Equal-layout edits cannot move any table entry or opaque neighbor record.
    if (len(proposed)!=len(bank) or animation_record_ranges(proposed)!=ranges
            or proposed[:start]!=bank[:start] or proposed[end:]!=bank[end:]):
        raise ImportError('World animation edit changed bank layout or neighboring records')
    changed=[dict(byte_offset=i,before_byte=a,after_byte=b) for i,(a,b) in enumerate(zip(bank,proposed)) if a!=b]
    allowed={start+r['channel_byte_offset']+n for r in channels for n in range(8)}
    if any(r['byte_offset'] not in allowed for r in changed):
        raise ImportError('World animation edit changed bytes outside reviewed channels')
    return proposed,dict(scope='world-animation-channel-content-only',record_index=record_index,
        byte_offset=start,byte_length=end-start,source_bank_sha256=expected_sha256,
        proposed_bank_sha256=sha256(proposed).hexdigest(),source_record_sha256=record_sha256,
        proposed_record_sha256=sha256(replacement).hexdigest(),channels=deepcopy(channels),
        changed_bytes=changed,gameplay_verified=False)
