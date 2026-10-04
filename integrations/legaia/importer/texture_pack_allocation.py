"""Rebase existing TIM pack members after source-qualified image allocation."""
from hashlib import sha256
import struct

from .core import ImportError
from .textures import _pack_members,parse_tim,MAX_ENTRY_BYTES
from .texture_layout_allocation import validate_tim_allocation


def allocate_texture_pack(source, expected_sha256, edits, *, standalone=False):
    if (not isinstance(source,bytes) or not 0<len(source)<=MAX_ENTRY_BYTES or
            sha256(source).hexdigest()!=expected_sha256 or type(standalone) is not bool):
        raise ImportError('Texture pack allocation requires bounded, hash-qualified source bytes')
    if not isinstance(edits,list) or not 1<=len(edits)<=128:
        raise ImportError('Texture pack allocation requires one to 128 source member edits')
    members=_pack_members(source,standalone);prepared={};audits={}
    for edit in edits:
        if not isinstance(edit,dict) or set(edit)!={'slot_index','source_tim_sha256','tim'}:
            raise ImportError('Texture pack allocation edit fields are malformed')
        slot=edit['slot_index']
        if type(slot) is not int or not 0<=slot<len(members) or slot in prepared:
            raise ImportError('Texture pack allocation slot is invalid or duplicated')
        start,end=members[slot];old=parse_tim(source[start:end]);original=source[start:start+old.byte_length]
        if sha256(original).hexdigest()!=edit['source_tim_sha256']:
            raise ImportError('Texture pack allocation member source hash changed')
        audits[slot]=validate_tim_allocation(original,edit['tim']);prepared[slot]=edit['tim']
    result=bytearray(source[:members[0][0]]);rows=[];base=4 if standalone else 0
    for slot,(start,end) in enumerate(members):
        old=parse_tim(source[start:end]);payload=prepared.get(slot,source[start:start+old.byte_length]);tail=source[start+old.byte_length:end]
        proposed_start=len(result)
        if (proposed_start-base)%4:
            raise ImportError('Texture pack allocation member lost word alignment')
        struct.pack_into('<I',result,base+4+slot*4,(proposed_start-base)//4)
        result.extend(payload);result.extend(tail)
        padding=(-len(result))%4 if slot<len(members)-1 else 0
        result.extend(bytes(padding))
        if len(result)>MAX_ENTRY_BYTES:
            raise ImportError('Texture pack allocation exceeds its decoded byte budget')
        rows.append(dict(slot_index=slot,source_byte_offset=start,proposed_byte_offset=proposed_start,
                         source_tim_byte_length=old.byte_length,proposed_tim_byte_length=len(payload),
                         opaque_tail_sha256=sha256(tail).hexdigest(),opaque_tail_byte_length=len(tail),
                         alignment_padding_bytes=padding,replacement=slot in prepared))
    candidate=bytes(result);reopened=_pack_members(candidate,standalone)
    if len(reopened)!=len(members):
        raise ImportError('Texture pack allocation changed native member identities')
    for row,(start,end) in zip(rows,reopened):
        slot=row['slot_index'];old_start,old_end=members[slot]
        payload=prepared.get(slot,source[old_start:old_start+row['source_tim_byte_length']])
        tail=source[old_start+row['source_tim_byte_length']:old_end]
        if start!=row['proposed_byte_offset'] or candidate[start:end]!=payload+tail+bytes(row['alignment_padding_bytes']):
            raise ImportError('Texture pack allocation failed exact member/tail readback')
        parse_tim(candidate[start:end])
    return candidate,dict(schema_version='legaia.texture-pack-allocation.v1',source_sha256=expected_sha256,
                         proposed_sha256=sha256(candidate).hexdigest(),source_byte_length=len(source),
                         proposed_byte_length=len(candidate),growth_bytes=len(candidate)-len(source),
                         standalone=standalone,slot_count=len(members),members=rows,
                         edits=[dict(slot_index=slot,allocation=audits[slot]) for slot in sorted(audits)],
                         native_members_verified=True,opaque_tails_preserved=True,gameplay_verified=False)
