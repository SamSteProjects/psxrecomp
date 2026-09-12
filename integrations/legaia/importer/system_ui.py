"""Pinned boot-resident UI uploads, in source pack order (private disc data).

Evidence: reference system_ui_bundle.rs and scene/host/scene_entry.rs.
This is a static boot underlay, not a capture of current VRAM residency.
"""
from __future__ import annotations
import hashlib
import struct
from .core import ImportError
from .textures import TimBlock, parse_tim, _pack_members


def decode_boot_uploads(entries: tuple[bytes, bytes], digest: str):
    if len(entries) != 2 or any(not isinstance(entry, bytes) for entry in entries):
        raise ImportError('Boot UI requires exactly two raw byte entries')
    uploads = []
    atlas = False
    patches = []
    for raw_index, data in enumerate(entries):
        if len(data) > 2 * 1024 * 1024:
            raise ImportError('Boot UI entry exceeds bounded size')
        members = _pack_members(data, True)
        if len(members) != (20, 1)[raw_index]:
            raise ImportError('Boot UI pack member count differs from pinned layout')
        for slot, (start, end) in enumerate(members):
            body = data[start:end]
            source = {'semantic_id': f'texture://legaia/boot-ui/raw-{raw_index}/{slot}',
                      'disc_sha256': digest, 'raw_toc_entry': raw_index, 'pack_slot': slot,
                      'byte_offset': start, 'byte_coordinate_space': 'raw_prot_toc_entry',
                      'source_sha256': hashlib.sha256(body).hexdigest(),
                      'upload_evidence': 'system_ui_bundle.rs:table_order_image_then_flat_clut'}
            if body[:4] == b'\x10\0\0\0':
                tim = parse_tim(body)
                uploads.append((tim.image, dict(source, block='image')))
                if tim.clut:
                    c = tim.clut
                    if c.x + c.width_words * c.height > 1024:
                        raise ImportError('Boot UI CLUT strip exceeds VRAM')
                    uploads.append((TimBlock(c.x, c.y, c.width_words*c.height, 1, c.data), dict(source, block='clut')))
                    atlas |= raw_index == 0 and tim.image.metadata() == dict(x=960,y=256,width_words=64,height=256) and c.metadata() == dict(x=0,y=510,width_words=16,height=16)
            else:
                if len(body) < 20:
                    raise ImportError('Truncated boot UI row patch')
                size,x,y,w,h = struct.unpack_from('<I4H',body,8)
                if raw_index != 0 or (x,w,h) != (960,256,1) or y not in (456,457,458,460,461,462) or size != 12+w*h*2 or 8+size > len(body):
                    raise ImportError('Unsupported boot UI row patch')
                patches.append(y)
                uploads.append((TimBlock(x,y,w,h,body[20:8+size]),dict(source,block='row_patch',clipping='right_vram_edge')))
    if not atlas or sorted(patches) != [456,457,458,460,461,462]:
        raise ImportError('Boot UI atlas or row-patch fingerprint differs from pinned layout')
    return uploads


def load_boot_uploads(archive, digest):
    sectors = archive.toc[:3]
    if len(sectors) != 3 or not 0 < sectors[0] < sectors[1] < sectors[2]:
        raise ImportError('Boot UI raw TOC ranges are not monotonic')
    entries = []
    for start,end in zip(sectors,sectors[1:]):
        length = (end-start)*2048
        if length > 2*1024*1024:
            raise ImportError('Boot UI raw TOC range exceeds bounded size')
        entries.append(archive.image.read_user(archive.node.extent_lba,start*2048,length,archive.node.size))
    return decode_boot_uploads(tuple(entries),digest)
