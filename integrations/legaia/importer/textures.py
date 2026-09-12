"""Bounded TIM previews and evidence-preserving field texture discovery.

Independent implementation; reference pin is pipeline.REFERENCE_COMMIT.
Format evidence: crates/tim/{lib,vram}.rs, crates/prot/src/timpack.rs,
docs/formats/{tim-pack,pack,scene-bundles}.md and
crates/engine-core/src/scene_resources.rs in Andrew's pinned repository.
The field uploader FUN_800198E0 flattens CLUT blocks into a single strip.
Static address agreement is not proof of runtime residency or upload order.
Texture bytes are private disc-derived output, never metadata fixtures.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import struct
from typing import Any

from .core import (ImportError, decompress_lzs, global_special_tmd_pool,
                   is_scene_tmd_stream, parse_lzs_sections, parse_scene_assets)
from .pipeline import (REFERENCE_COMMIT, _bounded_scene_range, _disc_context,
                       _model_source_locator)

MAX_TIM_BYTES = 2 * 1024 * 1024
MAX_CATALOG_BYTES = 16 * 1024 * 1024
MAX_TEXTURES = 1024
MAX_ENTRY_BYTES = 8 * 1024 * 1024
_FIELD_PARTY_IDS = tuple(f"asset://legaia/models/global-special/{i:04x}" for i in range(0xF0, 0xF3))


@dataclass(frozen=True)
class TimBlock:
    x: int
    y: int
    width_words: int
    height: int
    data: bytes

    def metadata(self) -> dict[str, int]:
        return dict(x=self.x, y=self.y, width_words=self.width_words, height=self.height)


@dataclass(frozen=True)
class Tim:
    bpp: int
    image: TimBlock
    clut: TimBlock | None
    byte_length: int
    flags: int = 0

    @property
    def width(self) -> int:
        return self.image.width_words * 16 // self.bpp


def parse_tim(data: bytes) -> Tim:
    """Parse one TIM prefix; reject unknown modes/flags and malformed blocks.

    CLUT rows may extend beyond VRAM as declared: the field uploader flattens
    them. Both declared dimensions and payload are bounded here; upload bounds
    are checked separately when constructing the material address view.
    """
    if len(data) < 8:
        raise ImportError("truncated TIM header")
    magic, flags = struct.unpack_from("<II", data)
    # Pinned lib.rs's strict_rejects_reserved_flag_bits test documents the
    # retail 0x00010008 variant. Preserve that opaque word, accept no other
    # reserved flags, and interpret only the documented low mode bits.
    if magic != 0x10 or (flags & ~0xF and flags != 0x10008) or (flags & 7) > 3:
        raise ImportError("unsupported TIM magic, reserved flags or mixed pixel mode")
    bpp = (4, 8, 16, 24)[flags & 7]
    pos = 8

    def block(is_clut: bool) -> TimBlock:
        nonlocal pos
        if pos + 12 > len(data):
            raise ImportError("truncated TIM block header")
        size, x, y, w, h = struct.unpack_from("<I4H", data, pos)
        if not (0 < w <= 1024 and 0 < h <= 512 and x < 1024 and y < 512):
            raise ImportError("TIM block dimensions exceed bounded VRAM coordinates")
        if size != 12 + w * h * 2 or pos + size > min(len(data), MAX_TIM_BYTES):
            raise ImportError("TIM block length does not match its dimensions or available bytes")
        if not is_clut and (x + w > 1024 or y + h > 512):
            raise ImportError("TIM image rectangle extends outside VRAM")
        result = TimBlock(x, y, w, h, data[pos + 12:pos + size])
        pos += size
        return result

    clut = block(True) if flags & 8 else None
    image = block(False)
    if bpp == 24 and image.width_words * 2 % 3:
        raise ImportError("unsupported 24-bpp TIM row padding: width must contain whole RGB pixels")
    return Tim(bpp, image, clut, pos, flags)


def _rgba(word: int) -> bytes:
    values = [(word >> shift) & 31 for shift in (0, 5, 10)]
    return bytes([(v << 3) | (v >> 2) for v in values] + [0 if word == 0 else 255])


def decode_tim(tim: Tim | bytes, palette_index: int = 0) -> dict[str, Any]:
    """Decode TIM-local pixels; STP is separate from transparent-zero alpha.

    Returns width, height, rgba (bytes), stp (one byte per pixel). Indexed TIMs
    lacking their own palette need associate_material's cross-TIM address view.
    """
    if isinstance(tim, bytes):
        tim = parse_tim(tim)
    if not isinstance(tim, Tim) or tim.bpp not in (4, 8, 16, 24):
        raise ImportError("decode requires a supported parsed TIM")
    for part in (tim.image, tim.clut):
        if part is not None and (not 0 < part.width_words <= 1024 or not 0 < part.height <= 512
                                 or len(part.data) != part.width_words * part.height * 2):
            raise ImportError("TIM block dimensions and payload do not agree")
    if tim.bpp == 24 and tim.image.width_words * 2 % 3:
        raise ImportError("unsupported 24-bpp TIM row padding")
    if type(palette_index) is not int or palette_index < 0:
        raise ImportError("palette index must be a non-negative integer")
    palette = None
    if tim.bpp <= 8:
        count = 1 << tim.bpp
        if tim.clut is None or (palette_index + 1) * count * 2 > len(tim.clut.data):
            raise ImportError("indexed TIM has no complete requested palette")
        palette = struct.unpack_from(f"<{count}H", tim.clut.data, palette_index * count * 2)
    elif palette_index:
        raise ImportError("direct-color TIM has no palette index")
    rgba, stp = bytearray(), bytearray()
    if tim.bpp == 24:
        for i in range(0, len(tim.image.data), 3):
            rgba.extend(tim.image.data[i:i + 3] + b"\xff")
            stp.append(0)
    else:
        for (raw,) in struct.iter_unpack("<H", tim.image.data):
            for shift in range(0, 16, tim.bpp):
                word = palette[(raw >> shift) & ((1 << tim.bpp) - 1)] if palette else raw
                rgba.extend(_rgba(word))
                stp.append(word >> 15)
    return dict(width=tim.width, height=tim.image.height, rgba=bytes(rgba), stp=bytes(stp))


@dataclass
class TextureCatalog:
    scene: str
    disc_sha256: str
    textures: list[tuple[Tim, dict[str, Any]]] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)

    def metadata(self) -> dict[str, Any]:
        return {
            "schema_version": "legaia.scene-textures.v1", "scene": self.scene,
            "disc_sha256": self.disc_sha256, "reference_commit": REFERENCE_COMMIT,
            "association_evidence": "static_vram_addresses_not_runtime_residency",
            "clut_upload": "flat_strip_FUN_800198E0",
            "textures": [dict(source, bpp=tim.bpp, flags=tim.flags, width=tim.width,
                              height=tim.image.height, image=tim.image.metadata(),
                              clut=tim.clut.metadata() if tim.clut else None)
                         for tim, source in self.textures],
            "diagnostics": list(self.diagnostics),
        }


def _pack_members(data: bytes, standalone: bool) -> list[tuple[int, int]]:
    base = 4 if standalone else 0
    if len(data) < base + 8:
        raise ImportError("truncated TIM pack")
    if standalone and (data[3] != 1 or data[2] >= 0x10):
        raise ImportError("unsupported standalone TIM pack signature")
    count = struct.unpack_from("<I", data, base)[0]
    end = base + 4 + count * 4
    if not 1 <= count <= MAX_TEXTURES or end > len(data):
        raise ImportError("TIM pack count/table exceeds bounds")
    offsets = [base + 4 * v for v in struct.unpack_from(f"<{count}I", data, base + 4)]
    if offsets[0] < end or any(a >= b for a, b in zip(offsets, offsets[1:])) or offsets[-1] >= len(data):
        raise ImportError("TIM pack offsets are non-monotonic or out of bounds")
    return list(zip(offsets, offsets[1:] + [len(data)]))


def load_scene_texture_catalog(disc: Any, scene: str = "town01") -> TextureCatalog:
    """Discover structural scene packs, with verified source identity and limits.

    No arbitrary magic sweep, shared character-bank upload, PCH sidecar sweep,
    battle stream, or world-map special uploader is guessed. Unrecognized
    carriers remain outside this explicitly partial catalog.
    """
    with _disc_context(disc) as (_, digest, mapping, archive):
        start, end = _bounded_scene_range(archive, mapping, scene)
        catalog = TextureCatalog(scene, digest)
        catalog.diagnostics.append("Partial scene catalog: shared UI/field-character uploads, runtime CLUT animation, texture windows and conditional PCH resources are unsupported.")
        total = 0

        def add_pack(data: bytes, standalone: bool, locator: dict[str, Any]) -> None:
            nonlocal total
            for slot, (a, b) in enumerate(_pack_members(data, standalone)):
                if data[a:a + 4] != b"\x10\0\0\0":
                    catalog.diagnostics.append(f"entry {locator['prot_entry_index']} pack member {slot}: unsupported non-TIM member")
                    continue
                try:
                    tim = parse_tim(data[a:b])
                except ImportError as exc:
                    catalog.diagnostics.append(f"entry {locator['prot_entry_index']} pack member {slot}: {exc}")
                    continue
                total += tim.byte_length
                if total > MAX_CATALOG_BYTES or len(catalog.textures) >= MAX_TEXTURES:
                    raise ImportError("scene texture catalog exceeds byte/count limit")
                source = dict(locator, pack_slot=slot, byte_offset=a, byte_length=tim.byte_length)
                source["semantic_id"] = f"texture://{scene}/{locator['prot_entry_index']}/{locator.get('descriptor_index', 'raw')}/{slot}"
                catalog.textures.append((tim, source))

        for index in range(start, end):
            entry = archive.entry(index)
            if entry.size_sectors * 2048 > MAX_ENTRY_BYTES:
                catalog.diagnostics.append(f"entry {index}: exceeds texture source size limit")
                continue
            indexed = archive.read_entry(entry, extended=False)
            if is_scene_tmd_stream(indexed):
                continue
            locator = dict(prot_entry_index=index, byte_coordinate_space="prot_entry")
            if len(indexed) >= 8 and indexed[3] == 1 and indexed[2] < 0x10:
                try:
                    # Like scene descriptors, the TIM pack can continue past
                    # the indexed sub-region into its extended entry footprint.
                    add_pack(archive.read_entry(entry, extended=True), True, locator)
                except ImportError as exc:
                    if "catalog exceeds" in str(exc):
                        raise
                    catalog.diagnostics.append(f"entry {index}: {exc}")
                continue
            # Require a table at the entry head. PCH/embedded carriers need a
            # separate dispatch proof; sector scanning risks adjacent-file data.
            bundle = parse_scene_assets(indexed, index)
            if bundle is None:
                continue
            for descriptor in bundle.descriptors:
                if descriptor.type_byte != 1 or descriptor.size == 0:
                    continue
                raw = archive.read_entry(entry, extended=True)
                try:
                    ceiling = min([d.data_offset for d in bundle.descriptors
                                   if d.data_offset > descriptor.data_offset] + [len(raw)])
                    if (sum(d.size > 0 and d.data_offset == descriptor.data_offset for d in bundle.descriptors) != 1
                            or not 8 + len(bundle.descriptors) * 8 <= descriptor.data_offset < ceiling <= len(raw)):
                        raise ImportError('TIM descriptor aliases or exceeds its resource span')
                    decoded, _ = decompress_lzs(raw[descriptor.data_offset:ceiling], descriptor.size)
                    add_pack(decoded, False, dict(locator, descriptor_index=descriptor.index,
                             compressed_stream_offset=descriptor.data_offset,
                             byte_coordinate_space="decoded_lzs_descriptor"))
                except ImportError as exc:
                    if "catalog exceeds" in str(exc):
                        raise
                    catalog.diagnostics.append(f"entry {index} descriptor {descriptor.index}: {exc}")
        return catalog


def uses_field_party_textures(asset: dict[str, Any]) -> bool:
    """Cheap routing hint only; loading revalidates the complete disc locator."""
    return isinstance(asset, dict) and asset.get("semantic_id") in _FIELD_PARTY_IDS


def _field_party_catalog(raw: bytes, digest: str) -> TextureCatalog:
    """Decode only the pinned player.lzs section-2 loader path.

    FUN_8001E890 sends these pack members through FUN_800198E0. Images use
    their declared rectangles and CLUTs use flat strips with no STP forcing.
    No scene palette or conditional resource is mixed into this address view.
    """
    if len(raw) > MAX_ENTRY_BYTES:
        raise ImportError("field texture source exceeds byte limit")
    sections = parse_lzs_sections(raw)
    if len(sections) != 3:
        raise ImportError("unsupported field texture container descriptor count")
    section = sections[2]
    data, consumed = decompress_lzs(raw[section.stream_offset:], section.decoded_size)
    ranges = _pack_members(data, False)
    if len(ranges) != 8:
        raise ImportError("field texture pack does not match pinned eight-member layout")
    catalog = TextureCatalog("global-field-party", digest)
    catalog.diagnostics.append("Pinned field player loader uploads only; live residency, equipment swaps, blend emulation and palette animation are not reconstructed.")
    total = 0
    for slot, (start, end) in enumerate(ranges):
        tim = parse_tim(data[start:end])
        if tim.clut is None or tim.bpp != 4:
            raise ImportError("unsupported field texture member mode: expected indexed 4-bpp TIM with CLUT")
        if tim.clut.x + tim.clut.width_words * tim.clut.height > 1024:
            raise ImportError("field texture CLUT strip extends outside VRAM")
        total += tim.byte_length
        if total > MAX_CATALOG_BYTES:
            raise ImportError("field texture catalog exceeds byte limit")
        catalog.textures.append((tim, {
            "semantic_id": f"texture://legaia/field-party/874/2/{slot}",
            "disc": {"sha256": digest, "serial": "SCUS-94254"}, "iso_file": "PROT.DAT",
            "prot_entry_index": 874, "container_section": 2, "pack_slot": slot,
            "compressed_stream_offset": section.stream_offset,
            "compressed_bytes_consumed": consumed, "byte_offset": start,
            "byte_length": tim.byte_length, "containing_size": len(data),
            "byte_coordinate_space": "decoded_lzs_section",
            "upload_evidence": "field_char_textures.rs:FUN_8001E890_to_FUN_800198E0",
            "force_stp": False,
        }))
    return catalog


def load_asset_texture_catalog(disc: Any, asset: dict[str, Any],
                               scene_catalog: TextureCatalog) -> TextureCatalog:
    """Select an evidenced upload scope without changing the scene catalog.

    F0/F1/F2 use the independently verified shared player texture bank. Other
    assets retain the caller's scene catalog. A routing ID alone is never
    sufficient to establish the shared-bank source association.
    """
    if not uses_field_party_textures(asset):
        if asset.get("source_record", {}).get("disc", {}).get("sha256") != scene_catalog.disc_sha256:
            raise ImportError("model and scene texture catalog disc provenance do not match")
        return scene_catalog
    slot = _FIELD_PARTY_IDS.index(asset["semantic_id"])
    with _disc_context(disc) as (_, digest, _, archive):
        record = global_special_tmd_pool(archive)[slot]
        if asset.get("source_record") != _model_source_locator(digest, "", record):
            raise ImportError("field texture model provenance does not match the verified global pack record")
        raw = archive.read_entry(archive.entry(874), extended=True)
        return _field_party_catalog(raw, digest)


def associate_material(catalog: TextureCatalog, material: dict[str, Any],
                       uv_bounds: tuple[int, int, int, int] = (0, 0, 255, 255)) -> dict[str, Any]:
    """Resolve an inclusive UV crop against unique catalog word values.

    Output status is address_match, missing, ambiguous or unsupported. Only
    address_match includes rgba/stp bytes. These are a static preview, not a
    claim about runtime upload order, palette animation or blend results.
    """
    result: dict[str, Any] = dict(status="unsupported", evidence="static_vram_addresses_not_runtime_residency")
    if not material.get("textured"):
        return dict(result, reason="material is untextured")
    page, clut = material.get("tpage"), material.get("clut")
    if type(page) is not int or not 0 <= page <= 0xFFFF or type(clut) is not int or not 0 <= clut <= 0x7FFF:
        return dict(result, reason="material requires raw 16-bit tpage and CLUT values")
    if page & ~0x1FF or (page >> 7) & 3 == 3:
        return dict(result, reason="unsupported texture page bits or reserved pixel mode")
    if len(uv_bounds) != 4 or any(type(v) is not int or not 0 <= v <= 255 for v in uv_bounds):
        raise ImportError("UV bounds must contain four integer bytes")
    u0, v0, u1, v1 = uv_bounds
    if u0 > u1 or v0 > v1:
        raise ImportError("UV bounds must be ordered, inclusive, without wrapping")
    bpp = (4, 8, 16)[(page >> 7) & 3]
    page_x, page_y = (page & 15) * 64, ((page >> 4) & 1) * 256
    cx, cy = (clut & 63) * 16, (clut >> 6) & 511
    used: set[str] = set()
    blocks = []
    for tim, source in catalog.textures:
        blocks.append((tim.image, source["semantic_id"], False))
        if tim.clut:
            c = tim.clut
            if c.x + c.width_words * c.height > 1024:
                return dict(result, reason="catalog includes unsupported CLUT strip clipping")
            blocks.append((c, source["semantic_id"], True))
    cache: dict[tuple[int, int], int] = {}

    def word(x: int, y: int) -> int:
        if (x, y) in cache:
            return cache[x, y]
        values: set[int] = set()
        for block, identity, flat in blocks:
            w, h = (block.width_words * block.height, 1) if flat else (block.width_words, block.height)
            if block.x <= x < block.x + w and block.y <= y < block.y + h:
                offset = ((y - block.y) * w + x - block.x) * 2
                values.add(struct.unpack_from("<H", block.data, offset)[0])
                used.add(identity)
        if not values:
            raise LookupError(f"missing VRAM word ({x}, {y})")
        if len(values) > 1:
            raise ValueError(f"conflicting candidate uploads at VRAM word ({x}, {y})")
        cache[x, y] = values.pop()
        return cache[x, y]

    rgba, stp = bytearray(), bytearray()
    try:
        for v in range(v0, v1 + 1):
            for u in range(u0, u1 + 1):
                raw = word(page_x + u * bpp // 16, page_y + v)
                if bpp < 16:
                    index = (raw >> ((u % (16 // bpp)) * bpp)) & ((1 << bpp) - 1)
                    raw = word(cx + index, cy)
                rgba.extend(_rgba(raw))
                stp.append(raw >> 15)
    except LookupError as exc:
        return dict(result, status="missing", reason=str(exc), source_ids=sorted(used))
    except ValueError as exc:
        return dict(result, status="ambiguous", reason=str(exc), source_ids=sorted(used))
    return dict(result, status="address_match", width=u1-u0+1, height=v1-v0+1,
                uv_origin=[u0, v0], rgba=bytes(rgba), stp=bytes(stp),
                source_ids=sorted(used), semi_transparent=bool(material.get("semi_transparent")))
