"""Source-bound logical PROT growth. Does not serialize a disc image."""
from hashlib import sha256
import struct
from .core import ImportError


def patch_archive_spans(source: bytes, expected_sha256: str, patches: list[dict]) -> tuple[bytes, list[dict]]:
    """Compose source-addressed equal-span assets before physical relocation."""
    if not isinstance(source,bytes) or sha256(source).hexdigest()!=expected_sha256:
        raise ImportError('Archive patch source hash mismatch')
    if not isinstance(patches,list) or len(patches)>512:
        raise ImportError('Archive patch inventory exceeds bounds')
    spans=[]
    for patch in patches:
        if not isinstance(patch,dict) or set(patch)!={'offset','payload','expected_sha256'}:
            raise ImportError('Archive patch fields are invalid')
        offset,payload=patch['offset'],patch['payload']
        if type(offset) is not int or not isinstance(payload,bytes) or not payload or offset<0 or offset+len(payload)>len(source):
            raise ImportError('Archive patch exceeds source bounds')
        if sha256(source[offset:offset+len(payload)]).hexdigest()!=patch['expected_sha256']:
            raise ImportError('Archive patch preimage mismatch')
        spans.append((offset,payload,patch['expected_sha256']))
    output=bytearray(source)
    prior_end=-1
    audit=[]
    for offset,payload,before in sorted(spans,key=lambda item:item[0]):
        if offset<prior_end:
            raise ImportError('Archive asset patches overlap; compose their shared container first')
        prior_end=offset+len(payload)
        output[offset:prior_end]=payload
        audit.append(dict(offset=offset,size=len(payload),before_sha256=before,after_sha256=sha256(payload).hexdigest()))
    return bytes(output),audit


def rebuild_man_entries(source: bytes, expected_sha256: str, entries: list[dict],
                        *, header_offset: int = 0) -> tuple[bytes, dict]:
    """Rebuild distinct physical MAN owners in stable archive-index order.

    Entry indices survive TOC relocation. Table offsets remain owner-relative;
    shared physical owners require container composition before this operation.
    """
    if not isinstance(source,bytes) or sha256(source).hexdigest()!=expected_sha256:
        raise ImportError('Batch PROT source hash mismatch')
    if not isinstance(entries,list) or not 1<=len(entries)<=128:
        raise ImportError('Batch MAN rebuild requires 1 through 128 entries')
    owners=set()
    for item in entries:
        if not isinstance(item,dict) or set(item)!={'entry_index','table_offset','source_man_sha256','candidate'}:
            raise ImportError('Batch MAN entry fields are invalid')
        index=item['entry_index']
        if type(index) is not int or index<0 or index in owners:
            raise ImportError('Batch MAN entries require distinct physical owners')
        owners.add(index)
    result=source
    audits=[]
    for item in sorted(entries,key=lambda item:item['entry_index']):
        result,audit=rebuild_man_entry(result,sha256(result).hexdigest(),**item,header_offset=header_offset)
        audits.append(dict(entry_index=item['entry_index'],**audit))
    return result,dict(source_sha256=expected_sha256,result_sha256=sha256(result).hexdigest(),
                       entries=audits,build_ready=False)


