"""Equal-span, plain-glyph MAN dialogue edits with preserved VM/MES boundaries.

Independent adapter over script_inspection's proven MES intervals. Evidence at
pipeline.REFERENCE_COMMIT: crates/mes/src/lib.rs byte walker (0x5E is a two-byte
spacing alias), engine-core/src/dialog.rs inline MAN segments, and
asset/src/man_section.rs / engine-core/src/man_field_scripts/records.rs bounds.
Menu label/jump layout also follows crates/mes/src/picker.rs at the same pin.
Font renderer newline 0x7C follows crates/font/src/lib.rs and docs/formats/dialog-font.md.
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
    "Only evidenced contiguous one-byte printable ASCII glyph runs are editable; caret, renderer newline (pipe), controls and substitutions are excluded.",
    "Shorter replacements are right-padded with spaces to preserve every byte offset; longer replacements are rejected.",
    "Ordinary dialogue requires no instruction stops; menu labels require decoded nonconflicting picker spans. Aliased records are unsupported.",
    "Menu labels preserve jump entries, continuation bytes, token controls and every record offset; pager execution remains unresolved.",
    "Unvisited tail bytes remain unchanged; static paths do not prove current dialogue reachability or full script behavior.",
    "Glyph width, line wrapping, dialogue boxes and current story state are not simulated.",
    "Playable packaging separately requires the edited MAN to fit the original compressed capacity.",
]


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_dialogue_text(text: Any, *, allow_renderer_newline: bool = False) -> str:
    """Validate text; the legacy reader flag never enables serializer writes."""
    if not isinstance(text, str) or len(text) > MAX_TEXT_LENGTH:
        raise ImportError("dialogue text must be a string of at most 4096 characters")
    if any(not 0x20 <= ord(c) <= 0x7E or c == "^" or (c == "|" and not allow_renderer_newline) for c in text):
        raise ImportError("dialogue text requires printable ASCII excluding caret (^) and renderer newline (|); control bytes and non-ASCII are unsupported")
    return text


def validate_run_id(actor_id: Any, run_id: Any) -> str:
    """Validate structure only; source membership is reverified by context.patch."""
    if not isinstance(actor_id, str) or re.fullmatch(r"scene://[A-Za-z0-9_-]+/(?:actors/man-p1|scripts/man-p2)/[0-9]{4}", actor_id) is None:
        raise ImportError("dialogue authoring requires a partition-1 actor or partition-2 script identifier")
    prefix = "script://" + actor_id.removeprefix("scene://")
    if not isinstance(run_id, str) or re.fullmatch(re.escape(prefix) + r"/(?:dialogue/[0-9a-f]{4}|menu/[0-9a-f]{4}/option/[0-3])/run/[0-9a-f]{4}", run_id) is None:
        raise ImportError("dialogue run identifier must belong to the actor and contain fixed hexadecimal PCs")
    return run_id


def _plain_glyph(token: dict) -> bool:
    return (token["kind"] == "glyph" and token["length"] == 1 and
            0x20 <= token["value"] <= 0x7E and token["value"] not in (0x5E, 0x7C))


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
    for instruction in result["instructions"]:
        if instruction["mnemonic"] != "DIALOGUE_PICKER":
            continue
        raw = bytearray.fromhex(instruction["raw_hex"])
        for option in instruction["operands"]["options"]:
            option.pop("label")
            for token in option["label_tokens"]:
                if _plain_glyph(token):
                    raw[token["pc"] - instruction["pc"]] = 0x20
                    for key in ("value", "text", "raw_hex"):
                        token.pop(key, None)
        instruction["raw_hex"] = raw.hex()
        instruction["operands"]["encoded_hex"] = raw[1:].hex()
    return result


class DialogueAuthoringContext:
    """Private request-scoped source snapshot; construction is for decoder products.

    patch accepts an exact optional baseline guard, not previously edited input.
    Build composition merges the audited spans with independently verified header
    edits before final serialization; this module never writes files or disc bytes.
    """
    def __init__(self, scene: str, man: bytes, stream: bytes, source: dict, *, compression='lzs'):
        if not isinstance(man, bytes) or not 0 < len(man) <= MAX_MAN_BYTES:
            raise ImportError("dialogue MAN source exceeds bounded immutable byte size")
        parsed = parse_man(man, scene)
        if len(parsed.actors) > MAX_ACTORS:
            raise ImportError("dialogue MAN actor count exceeds bound")
        if compression == 'none':
            decoded, consumed = stream, len(stream)
        elif compression == 'lzs':
            decoded, consumed = decompress_lzs(stream, len(man))
        else:
            raise ImportError('Unsupported dialogue source compression')
        if decoded != man:
            raise ImportError("dialogue MAN encoded and decoded sources disagree")
        self.scene, self._man, self._stream = scene, man, bytes(stream[:consumed])
        self._source = deepcopy(source)
        self._compression = compression
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
                    decoded_man_size=len(self._man), limitations=[
                        'Streaming packaging preserves the original raw payload size.' if self._compression == 'none' and 'compressed capacity' in text else text
                        for text in LIMITATIONS])

    def _inspect(self, actor_id: str, man: bytes) -> dict:
        actor = self._actors[actor_id]
        record = man[actor.byte_offset:actor.byte_offset + actor.byte_length]
        entry = _p2_entry(record)[0] if "/scripts/man-p2/" in actor_id else 1 + actor.local_count * 2 + 4
        return inspect_record(record, entry,
                              semantic_id="script://" + actor_id.removeprefix("scene://"),
                              base_offset=actor.byte_offset)

    def _register_owner(self, actor_id: str) -> None:
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

    def verified_record(self, actor_id: str) -> tuple[int, bytes, int]:
        """Return an immutable, uniquely owned script span and its entry PC.

        Other equal-span serializers share the MAN ownership checks without
        depending on dialogue availability or populating glyph-run caches.
        """
        self._register_owner(actor_id)
        if actor_id not in self._unique:
            raise ImportError("script edits require a non-aliased record outside MAN sections")
        actor = self._actors[actor_id]
        record = self._man[actor.byte_offset:actor.byte_offset + actor.byte_length]
        entry = _p2_entry(record)[0] if "/scripts/man-p2/" in actor_id else 1 + actor.local_count * 2 + 4
        return actor.byte_offset, record, entry

    def options(self, actor_id: str) -> dict:
        self._register_owner(actor_id)
        if actor_id not in self._options:
            runs, reason, status = [], None, "unavailable"
            actor = self._actors[actor_id]
            try:
                if actor_id not in self._unique:
                    raise ImportError("dialogue edits require a non-aliased actor record outside MAN sections")
                report = self._inspect(actor_id, self._man)
                status = report["status"]
                self._reports[actor_id] = report
                segments = []
                # Keep the ordinary dialogue stop gate. Label spans are local,
                # fully decoded parts of reached pickers, not inferred pages.
                if not report["stops"]:
                    segments.extend((dialogue, {}) for dialogue in report["dialogues"])
                else:
                    reason = "Ordinary dialogue edits require no unknown or conflicting instruction stops; only supported menu labels are offered"
                for row in report["instructions"]:
                    if row["mnemonic"] != "DIALOGUE_PICKER":
                        continue
                    for option in row["operands"]["options"]:
                        label_id = ("script://" + actor_id.removeprefix("scene://") +
                                    f"/menu/{row['pc']:04x}/option/{option['index']}")
                        tokens = deepcopy(option["label_tokens"])
                        for token in tokens:
                            token["byte_offset"] = actor.byte_offset + token["pc"]
                        segments.append((dict(semantic_id=label_id, pc=option["label_pc"],
                                              text=option["label"], tokens=tokens),
                                         dict(kind="menu_label", menu_pc=row["pc"],
                                              option_index=option["index"],
                                              option_count=row["operands"]["option_count"],
                                              entry_pc=option["entry_pc"],
                                              relative_jump=option["relative_jump"],
                                              encoded_target=option["encoded_target"],
                                              runtime_choice="not_observed")))
                for dialogue, metadata in segments:
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
                                   source_text_sha256=_sha(text.encode("ascii")), **metadata)
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

    def patch_appended(self, candidate: bytes, edits: dict[str, str]) -> tuple[bytes, list[dict]]:
        """Rebase supported original dialogue spans after actor table growth."""
        from .man_layout import read_man_layout
        _, changes = self.patch(edits)
        layout = read_man_layout(candidate)
        records = {(r['partition'],r['record_index']):r for r in layout['records']}
        output, audit = bytearray(candidate), []
        for change in changes:
            run = self._runs[change['run_id']]
            owner = self._actors[run['actor_id']]
            partition = 2 if '/scripts/man-p2/' in run['actor_id'] else 1
            record = records.get((partition,change['record_index']))
            if record is None or record['byte_length'] != owner.byte_length:
                raise ImportError('Appended dialogue record differs from verified source extent')
            relative = change['decoded_byte_offset'] - owner.byte_offset
            size = change['byte_length']
            if not 0 <= relative <= record['byte_length']-size:
                raise ImportError('Appended dialogue span escapes its record')
            offset = record['byte_offset'] + relative
            if candidate[offset:offset+size].hex() != change['before_hex']:
                raise ImportError('Appended dialogue preimage differs from verified source')
            output[offset:offset+size] = bytes.fromhex(change['after_hex'])
            audit.append(dict(change,source_decoded_byte_offset=change['decoded_byte_offset'],
                              decoded_byte_offset=offset,appended_man_sha256=_sha(candidate)))
        result = bytes(output)
        if read_man_layout(result) != layout:
            raise ImportError('Appended dialogue patch changed MAN layout')
        return result,audit

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
            actor_id = "scene://" + re.split(r"/(?:dialogue|menu)/", identifier.removeprefix("script://"), maxsplit=1)[0]
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
            if run.get("kind") == "menu_label":
                audit[-1].update(kind="menu_label", menu_pc=run["menu_pc"],
                                 option_index=run["option_index"], encoded_target=run["encoded_target"])
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
        try:
            bundle, raw = find_scene_bundle(archive, start, end)
        except ImportError:
            from .man_source import read_man_source
            carrier = read_man_source(archive, start, end, scene)
            if carrier.kind != 'raw_streaming_man':
                raise ImportError('Dialogue source kind changed during streaming resolution')
            source = dict(disc_sha256=digest, iso_file='PROT.DAT', prot_entry_index=carrier.entry_index,
                          man=carrier.provenance())
            return DialogueAuthoringContext(scene, carrier.payload, carrier.payload, source, compression='none')
        descriptors = [d for d in bundle.descriptors if d.type_byte == 3 and d.size > 0]
        if len(descriptors) != 1:
            raise ImportError("dialogue authoring requires exactly one scene MAN descriptor")
        descriptor = descriptors[0]
        if not 0 < descriptor.size <= MAX_MAN_BYTES:
            raise ImportError("script authoring MAN exceeds the decoded size bound")
        if sum(d.size > 0 and d.data_offset == descriptor.data_offset for d in bundle.descriptors) != 1:
            raise ImportError("script authoring requires a non-aliased MAN descriptor")
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
