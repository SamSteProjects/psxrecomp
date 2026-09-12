"""ISO metadata transforms for PROT growth; physical sector writing is separate."""
import struct
from .core import ImportError


def collect_metadata_relocation(image, growth_sectors: int) -> tuple[dict[int, bytes], dict]:
    """Return changed logical sectors keyed by their OLD disc LBA.

    The streaming writer relocates these keys after inserting the new allocation.
    Payload bytes stay internal; the returned audit contains metadata only.
    """
    prot = image.find('PROT.DAT')
    pvd = image.user_sector(16)
    changed = {}

    def patch(extent, offset, before, after):
        if len(before) != len(after):
            raise ImportError('ISO metadata transform changed allocation length')
        position = 0
        while position < len(before):
            lba = extent+(offset+position)//2048
            inside = (offset+position) % 2048
            take = min(2048-inside, len(before)-position)
            original = image.user_sector(lba)
            if original[inside:inside+take] != before[position:position+take]:
                raise ImportError('ISO metadata source preimage mismatch')
            current = bytearray(changed.get(lba, original))
            expected = before[position:position+take]
            replacement = after[position:position+take]
            if current[inside:inside+take] not in (expected, replacement):
                raise ImportError('Conflicting ISO metadata transforms')
            current[inside:inside+take] = replacement
            if current != original:
                changed[lba] = bytes(current)
            position += take

    patch(16, 0, pvd, relocate_primary_descriptor(pvd, prot.extent_lba, prot.size, growth_sectors))
    boundary = prot.extent_lba+prot.size//2048
    tables = path_table_locations(pvd)
    for table in tables:
        if table['size'] > 1024*1024:
            raise ImportError('ISO path table exceeds relocation limit')
        raw = image.read_user(table['lba'], 0, table['size'], table['size'])
        patch(table['lba'], 0, raw, relocate_path_table(
            raw, boundary, growth_sectors, big_endian=table['big_endian']))
    queue, seen = [image.root], {}
    records = 0
    while queue:
        directory = queue.pop()
        if directory.extent_lba in seen:
            if seen[directory.extent_lba] != directory.size:
                raise ImportError('ISO directory aliases disagree on size')
            continue
        if len(seen) >= 4096 or not 0 < directory.size <= 4*1024*1024:
            raise ImportError('ISO directory traversal exceeds relocation limits')
        seen[directory.extent_lba] = directory.size
        raw = image.read_file(directory)
        offset = 0
        while offset < len(raw):
            length = raw[offset]
            if not length:
                offset = (offset//2048+1)*2048
                continue
            if offset+length > len(raw) or offset % 2048+length > 2048:
                raise ImportError('ISO directory record crosses allocation or sector boundary')
            record = raw[offset:offset+length]
            relocated = relocate_directory_record(record, prot.extent_lba, prot.size, growth_sectors)
            patch(directory.extent_lba, offset, record, relocated)
            child = image._directory_record(raw, offset)
            if child.is_dir and child.name not in ('.', '..'):
                queue.append(child)
            offset += length
            records += 1
            if records > 100000:
                raise ImportError('ISO directory record count exceeds relocation limit')
    return changed, dict(prot_lba=prot.extent_lba, prot_bytes=prot.size,
                         insertion_lba=boundary, growth_sectors=growth_sectors,
                         directory_count=len(seen), directory_records=records,
                         path_table_count=len(tables), changed_sector_count=len(changed))


def relocate_primary_descriptor(pvd: bytes, prot_lba: int, prot_bytes: int,
                                 growth_sectors: int) -> bytes:
    """Relocate the PVD's volume size, table pointers and embedded root record."""
    locations = path_table_locations(pvd)
    if any(type(v) is not int or v < 0 for v in (prot_lba, prot_bytes, growth_sectors)):
        raise ImportError('Invalid ISO volume relocation range')
    if not prot_bytes or prot_bytes % 2048:
        raise ImportError('PROT extent must contain whole sectors')
    blocks = struct.unpack_from('<I', pvd, 80)[0]
    if blocks != struct.unpack_from('>I', pvd, 84)[0]:
        raise ImportError('ISO volume size endian copies disagree')
    block_size = struct.unpack_from('<H', pvd, 128)[0]
    if block_size != 2048 or block_size != struct.unpack_from('>H', pvd, 130)[0]:
        raise ImportError('ISO logical block size is unsupported or inconsistent')
    boundary = prot_lba+prot_bytes//2048
    if boundary > blocks or blocks+growth_sectors > 0xffffffff:
        raise ImportError('ISO volume relocation exceeds bounds')
    out = bytearray(pvd)
    struct.pack_into('<I', out, 80, blocks+growth_sectors)
    struct.pack_into('>I', out, 84, blocks+growth_sectors)
    for location in locations:
        start = location['lba']
        end = start+(location['size']+2047)//2048
        if end > blocks or (start < boundary and end > prot_lba):
            raise ImportError('ISO path table overlaps PROT or exceeds volume')
        if start >= boundary:
            struct.pack_into(('>' if location['big_endian'] else '<')+'I',
                             out, location['descriptor_offset'], start+growth_sectors)
    root_length = pvd[156]
    root = pvd[156:156+root_length]
    if len(root) < 34 or not root[25] & 2 or root[32:34] != b'\x01\x00':
        raise ImportError('ISO embedded root directory record is invalid')
    out[156:156+root_length] = relocate_directory_record(
        root, prot_lba, prot_bytes, growth_sectors)
    return bytes(out)


def path_table_locations(pvd: bytes) -> list[dict]:
    """Read mandatory and optional table locations from the primary descriptor."""
    if not isinstance(pvd, bytes) or len(pvd) != 2048 or pvd[:7] != b'\x01CD001\x01':
        raise ImportError('Invalid ISO primary volume descriptor')
    size = struct.unpack_from('<I', pvd, 132)[0]
    if size != struct.unpack_from('>I', pvd, 136)[0] or not size:
        raise ImportError('ISO path table size copies disagree or are empty')
    locations = []
    for offset, endian, required in [(140, '<', True), (144, '<', False),
                                      (148, '>', True), (152, '>', False)]:
        lba = struct.unpack_from(endian+'I', pvd, offset)[0]
        if not lba:
            if required:
                raise ImportError('Mandatory ISO path table is absent')
            continue
        locations.append(dict(lba=lba, size=size, big_endian=endian == '>',
                              descriptor_offset=offset))
    return locations


def relocate_path_table(table: bytes, insertion_lba: int, growth_sectors: int,
                        *, big_endian: bool) -> bytes:
    """Transform a complete logical path table, including odd-name padding."""
    if not isinstance(table, bytes) or not table or type(big_endian) is not bool:
        raise ImportError('Invalid ISO path table input')
    if any(type(v) is not int or not 0 <= v <= 0xffffffff
           for v in (insertion_lba, growth_sectors)):
        raise ImportError('Invalid ISO path table relocation range')
    endian = '>' if big_endian else '<'
    out = bytearray(table)
    offset = 0
    while offset < len(table):
        if offset+8 > len(table):
            raise ImportError('Truncated ISO path table header')
        length = table[offset]
        end = offset+8+length+(length & 1)
        if not length or end > len(table) or table[offset+1]:
            raise ImportError('Invalid or extended ISO path table record')
        extent = struct.unpack_from(endian+'I', table, offset+2)[0]
        if extent >= insertion_lba:
            extent += growth_sectors
            if extent > 0xffffffff:
                raise ImportError('ISO path table extent overflow')
            struct.pack_into(endian+'I', out, offset+2, extent)
        offset = end
    return bytes(out)


def relocate_directory_record(record: bytes, prot_lba: int, prot_bytes: int,
                              growth_sectors: int) -> bytes:
    """Update both endian copies while preserving all other record fields."""
    if any(type(v) is not int or v < 0 for v in (prot_lba, prot_bytes, growth_sectors)):
        raise ImportError('ISO relocation requires nonnegative integer extents')
    if not prot_bytes or prot_bytes % 2048:
        raise ImportError('PROT extent must contain whole sectors')
    if not isinstance(record, bytes) or len(record) < 34 or record[0] != len(record):
        raise ImportError('ISO directory record length mismatch')
    if not record[32] or 33+record[32] > len(record):
        raise ImportError('ISO directory identifier exceeds record')
    extent, size = struct.unpack_from('<I', record, 2)[0], struct.unpack_from('<I', record, 10)[0]
    if extent != struct.unpack_from('>I', record, 6)[0] or size != struct.unpack_from('>I', record, 14)[0]:
        raise ImportError('ISO directory endian copies disagree')
    if record[1] or record[26] or record[27] or record[25] & 0x80:
        raise ImportError('Extended, interleaved or multi-extent ISO record unsupported')
    end = prot_lba+prot_bytes//2048
    name = record[33:33+record[32]].split(b';', 1)[0]
    is_prot = name == b'PROT.DAT' and not record[25] & 2
    new_extent, new_size = extent, size
    if is_prot:
        if extent != prot_lba or size != prot_bytes:
            raise ImportError('PROT directory record disagrees with source extent')
        new_size += growth_sectors*2048
    elif extent >= end:
        new_extent += growth_sectors
    elif size and extent+(size+2047)//2048 > prot_lba:
        raise ImportError('Another ISO extent overlaps PROT allocation')
    if max(new_extent, new_size) > 0xffffffff:
        raise ImportError('Relocated ISO record exceeds 32-bit fields')
    out = bytearray(record)
    struct.pack_into('<I', out, 2, new_extent)
    struct.pack_into('>I', out, 6, new_extent)
    struct.pack_into('<I', out, 10, new_size)
    struct.pack_into('>I', out, 14, new_size)
    return bytes(out)
