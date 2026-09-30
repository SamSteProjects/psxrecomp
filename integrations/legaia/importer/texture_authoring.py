"""Exact-layout user TIM replacements in verified scene texture carriers.

Uses textures.py's existing TIM/pack discovery. Pinned format evidence:
crates/tim/src/lib.rs, crates/prot/src/timpack.rs, docs/formats/{tim-pack,pack}.md.
Standalone word offsets include +4; descriptor-pack offsets do not. Source
headers and VRAM placement stay exact; only image and palette bytes may differ.
No disc writes, relocation, shared-bank discovery or runtime residency claims.
"""
from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
import hashlib
from typing import Any

from .core import ImportError, decompress_lzs, parse_scene_assets
from .pipeline import REFERENCE_COMMIT, _disc_context
from .textures import (MAX_ENTRY_BYTES, MAX_TIM_BYTES, TextureCatalog, Tim,
                       _pack_members, load_scene_texture_catalog, parse_tim)

MAX_EDITS = 128
MAX_EDIT_BYTES = 16 * 1024 * 1024
MAX_OVERLAY_BYTES = 32 * 1024 * 1024
LIMITATIONS = [
    "Replacement must preserve every TIM header, mode, dimension, image/CLUT VRAM rectangle and byte length.",
    "Only existing scene TIM image and palette payloads are replaceable; shared or conditional texture banks are outside this context.",
    "One source image can serve several materials; runtime residency, palette animation and gameplay appearance are not proved.",
    "Compressed packs must fit their original consumed stream span; following opaque bytes and other members remain unchanged.",
]


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _payload_ranges(tim: Tim) -> list[tuple[int, int]]:
    cursor, ranges = 8, []
    for block in (tim.clut, tim.image):
        if block is not None:
            end = cursor + 12 + len(block.data)
            ranges.append((cursor + 12, end))
            cursor = end
    return ranges


def _validate(original: bytes, replacement: bytes) -> dict:
    if not isinstance(replacement, bytes) or len(replacement) != len(original) or len(replacement) > MAX_TIM_BYTES:
        raise ImportError("replacement TIM must be immutable bytes of the exact original byte length")
    old, new = parse_tim(original), parse_tim(replacement)
    if old.byte_length != len(original) or new.byte_length != len(replacement):
        raise ImportError("replacement must contain exactly one TIM, without trailing payload")
    cursor = 0
    for start, end in _payload_ranges(old):
        if replacement[cursor:start] != original[cursor:start]:
            raise ImportError("replacement TIM headers, flags, dimensions and VRAM/CLUT layout must remain byte-exact")
        cursor = end
    if cursor != len(original):
        raise ImportError("TIM payload ranges do not cover the original structure")
    return {"format": "tim", "byte_length": len(original), "before_sha256": _sha(original),
            "after_sha256": _sha(replacement), "changed": replacement != original,
            "image_changed": old.image.data != new.image.data,
            "palette_changed": (old.clut.data if old.clut else None) != (new.clut.data if new.clut else None)}


def _encode_pack(original_stream: bytes, decoded: bytes) -> tuple[bytes, dict]:
    from .serialization import compress_lzs
    from .lzs_optimal import MAX_OPTIMAL_BYTES, compress_lzs_optimal
    encoded = compress_lzs(decoded)
    stats = {"original_encoded_size": len(original_stream), "decoded_size": len(decoded)}
    if len(encoded) > len(original_stream) and len(decoded) <= MAX_OPTIMAL_BYTES:
        stats.update(compression_strategy="bounded_optimal_lzs", greedy_encoded_size=len(encoded))
        encoded = compress_lzs_optimal(decoded)
    if len(encoded) > len(original_stream):
        raise ImportError(f"edited TIM pack requires {len(encoded)} compressed bytes but its original span holds {len(original_stream)}; relocation is unsupported")
    verified, consumed = decompress_lzs(encoded, len(decoded))
    if verified != decoded or consumed != len(encoded):
        raise ImportError("independent decoder rejected the edited TIM pack")
    replacement = encoded + original_stream[len(encoded):]
    if decompress_lzs(replacement, len(decoded))[0] != decoded:
        raise ImportError("padded TIM pack failed independent decode verification")
    stats["new_encoded_size"] = len(encoded)
    return replacement, stats


