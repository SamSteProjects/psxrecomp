"""Build private disc overlays from bounded authored MAN data and scene TIMs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import stat
import tempfile
import zipfile

from importer.core import ImportError, canonical_json, decompress_lzs
from importer.pipeline import _bounded_scene_range, _disc_context, _read_scene_man, import_scene
from importer.serialization import patch_man_positions, serialize_man_decoded, serialize_man_stream
from importer.man_assignments import load_man_assignment_context
from .project import ProjectError


class BuildError(ProjectError):
    pass


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def authored_state_key(project) -> str:
    """Build-input metadata identity, excluding selection, history and templates.

    This identifies the authored snapshot, not continued integrity of disc or
    output files. Build always verifies those independently.
    """
    return _hash(canonical_json({"name": project.name, "root": str(project.root),
                                "disc_path": str(project.disc_path), "imports": project.imports,
                                "overrides": project.overrides,
                                "textures": getattr(project, "texture_overrides", {})}).encode("utf-8"))


def build_report(audit) -> dict:
    """Present only audited changes that actually entered the emitted package."""
    changes = []
    for change in audit["edits"]:
        field = change["field"]
        if field == "dialogue.text":
            before = bytes.fromhex(change["before_hex"]).decode("ascii")
            after = bytes.fromhex(change["after_hex"]).decode("ascii")
        elif field == "texture.tim":
            before, after = change["before_sha256"], change["after_sha256"]
        else:
            before = change.get("before_value", change.get("before_byte"))
            after = change.get("after_value", change.get("after_byte"))
        changes.append({"scene": change["scene"], "asset_id": change.get("transition_id", change.get("run_id", change["semantic_id"])),
                        "owner_id": change["semantic_id"],
                        "field": field, "before": before, "after": after,
                        "scope": change.get("scope", "initial-man-placement-only")})
    return {"schema_version": "legaia.build-report.v1", "changes": changes,
            "validation": dict(audit["validation"]), "change_count": len(changes),
            "scene_count": len({change["scene"] for change in changes}),
            "overlay_bytes": sum(overlay["size"] for overlay in audit["overlays"])}


def _merge_dialogue_patch(baseline, working, dialogue, changes, expected_runs, previous_changes):
    """Merge only fresh, independently audited equal-size glyph spans."""
    if not isinstance(dialogue, bytes) or len(dialogue) != len(baseline) or len(working) != len(baseline):
        raise BuildError("Dialogue patch must preserve the decoded MAN length")
    occupied = {change["decoded_byte_offset"] for change in previous_changes}
    dialogue_offsets = set()
    merged = bytearray(working)
    source_hash = _hash(baseline)
    for change in changes:
        run = expected_runs.get(change.get("run_id"))
        offset, length = change.get("decoded_byte_offset"), change.get("byte_length")
        if (run is None or type(offset) is not int or type(length) is not int or
                not 0 < length <= len(baseline) or offset < 0 or offset + length > len(baseline) or
                change.get("record_index") != run["record_index"] or
                offset != run["decoded_byte_offset"] or length != run["byte_length"] or
                change.get("source_decoded_man_sha256") != source_hash):
            raise BuildError("Dialogue audit does not match the verified actor/run source")
        try:
            before, after = bytes.fromhex(change["before_hex"]), bytes.fromhex(change["after_hex"])
        except (ValueError, KeyError, TypeError) as exc:
            raise BuildError("Dialogue audit has invalid encoded byte spans") from exc
        if (len(before) != length or len(after) != length or before != baseline[offset:offset+length] or
                after != dialogue[offset:offset+length]):
            raise BuildError("Dialogue audit bytes disagree with the verified source or patch")
        span = set(range(offset, offset + length))
        if span & (occupied | dialogue_offsets):
            raise BuildError("Dialogue patch overlaps another authored MAN span")
        dialogue_offsets.update(span)
        merged[offset:offset+length] = after
    if any(a != b and i not in dialogue_offsets for i, (a, b) in enumerate(zip(baseline, dialogue))):
        raise BuildError("Dialogue patch altered an unaudited MAN byte")
    return bytes(merged)


def _merge_transition_patch(baseline, working, patched, changes, expected, previous):
    from importer.transition_authoring import ENTRY_FIELDS
    if not isinstance(patched, bytes) or len(patched) != len(baseline) or len(working) != len(baseline):
        raise BuildError("Transition patch changed MAN length")
    occupied = {i for c in previous for i in range(c["decoded_byte_offset"], c["decoded_byte_offset"] + c.get("byte_length", 1))}
    audited = set()
    result = bytearray(working)
    digest = _hash(baseline)
    for c in changes:
        entry = expected.get(c.get("transition_id"))
        offset, field = c.get("decoded_byte_offset"), c.get("field")
        if (entry is None or field not in ENTRY_FIELDS or type(offset) is not int or
                not 0 <= offset < len(baseline) or
                offset != entry["decoded_byte_offset"] + ENTRY_FIELDS.index(field) or
                c.get("owner_id") != entry["owner_id"] or
                c.get("source_record_sha256") != entry["source_record_sha256"] or
                c.get("source_decoded_man_sha256") != digest or
                c.get("before_byte") != baseline[offset] or c.get("after_byte") != patched[offset]):
            raise BuildError("Transition audit disagrees with verified source bytes")
        if offset in occupied or offset in audited:
            raise BuildError("Transition patch overlaps another authored MAN span")
        audited.add(offset)
        result[offset] = patched[offset]
    if any(a != b and i not in audited for i, (a, b) in enumerate(zip(baseline, patched))):
        raise BuildError("Transition patch changed an unaudited MAN byte")
    return bytes(result)


def _guard_output(path: Path, boundary: Path) -> None:
    path, boundary = path.absolute(), boundary.absolute()
    if not path.is_relative_to(boundary) or not path.resolve().is_relative_to(boundary.resolve()):
        raise BuildError("Build output escapes its declared output root")
    current = path
    while current != boundary:
        try:
            info = current.lstat()
        except FileNotFoundError:
            pass
        else:
            if (stat.S_ISLNK(info.st_mode) or
                    getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)):
                raise BuildError(f"Build output contains a symlink or reparse point: {current}")
        current = current.parent


def _write_exact(path: Path, content: bytes, boundary: Path) -> None:
    _guard_output(path, boundary)
    if path.exists():
        if not path.is_file() or path.read_bytes() != content:
            raise BuildError(f"Existing build output differs; choose a new output directory: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    _guard_output(path, boundary)
    with path.open("xb") as handle:
        handle.write(content)


def build_project(project, output_dir: Path | str | None = None) -> dict:
    """Emit a deterministic .psxmod archive, package sources and bounded audit.

    Supports representable authored field X/Z placement, evidenced initial
    MAN donor model/animation assignments, equal-span dialogue glyph runs,
    layout-compatible scene TIM replacements,
    and unchanged retail builds after clearing overrides. The input disc and
    imported metadata remain unchanged. Installation/enabling and a live
    launch are separate actions; this function does not claim runtime testing.
    """
    try:
        return _build_project(project, output_dir)
    except ImportError as exc:
        raise BuildError(str(exc)) from exc


def _build_project(project, output_dir) -> dict:
    if not project.disc_path:
        raise BuildError("Build requires the project's verified user-owned retail disc")
    if not project.imports:
        raise BuildError("Build requires at least one verified imported scene")
    scene_edits: dict[str, dict] = {}
    entity_lookup = {actor["semantic_id"]: (scene_id, actor)
                     for scene_id, document in project.imports.items()
                     for actor in document["actors"]}
    for identifier, components in sorted(project.overrides.items()):
        if isinstance(components, dict) and "Transitions" in components:
            project._validate_transitions(identifier, components["Transitions"])
            document = project._dialogue_document(identifier)
            scene_id = "scene://" + document["scene"]["name"]
            edits = scene_edits.setdefault(scene_id, {"positions": {}, "assignments": {}, "dialogues": {}, "transitions": {}})
            edits["transitions"][identifier] = components["Transitions"]["entries"]
            components = {k: v for k, v in components.items() if k != "Transitions"}
            if not components:
                continue
        if isinstance(identifier, str) and "/scripts/man-p2/" in identifier:
            from importer.dialogue_authoring import validate_run_id
            validate_run_id(identifier, "script://" + identifier.removeprefix("scene://") + "/dialogue/0000/run/0000")
            scene_id = identifier.split("/scripts/man-p2/", 1)[0]
            if scene_id not in project.imports or not isinstance(components, dict) or set(components) != {"Dialogue"}:
                raise BuildError("Partition-2 script overrides require an imported scene and only Dialogue")
            dialogue = components["Dialogue"]
            if (not isinstance(dialogue, dict) or set(dialogue) != {"runs"} or
                    not isinstance(dialogue["runs"], dict) or not dialogue["runs"]):
                raise BuildError("Partition-2 Dialogue requires nonempty runs")
            for run, text in dialogue["runs"].items():
                validate_run_id(identifier, run)
                if not isinstance(text, str):
                    raise BuildError("Dialogue replacement must be text")
            edits = scene_edits.setdefault(scene_id, {"positions": {}, "assignments": {}, "dialogues": {}, "transitions": {}})
            edits["dialogues"][identifier] = dialogue["runs"]
            continue
        if identifier not in entity_lookup:
            raise BuildError(f"Authored entity has no imported provenance: {identifier}")
        scene_id, actor = entity_lookup[identifier]
        if (not isinstance(components, dict) or not components or
                set(components) - {"Transform", "ActorAppearance", "Dialogue"}):
            raise BuildError(f"{identifier}: only authored Transform.position, ActorAppearance and bounded Dialogue runs can be built")
        edits = scene_edits.setdefault(scene_id, {"positions": {}, "assignments": {}, "dialogues": {}, "transitions": {}})
        record = actor["source_record"]["record_index"]
        if "Transform" in components:
            transform = components["Transform"]
            if not isinstance(transform, dict) or set(transform) != {"position"}:
                raise BuildError(f"{identifier}: only authored Transform.position X/Z edits can be built")
            position = transform["position"]
            if not isinstance(position, dict) or not position or set(position) - {"x", "z"}:
                raise BuildError(f"{identifier}: only X/Z placement can be built; height and other fields are unsupported")
            edits["positions"][record] = position
        if "ActorAppearance" in components:
            appearance = components["ActorAppearance"]
            if (not isinstance(appearance, dict) or set(appearance) != {"donor_entity_id"} or
                    not isinstance(appearance["donor_entity_id"], str)):
                raise BuildError(f"{identifier}: ActorAppearance requires only donor_entity_id")
            donor_id = appearance["donor_entity_id"]
            if donor_id not in entity_lookup or entity_lookup[donor_id][0] != scene_id:
                raise BuildError(f"{identifier}: appearance donor must be an imported actor in the same scene")
            edits["assignments"][record] = donor_id
        if "Dialogue" in components:
            dialogue = components["Dialogue"]
            if (not isinstance(dialogue, dict) or set(dialogue) != {"runs"} or
                    not isinstance(dialogue["runs"], dict) or not dialogue["runs"] or
                    any(not isinstance(run, str) or not isinstance(text, str) for run, text in dialogue["runs"].items())):
                raise BuildError(f"{identifier}: Dialogue requires only nonempty runs mapping run identities to text")
            edits["dialogues"][identifier] = dialogue["runs"]

    texture_edits = {}
    texture_overrides = getattr(project, "texture_overrides", {})
    if not isinstance(texture_overrides, dict) or len(texture_overrides) > 128:
        raise BuildError("Texture overrides must be a bounded mapping of resource identities")
    for identifier, binding in texture_overrides.items():
        if (not isinstance(identifier, str) or not identifier.startswith("texture://") or
                len(identifier) > 512 or not isinstance(binding, dict) or
                set(binding) != {"asset_sha256", "byte_length", "format", "source_scene_id"} or
                binding.get("format") != "tim" or type(binding.get("byte_length")) is not int or
                not 1 <= binding["byte_length"] <= 1024 * 1024 or not isinstance(binding.get("asset_sha256"), str) or
                len(binding["asset_sha256"]) != 64 or
                any(c not in "0123456789abcdef" for c in binding["asset_sha256"]) or
                not isinstance(binding.get("source_scene_id"), str) or
                binding["source_scene_id"] not in project.imports):
            raise BuildError("Texture override requires a verified private TIM binding and imported source scene")
        texture_edits.setdefault(binding["source_scene_id"], {})[identifier] = binding

    # Reimport before using authored locators: modified/stale metadata cannot
    # redirect an otherwise disc-identity-valid overlay onto unrelated bytes.
    for scene_id in sorted(set(scene_edits) | set(texture_edits)) or project.imports:
        document = project.imports[scene_id]
        fresh = import_scene(project.disc_path, document["scene"]["name"])
        if canonical_json(document) != canonical_json(fresh):
            raise BuildError(f"Imported provenance for {scene_id} no longer matches a fresh retail import")

    overlays = []
    audit_edits = []
    with _disc_context(project.disc_path) as (_image, disc_hash, mapping, archive):
        for scene_id, edits in sorted(scene_edits.items()):
            document = project.imports[scene_id]
            scene = document["scene"]["name"]
            if document["source"]["disc_identity"] != "sha256:" + disc_hash:
                raise BuildError(f"Source disc identity does not match {scene_id}")
            start, end = _bounded_scene_range(archive, mapping, scene)
            bundle, descriptor, consumed, _parsed = _read_scene_man(archive, start, end, scene)
            entry = archive.entry(bundle.entry_index)
            body = archive.read_entry(entry)
            stream_offset = bundle.table_offset + descriptor.data_offset
            original_span = body[stream_offset:stream_offset + consumed]
            if edits["assignments"] or edits["dialogues"] or edits["transitions"]:
                baseline = decompress_lzs(original_span, descriptor.size)[0]
                changed, changes = baseline, []
            if edits["assignments"]:
                context = load_man_assignment_context(project.disc_path, scene)
                assignments = {}
                for record, donor_id in edits["assignments"].items():
                    donor = entity_lookup[donor_id][1]
                    pair = {"model_index": donor["model_reference"]["model_index"],
                            "animation_id": donor["placement_fields"]["animation_id"]}
                    options = context.options(record)
                    if not options["supported"] or not any(
                            option["model_index"] == pair["model_index"] and
                            option["animation_id"] == pair["animation_id"] and
                            donor["source_record"]["record_index"] in option["donor_records"]
                            for option in options["pairs"]):
                        raise BuildError(f"{scene} actor {record}: unsupported initial donor assignment; "
                                         + (options["reason"] or "pair lacks compatible same-scene donor evidence"))
                    assignments[record] = pair
                changed, changes = context.patch(assignments, original=baseline)
                for change in changes:
                    change["donor_entity_id"] = edits["assignments"][change["record_index"]]
            if edits["assignments"] or edits["dialogues"] or edits["transitions"]:
                changed, position_changes = patch_man_positions(changed, scene, edits["positions"])
                changes.extend(position_changes)
                if edits["dialogues"]:
                    from importer.dialogue_authoring import load_dialogue_authoring_context
                    context = load_dialogue_authoring_context(project.disc_path, scene)
                    requested, expected_runs = {}, {}
                    for identifier, runs in edits["dialogues"].items():
                        record = (int(identifier.rsplit("/", 1)[1]) if "/scripts/man-p2/" in identifier
                                  else entity_lookup[identifier][1]["source_record"]["record_index"])
                        options = context.options(identifier)
                        allowed = {run["semantic_id"]: run for run in options["runs"]}
                        for run_id, text in runs.items():
                            run = allowed.get(run_id)
                            if (run is None or run.get("actor_id") != identifier or
                                    run.get("record_index") != record or run_id in requested):
                                raise BuildError(f"{identifier}: dialogue run is not an evidenced unique run owned by this actor")
                            requested[run_id] = text
                            expected_runs[run_id] = run
                    dialogue_changed, dialogue_changes = context.patch(requested, original=baseline)
                    changed = _merge_dialogue_patch(baseline, changed, dialogue_changed, dialogue_changes,
                                                   expected_runs, changes)
                    for change in dialogue_changes:
                        change.update(field="dialogue.text", scope="inline-mes-glyph-run-only",
                                      semantic_id=expected_runs[change["run_id"]]["actor_id"])
                    changes.extend(dialogue_changes)
                if edits["transitions"]:
                    from importer.transition_authoring import load_transition_authoring_context
                    context = load_transition_authoring_context(project.disc_path, scene)
                    requested, expected = {}, {}
                    for owner, entries in edits["transitions"].items():
                        allowed = {e["semantic_id"]: e for e in context.options(owner)["transitions"]}
                        for key, values in entries.items():
                            if key not in allowed or key in requested:
                                raise BuildError("Transition is not uniquely owned by the verified source")
                            requested[key], expected[key] = values, allowed[key]
                    transition_man, transition_changes = context.patch(requested, original=baseline)
                    changed = _merge_transition_patch(baseline, changed, transition_man,
                                                      transition_changes, expected, changes)
                    for change in transition_changes:
                        change.update(semantic_id=change["owner_id"],
                                      record_index=int(change["owner_id"].rsplit("/", 1)[1]),
                                      scope="encoded-transition-entry-only")
                    changes.extend(transition_changes)
                replacement, sizes = serialize_man_decoded(original_span, descriptor.size, changed, scene)
            else:
                replacement, changes, sizes = serialize_man_stream(original_span, descriptor.size, scene, edits["positions"])
            if not changes:
                continue
            if len(replacement) != len(original_span):
                raise BuildError("MAN serializer changed the guarded source span length")
            # Apply exactly the proposed overlay to a private entry copy and
            # independently decode it, checking the surrounding opaque bytes.
            patched = body[:stream_offset] + replacement + body[stream_offset + consumed:]
            if patched[:stream_offset] != body[:stream_offset] or patched[stream_offset + consumed:] != body[stream_offset + consumed:]:
                raise BuildError("MAN patch altered bytes outside its original compressed span")
            after_man = decompress_lzs(patched[stream_offset:], descriptor.size)[0]
            before_man = decompress_lzs(original_span, descriptor.size)[0]
            changed_offsets = {offset for change in changes for offset in range(
                change["decoded_byte_offset"], change["decoded_byte_offset"] + change.get("byte_length", 1))}
            if any(a != b and n not in changed_offsets for n, (a, b) in enumerate(zip(before_man, after_man))):
                raise BuildError("MAN round trip altered an opaque decoded byte")
            location = (archive.node.extent_lba + entry.start_lba) * 2048 + stream_offset
            overlays.append({
                "scene": scene, "offset": location, "size": len(replacement),
                "file": f"assets/{scene}-man.lzs", "payload": replacement,
                "sha256": _hash(replacement), "expected_sha256": _hash(original_span),
                "decoded_before_sha256": _hash(before_man), "decoded_after_sha256": _hash(after_man),
                **sizes,
            })
            for change in changes:
                audit_edits.append({"scene": scene, "semantic_id": f"scene://{scene}/actors/man-p1/{change['record_index']:04d}", **change})
        for scene_id, bindings in sorted(texture_edits.items()):
            from importer.texture_authoring import load_texture_authoring_context
            document = project.imports[scene_id]
            scene = document["scene"]["name"]
            if document["source"]["disc_identity"] != "sha256:" + disc_hash:
                raise BuildError(f"Source disc identity does not match {scene_id}")
            context = load_texture_authoring_context(project.disc_path, scene)
            replacements = {}
            for identifier, binding in sorted(bindings.items()):
                payload = project.read_texture_replacement(binding)
                if (not isinstance(payload, bytes) or len(payload) != binding["byte_length"] or
                        _hash(payload) != binding["asset_sha256"]):
                    raise BuildError("Private texture replacement no longer matches its authored binding")
                replacements[identifier] = payload
            texture_overlays, texture_changes = context.patch(replacements)
            changed_ids = set()
            for change in texture_changes:
                identifier = change.get("semantic_id")
                if (identifier not in replacements or identifier in changed_ids or
                        change.get("scope") != "TIM-image-and-palette-payload-only" or
                        change.get("after_sha256") != _hash(replacements[identifier]) or
                        change.get("before_sha256") != _hash(context.original_tim(identifier)) or
                        change.get("byte_length") != len(replacements[identifier])):
                    raise BuildError("Texture audit does not match the freshly verified replacement")
                changed_ids.add(identifier)
                audit_edits.append({**change, "scene": scene, "field": "texture.tim"})
            expected_changes = {identifier for identifier, payload in replacements.items()
                                if payload != context.original_tim(identifier)}
            if changed_ids != expected_changes or bool(texture_overlays) != bool(texture_changes):
                raise BuildError("Texture audit omits or invents an authored replacement")
            disc_user_size = (_image.size // 2352) * 2048
            for overlay in texture_overlays:
                offset, size, payload = overlay.get("offset"), overlay.get("size"), overlay.get("payload")
                if (overlay.get("scene") != scene or type(offset) is not int or type(size) is not int or
                        offset < 0 or size <= 0 or offset + size > disc_user_size or
                        not isinstance(payload, bytes) or len(payload) != size or
                        _hash(payload) != overlay.get("sha256")):
                    raise BuildError("Texture overlay has invalid guarded disc coordinates or payload")
                original = _image.read_user(0, offset, size, disc_user_size)
                if _hash(original) != overlay.get("expected_sha256") or original == payload:
                    raise BuildError("Texture overlay disagrees with the original disc span")
                overlays.append({**overlay, "file": f"assets/{scene}-texture-{offset:08x}.bin"})
    build_kind = "authored" if overlays else "retail"
    ordered = sorted(overlays, key=lambda item: item["offset"])
    if any(a["offset"] + a["size"] > b["offset"] for a, b in zip(ordered, ordered[1:])):
        raise BuildError("Generated scene overlays overlap; refusing ambiguous build")
    audit = {
        "schema_version": "legaia.build-audit.v1", "disc_sha256": disc_hash,
        "game_id": "SCUS-94254", "project_name": project.name, "build_kind": build_kind,
        "edits": audit_edits,
        "overlays": [{key: value for key, value in overlay.items() if key != "payload"} for overlay in overlays],
        "validation": {"retail_provenance": "fresh_import_match", "unchanged_opaque_bytes": True,
                       "lz_decode_round_trip": True if overlays else "not_required_unmodified_disc",
                       "live_runtime": "not_run"},
    }
    audit_bytes = (canonical_json(audit, pretty=True) + "\n").encode("utf-8")
    build_id = _hash(audit_bytes)[:16]
    package_id = "legaia.sdk." + _hash((project.name + disc_hash).encode("utf-8"))[:12]
    version = "0.1.0-" + build_id
    destination = Path(output_dir).absolute() if output_dir is not None else project.root / "Builds" / build_id
    # The server uses the default project-local path. Check its full suffix
    # before resolving, so an existing Builds junction cannot redirect writes.
    boundary = project.root if output_dir is None else destination.parent.resolve()
    _guard_output(destination, boundary)
    destination = destination.resolve()
    package_dir = destination / "package"
    has_appearance = any(change.get("scope") == "initial-man-header-only" for change in audit_edits)
    has_dialogue = any(change.get("scope") == "inline-mes-glyph-run-only" for change in audit_edits)
    has_texture = any(change.get("scope") == "TIM-image-and-palette-payload-only" for change in audit_edits)
    package_suffix = " authored actor headers" if has_appearance else (" authored placements" if overlays else " retail baseline")
    feature_name = "Authored actor headers" if has_appearance else "Authored actor placements"
    description = ("Private initial model/animation and placement headers; script compatibility is unverified."
                   if has_appearance else "Private authored field placements for the verified retail disc.")
    feature_description = ("Apply initial MAN donor assignments and X/Z placements; scripts may override appearance."
                           if has_appearance else "Apply this project's representable field X/Z placement edits.")
    if has_dialogue:
        package_suffix = " authored actor data"
        feature_name = "Authored actor data"
        description = "Private bounded MAN glyph-run text and optional initial actor headers; script controls and boundaries remain unchanged."
        feature_description = "Apply equal-span dialogue glyphs and optional actor headers; no script control edits or relocation."
    if has_texture:
        package_suffix = " authored scene data"
        feature_name = "Authored scene data"
        description = "Private layout-compatible TIM payloads and optional bounded MAN edits; retail disc spans and resource layouts remain fixed."
        feature_description = "Apply verified scene textures and optional actor/text data; no resource relocation or script control edits."
    if any(c.get("scope") == "encoded-transition-entry-only" for c in audit_edits):
        package_suffix = " authored scene data"
        feature_name = "Authored scene data"
        description = "Private bounded MAN entry-byte edits and optional actor, text and texture data."
        feature_description = "Apply verified encoded transition entries without destination or resource relocation."
    lines = [
        "format_version = 6", f"id = {json.dumps(package_id)}", f"version = {json.dumps(version)}",
        f"name = {json.dumps(project.name + package_suffix)}",
        'author = "Local SDK project"', f"description = {json.dumps(description)}",
        'license = "Private user-owned retail derivative; not for redistribution"', 'resolver = "declarative"',
        "", "[[target]]", 'game_id = "SCUS-94254"', f'disc_sha256 = "{disc_hash}"',
        "", "[[feature]]", 'id = "placements"', f"name = {json.dumps(feature_name)}",
        f"description = {json.dumps(feature_description)}",
        'group = "Scene authoring"', "default_enabled = false",
    ]
    for overlay in overlays:
        lines.extend(["", "[[overlay]]", 'feature = "placements"', 'target = "disc_user"',
                      f'offset = {overlay["offset"]}', f'file = "{overlay["file"]}"',
                      f'sha256 = "{overlay["sha256"]}"', f'expected_sha256 = "{overlay["expected_sha256"]}"'])
    # Validate TOML before writing any output.
    import tomllib
    manifest = ("\n".join(lines) + "\n").encode("utf-8")
    tomllib.loads(manifest.decode("utf-8"))
    expected_files = {"manifest.toml", *(overlay["file"] for overlay in overlays)}
    if package_dir.exists():
        _guard_output(package_dir, boundary)
        present_files = set()
        for path in package_dir.rglob("*"):
            _guard_output(path, boundary)
            if path.is_file():
                present_files.add(path.relative_to(package_dir).as_posix())
        if present_files - expected_files:
            raise BuildError("Package directory contains unrelated files; choose a new output directory")
    _write_exact(destination / ".gitignore", b"*\n", boundary)
    for overlay in overlays:
        _write_exact(package_dir / overlay["file"], overlay["payload"], boundary)
    _write_exact(package_dir / "manifest.toml", manifest, boundary)
    _write_exact(destination / "build-audit.json", audit_bytes, boundary)
    archive_path = destination / f"{package_id}-{version}.psxmod"
    private_temp = Path(tempfile.mkdtemp(prefix="pack-", dir=destination))
    temporary_archive = private_temp / "package.psxmod"
    packer = Path(__file__).resolve().parents[3] / "tools" / "psxmod_pack.py"
    packed = subprocess.run([sys.executable, str(packer), str(package_dir), str(temporary_archive)],
                            capture_output=True, text=True)
    if packed.returncode:
        raise BuildError("Generic psxmod packer failed: " + packed.stderr.strip())
    archive_bytes = temporary_archive.read_bytes()
    _write_exact(archive_path, archive_bytes, boundary)
    temporary_archive.unlink()
    private_temp.rmdir()
    # Confirm the framework packer's archive retains the manifest and payloads.
    with zipfile.ZipFile(archive_path) as archive_file:
        if archive_file.read("manifest.toml") != manifest:
            raise BuildError("Packaged manifest changed during packing")
        for overlay in overlays:
            if _hash(archive_file.read(overlay["file"])) != overlay["sha256"]:
                raise BuildError("Packaged overlay payload hash mismatch")
    return {
        "path": str(archive_path), "audit": str(destination / "build-audit.json"), "build_kind": build_kind,
        "authored_state_key": authored_state_key(project), "report": build_report(audit),
        "package_directory": str(package_dir), "package_id": package_id, "version": version,
        "sha256": _hash(archive_bytes), "changed_fields": len(audit_edits), "overlay_count": len(overlays),
        **({"changed_fields_unit": "authored fields/runs/textures"} if has_texture else
           {"changed_fields_unit": "authored fields/runs"} if has_dialogue else {}),
        "runtime_status": "package_built_not_launched", "feature_id": "placements",
        "install_instruction": (f"Import the .psxmod in the runtime mod manager, enable {feature_name}, then launch against the matching stock disc."
                                if overlays else "This verified retail baseline has no modified bytes. Build & Run starts a fresh private run without previous placement overlays."),
    }
