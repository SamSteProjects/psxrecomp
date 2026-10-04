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
        self.material_reference_catalogs: dict[str, dict] = {}

    def register_resources(self, scene_id: str, source_key: str, records: list[dict], limitations: list[str], *, flag_state_key: str | None = None, transition_state_key: str | None = None, region_state_key: str | None = None, trigger_state_key: str | None = None) -> dict:
        """Replace a verified derived catalog without mutating imported project facts."""
        indexed = {}
        for item in records:
            identifier = item.get("semantic_id")
            kind = item.get("asset_kind")
            if not isinstance(identifier, str) or kind not in ("texture", "animation", "script", "dialogue", "collision", "trigger", "region", "worldmap", "flag", "transition") or identifier in indexed:
                raise ProjectError("Resource catalog has an invalid or duplicate identity")
            record = deepcopy(item)
            record.update(id=identifier, kind=kind, layer="derived", scene_id=scene_id)
            indexed[identifier] = record
        result = {"scene_id": scene_id, "source_key": source_key,
                  "records": [indexed[key] for key in sorted(indexed)], "limitations": list(limitations)}
        if flag_state_key is not None:
            result['flag_state_key'] = flag_state_key
        if transition_state_key is not None:
            result['transition_state_key'] = transition_state_key
        if region_state_key is not None:
            result['region_state_key'] = region_state_key
        if trigger_state_key is not None:
            result['trigger_state_key'] = trigger_state_key
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
    REVIEW_COMPONENTS = frozenset({"Transform", "ActorAppearance", "ActorAnimation", "ActorAllocatedAnimation", "Dialogue", "Transitions",
                                  "ScriptMovement", "ScriptFlags", "ScriptWaits", "ScriptModelSelectors", "ScriptFacing", "ScriptBranches",
                                  "Environment", "AnimationChannels", "AnimationRecords", "Collision", "RegionBounds", "TriggerCells"})

    def __init__(self, root: Path, name: str = "Legaia project") -> None:
        self.root = root.resolve()
        self.name = name
        self.imports: dict[str, dict] = {}
        self.assets = AssetDatabase()
        self.overrides: dict[str, dict] = {}
        self.actor_templates: dict[str, dict] = {}
        self.actor_selection_sets: dict[str, dict] = {}
        self.scene_selection_sets: dict[str, dict] = {}
        self.scene_views: dict[str, dict] = {}
        self.actor_drafts: dict[str, dict] = {}
        self.texture_overrides: dict[str, dict] = {}
        self.model_overrides: dict[str, dict] = {}
        self.active_scene: str | None = None
        self.selected: str | None = None
        self.undo_stack: list[dict] = []
        self.redo_stack: list[dict] = []
        self.saved_digest: str | None = None
        self.saved_sections: dict[str, str] = {}
        self.disc_path: str | None = None
        self.mode = "edit"
        self._live_correlation: dict | None = None

    def _appearance_donors(self) -> dict:
        document = self.imports.get(self.active_scene)
        return {actor["semantic_id"]: self.overrides[actor["semantic_id"]]["ActorAppearance"]["donor_entity_id"]
                for actor in document["actors"] if self.overrides.get(actor["semantic_id"], {}).get("ActorAppearance")} if document else {}

    def _animation_donors(self) -> dict:
        document = self.imports.get(self.active_scene)
        if not document:
            return {}
        from .actor_animation import validate
        return {actor['semantic_id']: validate(self, actor['semantic_id'],
                    self.overrides[actor['semantic_id']]['ActorAnimation'])['semantic_id']
                for actor in document['actors']
                if self.overrides.get(actor['semantic_id'], {}).get('ActorAnimation')}

    def _allocated_animation_assignments(self) -> dict:
        return {a['semantic_id']:deepcopy(self.overrides[a['semantic_id']]['ActorAllocatedAnimation'])
                for a in self.imports.get(self.active_scene,{}).get('actors',[])
                if 'ActorAllocatedAnimation' in self.overrides.get(a['semantic_id'],{})}

    def correlate_runtime(self, live_status: dict) -> dict:
        from integrations.legaia.observer.correlation import correlate
        # Always replace prior observations, including on disconnect/rejection.
        # Nothing from this layer participates in save, dirty state or commands.
        self._live_correlation = None
        result = correlate(self.imports.get(self.active_scene), live_status, self._appearance_donors(), self._animation_donors(),
            allocated_assignments=self._allocated_animation_assignments())
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
            if current.get("appearance_donors", {}) != self._appearance_donors():
                self._live_correlation = None
                return unavailable("Authored appearance changed since observation; capture again")
            if current.get('animation_donors', {}) != self._animation_donors():
                self._live_correlation = None
                return unavailable('Authored initial animation changed since observation; capture again')
            allocated=self._allocated_animation_assignments()
            if current.get('allocated_assignment_digest') != (_digest(allocated) if allocated else None):
                self._live_correlation = None
                return unavailable('Authored allocated initial animation changed since observation; capture again')
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
                **({"scene_views": deepcopy(self.scene_views)} if self.scene_views else {}),
                **({"actor_selection_sets": deepcopy(self.actor_selection_sets)} if self.actor_selection_sets else {}),
                **({"scene_selection_sets": deepcopy(self.scene_selection_sets)} if self.scene_selection_sets else {}),
                **({"actor_drafts": deepcopy(self.actor_drafts)} if self.actor_drafts else {}),
                **({"texture_overrides": deepcopy(self.texture_overrides)} if self.texture_overrides else {}),
                **({"model_overrides": deepcopy(self.model_overrides)} if self.model_overrides else {})}

    @property
    def dirty(self) -> bool:
        return digest(self._document()) != self.saved_digest

    @staticmethod
    def _placement_issues(authored: dict) -> list[str]:
        from importer.serialization import encode_placement_coordinate
        from importer.core import ImportError as PlacementError
        issues = []
        for axis, value in authored.get("position", {}).items():
            if axis == "y":
                issues.append("Y is project-only; clear authored height before Build")
            else:
                try:
                    encode_placement_coordinate(value, axis.upper())
                except PlacementError as exc:
                    issues.append(str(exc))
        return issues

    def placement_build_issues(self) -> list[dict]:
        result = []
        for scene_id, document in sorted(self.imports.items()):
            for actor in document["actors"]:
                identifier = actor["semantic_id"]
                issues = self._placement_issues(self.overrides.get(identifier, {}).get("Transform", {}))
                if issues:
                    result.append({"scene_id": scene_id, "scene_name": document["scene"]["name"],
                                   "entity_id": identifier, "issues": issues})
        return result

    @property
    def unsaved_sections(self) -> list[str]:
        document = self._document()
        labels = {"name": "Project name", "retail_source": "Retail source",
                  "imports": "Imported scenes", "active_scene": "Active scene",
                  "authored": "Scene and game-data edits", "actor_templates": "Actor presets",
                  "texture_overrides": "Texture replacements", "model_overrides": "Model content",
                  "actor_drafts": "New NPC drafts", "actor_selection_sets": "Saved actor selections", "scene_selection_sets": "Saved scene selections", "scene_views": "Saved scene views"}
        return [label for key, label in labels.items()
                if digest(document.get(key)) != self.saved_sections.get(key)]

    def _mark_saved(self) -> None:
        document = self._document()
        self.saved_digest = digest(document)
        self.saved_sections = {key: digest(document.get(key)) for key in
                               ("name", "retail_source", "imports", "active_scene",
                                "authored", "actor_templates", "texture_overrides", "model_overrides", "actor_drafts", "actor_selection_sets", "scene_selection_sets", "scene_views")}

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
            if any(template['source']['scene_id']==scene_id for template in self.actor_templates.values()):
                raise ProjectError('Imported evidence changed under actor presets; resolve the preset library before reimport')
            draft_history = [entry.get(field) for entry in self.undo_stack+self.redo_stack
                             if entry.get('target')=='actor_drafts' for field in ('before','after')]
            if any(draft and draft.get('scene_id')==scene_id
                   for draft in list(self.actor_drafts.values())+draft_history):
                raise ProjectError('Imported evidence changed under NPC drafts or their history; resolve drafts before reimport')
            if any(value['scene_id'] == scene_id for value in self.actor_selection_sets.values()):
                raise ProjectError('Imported evidence changed under saved actor selections; resolve selections before reimport')
            if any(value['scene_id']==scene_id for value in self.scene_selection_sets.values()) or any(entry.get('target')=='scene_selection_sets' and entry.get('scene_id')==scene_id for entry in self.undo_stack+self.redo_stack):
                raise ProjectError('Imported evidence changed under saved scene selections or their history; resolve selections before reimport')
            if any(value['scene_id'] == scene_id for value in self.scene_views.values()) or any(entry.get('target') == 'scene_views' and entry.get('scene_id') == scene_id for entry in self.undo_stack + self.redo_stack):
                raise ProjectError('Imported evidence changed under saved scene views or their history; resolve views before reimport')
            affected = set(ids) | {actor["semantic_id"] for actor in previous["actors"]}
            if any(key in affected for key in self.overrides) or any(
                    entry.get('entity_id') in affected or affected.intersection(entry.get('entity_ids', [])) or affected.intersection(entry.get('source_entity_ids', []))
                    for entry in self.undo_stack + self.redo_stack):
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

    def _validate_animation_override(self, identifier: str, value: dict) -> None:
        from importer.scene_animation import load_scene_actor_animation_catalog
        if not isinstance(value, dict) or set(value) != {"animation_id", "source_record_sha256", "edits"}:
            raise ProjectError("Animation override requires source identity, digest and channel edits")
        options = self.animation_authoring_options(identifier)
        binding = options["binding"]
        if value["animation_id"] != binding["semantic_id"]:
            raise ProjectError("Animation override differs from the imported actor binding")
        document = next(doc for doc in self.imports.values()
                        if any(a["semantic_id"] == identifier for a in doc["actors"]))
        actor = self._actor(identifier)
        asset = next(a for a in document["assets"]["models"]
                     if a["semantic_id"] == binding["asset_semantic_id"])
        catalog = load_scene_actor_animation_catalog(self.disc_path, document["scene"]["name"])
        catalog.authored_animation_record(actor, asset, value["edits"], value["source_record_sha256"])
        proposed = {a["semantic_id"]: self.overrides[a["semantic_id"]]["AnimationChannels"]
                    for a in document["actors"] if "AnimationChannels" in self.overrides.get(a["semantic_id"], {})}
        proposed[identifier] = value
        catalog.authored_bank(proposed)

    def animation_record_source(self, identifier: str, layer: str = "retail", format: str = "record") -> tuple[bytes, dict]:
        """Return a freshly verified private source record and its binding."""
        from importer.pipeline import _disc_context
        from importer.scene_animation import load_scene_actor_animation_catalog
        if format not in ('record', 'json'):
            raise ProjectError('Choose record or json animation format')
        if layer not in ('retail', 'effective'):
            raise ProjectError('Choose retail or effective animation record')
        if not self.disc_path:
            raise ProjectError('Animation source requires the project user-owned disc')
        with _disc_context(self.disc_path):
            options = self.animation_authoring_options(identifier)
            binding = options['binding']
            document = next(doc for doc in self.imports.values()
                            if any(a['semantic_id'] == identifier for a in doc['actors']))
            catalog = load_scene_actor_animation_catalog(self.disc_path, document['scene']['name'])
            asset = next(a for a in document['assets']['models'] if a['semantic_id'] == binding['asset_semantic_id'])
            source, _ = catalog.authored_animation_record(self._actor(identifier), asset, [], binding['source_record']['record_sha256'])
            if layer == 'effective':
                overrides = {a['semantic_id']: self.overrides[a['semantic_id']]['AnimationChannels']
                             for a in document['actors'] if 'AnimationChannels' in self.overrides.get(a['semantic_id'], {})}
                bank, _ = catalog.authored_bank(overrides)
                start = binding['source_record']['byte_offset']
                source = bank[start:start + len(source)]
            if format == 'json':
                import json
                from importer.animation_authoring import export_animation_channels
                document = json.loads(export_animation_channels(source))
                document['source_record_sha256'] = binding['source_record']['record_sha256']
                source = (json.dumps(document, sort_keys=True, indent=2) + '\n').encode('utf-8')
            return source, deepcopy(binding)

    def _prepare_animation_record(self, identifier: str, content: bytes, format: str = "record") -> tuple[dict, dict]:
        """Resolve a file to a source-bound command without mutating project state."""
        from importer.animation_authoring import replace_animation_record, import_animation_channels
        if format not in ('record', 'json'):
            raise ProjectError('Choose record or json animation format')
        if self.mode != 'edit':
            raise ProjectError('Animation record import requires Edit mode')
        if not isinstance(content, bytes) or not 1 <= len(content) <= 4 * 1024 * 1024:
            raise ProjectError('Animation record import requires at most 4 MiB of bytes')
        source, binding = self.animation_record_source(identifier)
        _, audit = (import_animation_channels(source, content) if format == 'json' else
                    replace_animation_record(source, binding['source_record']['record_sha256'], content))
        edits = {}
        for row in audit:
            key = (row['frame_index'], row['object_index'])
            edit = edits.setdefault(key, {'frame_index': key[0], 'object_index': key[1]})
            field, axis = row['field'].split('.')
            edit.setdefault(field, {})[axis] = row['after_value']
        value = {'animation_id': binding['semantic_id'],
                 'source_record_sha256': binding['source_record']['record_sha256'],
                 'edits': list(edits.values())}
        command = ({'type': 'set_animation_channels', 'entity_id': identifier, 'value': value} if edits else
                   {'type': 'clear_animation_channels', 'entity_id': identifier})
        report = {'animation_id': binding['semantic_id'], 'changed_axes': len(audit),
                  'changed_channels': len(edits), 'scope': 'actor_channel_contribution',
                  'shared_clip_users': 'Other contributors remain unchanged; conflicts reject the import.'}
        return command, {**report, 'changes': audit, 'source_record_sha256': value['source_record_sha256'],
                         'proposed_value': value}

    def preview_animation_record(self, identifier: str, content: bytes, format: str = "record") -> dict:
        """Check source and composed shared channels; leave history and overrides unchanged."""
        command, report = self._prepare_animation_record(identifier, content, format)
        self._validate_animation_override(identifier, report.pop('proposed_value'))
        report['action'] = 'replace_contribution' if report['changed_axes'] else 'clear_contribution'
        report['comparison'] = 'retail_source'
        return report

    def animation_file_pose_preview(self, identifier: str, content: bytes, format: str = "record") -> tuple[dict, dict]:
        """Pose a proposed shared clip using private input without applying a command."""
        from importer.scene_animation import load_scene_actor_animation_catalog
        _, report = self._prepare_animation_record(identifier, content, format)
        value = report.pop('proposed_value')
        document = self.imports.get(self.active_scene)
        actor = next((item for item in (document or {}).get('actors', [])
                      if item['semantic_id'] == identifier), None)
        if actor is None:
            raise ProjectError('Animation file pose requires an actor in the active scene')
        asset = next(a for a in document['assets']['models']
                     if a['semantic_id'] == actor['model_reference']['asset_semantic_id'])
        overrides = {a['semantic_id']: deepcopy(self.overrides[a['semantic_id']]['AnimationChannels'])
                     for a in document['actors'] if a['semantic_id'] != identifier and
                     'AnimationChannels' in self.overrides.get(a['semantic_id'], {})}
        if value['edits']:
            overrides[identifier] = value
        catalog = load_scene_actor_animation_catalog(self.disc_path, document['scene']['name'])
        preview = catalog.authored_bank_preview(actor, asset, overrides)
        preview['representation'] = 'file_preview'
        preview['proposal'] = {**report, 'project_changed': False, 'comparison': 'retail_source'}
        return preview, deepcopy(asset)

    def import_animation_record(self, identifier: str, content: bytes, format: str = "record") -> dict:
        """Replace this actor's clip contribution using validated source channels."""
        command, report = self._prepare_animation_record(identifier, content, format)
        self.command(command)
        return {key: value for key, value in report.items()
                if key not in ('changes', 'source_record_sha256', 'proposed_value')}

    def animation_channel_values(self, identifier: str, frame_index: int, object_index: int) -> dict:
        from importer.scene_animation import load_scene_actor_animation_catalog
        options = self.animation_authoring_options(identifier)
        document = next(doc for doc in self.imports.values()
                        if any(a["semantic_id"] == identifier for a in doc["actors"]))
        catalog = load_scene_actor_animation_catalog(self.disc_path, document["scene"]["name"])
        asset = next(a for a in document["assets"]["models"] if a["semantic_id"] == options["binding"]["asset_semantic_id"])
        overrides = {a["semantic_id"]: self.overrides[a["semantic_id"]]["AnimationChannels"]
                     for a in document["actors"] if "AnimationChannels" in self.overrides.get(a["semantic_id"], {})}
        return catalog.channel_values(self._actor(identifier), asset, frame_index, object_index, overrides)

    def animation_authoring_options(self, identifier: str) -> dict:
        """Resolve editable imported rigid channels against current retail evidence."""
        from importer.pipeline import _disc_context, import_scene
        from importer.scene_animation import load_scene_actor_animation_catalog
        if not self.disc_path:
            raise ProjectError("Animation authoring requires the project's user-owned disc")
        actor = self._actor(identifier)
        document = next(doc for doc in self.imports.values()
                        if any(a["semantic_id"] == identifier for a in doc["actors"]))
        with _disc_context(self.disc_path):
            if digest(import_scene(self.disc_path, document["scene"]["name"])) != digest(document):
                raise ProjectError("Animation source differs from freshly verified imported evidence")
            catalog = load_scene_actor_animation_catalog(self.disc_path, document["scene"]["name"])
            bindings = catalog.referenced_animation_metadata()["bindings"]
            binding = next((item for item in bindings
                            if item.get("actor_semantic_id") == identifier), None)
            if binding is None:
                raise ProjectError("Actor has no supported imported rigid animation binding")
            return {"entity_id": identifier, "binding": deepcopy(binding),
                    "shared_actor_ids": [a["semantic_id"] for a in document["actors"]
                                         if a["placement_fields"].get("animation_id") == actor["placement_fields"].get("animation_id")
                                         and type(a["model_reference"].get("model_index")) is int
                                         and 0 <= a["model_reference"]["model_index"] < 0xF0],
                    "authored": deepcopy(self.overrides.get(identifier, {}).get("AnimationChannels")),
                    "scope": "existing_imported_rigid_channels",
                    "translation": {"minimum": -2048, "maximum": 2047, "step": 1},
                    "rotation_psx": {"minimum": 0, "maximum": 4080, "step": 16}}

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

    def _validate_dialogue(self, identifier: str, value: dict, *, allow_legacy_newline=False) -> None:
        from importer.dialogue_authoring import MAX_EDIT_RUNS, validate_dialogue_text, validate_run_id
        self._dialogue_document(identifier)
        if (not isinstance(value, dict) or set(value) != {"runs"} or
                not isinstance(value["runs"], dict) or not 1 <= len(value["runs"]) <= MAX_EDIT_RUNS):
            raise ProjectError("Dialogue requires a bounded nonempty text-run collection")
        for run_id, text in value["runs"].items():
            validate_run_id(identifier, run_id)
            validate_dialogue_text(text, allow_renderer_newline=allow_legacy_newline)

    def _dialogue_document(self, identifier: str) -> dict:
        """Resolve the imported scene; actual P2 membership is verified on edit/build."""
        if isinstance(identifier, str) and "/scripts/man-p2/" in identifier:
            from importer.dialogue_authoring import validate_run_id
            validate_run_id(identifier, "script://" + identifier.removeprefix("scene://") + "/dialogue/0000/run/0000")
            scene_id = identifier.split("/scripts/man-p2/", 1)[0]
            if scene_id not in self.imports:
                raise ProjectError("Dialogue script scene has not been imported")
            return self.imports[scene_id]
        self._actor(identifier)
        return next(doc for doc in self.imports.values() if any(a["semantic_id"] == identifier for a in doc["actors"]))

    def _dialogue_context(self, identifier: str):
        from importer.dialogue_authoring import load_dialogue_authoring_context
        from importer.pipeline import _disc_context, import_scene
        document = self._dialogue_document(identifier)
        if not self.disc_path:
            raise ProjectError("Dialogue authoring requires the project's user-owned disc")
        with _disc_context(self.disc_path):
            if import_scene(self.disc_path, document["scene"]["name"]) != document:
                raise ProjectError("Dialogue source differs from freshly verified imported evidence")
            return load_dialogue_authoring_context(self.disc_path, document["scene"]["name"])

    def _validate_collision(self, identifier: str, value: dict) -> None:
        from importer.collision_authoring import patch_collision_walls
        if not isinstance(identifier, str) or identifier not in self.imports:
            raise ProjectError("Collision owner must be an imported scene")
        if not isinstance(value, dict) or set(value) != {"source_sha256", "edits"}:
            raise ProjectError("Collision override requires source SHA256 and wall edits")
        patch_collision_walls(self._environment_source(identifier), value["source_sha256"], value["edits"])

    def _validate_region_bounds(self, identifier: str, value: dict) -> dict | None:
        from importer.region_authoring import patch_field_regions, region_authoring_options
        if not isinstance(identifier, str) or identifier not in self.imports:
            raise ProjectError('Region bounds owner must be an imported scene')
        if not isinstance(value, dict) or set(value) != {'source_sha256', 'edits'}:
            raise ProjectError('Region bounds require a source SHA256 and corner edits only')
        original = self._environment_source(identifier)
        scene = self.imports[identifier]['scene']['name']
        patch_field_regions(original, value['source_sha256'], scene, value['edits'])
        records = {row['region_id']: row for row in region_authoring_options(original, scene)['records']}
        edits = [deepcopy(row) for row in value['edits']
                 if any(row[key] != records[row['region_id']]['encoded'][key] for key in ('x0', 'z0', 'x1', 'z1'))]
        return {'source_sha256': value['source_sha256'], 'edits': sorted(edits, key=lambda row: row['region_id'])} if edits else None

    def _validate_trigger_cells(self, identifier: str, value: dict) -> dict | None:
        from importer.trigger_authoring import patch_field_triggers, trigger_authoring_options
        if not isinstance(identifier, str) or identifier not in self.imports:
            raise ProjectError('Trigger cells owner must be an imported scene')
        if not isinstance(value, dict) or set(value) != {'source_sha256', 'edits'}:
            raise ProjectError('Trigger cells require a source SHA256 and cell edits only')
        original = self._environment_source(identifier)
        scene = self.imports[identifier]['scene']['name']
        patch_field_triggers(original, value['source_sha256'], scene, value['edits'])
        records = {row['trigger_id']: row for row in trigger_authoring_options(original, scene)['records']}
        edits = [deepcopy(row) for row in value['edits']
                 if any(row[key] != records[row['trigger_id']]['encoded'][key] for key in ('tile_x', 'tile_z'))]
        return {'source_sha256': value['source_sha256'], 'edits': sorted(edits, key=lambda row: row['trigger_id'])} if edits else None

    def _validate_environment(self, identifier: str, value: dict) -> None:
        import re
        import struct
        from importer.environment_authoring import patch_environment_transforms, patch_environment_instances
        if identifier not in self.imports or not isinstance(value, dict) or 'source_sha256' not in value or set(value) - {"source_sha256", "edits", "instances"}:
            raise ProjectError("Environment edits require an imported scene and source binding")
        if not isinstance(value["source_sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", value["source_sha256"]):
            raise ProjectError("Environment source binding requires a SHA256 digest")
        if not isinstance(value.get("edits", []), list) or not isinstance(value.get("instances", []), list) or not (value.get("edits") or value.get("instances")):
            raise ProjectError("Environment edits must be nonempty")
        # Offline schema validation uses a complete synthetic grid containing
        # every descriptor. Real source ownership is checked on edit/build.
        fixture = bytearray(0x12000)
        for record in range(512):
            struct.pack_into('<H', fixture, 0x8000 + record * 2, record)
        fixture = bytes(fixture)
        patch_environment_transforms(fixture, hashlib.sha256(fixture).hexdigest(), value.get("edits", []))
        instances = value.get("instances", [])
        if len(instances) > 512:
            raise ProjectError("Too many environment instance edits")
        seen = set()
        for edit in instances:
            cell = edit.get('cell_index') if isinstance(edit, dict) else None
            if type(cell) is not int or not 0 <= cell < 16384 or cell in seen:
                raise ProjectError("Invalid or duplicate environment instance cell")
            seen.add(cell)
            fixture = bytearray(0x12000)
            struct.pack_into('<H', fixture, 0x8000 + cell*2, 0x2004)
            fixture = bytes(fixture)
            patch_environment_instances(fixture, hashlib.sha256(fixture).hexdigest(), [edit])

    def _environment_source(self, identifier: str) -> bytes:
        from importer.pipeline import _disc_context, import_scene
        from importer.environment import load_environment_placements
        if not self.disc_path or identifier not in self.imports:
            raise ProjectError("Environment authoring requires an imported scene and retail source")
        document = self.imports[identifier]
        with _disc_context(self.disc_path) as (_, _, _, archive):
            if import_scene(self.disc_path, document["scene"]["name"]) != document:
                raise ProjectError("Environment source differs from imported evidence")
            source = load_environment_placements(self.disc_path, document["scene"]["name"])["source_record"]
            data = archive.read_entry(archive.entry(source["map_entry_index"]), extended=True)
            if hashlib.sha256(data).hexdigest() != source["map_sha256"]:
                raise ProjectError("Environment MAP changed during source verification")
            return data

    def _validate_movements(self, identifier: str, value: dict) -> None:
        import re
        from importer.core import ImportError
        from importer.movement_authoring import validate_movement_values
        self._dialogue_document(identifier)
        if (not isinstance(value, dict) or set(value) != {"entries"} or
                not isinstance(value["entries"], dict) or not 1 <= len(value["entries"]) <= 1024):
            raise ProjectError("ScriptMovement requires a bounded nonempty entry collection")
        prefix = "script://" + identifier.removeprefix("scene://") + "/movement/"
        for key, fields in value["entries"].items():
            if not isinstance(key, str) or re.fullmatch(re.escape(prefix) + r"[0-9a-f]{4}", key) is None:
                raise ProjectError("Movement must belong to its source owner")
            try:
                validate_movement_values(fields)
            except ImportError as error:
                raise ProjectError(str(error)) from error

    def _movement_context(self, identifier: str):
        from importer.movement_authoring import MovementAuthoringContext
        return MovementAuthoringContext(self._dialogue_context(identifier))

    def movement_options(self, identifier: str) -> dict:
        from importer.movement_authoring import validate_movement_values
        result = self._movement_context(identifier).options(identifier)
        authored = self.overrides.get(identifier, {}).get("ScriptMovement", {}).get("entries", {})
        known = set()
        for entry in result["targets"]:
            key = entry["semantic_id"]
            known.add(key)
            entry["authored_values"] = deepcopy(authored.get(key, {}))
            entry["effective_values"] = dict(entry["values"], **authored.get(key, {}))
            encoded = validate_movement_values(entry["effective_values"])
            entry["effective_parked_target"] = ((encoded['x'] & 127) == 127 and (encoded['z'] & 127) == 127) if entry['mnemonic'] == 'NPC_RUN' else None
        result["unresolved_overrides"] = sorted(set(authored) - known)
        return result

    def _validate_facing(self, identifier: str, value: dict) -> None:
        import re
        from importer.core import ImportError
        from importer.facing_authoring import validate_facing_values
        self._dialogue_document(identifier)
        if (not isinstance(value, dict) or set(value) != {'entries'} or
                not isinstance(value['entries'], dict) or not 1 <= len(value['entries']) <= 1024):
            raise ProjectError('ScriptFacing requires a bounded nonempty entry collection')
        prefix = 'script://' + identifier.removeprefix('scene://') + '/facing/'
        for key, fields in value['entries'].items():
            if not isinstance(key, str) or re.fullmatch(re.escape(prefix) + r'[0-9a-f]{4}', key) is None:
                raise ProjectError('Facing operand must belong to its source owner')
            try:
                validate_facing_values(fields)
            except ImportError as error:
                raise ProjectError(str(error)) from error

    def _facing_context(self, identifier: str):
        from importer.facing_authoring import FacingAuthoringContext
        return FacingAuthoringContext(self._dialogue_context(identifier))

    def facing_options(self, identifier: str) -> dict:
        from importer.facing_authoring import validate_facing_values
        result = self._facing_context(identifier).options(identifier)
        authored = self.overrides.get(identifier, {}).get('ScriptFacing', {}).get('entries', {})
        known = set()
        for entry in result['targets']:
            key = entry['semantic_id']
            known.add(key)
            entry['authored_values'] = deepcopy(authored.get(key, {}))
            entry['effective_values'] = dict(entry['values'], **authored.get(key, {}))
            validate_facing_values(entry['effective_values'])
        result['unresolved_overrides'] = sorted(set(authored) - known)
        return result

    def _validate_branches(self, identifier: str, value: dict) -> None:
        from .script_branches import validate
        validate(self, identifier, value)

    def _validate_worldmap_menu(self, identifier: str, value: dict) -> None:
        from .worldmap_authoring import validate
        validate(self, identifier, value)

    def _branch_context(self, identifier: str):
        from importer.branch_authoring import BranchAuthoringContext
        return BranchAuthoringContext(self._dialogue_context(identifier))

    def _validate_flags(self, identifier: str, value: dict) -> None:
        import re
        from importer.core import ImportError
        from importer.flag_authoring import validate_flag_values
        self._dialogue_document(identifier)
        if (not isinstance(value, dict) or set(value) != {"entries"} or
                not isinstance(value["entries"], dict) or not 1 <= len(value["entries"]) <= 1024):
            raise ProjectError("ScriptFlags requires a bounded nonempty entry collection")
        prefix = "script://" + identifier.removeprefix("scene://") + "/flag-bit/"
        for key, fields in value["entries"].items():
            if not isinstance(key, str) or re.fullmatch(re.escape(prefix) + r"[0-9a-f]{4}", key) is None:
                raise ProjectError("Flag operand must belong to its source owner")
            try:
                validate_flag_values(fields)
            except ImportError as error:
                raise ProjectError(str(error)) from error

    def _flag_context(self, identifier: str):
        from importer.flag_authoring import FlagAuthoringContext
        return FlagAuthoringContext(self._dialogue_context(identifier))

    def flag_options(self, identifier: str) -> dict:
        from importer.flag_authoring import validate_flag_values
        result = self._flag_context(identifier).options(identifier)
        authored = self.overrides.get(identifier, {}).get("ScriptFlags", {}).get("entries", {})
        known = set()
        for entry in result["targets"]:
            key = entry["semantic_id"]
            known.add(key)
            entry["authored_values"] = deepcopy(authored.get(key, {}))
            entry["effective_values"] = dict(entry["values"], **authored.get(key, {}))
            validate_flag_values(entry["effective_values"])
        result["unresolved_overrides"] = sorted(set(authored) - known)
        return result

    def _validate_waits(self, identifier: str, value: dict) -> None:
        import re
        from importer.core import ImportError
        from importer.wait_authoring import validate_wait_values
        self._dialogue_document(identifier)
        if (not isinstance(value, dict) or set(value) != {"entries"} or
                not isinstance(value["entries"], dict) or not 1 <= len(value["entries"]) <= 1024):
            raise ProjectError("ScriptWaits requires a bounded nonempty entry collection")
        prefix = "script://" + identifier.removeprefix("scene://") + "/wait/"
        for key, fields in value["entries"].items():
            if not isinstance(key, str) or re.fullmatch(re.escape(prefix) + r"[0-9a-f]{4}", key) is None:
                raise ProjectError("Wait operand must belong to its source owner")
            try:
                validate_wait_values(fields)
            except ImportError as error:
                raise ProjectError(str(error)) from error

    def _wait_context(self, identifier: str):
        from importer.wait_authoring import WaitAuthoringContext
        return WaitAuthoringContext(self._dialogue_context(identifier))

    def wait_options(self, identifier: str) -> dict:
        from importer.wait_authoring import validate_wait_values
        result = self._wait_context(identifier).options(identifier)
        authored = self.overrides.get(identifier, {}).get("ScriptWaits", {}).get("entries", {})
        known = set()
        for entry in result["targets"]:
            key = entry["semantic_id"]
            known.add(key)
            entry["authored_values"] = deepcopy(authored.get(key, {}))
            entry["effective_values"] = dict(entry["values"], **authored.get(key, {}))
            validate_wait_values(entry["effective_values"])
        result["unresolved_overrides"] = sorted(set(authored) - known)
        return result

    def _validate_model_selectors(self, identifier: str, value: dict) -> None:
        import re
        from importer.core import ImportError
        from importer.model_selector_authoring import validate_model_selector_values
        self._dialogue_document(identifier)
        if (not isinstance(value, dict) or set(value) != {"entries"} or
                not isinstance(value["entries"], dict) or not 1 <= len(value["entries"]) <= 1024):
            raise ProjectError("ScriptModelSelectors requires a bounded nonempty entry collection")
        prefix = "script://" + identifier.removeprefix("scene://") + "/model-selector/"
        for key, fields in value["entries"].items():
            if not isinstance(key, str) or re.fullmatch(re.escape(prefix) + r"[0-9a-f]{4}", key) is None:
                raise ProjectError("ModelSelector operand must belong to its source owner")
            try:
                validate_model_selector_values(fields)
            except ImportError as error:
                raise ProjectError(str(error)) from error

    def _model_selector_context(self, identifier: str):
        from importer.model_selector_authoring import ModelSelectorAuthoringContext
        return ModelSelectorAuthoringContext(self._dialogue_context(identifier))

    def model_selector_options(self, identifier: str) -> dict:
        from importer.model_selector_authoring import validate_model_selector_values
        result = self._model_selector_context(identifier).options(identifier)
        authored = self.overrides.get(identifier, {}).get("ScriptModelSelectors", {}).get("entries", {})
        known = set()
        for entry in result["targets"]:
            key = entry["semantic_id"]
            known.add(key)
            entry["authored_values"] = deepcopy(authored.get(key, {}))
            entry["effective_values"] = dict(entry["values"], **authored.get(key, {}))
            validate_model_selector_values(entry["effective_values"])
        result["unresolved_overrides"] = sorted(set(authored) - known)
        return result

    def _validate_transitions(self, identifier: str, value: dict) -> None:
        import re
        from importer.transition_authoring import ENTRY_FIELDS
        self._dialogue_document(identifier)
        if (not isinstance(value, dict) or set(value) != {"entries"} or
                not isinstance(value["entries"], dict) or not 1 <= len(value["entries"]) <= 1024):
            raise ProjectError("Transitions require a bounded nonempty entry collection")
        prefix = "script://" + identifier.removeprefix("scene://") + "/transition/"
        for key, fields in value["entries"].items():
            if not isinstance(key, str) or re.fullmatch(re.escape(prefix) + r"[0-9a-f]{4}", key) is None:
                raise ProjectError("Transition must belong to its source owner")
            if (not isinstance(fields, dict) or not fields or set(fields) - set(ENTRY_FIELDS) or
                    any(type(v) is not int or not 0 <= v <= 255 for v in fields.values())):
                raise ProjectError("Transition entry fields require encoded integer bytes")

    def _transition_context(self, identifier: str):
        from importer.transition_authoring import TransitionAuthoringContext
        return TransitionAuthoringContext(self._dialogue_context(identifier))

    def transition_options(self, identifier: str) -> dict:
        result = self._transition_context(identifier).options(identifier)
        authored = self.overrides.get(identifier, {}).get("Transitions", {}).get("entries", {})
        known = set()
        for entry in result["transitions"]:
            key = entry["semantic_id"]
            known.add(key)
            entry["authored_values"] = deepcopy(authored.get(key, {}))
            entry["effective_values"] = dict(entry["values"], **authored.get(key, {}))
            from importer.transition_authoring import reference_entry_interpretation
            entry["effective_interpretation"] = reference_entry_interpretation(entry["effective_values"])
        result["unresolved_overrides"] = sorted(set(authored) - known)
        return result

    def dialogue_options(self, identifier: str) -> dict:
        return self._dialogue_options(self._dialogue_context(identifier), identifier)

    def _dialogue_options(self, context, identifier: str) -> dict:
        """Annotate one verified snapshot consistently for inspection/discovery."""
        result = deepcopy(context.options(identifier))
        authored = self.overrides.get(identifier, {}).get("Dialogue", {}).get("runs", {})
        known = set()
        for run in result["runs"]:
            run_id = run["semantic_id"]
            known.add(run_id)
            replacement = authored.get(run_id)
            run["authored_text"] = replacement
            run["effective_text"] = run["text"] if replacement is None else replacement.ljust(run["max_length"])
            if replacement is not None and "|" in replacement:
                run["effective_text"] = None
                run["validation_error"] = "Saved replacement contains renderer newline (|); clear it or replace it with supported glyphs"
            elif replacement is not None and len(replacement) > run["max_length"]:
                run["effective_text"] = None
                run["validation_error"] = "Saved replacement exceeds the verified source run capacity"
        result["unresolved_overrides"] = sorted(set(authored) - known)
        return result

    def dialogue_font(self, identifier: str) -> dict:
        from importer.dialogue_font import load_dialogue_font
        from importer.pipeline import _disc_context
        if not self.disc_path:
            raise ProjectError("Glyph preview requires the project retail disc")
        with _disc_context(self.disc_path):
            context = self._dialogue_context(identifier)
            if not context.options(identifier)["supported"]:
                raise ProjectError("Glyph preview requires supported source text runs")
            result = load_dialogue_font(self.disc_path)
            result.update(owner_id=identifier, decoded_man_sha256=context.provenance()["decoded_man_sha256"])
            return result

    def _dialogue_json_document(self, identifier: str, context) -> dict:
        options = context.options(identifier)
        authored = self.overrides.get(identifier, {}).get("Dialogue", {}).get("runs", {})
        known = {run["semantic_id"] for run in options["runs"]}
        if not options["supported"] or set(authored) - known:
            raise ProjectError("Text JSON requires supported runs and no unresolved text overrides")
        document = dict(schema="legaia.text-runs.v1", owner_id=identifier,
                        decoded_man_sha256=context.provenance()["decoded_man_sha256"],
                        authored_state_sha256=digest(authored), runs=[
                            dict(run_id=run["semantic_id"], byte_length=run["byte_length"],
                                 retail_text=run["text"], text=authored.get(run["semantic_id"]))
                            for run in options["runs"]])
        if len(canonical(document)) > 1024 * 1024:
            raise ProjectError("Text JSON exceeds the 1 MiB file bound")
        return document

    def dialogue_json_source(self, identifier: str) -> dict:
        return self._dialogue_json_document(identifier, self._dialogue_context(identifier))

    def _prepare_dialogue_json(self, identifier: str, content: bytes):
        if self.mode != "edit":
            raise ProjectError("Text JSON import requires Edit mode")
        if not isinstance(content, bytes) or not 0 < len(content) <= 1024 * 1024:
            raise ProjectError("Text JSON requires a nonempty file of at most 1 MiB")
        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ProjectError("Text JSON contains duplicate object keys")
                result[key] = value
            return result
        def finite(_):
            raise ProjectError("Text JSON requires finite values")
        try:
            document = json.loads(content.decode("utf-8"), object_pairs_hook=unique, parse_constant=finite)
        except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
            raise ProjectError("Text JSON is not bounded UTF-8 JSON") from exc
        context = self._dialogue_context(identifier)
        expected = self._dialogue_json_document(identifier, context)
        if not isinstance(document, dict) or set(document) != set(expected):
            raise ProjectError("Text JSON has unknown or missing fields")
        if any(document[key] != expected[key] for key in expected if key != "runs"):
            raise ProjectError("Text JSON source or authored-state binding is stale or belongs to another owner")
        items = document["runs"]
        if not isinstance(items, list) or len(items) != len(expected["runs"]):
            raise ProjectError("Text JSON must retain the complete supported run collection")
        source = {run["run_id"]: run for run in expected["runs"]}
        requested, seen, changes = {}, set(), []
        from importer.dialogue_authoring import validate_dialogue_text
        for item in items:
            if not isinstance(item, dict) or set(item) != {"run_id", "byte_length", "retail_text", "text"}:
                raise ProjectError("Text JSON run has unknown or missing fields")
            run_id = item["run_id"]
            if not isinstance(run_id, str) or run_id not in source or run_id in seen:
                raise ProjectError("Text JSON run is duplicated or not supported by this owner")
            seen.add(run_id)
            original = source[run_id]
            if type(item["byte_length"]) is not int or not isinstance(item["retail_text"], str):
                raise ProjectError("Text JSON immutable run metadata requires exact scalar types")
            if digest({key:value for key,value in item.items() if key != "text"}) != digest({key:value for key,value in original.items() if key != "text"}):
                raise ProjectError("Text JSON changed immutable run identity, capacity or retail text")
            text = item["text"]
            if text is not None:
                validate_dialogue_text(text)
                if len(text) > original["byte_length"]:
                    raise ProjectError("Text JSON replacement exceeds its source run capacity")
                requested[run_id] = text
            if text != original["text"]:
                changes.append(dict(run_id=run_id, before=original["text"], after=text,
                                    retail=original["retail_text"],
                                    effective=original["retail_text"] if text is None else text.ljust(original["byte_length"])))
        context.patch(requested)
        return requested, dict(owner_id=identifier, change_count=len(changes), changes=changes,
                               candidate_sha256=hashlib.sha256(content).hexdigest(),
                               scope="equal-span-text-runs", gameplay="not_verified")

    def preview_dialogue_json(self, identifier: str, content: bytes) -> dict:
        return self._prepare_dialogue_json(identifier, content)[1]

    def import_dialogue_json(self, identifier: str, content: bytes) -> dict:
        requested, report = self._prepare_dialogue_json(identifier, content)
        before = deepcopy(self.overrides.get(identifier))
        after = deepcopy(before or {})
        if requested:
            after["Dialogue"] = {"runs": requested}
        else:
            after.pop("Dialogue", None)
        after = after or None
        if before != after:
            if after is None:
                self.overrides.pop(identifier, None)
            else:
                self.overrides[identifier] = after
            self.undo_stack.append(dict(entity_id=identifier, before=before, after=deepcopy(after)))
            self.redo_stack.clear()
        return report

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

    def texture_palette_source(self, asset_id: str, palette_index: int) -> dict:
        import struct
        from importer.textures import parse_tim
        context = self._texture_context(asset_id)
        original = context.original_tim(asset_id)
        effective = (self.read_texture_replacement(self.texture_overrides[asset_id])
                     if asset_id in self.texture_overrides else original)
        context.validate_replacement(asset_id, effective)
        tim, retail = parse_tim(effective), parse_tim(original)
        if tim.bpp not in (4, 8) or tim.clut is None:
            raise ProjectError('Palette editing requires an indexed scene TIM')
        count = 16 if tim.bpp == 4 else 256
        if type(palette_index) is not int or palette_index < 0 or (palette_index + 1) * count * 2 > len(tim.clut.data):
            raise ProjectError('Choose an existing texture palette')
        offset = palette_index * count * 2
        return {'asset_id': asset_id, 'palette_index': palette_index, 'entry_count': count,
                'source_sha256': hashlib.sha256(original).hexdigest(),
                'effective_sha256': hashlib.sha256(effective).hexdigest(),
                'words': list(struct.unpack_from(f'<{count}H', tim.clut.data, offset)),
                'retail_words': list(struct.unpack_from(f'<{count}H', retail.clut.data, offset))}

    def set_texture_palette_word(self, asset_id: str, palette_index: int, entry_index: int,
                                 word: int, expected_sha256: str) -> None:
        from importer.texture_authoring import patch_tim_palette_word
        if self.mode != 'edit':
            raise ProjectError('Texture palette authoring requires Edit mode')
        original = self._texture_context(asset_id).original_tim(asset_id)
        effective = (self.read_texture_replacement(self.texture_overrides[asset_id])
                     if asset_id in self.texture_overrides else original)
        replacement = patch_tim_palette_word(effective, expected_sha256, palette_index, entry_index, word)
        if replacement != effective:
            self.set_texture_replacement(asset_id, replacement)

    def texture_pixel_source(self, asset_id: str, palette_index: int, x: int, y: int) -> dict:
        from importer.texture_authoring import inspect_tim_pixel_index
        source = self.texture_palette_source(asset_id, palette_index)
        original = self._texture_context(asset_id).original_tim(asset_id)
        effective = (self.read_texture_replacement(self.texture_overrides[asset_id])
                     if asset_id in self.texture_overrides else original)
        pixel = inspect_tim_pixel_index(effective, x, y)
        return dict(source, pixel=pixel, retail_entry=inspect_tim_pixel_index(original, x, y)['palette_entry'])

    def set_texture_pixel_index(self, asset_id: str, x: int, y: int, palette_entry: int,
                                expected_sha256: str) -> None:
        from importer.texture_authoring import patch_tim_pixel_index
        if self.mode != 'edit':
            raise ProjectError('Texture pixel authoring requires Edit mode')
        original = self._texture_context(asset_id).original_tim(asset_id)
        effective = (self.read_texture_replacement(self.texture_overrides[asset_id])
                     if asset_id in self.texture_overrides else original)
        replacement = patch_tim_pixel_index(effective, expected_sha256, x, y, palette_entry)
        if replacement != effective:
            self.set_texture_replacement(asset_id, replacement)

    def set_texture_index_rectangle(self, asset_id: str, x: int, y: int, width: int,
                                     height: int, palette_entry: int, expected_sha256: str) -> None:
        from importer.texture_authoring import patch_tim_index_rectangle
        if self.mode != 'edit':
            raise ProjectError('Texture rectangle authoring requires Edit mode')
        context = self._texture_context(asset_id)
        original = context.original_tim(asset_id)
        effective = (self.read_texture_replacement(self.texture_overrides[asset_id])
                     if asset_id in self.texture_overrides else original)
        context.validate_replacement(asset_id,effective)
        replacement = patch_tim_index_rectangle(effective,expected_sha256,x,y,width,height,palette_entry)
        if replacement != effective:
            self.set_texture_replacement(asset_id,replacement)

    def copy_texture_index_rectangle(self, asset_id: str, source_x: int, source_y: int,
                                     x: int, y: int, width: int, height: int, expected_sha256: str) -> None:
        from importer.texture_authoring import copy_tim_index_rectangle
        if self.mode != 'edit':
            raise ProjectError('Texture rectangle authoring requires Edit mode')
        context = self._texture_context(asset_id)
        original = context.original_tim(asset_id)
        effective = (self.read_texture_replacement(self.texture_overrides[asset_id])
                     if asset_id in self.texture_overrides else original)
        context.validate_replacement(asset_id, effective)
        replacement = copy_tim_index_rectangle(effective, expected_sha256, source_x, source_y, x, y, width, height)
        if replacement != effective:
            self.set_texture_replacement(asset_id, replacement)

    def texture_json_source(self, asset_id: str, layer: str = 'imported') -> dict:
        import base64
        from importer.texture_json import export_texture_json
        if layer not in ('imported','effective'):
            raise ProjectError('Choose imported or effective texture JSON')
        context = self._texture_context(asset_id)
        original = context.original_tim(asset_id)
        effective = (self.read_texture_replacement(self.texture_overrides[asset_id])
                     if layer == 'effective' and asset_id in self.texture_overrides else original)
        context.validate_replacement(asset_id,effective)
        document = json.loads(export_texture_json(effective))
        document['source_sha256'] = hashlib.sha256(original).hexdigest()
        content = (json.dumps(document,separators=(',',':'),sort_keys=True)+'\n').encode()
        return {'asset_id':asset_id,'layer':layer,'source_sha256':document['source_sha256'],
                'effective_sha256':hashlib.sha256(effective).hexdigest(),
                'json_base64':base64.b64encode(content).decode('ascii')}

    def set_texture_json(self, asset_id: str, content: bytes) -> None:
        from importer.texture_json import import_texture_json
        if self.mode != 'edit':
            raise ProjectError('Texture JSON authoring requires Edit mode')
        original = self._texture_context(asset_id).original_tim(asset_id)
        replacement = import_texture_json(original,hashlib.sha256(original).hexdigest(),content)
        self.set_texture_replacement(asset_id,replacement)

    def _prepare_texture_file(self, asset_id: str, content: bytes, format: str,
                              palette_index: int = 0) -> tuple[bytes, dict]:
        import base64
        from importer.texture_json import import_texture_json
        from importer.texture_authoring import texture_payload_changes
        from importer.textures import parse_tim, decode_tim
        if self.mode != 'edit' or format not in ('tim','json'):
            raise ProjectError('Texture file preview requires Edit mode and TIM or JSON')
        context = self._texture_context(asset_id)
        original = context.original_tim(asset_id)
        candidate = import_texture_json(original,hashlib.sha256(original).hexdigest(),content) if format == 'json' else content
        context.validate_replacement(asset_id,candidate)
        effective = (self.read_texture_replacement(self.texture_overrides[asset_id])
                     if asset_id in self.texture_overrides else original)
        context.validate_replacement(asset_id,effective)
        pixels = decode_tim(candidate,palette_index)
        return candidate, {'asset_id':asset_id,'input_format':format,'palette_index':palette_index,
                'source_sha256':hashlib.sha256(original).hexdigest(),
                'effective_sha256':hashlib.sha256(effective).hexdigest(),
                'candidate_sha256':hashlib.sha256(candidate).hexdigest(),
                'width':pixels['width'],'height':pixels['height'],'bpp':parse_tim(candidate).bpp,
                'rgba_base64':base64.b64encode(pixels['rgba']).decode('ascii'),
                'stp_base64':base64.b64encode(pixels['stp']).decode('ascii'),
                'retail_changes':texture_payload_changes(original,candidate),
                'current_changes':texture_payload_changes(effective,candidate),
                'representation':'proposed_file','project_changed':False}

    def preview_texture_file(self, asset_id: str, content: bytes, format: str,
                             palette_index: int = 0) -> dict:
        return self._prepare_texture_file(asset_id,content,format,palette_index)[1]

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

    def _model_source(self, asset_id: str, scene_id: str):
        from importer.pipeline import _disc_context, import_scene
        from importer.assets import load_model_source
        document = self.imports.get(scene_id)
        if document is None or not self.disc_path:
            raise ProjectError('Model shape requires an imported scene and its disc')
        asset = next((a for a in document['assets']['models'] if a['semantic_id'] == asset_id), None)
        if asset is None:
            raise ProjectError('Unknown imported model identity')
        with _disc_context(self.disc_path):
            if import_scene(self.disc_path, document['scene']['name']) != document:
                raise ProjectError('Model source differs from imported evidence')
            return load_model_source(self.disc_path, asset)

    def _model_candidate_changes(self, asset_id, original, content):
        """Audit against actual Retail ownership, retaining an existing topology binding."""
        from importer.model_authoring import replace_model_content
        from importer.model_face_removal import qualify_face_removal, FORMAT
        binding = self.model_overrides.get(asset_id)
        if binding and binding['format'] == 'tmd-face-addition-v1':
            effective = self.read_model_replacement(asset_id,binding)
            from importer.core import ImportError as ModelImportError
            try:
                return replace_model_content(effective,hashlib.sha256(effective).hexdigest(),content,
                                             allow_normal_references=True)[1]
            except ModelImportError as error:
                raise ProjectError(str(error)) from error
        if binding and binding['format'] == FORMAT:
            _, changes = qualify_face_removal(original, hashlib.sha256(original).hexdigest(),
                                              content, binding['removed_faces'])
            return changes + [dict(kind='primitive_removal', **row) for row in binding['removed_faces']]
        return replace_model_content(original, hashlib.sha256(original).hexdigest(), content,
                                     allow_normal_references=True)[1]

    def read_model_replacement(self, asset_id: str, binding: dict) -> bytes:
        from importer.model_authoring import replace_model_shape, replace_model_content
        removal = isinstance(binding, dict) and binding.get('format') == 'tmd-face-removal-v1'
        addition = isinstance(binding, dict) and binding.get('format') == 'tmd-face-addition-v1'
        extra = {'base_binding', 'ledger'} if addition else {'removed_faces'} if removal else set()
        if (not isinstance(binding, dict) or set(binding) != {'asset_sha256','source_sha256','byte_length','source_scene_id','format'} | extra
                or binding['format'] not in ('tmd-shape', 'tmd-content-v1', 'tmd-content-v2', 'tmd-content-v3', 'tmd-face-removal-v1', 'tmd-face-addition-v1') or type(binding['byte_length']) is not int
                or not 1 <= binding['byte_length'] <= 4*1024*1024
                or any(not isinstance(binding[k],str) or len(binding[k]) != 64 or any(c not in '0123456789abcdef' for c in binding[k]) for k in ('asset_sha256','source_sha256'))
                or not isinstance(binding['source_scene_id'], str)):
            raise ProjectError('Invalid model shape binding')
        path = self.root / 'Authored' / 'Models' / (binding['asset_sha256'] + '.tmd')
        if not path.resolve().is_relative_to(self.root) or path.stat().st_size != binding['byte_length']:
            raise ProjectError('Model shape path or size differs from binding')
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != binding['asset_sha256']:
            raise ProjectError('Model shape content hash differs from binding')
        original = self._model_source(asset_id, binding['source_scene_id'])
        if addition:
            from .model_face_addition import base_content
            from importer.model_face_ledger import qualify_face_ledger
            if hashlib.sha256(original).hexdigest() != binding['source_sha256']:
                raise ProjectError('Face addition Retail source hash changed')
            base = base_content(self, asset_id, original, binding)
            qualify_face_ledger(base, binding['ledger'], content)
        elif removal:
            from importer.model_face_removal import qualify_face_removal
            qualify_face_removal(original, binding['source_sha256'], content, binding['removed_faces'])
        elif binding['format'] == 'tmd-shape':
            replace_model_shape(original, binding['source_sha256'], content)
        else:
            replace_model_content(original, binding['source_sha256'], content,
                                  allow_materials=binding['format'] in ('tmd-content-v2', 'tmd-content-v3'),
                                  allow_normal_references=binding['format'] == 'tmd-content-v3')
        return content

    def apply_model_face_additions(self, asset_id, requests, expected_sha256, expected_key, proposed_sha256):
        from .model_face_addition import prepare
        content, binding, report = prepare(self, asset_id, requests, expected_sha256, expected_key)
        if proposed_sha256 != report['proposed_sha256']:
            raise ProjectError('Face addition differs from its reviewed candidate')
        self._publish_model_ledger(asset_id,content,binding,expected_key,'Face addition')

    def apply_model_vector_allocations(self, asset_id, requests, expected_sha256, expected_key, proposed_sha256):
        from .model_vector_allocation import prepare
        content,binding,report=prepare(self,asset_id,requests,expected_sha256,expected_key)
        if proposed_sha256!=report['proposed_sha256']:
            raise ProjectError('Vector allocation differs from its reviewed candidate')
        self._publish_model_ledger(asset_id,content,binding,expected_key,'Vector allocation')

    def apply_model_group_allocations(self,asset_id,requests,expected_sha256,expected_key,review_key):
        from .model_group_allocation import prepare
        content,binding,report=prepare(self,asset_id,requests,expected_sha256,expected_key)
        if review_key!=report['review_key']:
            raise ProjectError('Group allocation identities or fields differ from the reviewed draft')
        self._publish_model_ledger(asset_id,content,binding,expected_key,'Group allocation')

    def apply_model_object_allocations(self,asset_id,requests,expected_sha256,expected_key,review_key):
        from .model_object_allocation import prepare
        content,binding,report=prepare(self,asset_id,requests,expected_sha256,expected_key)
        if review_key!=report['review_key']:
            raise ProjectError('Object allocation identities differ from the reviewed draft')
        self._publish_model_ledger(asset_id,content,binding,expected_key,'Object allocation')

    def apply_model_mesh_append(self,asset_id,content,donor_face_id,expected_sha256,expected_key,review_key,*,new_group=False,replace_group=False,preserve_primitives=False,primitive_index=None,material_colors=False,scene_index=None,uv_set=0):
        from .model_mesh_append import prepare
        candidate,binding,report=prepare(self,asset_id,content,donor_face_id,expected_sha256,expected_key,new_group=new_group,replace_group=replace_group,preserve_primitives=preserve_primitives,primitive_index=primitive_index,material_colors=material_colors,scene_index=scene_index,uv_set=uv_set)
        if review_key!=report['review_key']:
            raise ProjectError('Mesh import differs from the reviewed geometry or donor')
        self._publish_model_ledger(asset_id,candidate,binding,expected_key,'Mesh append')

    def _publish_model_ledger(self,asset_id,content,binding,expected_key,operation):
        from .scene_preview import source_key
        if asset_id not in self.model_overrides and len(self.model_overrides) >= 128:
            raise ProjectError('Project supports at most 128 model replacements')
        path = self.root / 'Authored' / 'Models' / (binding['asset_sha256'] + '.tmd')
        if not path.resolve().is_relative_to(self.root):
            raise ProjectError(operation+' path escapes project')
        if source_key(self) != expected_key:
            raise ProjectError('Project changed while preparing '+operation.lower())
        if path.exists():
            self.read_model_replacement(asset_id, binding)
        else:
            atomic_write(path, content)
        if source_key(self)!=expected_key:
            raise ProjectError('Project changed before publishing '+operation.lower())
        before = deepcopy(self.model_overrides.get(asset_id))
        self.model_overrides[asset_id] = deepcopy(binding)
        self.undo_stack.append(dict(target='model_overrides', asset_id=asset_id, before=before, after=deepcopy(binding)))
        self.redo_stack.clear()

    def apply_model_face_removal(self, asset_id, selections, expected_sha256, expected_key, proposed_sha256, *, restore=False):
        from .model_face_removal import prepare
        from .scene_preview import source_key
        content, removed, report = prepare(self, asset_id, selections, expected_sha256, expected_key, restore=restore)
        if proposed_sha256 != report['proposed_sha256']:
            raise ProjectError('Face removal differs from its reviewed candidate')
        if content == report.pop('_effective'):
            return
        if asset_id not in self.model_overrides and len(self.model_overrides) >= 128:
            raise ProjectError('Project supports at most 128 model replacements')
        retained_ledger = report.pop('_binding', None)
        binding = retained_ledger or dict(format='tmd-face-removal-v1', source_scene_id=self.active_scene,
                       source_sha256=report['source_sha256'], asset_sha256=report['proposed_sha256'],
                       byte_length=len(content), removed_faces=removed)
        if not removed and retained_ledger is None:
            from importer.model_authoring import replace_model_content
            original = self._model_source(asset_id, self.active_scene)
            _, changes = replace_model_content(original, report['source_sha256'], content, allow_normal_references=True)
            material = any(row['kind'] == 'primitive_group' or row['kind'] == 'primitive' and row['field'] in ('clut', 'tpage') for row in changes)
            normals = any(row['kind'] == 'primitive' and row['field'] == 'normal_index' for row in changes)
            binding.pop('removed_faces')
            binding['format'] = 'tmd-content-v3' if normals else 'tmd-content-v2' if material else 'tmd-content-v1' if any(row['kind'] == 'primitive' for row in changes) else 'tmd-shape'
            if not changes:
                binding = None
        path = self.root / 'Authored' / 'Models' / (report['proposed_sha256'] + '.tmd')
        if not path.resolve().is_relative_to(self.root):
            raise ProjectError('Model replacement path escapes project')
        if source_key(self) != expected_key:
            raise ProjectError('Project changed while preparing face removal')
        if binding is not None:
            if path.exists():
                self.read_model_replacement(asset_id, binding)
            else:
                atomic_write(path, content)
        before = deepcopy(self.model_overrides.get(asset_id))
        if binding is None:
            self.model_overrides.pop(asset_id, None)
        else:
            self.model_overrides[asset_id] = binding
        self.undo_stack.append(dict(target='model_overrides', asset_id=asset_id, before=before, after=deepcopy(binding)))
        self.redo_stack.clear()

    def _prepare_model_file(self, asset_id: str, content: bytes, format: str) -> tuple[bytes, dict]:
        from importer.model_authoring import replace_model_content
        from importer.model_json import import_shape_json, export_shape_json
        from importer.model_obj import import_shape_obj
        if self.mode != 'edit':
            raise ProjectError('Model shape authoring requires Edit mode')
        if format not in ('tmd', 'obj', 'json'):
            raise ProjectError('Choose TMD, OBJ or JSON model file')
        original = self._model_source(asset_id, self.active_scene)
        digest = hashlib.sha256(original).hexdigest()
        effective = (self.read_model_replacement(asset_id, self.model_overrides[asset_id])
                     if asset_id in self.model_overrides else original)
        if format == 'json':
            import json
            json_source = effective if self.model_overrides.get(asset_id, {}).get('format') == 'tmd-face-addition-v1' else original
            vectors, _ = import_shape_json(json_source, hashlib.sha256(json_source).hexdigest(), content)
            document = json.loads(export_shape_json(vectors))
            document['source_sha256'] = hashlib.sha256(effective).hexdigest()
            replacement, _ = import_shape_json(effective, document['source_sha256'], json.dumps(document).encode())
        elif format == 'obj':
            replacement, _ = import_shape_obj(effective, hashlib.sha256(effective).hexdigest(), content)
        else:
            self._model_candidate_changes(asset_id, original, content)
            replacement = content
        changes = self._model_candidate_changes(asset_id, original, replacement)
        _, pending = replace_model_content(effective, hashlib.sha256(effective).hexdigest(), replacement, allow_normal_references=True)
        return replacement, {'asset_id': asset_id, 'source_sha256': digest,
                             'proposed_sha256': hashlib.sha256(replacement).hexdigest(),
                             'comparison': ('current_addition_topology' if self.model_overrides.get(asset_id, {}).get('format') == 'tmd-face-addition-v1' else 'retail_source'), 'coordinate_changes': changes,
                             'changes_from_current': pending, 'project_changed': False}

    def model_primitive_source(self, asset_id: str) -> dict:
        """Inspect source packet identities and the current authored values."""
        from importer.model_primitives import inspect_model_primitives
        from .scene_preview import source_key
        key = source_key(self)
        original = self._model_source(asset_id, self.active_scene)
        effective = (self.read_model_replacement(asset_id, self.model_overrides[asset_id])
                     if asset_id in self.model_overrides else original)
        report = inspect_model_primitives(effective, include_normal_references=True)
        report.update(asset_id=asset_id, source_sha256=hashlib.sha256(original).hexdigest(),
                      effective_sha256=hashlib.sha256(effective).hexdigest(),
                      project_source_key=key,
                      retail_objects=inspect_model_primitives(original, include_normal_references=True)['objects'])
        if self.model_overrides.get(asset_id, {}).get('format') == 'tmd-face-removal-v1':
            from .model_reference_faces import mapping
            report.update(schema_version='legaia.model-primitives.v3', face_mappings=[mapping(original, effective, self.model_overrides[asset_id], obj['object_index']) for obj in report['objects']])
        if self.model_overrides.get(asset_id, {}).get('format') == 'tmd-face-addition-v1':
            from .model_reference_faces import addition_mapping
            maps,authored=addition_mapping(self,asset_id,original,effective,self.model_overrides[asset_id])
            report.update(schema_version='legaia.model-primitives.v4',face_mappings=maps,authored_faces=authored)
            ledger = self.model_overrides[asset_id]['ledger']
            if ledger['schema_version'] in ('legaia.model-face-addition-ledger.v5','legaia.model-face-addition-ledger.v6'):
                growth = [dict(object_index=obj['object_index'], vertices=0, normals=0)
                          for obj in report['objects']]
                for operation in ledger['operations']:
                    if operation['kind'] == 'allocate_vectors':
                        for request in operation['requests']:
                            growth[request['object_index']][request['kind']] += len(request['vectors'])
                for current, retail, added in zip(report['objects'], report['retail_objects'], growth):
                    if any(current[('vertex_count' if kind == 'vertices' else 'normal_count')] != retail[('vertex_count' if kind == 'vertices' else 'normal_count')] + added[kind]
                           for kind in ('vertices', 'normals')):
                        raise ProjectError('Vector allocation ownership differs from the Retail tables')
                report.update(schema_version='legaia.model-primitives.v5', vector_growth=growth)
            if ledger['schema_version']=='legaia.model-face-addition-ledger.v7':
                from .model_reference_faces import addition_object_ownership
                object_mappings,growth=addition_object_ownership(self,asset_id,original,effective,self.model_overrides[asset_id])
                report.update(schema_version='legaia.model-primitives.v6',object_mappings=object_mappings,vector_growth=growth)

        if not key or source_key(self) != key:
            raise ProjectError('Scene changed during face inspection; reopen the editor')
        return report

    def _prepare_model_primitives(self, asset_id: str, edits: list, expected_sha256: str,
                                  expected_source_key: str) -> tuple[bytes, dict]:
        from importer.model_primitives import patch_model_primitives
        from importer.model_authoring import replace_model_content
        from importer.assets import decode_tmd
        from .scene_preview import source_key
        if self.mode != 'edit':
            raise ProjectError('Model face authoring requires Edit mode')
        key = source_key(self)
        if not key or expected_source_key != key:
            raise ProjectError('Scene changed since face inspection; reopen the editor')
        original = self._model_source(asset_id, self.active_scene)
        effective = (self.read_model_replacement(asset_id, self.model_overrides[asset_id])
                     if asset_id in self.model_overrides else original)
        replacement, pending = patch_model_primitives(effective, expected_sha256, edits)
        changes = self._model_candidate_changes(asset_id, original, replacement)
        if source_key(self) != key:
            raise ProjectError('Scene changed during face inspection; reopen the editor')
        return replacement, dict(asset_id=asset_id, source_sha256=hashlib.sha256(original).hexdigest(),
                                 effective_sha256=hashlib.sha256(effective).hexdigest(),
                                 project_source_key=key, proposed_sha256=hashlib.sha256(replacement).hexdigest(),
                                 coordinate_changes=changes, changes_from_current=pending,
                                 project_changed=False, preview=decode_tmd(replacement),
                                 current_preview=decode_tmd(effective))

    def preview_model_primitives(self, asset_id: str, edits: list, expected_sha256: str,
                                 expected_source_key: str) -> dict:
        return self._prepare_model_primitives(asset_id, edits, expected_sha256, expected_source_key)[1]

    def set_model_primitives(self, asset_id: str, edits: list, expected_sha256: str,
                             expected_source_key: str, proposed_sha256: str) -> None:
        replacement, report = self._prepare_model_primitives(asset_id, edits, expected_sha256, expected_source_key)
        if report['proposed_sha256'] != proposed_sha256:
            raise ProjectError('Face draft differs from the reviewed proposal; preview it again')
        if report['changes_from_current']:
            self.set_model_replacement(asset_id, replacement)

    def set_model_vector(self, asset_id: str, object_index: int, kind: str, vector_index: int,
                         values: list[int], expected_sha256: str) -> None:
        import json
        from importer.model_json import export_shape_json, import_shape_json
        if self.mode != 'edit':
            raise ProjectError('Model vector editing requires Edit mode')
        original = self._model_source(asset_id, self.active_scene)
        effective = (self.read_model_replacement(asset_id, self.model_overrides[asset_id])
                     if asset_id in self.model_overrides else original)
        if hashlib.sha256(effective).hexdigest() != expected_sha256:
            raise ProjectError('Model changed since vector inspection; reopen the vector editor')
        document = json.loads(export_shape_json(effective))
        if type(object_index) is not int or not 0 <= object_index < len(document['objects']) or kind not in ('vertices', 'normals'):
            raise ProjectError('Choose an existing model object and vector kind')
        vectors = document['objects'][object_index][kind]
        if type(vector_index) is not int or not 0 <= vector_index < len(vectors):
            raise ProjectError('Choose an existing vector in the selected object')
        if not isinstance(values, list) or len(values) != 3 or any(type(v) is not int or not -32768 <= v <= 32767 for v in values):
            raise ProjectError('Vector XYZ requires three signed16 integer source values')
        vectors[vector_index] = values
        # Patch the effective source so a vector edit retains authored faces/UVs/colors.
        replacement, _ = import_shape_json(effective, expected_sha256, json.dumps(document).encode())
        self.set_model_replacement(asset_id, replacement)

    def translate_model_object(self, asset_id: str, object_index: int, offset: list[int],
                               expected_sha256: str) -> None:
        replacement, report = self._prepare_model_object(asset_id, object_index, 'translation',
                                                          {'offset': offset}, expected_sha256)
        if report['changes_from_current']:
            self.set_model_replacement(asset_id, replacement)

    def _prepare_model_object(self, asset_id: str, object_index: int, operation: str,
                              values: dict, expected_sha256: str) -> tuple[bytes, dict]:
        from importer.model_json import translate_shape_object, rotate_shape_object, scale_shape_object
        from importer.model_normal_length import rescale_object_normals
        from importer.model_normal_retarget import retarget_object_normals
        from importer.model_vertex_references import retarget_object_vertices
        from importer.assets import decode_tmd
        if self.mode != 'edit':
            raise ProjectError('Model object preview requires Edit mode')
        original = self._model_source(asset_id, self.active_scene)
        effective = (self.read_model_replacement(asset_id, self.model_overrides[asset_id])
                     if asset_id in self.model_overrides else original)
        if not isinstance(values, dict):
            raise ProjectError('Model object preview requires operation values')
        # This edit preserves the qualified Current packet layout. The final
        # candidate is then audited against the actual Retail binding below.
        operation_source = effective if self.model_overrides.get(asset_id, {}).get('format') in ('tmd-face-removal-v1','tmd-face-addition-v1') else original
        args = (operation_source, effective, expected_sha256, object_index)
        if operation == 'translation' and set(values) == {'offset'}:
            replacement = translate_shape_object(*args, values['offset'])
        elif operation == 'rotation' and set(values) == {'axis', 'quarter_turns'}:
            replacement = rotate_shape_object(*args, values['axis'], values['quarter_turns'])
        elif operation == 'scale' and set(values) == {'percent'}:
            replacement = scale_shape_object(*args, values['percent'])
        elif operation == 'normal_length' and set(values) == {'length'}:
            replacement = rescale_object_normals(*args, values['length'])
        elif operation == 'normal_references' and set(values) == {'from_index','to_index'}:
            replacement = retarget_object_normals(*args, values['from_index'], values['to_index'])
        elif operation == 'vertex_references' and set(values) == {'from_index','to_index'}:
            replacement = retarget_object_vertices(*args, values['from_index'], values['to_index'])
        else:
            raise ProjectError('Choose translation, rotation, scale, normal_length, normal_references or vertex_references with exact operation fields')
        report = self.preview_model_file(asset_id, replacement)
        report.update(effective_sha256=hashlib.sha256(effective).hexdigest(),
                      object_index=object_index, operation=operation,
                      preview=decode_tmd(replacement), current_preview=decode_tmd(effective))
        return replacement, report

    def preview_model_object(self, asset_id: str, object_index: int, operation: str,
                             values: dict, expected_sha256: str) -> dict:
        return self._prepare_model_object(asset_id, object_index, operation, values, expected_sha256)[1]

    def rescale_model_normals(self, asset_id: str, object_index: int, length: int,
                             expected_sha256: str) -> None:
        replacement, report = self._prepare_model_object(asset_id, object_index, 'normal_length',
                                                          {'length': length}, expected_sha256)
        if report['changes_from_current']:
            self.set_model_replacement(asset_id, replacement)

    def retarget_model_normals(self, asset_id: str, object_index: int, from_index: int, to_index: int,
                               expected_sha256: str, proposed_sha256: str) -> None:
        replacement, report = self._prepare_model_object(asset_id, object_index, 'normal_references',
                                                        {'from_index':from_index,'to_index':to_index},expected_sha256)
        if report['proposed_sha256'] != proposed_sha256:
            raise ProjectError('Normal reference draft differs from its reviewed proposal')
        if report['changes_from_current']:
            self.set_model_replacement(asset_id,replacement)

    def preview_model_file(self, asset_id: str, content: bytes, format: str = 'tmd') -> dict:
        return self._prepare_model_file(asset_id, content, format)[1]

    def retarget_model_vertices(self, asset_id: str, object_index: int, from_index: int, to_index: int,
                               expected_sha256: str, proposed_sha256: str) -> None:
        replacement, report = self._prepare_model_object(asset_id, object_index, 'vertex_references',
                                                        {'from_index': from_index, 'to_index': to_index}, expected_sha256)
        if report['proposed_sha256'] != proposed_sha256:
            raise ProjectError('Vertex reference draft differs from its reviewed proposal')
        if report['changes_from_current']:
            self.set_model_replacement(asset_id, replacement)

    def set_model_json(self, asset_id: str, content: bytes) -> None:
        self.set_model_replacement(asset_id, self._prepare_model_file(asset_id, content, 'json')[0])

    def set_model_obj(self, asset_id: str, content: bytes) -> None:
        self.set_model_replacement(asset_id, self._prepare_model_file(asset_id, content, 'obj')[0])

    def rotate_model_object(self, asset_id: str, object_index: int, axis: str,
                            quarter_turns: int, expected_sha256: str) -> None:
        replacement, report = self._prepare_model_object(asset_id, object_index, 'rotation',
                                                          {'axis': axis, 'quarter_turns': quarter_turns}, expected_sha256)
        if report['changes_from_current']:
            self.set_model_replacement(asset_id, replacement)

    def scale_model_object(self, asset_id: str, object_index: int, percent: int, expected_sha256: str) -> None:
        replacement, report = self._prepare_model_object(asset_id, object_index, 'scale',
                                                          {'percent': percent}, expected_sha256)
        if report['changes_from_current']:
            self.set_model_replacement(asset_id, replacement)

    def set_model_replacement(self, asset_id: str, content: bytes) -> None:
        if self.mode != 'edit':
            raise ProjectError('Model shape authoring requires Edit mode')
        if not isinstance(asset_id, str) or len(asset_id) > 512 or not isinstance(content, bytes) or not 1 <= len(content) <= 4*1024*1024:
            raise ProjectError('Model shape requires an asset identity and at most 4 MiB of TMD data')
        if asset_id not in self.model_overrides and len(self.model_overrides) >= 128:
            raise ProjectError('Project supports at most 128 model shapes')
        original = self._model_source(asset_id, self.active_scene)
        source_hash = hashlib.sha256(original).hexdigest()
        audit = self._model_candidate_changes(asset_id, original, content)
        before = deepcopy(self.model_overrides.get(asset_id))
        has_materials = any(row['kind'] == 'primitive_group' or
                            (row['kind'] == 'primitive' and row['field'] in ('clut', 'tpage')) for row in audit)
        has_normal_references = any(row['kind'] == 'primitive' and row['field'] == 'normal_index' for row in audit)
        binding = {'format': ('tmd-content-v3' if has_normal_references else
                              'tmd-content-v2' if has_materials else
                              'tmd-content-v1' if any(row['kind'] == 'primitive' for row in audit) else 'tmd-shape'),
                   'source_scene_id':self.active_scene,'source_sha256':source_hash,
                   'asset_sha256':hashlib.sha256(content).hexdigest(),'byte_length':len(content)} if audit else None
        if before and before['format'] == 'tmd-face-addition-v1':
            from .model_face_addition import base_content
            from importer.model_face_ledger import append_content_ledger
            effective = self.read_model_replacement(asset_id,before)
            if effective == content:
                return
            base = base_content(self,asset_id,original,before)
            _,ledger,_ = append_content_ledger(base,before['ledger'],content)
            binding = deepcopy(before)
            binding.update(asset_sha256=hashlib.sha256(content).hexdigest(),byte_length=len(content),ledger=ledger)
        if before and before['format'] == 'tmd-face-removal-v1' and binding is not None:
            binding.update(format=before['format'], removed_faces=deepcopy(before['removed_faces']))
        if before == binding:
            return
        if binding is not None:
            path = self.root / 'Authored' / 'Models' / (binding['asset_sha256'] + '.tmd')
            if not path.resolve().is_relative_to(self.root):
                raise ProjectError('Model shape path escapes project root')
            if path.exists():
                self.read_model_replacement(asset_id, binding)
            else:
                atomic_write(path, content)
            self.model_overrides[asset_id] = binding
        else:
            self.model_overrides.pop(asset_id, None)
        self.undo_stack.append({'target':'model_overrides','asset_id':asset_id,'before':before,'after':deepcopy(binding)})
        self.redo_stack.clear()

    def command(self, command: dict) -> None:
        # Retained animation assignments must survive appearance/template changes
        # as coherent same-model bindings. Reject the whole change on conflict.
        changing_appearance = command.get('type') in {
            'set_actor_appearance', 'clear_actor_appearance', 'set_actor_group_appearance',
            'apply_actor_template', 'apply_actor_preset_batch',
            'revert_actor_group_component', 'revert_authored_component'}
        changing_allocated = changing_appearance or command.get('type') in {'set_animation_record_active','allocate_animation_record'}
        if ((changing_appearance and any('ActorAnimation' in value for value in self.overrides.values())) or
                (changing_allocated and any('ActorAllocatedAnimation' in value for value in self.overrides.values()))):
            before = deepcopy((self.overrides, self.undo_stack, self.redo_stack))
            try:
                self._command(command)
                from .actor_animation import validate
                for identifier, components in self.overrides.items():
                    if 'ActorAnimation' in components:
                        validate(self, identifier, components['ActorAnimation'], verify_disc=True)
                    if 'ActorAllocatedAnimation' in components:
                        from .allocated_animation_assignment import validate_binding
                        validate_binding(self,identifier,components['ActorAllocatedAnimation'],verify_disc=True)
            except Exception:
                self.overrides, self.undo_stack, self.redo_stack = before
                raise
            return
        self._command(command)

    def _command(self, command: dict) -> None:
        if command.get('type')=='edit_animation_record':
            from .animation_record_edit import apply
            apply(self,command)
            return
        if self.mode != "edit":
            raise ProjectError("Authoring commands require Edit mode")
        if command.get('type') == 'allocate_animation_record':
            from .animation_allocation import apply_command
            apply_command(self,command)
            return
        if command.get('type') == 'set_animation_record_active':
            from .animation_allocation import apply_activation_command
            apply_activation_command(self,command)
            return
        if command.get('type') == 'set_actor_animation':
            from .actor_animation import apply
            apply(self, command)
            return
        if command.get('type') == 'set_actor_allocated_animation':
            from .allocated_animation_assignment import apply
            apply(self,command)
            return
        if command.get('type') == 'rename_project':
            from .project_settings import rename
            rename(self,command)
            return
        if command.get('type') == 'set_branch':
            from .script_branches import apply
            apply(self, command)
            return
        if command.get('type') == 'set_worldmap_menu':
            from .worldmap_authoring import apply
            apply(self, command)
            return
        if command.get('type') == 'set_worldmap_placement':
            from .worldmap_placements import apply
            apply(self, command)
            return
        if command.get('type') == 'import_script_operand_bundle':
            from .script_operand_bundle import apply
            apply(self,command)
            return
        if command.get('type') == 'import_script_operands':
            from .script_operand_files import apply
            apply(self,command)
            return
        if command.get('type') == 'apply_actor_preset_batch':
            from .preset_batch import apply
            apply(self, command)
            return
        from .scene_views import COMMANDS as view_commands, command as view_command
        if isinstance(command.get('type'), str) and command.get('type') in view_commands:
            view_command(self, command)
            return
        from .scene_selection_sets import COMMANDS as scene_selection_commands, command as scene_selection_command
        if isinstance(command.get('type'),str) and command.get('type') in scene_selection_commands:
            scene_selection_command(self,command)
            return
        from .selection_sets import COMMANDS as selection_commands, command as selection_command
        if isinstance(command.get('type'), str) and command.get('type') in selection_commands:
            selection_command(self, command)
            return
        if command.get('type') == 'offset_actor_placements':
            if set(command) != {'type', 'scene_id', 'actor_ids', 'delta', 'review_key'}:
                raise ProjectError('Actor group offset requires scene, actors, delta and reviewed identity only')
            report = self.actor_placement_batch(command['actor_ids'], command['delta'])
            if command['scene_id'] != report['scene_id'] or command['review_key'] != report['review_key']:
                raise ProjectError('Actor placement group changed since preview; preview it again')
            before, after = {}, {}
            for row in report['targets']:
                identifier = row['entity_id']
                before[identifier] = deepcopy(self.overrides.get(identifier))
                value = deepcopy(before[identifier] or {})
                for axis, delta in command['delta'].items():
                    if delta:
                        value.setdefault('Transform', {}).setdefault('position', {})[axis] = row['proposed'][axis]
                after[identifier] = value or None
            if before == after:
                return
            for identifier, value in after.items():
                if value is None:
                    self.overrides.pop(identifier, None)
                else:
                    self.overrides[identifier] = value
            self.undo_stack.append({'target': 'entity_overrides', 'entity_ids': sorted(before),
                                    'before': before, 'after': deepcopy(after)})
            self.redo_stack.clear()
            return
        if command.get('type') == 'layout_actor_placements':
            if set(command) != {'type', 'scene_id', 'actor_ids', 'layout', 'review_key'}:
                raise ProjectError('Group layout requires scene, actors, layout and reviewed identity only')
            report = self.actor_placement_layout(command['actor_ids'], command['layout'])
            if command['scene_id'] != report['scene_id'] or command['review_key'] != report['review_key']:
                raise ProjectError('Actor placement group changed since preview; preview it again')
            axis = report['layout']['axis']
            before, after = {}, {}
            for row in report['targets']:
                if row['proposed'][axis] == row['effective'][axis]:
                    continue
                identifier = row['entity_id']
                before[identifier] = deepcopy(self.overrides.get(identifier))
                value = deepcopy(before[identifier] or {})
                value.setdefault('Transform', {}).setdefault('position', {})[axis] = row['proposed'][axis]
                after[identifier] = value
            if not before:
                return
            self.overrides.update(after)
            self.undo_stack.append({'target': 'entity_overrides', 'entity_ids': sorted(before),
                                    'before': before, 'after': deepcopy(after)})
            self.redo_stack.clear()
            return
        if command.get('type') == 'set_actor_group_appearance':
            if set(command) != {'type', 'scene_id', 'actor_ids', 'donor_entity_id', 'review_key'}:
                raise ProjectError('Group appearance accepts scene, actors, donor and reviewed identity only')
            if not isinstance(command['donor_entity_id'], str) or not command['donor_entity_id']:
                raise ProjectError('Choose a compatible group appearance donor')
            report = self.actor_appearance_batch(command['actor_ids'], command['donor_entity_id'])
            if command['scene_id'] != report['scene_id'] or command['review_key'] != report['review_key']:
                raise ProjectError('Group appearance changed since review; preview it again')
            before, after = {}, {}
            for row in report['targets']:
                identifier = row['entity_id']
                old = deepcopy(self.overrides.get(identifier))
                value = deepcopy(old or {})
                value['ActorAppearance'] = deepcopy(row['proposed'])
                if old != value:
                    before[identifier], after[identifier] = old, value
            if not before:
                return
            self.overrides.update(after)
            self.undo_stack.append({'target': 'entity_overrides', 'entity_ids': sorted(before),
                                    'before': before, 'after': deepcopy(after)})
            self.redo_stack.clear()
            return
        if command.get('type') == 'revert_actor_group_component':
            if set(command) != {'type', 'scene_id', 'actor_ids', 'component', 'review_key'}:
                raise ProjectError('Group component revert accepts scene, actors, component and review identity only')
            report = self.actor_component_batch(command['actor_ids'], command['component'])
            if command['scene_id'] != report['scene_id'] or command['review_key'] != report['review_key']:
                raise ProjectError('Actor group component changed since review; review it again')
            before, after = {}, {}
            for row in report['targets']:
                if not row['has_authored']:
                    continue
                identifier = row['entity_id']
                before[identifier] = deepcopy(self.overrides[identifier])
                after[identifier] = deepcopy(before[identifier])
                del after[identifier][command['component']]
                after[identifier] = after[identifier] or None
            if not before:
                return
            for identifier, value in after.items():
                if value is None:
                    self.overrides.pop(identifier, None)
                else:
                    self.overrides[identifier] = value
            self.undo_stack.append({'target': 'entity_overrides', 'entity_ids': sorted(before),
                                    'before': before, 'after': deepcopy(after)})
            self.redo_stack.clear()
            return
        if command.get('type') == 'revert_authored_component':
            if set(command) != {'type', 'entity_id', 'component', 'review_key'}:
                raise ProjectError('Component revert accepts only owner, component and review identity')
            identifier, component, key = command['entity_id'], command['component'], command['review_key']
            if (not isinstance(identifier, str) or not isinstance(component, str) or
                    component not in self.REVIEW_COMPONENTS or not isinstance(key, str)):
                raise ProjectError('Choose a supported authored component and review identity')
            reviews = {row['component']: row for row in self.component_reviews(identifier)}
            if component not in reviews or reviews[component]['review_key'] != key:
                raise ProjectError('Authored component changed since review; reopen its asset details')
            before = deepcopy(self.overrides[identifier])
            after = deepcopy(before)
            del after[component]
            if after:
                self.overrides[identifier] = after
            else:
                del self.overrides[identifier]
            self.undo_stack.append({'entity_id': identifier, 'before': before, 'after': after or None})
            self.redo_stack.clear()
            return
        if command.get('type') == 'repeat_actor_draft':
            from .draft_repeat import apply as apply_draft_repeat
            apply_draft_repeat(self,command)
            return
        if command.get('type') in ('rename_actor_draft', 'duplicate_actor_draft'):
            identifier=command.get('entity_id')
            if set(command)!={'type','entity_id','name'} or not isinstance(identifier,str) or identifier not in self.actor_drafts:
                raise ProjectError('Draft action requires an existing identity and name')
            before=deepcopy(self.actor_drafts[identifier])
            after={**before,'name':command['name']}
            duplicating=command['type']=='duplicate_actor_draft'
            if duplicating:
                if len(self.actor_drafts)>=128:
                    raise ProjectError('Actor draft limit reached')
                identifier='authored-actor://'+str(uuid.uuid4())
            self._validate_actor_draft(identifier,after)
            if duplicating or before!=after:
                self.actor_drafts[identifier]=after
                self.undo_stack.append({'target':'actor_drafts','entity_id':identifier,
                                       'before':None if duplicating else before,'after':deepcopy(after)})
                self.redo_stack.clear()
            return
        if command.get('type') == 'create_actor_draft':
            if set(command) != {'type', 'donor_entity_id', 'position', 'name'}:
                raise ProjectError('Actor draft requires donor, position and name')
            identifier = 'authored-actor://'+str(uuid.uuid4())
            draft = {'scene_id': self.active_scene, 'donor_entity_id': command['donor_entity_id'],
                     'position': deepcopy(command['position']), 'name': command['name']}
            self._validate_actor_draft(identifier, draft)
            if len(self.actor_drafts) >= 128:
                raise ProjectError('Actor draft limit reached')
            self.actor_drafts[identifier] = draft
            self.undo_stack.append({'target':'actor_drafts','entity_id':identifier,'before':None,'after':deepcopy(draft)})
            self.redo_stack.clear()
            return
        if command.get('type') in ('set_actor_draft_position','set_actor_draft_donor'):
            identifier = command.get('entity_id')
            field='position' if command['type']=='set_actor_draft_position' else 'donor_entity_id'
            if set(command) != {'type','entity_id',field} or not isinstance(identifier,str) or identifier not in self.actor_drafts:
                raise ProjectError('Draft edit requires an existing authored identity and '+field)
            before = deepcopy(self.actor_drafts[identifier])
            after = {**before, field: deepcopy(command[field])}
            self._validate_actor_draft(identifier,after)
            if before != after:
                self.actor_drafts[identifier] = after
                self.undo_stack.append({'target':'actor_drafts','entity_id':identifier,'before':before,'after':deepcopy(after)})
                self.redo_stack.clear()
            return
        if command.get('type') == 'delete_actor_draft':
            if set(command) != {'type','entity_id'} or command['entity_id'] not in self.actor_drafts:
                raise ProjectError('Delete actor draft requires an existing authored identity')
            identifier = command['entity_id']
            before = self.actor_drafts.pop(identifier)
            self.undo_stack.append({'target':'actor_drafts','entity_id':identifier,'before':before,'after':None})
            self.redo_stack.clear()
            return
        if command.get('type') == 'clear_model_replacement':
            if set(command) != {'type','asset_id'} or not isinstance(command['asset_id'],str):
                raise ProjectError('Clear model shape requires asset_id only')
            identifier = command['asset_id']
            before = deepcopy(self.model_overrides.pop(identifier, None))
            if before is not None:
                self.undo_stack.append({'target':'model_overrides','asset_id':identifier,'before':before,'after':None})
                self.redo_stack.clear()
            return
        if command.get('type')=='apply_scene_placement_group':
            from .scene_placement_group import apply
            apply(self,command)
            return
        if command.get('type')=='apply_environment_layout':
            from .environment_layout import apply
            apply(self,command)
            return
        if command.get('type')=='apply_environment_rotation_group':
            from .environment_rotation_group import apply
            apply(self,command)
            return
        if command.get('type')=='apply_environment_group':
            from .environment_group import apply
            apply(self,command)
            return
        if command.get('type')=='apply_collision_rectangle':
            from .collision_rectangle import apply
            apply(self,command)
            return
        if command.get('type') == 'apply_region_bounds':
            from .region_bounds import apply
            apply(self, command)
            return
        if command.get('type') in ('set_region_bounds', 'clear_region_bounds'):
            setting = command['type'] == 'set_region_bounds'
            if set(command) != ({'type', 'entity_id', 'value'} if setting else {'type', 'entity_id'}):
                raise ProjectError('Region bounds commands accept only scene identity and corner override')
            identifier = command['entity_id']
            if not isinstance(identifier, str) or identifier not in self.imports or identifier != self.active_scene:
                raise ProjectError('Region bounds require the active imported scene')
            before = deepcopy(self.overrides.get(identifier))
            after = deepcopy(before or {})
            value = self._validate_region_bounds(identifier, deepcopy(command['value'])) if setting else None
            if value is not None:
                after['RegionBounds'] = value
            else:
                after.pop('RegionBounds', None)
            after = after or None
            if before != after:
                if after is None:
                    self.overrides.pop(identifier, None)
                else:
                    self.overrides[identifier] = after
                self.undo_stack.append({'entity_id': identifier, 'before': before, 'after': deepcopy(after)})
                self.redo_stack.clear()
            return
        if command.get('type') == 'apply_trigger_cells':
            from .trigger_cells import apply
            apply(self, command)
            return
        if command.get('type') in ('set_trigger_cells', 'clear_trigger_cells'):
            setting = command['type'] == 'set_trigger_cells'
            if set(command) != ({'type', 'entity_id', 'value'} if setting else {'type', 'entity_id'}):
                raise ProjectError('Trigger cells commands accept only scene identity and cell override')
            identifier = command['entity_id']
            if not isinstance(identifier, str) or identifier not in self.imports or identifier != self.active_scene:
                raise ProjectError('Trigger cells require the active imported scene')
            before = deepcopy(self.overrides.get(identifier))
            after = deepcopy(before or {})
            value = self._validate_trigger_cells(identifier, deepcopy(command['value'])) if setting else None
            if value is not None:
                after['TriggerCells'] = value
            else:
                after.pop('TriggerCells', None)
            after = after or None
            if before != after:
                if after is None:
                    self.overrides.pop(identifier, None)
                else:
                    self.overrides[identifier] = after
                self.undo_stack.append({'entity_id': identifier, 'before': before, 'after': deepcopy(after)})
                self.redo_stack.clear()
            return
        if command.get("type") in ("set_collision_walls", "clear_collision_walls"):
            setting = command["type"] == "set_collision_walls"
            if set(command) != ({"type", "entity_id", "value"} if setting else {"type", "entity_id"}):
                raise ProjectError("Collision commands accept only scene identity and wall override")
            identifier = command["entity_id"]
            if not isinstance(identifier, str) or identifier not in self.imports:
                raise ProjectError("Collision owner must be an imported scene")
            before = deepcopy(self.overrides.get(identifier))
            after = deepcopy(before or {})
            if setting:
                value = deepcopy(command["value"])
                self._validate_collision(identifier, value)
                after["Collision"] = value
            else:
                after.pop("Collision", None)
            after = after or None
            if before != after:
                if after is None:
                    self.overrides.pop(identifier, None)
                else:
                    self.overrides[identifier] = after
                self.undo_stack.append({"entity_id": identifier, "before": before, "after": deepcopy(after)})
                self.redo_stack.clear()
            return
        if command.get("type") in ("set_animation_channels", "clear_animation_channels"):
            allowed = {"type", "entity_id", "value"} if command["type"] == "set_animation_channels" else {"type", "entity_id"}
            if set(command) != allowed:
                raise ProjectError("Animation commands accept only an actor identity and channel override")
            identifier = command.get("entity_id")
            if not isinstance(identifier, str) or not identifier.strip():
                raise ProjectError("Animation commands require a nonempty actor identity")
            self._actor(identifier)
            before = deepcopy(self.overrides.get(identifier))
            after = deepcopy(before or {})
            if command["type"] == "set_animation_channels":
                value = deepcopy(command.get("value"))
                self._validate_animation_override(identifier, value)
                after["AnimationChannels"] = value
            else:
                after.pop("AnimationChannels", None)
            after = after or None
            if before != after:
                if after is None:
                    self.overrides.pop(identifier, None)
                else:
                    self.overrides[identifier] = after
                self.undo_stack.append({"entity_id": identifier, "before": before, "after": deepcopy(after)})
                self.redo_stack.clear()
            return
        if command.get("type") in ("set_environment_transforms", "clear_environment_transforms"):
            identifier = command.get("entity_id")
            if identifier not in self.imports:
                raise ProjectError("Environment owner must be an imported scene")
            before = deepcopy(self.overrides.get(identifier))
            after = deepcopy(before or {})
            if command["type"] == "set_environment_transforms":
                from importer.environment_authoring import patch_environment_overrides
                value = deepcopy(command.get("value"))
                self._validate_environment(identifier, value)
                patch_environment_overrides(self._environment_source(identifier), value)
                after["Environment"] = value
            else:
                after.pop("Environment", None)
            after = after or None
            if before != after:
                if after is None:
                    self.overrides.pop(identifier, None)
                else:
                    self.overrides[identifier] = after
                self.undo_stack.append({"entity_id": identifier, "before": before, "after": deepcopy(after)})
                self.redo_stack.clear()
            return
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
        if command.get("type") == "set_transition_arrival":
            from importer.transition_authoring import encode_transition_arrival
            identifier, key = command.get("entity_id"), command.get("transition_id")
            self._validate_transitions(identifier, {"entries": {key: {"entry_x_encoded": 0}}})
            options = self.transition_options(identifier)
            entry = next((e for e in options["transitions"] if e["semantic_id"] == key), None)
            if entry is None:
                raise ProjectError("Arrival requires a verified transition entry")
            values = encode_transition_arrival(command.get("arrival"), entry["effective_values"])
            self.command({"type": "set_transition_entry", "entity_id": identifier,
                          "transition_id": key, "values": values})
            return
        if command.get("type") in ("set_movement_target", "clear_movement_target"):
            identifier, key = command.get("entity_id"), command.get("movement_id")
            # Clear also checks owner syntax, but remains possible offline.
            self._validate_movements(identifier, {"entries": {key: {"x": 64}}})
            before = deepcopy(self.overrides.get(identifier))
            after = deepcopy(before or {})
            entries = deepcopy(after.get("ScriptMovement", {}).get("entries", {}))
            if command["type"] == "set_movement_target":
                entries[key] = deepcopy(command.get("values"))
                self._validate_movements(identifier, {"entries": entries})
                self._movement_context(identifier).patch(entries)
            else:
                entries.pop(key, None)
            if entries:
                after["ScriptMovement"] = {"entries": entries}
            else:
                after.pop("ScriptMovement", None)
            after = after or None
            if before != after:
                if after is None:
                    self.overrides.pop(identifier, None)
                else:
                    self.overrides[identifier] = after
                self.undo_stack.append({"entity_id": identifier, "before": before, "after": deepcopy(after)})
                self.redo_stack.clear()
            return
        if command.get('type') in ('set_facing_target', 'clear_facing_target'):
            required = {'type', 'entity_id', 'facing_id'} | ({'values'} if command['type'] == 'set_facing_target' else set())
            if set(command) != required:
                raise ProjectError('Facing commands require only owner, instruction identity and sector')
            identifier, key = command.get('entity_id'), command.get('facing_id')
            self._validate_facing(identifier, {'entries': {key: {'sector': 0}}})
            before = deepcopy(self.overrides.get(identifier))
            after = deepcopy(before or {})
            entries = deepcopy(after.get('ScriptFacing', {}).get('entries', {}))
            if command['type'] == 'set_facing_target':
                entries[key] = deepcopy(command.get('values'))
                self._validate_facing(identifier, {'entries': entries})
                self._facing_context(identifier).patch(entries)
            else:
                entries.pop(key, None)
            if entries:
                after['ScriptFacing'] = {'entries': entries}
            else:
                after.pop('ScriptFacing', None)
            after = after or None
            if before != after:
                if after is None:
                    self.overrides.pop(identifier, None)
                else:
                    self.overrides[identifier] = after
                self.undo_stack.append({'entity_id': identifier, 'before': before, 'after': deepcopy(after)})
                self.redo_stack.clear()
            return
        if command.get("type") in ("set_flag_bit", "clear_flag_bit"):
            identifier, key = command.get("entity_id"), command.get("flag_id")
            # Clear also checks owner syntax, but remains possible offline.
            self._validate_flags(identifier, {"entries": {key: {"bit": 0}}})
            before = deepcopy(self.overrides.get(identifier))
            after = deepcopy(before or {})
            entries = deepcopy(after.get("ScriptFlags", {}).get("entries", {}))
            if command["type"] == "set_flag_bit":
                entries[key] = deepcopy(command.get("values"))
                self._validate_flags(identifier, {"entries": entries})
                self._flag_context(identifier).patch(entries)
            else:
                entries.pop(key, None)
            if entries:
                after["ScriptFlags"] = {"entries": entries}
            else:
                after.pop("ScriptFlags", None)
            after = after or None
            if before != after:
                if after is None:
                    self.overrides.pop(identifier, None)
                else:
                    self.overrides[identifier] = after
                self.undo_stack.append({"entity_id": identifier, "before": before, "after": deepcopy(after)})
                self.redo_stack.clear()
            return
        if command.get("type") in ("set_wait_target", "clear_wait_target"):
            identifier, key = command.get("entity_id"), command.get("wait_id")
            # Clear also checks owner syntax, but remains possible offline.
            self._validate_waits(identifier, {"entries": {key: {"duration_ticks": 0}}})
            before = deepcopy(self.overrides.get(identifier))
            after = deepcopy(before or {})
            entries = deepcopy(after.get("ScriptWaits", {}).get("entries", {}))
            if command["type"] == "set_wait_target":
                entries[key] = deepcopy(command.get("values"))
                self._validate_waits(identifier, {"entries": entries})
                self._wait_context(identifier).patch(entries)
            else:
                entries.pop(key, None)
            if entries:
                after["ScriptWaits"] = {"entries": entries}
            else:
                after.pop("ScriptWaits", None)
            after = after or None
            if before != after:
                if after is None:
                    self.overrides.pop(identifier, None)
                else:
                    self.overrides[identifier] = after
                self.undo_stack.append({"entity_id": identifier, "before": before, "after": deepcopy(after)})
                self.redo_stack.clear()
            return
        if command.get("type") in ("set_model_selector_target", "clear_model_selector_target"):
            identifier, key = command.get("entity_id"), command.get("model_selector_id")
            # Clear also checks owner syntax, but remains possible offline.
            self._validate_model_selectors(identifier, {"entries": {key: {"model_selector_signed": 0}}})
            before = deepcopy(self.overrides.get(identifier))
            after = deepcopy(before or {})
            entries = deepcopy(after.get("ScriptModelSelectors", {}).get("entries", {}))
            if command["type"] == "set_model_selector_target":
                entries[key] = deepcopy(command.get("values"))
                self._validate_model_selectors(identifier, {"entries": entries})
                self._model_selector_context(identifier).patch(entries)
            else:
                entries.pop(key, None)
            if entries:
                after["ScriptModelSelectors"] = {"entries": entries}
            else:
                after.pop("ScriptModelSelectors", None)
            after = after or None
            if before != after:
                if after is None:
                    self.overrides.pop(identifier, None)
                else:
                    self.overrides[identifier] = after
                self.undo_stack.append({"entity_id": identifier, "before": before, "after": deepcopy(after)})
                self.redo_stack.clear()
            return
        if command.get("type") in ("set_transition_entry", "clear_transition_entry"):
            identifier, key = command.get("entity_id"), command.get("transition_id")
            # Clear also checks owner syntax, but remains possible offline.
            self._validate_transitions(identifier, {"entries": {key: {"entry_x_encoded": 0}}})
            before = deepcopy(self.overrides.get(identifier))
            after = deepcopy(before or {})
            entries = deepcopy(after.get("Transitions", {}).get("entries", {}))
            if command["type"] == "set_transition_entry":
                entries[key] = deepcopy(command.get("values"))
                self._validate_transitions(identifier, {"entries": entries})
                self._transition_context(identifier).patch(entries)
            else:
                entries.pop(key, None)
            if entries:
                after["Transitions"] = {"entries": entries}
            else:
                after.pop("Transitions", None)
            after = after or None
            if before != after:
                if after is None:
                    self.overrides.pop(identifier, None)
                else:
                    self.overrides[identifier] = after
                self.undo_stack.append({"entity_id": identifier, "before": before, "after": deepcopy(after)})
                self.redo_stack.clear()
            return
        if command.get("type") in ("set_dialogue_text", "clear_dialogue_text"):
            from importer.dialogue_authoring import validate_run_id
            identifier, run_id = command.get("entity_id"), command.get("run_id")
            self._dialogue_document(identifier)
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
        if command.get('type')=='import_actor_template':
            from .template_files import apply
            apply(self,command)
            return
        if command.get("type") in ("create_actor_template", "apply_actor_template", "delete_actor_template", "rename_actor_template"):
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
        if template["id"] != identifier or template["scope"] not in ("authored-position-v1", "authored-appearance-v1", "authored-actor-preset-v1", "authored-actor-preset-v2"):
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
        scopes = {'authored-position-v1': {'Transform'}, 'authored-appearance-v1': {'ActorAppearance'},
                  'authored-actor-preset-v1': {'Transform', 'ActorAppearance'}}
        if template['scope'] == 'authored-actor-preset-v2':
            if (not isinstance(components, dict) or 'ActorAnimation' not in components or
                    set(components) - {'Transform', 'ActorAppearance', 'ActorAnimation'}):
                raise ProjectError('Animation presets require a captured clip and optional position/appearance')
        elif not isinstance(components, dict) or set(components) != scopes[template['scope']]:
            raise ProjectError('Template components differ from their versioned scope')
        if 'ActorAppearance' in components:
            document, _, _ = self._appearance_binding(source["entity_id"], components["ActorAppearance"])
            if document["scene"]["semantic_id"] != source["scene_id"]:
                raise ProjectError("Appearance template source scene does not match its actor")
        if 'Transform' in components:
            if not isinstance(components['Transform'], dict) or set(components['Transform']) != {'position'}:
                raise ProjectError('Template Transform supports authored position axes only')
            self._validate_position(components['Transform']['position'])
        if 'ActorAnimation' in components:
            from .preset_animation import validate_frozen
            validate_frozen(self, template)

    def template_application(self, template: dict, entity_id: str | None) -> dict:
        """Cheap selected-actor eligibility; Apply still verifies the retail source."""
        result = {"available": False, "verification": "project_structure_only"}
        if self.mode != "edit":
            return {**result, "reason": "Switch to Edit mode to apply a preset"}
        if not entity_id:
            return {**result, "reason": "Select an imported actor to apply this preset"}
        try:
            self._actor(entity_id)
            from .preset_animation import compose
            compose(self, entity_id, template['components'])
        except ProjectError as exc:
            return {**result, "reason": str(exc)}
        return {**result, "available": True, "reason":
                "Appearance/initial clip source and compatibility will be verified on Apply" if {'ActorAppearance','ActorAnimation'} & template['components'].keys()
                else "Applies the saved absolute position axes; other axes stay unchanged"}

    def _template_command(self, command: dict) -> None:
        kind = command["type"]
        if kind == "create_actor_template":
            entity_id = command.get("entity_id")
            self._actor(entity_id)
            name = command.get("name")
            if not isinstance(name, str):
                raise ProjectError("Template name must be a string")
            if len(self.actor_templates) >= 128:
                raise ProjectError("Project supports at most 128 authored actor templates")
            if any(value["name"].casefold() == name.strip().casefold() for value in self.actor_templates.values()):
                raise ProjectError("An authored template already uses that name")
            capture = command.get("capture", "position")
            if capture not in ("position", "appearance", "combined", "animation", "animated"):
                raise ProjectError("Template capture must be position, appearance, combined, animation or animated")
            position = self.overrides.get(entity_id, {}).get("Transform", {}).get("position", {})
            appearance = self.overrides.get(entity_id, {}).get("ActorAppearance")
            animation = self.overrides.get(entity_id, {}).get('ActorAnimation')
            if capture in ("appearance","combined") and not appearance:
                raise ProjectError("Author an appearance override before creating an appearance template")
            if capture in ("position","combined") and not position:
                raise ProjectError("Author one or more position axes before creating a template")
            if capture in ('animation','animated') and not animation:
                raise ProjectError('Author an initial animation assignment before capturing an animation preset')
            scene_id, document = next((key, value) for key, value in self.imports.items()
                                      if any(actor["semantic_id"] == entity_id for actor in value["actors"]))
            identifier = "template://" + str(uuid.uuid4())
            template = {"id": identifier, "name": name.strip(), "scope": "authored-actor-preset-v2" if capture in ('animation','animated') else "authored-actor-preset-v1" if capture=="combined" else "authored-appearance-v1" if capture == "appearance" else "authored-position-v1",
                        "source": {"disc_identity": document["source"]["disc_identity"], "scene_id": scene_id, "entity_id": entity_id},
                        "components": {"Transform":{"position":deepcopy(position)},"ActorAppearance":deepcopy(appearance)} if capture=="combined" else {"ActorAppearance": deepcopy(appearance)} if capture == "appearance" else {"Transform": {"position": deepcopy(position)}}}
            if capture in ('animation','animated'):
                template['components'] = {'ActorAnimation': deepcopy(animation)}
                if capture == 'animated':
                    if position: template['components']['Transform'] = {'position': deepcopy(position)}
                    if appearance: template['components']['ActorAppearance'] = deepcopy(appearance)
            self._validate_template(identifier, template)
            if capture in ('animation','animated'):
                from .actor_animation import validate
                from .preset_animation import validate_frozen
                validate(self, entity_id, animation, verify_disc=True)
                validate_frozen(self, template, verify_disc=True)
            self.actor_templates[identifier] = template
            self.undo_stack.append({"target": "actor_templates", "template_id": identifier, "entity_id": entity_id,
                                    "before": None, "after": deepcopy(template)})
            self.redo_stack.clear()
            return
        identifier = command.get("template_id")
        if not isinstance(identifier, str) or identifier not in self.actor_templates:
            raise ProjectError("Unknown authored actor template")
        template = self.actor_templates[identifier]
        self._validate_template(identifier, template)
        if kind == "rename_actor_template":
            name = command.get("name")
            if not isinstance(name, str):
                raise ProjectError("Template name must be a string")
            name = name.strip()
            if any(key != identifier and value["name"].casefold() == name.casefold()
                   for key, value in self.actor_templates.items()):
                raise ProjectError("An authored template already uses that name")
            renamed = {**deepcopy(template), "name": name}
            self._validate_template(identifier, renamed)
            if renamed == template:
                return
            self.actor_templates[identifier] = renamed
            self.undo_stack.append({"target": "actor_templates", "template_id": identifier,
                                    "entity_id": template["source"]["entity_id"],
                                    "before": deepcopy(template), "after": deepcopy(renamed)})
            self.redo_stack.clear()
            return
        if kind == "apply_actor_template":
            if template["scope"] in ('authored-actor-preset-v1','authored-actor-preset-v2'):
                from .actor_presets import apply as apply_actor_preset
                apply_actor_preset(self,command)
                return
            if template["scope"] == "authored-appearance-v1":
                self.command({"type": "set_actor_appearance", "entity_id": command.get("entity_id"),
                              "donor_entity_id": template["components"]["ActorAppearance"]["donor_entity_id"]})
                return
            # All currently imported actors expose the same project Transform schema.
            # This merges absolute authored axes; it never instantiates native actors.
            self.command({"type": "set_transform", "entity_id": command.get("entity_id"),
                          "position": deepcopy(template["components"]["Transform"]["position"])})
        else:
            self.actor_templates.pop(identifier)
            self.undo_stack.append({"target": "actor_templates", "template_id": identifier,
                                    "entity_id": template["source"]["entity_id"], "before": deepcopy(template), "after": None})
            self.redo_stack.clear()

    def _validate_actor_draft(self, identifier: str, draft: dict) -> None:
        from importer.serialization import encode_placement_coordinate
        if not isinstance(identifier, str) or not identifier.startswith('authored-actor://'):
            raise ProjectError('Invalid authored actor identity')
        try:
            if str(uuid.UUID(identifier.removeprefix('authored-actor://'))) != identifier.removeprefix('authored-actor://'):
                raise ValueError()
        except ValueError:
            raise ProjectError('Invalid authored actor UUID') from None
        if not isinstance(draft, dict) or set(draft) != {'scene_id','donor_entity_id','position','name'}:
            raise ProjectError('Invalid actor draft fields')
        if not isinstance(draft['name'],str) or not draft['name'].strip() or len(draft['name']) > 120:
            raise ProjectError('Actor draft name must contain 1 through 120 characters')
        document = self.imports.get(draft['scene_id'])
        if not document or not any(a['semantic_id']==draft['donor_entity_id'] for a in document['actors']):
            raise ProjectError('Actor draft donor must belong to its imported scene')
        if not isinstance(draft['position'],dict) or set(draft['position']) != {'x','z'}:
            raise ProjectError('Actor draft requires exact X/Z placement')
        for axis, value in draft['position'].items():
            encode_placement_coordinate(value, axis)

    def _apply_history(self, source: list, target: list, field: str) -> None:
        if self.mode != "edit":
            raise ProjectError("Undo and redo require Edit mode")
        if not source:
            raise ProjectError("No command to " + ("undo" if field == "before" else "redo"))
        entry = source.pop()
        value = deepcopy(entry[field])
        if entry.get('target') == 'project_name':
            self.name=value
            target.append(entry)
            return
        if entry.get('target') in ('entity_overrides','actor_draft_batch'):
            collection = self.actor_drafts if entry['target']=='actor_draft_batch' else self.overrides
            for identifier, components in value.items():
                if components is None:
                    collection.pop(identifier, None)
                else:
                    collection[identifier] = components
            target.append(entry)
            return
        if entry.get('target') == 'scene_views':
            collection, identifier = self.scene_views, entry['view_id']
        elif entry.get('target') == 'scene_selection_sets':
            collection, identifier = self.scene_selection_sets, entry['selection_set_id']
        elif entry.get('target') == 'actor_selection_sets':
            collection, identifier = self.actor_selection_sets, entry['selection_set_id']
        elif entry.get('target') == 'actor_drafts':
            collection, identifier = self.actor_drafts, entry['entity_id']
        elif entry.get("target") in ("texture_overrides", "model_overrides"):
            collection, identifier = getattr(self, entry['target']), entry["asset_id"]
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
        from .animation_record_ledger import validate as validate_animation_records
        for identifier,components in self.overrides.items():
            if 'AnimationRecords' in components:
                validate_animation_records(self,identifier,components['AnimationRecords'])
            if 'ActorAllocatedAnimation' in components:
                from .allocated_animation_assignment import validate_binding
                validate_binding(self,identifier,components['ActorAllocatedAnimation'])
        for asset_id, binding in self.model_overrides.items():
            self.read_model_replacement(asset_id, binding)
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
        self._mark_saved()
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
            if not isinstance(components, dict) or not components or set(components) - {"Transform", "ActorAppearance", "ActorAnimation", "ActorAllocatedAnimation", "Dialogue", "Transitions", "ScriptMovement", "ScriptFlags", "ScriptWaits", "ScriptModelSelectors", "ScriptFacing", "ScriptBranches", "Environment", "AnimationChannels", "AnimationRecords", "Collision", "RegionBounds", "TriggerCells", "WorldMapMenu", "WorldMapPlacements"}:
                raise ProjectError("Unsupported authored component")
            if 'WorldMapPlacements' in components:
                from .worldmap_placements import validate
                if set(components) != {'WorldMapPlacements'}:
                    raise ProjectError('World placements cannot contain field-actor components')
                validate(result, identifier, components['WorldMapPlacements'])
                result.overrides[identifier] = deepcopy(components)
                continue
            if 'WorldMapMenu' in components:
                if set(components) != {'WorldMapMenu'}:
                    raise ProjectError('Global world-map menu cannot contain field-actor components')
                result._validate_worldmap_menu(identifier, components['WorldMapMenu'])
                result.overrides[identifier] = deepcopy(components)
                continue
            if 'RegionBounds' in components:
                value = result._validate_region_bounds(identifier, components['RegionBounds'])
                if value is not None:
                    result.overrides.setdefault(identifier, {})['RegionBounds'] = value
            if 'TriggerCells' in components:
                value = result._validate_trigger_cells(identifier, components['TriggerCells'])
                if value is not None:
                    result.overrides.setdefault(identifier, {})['TriggerCells'] = value
            if "Collision" in components:
                result._validate_collision(identifier, components["Collision"])
                result.overrides.setdefault(identifier, {})["Collision"] = deepcopy(components["Collision"])
            if 'AnimationRecords' in components:
                from .animation_record_ledger import validate as validate_animation_records
                validate_animation_records(result,identifier,components['AnimationRecords'])
                result.overrides.setdefault(identifier,{})['AnimationRecords'] = deepcopy(components['AnimationRecords'])
            if "AnimationChannels" in components:
                result._validate_animation_override(identifier, components["AnimationChannels"])
                result.overrides.setdefault(identifier, {})["AnimationChannels"] = deepcopy(components["AnimationChannels"])
            if "Environment" in components:
                result._validate_environment(identifier, components["Environment"])
                result.overrides.setdefault(identifier, {})["Environment"] = deepcopy(components["Environment"])
            if "Transform" in components:
                if not isinstance(components["Transform"], dict) or set(components["Transform"]) != {"position"}:
                    raise ProjectError("Unsupported authored transform")
                result.command({"type": "set_transform", "entity_id": identifier,
                                "position": components["Transform"]["position"]})
            if "ActorAppearance" in components:
                # Opening metadata remains possible offline; preview/build reverify wire resources.
                result._appearance_binding(identifier, components["ActorAppearance"])
                result.overrides.setdefault(identifier, {})["ActorAppearance"] = deepcopy(components["ActorAppearance"])
            if 'ActorAnimation' in components:
                from .actor_animation import validate
                validate(result, identifier, components['ActorAnimation'])
                result.overrides.setdefault(identifier, {})['ActorAnimation'] = deepcopy(components['ActorAnimation'])
            if 'ActorAllocatedAnimation' in components:
                # Cross-component checks run after all scene ledgers are loaded;
                # JSON object order is not assignment provenance.
                result.overrides.setdefault(identifier,{})['ActorAllocatedAnimation']=deepcopy(components['ActorAllocatedAnimation'])
            if "Dialogue" in components:
                # Offline opening checks syntax; actual source capacities are verified on edit/build.
                result._validate_dialogue(identifier, components["Dialogue"], allow_legacy_newline=True)
                result.overrides.setdefault(identifier, {})["Dialogue"] = deepcopy(components["Dialogue"])
            if "Transitions" in components:
                result._validate_transitions(identifier, components["Transitions"])
                result.overrides.setdefault(identifier, {})["Transitions"] = deepcopy(components["Transitions"])
            if "ScriptMovement" in components:
                result._validate_movements(identifier, components["ScriptMovement"])
                result.overrides.setdefault(identifier, {})["ScriptMovement"] = deepcopy(components["ScriptMovement"])
            if 'ScriptFacing' in components:
                result._validate_facing(identifier, components['ScriptFacing'])
                result.overrides.setdefault(identifier, {})['ScriptFacing'] = deepcopy(components['ScriptFacing'])
            if 'ScriptBranches' in components:
                result._validate_branches(identifier, components['ScriptBranches'])
                result.overrides.setdefault(identifier, {})['ScriptBranches'] = deepcopy(components['ScriptBranches'])
            if "ScriptFlags" in components:
                result._validate_flags(identifier, components["ScriptFlags"])
                result.overrides.setdefault(identifier, {})["ScriptFlags"] = deepcopy(components["ScriptFlags"])
            if "ScriptWaits" in components:
                result._validate_waits(identifier, components["ScriptWaits"])
                result.overrides.setdefault(identifier, {})["ScriptWaits"] = deepcopy(components["ScriptWaits"])
            if "ScriptModelSelectors" in components:
                result._validate_model_selectors(identifier, components["ScriptModelSelectors"])
                result.overrides.setdefault(identifier, {})["ScriptModelSelectors"] = deepcopy(components["ScriptModelSelectors"])
        drafts = raw.get('actor_drafts', {})
        if not isinstance(drafts,dict) or len(drafts)>128:
            raise ProjectError('Invalid actor draft collection')
        for identifier, draft in drafts.items():
            result._validate_actor_draft(identifier,draft)
        result.actor_drafts = deepcopy(drafts)
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
        from .selection_sets import validate as validate_selection
        selection_sets = raw.get('actor_selection_sets', {})
        if not isinstance(selection_sets, dict) or len(selection_sets) > 128:
            raise ProjectError('Invalid saved actor selection collection')
        selection_names = set()
        for identifier, value in selection_sets.items():
            validate_selection(result, identifier, value)
            name = (value['scene_id'], value['name'].casefold())
            if name in selection_names:
                raise ProjectError('Duplicate saved selection name in scene')
            selection_names.add(name)
        result.actor_selection_sets = deepcopy(selection_sets)
        from .scene_selection_sets import validate as validate_scene_selection
        scene_selections=raw.get('scene_selection_sets',{})
        if not isinstance(scene_selections,dict) or len(scene_selections)>128:
            raise ProjectError('Invalid saved scene selection collection')
        scene_selection_names=set()
        for identifier,value in scene_selections.items():
            validate_scene_selection(result,identifier,value)
            name=(value['scene_id'],value['name'].casefold())
            if name in scene_selection_names:raise ProjectError('Duplicate saved scene selection name in scene')
            scene_selection_names.add(name)
        result.scene_selection_sets=deepcopy(scene_selections)
        from .scene_views import validate as validate_view
        views = raw.get('scene_views', {})
        if not isinstance(views, dict) or len(views) > 128:
            raise ProjectError('Invalid saved scene view collection')
        view_names = set()
        for identifier, value in views.items():
            validate_view(result, identifier, value)
            name = (value['scene_id'], value['name'].casefold())
            if name in view_names:
                raise ProjectError('Duplicate saved scene view name in scene')
            view_names.add(name)
        result.scene_views = deepcopy(views)
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
        models = raw.get('model_overrides', {})
        if not isinstance(models, dict) or len(models) > 128:
            raise ProjectError('Invalid model shape collection')
        for asset_id, binding in models.items():
            result.read_model_replacement(asset_id, binding)
        result.model_overrides = deepcopy(models)
        from .allocated_animation_assignment import validate_binding
        for identifier,components in result.overrides.items():
            if 'ActorAllocatedAnimation' in components:
                validate_binding(result,identifier,components['ActorAllocatedAnimation'])
        if raw.get("active_scene") is not None:
            result.set_scene(raw["active_scene"])
        result.undo_stack.clear()
        result.redo_stack.clear()
        result._mark_saved()
        return result

    def actor_placement_batch(self, actor_ids: list[str], delta: dict) -> dict:
        """Preview every source-grid placement before one atomic group command."""
        from importer.serialization import encode_placement_coordinate
        from importer.core import ImportError
        if (not isinstance(actor_ids, list) or not 2 <= len(actor_ids) <= 128 or
                any(not isinstance(identifier, str) for identifier in actor_ids) or
                len(set(actor_ids)) != len(actor_ids)):
            raise ProjectError('Choose 2 through 128 distinct imported actors in the active scene')
        if (not isinstance(delta, dict) or not delta or set(delta) - {'x', 'z'} or
                any(type(value) is not int or abs(value) > 16320 or value % 64 for value in delta.values())):
            raise ProjectError('Group offsets require X/Z integer multiples of 64, from -16320 through 16320')
        document = self.imports.get(self.active_scene)
        actors = {a['semantic_id']: a for a in document['actors']} if document else {}
        if any(identifier not in actors for identifier in actor_ids):
            raise ProjectError('Every group actor must belong to the active imported scene')
        targets = []
        for identifier in sorted(actor_ids):
            retail = deepcopy(actors[identifier]['imported_transform']['position'])
            authored = deepcopy(self.overrides.get(identifier, {}).get('Transform', {}).get('position', {}))
            effective = {**retail, **authored}
            proposed = dict(effective)
            for axis, offset in delta.items():
                value = effective.get(axis)
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                    raise ProjectError(f'{identifier} has no finite effective {axis.upper()} placement')
                proposed[axis] = value + offset
                try:
                    encode_placement_coordinate(proposed[axis], f'{identifier} proposed {axis.upper()}')
                except ImportError as exc:
                    raise ProjectError(str(exc)) from exc
            targets.append({'entity_id': identifier, 'retail': retail, 'authored': authored,
                            'effective': effective, 'proposed': proposed})
        review_key = digest({'project_root': str(self.root), 'scene_id': self.active_scene,
                             'source_document': digest(document), 'delta': delta,
                             'overrides': {identifier: self.overrides.get(identifier) for identifier in sorted(actor_ids)}})
        return {'schema_version': 'legaia.actor-placement-batch.v1', 'scene_id': self.active_scene,
                'targets': targets, 'delta': deepcopy(delta), 'review_key': review_key,
                'limitations': ['Only imported active-scene actor X/Z placement offsets are supported.',
                                'Proposed coordinates must fit the exact retail 64-unit placement grid.',
                                'Source Y, scripts, scheduling and runtime behavior are not inferred.']}

    def actor_placement_layout(self, actor_ids: list[str], layout: dict) -> dict:
        """Align or evenly distribute existing owners on the exact source grid."""
        if not isinstance(layout, dict) or layout.get('kind') not in ('align', 'distribute') or layout.get('axis') not in ('x', 'z'):
            raise ProjectError('Choose Align or Distribute along X or Z')
        fields = {'kind', 'axis', 'anchor_entity_id'} if layout['kind'] == 'align' else {'kind', 'axis'}
        if set(layout) != fields:
            raise ProjectError('Group layout accepts kind, axis and an alignment anchor only')
        base = self.actor_placement_batch(actor_ids, {'x': 0, 'z': 0})
        axis = layout['axis']
        targets = base['targets']
        if layout['kind'] == 'align':
            anchor = next((row for row in targets if row['entity_id'] == layout['anchor_entity_id']), None)
            if anchor is None:
                raise ProjectError('The alignment anchor must be a selected imported actor')
            for row in targets:
                row['proposed'][axis] = anchor['effective'][axis]
        else:
            ordered = sorted(targets, key=lambda row: (row['effective'][axis], row['entity_id']))
            low, high = int(ordered[0]['effective'][axis] // 64), int(ordered[-1]['effective'][axis] // 64)
            span, intervals = high - low, len(ordered) - 1
            if span < intervals:
                raise ProjectError('Distribution needs at least one 64-unit grid interval per gap')
            # Nearest grid coordinate, ties upward; endpoints stay fixed and
            # adjacent gaps differ by at most one retail grid interval.
            for index, row in enumerate(ordered):
                grid = low + (2 * span * index + intervals) // (2 * intervals)
                row['proposed'][axis] = grid * 64
        changed = sum(row['proposed'][axis] != row['effective'][axis] for row in targets)
        review = digest({'placement_review': base['review_key'], 'layout': layout,
                         'targets': targets, 'algorithm': 'source-grid-layout.v1'})
        return {'schema_version': 'legaia.actor-placement-layout.v1', 'scene_id': base['scene_id'],
                'targets': targets, 'layout': deepcopy(layout), 'changed_count': changed,
                'review_key': review, 'limitations': [
                    'Only source-grid X/Z positions change; height, facing, scripts and visibility are unchanged.',
                    'Distribution preserves coordinate endpoints and stable source-ID order for ties.',
                    'Nearest 64-unit spacing can differ by one grid interval; collision and gameplay are not validated.']}

    def actor_appearance_batch(self, actor_ids: list[str], donor_entity_id: str | None = None) -> dict:
        """Intersect verified initial donor pairs for all selected imported actors."""
        from importer.man_assignments import load_man_assignment_context
        from importer.pipeline import _disc_context, import_scene
        component = self.actor_component_batch(actor_ids, 'ActorAppearance')
        document = self.imports[self.active_scene]
        if not self.disc_path:
            raise ProjectError("Group appearance requires the project's user-owned disc")
        if donor_entity_id is not None and not isinstance(donor_entity_id, str):
            raise ProjectError('Group appearance donor must be an imported actor identity')
        records = {a['source_record']['record_index']: a for a in document['actors']}
        actors = {a['semantic_id']: a for a in document['actors']}
        with _disc_context(self.disc_path):
            if digest(import_scene(self.disc_path, document['scene']['name'])) != digest(document):
                raise ProjectError('Group appearance source differs from freshly verified imported evidence')
            context = load_man_assignment_context(self.disc_path, document['scene']['name'])
            common, support_rows = None, []
            for identifier in sorted(actor_ids):
                support = context.options(actors[identifier]['source_record']['record_index'])
                donors = {records[index]['semantic_id'] for pair in support['pairs'] for index in pair['donor_records']}
                support_rows.append({'entity_id': identifier, 'supported': support['supported'], 'reason': support['reason']})
                common = donors if common is None else common & donors
            options = []
            for donor_id in sorted(common or []):
                try:
                    for identifier in actor_ids:
                        self._appearance_binding(identifier, {'donor_entity_id': donor_id})
                except ProjectError:
                    continue
                donor = actors[donor_id]
                options.append({'donor_entity_id': donor_id, 'asset_id': donor['model_reference']['asset_semantic_id'],
                                'animation_id': donor['placement_fields']['animation_id'],
                                'label': f"Actor {donor['source_record']['record_index']:04d} · shared initial pair"})
            if donor_entity_id is not None and not any(o['donor_entity_id'] == donor_entity_id for o in options):
                raise ProjectError('Donor is not a verified compatible initial pair for every group actor')
            source = context.provenance()
        def pair(actor):
            return {'asset_id': actor['model_reference']['asset_semantic_id'],
                    'animation_id': actor['placement_fields']['animation_id']} if actor else None
        targets = [{**row, 'retail': pair(actors[row['entity_id']]),
                    'effective': pair(actors.get((row['authored'] or {}).get('donor_entity_id', row['entity_id']))),
                    'proposed': {'donor_entity_id': donor_entity_id} if donor_entity_id else None}
                   for row in component['targets']]
        key = digest({'component_review': component['review_key'], 'donor_entity_id': donor_entity_id,
                      'options': options, 'source': source})
        return {'schema_version': 'legaia.actor-appearance-batch.v1', 'scene_id': self.active_scene,
                'donor_entity_id': donor_entity_id, 'options': options, 'targets': targets,
                'support': support_rows, 'source': source, 'review_key': key,
                'changed_count': sum(row['proposed'] is not None and row['authored'] != row['proposed'] for row in targets),
                'limitations': ['Initial model/animation pairs only; object count and source assignment must agree.',
                                'Script scheduling, runtime model pools and gameplay compatibility remain unverified.']}

    def actor_component_batch(self, actor_ids: list[str], component: str) -> dict:
        """Read-only review binds the chosen component on every selected actor."""
        if (not isinstance(actor_ids, list) or not 2 <= len(actor_ids) <= 128 or
                any(not isinstance(identifier, str) for identifier in actor_ids) or
                len(set(actor_ids)) != len(actor_ids)):
            raise ProjectError('Choose 2 through 128 distinct imported actors in the active scene')
        if not isinstance(component, str) or component not in self.REVIEW_COMPONENTS:
            raise ProjectError('Choose a supported authored component')
        document = self.imports.get(self.active_scene)
        actors = {a['semantic_id']: a for a in document['actors']} if document else {}
        if any(identifier not in actors for identifier in actor_ids):
            raise ProjectError('Every group actor must belong to the active imported scene')
        targets = [{'entity_id': identifier,
                    'authored': deepcopy(self.overrides.get(identifier, {}).get(component)),
                    'has_authored': component in self.overrides.get(identifier, {})}
                   for identifier in sorted(actor_ids)]
        key = digest({'project_root': str(self.root), 'source_document_sha256': digest(document),
                      'scene_id': self.active_scene, 'component': component, 'targets': targets})
        return {'schema_version': 'legaia.actor-component-batch.v1', 'scene_id': self.active_scene,
                'component': component, 'targets': targets, 'review_key': key,
                'affected_count': sum(row['has_authored'] for row in targets)}

    def component_reviews(self, identifier: str, *, source_digest: str | None = None) -> list[dict]:
        """Detached authored settings with a source-bound identity for component removal."""
        document = self.imports.get(identifier)
        if document is None:
            document = self._dialogue_document(identifier)
        source_digest = source_digest or digest(document)
        return [{'component': component, 'authored': deepcopy(value),
                 'review_key': digest({'project_root': str(self.root), 'source_document_sha256': source_digest,
                                      'owner_id': identifier, 'component': component, 'authored': value})}
                for component, value in sorted(self.overrides.get(identifier, {}).items())
                if component in self.REVIEW_COMPONENTS]

    def authored_assets(self) -> list[dict]:
        """Project-wide authored references, independent of derived resource caches."""
        records = []
        for identifier, components in sorted(self.overrides.items()):
            if 'WorldMapPlacements' in components:
                binding=components['WorldMapPlacements']
                records.append(dict(id=identifier,kind='worldmap',scene_id=None,source_scene=binding['scene'],
                    name=f"{binding['scene']} source placements",changes=[f"Source transform records: {len(binding['entries'])}"],
                    authored={'WorldMapPlacements':deepcopy(binding)}))
        worldmap = self.overrides.get('worldmap://legaia/menu', {}).get('WorldMapMenu')
        if worldmap:
            records.append(dict(id='worldmap://legaia/menu', kind='worldmap', scene_id=None,
                source_scene='Global menu', name='World-map landmarks',
                changes=[f"Landmark records: {len(worldmap['entries'])} authored rows"],
                authored={'WorldMapMenu': deepcopy(worldmap)}))
        for scene_id, document in sorted(self.imports.items()):
            environment = self.overrides.get(scene_id, {}).get("Environment")
            collision = self.overrides.get(scene_id, {}).get("Collision")
            scene_changes, scene_authored = [], {}
            animation_records = self.overrides.get(scene_id,{}).get('AnimationRecords')
            if animation_records:
                active_count = len(animation_records['records'])-len(animation_records['removed_record_ids'])
                scene_changes.append(f'Allocated animation clips: {active_count} active records; Build relocation pending')
                scene_authored['AnimationRecords'] = deepcopy(animation_records)
            if environment:
                scene_changes.append(f"Scenery transforms: {len(environment.get('edits', []))} shared records, {len(environment.get('instances', []))} individual cells")
                scene_authored["Environment"] = deepcopy(environment)
            if collision:
                scene_changes.append(f"Collision walls: {len(collision['edits'])} authored bits")
                scene_authored["Collision"] = deepcopy(collision)
            region_bounds = self.overrides.get(scene_id, {}).get('RegionBounds')
            if region_bounds:
                scene_changes.append(f"Region bounds: {len(region_bounds['edits'])} authored rectangles")
                scene_authored['RegionBounds'] = deepcopy(region_bounds)
            trigger_cells = self.overrides.get(scene_id, {}).get('TriggerCells')
            if trigger_cells:
                scene_changes.append(f"Trigger cells: {len(trigger_cells['edits'])} authored cells")
                scene_authored['TriggerCells'] = deepcopy(trigger_cells)
            if scene_authored:
                records.append({"id":scene_id, "kind":"scene", "name":document["scene"]["name"],
                                "scene_id":scene_id, "source_scene":document["scene"]["name"],
                                "changes":scene_changes, "authored":scene_authored})
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
                if edits.get('ActorAnimation'):
                    changes.append('Initial animation assignment')
                if edits.get('ActorAllocatedAnimation'):
                    changes.append('Initial allocated animation assignment')
                channels = edits.get("AnimationChannels", {}).get("edits", [])
                if channels:
                    changes.append(f"Animation: {len(channels)} edited channel{'s' if len(channels) != 1 else ''}")
                runs = edits.get("Dialogue", {}).get("runs", {})
                if runs:
                    changes.append(f"Dialogue: {len(runs)} text runs")
                entries = edits.get("Transitions", {}).get("entries", {})
                if entries:
                    changes.append(f"Transitions: {len(entries)} entries")
                facing = edits.get('ScriptFacing', {}).get('entries', {})
                if facing:
                    changes.append(f'Facing operands: {len(facing)} instructions')
                movement = edits.get("ScriptMovement", {}).get("entries", {})
                if movement:
                    changes.append(f"Movement: {len(movement)} targets")
                branches = edits.get('ScriptBranches', {}).get('entries', {})
                if branches:
                    changes.append(f'Branch destinations: {len(branches)} instructions')
                flags = edits.get("ScriptFlags", {}).get("entries", {})
                if flags:
                    changes.append(f"Flags: {len(flags)} operands")
                waits = edits.get("ScriptWaits", {}).get("entries", {})
                if waits:
                    changes.append(f"Waits: {len(waits)} targets")
                selectors = edits.get("ScriptModelSelectors", {}).get("entries", {})
                if selectors:
                    changes.append(f"Model selectors: {len(selectors)} operands")
                records.append({"id": identifier, "kind": "actor", "name": "Actor " + identifier.rsplit("/", 1)[-1],
                                "scene_id": scene_id, "source_scene": document["scene"]["name"],
                                "changes": changes, "authored": deepcopy(edits),
                                "source_record": deepcopy(actor.get("source_record"))})
        for identifier, edits in sorted(self.overrides.items()):
            if "/scripts/man-p2/" not in identifier:
                continue
            scene_id = identifier.split("/scripts/man-p2/", 1)[0]
            runs = edits.get("Dialogue", {}).get("runs", {})
            entries = edits.get("Transitions", {}).get("entries", {})
            changes = ([f"Dialogue: {len(runs)} text runs"] if runs else []) + ([f"Transitions: {len(entries)} entries"] if entries else [])
            facing = edits.get('ScriptFacing', {}).get('entries', {})
            if facing:
                changes.append(f'Facing operands: {len(facing)} instructions')
            movement = edits.get("ScriptMovement", {}).get("entries", {})
            if movement:
                changes.append(f"Movement: {len(movement)} targets")
            branches = edits.get('ScriptBranches', {}).get('entries', {})
            if branches:
                changes.append(f'Branch destinations: {len(branches)} instructions')

            flags = edits.get("ScriptFlags", {}).get("entries", {})
            if flags:
                changes.append(f"Flags: {len(flags)} operands")
            waits = edits.get("ScriptWaits", {}).get("entries", {})
            if waits:
                changes.append(f"Waits: {len(waits)} targets")
            selectors = edits.get("ScriptModelSelectors", {}).get("entries", {})
            if selectors:
                changes.append(f"Model selectors: {len(selectors)} operands")
            if changes:
                records.append({"id": identifier, "kind": "script",
                                "name": "Partition 2 script " + str(int(identifier.rsplit("/", 1)[-1])),
                                "scene_id": scene_id, "source_scene": self.imports[scene_id]["scene"]["name"],
                                "changes": changes, "authored": deepcopy(edits),
                                "script_id": "script://" + identifier.removeprefix("scene://")})
        for identifier, binding in sorted(self.model_overrides.items()):
            scene_id = binding['source_scene_id']
            asset = next(a for a in self.imports[scene_id]['assets']['models'] if a['semantic_id'] == identifier)
            records.append({'id':identifier, 'kind':'model', 'name':'Model shape ' + identifier.rsplit('/',1)[-1],
                            'scene_id':scene_id, 'source_scene':self.imports[scene_id]['scene']['name'],
                            'changes':[{'tmd-face-addition-v1':'TMD count-changing face addition','tmd-face-removal-v1':'TMD count-changing face removal','tmd-content-v3':'TMD normal-reference/content replacement','tmd-content-v2':'TMD material/content replacement','tmd-content-v1':'TMD content replacement'}.get(binding['format'],'TMD shape replacement')], 'authored':deepcopy(binding),
                            'source_record':deepcopy(asset['source_record'])})
        for identifier, binding in sorted(self.texture_overrides.items()):
            scene_id = binding["source_scene_id"]
            records.append({"id": identifier, "kind": "texture", "name": "TIM " + identifier.split("/", 3)[-1].replace("/", " / "),
                            "scene_id": scene_id, "source_scene": self.imports[scene_id]["scene"]["name"],
                            "changes": ["TIM replacement"], "authored": deepcopy(binding)})
        for identifier, draft in sorted(self.actor_drafts.items()):
            scene_id = draft['scene_id']
            records.append({'id': identifier, 'kind': 'actor', 'name': draft['name'],
                            'scene_id': scene_id, 'source_scene': self.imports[scene_id]['scene']['name'],
                            'changes': ['NPC draft', 'Position: X, Z'], 'authored': deepcopy(draft),
                            'draft': True, 'donor_entity_id': draft['donor_entity_id']})
        for identifier, template in sorted(self.actor_templates.items()):
            scene_id = template["source"]["scene_id"]
            records.append({"id": identifier, "kind": "template", "name": template["name"],
                            "scene_id": scene_id, "source_scene": self.imports.get(scene_id, {}).get("scene", {}).get("name", scene_id),
                            "changes": ["Animation preset" if template['scope']=='authored-actor-preset-v2' else
                                        "Appearance template" if template["scope"] == "authored-appearance-v1" else
                                        "Position and appearance preset" if template['scope']=='authored-actor-preset-v1' else
                                        "Position template"], "authored": deepcopy(template)})
        source_digests = {}
        for record in records:
            if record['id'] not in self.overrides or record['scene_id'] is None:
                continue
            scene_id = record['scene_id']
            if scene_id not in source_digests:
                source_digests[scene_id] = digest(self.imports[scene_id])
            record['component_reviews'] = self.component_reviews(record['id'], source_digest=source_digests[scene_id])
        return records

    def model_references(self) -> list[dict]:
        """Project-wide initial assignments, not scripted runtime residency."""
        references = []
        for scene_id, document in self.imports.items():
            for actor in document["actors"]:
                identifier = actor["semantic_id"]
                donor = self.appearance_source_actor(identifier)
                imported = actor["model_reference"].get("asset_semantic_id")
                effective = donor["model_reference"].get("asset_semantic_id")
                for model_id in dict.fromkeys((imported, effective)):
                    if model_id is None:
                        continue
                    references.append({"source_id": identifier, "target_id": model_id,
                                       "scene_id": scene_id, "kind": "initial_model_assignment",
                                       "imported": model_id == imported, "effective": model_id == effective,
                                       "effective_donor_id": donor["semantic_id"] if model_id == effective else None,
                                       "runtime_binding": "not_asserted"})
            actors = {actor['semantic_id']: actor for actor in document['actors']}
            for identifier, draft in self.actor_drafts.items():
                if draft['scene_id'] != scene_id:
                    continue
                # Appended actors clone the retail donor, not its authored appearance.
                donor = actors[draft['donor_entity_id']]
                model_id = donor['model_reference'].get('asset_semantic_id')
                if model_id is not None:
                    references.append({'source_id': identifier, 'source_name': draft['name'],
                                       'target_id': model_id, 'scene_id': scene_id,
                                       'kind': 'draft_initial_model_assignment',
                                       'imported': False, 'effective': True,
                                       'effective_donor_id': donor['semantic_id'],
                                       'runtime_binding': 'not_asserted'})
        return references

    def state(self) -> dict:
        from .scene_views import review_key as view_review_key
        from .scene_selection_sets import review_key as scene_selection_review_key
        from .selection_sets import review_key as selection_review_key
        from .inspector_schema import inspector_schema
        document = self.imports.get(self.active_scene)
        correlation = self._current_correlation()
        entities = []
        for actor in document["actors"] if document else []:
            identifier = actor["semantic_id"]
            imported = deepcopy(actor["imported_transform"])
            authored = deepcopy(self.overrides.get(identifier, {}).get("Transform", {}))
            placement_issues = self._placement_issues(authored)
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
            from .actor_animation import source_actor as animation_source_actor
            animation_actor = animation_source_actor(self, identifier)
            def animation_identity(source):
                number = source['placement_fields'].get('animation_id')
                local = source['model_reference'].get('model_index')
                return {'animation_asset_id': f"animation://{document['scene']['name']}/scene-anm/{number-1:04d}"
                        if type(number) is int and 1 <= number <= 255 and type(local) is int and 0 <= local < 240 else None,
                        'initial_animation_id': number, 'donor_entity_id': source['semantic_id']}
            allocated=self.overrides.get(identifier,{}).get('ActorAllocatedAnimation')
            effective_animation=(dict(animation_asset_id=f"animation://{document['scene']['name']}/authored-record/{allocated['record_id']}",
                initial_animation_id=None,source_kind='allocated_record',record_id=allocated['record_id'])
                if allocated else animation_identity(animation_actor))
            entities.append({"id": identifier, "name": "Actor " + identifier.rsplit("/", 1)[-1],
                             "authored_components": sorted(key for key, value in self.overrides.get(identifier, {}).items() if value),
                             "components": {"Transform": {"imported": imported, "authored": authored, "effective": effective,
                                                           "build_issues": placement_issues},
                                            "ActorAppearance": {"imported": original_pair, "authored": appearance, "effective": effective_pair,
                                                                "limitations": ["Initial model/animation pair only; scripts may replace it. Script and gameplay compatibility remain unverified."]},
                                            "ModelRenderer": {"asset_id": model.get("asset_semantic_id"), "resolution_status": model.get("resolution_status")},
                                            "Animation": {"imported_id": actor["placement_fields"].get("animation_id"), "resolution_status": "unresolved", "authored_channels": deepcopy(self.overrides.get(identifier, {}).get("AnimationChannels"))},
                                            'ActorAnimation': {'imported': animation_identity(actor), 'base': animation_identity(donor),
                                                               'authored': deepcopy(self.overrides.get(identifier, {}).get('ActorAnimation', {})),
                                                               'effective': effective_animation},
                                            'ActorAllocatedAnimation': {'authored':deepcopy(self.overrides.get(identifier,{}).get('ActorAllocatedAnimation')),
                                                'initial_selection':'allocated_record_identity' if self.overrides.get(identifier,{}).get('ActorAllocatedAnimation') else None,
                                                'gameplay_verified':False},
                                            "Dialogue": {"authored": deepcopy(self.overrides.get(identifier, {}).get("Dialogue", {})),
                                                         "limitations": ["Only verified plain-text runs are writable; controls and record boundaries remain fixed. Source capacity is rechecked on edit/build."]},
                                            'ScriptBranches': {'entries': deepcopy(self.overrides.get(identifier, {}).get('ScriptBranches', {}).get('entries', {}))},
                                            'ScriptFacing': {'entries': deepcopy(self.overrides.get(identifier, {}).get('ScriptFacing', {}).get('entries', {}))},
                                            "RuntimeCorrelation": deepcopy(correlation.get("entities", {}).get(identifier, {"status": "unavailable", "binding_confirmed": False, "candidates": [], "reason": correlation.get("reason")})),
                                            "RetailMetadata": {key: deepcopy(actor.get(key)) for key in ("source_record", "claims", "unresolved")}}})
        from .project_settings import view as project_settings
        from .asset_references import source_key as reference_key
        return {"inspector_schema": inspector_schema(), "asset_reference_source_key": reference_key(self), "project_settings": project_settings(self), "project": {"name": self.name, "path": str(self.root), "disc_path": self.disc_path, "dirty": self.dirty, "unsaved_sections": self.unsaved_sections, "mode": self.mode},
                "placement_build_issues": self.placement_build_issues(),
                "scene": {"id": self.active_scene, "name": document["scene"]["name"] if document else None, "entities": entities},
                "scenes": [{"id": key, "name": value["scene"]["name"]} for key, value in self.imports.items()],
                "runtime_correlation": correlation,
                "scene_view_source_key": digest(document) if document else None,
                "scene_views": [{**deepcopy(value), "review_key": view_review_key(self, value)} for value in sorted(self.scene_views.values(), key=lambda item: (item["scene_id"], item["name"].casefold(), item["id"]))],
                "scene_selection_sets": [{**deepcopy(value),'review_key':scene_selection_review_key(self,value)} for value in sorted(self.scene_selection_sets.values(),key=lambda item:(item['scene_id'],item['name'].casefold(),item['id']))],
                "actor_selection_source_key": digest(document) if document else None,
                "actor_selection_sets": [{**deepcopy(value), 'review_key': selection_review_key(self, value)}
                                         for value in sorted(self.actor_selection_sets.values(), key=lambda item: (item['scene_id'], item['name'].casefold(), item['id']))],
                "actor_templates": [{**deepcopy(template), "application": self.template_application(template, self.selected)}
                                    for template in self.actor_templates.values()],
                "assets": deepcopy(list(self.assets.records.values())),
                "model_references": self.model_references(), "selection": {"entity_id": self.selected},
                "texture_overrides": deepcopy(self.texture_overrides),
                "actor_drafts": deepcopy(self.actor_drafts),
                "model_overrides": deepcopy(self.model_overrides),
                "authored_assets": self.authored_assets(),
                "history": {"can_undo": bool(self.undo_stack), "can_redo": bool(self.redo_stack)},
                "diagnostics": ["Scene viewport uses verified model poses where supported and explicit markers otherwise; scripted visibility is not reconstructed.",
                                "Retail Y and initial facing are unresolved; an authored Y is a project value.",
                                "Build supports representable X/Z placements and qualified script-facing operands; authored height and generic Transform rotation are unsupported."],
                "capabilities": {"project_settings": True, "project_navigation": True, "edit_transform": True, "authored_transform_templates": True, "saved_scene_views": True,
                                 "live_mode": False, "build": False, "model_preview": False}}