def patch_tim_palette_word(content: bytes, expected_sha256: str, palette_index: int,
                           entry_index: int, word: int) -> bytes:
    """Patch one existing indexed CLUT word; all headers/image bytes stay exact."""
    import struct
    if not isinstance(content, bytes) or _sha(content) != expected_sha256:
        raise ImportError('Texture changed since palette inspection; reopen the palette editor')
    tim = parse_tim(content)
    if tim.byte_length != len(content) or tim.bpp not in (4, 8) or tim.clut is None:
        raise ImportError('Palette editing requires one complete indexed 4/8-bpp TIM')
    count = 16 if tim.bpp == 4 else 256
    if (type(palette_index) is not int or palette_index < 0 or
            (palette_index + 1) * count * 2 > len(tim.clut.data) or
            type(entry_index) is not int or not 0 <= entry_index < count or
            type(word) is not int or not 0 <= word <= 65535):
        raise ImportError('Choose an existing palette entry and unsigned16 word')
    result = bytearray(content)
    struct.pack_into('<H', result, 20 + (palette_index * count + entry_index) * 2, word)
    replacement = bytes(result)
    _validate(content, replacement)
    return replacement


def inspect_tim_pixel_index(content: bytes, x: int, y: int) -> dict:
    if not isinstance(content, bytes):
        raise ImportError('Pixel inspection requires immutable TIM bytes')
    tim = parse_tim(content)
    if tim.byte_length != len(content) or tim.bpp not in (4, 8) or tim.clut is None or len(tim.clut.data) < (1 << tim.bpp) * 2:
        raise ImportError('Pixel-index editing requires one complete indexed 4/8-bpp TIM')
    if type(x) is not int or type(y) is not int or not 0 <= x < tim.width or not 0 <= y < tim.image.height:
        raise ImportError('Choose a pixel inside the source texture')
    per_byte = 8 // tim.bpp
    offset = 32 + len(tim.clut.data) + y * tim.image.width_words * 2 + x // per_byte
    shift = (x % per_byte) * tim.bpp
    return {'x': x, 'y': y, 'width': tim.width, 'height': tim.image.height,
            'bpp': tim.bpp, 'entry_count': 1 << tim.bpp, 'byte_offset': offset,
            'shift': shift, 'palette_entry': (content[offset] >> shift) & ((1 << tim.bpp) - 1)}


def patch_tim_pixel_index(content: bytes, expected_sha256: str, x: int, y: int,
                          palette_entry: int) -> bytes:
    if not isinstance(content, bytes) or _sha(content) != expected_sha256:
        raise ImportError('Texture changed since pixel inspection; reopen the pixel editor')
    pixel = inspect_tim_pixel_index(content, x, y)
    if type(palette_entry) is not int or not 0 <= palette_entry < pixel['entry_count']:
        raise ImportError('Pixel requires an existing encoded palette index')
    mask = (pixel['entry_count'] - 1) << pixel['shift']
    result = bytearray(content)
    offset = pixel['byte_offset']
    result[offset] = (result[offset] & (255 ^ mask)) | (palette_entry << pixel['shift'])
    replacement = bytes(result)
    _validate(content, replacement)
    return replacement


