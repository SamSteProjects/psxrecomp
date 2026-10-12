"""Equal-layout PLAYER action channel edits within the original record0 budget.

PLAYER uses nine bytes per part with six full twelve-bit components. This is
separate from the eight-byte field/World format. Counts, offsets, rate bytes,
art extensions, palettes, equipment descriptors and allocations remain owned
by the original source. This codec does not infer cadence or runtime activation.
"""
from hashlib import sha256
import struct
from .core import ImportError, decompress_lzs
from .player_battle import actions, decode_part
from .serialization import compress_lzs
from .lzs_optimal import MAX_OPTIMAL_BYTES, compress_lzs_optimal

MAX_EDITS = 16320


def _encode(translation, rotation):
    x,y,z = (v & 0xfff for v in translation)
    rx,ry,rz = rotation
    return bytes((x&255,y&255,(x>>8)|((y>>8)<<4),z&255,
        rx&255,(z>>8)|((rx>>8)<<4),ry&255,rz&255,(ry>>8)|((rz>>8)<<4)))


def patch_player_action(raw, expected_file_sha256, player_index, action_slot,
                        expected_action_sha256, edits):
    """Write exact axes in one stored action without allocating or relocating.

    Each sparse edit names a frame_index and native part_index, and nonempty
    translation and/or rotation_psx axis dictionaries. Duplicate frame/part
    ownership is rejected. No-op writes retain the original compressed bytes.
    """
    if not isinstance(raw,bytes) or sha256(raw).hexdigest()!=expected_file_sha256:
        raise ImportError('PLAYER action file differs from its source hash')
    clips,bank=actions(raw,player_index,'0'*64)
    if type(action_slot) is not int or not 0<=action_slot<len(clips):
        raise ImportError('PLAYER action slot is outside the stored table')
    clip=clips[action_slot];source=clip['source_record']
    if not clip['preview_supported'] or source['sha256']!=expected_action_sha256:
        raise ImportError('PLAYER action is empty or differs from its source hash')
    if not isinstance(edits,list) or len(edits)>MAX_EDITS:
        raise ImportError('PLAYER action edits exceed the bounded part-frame budget')
    seen=set()
    for edit in edits:
        if (not isinstance(edit,dict) or not {'frame_index','part_index'}<=set(edit)
                or set(edit)-{'frame_index','part_index','translation','rotation_psx'}
                or not {'translation','rotation_psx'}&set(edit)):
            raise ImportError('PLAYER action edit requires frame/part and transform axes only')
        frame,part=edit['frame_index'],edit['part_index']
        if type(frame) is not int or type(part) is not int or not 0<=frame<clip['frame_count'] or not 0<=part<clip['part_count']:
            raise ImportError('PLAYER action frame/part is outside the stored stream')
        if (frame,part) in seen:raise ImportError('Duplicate PLAYER action frame/part edit')
        seen.add((frame,part))
        for field in ('translation','rotation_psx'):
            if field not in edit:continue
            axes=edit[field]
            if not isinstance(axes,dict) or not axes or set(axes)-set('xyz'):
                raise ImportError('PLAYER action axes require a nonempty X/Y/Z mapping')
            low,high=(-2048,2047) if field=='translation' else (0,4095)
            if any(type(v) is not int or not low<=v<=high for v in axes.values()):
                raise ImportError('PLAYER action axes require exact twelve-bit integers')
    proposed_bank=bytearray(bank);channels=[];allowed=set()
    for edit in sorted(edits,key=lambda e:(e['frame_index'],e['part_index'])):
        frame,part=edit['frame_index'],edit['part_index']
        offset=source['byte_offset']+2+(frame*clip['part_count']+part)*9
        old=decode_part(bank[offset:offset+9]);values={k:list(v) for k,v in old.items()}
        for field in ('translation','rotation_psx'):
            for axis,value in sorted(edit.get(field,{}).items()):
                index='xyz'.index(axis)
                if value==values[field][index]:continue
                channels.append(dict(frame_index=frame,part_index=part,field=field+'.'+axis,
                    before_value=values[field][index],after_value=value,bank_byte_offset=offset))
                values[field][index]=value
        proposed_bank[offset:offset+9]=_encode(values['translation'],values['rotation_psx'])
        allowed.update(range(offset,offset+9))
    proposed_bank=bytes(proposed_bank)
    changed=[dict(byte_offset=i,before_byte=a,after_byte=b) for i,(a,b) in enumerate(zip(bank,proposed_bank)) if a!=b]
    if any(r['byte_offset'] not in allowed for r in changed):
        raise ImportError('PLAYER action edit changed a protected record0 byte')
    report=dict(schema_version='legaia.player-action-projection.v1',scope='PLAYER-action-channel-content-only',
        player_index=player_index,action_slot=action_slot,frame_count=clip['frame_count'],part_count=clip['part_count'],
        source_file_sha256=expected_file_sha256,source_bank_sha256=sha256(bank).hexdigest(),
        proposed_bank_sha256=sha256(proposed_bank).hexdigest(),source_action_sha256=expected_action_sha256,
        proposed_action_sha256=sha256(proposed_bank[source['byte_offset']:source['byte_offset']+source['byte_length']]).hexdigest(),
        channels=channels,changed_bytes=changed,gameplay_verified=False)
    if not channels:
        report.update(proposed_file_sha256=expected_file_sha256,compression='unchanged_noop')
        return raw,report
    descriptor_offset=struct.unpack_from('<I',raw)[0];capacity=descriptor_offset-16
    stream=compress_lzs(proposed_bank)
    strategy='greedy_lzs';greedy_bytes=len(stream)
    if len(stream)>capacity and len(proposed_bank)<=MAX_OPTIMAL_BYTES:
        stream=compress_lzs_optimal(proposed_bank);strategy='bounded_optimal_lzs'
    if len(stream)>capacity:raise ImportError('Edited PLAYER action exceeds its original record0 compressed allocation')
    decoded,used=decompress_lzs(stream,len(bank))
    if decoded!=proposed_bank or used!=len(stream):raise ImportError('PLAYER action compression failed exact readback')
    result=bytearray(raw);result[16:16+len(stream)]=stream;result=bytes(result)
    reopened,reopened_bank=actions(result,player_index,'0'*64)
    if reopened_bank!=proposed_bank or result[:16]!=raw[:16] or result[descriptor_offset:]!=raw[descriptor_offset:]:
        raise ImportError('PLAYER action projection changed a protected physical allocation')
    if any({k:v for k,v in a.items() if k!='source_record'}!={k:v for k,v in b.items() if k!='source_record'} for a,b in zip(clips,reopened)):
        raise ImportError('PLAYER action projection changed stored action structure')
    report.update(proposed_file_sha256=sha256(result).hexdigest(),compression=dict(
        allocation_bytes=capacity,old_consumed_bytes=source['compressed_bytes_consumed'],new_consumed_bytes=len(stream),
        strategy=strategy,greedy_encoded_bytes=greedy_bytes,
        unused_suffix_preserved=True,decoded_roundtrip=True))
    return result,report
