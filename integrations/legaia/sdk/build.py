"""Build private, runtime-consumable disc overlays from authored MAN placements."""
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
    MAN donor model/animation assignments, and unchanged retail
    builds after clearing overrides. The input disc
    and imported metadata remain unchanged. Installation/enabling and a live
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
        if identifier not in entity_lookup:
            raise BuildError(f"Authored entity has no imported provenance: {identifier}")
        scene_id, actor = entity_lookup[identifier]
        if (not isinstance(components, dict) or not components or
                set(components) - {"Transform", "ActorAppearance"}):
            raise BuildError(f"{identifier}: only authored Transform.position and ActorAppearance donor assignments can be built")
        edits = scene_edits.setdefault(scene_id, {"positions": {}, "assignments": {}})
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

    # Reimport before using authored locators: modified/stale metadata cannot
    # redirect an otherwise disc-identity-valid overlay onto unrelated bytes.
    for scene_id in scene_edits or project.imports:
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
                baseline = decompress_lzs(original_span, descriptor.size)[0]
                changed, changes = context.patch(assignments, original=baseline)
                for change in changes:
                    change["donor_entity_id"] = edits["assignments"][change["record_index"]]
                changed, position_changes = patch_man_positions(changed, scene, edits["positions"])
                changes.extend(position_changes)
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
            changed_offsets = {change["decoded_byte_offset"] for change in changes}
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
    package_suffix = " authored actor headers" if has_appearance else (" authored placements" if overlays else " retail baseline")
    feature_name = "Authored actor headers" if has_appearance else "Authored actor placements"
    description = ("Private initial model/animation and placement headers; script compatibility is unverified."
                   if has_appearance else "Private authored field placements for the verified retail disc.")
    feature_description = ("Apply initial MAN donor assignments and X/Z placements; scripts may override appearance."
                           if has_appearance else "Apply this project's representable field X/Z placement edits.")
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
        "package_directory": str(package_dir), "package_id": package_id, "version": version,
        "sha256": _hash(archive_bytes), "changed_fields": len(audit_edits), "overlay_count": len(overlays),
        "runtime_status": "package_built_not_launched", "feature_id": "placements",
        "install_instruction": (f"Import the .psxmod in the runtime mod manager, enable {feature_name}, then launch against the matching stock disc."
                                if overlays else "This verified retail baseline has no modified bytes. Build & Run starts a fresh private run without previous placement overlays."),
    }
