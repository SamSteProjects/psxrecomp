"""Build private disc overlays from bounded authored MAN data and scene TIMs."""
from __future__ import annotations

from copy import deepcopy
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
                                "actor_drafts": getattr(project, "actor_drafts", {}),
                                "textures": getattr(project, "texture_overrides", {}),
                                "models": getattr(project, "model_overrides", {})}).encode("utf-8"))


def package_change_kinds(edits) -> list[str]:
    """Describe emitted audit scopes, without inferring unexecuted game behavior."""
    labels = {
        'initial-man-placement-only': 'actor positions',
        'initial-man-header-only': 'initial actor appearance',
        'inline-mes-glyph-run-only': 'dialogue text',
        'TIM-image-and-palette-payload-only': 'textures',
        'shared-MAP-transform-only': 'shared scenery transforms',
        'instance-MAP-transform-only': 'individual decoration transforms',
        'encoded-transition-entry-only': 'transition entries',
        'script-movement-target-only': 'script movement targets',
        'script-flag-bit-only': 'script flag operands',
        'TMD-vertex-normal-XYZ-only': 'model shapes',
        'source-MAP-wall-bit-only': 'source collision walls',
        'shared-scene-animation-record': 'animation channels',
    }
    return sorted({labels.get(edit.get('scope', 'initial-man-placement-only'), 'other audited scene data') for edit in edits})


