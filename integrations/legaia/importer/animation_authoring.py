"""Source-preserving writes to existing rigid animation channels.

Format evidence: pinned player_anm.rs and the existing animation decoder.
Edits retain the header, frame/channel counts, trailer and opaque high nibble.
This does not allocate records, infer timing or prove runtime model compatibility.
"""
from __future__ import annotations

import hashlib
import json

from .animation import decode_animation_record
from .core import ImportError

MAX_CHANNEL_EDITS = 4096


def patch_animation_channels(original: bytes, expected_sha256: str,
                             edits: list[dict]) -> tuple[bytes, list[dict]]:
    """Patch exact integer axes in a verified record; no quantization or wrapping.

    Each edit names frame_index and object_index, plus translation and/or
    rotation_psx axis dictionaries. Rotation uses 0..4080 in steps of16;
    translation uses signed twelve-bit actor-local units. Duplicate channels
    are rejected, avoiding order-dependent results.
    """
    if not isinstance(original, bytes):
        raise ImportError("animation source must be immutable bytes")
    if (not isinstance(expected_sha256, str) or
            hashlib.sha256(original).hexdigest() != expected_sha256):
        raise ImportError("animation record source hash does not match")
    decoded = decode_animation_record(original)
    if not isinstance(edits, list) or len(edits) > MAX_CHANNEL_EDITS:
        raise ImportError("animation channel edits exceed the bounded list limit")
    normalized, seen = [], set()
    for edit in edits:
        if (not isinstance(edit, dict) or
                set(edit) - {"frame_index", "object_index", "translation", "rotation_psx"} or
                not {"frame_index", "object_index"} <= set(edit) or
                not ({"translation", "rotation_psx"} & set(edit))):
            raise ImportError("animation edit requires frame/object indices and transform axes only")
        frame, obj = edit["frame_index"], edit["object_index"]
        if (type(frame) is not int or type(obj) is not int or
                not 0 <= frame < decoded["frame_count"] or
                not 0 <= obj < decoded["bone_count"]):
            raise ImportError("animation frame/object index is outside the source record")
        if (frame, obj) in seen:
            raise ImportError("duplicate animation frame/object edit")
        seen.add((frame, obj))
        for field in ("translation", "rotation_psx"):
            if field not in edit:
                continue
            axes = edit[field]
            if not isinstance(axes, dict) or not axes or set(axes) - set("xyz"):
                raise ImportError("animation transform requires nonempty X/Y/Z axes")
            for value in axes.values():
                if type(value) is not int:
                    raise ImportError("animation transform components must be exact integers")
                if field == "translation" and not -2048 <= value <= 2047:
                    raise ImportError("animation translation exceeds signed twelve-bit range")
                if field == "rotation_psx" and (not 0 <= value <= 4080 or value % 16):
                    raise ImportError("animation rotation must be 0..4080 in exact steps of16")
        normalized.append(edit)

    result, audit = bytearray(original), []
    for edit in sorted(normalized, key=lambda e: (e["frame_index"], e["object_index"])):
        frame, obj = edit["frame_index"], edit["object_index"]
        offset = 8 + (frame * decoded["bone_count"] + obj) * 8
        before = decoded["frames"][frame]["object_transforms"][obj]
        translation, rotation = list(before["translation"]), list(before["rotation_psx"])
        for field, values in (("translation", translation), ("rotation_psx", rotation)):
            for axis, value in sorted(edit.get(field, {}).items()):
                index = "xyz".index(axis)
                if value == values[index]:
                    continue
                audit.append({"frame_index": frame, "object_index": obj,
                              "field": f"{field}.{axis}", "before_value": values[index],
                              "after_value": value, "channel_byte_offset": offset})
                values[index] = value
        x, y, z = (value & 0xFFF for value in translation)
        result[offset:offset + 8] = bytes((x & 255, y & 255,
            (x >> 8) | ((y >> 8) << 4), z & 255,
            (original[offset + 4] & 0xF0) | (z >> 8),
            *(value // 16 for value in rotation)))
    changed = bytes(result)
    verified = decode_animation_record(changed)
    for row in audit:
        field, axis = row["field"].split(".")
        actual = verified["frames"][row["frame_index"]]["object_transforms"][row["object_index"]]
        if actual[field]["xyz".index(axis)] != row["after_value"]:
            raise ImportError("animation channel round-trip failed")
    return changed, audit


def replace_animation_record(original: bytes, expected_sha256: str,
                             replacement: bytes) -> tuple[bytes, list[dict]]:
    """Import channel values from an equal-layout record, retaining opaque bytes.

    This is a same-clip replacement, not topology/frame-count conversion or
    retargeting. Re-encoding against the original must reproduce every input
    byte before the replacement is accepted.
    """
    if not isinstance(original, bytes) or hashlib.sha256(original).hexdigest() != expected_sha256:
        raise ImportError("Animation replacement source hash does not match")
    if not isinstance(replacement, bytes) or len(replacement) != len(original):
        raise ImportError("Animation replacement must preserve source byte length")
    source = decode_animation_record(original)
    candidate = decode_animation_record(replacement)
    if any(source[key] != candidate[key] for key in ("frame_count", "bone_count")):
        raise ImportError("Animation replacement must preserve frame and object counts")
    edits = []
    for frame in candidate["frames"]:
        for channel in frame["object_transforms"]:
            before = source["frames"][frame["frame_index"]]["object_transforms"][channel["object_index"]]
            edit = {"frame_index": frame["frame_index"], "object_index": channel["object_index"]}
            for field in ("translation", "rotation_psx"):
                axes = {axis: value for axis, value, old in zip("xyz", channel[field], before[field]) if value != old}
                if axes:
                    edit[field] = axes
            if len(edit) > 2:
                edits.append(edit)
    changed, audit = patch_animation_channels(original, expected_sha256, edits)
    if changed != replacement:
        raise ImportError("Animation replacement changed header, padding, trailer or opaque channel bits")
    return changed, audit


def export_animation_channels(original: bytes) -> bytes:
    """Export complete existing channels with an immutable source binding."""
    decoded = decode_animation_record(original)
    if decoded['frame_count'] * decoded['bone_count'] > MAX_CHANNEL_EDITS:
        raise ImportError('Animation interchange exceeds the channel budget')
    channels = [{'frame_index': frame['frame_index'], 'object_index': channel['object_index'],
                 **{field: dict(zip('xyz', channel[field])) for field in ('translation', 'rotation_psx')}}
                for frame in decoded['frames'] for channel in frame['object_transforms']]
    return (json.dumps({'schema_version': 'legaia.animation-channels.v1',
                        'source_record_sha256': hashlib.sha256(original).hexdigest(),
                        'frame_count': decoded['frame_count'], 'object_count': decoded['bone_count'],
                        'channels': channels}, sort_keys=True, indent=2) + '\n').encode('utf-8')


def import_animation_channels(original: bytes, content: bytes) -> tuple[bytes, list[dict]]:
    """Import a complete bounded JSON clip; never infer missing channels/axes."""
    if not isinstance(content, bytes) or not 1 <= len(content) <= 4 * 1024 * 1024:
        raise ImportError('Animation channel JSON must contain at most 4 MiB')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    try:
        document = json.loads(content.decode('utf-8-sig'), object_pairs_hook=unique)
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise ImportError('Animation channels require valid unambiguous JSON') from exc
    fields = {'schema_version', 'source_record_sha256', 'frame_count', 'object_count', 'channels'}
    if not isinstance(document, dict) or set(document) != fields or document['schema_version'] != 'legaia.animation-channels.v1':
        raise ImportError('Unsupported animation channel document')
    decoded = decode_animation_record(original)
    for key, expected in (('frame_count', decoded['frame_count']), ('object_count', decoded['bone_count'])):
        if type(document[key]) is not int or document[key] != expected:
            raise ImportError('Animation channel document layout differs from source')
    channels = document['channels']
    if not isinstance(channels, list) or len(channels) != decoded['frame_count'] * decoded['bone_count']:
        raise ImportError('Animation channel document must contain every source channel')
    for channel in channels:
        if not isinstance(channel, dict) or set(channel) != {'frame_index','object_index','translation','rotation_psx'}:
            raise ImportError('Animation interchange requires full channel values')
        for field in ('translation', 'rotation_psx'):
            if not isinstance(channel[field], dict) or set(channel[field]) != set('xyz'):
                raise ImportError('Animation interchange requires all three axes')
    return patch_animation_channels(original, document['source_record_sha256'], channels)
