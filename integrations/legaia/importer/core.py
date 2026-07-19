"""Independent parsers for the metadata-only Legaia scene importer.

Format interpretations are attributed in ../provenance/reference-manifest.json.
This module contains no code dependency on the reference repository.
"""

from __future__ import annotations

import hashlib
import json
import re
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, Iterable


class ImportError(Exception):
    """A safe importer failure containing structural, never binary, context."""


def _u24(data: bytes, offset: int) -> int:
    if offset < 0 or offset + 3 > len(data):
        raise ImportError(f"truncated u24 at decoded offset 0x{offset:X}")
    return int.from_bytes(data[offset : offset + 3], "little")


def _u32(data: bytes, offset: int) -> int:
    if offset < 0 or offset + 4 > len(data):
        raise ImportError(f"truncated u32 at offset 0x{offset:X}")
    return struct.unpack_from("<I", data, offset)[0]


def stable_actor_id(scene: str, partition: int, record_index: int) -> str:
    if not re.fullmatch(r"[a-z0-9_]+", scene):
        raise ImportError(f"invalid structural scene name: {scene!r}")
    if partition < 0 or record_index < 0:
        raise ImportError("actor identity indices must be non-negative")
    return f"scene://{scene}/actors/man-p{partition}/{record_index:04d}"


def stable_model_asset_id(scene: str, pool: str, pool_index: int) -> str:
    if not re.fullmatch(r"[a-z0-9_]+", scene):
        raise ImportError(f"invalid structural scene name: {scene!r}")
    if pool_index < 0:
        raise ImportError("model pool index must be non-negative")
    if pool == "scene_tmd":
        return f"asset://{scene}/models/scene-tmd/{pool_index:04d}"
    if pool == "global_special":
        encoded = 0xF0 + pool_index
        if encoded > 0xFF:
            raise ImportError("global-special model pool index exceeds placement byte range")
        return f"asset://legaia/models/global-special/{encoded:04x}"
    raise ImportError(f"unsupported model pool: {pool}")


CONFIDENCE_VALUES = {
    "confirmed",
    "strongly_inferred",
    "tentative",
    "unknown",
    "contradictory",
}


def claim(
    property_name: str,
    value: Any,
    confidence: str,
    evidence: list[dict[str, Any]],
    source: dict[str, Any],
    notes: str,
) -> dict[str, Any]:
    if confidence not in CONFIDENCE_VALUES:
        raise ImportError(f"unsupported claim confidence: {confidence}")
    return {
        "property": property_name,
        "value": value,
        "confidence": confidence,
        "evidence": evidence,
        "source": source,
        "notes": notes,
    }


