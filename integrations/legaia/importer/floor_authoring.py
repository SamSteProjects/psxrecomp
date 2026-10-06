"""Source MAP floor selectors, independently implemented from pinned field_objects.rs.

Only the low nibble at MAP +0x4000 changes. MAN LUT entries, wall bits,
object-grid flags and kind-2 ramp records remain source-owned.
"""
from hashlib import sha256
from .core import ImportError

def patch_floor_tiers(original: bytes, expected_sha256: str, edits: list[dict]):
    if not isinstance(original, bytes) or len(original) != 0x12000:
        raise ImportError('Floor authoring requires a complete supported MAP')
    if sha256(original).hexdigest() != expected_sha256:
        raise ImportError('Floor MAP source hash differs from the authored binding')
    if not isinstance(edits, list) or len(edits)>4096:
        raise ImportError('Floor authoring accepts at most 4096 selectors')
    seen=set()
    for edit in edits:
        if not isinstance(edit,dict) or set(edit)!={'row','column','tier'}:
            raise ImportError('Floor edits require row, column and tier only')
        if any(type(edit[key]) is not int or not 0<=edit[key]<=high for key,high in [('row',127),('column',127),('tier',15)]):
            raise ImportError('Floor row/column or tier is outside the evidenced grid')
        identity=(edit['row'],edit['column'])
        if identity in seen:raise ImportError('Duplicate floor selector')
        seen.add(identity)
    result=bytearray(original);audit=[]
    for edit in sorted(edits,key=lambda e:(e['row'],e['column'])):
        offset=0x4000+edit['row']*128+edit['column'];before=original[offset]&15
        if before==edit['tier']:continue
        result[offset]=(original[offset]&0xf0)|edit['tier']
        audit.append({**edit,'field':'floor.tier','byte_offset':offset,'bit_mask':15,
                      'before_value':before,'after_value':edit['tier'],'scope':'source-MAP-floor-selector-only'})
    allowed={row['byte_offset'] for row in audit}
    if any((a^b)&(0xf0 if i in allowed else 0xff) for i,(a,b) in enumerate(zip(original,result))):
        raise ImportError('Floor patch altered unaudited source bits')
    return bytes(result),audit
