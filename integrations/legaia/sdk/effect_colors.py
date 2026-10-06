"""Compose source-qualified fixed color operands without overlapping other edits."""
from hashlib import sha256
from importer.effect_color_authoring import validate_effect_color_values
from .build import BuildError

def merge_patch(baseline,working,patched,changes,expected,previous):
    if not isinstance(patched,bytes) or len(patched)!=len(baseline) or len(working)!=len(baseline):raise BuildError('Effect color patch changed MAN length')
    occupied={i for c in previous for i in range(c['decoded_byte_offset'],c['decoded_byte_offset']+c.get('byte_length',1))};audited=set();result=bytearray(working)
    for change in changes:
        target=expected.get(change.get('effect_color_id'));at=change.get('decoded_byte_offset')
        if (target is None or type(at) is not int or not 0<=at<=len(baseline)-5 or at!=target['decoded_byte_offset'] or
            change.get('byte_length')!=5 or change.get('field')!='color_intensity' or change.get('owner_id')!=target['owner_id'] or
            change.get('source_record_sha256')!=target['source_record_sha256'] or change.get('source_decoded_man_sha256')!=sha256(baseline).hexdigest() or
            change.get('pc')!=target['pc'] or change.get('mnemonic')!='EFFECT_COLOR_INTENSITY' or change.get('target_context')!=target['target_context'] or
            change.get('before_hex')!=baseline[at:at+5].hex() or change.get('after_hex')!=patched[at:at+5].hex() or
            change.get('before_values')!=target['values'] or change.get('after_values')!=target['requested_values'] or
            patched[at:at+5]!=validate_effect_color_values(target['requested_values'])):raise BuildError('Effect color audit differs from verified source or requested bytes')
        span=set(range(at,at+5))
        if span&(occupied|audited) or working[at:at+5]!=baseline[at:at+5]:raise BuildError('Effect color patch overlaps another authored MAN span')
        audited.update(span);result[at:at+5]=patched[at:at+5]
    if any(a!=b and i not in audited for i,(a,b) in enumerate(zip(baseline,patched))):raise BuildError('Effect color patch changed an unaudited MAN byte')
    return bytes(result)