def normalize_claims(claims: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove exact duplicates and preserve conflicts as contradictory claims."""
    unique: dict[str, dict[str, Any]] = {}
    for item in claims:
        key = canonical_json(item)
        unique.setdefault(key, dict(item))
    result = list(unique.values())
    by_property: dict[str, set[str]] = {}
    for item in result:
        by_property.setdefault(item["property"], set()).add(canonical_json(item["value"]))
    for item in result:
        if len(by_property[item["property"]]) > 1:
            item["confidence"] = "contradictory"
            item["notes"] = (item.get("notes", "") + " Conflicts with another active value.").strip()
    return sorted(result, key=lambda x: (x["property"], canonical_json(x["value"])))


def canonical_json(value: Any, *, pretty: bool = False) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        indent=2 if pretty else None,
        separators=None if pretty else (",", ":"),
    )


FORBIDDEN_METADATA_KEYS = {
    "asset_bytes",
    "binary",
    "data",
    "dialogue",
    "disc_path",
    "mesh",
    "payload",
    "raw_bytes",
    "sectors",
    "texture",
}


def validate_metadata_only(value: Any, path: str = "$") -> None:
    if isinstance(value, (bytes, bytearray, memoryview)):
        raise ImportError(f"metadata-only output contains binary value at {path}")
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in FORBIDDEN_METADATA_KEYS:
                raise ImportError(f"metadata-only output contains forbidden field {path}.{key}")
            validate_metadata_only(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            validate_metadata_only(child, f"{path}[{index}]")
    elif not isinstance(value, (str, int, float, bool, type(None))):
        raise ImportError(f"metadata-only output contains unsupported value at {path}")


MODE2_SECTOR = 2352
USER_OFFSET = 24
USER_SIZE = 2048
SYNC = b"\x00" + b"\xff" * 10 + b"\x00"


@dataclass(frozen=True)
class IsoNode:
    extent_lba: int
    size: int
    is_dir: bool
    name: str


class Mode2Image:
    """Streaming Mode 2/2352 reader with an ISO9660 file lookup."""

    def __init__(self, path: Path):
        self.path = resolve_disc_path(path)
        try:
            self.handle: BinaryIO = self.path.open("rb")
        except OSError as exc:
            raise ImportError(f"cannot open disc image: {exc}") from exc
        self.size = self.path.stat().st_size
        if self.size % MODE2_SECTOR:
            self.close()
            raise ImportError("unsupported disc layout: expected Mode 2/2352 sectors")
        try:
            if self._raw_sector(16)[:12] != SYNC:
                raise ImportError("unsupported disc layout: Mode 2 sync pattern absent")
            pvd = self.user_sector(16)
            if pvd[0] != 1 or pvd[1:6] != b"CD001":
                raise ImportError("ISO9660 primary volume descriptor is missing")
            self.root = self._directory_record(pvd, 156)
        except Exception:
            self.close()
            raise

    def close(self) -> None:
        if not self.handle.closed:
            self.handle.close()

    def __enter__(self) -> "Mode2Image":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _raw_sector(self, lba: int) -> bytes:
        if lba < 0 or (lba + 1) * MODE2_SECTOR > self.size:
            raise ImportError(f"disc LBA {lba} is out of bounds")
        self.handle.seek(lba * MODE2_SECTOR)
        raw = self.handle.read(MODE2_SECTOR)
        if len(raw) != MODE2_SECTOR:
            raise ImportError(f"truncated disc sector at LBA {lba}")
        return raw

    def user_sector(self, lba: int) -> bytes:
        raw = self._raw_sector(lba)
        if raw[:12] != SYNC:
            raise ImportError(f"invalid Mode 2 sector sync at LBA {lba}")
        return raw[USER_OFFSET : USER_OFFSET + USER_SIZE]

    def read_user(self, extent_lba: int, offset: int, length: int, file_size: int) -> bytes:
        if offset < 0 or length < 0 or offset + length > file_size:
            raise ImportError(
                f"ISO file read [0x{offset:X}, +{length}] exceeds file size 0x{file_size:X}"
            )
        output = bytearray()
        position = offset
        while len(output) < length:
            lba = extent_lba + position // USER_SIZE
            inside = position % USER_SIZE
            take = min(length - len(output), USER_SIZE - inside)
            output += self.user_sector(lba)[inside : inside + take]
            position += take
        return bytes(output)

    @staticmethod
    def _directory_record(data: bytes, offset: int) -> IsoNode:
        if offset < 0 or offset >= len(data) or data[offset] < 34:
            raise ImportError(f"invalid ISO9660 directory record at offset 0x{offset:X}")
        length = data[offset]
        if offset + length > len(data):
            raise ImportError(f"truncated ISO9660 directory record at offset 0x{offset:X}")
        name_len = data[offset + 32]
        raw_name = data[offset + 33 : offset + 33 + name_len]
        if raw_name == b"\x00":
            name = "."
        elif raw_name == b"\x01":
            name = ".."
        else:
            name = raw_name.decode("ascii", "strict").split(";", 1)[0]
        return IsoNode(
            extent_lba=struct.unpack_from("<I", data, offset + 2)[0],
            size=struct.unpack_from("<I", data, offset + 10)[0],
            is_dir=bool(data[offset + 25] & 2),
            name=name,
        )

    def _children(self, directory: IsoNode) -> list[IsoNode]:
        if not directory.is_dir:
            raise ImportError(f"ISO9660 path component {directory.name} is not a directory")
        body = self.read_user(directory.extent_lba, 0, directory.size, directory.size)
        children: list[IsoNode] = []
        offset = 0
        while offset < len(body):
            length = body[offset]
            if length == 0:
                offset = ((offset // USER_SIZE) + 1) * USER_SIZE
                continue
            node = self._directory_record(body, offset)
            if node.name not in {".", ".."}:
                children.append(node)
            offset += length
        return children

    def find(self, path: str) -> IsoNode:
        current = self.root
        for part in [p for p in path.replace("\\", "/").split("/") if p]:
            match = next((n for n in self._children(current) if n.name.upper() == part.upper()), None)
            if match is None:
                raise ImportError(f"required ISO9660 file is absent: {path}")
            current = match
        return current

    def read_file(self, node: IsoNode) -> bytes:
        return self.read_user(node.extent_lba, 0, node.size, node.size)


def resolve_disc_path(path: Path) -> Path:
    if path.suffix.lower() != ".cue":
        return path
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise ImportError(f"cannot open cue sheet: {exc}") from exc
    match = re.search(r'^\s*FILE\s+(?:"([^"]+)"|(\S+))\s+BINARY\s*$', text, re.I | re.M)
    if not match:
        raise ImportError("cue sheet has no BINARY FILE entry")
    return path.parent / (match.group(1) or match.group(2))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise ImportError(f"cannot fingerprint disc image: {exc}") from exc
    return digest.hexdigest()


SUPPORTED_DISC_SHA256 = "e6120a5d70716dd2f026a2da32d0171d52651971b52c4347a68541299f75258c"


@dataclass(frozen=True)
class ProtEntry:
    index: int
    start_lba: int
    indexed_size_sectors: int
    size_sectors: int


class ProtArchive:
    SECTOR = 0x800
    MAX_SECTORS = 64 * 1024

    def __init__(self, image: Mode2Image, node: IsoNode):
        self.image = image
        self.node = node
        self.header_offset, file_num, header_sectors = self._detect_header()
        toc_start = self.header_offset + 8
        toc_end = self.header_offset + header_sectors * self.SECTOR
        raw = image.read_user(node.extent_lba, toc_start, toc_end - toc_start, node.size)
        self.toc = list(struct.unpack(f"<{len(raw) // 4}I", raw[: len(raw) // 4 * 4]))
        self.entries: list[ProtEntry] = []
        for index in range(max(file_num - 1, 0)):
            if index + 5 >= len(self.toc):
                break
            start = self.toc[index + 2]
            next_start = self.toc[index + 3]
            payload_end = self.toc[index + 5]
            if start == next_start == payload_end == 0:
                continue
            indexed_raw = (payload_end - next_start + 4) & 0xFFFFFFFF
            footprint = (next_start - start) & 0xFFFFFFFF
            footprint_sane = 0 < footprint <= self.MAX_SECTORS
            if indexed_raw <= self.MAX_SECTORS:
                indexed = indexed_raw
            elif footprint_sane:
                indexed = footprint
            else:
                continue
            full = max(indexed, footprint) if footprint_sane else indexed
            if (start + full) * self.SECTOR > node.size:
                continue
            self.entries.append(ProtEntry(index, start, indexed, full))

    def _detect_header(self) -> tuple[int, int, int]:
        for offset in (0, 0x800):
            if offset + 12 > self.node.size:
                continue
            buf = self.image.read_user(self.node.extent_lba, offset, 12, self.node.size)
            file_num_minus_1, header_sectors = struct.unpack_from("<ii", buf, 4)
            if file_num_minus_1 <= 0 or header_sectors <= 0:
                continue
            if offset + header_sectors * self.SECTOR <= self.node.size:
                return offset, file_num_minus_1 + 1, header_sectors
        raise ImportError("PROT.DAT has no supported header at offset 0x000 or 0x800")

    def entry(self, index: int) -> ProtEntry:
        match = next((entry for entry in self.entries if entry.index == index), None)
        if match is None:
            raise ImportError(f"PROT entry {index} is absent or structurally invalid")
        return match

    def read_entry(self, entry: ProtEntry, *, extended: bool = True) -> bytes:
        sectors = entry.size_sectors if extended else entry.indexed_size_sectors
        return self.image.read_user(
            self.node.extent_lba,
            entry.start_lba * self.SECTOR,
            sectors * self.SECTOR,
            self.node.size,
        )


def parse_prot_bytes(data: bytes) -> list[ProtEntry]:
    """Synthetic-data convenience parser used by unit tests."""
    class MemoryImage:
        def read_user(self, _lba: int, offset: int, length: int, file_size: int) -> bytes:
            if offset < 0 or offset + length > file_size:
                raise ImportError("synthetic PROT read out of bounds")
            return data[offset : offset + length]

    node = IsoNode(0, len(data), False, "PROT.DAT")
    return ProtArchive(MemoryImage(), node).entries  # type: ignore[arg-type]


def parse_cdname(text: str) -> dict[int, str]:
    result: dict[int, str] = {}
    for line in text.splitlines():
        match = re.match(r"\s*#define\s+(\S+)\s+(\d+)\s*$", line)
        if match:
            result[int(match.group(2))] = match.group(1)
    return dict(sorted(result.items()))


def scene_range(mapping: dict[int, str], scene: str) -> tuple[int, int]:
    starts = [index for index, name in mapping.items() if name == scene]
    if not starts:
        raise ImportError(f"unsupported or absent scene: {scene}")
    raw_start = starts[0]
    raw_end = next((index for index in mapping if index > raw_start), 0xFFFFFFFF)
    if raw_start < 2:
        return raw_start, raw_end
    return raw_start - 2, max(raw_end - 2, 0)


KNOWN_ASSET_TYPES = set(range(0x00, 0x0C)) | {0x0F, 0x14}


@dataclass(frozen=True)
class Descriptor:
    index: int
    type_byte: int
    size: int
    data_offset: int


@dataclass(frozen=True)
class SceneBundle:
    entry_index: int
    table_offset: int
    descriptors: tuple[Descriptor, ...]


@dataclass(frozen=True)
class LzsSection:
    index: int
    decoded_size: int
    stream_offset: int


@dataclass(frozen=True)
class TmdRecord:
    pool: str
    pool_index: int
    entry_index: int
    source_kind: str
    byte_offset: int
    byte_length: int
    containing_size: int
    object_count: int
    container_section: int | None = None
    stream_offset: int | None = None
    pack_slot: int | None = None
    tmd_byte_length: int | None = None


def parse_scene_table(data: bytes, entry_index: int, offset: int = 0) -> SceneBundle | None:
    if offset < 0 or offset + 8 > len(data):
        return None
    count = _u32(data, offset)
    if count not in (6, 7):
        return None
    table_size = 8 + count * 8
    if offset + table_size > len(data):
        return None
    descriptors = []
    for index in range(count):
        word = _u32(data, offset + 8 + index * 8)
        data_offset = _u32(data, offset + 12 + index * 8)
        type_byte = word >> 24
        size = word & 0xFFFFFF
        if type_byte not in KNOWN_ASSET_TYPES or size > 4 * 1024 * 1024:
            return None
        if (index == 0 and data_offset != table_size) or (index > 0 and data_offset > 16 * 1024 * 1024):
            return None
        descriptors.append(Descriptor(index, type_byte, size, data_offset))
    if not any(item.type_byte == 3 and item.size > 0 for item in descriptors):
        return None
    return SceneBundle(entry_index, offset, tuple(descriptors))


def find_scene_bundle(archive: ProtArchive, start: int, end: int) -> tuple[SceneBundle, bytes]:
    end = min(end, max((entry.index for entry in archive.entries), default=-1) + 1)
    for index in range(start, end):
        try:
            entry = archive.entry(index)
        except ImportError:
            continue
        indexed = archive.read_entry(entry, extended=False)
        for offset in [0, *range(0x800, len(indexed), 0x800)]:
            bundle = parse_scene_table(indexed, index, offset)
            if bundle:
                return bundle, archive.read_entry(entry, extended=True)
    raise ImportError(f"town01 scene range [{start}, {end}) contains no MAN-bearing bundle")


def decompress_lzs(data: bytes, expected_size: int) -> tuple[bytes, int]:
    if expected_size < 0 or expected_size > 4 * 1024 * 1024:
        raise ImportError(f"invalid LZS output size: {expected_size}")
    window = bytearray(4096)
    window_pos = 0xFEE
    source = 0
    control = 0
    output = bytearray()
    while len(output) < expected_size:
        if control & 0x100 == 0:
            if source >= len(data):
                raise ImportError(f"truncated LZS control at decoded byte {len(output)}")
            control = data[source] | 0xFF00
            source += 1
        if control & 1:
            if source >= len(data):
                raise ImportError(f"truncated LZS literal at decoded byte {len(output)}")
            value = data[source]
            source += 1
            output.append(value)
            window[window_pos] = value
            window_pos = (window_pos + 1) & 0xFFF
        else:
            if source + 2 > len(data):
                raise ImportError(f"truncated LZS back-reference at decoded byte {len(output)}")
            b0, b1 = data[source], data[source + 1]
            source += 2
            base = b0 | ((b1 & 0xF0) << 4)
            length = (b1 & 0x0F) + 3
            for step in range(length):
                value = window[(base + step) & 0xFFF]
                output.append(value)
                window[window_pos] = value
                window_pos = (window_pos + 1) & 0xFFF
                if len(output) == expected_size:
                    break
        control >>= 1
    return bytes(output), source


def parse_lzs_sections(data: bytes, *, maximum: int = 64) -> tuple[LzsSection, ...]:
    """Parse the bounded `(decoded size, stream offset)` container table."""
    if len(data) < 16:
        raise ImportError("LZS container is shorter than its header")
    sections: list[LzsSection] = []
    last_offset = 0
    for index in range(min(len(data) // 8 - 1, maximum)):
        pair_offset = 8 + index * 8
        decoded_size = _u32(data, pair_offset) & 0xFFFFFF
        stream_offset = _u32(data, pair_offset + 4)
        if decoded_size == 0 or stream_offset == 0:
            break
        if stream_offset >= len(data) or stream_offset < last_offset:
            break
        sections.append(LzsSection(index, decoded_size, stream_offset))
        last_offset = stream_offset
    if not sections:
        raise ImportError("LZS container has no bounded sections")
    return tuple(sections)


def decode_lzs_sections(data: bytes) -> tuple[tuple[LzsSection, bytes, int], ...]:
    sections = parse_lzs_sections(data)
    decoded = []
    for position, section in enumerate(sections):
        stream_end = sections[position + 1].stream_offset if position + 1 < len(sections) else len(data)
        body, consumed = decompress_lzs(data[section.stream_offset:stream_end], section.decoded_size)
        if consumed > stream_end - section.stream_offset:
            raise ImportError(f"LZS section {section.index} consumed beyond its encoded bounds")
        decoded.append((section, body, consumed))
    return tuple(decoded)


TMD_MAGIC = 0x80000002
TMD_HEADER_SIZE = 12
TMD_OBJECT_SIZE = 28
TMD_VECTOR_SIZE = 8


def _tmd_extent(data: bytes, offset: int) -> tuple[int, int] | None:
    """Return `(byte extent, object count)` for a structurally bounded TMD."""
    if offset < 0 or offset + TMD_HEADER_SIZE > len(data) or _u32(data, offset) != TMD_MAGIC:
        return None
    object_count = _u32(data, offset + 8)
    if object_count == 0 or object_count > 1024:
        return None
    table_end = TMD_HEADER_SIZE + object_count * TMD_OBJECT_SIZE
    available = len(data) - offset
    if table_end > available:
        return None
    extent = table_end
    total_vertices = 0
    for index in range(object_count):
        base = offset + TMD_HEADER_SIZE + index * TMD_OBJECT_SIZE
        vert_top, n_vert, normal_top, n_normal, prim_top = struct.unpack_from("<IIIII", data, base)
        if n_vert > 1_000_000 or n_normal > 1_000_000:
            return None
        vert_start = TMD_HEADER_SIZE + vert_top
        normal_start = TMD_HEADER_SIZE + normal_top
        prim_start = TMD_HEADER_SIZE + prim_top
        vert_end = vert_start + n_vert * TMD_VECTOR_SIZE
        normal_end = normal_start + n_normal * TMD_VECTOR_SIZE
        if vert_end > available or normal_end > available or prim_start > available:
            return None
        prim_end = min(
            [candidate for count, candidate in ((n_vert, vert_start), (n_normal, normal_start)) if count]
            or [available]
        )
        if prim_start > prim_end:
            return None
        extent = max(extent, vert_end, normal_end, prim_end)
        total_vertices += n_vert
    if total_vertices < 4:
        return None
    return extent, object_count


def scan_tmds(data: bytes) -> tuple[tuple[int, int, int], ...]:
    hits = []
    for offset in range(0, max(len(data) - 3, 0), 4):
        if _u32(data, offset) != TMD_MAGIC:
            continue
        parsed = _tmd_extent(data, offset)
        if parsed is not None:
            hits.append((offset, parsed[0], parsed[1]))
    return tuple(hits)


def is_scene_tmd_stream(data: bytes) -> bool:
    if len(data) < 32 or _u32(data, 4) != TMD_MAGIC or _u32(data, 8) != 0:
        return False
    object_count = _u32(data, 12)
    header = _u32(data, 0)
    tmd_size = header & 0xFFFFFF
    if header >> 24 or object_count == 0 or object_count > 64:
        return False
    if tmd_size < TMD_HEADER_SIZE + object_count * TMD_OBJECT_SIZE or tmd_size % 4:
        return False
    return 4 + tmd_size <= len(data) and _tmd_extent(data, 4) is not None


def scene_tmd_pool(archive: ProtArchive, start: int, end: int) -> tuple[TmdRecord, ...]:
    records: list[TmdRecord] = []
    for entry_index in range(start, end):
        try:
            entry = archive.entry(entry_index)
        except ImportError:
            continue
        raw = archive.read_entry(entry, extended=True)
        if is_scene_tmd_stream(raw):
            continue
        for byte_offset, byte_length, object_count in scan_tmds(raw):
            records.append(
                TmdRecord("scene_tmd", len(records), entry_index, "raw_prot_entry", byte_offset, byte_length, len(raw), object_count)
            )
        try:
            sections = decode_lzs_sections(raw)
        except ImportError:
            continue
        for section, body, _consumed in sections:
            for byte_offset, byte_length, object_count in scan_tmds(body):
                records.append(
                    TmdRecord(
                        "scene_tmd",
                        len(records),
                        entry_index,
                        "decoded_lzs_section",
                        byte_offset,
                        byte_length,
                        len(body),
                        object_count,
                        container_section=section.index,
                        stream_offset=section.stream_offset,
                    )
                )
    return tuple(records)


def _pack_ranges(data: bytes) -> tuple[tuple[int, int], ...]:
    if len(data) < 4:
        raise ImportError("model pack is shorter than its count")
    count = _u32(data, 0)
    if count > 65536 or 4 + count * 4 > len(data):
        raise ImportError(f"model pack has invalid entry count {count}")
    offsets = [_u32(data, 4 + index * 4) * 4 for index in range(count)]
    if any(offset > len(data) for offset in offsets) or offsets != sorted(offsets):
        raise ImportError("model pack offsets are out of bounds or non-monotonic")
    ends = offsets[1:] + [len(data)]
    return tuple(zip(offsets, ends))


def global_special_tmd_pool(archive: ProtArchive) -> tuple[TmdRecord, ...]:
    entry_index = 874
    raw = archive.read_entry(archive.entry(entry_index), extended=True)
    decoded_sections = decode_lzs_sections(raw)
    if not decoded_sections or decoded_sections[0][0].index != 0:
        raise ImportError("PROT entry 874 has no decoded global-special section 0")
    section, body, _consumed = decoded_sections[0]
    ranges = _pack_ranges(body)
    if len(ranges) < 5:
        raise ImportError(f"global-special TMD pack has {len(ranges)} entries; expected at least 5")
    records = []
    for slot, (start, end) in enumerate(ranges[:5]):
        parsed = _tmd_extent(body[start:end], 0)
        if parsed is None:
            raise ImportError(f"global-special TMD pack slot {slot} is not structurally valid")
        tmd_length, object_count = parsed
        records.append(
            TmdRecord(
                "global_special",
                slot,
                entry_index,
                "decoded_tmd_pack_slot",
                start,
                end - start,
                len(body),
                object_count,
                container_section=section.index,
                stream_offset=section.stream_offset,
                pack_slot=slot,
                tmd_byte_length=tmd_length,
            )
        )
    return tuple(records)


@dataclass(frozen=True)
class ManActor:
    record_index: int
    byte_offset: int
    byte_length: int
    local_count: int
    model_index: int
    animation_id: int
    tile_x: int
    tile_z: int
    world_x: int
    world_z: int


@dataclass(frozen=True)
class ParsedMan:
    partition_counts: tuple[int, int, int]
    actors: tuple[ManActor, ...]


def parse_man(data: bytes, scene: str = "town01") -> ParsedMan:
    if len(data) < 0x2B:
        raise ImportError(f"{scene} MAN header is truncated")
    counts = struct.unpack_from("<hhh", data, 0x22)
    if any(count < 0 for count in counts):
        raise ImportError(f"{scene} MAN has negative partition counts")
    total = sum(counts)
    table_end = 0x2B + total * 3
    if table_end > len(data):
        raise ImportError(f"{scene} MAN record-offset table is truncated")
    data_region = table_end
    offsets = [_u24(data, 0x2B + index * 3) for index in range(total)]
    section_offsets: list[int] = []
    section = data_region + _u24(data, 0x28)
    for index in range(6):
        if section + 3 > len(data):
            raise ImportError(f"{scene} MAN section {index} offset exceeds decoded payload")
        section_offsets.append(section)
        length = _u24(data, section)
        section += 3 + length
        if section > len(data):
            raise ImportError(f"{scene} MAN section {index} is truncated")
    absolute_records = [data_region + offset for offset in offsets]
    p1_base = counts[0]
    actors = []
    for record_index in range(1, counts[1]):
        absolute = absolute_records[p1_base + record_index]
        bounds = [candidate for candidate in absolute_records + section_offsets + [len(data)] if candidate > absolute]
        end = min(bounds) if bounds else len(data)
        if absolute >= len(data):
            raise ImportError(f"{scene} MAN record {record_index} exceeds decoded payload bounds")
        local_count = data[absolute]
        header = absolute + 1 + local_count * 2
        if header + 4 > end:
            raise ImportError(f"{scene} MAN record {record_index} placement header exceeds record bounds")
        model_index, animation_id, bx, bz = data[header : header + 4]
        position = lambda value: (value & 0x7F) * 128 + (128 if value & 0x80 else 64)
        actors.append(
            ManActor(
                record_index,
                absolute,
                end - absolute,
                local_count,
                model_index,
                animation_id,
                bx & 0x7F,
                bz & 0x7F,
                position(bx),
                position(bz),
            )
        )
    return ParsedMan(tuple(counts), tuple(actors))
