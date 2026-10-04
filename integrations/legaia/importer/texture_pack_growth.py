"""Relocate compressed TIM packs while preserving native layouts and opaque bytes."""
from hashlib import sha256
import struct

from .core import ImportError, parse_scene_assets, decompress_lzs
from .textures import MAX_ENTRY_BYTES, _pack_members, parse_tim
from .texture_authoring import _validate, _encode_pack
from .model_pack_archive import _archive
from .prot_layout import locate_physical_span
from .prot_rebuild import replace_physical_entry


def qualify_texture_pack(source, candidate):
    if not isinstance(source,bytes) or not isinstance(candidate,bytes) or not 0<len(source)<=MAX_ENTRY_BYTES or len(source)!=len(candidate):
        raise ImportError('Texture pack replacement must preserve bounded decoded length')
    ranges=_pack_members(source,False)
    if not ranges or ranges!=_pack_members(candidate,False):
        raise ImportError('Texture pack member layout changed')
    cursor=0;changed=[]
    for slot,(start,end) in enumerate(ranges):
        if start<cursor or source[cursor:start]!=candidate[cursor:start]:
            raise ImportError('Texture pack changed headers or opaque bytes')
        old=parse_tim(source[start:end]);new=parse_tim(candidate[start:end])
        if old.byte_length!=new.byte_length:
            raise ImportError('Texture pack changed a TIM allocation')
        info=_validate(source[start:start+old.byte_length],candidate[start:start+old.byte_length])
        if info['changed']:changed.append(slot)
        cursor=start+old.byte_length
    if source[cursor:]!=candidate[cursor:]:
        raise ImportError('Texture pack changed opaque trailing bytes')
    return dict(source_sha256=sha256(source).hexdigest(),proposed_sha256=sha256(candidate).hexdigest(),
                byte_length=len(source),changed_slots=changed,slot_count=len(ranges))


def grow_texture_carrier(source, expected_sha256, descriptor_index, expected_pack_sha256, pack):
    if not isinstance(source,bytes) or not 0<len(source)<=MAX_ENTRY_BYTES or sha256(source).hexdigest()!=expected_sha256:
        raise ImportError('Texture carrier source changed or exceeds its byte budget')
    if type(descriptor_index) is not int:
        raise ImportError('Texture carrier requires an integer descriptor')
    table=parse_scene_assets(source,0)
    if table is None or not 0<=descriptor_index<len(table.descriptors):
        raise ImportError('Texture carrier descriptor is missing')
    row=table.descriptors[descriptor_index];table_end=8+8*len(table.descriptors)
    if row.type_byte!=1 or not row.size or any(not table_end<=d.data_offset<=len(source) or d.size and d.data_offset==len(source) for d in table.descriptors):
        raise ImportError('Texture carrier descriptor type or bounds changed')
    start=row.data_offset;end=min([d.data_offset for d in table.descriptors if d.data_offset>start]+[len(source)])
    if sum(d.data_offset==start for d in table.descriptors)!=1:
        raise ImportError('Texture carrier target has aliased ownership')
    original,consumed=decompress_lzs(source[start:end],row.size)
    if sha256(original).hexdigest()!=expected_pack_sha256:
        raise ImportError('Texture pack source hash changed')
    pack_audit=qualify_texture_pack(original,pack)
    encoded,stats=_encode_pack(source[start:start+consumed],pack,allow_growth=True)
    growth=stats['growth_bytes'];tail=start+consumed
    if len(source)+growth>MAX_ENTRY_BYTES:
        raise ImportError('Texture carrier growth exceeds its byte budget')
    candidate=bytearray(source[:start]+encoded+source[tail:]);moved=[]
    for descriptor in table.descriptors:
        if growth and descriptor.data_offset>=tail:
            struct.pack_into('<I',candidate,12+descriptor.index*8,descriptor.data_offset+growth)
            moved.append(dict(descriptor_index=descriptor.index,source_byte_offset=descriptor.data_offset,
                              proposed_byte_offset=descriptor.data_offset+growth))
    candidate=bytes(candidate);reopened=parse_scene_assets(candidate,0)
    if reopened is None or candidate[tail+growth:]!=source[tail:]:
        raise ImportError('Texture carrier changed following opaque payload')
    for before,after in zip(table.descriptors,reopened.descriptors):
        if after.type_byte!=before.type_byte or after.size!=before.size or after.data_offset!=before.data_offset+(growth if before.data_offset>=tail else 0):
            raise ImportError('Texture carrier descriptor relocation failed readback')
    verified,used=decompress_lzs(candidate[start:start+len(encoded)],row.size)
    if verified!=pack or used!=stats['new_encoded_size']:
        raise ImportError('Texture carrier failed independent exact pack readback')
    return candidate,dict(descriptor_index=descriptor_index,pack_audit=pack_audit,
                          moved_descriptors=moved,following_payload_preserved=True,**stats)


def rebuild_texture_pack_entry(source, expected_sha256, entry_index, table_offset, descriptor_index,
                               expected_pack_sha256, pack, *, header_offset=0):
    if not isinstance(source,bytes) or sha256(source).hexdigest()!=expected_sha256 or type(entry_index) is not int or type(table_offset) is not int or table_offset!=0:
        raise ImportError('Texture archive requires qualified source and an entry-head table')
    archive=_archive(source)
    if type(header_offset) is not int or archive.header_offset!=header_offset:
        raise ImportError('Texture archive header changed')
    entry=archive.entry(entry_index);span=locate_physical_span(archive,entry.start_lba*2048)
    if span['entry_index']!=entry_index or span['offset_within_span']!=0:
        raise ImportError('Texture archive requires unique physical ownership')
    start,length=span['byte_offset'],span['byte_length'];raw=source[start:start+length]
    grown,carrier=grow_texture_carrier(raw,sha256(raw).hexdigest(),descriptor_index,expected_pack_sha256,pack)
    padded=grown+bytes(-len(grown)%2048)
    result,allocation=replace_physical_entry(source,expected_sha256,entry_index,padded,header_offset=header_offset)
    reopened=_archive(result);target=reopened.entry(entry_index);new=locate_physical_span(reopened,target.start_lba*2048)
    if result[new['byte_offset']:new['byte_offset']+new['byte_length']]!=padded or result[start+len(padded):]!=source[start+length:]:
        raise ImportError('Texture archive carrier or physical neighbor readback changed')
    return result,dict(kind='texture-pack',entry_index=entry_index,source_sha256=expected_sha256,proposed_sha256=sha256(result).hexdigest(),
                       carrier=carrier,archive=allocation,reopened_pack_verified=True,physical_neighbors_preserved=True)