def rebuild_man_entry(source: bytes, expected_sha256: str, entry_index: int,
                      table_offset: int, source_man_sha256: str, candidate: bytes,
                      *, header_offset: int = 0) -> tuple[bytes, dict]:
    """Compose MAN compression, physical allocation and logical TOC relocation."""
    from .core import ProtArchive, IsoNode, parse_scene_table, decompress_lzs
    from .man_container import encode_man_candidate
    from .prot_layout import locate_physical_span

    if not isinstance(source, bytes) or sha256(source).hexdigest() != expected_sha256:
        raise ImportError('PROT source hash mismatch')

    class MemoryImage:
        def __init__(self, data):
            self.data = data

        def read_user(self, _lba, offset, length, file_size):
            if offset < 0 or length < 0 or offset+length > min(file_size, len(self.data)):
                raise ImportError('Logical PROT read exceeds bounds')
            return self.data[offset:offset+length]

    archive = ProtArchive(MemoryImage(source), IsoNode(0, len(source), False, 'PROT.DAT'))
    if archive.header_offset != header_offset:
        raise ImportError('PROT header location disagrees with caller')
    if type(entry_index) is not int:
        raise ImportError('PROT entry index must be an integer')
    entry = archive.entry(entry_index)
    span = locate_physical_span(archive, entry.start_lba*archive.SECTOR)
    if span['entry_index'] != entry_index:
        raise ImportError('PROT entry is not a unique physical owner')
    start, length = span['byte_offset'], span['byte_length']
    container = source[start:start+length]
    encoded, container_audit = encode_man_candidate(
        container, sha256(container).hexdigest(), table_offset,
        source_man_sha256, candidate, allow_growth=True)
    encoded += bytes((-len(encoded)) % archive.SECTOR)
    rebuilt, archive_audit = replace_physical_entry(
        source, expected_sha256, entry_index, encoded, header_offset=header_offset)
    reopened = ProtArchive(MemoryImage(rebuilt), IsoNode(0, len(rebuilt), False, 'PROT.DAT'))
    target = reopened.entry(entry_index)
    raw = reopened.read_entry(target)
    table = parse_scene_table(raw, entry_index, table_offset)
    descriptors = [] if table is None else [d for d in table.descriptors if d.type_byte == 3 and d.size]
    if len(descriptors) != 1:
        raise ImportError('Rebuilt PROT does not expose one MAN descriptor')
    descriptor = descriptors[0]
    decoded, _ = decompress_lzs(raw[table_offset+descriptor.data_offset:], descriptor.size)
    if decoded != candidate:
        raise ImportError('Rebuilt PROT MAN roundtrip mismatch')
    return rebuilt, dict(container=container_audit, archive=archive_audit,
                         reopened_man_verified=True, build_ready=False)


def replace_physical_entry(source: bytes, expected_sha256: str, entry_index: int,
                           replacement: bytes, *, header_offset: int = 0) -> tuple[bytes, dict]:
    """Replace one consecutive-start span and relocate every later TOC start.

    Use the raw TOC, including end sentinels excluded by the decoder's read-window
    validation. Zero terminal words are retained. ISO relocation is a separate step.
    """
    sector = 2048
    if not isinstance(source, bytes) or sha256(source).hexdigest() != expected_sha256:
        raise ImportError('PROT source hash mismatch')
    if header_offset not in (0, sector) or type(header_offset) is not int:
        raise ImportError('Unsupported PROT header offset')
    if len(source) % sector or header_offset+12 > len(source):
        raise ImportError('PROT source must contain whole sectors and a header')
    count, header_sectors = struct.unpack_from('<ii', source, header_offset+4)
    table_start = header_offset+16
    table_end = table_start+count*4
    header_end = header_offset+header_sectors*sector
    if count < 2 or header_sectors < 1 or not table_end <= header_end <= len(source):
        raise ImportError('PROT start table exceeds header')
    starts = list(struct.unpack_from(f'<{count}I', source, table_start))
    active = []
    terminal = False
    for index, start in enumerate(starts):
        if start == 0:
            terminal = True
            continue
        if terminal or start*sector > len(source) or start*sector < header_end:
            raise ImportError('PROT starts are nonterminal after zero or outside payload')
        if active and start < active[-1][1]:
            raise ImportError('PROT starts are not monotonic')
        active.append((index, start))
    if type(entry_index) is not int or not 0 <= entry_index < len(active)-1:
        raise ImportError('PROT replacement requires a consecutive physical successor')
    start, end = starts[entry_index]*sector, starts[entry_index+1]*sector
    if start >= end:
        raise ImportError('PROT replacement span is empty')
    if not isinstance(replacement, bytes) or len(replacement) % sector or len(replacement) < end-start:
        raise ImportError('PROT replacement must be sector-aligned and cannot shrink')
    growth = len(replacement)-(end-start)
    delta = growth//sector
    if len(source)//sector+delta > 0xffffffff:
        raise ImportError('PROT sector count overflow')
    result = bytearray(source[:start]+replacement+source[end:])
    changes = []
    for index, old_start in active:
        if index <= entry_index:
            continue
        new_start = old_start+delta
        if delta:
            struct.pack_into('<I', result, table_start+index*4, new_start)
            changes.append(dict(entry_index=index, before=old_start, after=new_start))
    if result[end+growth:] != source[end:]:
        raise ImportError('PROT trailing payload preservation failed')
    encoded = bytes(result)
    return encoded, dict(source_sha256=expected_sha256,
                         result_sha256=sha256(encoded).hexdigest(),
                         entry_index=entry_index, source_bytes=len(source),
                         result_bytes=len(encoded), growth_sectors=delta,
                         relocated_starts=changes, following_payload_preserved=True,
                         disc_relocation_required=bool(delta), build_ready=False)
