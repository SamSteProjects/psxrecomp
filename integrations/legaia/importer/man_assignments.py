"""Bounded MAN initial model/animation donor assignments, never live writes.

Evidence: AndrewAltimit/legend-of-legaia-re at pipeline.REFERENCE_COMMIT,
asset/man_section.rs ActorPlacement and web-viewer/field_npc.rs. See
docs/legaia-sdk/man-assignment-authoring.md for restrictions and non-claims.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
from typing import Any

from .animation import animation_record_ranges, decode_animation_record
from .core import ImportError, decompress_lzs, find_scene_bundle, parse_man, scene_tmd_pool
from .pipeline import REFERENCE_COMMIT, _bounded_scene_range, _disc_context
from .serialization import compress_lzs

MAX_MAN_BYTES = 4 * 1024 * 1024
MAX_ACTORS = 512
LIMITATIONS = [
    "Initial MAN header assignment only; scripts can later override model and animation.",
    "An observed donor pair and matching object/channel count do not prove script or NPC behavior compatibility.",
    "No anatomical skeleton equivalence, collision dimensions, playback cadence or visual suitability is inferred.",
    "Global banks, zero-animation assignments, new models/clips, and native spawning are unsupported.",
]


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class ManAssignmentContext:
    """Request-scoped private source snapshot. Use load_man_assignment_context.

    Constructor inputs are internal decoder products, not client metadata.
    Neither patch nor serialize writes to the disc, project or filesystem.
    """
    def __init__(self, scene: str, man: bytes, stream: bytes, model_counts: dict[int, int],
                 anm: bytes, source: dict[str, Any]):
        if not isinstance(man, bytes) or not 0 < len(man) <= MAX_MAN_BYTES:
            raise ImportError("MAN source must be bounded immutable decoded bytes")
        parsed = parse_man(man, scene)
        if len(parsed.actors) > MAX_ACTORS:
            raise ImportError("MAN actor count exceeds assignment bound")
        decoded, consumed = decompress_lzs(stream, len(man))
        if decoded != man:
            raise ImportError("MAN encoded and decoded sources disagree")
        if (not isinstance(model_counts, dict) or len(model_counts) > 240 or
                any(type(k) is not int or not 0 <= k < 240 or
                    type(v) is not int or not 1 <= v <= 1024 for k, v in model_counts.items())):
            raise ImportError("scene model bank has invalid indices or object counts")
        self.scene = scene
        self._man, self._stream, self._anm = man, bytes(stream[:consumed]), bytes(anm)
        self._models = dict(model_counts)
        self._actors = {a.record_index: a for a in parsed.actors}
        self._ranges = animation_record_ranges(anm)
        self._animation_counts: dict[int, int] = {}
        self._source = deepcopy(source)
        total = sum(parsed.partition_counts)
        data_region = 0x2B + total * 3
        record_starts = Counter(data_region + int.from_bytes(man[0x2B+i*3:0x2E+i*3], "little")
                                for i in range(total))
        self._unique = {a.record_index for a in parsed.actors if record_starts[a.byte_offset] == 1}
        self._pairs: dict[tuple[int, int], list[int]] = {}
        for actor in parsed.actors:
            if actor.record_index in self._unique:
                self._pairs.setdefault((actor.model_index, actor.animation_id), []).append(actor.record_index)

    def provenance(self) -> dict[str, Any]:
        return dict(deepcopy(self._source), scene=self.scene, reference_commit=REFERENCE_COMMIT,
                    decoded_man_sha256=_sha(self._man), decoded_anm_sha256=_sha(self._anm),
                    encoded_man_sha256=_sha(self._stream), decoded_man_size=len(self._man),
                    model_object_counts=dict(self._models), limitations=list(LIMITATIONS))

    def _actor(self, record: int):
        if type(record) is not int or record not in self._actors or record not in self._unique:
            raise ImportError("assignment requires an existing, non-aliased partition-1 actor record")
        return self._actors[record]

    def _pair(self, model: int, animation: int) -> int:
        if type(model) is not int or not 0 <= model < 0xF0 or model not in self._models:
            raise ImportError("assignment model must resolve in the existing scene TMD bank; global banks are unsupported")
        if type(animation) is not int or not 1 <= animation <= 255 or animation > len(self._ranges):
            raise ImportError("assignment animation must be a nonzero existing scene ANM record plus one")
        if animation not in self._animation_counts:
            start, end = self._ranges[animation - 1]
            decoded = decode_animation_record(self._anm[start:end])
            self._animation_counts[animation] = decoded["bone_count"]
        if self._animation_counts[animation] != self._models[model]:
            raise ImportError("animation channel count does not match model object count")
        return self._models[model]

    def _validate(self, record: int, model: int, animation: int) -> list[int]:
        actor = self._actor(record)
        source_count = self._pair(actor.model_index, actor.animation_id)
        if self._pair(model, animation) != source_count:
            raise ImportError("donor and original actor must have the same object/channel count")
        donors = self._pairs.get((model, animation))
        if not donors:
            raise ImportError("model/animation combination has no evidenced donor in this MAN")
        return list(donors)

    def options(self, record: int) -> dict[str, Any]:
        """List only supported initial pairs, retaining explicit unavailable reasons."""
        actor = self._actor(record)
        try:
            self._pair(actor.model_index, actor.animation_id)
        except ImportError as exc:
            return dict(supported=False, reason=str(exc), pairs=[], limitations=list(LIMITATIONS))
        pairs = []
        for model, animation in sorted(self._pairs):
            try:
                donors = self._validate(record, model, animation)
            except ImportError:
                continue
            pairs.append(dict(model_index=model, animation_id=animation, donor_records=donors,
                              unchanged=(model, animation) == (actor.model_index, actor.animation_id)))
        return dict(supported=True, reason=None, pairs=pairs, limitations=list(LIMITATIONS))

    def patch(self, edits: dict[int, dict[str, int]], *, original: bytes | None = None
              ) -> tuple[bytes, list[dict[str, Any]]]:
        """Return verified baseline with only model/animation bytes changed.

        Optional original is an exact source guard, not permission to accept
        arbitrary edited buffers. Compose position patches on this result later.
        """
        if original is not None and original != self._man:
            raise ImportError("MAN assignment source differs from the verified baseline")
        if not isinstance(edits, dict) or len(edits) > MAX_ACTORS:
            raise ImportError("invalid or excessive MAN assignment edit set")
        staged = []
        for record, fields in edits.items():
            actor = self._actor(record)
            if not isinstance(fields, dict) or not fields or set(fields) - {"model_index", "animation_id"}:
                raise ImportError("assignment supports only model_index and animation_id")
            model = fields.get("model_index", actor.model_index)
            animation = fields.get("animation_id", actor.animation_id)
            donors = self._validate(record, model, animation)
            staged.append((record, actor, fields, model, animation, donors))
        result = bytearray(self._man)
        audit = []
        for record, actor, fields, model, animation, donors in sorted(staged):
            offset = actor.byte_offset + 1 + actor.local_count * 2
            for name, value, delta in (("model_index", model, 0), ("animation_id", animation, 1)):
                if name not in fields or self._man[offset + delta] == value:
                    continue
                result[offset + delta] = value
                audit.append(dict(record_index=record, field=name, decoded_byte_offset=offset + delta,
                                  before_byte=self._man[offset + delta], after_byte=value,
                                  source_decoded_man_sha256=_sha(self._man), donor_records=donors,
                                  target_pair=dict(model_index=model, animation_id=animation),
                                  scope="initial-man-header-only", script_compatibility="unverified"))
        changed = bytes(result)
        reparsed = {a.record_index: a for a in parse_man(changed, self.scene).actors}
        for record, _, _, model, animation, _ in staged:
            if (reparsed[record].model_index, reparsed[record].animation_id) != (model, animation):
                raise ImportError("MAN assignment round-trip validation failed")
        return changed, audit

    def patch_appended(self, candidate: bytes, edits: dict[int, dict[str, int]]) -> tuple[bytes, list[dict]]:
        """Rebase verified original-actor header edits onto an appended MAN.

        Appended donors retain their retail appearance. Never reuse baseline
        absolute offsets after the partition table has grown.
        """
        _, audit = self.patch(edits)
        actors = {a.record_index: a for a in parse_man(candidate, self.scene).actors}
        result = bytearray(candidate)
        rebased = []
        for change in audit:
            actor = actors.get(change['record_index'])
            original = self._actor(change['record_index'])
            if actor is None or (actor.local_count, actor.model_index, actor.animation_id) != (
                    original.local_count, original.model_index, original.animation_id):
                raise ImportError('Appended MAN original actor header differs from baseline')
            delta = 0 if change['field'] == 'model_index' else 1
            offset = actor.byte_offset + 1 + actor.local_count * 2 + delta
            if candidate[offset] != change['before_byte']:
                raise ImportError('Appended MAN assignment preimage differs from baseline')
            result[offset] = change['after_byte']
            rebased.append(dict(change, source_decoded_byte_offset=change['decoded_byte_offset'],
                                decoded_byte_offset=offset,
                                appended_man_sha256=_sha(candidate)))
        return bytes(result), rebased

    def serialize(self, edits: dict[int, dict[str, int]]) -> tuple[bytes, list[dict], dict]:
        """Equal-span encoded replacement; reject compressed growth, no relocation."""
        changed, audit = self.patch(edits)
        encoded = compress_lzs(changed) if audit else self._stream
        if len(encoded) > len(self._stream):
            raise ImportError("edited MAN exceeds original compressed capacity; relocation is unsupported")
        replacement = encoded + self._stream[len(encoded):]
        decoded, consumed = decompress_lzs(replacement, len(changed))
        if decoded != changed or (audit and consumed != len(encoded)):
            raise ImportError("encoded MAN assignment failed independent decode verification")
        return replacement, audit, dict(original_encoded_size=len(self._stream), new_encoded_size=len(encoded),
                                        decoded_size=len(changed), decoded_sha256=_sha(changed))


def load_man_assignment_context(disc: Any, scene: str) -> ManAssignmentContext:
    """Load private baseline and both banks from one identity-verified disc scope."""
    with _disc_context(disc) as (_, digest, mapping, archive):
        start, end = _bounded_scene_range(archive, mapping, scene)
        bundle, raw = find_scene_bundle(archive, start, end)
        values = {}
        source = dict(disc_sha256=digest, iso_file="PROT.DAT", prot_entry_index=bundle.entry_index,
                      scene_table_offset=bundle.table_offset)
        for kind, name in ((3, "man"), (5, "anm")):
            matches = [d for d in bundle.descriptors if d.type_byte == kind and d.size > 0]
            if len(matches) != 1:
                raise ImportError(f"assignment requires exactly one scene {name.upper()} descriptor")
            descriptor = matches[0]
            offset = bundle.table_offset + descriptor.data_offset
            later = [bundle.table_offset + d.data_offset for d in bundle.descriptors if d.data_offset > descriptor.data_offset]
            limit = min(later + [len(raw)])
            if not 0 <= offset < limit <= len(raw):
                raise ImportError("assignment stream exceeds containing descriptor bounds")
            decoded, consumed = decompress_lzs(raw[offset:limit], descriptor.size)
            values[name] = (decoded, raw[offset:offset+consumed])
            source[name] = dict(descriptor_index=descriptor.index, descriptor_type=kind,
                                compressed_stream_offset=offset, compressed_bytes_consumed=consumed)
        models = scene_tmd_pool(archive, start, end)
        counts = {r.pool_index: r.object_count for r in models if r.pool_index < 0xF0}
        return ManAssignmentContext(scene, *values["man"], counts, values["anm"][0], source)
