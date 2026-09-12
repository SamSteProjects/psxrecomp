"""Read-only PROT overlap inventory; entries are not independent file extents."""
from .core import ImportError, ProtArchive


def locate_physical_span(archive: ProtArchive, byte_offset: int) -> dict:
    """Locate an offset between consecutive indexed starts, rejecting ambiguity."""
    if type(byte_offset) is not int or not 0 <= byte_offset < archive.node.size:
        raise ImportError('PROT physical offset is outside archive bounds')
    by_index = {entry.index: entry for entry in archive.entries}
    matches = []
    for entry in archive.entries:
        following = by_index.get(entry.index+1)
        if following is None:
            continue  # Tail ownership is not inferred from missing rows.
        start, end = entry.start_lba*archive.SECTOR, following.start_lba*archive.SECTOR
        if start <= byte_offset < end <= archive.node.size:
            matches.append(dict(entry_index=entry.index, byte_offset=start,
                                byte_length=end-start, offset_within_span=byte_offset-start,
                                evidence='consecutive_indexed_starts', relocation_verified=False))
    if len(matches) != 1:
        raise ImportError('PROT physical span is absent or ambiguous')
    return matches[0]


def inspect_entry_footprint(archive: ProtArchive, entry_index: int) -> dict:
    if type(entry_index) is not int:
        raise ImportError('PROT entry index must be an integer')
    entry = archive.entry(entry_index)
    toc_indices = [entry.index+2, entry.index+3, entry.index+5]
    toc_inputs = [dict(toc_index=i, byte_offset=archive.header_offset+8+4*i,
                       value=archive.toc[i]) for i in toc_indices]
    start, end = entry.start_lba, entry.start_lba+entry.size_sectors
    overlaps = []
    for other in archive.entries:
        if other.index == entry.index:
            continue
        lo, hi = max(start, other.start_lba), min(end, other.start_lba+other.size_sectors)
        if lo < hi:
            overlaps.append(dict(entry_index=other.index, start_lba=other.start_lba,
                                 overlap_start_lba=lo, overlap_sectors=hi-lo))
    return dict(entry_index=entry.index, start_lba=start, read_sectors=entry.size_sectors,
                indexed_size_sectors=entry.indexed_size_sectors,
                toc_inputs=toc_inputs,
                indexed_size_formula='(toc[index+5] - toc[index+3] + 4) modulo 2^32',
                footprint_formula='max(sane indexed size, sane next-start minus start)',
                overlapping_entries=overlaps,
                independent_resize_verified=False,
                interpretation='Decoded read windows; not independent allocation ownership')
