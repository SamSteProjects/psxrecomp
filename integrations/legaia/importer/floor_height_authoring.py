"""Qualified MAN 0x02..0x22 height-table edits; no floor/ramp behavior inference."""
from hashlib import sha256
import struct
from .core import ImportError,parse_man

def patch_floor_heights(source,source_sha256,scene,edits):
    if not isinstance(source,bytes) or sha256(source).hexdigest()!=source_sha256:raise ImportError('Floor MAN source hash differs from authored binding')
    parse_man(source,scene)
    if not isinstance(edits,list) or len(edits)>16:raise ImportError('Floor heights accept at most sixteen tier edits')
    changed=bytearray(source);seen=set();audit=[]
    for e in edits:
        if not isinstance(e,dict) or set(e)!={'tier','height'} or type(e['tier']) is not int or not 0<=e['tier']<16 or type(e['height']) is not int or not -32768<=e['height']<=32767 or e['tier'] in seen:raise ImportError('Floor heights require unique native tiers and signed sixteen-bit heights')
        tier=e['tier'];seen.add(tier);offset=2+tier*2;before=struct.unpack_from('<h',source,offset)[0]
        if before!=e['height']:
            struct.pack_into('<h',changed,offset,e['height']);audit.append(dict(tier=tier,field='floor_height',decoded_byte_offset=offset,byte_length=2,before_value=before,after_value=e['height'],record_index=0,semantic_id=f'scene://{scene}',scope='MAN-floor-height-table-only'))
    result=bytes(changed);parse_man(result,scene)
    if result[:2]!=source[:2] or result[0x22:]!=source[0x22:]:raise ImportError('Floor height edit changed an unauthorised MAN span')
    return result,sorted(audit,key=lambda e:e['tier'])
