"""Metadata-backed project model. Imported evidence never doubles as editable state."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
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
        self.active_scene: str | None = None
        self.selected: str | None = None
        self.undo_stack: list[dict] = []
        self.redo_stack: list[dict] = []
        self.saved_digest: str | None = None
        self.disc_path: str | None = None
        self.mode = "edit"

    def _document(self) -> dict:
        return {"format": self.FORMAT, "name": self.name,
                "retail_source": {"disc_path": self.disc_path,
                                  "disc_identity": next(iter(self.imports.values()))["source"]["disc_identity"] if self.imports else None},
                "imports": [{"scene": key, "file": f"Imported/{digest(value)}.json", "sha256": digest(value)}
                            for key, value in sorted(self.imports.items())],
                "active_scene": self.active_scene, "authored": deepcopy(self.overrides)}

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

    def set_scene(self, identifier: str) -> None:
        if identifier not in self.imports:
            raise ProjectError("Scene has not been imported")
        self.active_scene = identifier
        self.selected = None

    def command(self, command: dict) -> None:
        if self.mode != "edit":
            raise ProjectError("Authoring commands require Edit mode")
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
        if not isinstance(position, dict) or not position or set(position) - {"x", "y", "z"}:
            raise ProjectError("Position must contain one or more X/Y/Z values")
        for value in position.values():
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or abs(value) > 32767:
                raise ProjectError("Authored coordinates must be finite numbers between -32767 and 32767")
        before = deepcopy(self.overrides.get(identifier))
        after = deepcopy(before or {})
        after.setdefault("Transform", {}).setdefault("position", {}).update(position)
        if before == after:
            return
        self.overrides[identifier] = after
        self.undo_stack.append({"entity_id": identifier, "before": before, "after": deepcopy(after)})
        self.redo_stack.clear()

    def _apply_history(self, source: list, target: list, field: str) -> None:
        if self.mode != "edit":
            raise ProjectError("Undo and redo require Edit mode")
        if not source:
            raise ProjectError("No command to " + ("undo" if field == "before" else "redo"))
        entry = source.pop()
        value = deepcopy(entry[field])
        if value is None:
            self.overrides.pop(entry["entity_id"], None)
        else:
            self.overrides[entry["entity_id"]] = value
        target.append(entry)

    def undo(self) -> None:
        self._apply_history(self.undo_stack, self.redo_stack, "before")

    def redo(self) -> None:
        self._apply_history(self.redo_stack, self.undo_stack, "after")

    def save(self) -> Path:
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
            if not isinstance(components, dict) or set(components) != {"Transform"} or not isinstance(components["Transform"], dict) or set(components["Transform"]) != {"position"}:
                raise ProjectError("Unsupported authored component")
            result.command({"type": "set_transform", "entity_id": identifier,
                            "position": components["Transform"]["position"]})
        if raw.get("active_scene") is not None:
            result.set_scene(raw["active_scene"])
        result.undo_stack.clear()
        result.redo_stack.clear()
        result.saved_digest = digest(result._document())
        return result

    def state(self) -> dict:
        document = self.imports.get(self.active_scene)
        entities = []
        for actor in document["actors"] if document else []:
            identifier = actor["semantic_id"]
            imported = deepcopy(actor["imported_transform"])
            authored = deepcopy(self.overrides.get(identifier, {}).get("Transform", {}))
            effective = deepcopy(imported)
            effective["position"].update(authored.get("position", {}))
            model = actor["model_reference"]
            entities.append({"id": identifier, "name": "Actor " + identifier.rsplit("/", 1)[-1],
                             "components": {"Transform": {"imported": imported, "authored": authored, "effective": effective},
                                            "ModelRenderer": {"asset_id": model.get("asset_semantic_id"), "resolution_status": model.get("resolution_status")},
                                            "Animation": {"imported_id": actor["placement_fields"].get("animation_id"), "resolution_status": "unresolved"},
                                            "RetailMetadata": {key: deepcopy(actor.get(key)) for key in ("source_record", "claims", "unresolved")}}})
        return {"project": {"name": self.name, "path": str(self.root), "dirty": self.dirty, "mode": self.mode},
                "scene": {"id": self.active_scene, "name": document["scene"]["name"] if document else None, "entities": entities},
                "scenes": [{"id": key, "name": value["scene"]["name"]} for key, value in self.imports.items()],
                "assets": deepcopy(list(self.assets.records.values())), "selection": {"entity_id": self.selected},
                "history": {"can_undo": bool(self.undo_stack), "can_redo": bool(self.redo_stack)},
                "diagnostics": ["Scene viewport uses placement markers; decoded model objects can be inspected separately.",
                                "Retail Y and initial facing are unresolved; an authored Y is a project value.",
                                "Build supports representable X/Z placements; authored height and facing cannot yet be serialized."],
                "capabilities": {"edit_transform": True, "live_mode": False, "build": False, "model_preview": False}}
