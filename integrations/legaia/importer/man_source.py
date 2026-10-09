"""Typed MAN source handoff; raw streaming bytes never impersonate LZS bundles."""
from dataclasses import dataclass
from hashlib import sha256
from .core import ImportError, ParsedMan, SceneBundle, Descriptor, find_scene_bundle, decompress_lzs, parse_man
from .streaming_man import find_streaming_man_candidates


@dataclass(frozen=True)
class ManSource:
    kind: str
    entry_index: int
    payload_offset: int
    payload: bytes
    parsed: ParsedMan
    encoded_size: int
    bundle: SceneBundle | None = None
    descriptor: Descriptor | None = None
    chunk_header_offset: int | None = None

    def provenance(self):
        return dict(source_kind=self.kind,entry_index=self.entry_index,
                    payload_offset=self.payload_offset,decoded_size=len(self.payload),
                    encoded_size=self.encoded_size,payload_sha256=sha256(self.payload).hexdigest(),
                    compression='lzs' if self.kind=='descriptor_man' else 'none',
                    chunk_header_offset=self.chunk_header_offset)


def _qualify_controller_only_man(payload, parsed, scene):
    """An actor-free scene still requires a bounded partition-1 controller.

    This qualifies record ownership only; controller/P0 script semantics remain
    unknown. Streaming containers retain their separate placement requirement.
    """
    if parsed.partition_counts[1] != 1:
        raise ImportError(f'{scene}: MAN contains no actor placements or unique scene controller')
    total = sum(parsed.partition_counts)
    base = 0x2B + total * 3
    section = base + int.from_bytes(payload[0x28:0x2B], 'little')
    starts = [base + int.from_bytes(payload[0x2B + i * 3:0x2E + i * 3], 'little')
              for i in range(total)]
    if (not starts or len(set(starts)) != total
            or any(not base <= start < section <= len(payload) for start in starts)):
        raise ImportError(f'{scene}: controller-only MAN record ownership is invalid')


def read_man_source(archive,start,end,scene):
    try:
        bundle,raw=find_scene_bundle(archive,start,end)
    except ImportError as missing:
        candidates=find_streaming_man_candidates(archive,start,end,scene)
        if len(candidates)!=1:
            raise ImportError(f'{scene}: no unique MAN source ({len(candidates)} validated streaming candidates); {missing}') from missing
        candidate=candidates[0]
        payload=candidate['payload']
        parsed=parse_man(payload,scene)
        if not parsed.actors:
            raise ImportError(f'{scene}: streaming MAN has no actor placement records')
        return ManSource('raw_streaming_man',candidate['entry_index'],candidate['payload_offset'],
                         payload,parsed,len(payload),chunk_header_offset=candidate['chunk_header_offset'])
    descriptors=[d for d in bundle.descriptors if d.type_byte==3 and d.size>0]
    if len(descriptors)!=1:
        raise ImportError(f'{scene}: bundle requires a unique MAN descriptor')
    descriptor=descriptors[0]
    offset=bundle.table_offset+descriptor.data_offset
    ceiling=min([bundle.table_offset+d.data_offset for d in bundle.descriptors
                 if d.data_offset>descriptor.data_offset]+[len(raw)])
    if not 0<=offset<ceiling<=len(raw):
        raise ImportError(f'{scene}: MAN descriptor exceeds containing entry')
    # A malformed preferred descriptor is an error, not permission to silently
    # switch to a different script carrier from the same scene.
    payload,consumed=decompress_lzs(raw[offset:ceiling],descriptor.size)
    parsed=parse_man(payload,scene)
    if not parsed.actors:
        _qualify_controller_only_man(payload, parsed, scene)
    return ManSource('descriptor_man',bundle.entry_index,offset,payload,parsed,consumed,bundle,descriptor)