def build_report(audit) -> dict:
    """Present only audited changes that actually entered the emitted package."""
    changes = []
    for change in audit["edits"]:
        field = change["field"]
        if change.get('scope') == 'script-movement-target-only':
            field = 'movement.' + field
            before, after = change['before_coordinate'], change['after_coordinate']
        elif change.get("scope") == "script-flag-bit-only":
            field = "flag.bit"
            before, after = change["before_bit"], change["after_bit"]
        elif field == "dialogue.text":
            before = bytes.fromhex(change["before_hex"]).decode("ascii")
            after = bytes.fromhex(change["after_hex"]).decode("ascii")
        elif field in ("texture.tim", "model.shape"):
            before, after = change["before_sha256"], change["after_sha256"]
        else:
            before = change.get("before_value", change.get("before_byte"))
            after = change.get("after_value", change.get("after_byte"))
        changes.append({"scene": change["scene"], "asset_id": change.get("flag_id", change.get("movement_id", change.get("transition_id", change.get("run_id", change["semantic_id"])))),
                        "owner_id": change["semantic_id"],
                        "field": field, "before": before, "after": after,
                        **({"frame_index": change["frame_index"], "object_index": change["object_index"],
                            "authored_owners": list(change.get("axis_owners", change.get("authored_owners", []))),
                            "contributor_scope": "axis" if "axis_owners" in change else "clip"}
                           if change.get("scope") == "shared-scene-animation-record" else {}),
                        **({'payload_changes': deepcopy(change['payload_changes'])}
                           if field == 'texture.tim' and 'payload_changes' in change else {}),
                        **({'coordinate_changes': [dict(row) for row in change['coordinate_changes']]}
                           if field == 'model.shape' and 'coordinate_changes' in change else {}),
                        **({"affected_grid_cell_count":len(change["affected_grid_cells"])}
                           if "affected_grid_cells" in change else {}),
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


def _merge_movement_patch(baseline, working, patched, changes, expected, previous):
    from importer.movement_authoring import validate_movement_values
    ENTRY_FIELDS = {'x': 0, 'z': 1, 'move_id': 3}
    if not isinstance(patched, bytes) or len(patched) != len(baseline) or len(working) != len(baseline):
        raise BuildError("Movement patch changed MAN length")
    occupied = {i for c in previous for i in range(c["decoded_byte_offset"], c["decoded_byte_offset"] + c.get("byte_length", 1))}
    audited = set()
    result = bytearray(working)
    digest = _hash(baseline)
    for c in changes:
        entry = expected.get(c.get("movement_id"))
        offset, field = c.get("decoded_byte_offset"), c.get("field")
        offsets = entry.get("operand_offsets", ENTRY_FIELDS) if entry else {}
        if (entry is None or field not in offsets or type(offset) is not int or
                not 0 <= offset < len(baseline) or
                offset != entry["decoded_byte_offset"] + offsets[field] or
                c.get("owner_id") != entry["owner_id"] or
                c.get("source_record_sha256") != entry["source_record_sha256"] or
                c.get("source_decoded_man_sha256") != digest or
                c.get("before_byte") != baseline[offset] or c.get("after_byte") != patched[offset]):
            raise BuildError("Movement audit disagrees with verified source bytes")
        if offset in occupied or offset in audited:
            raise BuildError("Movement patch overlaps another authored MAN span")
        encoded = validate_movement_values(entry['requested_values'])
        if field not in encoded or c.get('after_byte') != encoded[field]:
            raise BuildError('Movement patch differs from requested coordinates')
        audited.add(offset)
        result[offset] = patched[offset]
    if any(a != b and i not in audited for i, (a, b) in enumerate(zip(baseline, patched))):
        raise BuildError("Movement patch changed an unaudited MAN byte")
    return bytes(result)


def _merge_flag_patch(baseline, working, patched, changes, expected, previous):
    """Compose independently verified low-five-bit changes without sharing spans."""
    from importer.flag_authoring import validate_flag_values
    if not isinstance(patched, bytes) or len(patched) != len(baseline) or len(working) != len(baseline):
        raise BuildError("Flag patch changed MAN length")
    occupied = {i for c in previous for i in range(c["decoded_byte_offset"], c["decoded_byte_offset"] + c.get("byte_length", 1))}
    audited = set()
    result = bytearray(working)
    for change in changes:
        target = expected.get(change.get('flag_id'))
        offset = change.get('decoded_byte_offset')
        if (target is None or change.get('field') != 'bit' or type(offset) is not int or
                not 0 <= offset < len(baseline) or offset != target['decoded_byte_offset'] or
                change.get('owner_id') != target['owner_id'] or
                change.get('source_record_sha256') != target['source_record_sha256'] or
                change.get('source_decoded_man_sha256') != _hash(baseline) or
                change.get('mnemonic') != target['mnemonic'] or
                change.get('target_context') != target['target_context'] or
                change.get('before_byte') != baseline[offset] or change.get('after_byte') != patched[offset]):
            raise BuildError('Flag audit disagrees with verified source bytes')
        bit = validate_flag_values(target['requested_values'])
        if (change.get('before_bit') != (baseline[offset] & 31) or
                change.get('after_bit') != bit or patched[offset] != ((baseline[offset] & 224) | bit)):
            raise BuildError('Flag patch differs from requested bit or upper operand bits')
        if offset in occupied or offset in audited or working[offset] != baseline[offset]:
            raise BuildError('Flag patch overlaps another authored MAN span')
        audited.add(offset)
        result[offset] = patched[offset]
    if any(a != b and i not in audited for i,(a,b) in enumerate(zip(baseline,patched))):
        raise BuildError('Flag patch changed an unaudited MAN byte')
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
    if getattr(project, 'actor_drafts', {}):
        raise BuildError('New NPC drafts are not yet connected to playable Build; remove drafts before building existing overrides')
    if not project.disc_path:
        raise BuildError("Build requires the project's verified user-owned retail disc")
    if not project.imports:
        raise BuildError("Build requires at least one verified imported scene")
    scene_edits: dict[str, dict] = {}
    environment_edits = {}
    collision_edits = {}
    animation_edits = {}
    entity_lookup = {actor["semantic_id"]: (scene_id, actor)
                     for scene_id, document in project.imports.items()
                     for actor in document["actors"]}
    for identifier, components in sorted(project.overrides.items()):
        if isinstance(components, dict) and "Collision" in components:
            project._validate_collision(identifier, components["Collision"])
            collision_edits[identifier] = components["Collision"]
            components = {k:v for k,v in components.items() if k != "Collision"}
            if not components:
                continue
        if isinstance(components, dict) and "AnimationChannels" in components:
            project._validate_animation_override(identifier, components["AnimationChannels"])
            scene_id, _actor = entity_lookup[identifier]
            animation_edits.setdefault(scene_id, {})[identifier] = components["AnimationChannels"]
            components = {k:v for k,v in components.items() if k != "AnimationChannels"}
            if not components:
                continue
        if isinstance(components, dict) and "Environment" in components:
            project._validate_environment(identifier, components["Environment"])
            environment_edits[identifier] = components["Environment"]
            components = {k:v for k,v in components.items() if k != "Environment"}
            if not components:
                continue
        if isinstance(components, dict) and "ScriptMovement" in components:
            project._validate_movements(identifier, components["ScriptMovement"])
            document = project._dialogue_document(identifier)
            scene_id = "scene://" + document["scene"]["name"]
            edits = scene_edits.setdefault(scene_id, {"positions": {}, "assignments": {}, "dialogues": {}, "transitions": {}, "movements": {}, "flags": {}})
            edits["movements"][identifier] = components["ScriptMovement"]["entries"]
            components = {k: v for k, v in components.items() if k != "ScriptMovement"}
            if not components:
                continue
        if isinstance(components, dict) and "ScriptFlags" in components:
            project._validate_flags(identifier, components["ScriptFlags"])
            document = project._dialogue_document(identifier)
            scene_id = "scene://" + document["scene"]["name"]
            edits = scene_edits.setdefault(scene_id, {"positions": {}, "assignments": {}, "dialogues": {}, "transitions": {}, "movements": {}, "flags": {}})
            edits["flags"][identifier] = components["ScriptFlags"]["entries"]
            components = {k: v for k, v in components.items() if k != "ScriptFlags"}
            if not components:
                continue
        if isinstance(components, dict) and "Transitions" in components:
            project._validate_transitions(identifier, components["Transitions"])
            document = project._dialogue_document(identifier)
            scene_id = "scene://" + document["scene"]["name"]
            edits = scene_edits.setdefault(scene_id, {"positions": {}, "assignments": {}, "dialogues": {}, "transitions": {}, "movements": {}, "flags": {}})
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
            edits = scene_edits.setdefault(scene_id, {"positions": {}, "assignments": {}, "dialogues": {}, "transitions": {}, "movements": {}, "flags": {}})
            edits["dialogues"][identifier] = dialogue["runs"]
            continue
        if identifier not in entity_lookup:
            raise BuildError(f"Authored entity has no imported provenance: {identifier}")
        scene_id, actor = entity_lookup[identifier]
        if (not isinstance(components, dict) or not components or
                set(components) - {"Transform", "ActorAppearance", "Dialogue"}):
            raise BuildError(f"{identifier}: only authored Transform.position, ActorAppearance and bounded Dialogue runs can be built")
        edits = scene_edits.setdefault(scene_id, {"positions": {}, "assignments": {}, "dialogues": {}, "transitions": {}, "movements": {}, "flags": {}})
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
    for scene_id in sorted(set(scene_edits) | set(texture_edits) | set(environment_edits) | set(animation_edits) | set(collision_edits)) or project.imports:
        document = project.imports[scene_id]
        fresh = import_scene(project.disc_path, document["scene"]["name"])
        if canonical_json(document) != canonical_json(fresh):
            raise BuildError(f"Imported provenance for {scene_id} no longer matches a fresh retail import")

    overlays = []
    audit_edits = []
    with _disc_context(project.disc_path) as (_image, disc_hash, mapping, archive):
        from importer.model_authoring import model_shape_overlays
        model_assets, model_payloads = {}, {}
        for identifier, binding in sorted(getattr(project, 'model_overrides', {}).items()):
            model_payloads[identifier] = project.read_model_replacement(identifier, binding)
            document = project.imports[binding['source_scene_id']]
            model_assets[identifier] = next(a for a in document['assets']['models'] if a['semantic_id'] == identifier)
        shape_overlays, shape_changes = model_shape_overlays(archive, model_assets, model_payloads)
        for overlay in shape_overlays:
            if _hash(_image.read_user(0, overlay['offset'], overlay['size'], (_image.size // 2352)*2048)) != overlay['expected_sha256']:
                raise BuildError('Model shape overlay differs from its original disc span')
            overlays.append({**overlay, 'scene':'shared-model-source', 'file':f"assets/model-shape-{overlay['offset']:08x}.bin"})
        audit_edits.extend({**change, 'scene':project.imports[project.model_overrides[change['semantic_id']]['source_scene_id']]['scene']['name']} for change in shape_changes)
        for scene_id, bindings in sorted(animation_edits.items()):
            from importer.scene_animation import load_scene_actor_animation_catalog
            from importer.serialization import serialize_lzs_decoded
            scene = project.imports[scene_id]["scene"]["name"]
            catalog = load_scene_actor_animation_catalog(project.disc_path, scene)
            changed, changes = catalog.authored_bank(bindings)
            if not changes:
                continue
            source = catalog._source
            entry = archive.entry(source["prot_entry_index"])
            body = archive.read_entry(entry)
            offset, consumed = source["compressed_stream_offset"], source["compressed_bytes_consumed"]
            original = body[offset:offset + consumed]
            replacement, sizes = serialize_lzs_decoded(original, len(catalog._body), changed, scene + " animation")
            location = (archive.node.extent_lba + entry.start_lba) * 2048 + offset
            if _image.read_user(0, location, len(original), (_image.size // 2352) * 2048) != original:
                raise BuildError("Animation overlay differs from its verified disc span")
            overlays.append({"scene": scene, "offset": location, "size": len(replacement),
                             "file": f"assets/{scene}-animation.lzs", "payload": replacement,
                             "sha256": _hash(replacement), "expected_sha256": _hash(original),
                             "decoded_before_sha256": _hash(catalog._body), "decoded_after_sha256": _hash(changed), **sizes})
            audit_edits.extend({**change, "scene": scene, "semantic_id": change["animation_id"]} for change in changes)
        for scene_id in sorted(set(environment_edits) | set(collision_edits)):
            binding = environment_edits.get(scene_id)
            from importer.environment_authoring import patch_environment_overrides
            from importer.environment import load_environment_placements
            document = project.imports[scene_id]
            scene = document["scene"]["name"]
            if document["source"]["disc_identity"] != "sha256:" + disc_hash:
                raise BuildError(f"Source disc identity does not match {scene_id}")
            source = load_environment_placements(project.disc_path, scene)["source_record"]
            entry = archive.entry(source["map_entry_index"])
            original = archive.read_entry(entry, extended=True)
            changed, changes = patch_environment_overrides(original, binding) if binding else (original, [])
            wall_changes = []
            if scene_id in collision_edits:
                from importer.collision_authoring import patch_collision_walls
                walls = collision_edits[scene_id]
                wall_data, wall_changes = patch_collision_walls(original, walls["source_sha256"], walls["edits"])
                merged = bytearray(changed)
                for row in wall_changes:
                    offset, mask = row["byte_offset"], row["bit_mask"]
                    if (changed[offset] ^ original[offset]) & mask:
                        raise BuildError("Collision wall edit overlaps a scenery edit")
                    merged[offset] = (merged[offset] & ~mask) | (wall_data[offset] & mask)
                changed = bytes(merged)
            allowed = set()
            for row in changes:
                if 'allocation' in row:
                    allocation = row['allocation']
                    for prefix in ('descriptor', 'grid'):
                        start = allocation[prefix+'_byte_offset']
                        allowed.update(range(start, start+allocation[prefix+'_byte_length']))
                else:
                    allowed.update(range(row['byte_offset'], row['byte_offset']+2))
            allowed.update(row["byte_offset"] for row in wall_changes)
            if len(changed) != len(original) or any(a != b and i not in allowed for i,(a,b) in enumerate(zip(original,changed))):
                raise BuildError("Environment patch changed bytes outside audited transform axes")
            location = (archive.node.extent_lba + entry.start_lba) * 2048
            disc_user_size = (_image.size // 2352) * 2048
            if _image.read_user(0, location, len(original), disc_user_size) != original:
                raise BuildError("Environment MAP overlay differs from its original disc span")
            if changes or wall_changes:
                overlays.append({"scene":scene, "offset":location, "size":len(changed),
                                 "file":f"assets/{scene}-environment.map", "payload":changed,
                                 "sha256":_hash(changed), "expected_sha256":_hash(original)})
                for row in changes:
                    audit_edits.append({**row, "scene":scene,
                        "semantic_id":(f"environment://{scene}/field-map/decorations/{row['allocation']['cell_index']:05d}"
                                       if 'allocation' in row else f"environment://{scene}/field-map/records/{row['record_index']:03d}"),
                        "scope":row.get('scope', 'shared-MAP-transform-only')})
                audit_edits.extend({**row, "scene": scene, "semantic_id": f"collision://{scene}/field-map"} for row in wall_changes)
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
            if edits["assignments"] or edits["dialogues"] or edits["transitions"] or edits["movements"] or edits["flags"]:
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
            if edits["assignments"] or edits["dialogues"] or edits["transitions"] or edits["movements"] or edits["flags"]:
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
                if edits["movements"]:
                    from importer.movement_authoring import load_movement_authoring_context
                    context = load_movement_authoring_context(project.disc_path, scene)
                    requested, expected = {}, {}
                    for owner, entries in edits["movements"].items():
                        allowed = {e["semantic_id"]: e for e in context.options(owner)["targets"]}
                        for key, values in entries.items():
                            if key not in allowed or key in requested:
                                raise BuildError("Movement is not uniquely owned by the verified source")
                            requested[key], expected[key] = values, dict(allowed[key], requested_values=values)
                    movement_man, movement_changes = context.patch(requested, original=baseline)
                    changed = _merge_movement_patch(baseline, changed, movement_man,
                                                      movement_changes, expected, changes)
                    for change in movement_changes:
                        change.update(semantic_id=change["owner_id"],
                                      record_index=int(change["owner_id"].rsplit("/", 1)[1]),
                                      scope="script-movement-target-only")
                    changes.extend(movement_changes)
                if edits["flags"]:
                    from importer.flag_authoring import load_flag_authoring_context
                    context = load_flag_authoring_context(project.disc_path, scene)
                    requested, expected = {}, {}
                    for owner, entries in edits["flags"].items():
                        allowed = {e["semantic_id"]: e for e in context.options(owner)["targets"]}
                        for key, values in entries.items():
                            if key not in allowed or key in requested:
                                raise BuildError("Flag operand is not uniquely owned by the verified source")
                            requested[key], expected[key] = values, dict(allowed[key], requested_values=values)
                    flag_man, flag_changes = context.patch(requested, original=baseline)
                    changed = _merge_flag_patch(baseline, changed, flag_man,
                                                      flag_changes, expected, changes)
                    for change in flag_changes:
                        change.update(semantic_id=change["owner_id"],
                                      record_index=int(change["owner_id"].rsplit("/", 1)[1]),
                                      scope="script-flag-bit-only")
                    changes.extend(flag_changes)
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
                       "lz_decode_round_trip": (True if any(o["file"].endswith(('-man.lzs', '-animation.lzs')) or 'decoded_after_sha256' in o for o in overlays)
                                                else "not_required_no_compressed_scene_overlay" if overlays else "not_required_unmodified_disc"),
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
    if any(c.get("scope") in ("shared-MAP-transform-only", "instance-MAP-transform-only") for c in audit_edits):
        package_suffix = " authored scene data"
        feature_name = "Authored scene data"
        description = "Private source-bound scene edits including MAP placement transforms."
        feature_description = "Apply shared scenery transforms and individual static decoration overrides."
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
    if any(c.get('scope') == 'script-movement-target-only' for c in audit_edits):
        package_suffix = ' authored scene data'
        feature_name = 'Authored scene data'
        description = 'Private fixed-width script movement targets and optional authored scene data.'
        feature_description = 'Apply verified MOVE_TO/NPC_RUN X/Z operands; execution and gameplay remain unverified.'
    if any(c.get('scope') == 'script-flag-bit-only' for c in audit_edits):
        package_suffix = ' authored scene data'
        feature_name = 'Authored scene data'
    if any(c.get('scope') == 'TMD-vertex-normal-XYZ-only' for c in audit_edits):
        package_suffix = ' authored scene data'
        feature_name = 'Authored scene data'
        description = 'Private source-bound model shapes and optional authored scene data.'
        feature_description = 'Apply verified model coordinate edits and other packaged overrides; model topology and materials remain source-owned.'
    change_kinds = package_change_kinds(audit_edits)
    if len(change_kinds) > 1 or any(kind in change_kinds for kind in ('animation channels', 'source collision walls', 'other audited scene data')):
        package_suffix = ' authored scene data'
        feature_name = 'Authored scene data'
    if change_kinds:
        description = 'Private source-bound edits: ' + ', '.join(change_kinds) + '.'
        feature_description = 'Apply packaged edits: ' + ', '.join(change_kinds) + '. Gameplay remains unverified.'
        if has_appearance:
            feature_description += ' Initial assignments only; scripts may override appearance.'
        if has_dialogue:
            feature_description += ' Dialogue: glyph edits only; no script control edits or relocation.'
        if has_texture:
            feature_description += ' Textures: layout-compatible payloads; no resource relocation.'
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