def texture_payload_changes(source: bytes, candidate: bytes) -> dict:
    """Exact payload differences, with bounded detail and complete counts."""
    import struct
    _validate(source,candidate)
    old,new = parse_tim(source),parse_tim(candidate)
    details,words,pixels,image_bytes = [],0,0,0
    if old.clut:
        for index,(before,after) in enumerate(zip(struct.iter_unpack('<H',old.clut.data),struct.iter_unpack('<H',new.clut.data))):
            if before == after:
                continue
            words += 1
            if len(details) < 256:
                details.append({'kind':'palette_word','word_index':index,'before':before[0],'after':after[0]})
    for index,(before,after) in enumerate(zip(old.image.data,new.image.data)):
        if before == after:
            continue
        image_bytes += 1
        if old.bpp in (4,8):
            mask = (1 << old.bpp)-1
            for lane,shift in enumerate(range(0,8,old.bpp)):
                a,b = (before >> shift)&mask,(after >> shift)&mask
                if a == b:
                    continue
                pixels += 1
                position = index*(8//old.bpp)+lane
                if len(details) < 256:
                    details.append({'kind':'pixel_index','x':position%old.width,'y':position//old.width,'before':a,'after':b})
        elif len(details) < 256:
            details.append({'kind':'image_byte','image_byte_index':index,'before':before,'after':after})
    total = words + (pixels if old.bpp in (4,8) else image_bytes)
    return {'palette_words_changed':words,'pixel_indices_changed':pixels if old.bpp in (4,8) else None,
            'image_bytes_changed':image_bytes,'total_change_count':total,'changes':details,
            'changes_truncated':total > len(details)}


class TextureAuthoringContext:
    """Identity-bound catalog snapshot; carriers are reread per operation.

    Constructor inputs are private decoder products. Public callers use
    load_texture_authoring_context and provide IDs/bytes, never source locators.
    """
    def __init__(self, disc: Any, scene: str, catalog: TextureCatalog):
        self.disc, self.scene, self._digest = disc, scene, catalog.disc_sha256
        self._items = {source["semantic_id"]: (tim, deepcopy(source)) for tim, source in catalog.textures}
        if len(self._items) != len(catalog.textures) or catalog.scene != scene:
            raise ImportError("texture authoring catalog contains ambiguous identifiers or scene identity")

    @contextmanager
    def _archive(self):
        with _disc_context(self.disc) as (_, digest, _, archive):
            if digest != self._digest:
                raise ImportError("texture authoring source disc changed since catalog verification")
            yield archive

    def _item(self, identifier: str) -> tuple[Tim, dict]:
        if not isinstance(identifier, str) or identifier not in self._items:
            raise ImportError("texture identifier is not in the verified scene catalog")
        return self._items[identifier]

    def _carrier(self, archive, source: dict) -> dict:
        entry = archive.entry(source["prot_entry_index"])
        if entry.size_sectors * 2048 > MAX_ENTRY_BYTES:
            raise ImportError("texture carrier exceeds bounded entry size")
        raw = archive.read_entry(entry, extended=True)
        location = (archive.node.extent_lba + entry.start_lba) * 2048
        descriptor_index = source.get("descriptor_index")
        if descriptor_index is None:
            if source["byte_coordinate_space"] != "prot_entry":
                raise ImportError("standalone texture source coordinate space disagrees")
            return {"kind": "raw_tim_pack", "decoded": raw, "stream": None, "offset": location,
                    "ranges": _pack_members(raw, True), "stream_offset": 0,
                    "source": {"prot_entry_index": entry.index}}
        table = parse_scene_assets(archive.read_entry(entry, extended=False), entry.index)
        if table is None:
            raise ImportError("texture source has no verified entry-head descriptor table")
        descriptor = next((d for d in table.descriptors if d.index == descriptor_index), None)
        if (descriptor is None or descriptor.type_byte != 1 or not descriptor.size or
                source["byte_coordinate_space"] != "decoded_lzs_descriptor" or
                descriptor.data_offset != source["compressed_stream_offset"]):
            raise ImportError("texture descriptor differs from its verified catalog locator")
        if sum(d.size > 0 and d.data_offset == descriptor.data_offset for d in table.descriptors) != 1:
            raise ImportError("texture descriptor aliases another nonempty resource")
        start = descriptor.data_offset
        ceiling = min([d.data_offset for d in table.descriptors if d.data_offset > start] + [len(raw)])
        if not 8 + len(table.descriptors) * 8 <= start < ceiling <= len(raw):
            raise ImportError("texture compressed stream exceeds descriptor boundaries")
        decoded, consumed = decompress_lzs(raw[start:ceiling], descriptor.size)
        return {"kind": "lzs_descriptor_tim_pack", "decoded": decoded,
                "stream": raw[start:start + consumed], "offset": location + start,
                "ranges": _pack_members(decoded, False), "stream_offset": start,
                "source": {"prot_entry_index": entry.index, "descriptor_index": descriptor.index,
                           "compressed_stream_offset": start, "compressed_bytes_consumed": consumed}}

    def _original(self, identifier: str, carrier: dict) -> bytes:
        expected, source = self._item(identifier)
        slot = source["pack_slot"]
        if type(slot) is not int or not 0 <= slot < len(carrier["ranges"]):
            raise ImportError("texture pack slot is outside verified source bounds")
        start, end = carrier["ranges"][slot]
        if start != source["byte_offset"] or start + source["byte_length"] > end:
            raise ImportError("texture pack member differs from its verified source interval")
        original = carrier["decoded"][start:start + source["byte_length"]]
        if parse_tim(original) != expected or len(original) != expected.byte_length:
            raise ImportError("texture source bytes differ from the verified catalog TIM")
        return original

    def _source(self, identifier: str) -> dict:
        return dict(deepcopy(self._item(identifier)[1]), disc={"sha256": self._digest, "serial": "SCUS-94254"},
                    iso_file="PROT.DAT", reference_commit=REFERENCE_COMMIT)

    def options(self, identifier: str) -> dict:
        tim, source = self._item(identifier)
        palettes = len(tim.clut.data) // ((1 << tim.bpp) * 2) if tim.clut and tim.bpp <= 8 else 0
        result = {"asset_id": identifier, "format": "tim", "source_record": self._source(identifier),
                  "byte_length": tim.byte_length, "width": tim.width, "height": tim.image.height,
                  "bpp": tim.bpp, "palette_count": palettes, "limitations": list(LIMITATIONS)}
        try:
            with self._archive() as archive:
                carrier = self._carrier(archive, source)
                original = self._original(identifier, carrier)
                result.update(supported=True, reason=None, original_sha256=_sha(original),
                              carrier={"kind": carrier["kind"], **carrier["source"],
                                       "decoded_size": len(carrier["decoded"]),
                                       "original_encoded_size": len(carrier["stream"]) if carrier["stream"] is not None else None})
        except ImportError as exc:
            result.update(supported=False, reason=str(exc), carrier=None)
        return result

    def original_tim(self, identifier: str) -> bytes:
        _, source = self._item(identifier)
        with self._archive() as archive:
            return self._original(identifier, self._carrier(archive, source))

    def validate_replacement(self, identifier: str, replacement: bytes) -> dict:
        return dict(_validate(self.original_tim(identifier), replacement), asset_id=identifier,
                    source_record=self._source(identifier), limitations=list(LIMITATIONS))

    def patch(self, edits: dict[str, bytes]) -> tuple[list[dict], list[dict]]:
        if not isinstance(edits, dict) or len(edits) > MAX_EDITS:
            raise ImportError("texture replacement edit count exceeds bounded limit")
        groups, supplied = {}, 0
        for identifier, replacement in edits.items():
            _, source = self._item(identifier)
            if not isinstance(replacement, bytes) or len(replacement) > MAX_TIM_BYTES:
                raise ImportError("texture replacement requires bounded immutable TIM bytes")
            supplied += len(replacement)
            if supplied > MAX_EDIT_BYTES:
                raise ImportError("texture replacement payload exceeds 16 MiB edit budget")
            key = (source["prot_entry_index"], source.get("descriptor_index", -1))
            groups.setdefault(key, []).append(identifier)
        overlays, audit, overlay_size = [], [], 0
        with self._archive() as archive:
            for key, identifiers in sorted(groups.items()):
                carrier = self._carrier(archive, self._item(identifiers[0])[1])
                changed = bytearray(carrier["decoded"]) if carrier["stream"] is not None else None
                group_audit = []
                for identifier in sorted(identifiers):
                    original = self._original(identifier, carrier)
                    replacement = edits[identifier]
                    info = _validate(original, replacement)
                    if not info["changed"]:
                        continue
                    source = self._source(identifier)
                    record = dict(info, semantic_id=identifier, source_record=source,
                                  scope="TIM-image-and-palette-payload-only",
                                  payload_changes=texture_payload_changes(original,replacement))
                    group_audit.append(record)
                    if changed is not None:
                        offset = source["byte_offset"]
                        changed[offset:offset + len(replacement)] = replacement
                    else:
                        overlays.append({"scene": self.scene, "offset": carrier["offset"] + source["byte_offset"],
                                         "size": len(replacement), "payload": replacement,
                                         "sha256": info["after_sha256"], "expected_sha256": info["before_sha256"],
                                         "carrier_kind": carrier["kind"], "source_record": source})
                        overlay_size += len(replacement)
                if group_audit and changed is not None:
                    decoded = bytes(changed)
                    replacement, stats = _encode_pack(carrier["stream"], decoded)
                    # Re-extract requested members from independently decoded bytes.
                    check = dict(carrier, decoded=decompress_lzs(replacement, len(decoded))[0])
                    for record in group_audit:
                        offset, size = record["source_record"]["byte_offset"], record["byte_length"]
                        if check["decoded"][offset:offset + size] != edits[record["semantic_id"]]:
                            raise ImportError("encoded texture member failed exact replacement verification")
                    overlays.append({"scene": self.scene, "offset": carrier["offset"], "size": len(replacement),
                                     "payload": replacement, "sha256": _sha(replacement),
                                     "expected_sha256": _sha(carrier["stream"]), "carrier_kind": carrier["kind"],
                                     "source_record": dict(carrier["source"], disc={"sha256": self._digest}),
                                     "decoded_before_sha256": _sha(carrier["decoded"]), "decoded_after_sha256": _sha(decoded),
                                     **stats})
                    overlay_size += len(replacement)
                audit.extend(group_audit)
                if overlay_size > MAX_OVERLAY_BYTES:
                    raise ImportError("texture replacement overlays exceed 32 MiB budget")
        overlays.sort(key=lambda o: o["offset"])
        if any(a["offset"] + a["size"] > b["offset"] for a, b in zip(overlays, overlays[1:])):
            raise ImportError("texture replacement carrier spans overlap; ambiguous aliases are unsupported")
        return overlays, sorted(audit, key=lambda row: row["semantic_id"])


def load_texture_authoring_context(disc: Any, scene: str) -> TextureAuthoringContext:
    with _disc_context(disc):
        return TextureAuthoringContext(disc, scene, load_scene_texture_catalog(disc, scene))
