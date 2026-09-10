"""Equal-span, plain-glyph MAN dialogue edits with preserved VM/MES boundaries.

Independent adapter over script_inspection's proven MES intervals. Evidence at
pipeline.REFERENCE_COMMIT: crates/mes/src/lib.rs byte walker (0x5E is a two-byte
spacing alias), engine-core/src/dialog.rs inline MAN segments, and
asset/src/man_section.rs / engine-core/src/man_field_scripts/records.rs bounds.
No text relocation, control editing, story execution or font layout is inferred.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import re
from types import SimpleNamespace
from typing import Any

from .core import ImportError, decompress_lzs, find_scene_bundle, parse_man, stable_actor_id
from .pipeline import REFERENCE_COMMIT, _bounded_scene_range, _disc_context
from .script_inspection import inspect_record
from .trigger_scripts import _p2_record, _p2_entry

MAX_MAN_BYTES = 4 * 1024 * 1024
MAX_ACTORS = 512
MAX_TEXT_LENGTH = 4096
MAX_EDIT_RUNS = 1024
MAX_EDIT_BYTES = 65536
LIMITATIONS = [
    "Only evidenced contiguous one-byte printable ASCII glyph runs are editable; caret, controls and substitutions are excluded.",
    "Shorter replacements are right-padded with spaces to preserve every byte offset; longer replacements are rejected.",
    "Records with unknown instruction stops, conflicting decode boundaries or aliased source records are unsupported.",
    "Unvisited tail bytes remain unchanged; static paths do not prove current dialogue reachability or full script behavior.",
    "Glyph width, line wrapping, dialogue boxes and current story state are not simulated.",
    "Playable packaging separately requires the edited MAN to fit the original compressed capacity.",
]


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_dialogue_text(text: Any) -> str:
    """Validate authored project text without requiring proprietary source data."""
    if not isinstance(text, str) or len(text) > MAX_TEXT_LENGTH:
        raise ImportError("dialogue text must be a string of at most 4096 characters")
    if any(not 0x20 <= ord(c) <= 0x7E or c == "^" for c in text):
        raise ImportError("dialogue text requires printable ASCII excluding caret (^); control bytes and non-ASCII are unsupported")
    return text


def validate_run_id(actor_id: Any, run_id: Any) -> str:
    """Validate structure only; source membership is reverified by context.patch."""
    if not isinstance(actor_id, str) or re.fullmatch(r"scene://[A-Za-z0-9_-]+/(?:actors/man-p1|scripts/man-p2)/[0-9]{4}", actor_id) is None:
        raise ImportError("dialogue authoring requires a partition-1 actor or partition-2 script identifier")
    prefix = "script://" + actor_id.removeprefix("scene://")
    if not isinstance(run_id, str) or re.fullmatch(re.escape(prefix) + r"/dialogue/[0-9a-f]{4}/run/[0-9a-f]{4}", run_id) is None:
        raise ImportError("dialogue run identifier must belong to the actor and contain fixed hexadecimal PCs")
    return run_id


def _plain_glyph(token: dict) -> bool:
    return (token["kind"] == "glyph" and token["length"] == 1 and
            0x20 <= token["value"] <= 0x7E and token["value"] != 0x5E)


def _shape(report: dict) -> dict:
    """Retain every boundary/control/branch while masking replaceable glyphs."""
    result = deepcopy(report)
    for dialogue in result["dialogues"]:
        dialogue.pop("text")
        dialogue.pop("raw_hex")
        for token in dialogue["tokens"]:
            if _plain_glyph(token):
                for key in ("value", "text", "raw_hex"):
                    token.pop(key, None)
    return result


class DialogueAuthoringContext:
    """Private request-scoped source snapshot; construction is for decoder products.

    patch accepts an exact optional baseline guard, not previously edited input.
    Build composition merges the audited spans with independently verified header
    edits before final serialization; this module never writes files or disc bytes.
    """
    def __init__(self, scene: str, man: bytes, stream: bytes, source: dict):
        if not isinstance(man, bytes) or not 0 < len(man) <= MAX_MAN_BYTES:
            raise ImportError("dialogue MAN source exceeds bounded immutable byte size")
        parsed = parse_man(man, scene)
        if len(parsed.actors) > MAX_ACTORS:
            raise ImportError("dialogue MAN actor count exceeds bound")
        decoded, consumed = decompress_lzs(stream, len(man))
        if decoded != man:
            raise ImportError("dialogue MAN encoded and decoded sources disagree")
        self.scene, self._man, self._stream = scene, man, bytes(stream[:consumed])
        self._source = deepcopy(source)
        self._actors = {stable_actor_id(scene, 1, a.record_index): a for a in parsed.actors}
        total = sum(parsed.partition_counts)
        region = 0x2B + 3 * total
        starts = [region + int.from_bytes(man[0x2B + 3*i:0x2E + 3*i], "little") for i in range(total)]
        if any(not region <= start < len(man) for start in starts):
            raise ImportError("MAN record table contains out-of-bounds aliases")
        counts = Counter(starts)
        section = region + int.from_bytes(man[0x28:0x2B], "little")
        sections = []
        for _ in range(6):
            end = section + 3 + int.from_bytes(man[section:section + 3], "little")
            sections.append((section, end))
            section = end
        self._unique = {identifier for identifier, a in self._actors.items()
                        if counts[a.byte_offset] == 1 and not any(
                            a.byte_offset < end and start < a.byte_offset + a.byte_length for start, end in sections)}
        self._reports: dict[str, dict] = {}
        self._options: dict[str, dict] = {}
        self._runs: dict[str, dict] = {}

    def provenance(self) -> dict:
        return dict(deepcopy(self._source), scene=self.scene, reference_commit=REFERENCE_COMMIT,
                    decoded_man_sha256=_sha(self._man), encoded_man_sha256=_sha(self._stream),
                    decoded_man_size=len(self._man), limitations=list(LIMITATIONS))

    def _inspect(self, actor_id: str, man: bytes) -> dict:
        actor = self._actors[actor_id]
        record = man[actor.byte_offset:actor.byte_offset + actor.byte_length]
        entry = _p2_entry(record)[0] if "/scripts/man-p2/" in actor_id else 1 + actor.local_count * 2 + 4
        return inspect_record(record, entry,
                              semantic_id="script://" + actor_id.removeprefix("scene://"),
                              base_offset=actor.byte_offset)

    def options(self, actor_id: str) -> dict:
        if isinstance(actor_id, str) and actor_id not in self._actors:
            match = re.fullmatch(re.escape(f"scene://{self.scene}/scripts/man-p2/") + r"([0-9]{4})", actor_id)
            if match:
                index = int(match[1])
                offset, record = _p2_record(self._man, index)
                _p2_entry(record)
                self._actors[actor_id] = SimpleNamespace(record_index=index, byte_offset=offset,
                                                        byte_length=len(record))
                self._unique.add(actor_id)
        if not isinstance(actor_id, str) or actor_id not in self._actors:
            raise ImportError("dialogue actor is not present in the verified MAN")
        if actor_id not in self._options:
            runs, reason, status = [], None, "unavailable"
            actor = self._actors[actor_id]
            try:
                if actor_id not in self._unique:
                    raise ImportError("dialogue edits require a non-aliased actor record outside MAN sections")
                report = self._inspect(actor_id, self._man)
                status = report["status"]
                if report["stops"]:
                    raise ImportError("dialogue edits require no unknown or conflicting instruction stops in the inspected actor graph")
                self._reports[actor_id] = report
                for dialogue in report["dialogues"]:
                    group = []
                    def finish():
                        if not group:
                            return
                        pc = group[0]["pc"]
                        identifier = f"{dialogue['semantic_id']}/run/{pc:04x}"
                        text = "".join(t["text"] for t in group)
                        run = dict(semantic_id=identifier, dialogue_id=dialogue["semantic_id"],
                                   actor_id=actor_id, record_index=actor.record_index, pc=pc,
                                   dialogue_pc=dialogue["pc"], decoded_byte_offset=group[0]["byte_offset"],
                                   byte_length=len(group), max_length=len(group), text=text,
                                   dialogue_text=dialogue["text"], padding="right_spaces",
                                   source_text_sha256=_sha(text.encode("ascii")))
                        self._runs[identifier] = run
                        runs.append(run)
                        group.clear()
                    for token in dialogue["tokens"]:
                        if _plain_glyph(token):
                            group.append(token)
                        else:
                            finish()
                    finish()
                if not runs:
                    reason = "No supported plain-glyph dialogue runs occur on the inspected paths"
            except ImportError as exc:
                reason = str(exc)
            self._options[actor_id] = dict(supported=bool(runs), reason=reason, actor_id=actor_id,
                                           graph_status=status, runs=runs, source=self.provenance(),
                                           limitations=list(LIMITATIONS))
        return deepcopy(self._options[actor_id])

    def patch(self, edits: dict[str, str], *, original: bytes | None = None) -> tuple[bytes, list[dict]]:
        if original is not None and original != self._man:
            raise ImportError("dialogue MAN source differs from the verified baseline")
        if not isinstance(edits, dict) or len(edits) > MAX_EDIT_RUNS:
            raise ImportError("dialogue edit set exceeds the bounded run count")
        staged, edited_bytes = [], 0
        for identifier, text in edits.items():
            validate_dialogue_text(text)
            if not isinstance(identifier, str):
                raise ImportError("dialogue edit requires a structural run identifier")
            actor_id = "scene://" + identifier.removeprefix("script://").split("/dialogue/", 1)[0]
            validate_run_id(actor_id, identifier)
            options = self.options(actor_id)
            run = self._runs.get(identifier)
            if not options["supported"] or run is None:
                raise ImportError("dialogue run is not a supported span in the verified actor record")
            size = run["byte_length"]
            if len(text) > size:
                raise ImportError(f"dialogue run permits at most {size} printable ASCII characters; relocation is unsupported")
            edited_bytes += size
            if edited_bytes > MAX_EDIT_BYTES:
                raise ImportError("dialogue edits exceed the 65536-byte span budget")
            staged.append((run, text.encode("ascii").ljust(size, b" "), len(text)))
        result, audit, changed_actors = bytearray(self._man), [], set()
        for run, replacement, text_length in sorted(staged, key=lambda item: item[0]["decoded_byte_offset"]):
            offset, size = run["decoded_byte_offset"], run["byte_length"]
            before = self._man[offset:offset + size]
            if before == replacement:
                continue
            result[offset:offset + size] = replacement
            changed_actors.add(run["actor_id"])
            audit.append(dict(record_index=run["record_index"], run_id=run["semantic_id"],
                              decoded_byte_offset=offset, byte_length=size, before_hex=before.hex(),
                              after_hex=replacement.hex(), padding_bytes=size - text_length,
                              source_decoded_man_sha256=_sha(self._man), scope="equal-span-plain-MES-glyphs"))
        changed = bytes(result)
        for actor_id in changed_actors:
            if _shape(self._reports[actor_id]) != _shape(self._inspect(actor_id, changed)):
                raise ImportError("dialogue patch changed decoded instruction, token or control boundaries")
        if parse_man(changed, self.scene) != parse_man(self._man, self.scene):
            raise ImportError("dialogue patch changed MAN placement or record boundaries")
        return changed, audit


def load_dialogue_authoring_context(disc: Any, scene: str) -> DialogueAuthoringContext:
    """Read exactly one bounded MAN stream through the verified disc context."""
    with _disc_context(disc) as (_, digest, mapping, archive):
        start, end = _bounded_scene_range(archive, mapping, scene)
        bundle, raw = find_scene_bundle(archive, start, end)
        descriptors = [d for d in bundle.descriptors if d.type_byte == 3 and d.size > 0]
        if len(descriptors) != 1:
            raise ImportError("dialogue authoring requires exactly one scene MAN descriptor")
        descriptor = descriptors[0]
        offset = bundle.table_offset + descriptor.data_offset
        ceiling = min([bundle.table_offset + d.data_offset for d in bundle.descriptors
                       if d.data_offset > descriptor.data_offset] + [len(raw)])
        if not 0 <= offset < ceiling <= len(raw):
            raise ImportError("dialogue MAN compressed span exceeds its containing descriptor")
        man, consumed = decompress_lzs(raw[offset:ceiling], descriptor.size)
        source = dict(disc_sha256=digest, iso_file="PROT.DAT", prot_entry_index=bundle.entry_index,
                      scene_table_offset=bundle.table_offset,
                      man=dict(descriptor_index=descriptor.index, descriptor_type=3,
                               compressed_stream_offset=offset, compressed_bytes_consumed=consumed))
        return DialogueAuthoringContext(scene, man, raw[offset:offset + consumed], source)
