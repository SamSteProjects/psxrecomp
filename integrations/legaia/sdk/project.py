"""Metadata-backed project model. Imported evidence never doubles as editable state."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
import uuid
from typing import Any


class ProjectError(ValueError):
    pass


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation never truncates an unrelated or symlinked predictable .tmp.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def read_metadata_json(path: Path) -> dict:
    # Project/import documents contain metadata, never geometry or retail payloads.
    if path.stat().st_size > 64 * 1024 * 1024:
        raise ProjectError("Project metadata document exceeds the 64 MiB limit")
    def reject_constant(value: str) -> None:
        raise ProjectError("Nonfinite JSON value: " + value)
    value = json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant)
    if not isinstance(value, dict):
        raise ProjectError("Project metadata must be a JSON object")
    return value


class AssetDatabase:
    """Stable structural identities scoped to one verified retail disc build."""

    def __init__(self) -> None:
        self.records: dict[str, dict] = {}
        self.resource_catalogs: dict[str, dict] = {}

    def register_resources(self, scene_id: str, source_key: str, records: list[dict], limitations: list[str]) -> dict:
        """Replace a verified derived catalog without mutating imported project facts."""
        indexed = {}
        for item in records:
            identifier = item.get("semantic_id")
            kind = item.get("asset_kind")
            if not isinstance(identifier, str) or kind not in ("texture", "animation", "script", "dialogue") or identifier in indexed:
                raise ProjectError("Resource catalog has an invalid or duplicate identity")
            record = deepcopy(item)
            record.update(id=identifier, kind=kind, layer="derived", scene_id=scene_id)
            indexed[identifier] = record
        result = {"scene_id": scene_id, "source_key": source_key,
                  "records": [indexed[key] for key in sorted(indexed)], "limitations": list(limitations)}
        self.resource_catalogs[scene_id] = result
        return deepcopy(result)

    def ingest(self, document: dict) -> None:
        disc = document["source"]["disc_identity"]
        for model in document.get("assets", {}).get("models", []):
            identifier = model["semantic_id"]
            record = deepcopy(model)
            record.update(id=identifier, kind="model", layer="imported", disc_identity=disc,
                          dependencies=[], preview_status="not_decoded")
            existing = self.records.get(identifier)
            if existing and existing["disc_identity"] != disc:
                raise ProjectError(f"Asset identity belongs to another disc: {identifier}")
            # Global model IDs may recur in several scenes; retain their original provenance.
            if existing is None:
                self.records[identifier] = record


class ProjectService:
    FORMAT = "legaia.project.v1"

    def __init__(self, root: Path, name: str = "Legaia project") -> None:
        self.root = root.resolve()
        self.name = name
        self.imports: dict[str, dict] = {}
        self.assets = AssetDatabase()
        self.overrides: dict[str, dict] = {}
        self.actor_templates: dict[str, dict] = {}
        self.texture_overrides: dict[str, dict] = {}
        self.active_scene: str | None = None
        self.selected: str | None = None
        self.undo_stack: list[dict] = []
        self.redo_stack: list[dict] = []
        self.saved_digest: str | None = None
        self.disc_path: str | None = None
        self.mode = "edit"
        self._live_correlation: dict | None = None

    def correlate_runtime(self, live_status: dict) -> dict:
        from integrations.legaia.observer.correlation import correlate
        # Always replace prior observations, including on disconnect/rejection.
        # Nothing from this layer participates in save, dirty state or commands.
        self._live_correlation = None
        result = correlate(self.imports.get(self.active_scene), live_status)
        self._live_correlation = deepcopy(result)
        return self._current_correlation()

    def _current_correlation(self) -> dict:
        from integrations.legaia.observer.correlation import unavailable, _digest
        document = self.imports.get(self.active_scene)
        current = self._live_correlation
        if current and current.get("available"):
            if document is None or current.get("import_digest") != _digest(document):
                self._live_correlation = None
                return unavailable("Imported evidence changed since observation")
        result = deepcopy(self._live_correlation) if self._live_correlation else unavailable("No accepted runtime correlation")
        for identifier, entry in result.get("entities", {}).items():
            authored = self.overrides.get(identifier, {}).get("Transform", {}).get("position", {})
            for candidate in entry.get("candidates", []):
                candidate["authored_comparison"] = {
                    "basis": "guarded-MAN-placement-header; candidate identity remains unconfirmed",
                    "axes": {axis: {"authored": value,
                                    "observed_header": candidate["placement_position"].get(axis),
                                    "matches": candidate["placement_position"].get(axis) == value}
                             for axis, value in authored.items() if axis in ("x", "z")}}
        return result

    def _document(self) -> dict:
        return {"format": self.FORMAT, "name": self.name,
                "retail_source": {"disc_path": self.disc_path,
                                  "disc_identity": next(iter(self.imports.values()))["source"]["disc_identity"] if self.imports else None},
                "imports": [{"scene": key, "file": f"Imported/{digest(value)}.json", "sha256": digest(value)}
                            for key, value in sorted(self.imports.items())],
                "active_scene": self.active_scene, "authored": deepcopy(self.overrides),
                "actor_templates": deepcopy(self.actor_templates),
                **({"texture_overrides": deepcopy(self.texture_overrides)} if self.texture_overrides else {})}

    @property
    def dirty(self) -> bool:
        return digest(self._document()) != self.saved_digest

    def import_metadata(self, metadata: dict, disc_path: str | None = None) -> None:
        if not isinstance(metadata, dict) or not isinstance(metadata.get("scene"), dict) or not isinstance(metadata.get("source"), dict):
            raise ProjectError("Imported metadata requires scene and source objects")
        if not all(isinstance(metadata["scene"].get(key), str) for key in ("semantic_id", "name")):
            raise ProjectError("Imported scene identity and name must be strings")
        if not isinstance(metadata.get("actors"), list) or not isinstance(metadata.get("assets", {}), dict):
            raise ProjectError("Invalid imported scene collections")
        models = metadata.get("assets", {}).get("models", [])
        if not isinstance(models, list) or any(not isinstance(model, dict) or not isinstance(model.get("semantic_id"), str) for model in models):
            raise ProjectError("Invalid imported model asset records")
        for actor in metadata["actors"]:
            if not isinstance(actor, dict) or not isinstance(actor.get("semantic_id"), str) or not all(isinstance(actor.get(key), dict) for key in ("imported_transform", "model_reference", "placement_fields")):
                raise ProjectError("Invalid imported actor record")
            position = actor["imported_transform"].get("position")
            if not isinstance(position, dict) or set(position) != {"x", "y", "z"}:
                raise ProjectError("Imported actor requires X/Y/Z position evidence")
            if any(value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)) for value in position.values()):
                raise ProjectError("Imported positions must be finite numbers or explicit unknowns")
        document = deepcopy(metadata)
        scene_id = document["scene"]["semantic_id"]
        if self.imports and next(iter(self.imports.values()))["source"]["disc_identity"] != document["source"]["disc_identity"]:
            raise ProjectError("A project cannot mix retail disc builds")
        ids = [actor["semantic_id"] for actor in document["actors"]]
        if len(ids) != len(set(ids)):
            raise ProjectError("Imported scene has duplicate actor identities")
        # Reimport cannot silently reinterpret existing authored edits.
        previous = self.imports.get(scene_id)
        if previous and digest(previous) != digest(document):
            affected = set(ids) | {actor["semantic_id"] for actor in previous["actors"]}
            if any(key in affected for key in self.overrides) or any(entry["entity_id"] in affected for entry in self.undo_stack + self.redo_stack):
                raise ProjectError("Imported evidence changed under authored edits or command history; create a new project or resolve edits first")
        other_ids = {actor["semantic_id"] for key, imported in self.imports.items() if key != scene_id for actor in imported["actors"]}
        if other_ids.intersection(ids):
            raise ProjectError("Imported actor identity collides with another scene")
        # Validate a staged project before publishing any imported or asset state.
        staged = deepcopy(self)
        staged.imports[scene_id] = document
        staged.active_scene = scene_id
        staged.selected = ids[0] if ids else None
        if disc_path:
            staged.disc_path = str(Path(disc_path).resolve())
        staged.assets = AssetDatabase()
        for imported in staged.imports.values():
            staged.assets.ingest(imported)
        try:
            canonical(staged.state())
        except (KeyError, TypeError, AttributeError, ValueError) as exc:
            raise ProjectError("Imported metadata is not a valid editor scene: " + str(exc)) from exc
        self._live_correlation = None
        self.imports = staged.imports
        self.assets = staged.assets
        self.active_scene = staged.active_scene
        self.selected = staged.selected
        self.disc_path = staged.disc_path

    def _actor(self, identifier: str) -> dict:
        for document in self.imports.values():
            for actor in document["actors"]:
                if actor["semantic_id"] == identifier:
                    return actor
        raise ProjectError(f"Unknown entity: {identifier}")

    def select(self, identifier: str | None) -> None:
        if identifier is not None:
            self._actor(identifier)
            if not any(a["semantic_id"] == identifier for a in self.imports[self.active_scene]["actors"]):
                raise ProjectError("Entity is outside the active scene")
        self.selected = identifier

    def _appearance_binding(self, identifier: str, value: dict) -> tuple[dict, dict, dict]:
        if not isinstance(value, dict) or set(value) != {"donor_entity_id"} or not isinstance(value["donor_entity_id"], str):
            raise ProjectError("Actor appearance requires one imported donor_entity_id")
        actor = self._actor(identifier)
        document = next(doc for doc in self.imports.values() if any(a["semantic_id"] == identifier for a in doc["actors"]))
        donor = next((a for a in document["actors"] if a["semantic_id"] == value["donor_entity_id"]), None)
        if donor is None:
            raise ProjectError("Appearance donor must belong to the actor's imported scene")
        counts = []
        for item in (actor, donor):
            reference = item["model_reference"]
            model, animation = reference.get("model_index"), item["placement_fields"].get("animation_id")
            asset = self.assets.records.get(reference.get("asset_semantic_id"), {})
            count = asset.get("source_record", {}).get("object_count")
            if (type(model) is not int or not 0 <= model < 240 or type(animation) is not int or
                    not 1 <= animation <= 255 or type(count) is not int or count < 1):
                raise ProjectError("Appearance requires existing scene models with nonzero initial animation and known object counts")
            counts.append(count)
        if counts[0] != counts[1]:
            raise ProjectError("Appearance donor must have the same object count as the imported actor")
        return document, actor, donor

    def appearance_options(self, identifier: str) -> dict:
        from importer.man_assignments import load_man_assignment_context
        from importer.pipeline import _disc_context, import_scene
        if not self.disc_path:
            raise ProjectError("Appearance options require the project's user-owned disc")
        actor = self._actor(identifier)
        document = next(doc for doc in self.imports.values() if any(a["semantic_id"] == identifier for a in doc["actors"]))
        with _disc_context(self.disc_path):
            if digest(import_scene(self.disc_path, document["scene"]["name"])) != digest(document):
                raise ProjectError("Appearance source differs from freshly verified imported evidence")
            context = load_man_assignment_context(self.disc_path, document["scene"]["name"])
            support = context.options(actor["source_record"]["record_index"])
            records = {a["source_record"]["record_index"]: a for a in document["actors"]}
            options = []
            for pair in support["pairs"]:
                for index in pair["donor_records"]:
                    donor = records[index]
                    options.append({"donor_entity_id": donor["semantic_id"], "label": f"Actor {index:04d} · model {pair['model_index']} / animation {pair['animation_id']}",
                                    "asset_id": donor["model_reference"]["asset_semantic_id"],
                                    "animation_id": pair["animation_id"], "unchanged": pair["unchanged"]})
            return {"supported": support["supported"], "reason": support["reason"], "options": options,
                    "limitations": support["limitations"], "source": context.provenance()}

    def appearance_source_actor(self, identifier: str, verify_disc: bool = False) -> dict:
        value = self.overrides.get(identifier, {}).get("ActorAppearance")
        if value is None:
            return self._actor(identifier)
        _, _, donor = self._appearance_binding(identifier, value)
        if verify_disc and not any(o["donor_entity_id"] == donor["semantic_id"] for o in self.appearance_options(identifier)["options"]):
            raise ProjectError("Appearance donor is not a verified compatible initial model/animation pair")
        return donor

    def set_scene(self, identifier: str) -> None:
        if identifier not in self.imports:
            raise ProjectError("Scene has not been imported")
        self.active_scene = identifier
        self.selected = None
        self._live_correlation = None

    def _validate_dialogue(self, identifier: str, value: dict) -> None:
        from importer.dialogue_authoring import MAX_EDIT_RUNS, validate_dialogue_text, validate_run_id
        self._actor(identifier)
        if (not isinstance(value, dict) or set(value) != {"runs"} or
                not isinstance(value["runs"], dict) or not 1 <= len(value["runs"]) <= MAX_EDIT_RUNS):
            raise ProjectError("Dialogue requires a bounded nonempty text-run collection")
        for run_id, text in value["runs"].items():
            validate_run_id(identifier, run_id)
            validate_dialogue_text(text)

    def _dialogue_context(self, identifier: str):
        from importer.dialogue_authoring import load_dialogue_authoring_context
        from importer.pipeline import _disc_context, import_scene
        self._actor(identifier)
        if not self.disc_path:
            raise ProjectError("Dialogue authoring requires the project's user-owned disc")
        document = next(doc for doc in self.imports.values() if any(a["semantic_id"] == identifier for a in doc["actors"]))
        with _disc_context(self.disc_path):
            if import_scene(self.disc_path, document["scene"]["name"]) != document:
                raise ProjectError("Dialogue source differs from freshly verified imported evidence")
            return load_dialogue_authoring_context(self.disc_path, document["scene"]["name"])

    def dialogue_options(self, identifier: str) -> dict:
        result = deepcopy(self._dialogue_context(identifier).options(identifier))
        authored = self.overrides.get(identifier, {}).get("Dialogue", {}).get("runs", {})
        known = set()
        for run in result["runs"]:
            run_id = run["semantic_id"]
            known.add(run_id)
            replacement = authored.get(run_id)
            run["authored_text"] = replacement
            run["effective_text"] = run["text"] if replacement is None else replacement.ljust(run["max_length"])
            if replacement is not None and len(replacement) > run["max_length"]:
                run["effective_text"] = None
                run["validation_error"] = "Saved replacement exceeds the verified source run capacity"
        result["unresolved_overrides"] = sorted(set(authored) - known)
        return result

    def _validate_texture_binding(self, binding: dict) -> None:
        if (not isinstance(binding, dict) or set(binding) != {"asset_sha256", "byte_length", "format", "source_scene_id"}
                or binding["format"] != "tim" or type(binding["byte_length"]) is not int
                or not 1 <= binding["byte_length"] <= 1024 * 1024
                or not isinstance(binding["asset_sha256"], str) or len(binding["asset_sha256"]) != 64
                or any(c not in "0123456789abcdef" for c in binding["asset_sha256"])
                or not isinstance(binding["source_scene_id"], str) or binding["source_scene_id"] not in self.imports):
            raise ProjectError("Invalid authored TIM content reference")

    def read_texture_replacement(self, binding: dict) -> bytes:
        self._validate_texture_binding(binding)
        path = self.root / "Authored" / "Textures" / (binding["asset_sha256"] + ".tim")
        if not path.resolve().is_relative_to(self.root):
            raise ProjectError("Authored texture path escapes project root")
        if path.stat().st_size != binding["byte_length"]:
            raise ProjectError("Authored texture size disagrees with project reference")
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != binding["asset_sha256"]:
            raise ProjectError("Authored texture digest disagrees with project reference")
        return content

    def _texture_context(self, asset_id: str):
        from importer.texture_authoring import load_texture_authoring_context
        from importer.pipeline import _disc_context, import_scene
        document = self.imports.get(self.active_scene)
        if not self.disc_path or document is None or not isinstance(asset_id, str) or len(asset_id) > 512:
            raise ProjectError("Texture replacement requires an imported scene and verified texture identity")
        with _disc_context(self.disc_path):
            if import_scene(self.disc_path, document["scene"]["name"]) != document:
                raise ProjectError("Texture source differs from freshly verified imported evidence")
            context = load_texture_authoring_context(self.disc_path, document["scene"]["name"])
            context.options(asset_id)
            return context

    def set_texture_replacement(self, asset_id: str, content: bytes) -> None:
        if self.mode != "edit":
            raise ProjectError("Texture authoring requires Edit mode")
        if not isinstance(asset_id, str) or not asset_id.startswith("texture://") or len(asset_id) > 512:
            raise ProjectError("Texture replacement requires a structural texture identity")
        if not isinstance(content, bytes) or not 1 <= len(content) <= 1024 * 1024:
            raise ProjectError("Authored TIM must contain at most 1 MiB")
        if asset_id not in self.texture_overrides and len(self.texture_overrides) >= 128:
            raise ProjectError("Project supports at most 128 texture replacements")
        self._texture_context(asset_id).validate_replacement(asset_id, content)
        binding = {"asset_sha256": hashlib.sha256(content).hexdigest(), "byte_length": len(content),
                   "format": "tim", "source_scene_id": self.active_scene}
        self._validate_texture_binding(binding)
        before = deepcopy(self.texture_overrides.get(asset_id))
        if before == binding:
            return
        path = self.root / "Authored" / "Textures" / (binding["asset_sha256"] + ".tim")
        if not path.resolve().is_relative_to(self.root):
            raise ProjectError("Authored texture path escapes project root")
        if path.exists():
            self.read_texture_replacement(binding)
        else:
            atomic_write(path, content)
        self.texture_overrides[asset_id] = binding
        self.undo_stack.append({"target": "texture_overrides", "asset_id": asset_id,
                                "before": before, "after": deepcopy(binding)})
        self.redo_stack.clear()

    def command(self, command: dict) -> None:
        if self.mode != "edit":
            raise ProjectError("Authoring commands require Edit mode")
        if command.get("type") == "clear_texture_replacement":
            identifier = command.get("asset_id")
            if not isinstance(identifier, str) or not identifier.startswith("texture://"):
                raise ProjectError("Texture clear requires a structural texture identity")
            before = deepcopy(self.texture_overrides.pop(identifier, None))
            if before is not None:
                self.undo_stack.append({"target": "texture_overrides", "asset_id": identifier,
                                        "before": before, "after": None})
                self.redo_stack.clear()
            return
        if command.get("type") in ("set_dialogue_text", "clear_dialogue_text"):
            from importer.dialogue_authoring import validate_run_id
            identifier, run_id = command.get("entity_id"), command.get("run_id")
            self._actor(identifier)
            validate_run_id(identifier, run_id)
            before = deepcopy(self.overrides.get(identifier))
            after = deepcopy(before or {})
            runs = after.get("Dialogue", {}).get("runs", {}).copy()
            if command["type"] == "set_dialogue_text":
                runs[run_id] = command.get("text")
                self._validate_dialogue(identifier, {"runs": runs})
                context = self._dialogue_context(identifier)
                allowed = {run["semantic_id"] for run in context.options(identifier)["runs"]}
                if not set(runs) <= allowed:
                    raise ProjectError("Dialogue run is not supported by the verified actor source")
                context.patch(runs)
            else:
                runs.pop(run_id, None)
            if runs:
                after["Dialogue"] = {"runs": runs}
            else:
                after.pop("Dialogue", None)
            after = after or None
            if before != after:
                if after is None:
                    self.overrides.pop(identifier, None)
                else:
                    self.overrides[identifier] = after
                self.undo_stack.append({"entity_id": identifier, "before": before, "after": deepcopy(after)})
                self.redo_stack.clear()
            return
        if command.get("type") in ("set_actor_appearance", "clear_actor_appearance"):
            identifier = command.get("entity_id")
            self._actor(identifier)
            before = deepcopy(self.overrides.get(identifier))
            after = deepcopy(before or {})
            if command["type"] == "set_actor_appearance":
                value = {"donor_entity_id": command.get("donor_entity_id")}
                self._appearance_binding(identifier, value)
                if not any(o["donor_entity_id"] == value["donor_entity_id"] for o in self.appearance_options(identifier)["options"]):
                    raise ProjectError("Appearance donor is not a verified compatible initial pair")
                after["ActorAppearance"] = value
            else:
                after.pop("ActorAppearance", None)
            after = after or None
            if before != after:
                if after is None:
                    self.overrides.pop(identifier, None)
                else:
                    self.overrides[identifier] = after
                self.undo_stack.append({"entity_id": identifier, "before": before, "after": deepcopy(after)})
                self.redo_stack.clear()
            return
        if command.get("type") in ("create_actor_template", "apply_actor_template", "delete_actor_template"):
            self._template_command(command)
            return
        if command.get("type") not in ("set_transform", "clear_transform"):
            raise ProjectError("Unsupported authoring command")
        identifier = command.get("entity_id")
        self._actor(identifier)
        if command["type"] == "clear_transform":
            axes = command.get("axes")
            if not isinstance(axes, list) or not axes or any(axis not in ("x", "y", "z") for axis in axes):
                raise ProjectError("Clear transform requires X/Y/Z axes")
            before = deepcopy(self.overrides.get(identifier))
            after = deepcopy(before or {})
            position = after.get("Transform", {}).get("position", {})
            for axis in axes:
                position.pop(axis, None)
            if not position:
                after.pop("Transform", None)
            after = after or None
            if before != after:
                if after is None:
                    self.overrides.pop(identifier, None)
                else:
                    self.overrides[identifier] = after
                self.undo_stack.append({"entity_id": identifier, "before": before, "after": deepcopy(after)})
                self.redo_stack.clear()
            return
        position = command.get("position")
        self._validate_position(position)
        before = deepcopy(self.overrides.get(identifier))
        after = deepcopy(before or {})
        after.setdefault("Transform", {}).setdefault("position", {}).update(position)
        if before == after:
            return
        self.overrides[identifier] = after
        self.undo_stack.append({"entity_id": identifier, "before": before, "after": deepcopy(after)})
        self.redo_stack.clear()

    @staticmethod
    def _validate_position(position: dict) -> None:
        if not isinstance(position, dict) or not position or set(position) - {"x", "y", "z"}:
            raise ProjectError("Position must contain one or more X/Y/Z values")
        for value in position.values():
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or abs(value) > 32767:
                raise ProjectError("Authored coordinates must be finite numbers between -32767 and 32767")

    def _validate_template(self, identifier: str, template: dict) -> None:
        if not isinstance(identifier, str) or not identifier.startswith("template://"):
            raise ProjectError("Invalid authored template identity")
        try:
            if str(uuid.UUID(identifier[11:])) != identifier[11:]:
                raise ValueError("noncanonical UUID")
        except ValueError as exc:
            raise ProjectError("Invalid authored template identity") from exc
        if not isinstance(template, dict) or set(template) != {"id", "name", "scope", "source", "components"}:
            raise ProjectError("Invalid authored transform template")
        if template["id"] != identifier or template["scope"] != "authored-position-v1":
            raise ProjectError("Unsupported authored template scope")
        name = template["name"]
        if not isinstance(name, str) or name != name.strip() or not 1 <= len(name) <= 80:
            raise ProjectError("Template name must contain 1 to 80 characters")
        source = template["source"]
        if not isinstance(source, dict) or set(source) != {"disc_identity", "scene_id", "entity_id"} or any(not isinstance(value, str) or not value for value in source.values()):
            raise ProjectError("Template requires source disc, scene and actor provenance")
        disc = next(iter(self.imports.values()))["source"]["disc_identity"] if self.imports else None
        if source["disc_identity"] != disc:
            raise ProjectError("Template belongs to a different imported disc")
        components = template["components"]
        if not isinstance(components, dict) or set(components) != {"Transform"} or not isinstance(components["Transform"], dict) or set(components["Transform"]) != {"position"}:
            raise ProjectError("Templates support authored position only")
        self._validate_position(components["Transform"]["position"])

    def _template_command(self, command: dict) -> None:
        kind = command["type"]
        if kind == "create_actor_template":
            entity_id = command.get("entity_id")
            self._actor(entity_id)
            name = command.get("name")
            if not isinstance(name, str):
                raise ProjectError("Template name must be a string")
            if len(self.actor_templates) >= 128:
                raise ProjectError("Project supports at most 128 authored transform templates")
            if any(value["name"].casefold() == name.strip().casefold() for value in self.actor_templates.values()):
                raise ProjectError("An authored template already uses that name")
            position = self.overrides.get(entity_id, {}).get("Transform", {}).get("position", {})
            if not position:
                raise ProjectError("Author one or more position axes before creating a template")
            scene_id, document = next((key, value) for key, value in self.imports.items()
                                      if any(actor["semantic_id"] == entity_id for actor in value["actors"]))
            identifier = "template://" + str(uuid.uuid4())
            template = {"id": identifier, "name": name.strip(), "scope": "authored-position-v1",
                        "source": {"disc_identity": document["source"]["disc_identity"], "scene_id": scene_id, "entity_id": entity_id},
                        "components": {"Transform": {"position": deepcopy(position)}}}
            self._validate_template(identifier, template)
            self.actor_templates[identifier] = template
            self.undo_stack.append({"target": "actor_templates", "template_id": identifier, "entity_id": entity_id,
                                    "before": None, "after": deepcopy(template)})
            self.redo_stack.clear()
            return
        identifier = command.get("template_id")
        if not isinstance(identifier, str) or identifier not in self.actor_templates:
            raise ProjectError("Unknown authored transform template")
        template = self.actor_templates[identifier]
        self._validate_template(identifier, template)
        if kind == "apply_actor_template":
            # All currently imported actors expose the same project Transform schema.
            # This merges absolute authored axes; it never instantiates native actors.
            self.command({"type": "set_transform", "entity_id": command.get("entity_id"),
                          "position": deepcopy(template["components"]["Transform"]["position"])})
        else:
            self.actor_templates.pop(identifier)
            self.undo_stack.append({"target": "actor_templates", "template_id": identifier,
                                    "entity_id": template["source"]["entity_id"], "before": deepcopy(template), "after": None})
            self.redo_stack.clear()

    def _apply_history(self, source: list, target: list, field: str) -> None:
        if self.mode != "edit":
            raise ProjectError("Undo and redo require Edit mode")
        if not source:
            raise ProjectError("No command to " + ("undo" if field == "before" else "redo"))
        entry = source.pop()
        value = deepcopy(entry[field])
        if entry.get("target") == "texture_overrides":
            collection, identifier = self.texture_overrides, entry["asset_id"]
        else:
            collection = self.actor_templates if entry.get("target") == "actor_templates" else self.overrides
            identifier = entry["template_id"] if entry.get("target") == "actor_templates" else entry["entity_id"]
        if value is None:
            collection.pop(identifier, None)
        else:
            collection[identifier] = value
        target.append(entry)

    def undo(self) -> None:
        self._apply_history(self.undo_stack, self.redo_stack, "before")

    def redo(self) -> None:
        self._apply_history(self.redo_stack, self.undo_stack, "after")

    def save(self) -> Path:
        for binding in self.texture_overrides.values():
            self.read_texture_replacement(binding)
        if not (self.root / "Imported").resolve().is_relative_to(self.root):
            raise ProjectError("Imported evidence directory escapes project root")
        for document in self.imports.values():
            path = self.root / "Imported" / (digest(document) + ".json")
            if not path.exists():
                atomic_write(path, canonical(document))
            elif hashlib.sha256(path.read_bytes()).hexdigest() != digest(document):
                raise ProjectError("Imported evidence cache was modified; refusing to save")
        document = self._document()
        path = self.root / "project.legaia.json"
        atomic_write(path, canonical(document))
        self.saved_digest = digest(document)
        return path

    @classmethod
    def open(cls, path: Path) -> "ProjectService":
        path = path.resolve()
        if path.is_dir():
            path /= "project.legaia.json"
        raw = read_metadata_json(path)
        if raw.get("format") != cls.FORMAT:
            raise ProjectError("Unsupported Legaia project format")
        if not isinstance(raw.get("name"), str) or not raw["name"].strip() or len(raw["name"]) > 128:
            raise ProjectError("Project name must contain 1 to 128 characters")
        if not isinstance(raw.get("imports"), list) or not isinstance(raw.get("authored", {}), dict) or not isinstance(raw.get("retail_source", {}), dict):
            raise ProjectError("Invalid project collection fields")
        result = cls(path.parent, raw["name"])
        for item in raw["imports"]:
            if not isinstance(item, dict) or not all(isinstance(item.get(key), str) for key in ("sha256", "file", "scene")):
                raise ProjectError("Invalid project import reference")
            expected = f"Imported/{item['sha256']}.json"
            if item["file"] != expected or len(item["sha256"]) != 64 or any(c not in "0123456789abcdef" for c in item["sha256"]):
                raise ProjectError("Invalid project import reference")
            source = (path.parent / expected).resolve()
            if not source.is_relative_to(path.parent):
                raise ProjectError("Import reference escapes project root")
            if source.stat().st_size > 64 * 1024 * 1024:
                raise ProjectError("Imported evidence document exceeds the 64 MiB limit")
            content = source.read_bytes()
            if hashlib.sha256(content).hexdigest() != item["sha256"]:
                raise ProjectError("Imported evidence digest does not match project")
            metadata = json.loads(content)
            if not isinstance(metadata, dict) or not isinstance(metadata.get("scene"), dict):
                raise ProjectError("Invalid imported scene metadata")
            if metadata["scene"]["semantic_id"] != item["scene"]:
                raise ProjectError("Imported scene identity does not match project")
            result.import_metadata(metadata)
        result.disc_path = raw.get("retail_source", {}).get("disc_path")
        if result.disc_path is not None and not isinstance(result.disc_path, str):
            raise ProjectError("Project disc path must be a string or null")
        saved_identity = raw.get("retail_source", {}).get("disc_identity")
        actual_identity = next(iter(result.imports.values()))["source"]["disc_identity"] if result.imports else None
        if saved_identity != actual_identity:
            raise ProjectError("Project retail identity disagrees with imported evidence")
        for identifier, components in raw.get("authored", {}).items():
            if not isinstance(components, dict) or not components or set(components) - {"Transform", "ActorAppearance", "Dialogue"}:
                raise ProjectError("Unsupported authored component")
            if "Transform" in components:
                if not isinstance(components["Transform"], dict) or set(components["Transform"]) != {"position"}:
                    raise ProjectError("Unsupported authored transform")
                result.command({"type": "set_transform", "entity_id": identifier,
                                "position": components["Transform"]["position"]})
            if "ActorAppearance" in components:
                # Opening metadata remains possible offline; preview/build reverify wire resources.
                result._appearance_binding(identifier, components["ActorAppearance"])
                result.overrides.setdefault(identifier, {})["ActorAppearance"] = deepcopy(components["ActorAppearance"])
            if "Dialogue" in components:
                # Offline opening checks syntax; actual source capacities are verified on edit/build.
                result._validate_dialogue(identifier, components["Dialogue"])
                result.overrides.setdefault(identifier, {})["Dialogue"] = deepcopy(components["Dialogue"])
        templates = raw.get("actor_templates", {})
        if not isinstance(templates, dict) or len(templates) > 128:
            raise ProjectError("Invalid authored template collection")
        names = set()
        for identifier, template in templates.items():
            result._validate_template(identifier, template)
            if template["name"].casefold() in names:
                raise ProjectError("Duplicate authored template name")
            names.add(template["name"].casefold())
        result.actor_templates = deepcopy(templates)
        textures = raw.get("texture_overrides", {})
        if not isinstance(textures, dict) or len(textures) > 128:
            raise ProjectError("Invalid texture replacement collection")
        for identifier, binding in textures.items():
            result._validate_texture_binding(binding)
            scene = result.imports[binding["source_scene_id"]]["scene"]["name"]
            if not isinstance(identifier, str) or len(identifier) > 512 or not identifier.startswith(f"texture://{scene}/"):
                raise ProjectError("Texture reference does not belong to its imported scene")
            result.read_texture_replacement(binding)
        result.texture_overrides = deepcopy(textures)
        if raw.get("active_scene") is not None:
            result.set_scene(raw["active_scene"])
        result.undo_stack.clear()
        result.redo_stack.clear()
        result.saved_digest = digest(result._document())
        return result

    def authored_assets(self) -> list[dict]:
        """Project-wide authored references, independent of derived resource caches."""
        records = []
        for scene_id, document in sorted(self.imports.items()):
            for actor in document["actors"]:
                identifier = actor["semantic_id"]
                edits = self.overrides.get(identifier, {})
                if not edits:
                    continue
                changes = []
                position = edits.get("Transform", {}).get("position", {})
                if position:
                    changes.append("Position: " + ", ".join(axis.upper() for axis in sorted(position)))
                if edits.get("ActorAppearance"):
                    changes.append("Initial appearance")
                runs = edits.get("Dialogue", {}).get("runs", {})
                if runs:
                    changes.append(f"Dialogue: {len(runs)} text runs")
                records.append({"id": identifier, "kind": "actor", "name": "Actor " + identifier.rsplit("/", 1)[-1],
                                "scene_id": scene_id, "source_scene": document["scene"]["name"],
                                "changes": changes, "authored": deepcopy(edits),
                                "source_record": deepcopy(actor.get("source_record"))})
        for identifier, binding in sorted(self.texture_overrides.items()):
            scene_id = binding["source_scene_id"]
            records.append({"id": identifier, "kind": "texture", "name": "TIM " + identifier.split("/", 3)[-1].replace("/", " / "),
                            "scene_id": scene_id, "source_scene": self.imports[scene_id]["scene"]["name"],
                            "changes": ["TIM replacement"], "authored": deepcopy(binding)})
        for identifier, template in sorted(self.actor_templates.items()):
            scene_id = template["source"]["scene_id"]
            records.append({"id": identifier, "kind": "template", "name": template["name"],
                            "scene_id": scene_id, "source_scene": self.imports.get(scene_id, {}).get("scene", {}).get("name", scene_id),
                            "changes": ["Position template"], "authored": deepcopy(template)})
        return records

    def state(self) -> dict:
        document = self.imports.get(self.active_scene)
        correlation = self._current_correlation()
        entities = []
        for actor in document["actors"] if document else []:
            identifier = actor["semantic_id"]
            imported = deepcopy(actor["imported_transform"])
            authored = deepcopy(self.overrides.get(identifier, {}).get("Transform", {}))
            effective = deepcopy(imported)
            effective["position"].update(authored.get("position", {}))
            model = actor["model_reference"]
            appearance = deepcopy(self.overrides.get(identifier, {}).get("ActorAppearance", {}))
            donor = self.appearance_source_actor(identifier)
            original_pair = {"asset_id": model.get("asset_semantic_id"), "animation_id": actor["placement_fields"].get("animation_id")}
            effective_pair = {"asset_id": donor["model_reference"].get("asset_semantic_id"),
                              "animation_id": donor["placement_fields"].get("animation_id")}
            if appearance:
                effective_pair["donor_entity_id"] = donor["semantic_id"]
            entities.append({"id": identifier, "name": "Actor " + identifier.rsplit("/", 1)[-1],
                             "components": {"Transform": {"imported": imported, "authored": authored, "effective": effective},
                                            "ActorAppearance": {"imported": original_pair, "authored": appearance, "effective": effective_pair,
                                                                "limitations": ["Initial model/animation pair only; scripts may replace it. Script and gameplay compatibility remain unverified."]},
                                            "ModelRenderer": {"asset_id": model.get("asset_semantic_id"), "resolution_status": model.get("resolution_status")},
                                            "Animation": {"imported_id": actor["placement_fields"].get("animation_id"), "resolution_status": "unresolved"},
                                            "Dialogue": {"authored": deepcopy(self.overrides.get(identifier, {}).get("Dialogue", {})),
                                                         "limitations": ["Only verified plain-text runs are writable; controls and record boundaries remain fixed. Source capacity is rechecked on edit/build."]},
                                            "RuntimeCorrelation": deepcopy(correlation.get("entities", {}).get(identifier, {"status": "unavailable", "binding_confirmed": False, "candidates": [], "reason": correlation.get("reason")})),
                                            "RetailMetadata": {key: deepcopy(actor.get(key)) for key in ("source_record", "claims", "unresolved")}}})
        return {"project": {"name": self.name, "path": str(self.root), "dirty": self.dirty, "mode": self.mode},
                "scene": {"id": self.active_scene, "name": document["scene"]["name"] if document else None, "entities": entities},
                "scenes": [{"id": key, "name": value["scene"]["name"]} for key, value in self.imports.items()],
                "runtime_correlation": correlation,
                "actor_templates": deepcopy(list(self.actor_templates.values())),
                "assets": deepcopy(list(self.assets.records.values())), "selection": {"entity_id": self.selected},
                "texture_overrides": deepcopy(self.texture_overrides),
                "authored_assets": self.authored_assets(),
                "history": {"can_undo": bool(self.undo_stack), "can_redo": bool(self.redo_stack)},
                "diagnostics": ["Scene viewport uses verified model poses where supported and explicit markers otherwise; scripted visibility is not reconstructed.",
                                "Retail Y and initial facing are unresolved; an authored Y is a project value.",
                                "Build supports representable X/Z placements; authored height and facing cannot yet be serialized."],
                "capabilities": {"edit_transform": True, "authored_transform_templates": True,
                                 "live_mode": False, "build": False, "model_preview": False}}
