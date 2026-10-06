"""Loopback-only editor service. Commands are serialized; no runtime RAM writes."""
from __future__ import annotations

import argparse
import base64
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import socket
import threading
from urllib.parse import urlsplit

from importer.core import ImportError as RetailImportError
from .project import ProjectError, ProjectService


def _slot_conversion_source(body):
    if 'conversion_source' not in body:return None
    source=body['conversion_source']
    if not isinstance(source,dict) or set(source) not in ({'png_base64','stp_png_base64','options'},{'png_base64','stp_png_base64','options','glb_source'}):
        raise ProjectError('Converted slot requires exact PNG/STP source fields')
    def decode(value):
        if not isinstance(value,str) or not 1<=len(value)<=11184812:raise ProjectError('Converted PNG source exceeds eight MiB')
        try:return base64.b64decode(value,validate=True)
        except ValueError as exc:raise ProjectError('Converted PNG source requires valid base64') from exc
    result=dict(png=decode(source['png_base64']),stp=decode(source['stp_png_base64']) if source['stp_png_base64'] is not None else None,options=source['options'])
    if 'glb_source' in source:result['glb_source']=source['glb_source']
    return result


def _transition_authoring_report(project, identifier):
    """Unsupported authoring must not suppress the read-only script report."""
    try:
        return project.transition_options(identifier)
    except (RetailImportError, ProjectError) as exc:
        return {"supported": False, "reason": str(exc), "transitions": [],
                "unresolved_overrides": sorted(project.overrides.get(identifier, {}).get("Transitions", {}).get("entries", {})),
                "limitations": ["Read-only inspection does not establish transition-write safety."]}


def _movement_authoring_report(project, identifier):
    """Unsupported authoring must not suppress the read-only script report."""
    try:
        return project.movement_options(identifier)
    except (RetailImportError, ProjectError) as exc:
        return {"supported": False, "reason": str(exc), "targets": [],
                "unresolved_overrides": sorted(project.overrides.get(identifier, {}).get("ScriptMovement", {}).get("entries", {})),
                "limitations": ["Read-only inspection does not establish movement-write safety."]}


def _facing_authoring_report(project, identifier):
    """Source operand availability never suppresses read-only script inspection."""
    try:
        return project.facing_options(identifier)
    except (RetailImportError, ProjectError) as exc:
        return {'supported': False, 'reason': str(exc), 'targets': [], 'unavailable': [],
                'unresolved_overrides': sorted(project.overrides.get(identifier, {}).get('ScriptFacing', {}).get('entries', {})),
                'limitations': ['No initial or live heading is established by source inspection.']}


def _flag_authoring_report(project, identifier):
    """Unsupported authoring must not suppress the read-only script report."""
    try:
        return project.flag_options(identifier)
    except (RetailImportError, ProjectError) as exc:
        return {"supported": False, "reason": str(exc), "targets": [],
                "unresolved_overrides": sorted(project.overrides.get(identifier, {}).get("ScriptFlags", {}).get("entries", {})),
                "limitations": ["Read-only inspection does not establish flag-write safety."]}


def _wait_authoring_report(project, identifier):
    """Unsupported authoring must not suppress the read-only script report."""
    try:
        return project.wait_options(identifier)
    except (RetailImportError, ProjectError) as exc:
        return {"supported": False, "reason": str(exc), "targets": [],
                "unresolved_overrides": sorted(project.overrides.get(identifier, {}).get("ScriptWaits", {}).get("entries", {})),
                "limitations": ["Read-only inspection does not establish wait-write safety."]}


def _model_selector_authoring_report(project, identifier):
    """Unsupported authoring must not suppress the read-only script report."""
    try:
        return project.model_selector_options(identifier)
    except (RetailImportError, ProjectError) as exc:
        return {"supported": False, "reason": str(exc), "targets": [],
                "unresolved_overrides": sorted(project.overrides.get(identifier, {}).get("ScriptModelSelectors", {}).get("entries", {})),
                "limitations": ["Read-only inspection does not establish model_selector-write safety."]}


def _animation_export_choice(body):
    """Exactly one export representation, before expensive source decoding."""
    import math
    if 'clip_fps' in body:
        fps = body['clip_fps']
        if 'frame_index' in body or type(fps) not in (int, float) or not math.isfinite(fps) or not 1 <= fps <= 120:
            raise ProjectError('Choose either a frame index or an explicit clip rate from 1 to 120 fps')
        return None, fps
    frame = body.get('frame_index')
    if type(frame) is not int or frame < 0:
        raise ProjectError('Choose a nonnegative animation frame index to export')
    return frame, None


class EditorServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def server_bind(self) -> None:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()

    def __init__(self, address: tuple[str, int], project: ProjectService, runtime_port: int = 4370):
        if address[0] not in ("127.0.0.1", "localhost"):
            raise ProjectError("Editor service must bind to loopback")
        from integrations.legaia.observer.service import ObserverService
        self.project = project
        self.last_build = None
        self.texture_catalogs = {}
        from .scene_preview import ScenePreviewService
        self.scene_previews = ScenePreviewService()
        from .run import RunService
        self.runs = RunService()
        self.observer = ObserverService(port=runtime_port)
        self.live_status = {"available": False, "state": "disconnected", "reason": {"message": "Runtime has not been checked"}}
        self.command_lock = threading.RLock()
        self.editor_root = Path(__file__).resolve().parents[1] / "editor"
        super().__init__(address, EditorHandler)

    def state(self) -> dict:
        from importer.animation import animation_capabilities
        state = self.project.state()
        state["runtime"] = self.live_status
        state["capabilities"]["live_mode"] = self.live_status.get("available", False)
        state["capabilities"]["runtime_discovery"] = True
        state["capabilities"]["model_preview"] = bool(self.project.disc_path)
        state["capabilities"]["model_shape_authoring"] = bool(self.project.disc_path)
        state["capabilities"]["model_glb_authoring"] = bool(self.project.disc_path)
        state["capabilities"]["model_material_authoring"] = bool(self.project.disc_path)
        state["capabilities"]["model_face_removal"] = bool(self.project.disc_path)
        state["capabilities"]["model_face_addition"] = bool(self.project.disc_path)
        state["capabilities"]["model_vector_allocation"] = bool(self.project.disc_path)
        state["capabilities"]["model_group_allocation"] = bool(self.project.disc_path)
        state["capabilities"]["model_object_allocation"] = bool(self.project.disc_path)
        state["capabilities"]["model_mesh_append"] = bool(self.project.disc_path)
        state["capabilities"]["model_allocation_inspection"] = bool(self.project.disc_path)
        state["capabilities"]["scene_animation_preview"] = bool(self.project.disc_path)
        state["capabilities"]["draft_output_review"] = bool(self.project.disc_path and self.project.actor_drafts)
        state["capabilities"]["texture_png_authoring"] = bool(self.project.disc_path)
        state["capabilities"]["animation_preview"] = bool(self.project.disc_path)
        from .scene_preview import source_key
        try:
            state["scene_preview_source_key"] = source_key(self.project)
        except (RetailImportError, OSError):
            state["scene_preview_source_key"] = None
        state["capabilities"]["scene_preview"] = bool(state["scene_preview_source_key"])
        for asset in state["assets"]:
            asset["animation_support"] = animation_capabilities(asset)
        from importer.scene_animation import actor_animation_capabilities
        actors = {actor["semantic_id"]: actor for actor in
                  self.project.imports.get(self.project.active_scene, {}).get("actors", [])}
        asset_support={asset['id']:asset.get('animation_support',{}) for asset in state['assets']}
        for entity in state["scene"]["entities"]:
            model=entity['components'].get('ModelRenderer')
            if model is not None:
                support=asset_support.get(model.get('asset_id'),{});clips=support.get('clips',[])
                model['reference_animation']={'supported':support.get('supported') is True and bool(clips),
                                              'first_clip_id':clips[0]['id'] if support.get('supported') is True and clips else None}
            actor = actors.get(entity["id"])
            if actor is not None and "Animation" in entity["components"]:
                asset = self.project.assets.records.get(actor["model_reference"].get("asset_semantic_id"), {})
                entity["components"]["Animation"]["preview_support"] = actor_animation_capabilities(actor, asset)
        state["capabilities"]["actor_animation_preview"] = bool(self.project.disc_path)
        state["capabilities"]["actor_animation_authoring"] = bool(self.project.disc_path)
        from .script_branches import state_key as script_state_key
        state['script_authoring_state_key'] = script_state_key(self.project)
        state['capabilities']['script_branch_authoring'] = bool(self.project.disc_path)
        from .worldmap_authoring import state_key as worldmap_state_key
        state['worldmap_authoring_state_key'] = worldmap_state_key(self.project)
        state['capabilities']['worldmap_authoring'] = bool(self.project.disc_path and self.project.imports)
        state['capabilities']['worldmap_geometry'] = bool(self.project.disc_path and self.project.imports)
        state['capabilities']['worldmap_export'] = bool(self.project.disc_path and self.project.imports)
        state['capabilities']['worldmap_placements'] = bool(self.project.disc_path and self.project.imports)
        from .project_assets import source_key as project_assets_source_key
        state['project_assets_source_key'] = None
        state['project_assets_unavailable_reason'] = None
        try:
            if 1 <= len(self.project.imports) <= 64:
                state['project_assets_source_key'] = project_assets_source_key(self.project)
            else:
                state['project_assets_unavailable_reason'] = 'Project resource discovery requires from 1 through 64 imported scenes.'
        except ProjectError as exc:
            state['project_assets_unavailable_reason'] = str(exc)
        if not self.project.disc_path:
            state['project_assets_unavailable_reason'] = 'Project resource discovery requires the user-owned source disc and imported scenes.'
        state['capabilities']['project_assets'] = bool(self.project.disc_path and state['project_assets_source_key'])
        state["capabilities"]["actor_script_preview"] = bool(self.project.disc_path)
        state["capabilities"]["actor_candidate_inspection"] = bool(self.project.disc_path)
        state["capabilities"]["actor_dialogue_authoring"] = bool(self.project.disc_path)
        state["capabilities"]["actor_wait_authoring"] = bool(self.project.disc_path)
        state["capabilities"]["actor_movement_authoring"] = bool(self.project.disc_path)
        state["capabilities"]["actor_facing_authoring"] = bool(self.project.disc_path)
        state["capabilities"]["actor_model_selector_authoring"] = bool(self.project.disc_path)
        state["capabilities"]["actor_flag_authoring"] = bool(self.project.disc_path)
        state["capabilities"]["actor_branch_authoring"] = bool(self.project.disc_path)
        state["capabilities"]["text_font_preview"] = bool(self.project.disc_path)
        state["capabilities"]["scene_text_search"] = bool(self.project.disc_path and self.project.active_scene)
        from .resources import scene_text_state_key, project_text_state_key, project_transition_state_key
        state['scene_text_state_key'] = scene_text_state_key(self.project)
        state['project_transition_state_key'] = project_transition_state_key(self.project)
        try:
            state['project_text_state_key'] = project_text_state_key(self.project)
        except (RetailImportError, OSError):
            state['project_text_state_key'] = None
        state["capabilities"]["actor_appearance"] = bool(self.project.disc_path)
        state['capabilities']['actor_animation_assignment'] = bool(self.project.disc_path and self.project.active_scene)
        state["capabilities"]["actor_preset_batch"] = bool(self.project.disc_path and self.project.active_scene)
        state["capabilities"]["resource_catalog"] = bool(self.project.disc_path and self.project.active_scene)
        state['capabilities']['asset_references'] = bool(self.project.disc_path and self.project.active_scene and len(self.project.imports)<=64)
        state['capabilities']['worldmap_source_navigation'] = bool(self.project.disc_path)
        state["capabilities"]["scene_transitions"] = state["capabilities"]["resource_catalog"]
        state["capabilities"]["scene_flags"] = state["capabilities"]["resource_catalog"]
        from .resources import scene_flag_state_key, project_flag_state_key, scene_transition_state_key, scene_region_state_key, scene_trigger_state_key
        state['scene_transition_state_key'] = scene_transition_state_key(self.project)
        from .resources import project_transition_state_key
        state['project_transition_state_key'] = project_transition_state_key(self.project)
        state['scene_region_state_key'] = scene_region_state_key(self.project)
        state['scene_trigger_state_key'] = scene_trigger_state_key(self.project)
        state['capabilities']['field_trigger_authoring'] = bool(self.project.disc_path and self.project.active_scene and self.project.mode == 'edit')
        state['capabilities']['field_trigger_script_authoring'] = bool(self.project.disc_path and self.project.active_scene and self.project.mode == 'edit')
        state['capabilities']['field_region_authoring'] = bool(self.project.disc_path and self.project.active_scene and self.project.mode == 'edit')
        state['scene_flag_state_key'] = scene_flag_state_key(self.project)
        state['project_flag_state_key'] = project_flag_state_key(self.project)
        state["capabilities"]["script_operand_files"] = bool(self.project.disc_path and self.project.active_scene)
        state['capabilities']['script_facing_authoring'] = bool(self.project.disc_path and self.project.active_scene)
        state["capabilities"]["texture_preview"] = state["capabilities"]["resource_catalog"]
        state["capabilities"]["texture_replacement"] = state["capabilities"]["resource_catalog"]
        state["capabilities"]["texture_slot_authoring"] = bool(state["capabilities"]["resource_catalog"] and self.project.mode=="edit")
        state["capabilities"]["texture_resize_authoring"] = bool(state["capabilities"]["resource_catalog"] and self.project.mode=="edit")
        state["capabilities"]["field_map_preview"] = state["capabilities"]["resource_catalog"]
        state["capabilities"]["trigger_script_preview"] = state["capabilities"]["resource_catalog"]
        state["capabilities"]["build"] = bool(self.project.disc_path and self.project.imports)
        state['capabilities']['build_review'] = bool(self.project.disc_path and 1<=len(self.project.imports)<=64)
        from .build import authored_state_key
        state['build_review_source_key'] = authored_state_key(self.project)
        from .project_copy import source_key as copy_source_key
        state['project_copy_source_key'] = copy_source_key(self.project)
        state['capabilities']['project_copy'] = self.project.mode=='edit' and len(self.project.imports)<=64
        if self.last_build is None:
            state["build"] = None
        else:
            from .build import authored_state_key
            from copy import deepcopy
            state["build"] = deepcopy(self.last_build)
            state["build"]["current"] = self.last_build.get("authored_state_key") == authored_state_key(self.project)
        state["run"] = self.runs.status()
        try:
            state["launch_config"] = self.runs.config(self.project)
        except (ProjectError, ValueError, OSError) as exc:
            state["launch_config"] = {}
            state["diagnostics"].append("Launch configuration: " + str(exc))
        state["capabilities"]["build_and_run"] = state["capabilities"]["build"]
        return state

    def server_close(self) -> None:
        self.observer.close()
        super().server_close()

    def actor_animation_preview(self, entity_id: str, representation: str = "imported") -> dict:
        """Resolve an imported actor; clients cannot supply a model or clip binding."""
        from importer.pipeline import _disc_context
        from importer.scene_animation import load_scene_actor_animation_catalog
        project = self.project
        if representation not in ("imported", "authored"):
            raise ProjectError("Animation representation must be imported or authored")
        if not project.disc_path:
            raise ProjectError("Actor animation preview requires the project's user-owned disc")
        document = project.imports.get(project.active_scene)
        actor = next((item for item in (document or {}).get("actors", [])
                      if item["semantic_id"] == entity_id), None)
        if actor is None:
            raise ProjectError("Actor animation requires an imported actor in the active scene")
        asset = project.assets.records.get(actor["model_reference"].get("asset_semantic_id"))
        if asset is None:
            raise ProjectError("Actor's imported model is unresolved")
        with _disc_context(project.disc_path):
            catalog = load_scene_actor_animation_catalog(project.disc_path, document["scene"]["name"])
            overrides = {a["semantic_id"]: project.overrides[a["semantic_id"]]["AnimationChannels"]
                         for a in document["actors"] if "AnimationChannels" in project.overrides.get(a["semantic_id"], {})}
            initial_id = actor["placement_fields"].get("animation_id")
            clip_id = f"animation://{document['scene']['name']}/scene-anm/{initial_id - 1:04d}" if type(initial_id) is int and initial_id > 0 else None
            affected = any(value["animation_id"] == clip_id for value in overrides.values())
            if representation == "authored":
                if not affected:
                    raise ProjectError("Actor's imported clip has no authored animation channels")
                animation = catalog.authored_bank_preview(actor, asset, overrides)
            else:
                animation = catalog.animation_preview(actor, asset)
            preview = self.model_preview(asset, prepared=animation.pop("geometry"))
            preview["frames"] = animation.pop("frames")
            animation.update(source_clip_id=animation["clip_id"], clip_id="authored-channels" if representation == "authored" else "scene-header", entity_id=entity_id, representation=representation)
            preview["animation"] = animation
            preview["animation_support"] = {
                "supported": True, "clips": [{"id": "scene-header", "label": "Imported scene animation"}],
                "evidence": "verified_man_header_initial_animation_not_runtime_script_state"}
            if affected:
                preview["animation_support"]["clips"].append({"id": "authored-channels", "label": "Authored channel overrides"})
        return preview

    def review_actor_drafts(self, expected_key: str) -> dict:
        from .draft_review import review
        return review(self.project, expected_key)

    def export_actor_drafts(self, entity_id: str | None = None) -> dict:
        from uuid import uuid4
        from .draft_build import export_draft_disc
        project = self.project
        if project.mode != 'edit':
            raise ProjectError('Draft export requires Edit mode')
        draft = project.actor_drafts.get(entity_id)
        if entity_id is not None and (draft is None or draft['scene_id'] != project.active_scene):
            raise ProjectError('Draft export requires a draft in the active scene')
        directory = (project.root / 'Builds' / ('experimental-drafts-' + uuid4().hex)).resolve()
        if not directory.is_relative_to(project.root.resolve()):
            raise ProjectError('Draft export directory escapes the project root')
        report = export_draft_disc(project, entity_id, directory)
        return dict(report_path=str(directory / 'report.json'),
                    input_project_path=str(directory / 'Inputs' / 'project.legaia.json'),
                    disc_path=report['disc']['output_path'],
                    output_sha256=report['disc']['output_sha256'],
                    gameplay_verified=False, experimental=True)

    def actor_candidate_inspection(self, entity_id: str) -> dict:
        from importer.actor_candidate_inspection import inspect_actor_candidate
        project = self.project
        if not project.disc_path:
            raise ProjectError("Actor candidate inspection requires the project's disc")
        document = project.imports.get(project.active_scene)
        draft = getattr(project, 'actor_drafts', {}).get(entity_id)
        if draft:
            project._validate_actor_draft(entity_id,draft)
            if draft['scene_id'] != project.active_scene:
                raise ProjectError('Actor draft is outside the active scene')
        donor_id = draft['donor_entity_id'] if draft else entity_id
        actor = next((item for item in (document or {}).get("actors", [])
                      if item["semantic_id"] == donor_id), None)
        if actor is None:
            raise ProjectError("Actor candidate requires an imported actor in the active scene")
        overrides = project.overrides.get(entity_id, {})
        authored = draft['position'] if draft else overrides.get("Transform", {}).get("position", {})
        position = {axis: authored[axis] for axis in ("x", "z") if axis in authored}
        report = inspect_actor_candidate(project.disc_path, document["scene"]["name"],
                                         actor["source_record"]["record_index"], position=position or None)
        report["entity_id"] = entity_id
        report["donor_entity_id"] = donor_id
        report["representation"] = "positioned_retail_donor_candidate" if position else "retail_donor_candidate"
        report["includes_project_overrides"] = bool(position)
        report["included_overrides"] = {"Transform": {"position": position}} if position else {}
        report["excluded_override_components"] = sorted(key for key in overrides if key != "Transform")
        report["excluded_transform_axes"] = sorted(set(authored)-set(position))
        if draft:
            report['representation'] = 'authored_npc_draft_candidate'
        return report

    def actor_script_preview(self, entity_id: str) -> dict:
        from importer.script_inspection import inspect_actor_script
        from importer.pipeline import _disc_context
        project = self.project
        if not project.disc_path:
            raise ProjectError("Script inspection requires the project's user-owned disc")
        document = project.imports.get(project.active_scene)
        actor = next((item for item in (document or {}).get("actors", [])
                      if item["semantic_id"] == entity_id), None)
        if actor is None:
            raise ProjectError("Script inspection requires an imported actor in the active scene")
        with _disc_context(project.disc_path):
            report = inspect_actor_script(project.disc_path, document["scene"]["name"], actor)
            report["movement_authoring"] = _movement_authoring_report(project, entity_id)
            report['facing_authoring'] = _facing_authoring_report(project, entity_id)
            report["flag_authoring"] = _flag_authoring_report(project, entity_id)
            report["wait_authoring"] = _wait_authoring_report(project, entity_id)
            report["model_selector_authoring"] = _model_selector_authoring_report(project, entity_id)
            try:
                report["dialogue_authoring"] = project.dialogue_options(entity_id)
                report["transition_authoring"] = _transition_authoring_report(project, entity_id)
            except (RetailImportError, ProjectError) as exc:
                reason = ("Read-only streaming script inspection. Text and transition authoring are not yet supported for this scene."
                          if report.get("man_source", {}).get("source_kind") == "raw_streaming_man" else str(exc))
                report["dialogue_authoring"] = {"supported": False, "reason": reason, "runs": [],
                                                "unresolved_overrides": sorted(project.overrides.get(entity_id, {}).get("Dialogue", {}).get("runs", {})),
                                                "limitations": ["Read-only script inspection does not establish text-write safety."]}
            return report

    def actor_appearance_preview(self, entity_id: str) -> dict:
        from importer.pipeline import _disc_context
        if not self.project.overrides.get(entity_id, {}).get("ActorAppearance"):
            raise ProjectError("Actor has no authored appearance override")
        with _disc_context(self.project.disc_path):
            donor = self.project.appearance_source_actor(entity_id, verify_disc=True)
            preview = self.actor_animation_preview(donor["semantic_id"])
            preview["animation"].update(entity_id=entity_id, donor_entity_id=donor["semantic_id"],
                                        clip_id="authored-appearance", layer="authored",
                                        label="Authored initial appearance")
            preview["animation_support"]["clips"] = [{"id": "authored-appearance", "label": "Authored initial appearance"}]
            return preview

    def actor_initial_animation_preview(self, entity_id: str) -> dict:
        from .actor_animation import source_actor
        from importer.pipeline import _disc_context
        if self.project.overrides.get(entity_id,{}).get('ActorAllocatedAnimation'):
            from .allocated_animation_assignment import assigned_pose
            animation,asset=assigned_pose(self.project,entity_id)
            geometry=animation.pop('geometry');geometry['frames']=animation.pop('frames')
            preview=self.model_preview(asset,prepared=geometry,effective_shape=True)
            preview['animation']=animation
            preview['animation_support']=dict(supported=True,clips=[dict(id='authored-allocated-animation',label='Assigned allocated initial clip')],
                evidence='authored_initial_header_assignment_not_runtime_state')
            return preview
        if not self.project.overrides.get(entity_id, {}).get('ActorAnimation'):
            raise ProjectError('Actor has no authored initial animation assignment')
        if not any(a['semantic_id'] == entity_id for a in
                   self.project.imports.get(self.project.active_scene, {}).get('actors', [])):
            raise ProjectError('Initial animation preview requires an actor in the active scene')
        with _disc_context(self.project.disc_path):
            witness = source_actor(self.project, entity_id, verify_disc=True)
            value = self.project.overrides[entity_id]['ActorAnimation']
            changed = any(c.get('AnimationChannels', {}).get('animation_id') == value['animation_asset_id']
                          for c in self.project.overrides.values())
            preview = self.actor_animation_preview(witness['semantic_id'], 'authored' if changed else 'imported')
            preview['animation'].update(entity_id=entity_id, donor_entity_id=witness['semantic_id'],
                clip_id='authored-initial-animation', source_clip_id=value['animation_asset_id'],
                layer='authored', label='Assigned initial animation',
                assignment_source_record_sha256=value['source_record_sha256'])
            preview['animation_support']['clips'] = [{'id':'authored-initial-animation', 'label':'Assigned initial animation'}]
            return preview

    def export_allocated_animation(self,body):
        from .scene_preview import source_key
        from .animation_allocation import pose_saved_record
        from .allocated_animation_assignment import assigned_pose,pose_preview
        representation=body.get('representation')
        fields={'scene_id','record_id','expected_source_key','representation'}
        if representation in ('allocated_assignment_preview','allocated_initial_assignment'):
            fields.add('entity_id')
        if representation=='allocated_assignment_preview':
            fields.add('review_key')
        choice={'clip_fps'} if 'clip_fps' in body else {'frame_index'}
        if representation not in ('allocated_record','allocated_assignment_preview','allocated_initial_assignment') or set(body)!=fields|choice:
            raise ProjectError('Allocated export requires exact retained identity, representation, current source and frame or rate')
        frame,fps=_animation_export_choice(body)
        key=source_key(self.project)
        if not key or body['expected_source_key']!=key or body['scene_id']!=self.project.active_scene:
            raise ProjectError('Allocated export source changed; reopen the clip Preview')
        if representation=='allocated_record':
            animation,asset=pose_saved_record(self.project,body['scene_id'],body['record_id'],key)
        elif representation=='allocated_assignment_preview':
            animation,asset,_=pose_preview(self.project,body['entity_id'],body['record_id'],key,body['review_key'])
        else:
            animation,asset=assigned_pose(self.project,body['entity_id'])
            if animation['authored_assignment']['record_id']!=body['record_id']:
                raise ProjectError('Allocated export differs from the current initial assignment')
        geometry=animation.pop('geometry');geometry['frames']=animation.pop('frames')
        preview=self.model_preview(asset,prepared=geometry,effective_shape=True)
        animation['export_source_key']=key;preview['animation']=animation
        binding=None
        if fps is not None and representation!='allocated_assignment_preview':
            from .animation_record_glb import export_binding
            binding=export_binding(self.project,body['scene_id'],body['record_id'],key,fps)
        result=self.export_preview(preview,frame,fps,expected_source_key=key)
        if binding is not None:
            from .build import _guard_output
            binding_path=Path(result['path']).with_suffix('.binding.json')
            _guard_output(binding_path,self.project.root)
            with binding_path.open('xb') as handle:
                handle.write((json.dumps(binding,sort_keys=True,indent=2,allow_nan=False)+'\n').encode('utf-8'))
            result.update(binding=binding,binding_path=str(binding_path),binding_filename=binding_path.name)
            result.update(glb_base64=base64.b64encode(Path(result['path']).read_bytes()).decode('ascii'))
        return result

    def export_preview(self, preview: dict, frame_index: int | None, clip_fps: float | None = None, *,expected_source_key=None) -> dict:
        from .build import _guard_output
        from .project import atomic_write
        from importer.export import write_model_export
        output = self.project.root / "Exports"
        _guard_output(output / ".gitignore", self.project.root)
        if expected_source_key is None:
            result = write_model_export(preview, output, frame_index, clip_fps=clip_fps)
        else:
            from importer.export import encode_model_glb,write_encoded_glb
            from .scene_preview import source_key
            data,audit=encode_model_glb(preview,frame_index,clip_fps=clip_fps)
            if source_key(self.project)!=expected_source_key:
                raise ProjectError('Allocated source changed during GLB encoding; no export published')
            result=write_encoded_glb(data,audit,output)
        if not (output / ".gitignore").exists():
            atomic_write(output / ".gitignore", b"*\n")
        return result

    def scene_shape_proposal(self, asset_id: str, entity_id: str, replacement: bytes, report: dict, key: str, all_instances: bool = False, material_content: bool = False, *, prepared_binding: dict | None = None) -> dict:
        from .scene_preview import source_key, preview_shape_instance, preview_shape_instances
        from importer.scene_animation import load_scene_actor_animation_catalog
        from importer.environment import load_environment_preview_catalog
        from .terrain_preview import terrain_preview
        if not key or source_key(self.project) != key:
            raise ProjectError('Scene changed; refresh before inspecting a proposed shape')
        scene = self.scene_previews.preview(self.project,
            lambda asset, *args, **kwargs: self.model_preview(asset, *args, effective_shape=True, **kwargs),
            load_scene_actor_animation_catalog, load_environment_preview_catalog, terrain_preview)
        material_content = material_content or self.project.model_overrides.get(asset_id, {}).get('format') in ('tmd-content-v2', 'tmd-content-v3')
        proposal_binding = {'asset_sha256': report['proposed_sha256'],
                            'format': 'tmd-content-v2' if material_content else 'tmd-content-v1'}
        existing = self.project.model_overrides.get(asset_id, {})
        if existing.get('format') == 'tmd-face-removal-v1':
            proposal_binding.update(format=existing['format'], removed_faces=[dict(row) for row in existing['removed_faces']])
        if prepared_binding is not None:
            from copy import deepcopy
            from hashlib import sha256
            if (prepared_binding.get('format') != 'tmd-face-addition-v1'
                    or prepared_binding.get('asset_sha256') != report['proposed_sha256']
                    or prepared_binding.get('asset_sha256') != sha256(replacement).hexdigest()
                    or prepared_binding.get('byte_length') != len(replacement)):
                raise ProjectError('Scene topology proposal differs from its prepared binding')
            proposal_binding = deepcopy(prepared_binding)
        report['preview'] = preview_shape_instance(scene,asset_id,entity_id,replacement,proposal_binding)
        if all_instances:
            report.update(preview_shape_instances(scene,asset_id,replacement,proposal_binding))
        # UV edits change the required texture crop even when CLUT/page bindings
        # stay fixed. Refresh each proposed pose group from the verified catalog.
        from .scene_preview import MAX_TEXTURE_BYTES
        asset = self.project.assets.records.get(asset_id)
        if asset is None:
            raise ProjectError('Scene model proposal has no imported asset identity')
        report['preview'] = self.model_preview(asset, prepared=report['preview'])
        texture_bytes = 0
        for geometry in report.get('proposal_assets', []):
            geometry['preview'] = self.model_preview(asset, prepared=geometry['preview'])
            texture_bytes += sum((len(t.get('rgba_base64', '')) + len(t.get('stp_base64', ''))) * 3 // 4
                                 for t in geometry['preview'].get('textures', []))
        if texture_bytes > MAX_TEXTURE_BYTES:
            raise ProjectError('Proposed scene model textures exceed the scene byte budget')
        report.pop('current_preview',None)
        report.update(entity_id=entity_id,scene_id=scene['scene_id'],project_source_key=key)
        if source_key(self.project) != key:
            raise ProjectError('Scene changed during shape proposal inspection')
        return report

    def scene_animation_preview(self, representation: str, expected_source_key: str) -> dict:
        from .scene_animation import prepare_scene_animation
        from .scene_preview import preview_project, source_key
        from .terrain_preview import terrain_preview
        from importer.pipeline import _disc_context
        from importer.animation import animation_capabilities
        from importer.scene_animation import load_scene_actor_animation_catalog
        from importer.environment import load_environment_preview_catalog
        project = self.project
        if project.mode != 'edit' or not expected_source_key or source_key(project) != expected_source_key:
            raise ProjectError('Scene animation source changed; refresh the editable scene')
        view = preview_project(project, representation)
        scene = self.scene_previews.preview(view,
            lambda asset, *args, **kwargs: self.model_preview(asset, *args, effective_shape=True, project_view=view, **kwargs),
            load_scene_actor_animation_catalog, load_environment_preview_catalog, terrain_preview)
        scene.update(representation=representation, project_source_key=expected_source_key)
        document = view.imports[view.active_scene]
        actors = {a['semantic_id']: a for a in document['actors']}
        overrides = {identifier: view.overrides[identifier]['AnimationChannels'] for identifier in actors
                     if 'AnimationChannels' in view.overrides.get(identifier, {})}
        catalog = None
        def load(instance, asset):
            nonlocal catalog
            actor = actors.get(instance.get('source_actor_id'))
            if actor is None or actor['model_reference'].get('asset_semantic_id') != asset['semantic_id']:
                raise ProjectError('Scene animation model and source actor binding differ')
            support = animation_capabilities(asset)
            if instance['pose_kind'] in ('reference_party_idle', 'reference_global_loop'):
                if support.get('supported') is not True or not support.get('clips'):
                    raise ProjectError('Scene reference clip no longer matches its model')
                preview = self.model_preview(asset, support['clips'][0]['id'], effective_shape=True, project_view=view)
                preview['animation']['source_clip_id'] = preview['animation']['semantic_id']
                return preview
            if catalog is None:
                catalog = load_scene_actor_animation_catalog(view.disc_path, document['scene']['name'])
            initial_id = actor['placement_fields'].get('animation_id')
            clip_id = f"animation://{document['scene']['name']}/scene-anm/{initial_id - 1:04d}" if type(initial_id) is int and initial_id > 0 else None
            affected = any(value['animation_id'] == clip_id for value in overrides.values())
            animation = (catalog.authored_bank_preview(actor, asset, overrides) if affected
                         else catalog.animation_preview(actor, asset))
            animation['source_clip_id'] = animation['semantic_id']
            prepared = animation.pop('geometry'); prepared['frames'] = animation.pop('frames')
            prepared['animation'] = animation
            return self.model_preview(asset, prepared=prepared, effective_shape=True, project_view=view)
        with _disc_context(view.disc_path):
            report = prepare_scene_animation(project, scene, load, representation, expected_source_key)
        if source_key(project) != expected_source_key:
            raise ProjectError('Scene changed during animation preparation')
        return report

    def scene_texture_proposal(self, asset_id: str, candidate: bytes, report: dict, key: str) -> dict:
        from copy import deepcopy
        from .scene_preview import source_key
        from .resources import apply_texture_overrides
        from importer.textures import load_scene_texture_catalog, parse_tim
        from importer.scene_animation import load_scene_actor_animation_catalog
        from importer.environment import load_environment_preview_catalog
        from .terrain_preview import terrain_preview
        if not key or source_key(self.project) != key:
            raise ProjectError('Scene changed; refresh before inspecting a texture proposal')
        scene = self.scene_previews.preview(self.project,
            lambda asset, *args, **kwargs: self.model_preview(asset, *args, effective_shape=True, **kwargs),
            load_scene_actor_animation_catalog, load_environment_preview_catalog, terrain_preview)
        from importer.pipeline import _disc_context
        with _disc_context(self.project.disc_path):
            catalog=deepcopy(apply_texture_overrides(self.project,load_scene_texture_catalog(self.project.disc_path,self.project.active_scene.removeprefix('scene://'))))
            matches=[i for i,(_,source) in enumerate(catalog.textures) if source['semantic_id']==asset_id]
            if len(matches)!=1:
                raise ProjectError('Texture proposal must resolve one source in the scene texture catalog')
            index=matches[0];catalog.textures[index]=(parse_tim(candidate),catalog.textures[index][1])
            changed=[];materials=0;unavailable=[];texture_bytes=0
            from .scene_preview import MAX_TEXTURE_BYTES
            for geometry in scene['assets']:
                asset=self.project.assets.records.get(geometry['asset_id'])
                if geometry.get('pose_kind')=='source_heightfield':
                    proposed=terrain_preview(self.project,prepared=geometry['preview'],catalog=catalog)
                elif asset is not None:
                    proposed=self.model_preview(asset,prepared=geometry['preview'],texture_catalog=catalog)
                else:
                    unavailable.append(geometry['geometry_key']);proposed=geometry['preview']
                texture_bytes+=sum((len(t.get('rgba_base64',''))+len(t.get('stp_base64','')))*3//4 for t in proposed.get('textures',[]))
                if texture_bytes>MAX_TEXTURE_BYTES:
                    raise ProjectError('Proposed scene textures exceed the scene byte budget')
                old=geometry['preview'].get('textures',[]);new=proposed.get('textures',[])
                if old!=new:
                    materials+=sum(a!=b for a,b in zip(old,new))+abs(len(old)-len(new))
                    changed.append({'geometry_key':geometry['geometry_key'],'asset_id':geometry['asset_id'],'preview':proposed})
        keys={a['geometry_key'] for a in changed}
        report.update(proposal_assets=changed,affected_instances=[e['entity_id'] for e in scene['entities'] if e.get('renderable') and e.get('geometry_key') in keys],
                      affected_material_count=materials,decoded_texture_bytes=texture_bytes,unavailable_geometry_keys=unavailable,scene_id=scene['scene_id'],project_source_key=key,
                      evidence='static_vram_address_reconstruction_not_runtime_residency')
        if source_key(self.project)!=key:
            raise ProjectError('Scene changed during texture proposal inspection')
        return report

    def model_preview(self, asset: dict, clip_id: str | None = None, *, prepared: dict | None = None, effective_shape: bool = False, project_view=None, texture_catalog=None) -> dict:
        from importer.assets import load_model_preview
        from importer.animation import animation_capabilities, load_animation_preview
        from importer.textures import (associate_material, load_asset_texture_catalog,
                                       load_scene_texture_catalog, uses_field_party_textures)
        project = self.project if project_view is None else project_view
        if prepared is not None:
            from copy import deepcopy
            preview = deepcopy(prepared)
        elif clip_id is not None:
            animation = load_animation_preview(Path(project.disc_path), asset, clip_id)
            preview = animation.pop("geometry")
            preview["frames"] = animation.pop("frames")
            preview["animation"] = animation
        else:
            preview = load_model_preview(Path(project.disc_path), asset)
        if effective_shape and asset['semantic_id'] in project.model_overrides:
            from importer.model_authoring import preview_model_shape
            binding = project.model_overrides[asset['semantic_id']]
            preview = preview_model_shape(preview, project.read_model_replacement(asset['semantic_id'], binding), binding)
        preview["animation_support"] = animation_capabilities(asset)
        scene = asset.get("source_record", {}).get("prot_entry_name")
        if scene == "befect_data":
            scene = project.imports.get(project.active_scene, {}).get("scene", {}).get("name")
        if not scene:
            preview["textures"] = []
            return preview
        from .scene_preview import source_key
        from .resources import apply_texture_overrides
        for binding in project.texture_overrides.values():
            if binding["source_scene_id"] == "scene://" + scene:
                project.read_texture_replacement(binding)
        from .texture_slots import read
        for identifier,binding in project.texture_additions.items():
            if binding['source_scene_id']=='scene://'+scene:read(project,identifier,binding)
        key = (project.disc_path, scene, source_key(project))
        if key not in self.texture_catalogs:
            if len(self.texture_catalogs) >= 2:
                self.texture_catalogs.clear()
            self.texture_catalogs[key] = apply_texture_overrides(project, load_scene_texture_catalog(project.disc_path, scene))
        # The selected shared bank never replaces or merges into the scene cache.
        catalog = load_asset_texture_catalog(project.disc_path, asset, texture_catalog if texture_catalog is not None else self.texture_catalogs[key])
        preview["texture_scope"] = "field_party" if uses_field_party_textures(asset) else "scene"
        preview["texture_catalog"] = catalog.metadata()
        preview["textures"] = []
        budget = 2 * 1024 * 1024
        for index, material in enumerate(preview.get("materials", [])):
            material['blend'] = {
                'enabled': bool(material.get('semi_transparent')),
                'mode': ((material['tpage'] >> 5) & 3) if material.get('textured') else 0,
                'texel_gate': 'stp_bit' if material.get('textured') else 'all_fragments',
                'evidence': 'decoded_primitive_ABE_and_tpage_ABR; untextured_ABR0_reference_default',
            }
            if not material.get("textured"):
                preview["textures"].append({"material_index": index, "status": "untextured", "reason": "Material uses vertex colors"})
                continue
            uvs = [uv for triangle_index, material_index in enumerate(preview["triangle_materials"])
                   if material_index == index for uv in (preview["triangle_uvs"][triangle_index] or [])]
            if not uvs or index >= 32:
                preview["textures"].append({"material_index": index, "status": "unsupported", "reason": "Missing texture coordinates or bounded preview limit"})
                continue
            bounds = (min(uv[0] for uv in uvs), min(uv[1] for uv in uvs), max(uv[0] for uv in uvs), max(uv[1] for uv in uvs))
            result = associate_material(catalog, material, bounds)
            rgba = result.pop("rgba", None)
            stp = result.pop("stp", None)
            if rgba is not None:
                if stp is None or len(stp) * 4 != len(rgba) or any(bit not in (0, 1) for bit in stp):
                    raise ProjectError('Texture transparency mask does not match decoded pixels')
                if len(rgba) + len(stp) > budget:
                    result = {"status": "unsupported", "reason": "Decoded texture preview byte budget exceeded"}
                else:
                    budget -= len(rgba) + len(stp)
                    result["rgba_base64"] = base64.b64encode(rgba).decode("ascii")
                    result["stp_base64"] = base64.b64encode(stp).decode("ascii")
            result["material_index"] = index
            preview["textures"].append(result)
        return preview


class EditorHandler(BaseHTTPRequestHandler):
    server: EditorServer

    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(10)

    def _trusted_request(self) -> bool:
        # Block browser-driven cross-origin local commands (including DNS rebinding).
        host = self.headers.get("Host", "")
        valid = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
        if host not in valid:
            self._json(403, {"error": "Editor accepts only its loopback host"})
            return False
        origin = self.headers.get("Origin")
        if origin and origin not in {"http://" + value for value in valid}:
            self._json(403, {"error": "Cross-origin editor requests are forbidden"})
            return False
        return True

    def _send(self, status: int, content: bytes, content_type: str) -> None:
        try:
            self._write_response(status, content, content_type)
        except (ConnectionError, TimeoutError):
            # The client may close a tab while a scene preview is computing.
            # A failed socket write cannot be repaired with another response.
            self.close_connection = True

    def _write_response(self, status: int, content: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(content)

    def _json(self, status: int, value: dict) -> None:
        self._send(status, json.dumps(value, allow_nan=False).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self) -> None:
        if not self._trusted_request():
            return
        route = urlsplit(self.path).path
        with self.server.command_lock:
            if route == "/api/run/status":
                self._json(200, {"run": self.server.runs.status()})
                return
            if route == "/api/state":
                self._json(200, self.server.state())
                return
        files = {"/": ("index.html", "text/html"), "/editor.js": ("editor.js", "text/javascript"),
                 "/text-font.js": ("text-font.js", "text/javascript"),
                 "/group-appearance.js": ("group-appearance.js", "text/javascript"),
                 "/actor-selection-sets.js": ("actor-selection-sets.js", "text/javascript"),
                 "/scene-views.js": ("scene-views.js", "text/javascript"),
                 "/scene-camera.js": ("scene-camera.js", "text/javascript"),
                 "/asset-search.js": ("asset-search.js", "text/javascript"),
                 "/hierarchy-navigation.js": ("hierarchy-navigation.js", "text/javascript"),
                 "/hierarchy-groups.js": ("hierarchy-groups.js", "text/javascript"),
                 "/scene-tool-drawer.js": ("scene-tool-drawer.js", "text/javascript"),
                 "/preset-batch.js": ("preset-batch.js", "text/javascript"),
                 "/draft-repeat.js": ("draft-repeat.js", "text/javascript"),
                 "/draft-group.js": ("draft-group.js", "text/javascript"),
                 "/draft-donor-group.js": ("draft-donor-group.js", "text/javascript"),
                 "/npc-script-comparison.js": ("npc-script-comparison.js", "text/javascript"),
                 "/npc-build-script.js": ("npc-build-script.js", "text/javascript"),
                 "/npc-dialogue.js": ("npc-dialogue.js", "text/javascript"),
                 "/npc-branches.js": ("npc-branches.js", "text/javascript"),
                 "/npc-model-selectors.js": ("npc-model-selectors.js", "text/javascript"),
                 "/npc-flags.js": ("npc-flags.js", "text/javascript"),
                 "/npc-facing.js": ("npc-facing.js", "text/javascript"),
                 "/npc-waits.js": ("npc-waits.js", "text/javascript"),
                 "/npc-movement.js": ("npc-movement.js", "text/javascript"),
                 "/npc-appearance.js": ("npc-appearance.js", "text/javascript"),
                 "/npc-donor-script.js": ("npc-donor-script.js", "text/javascript"),
                 "/npc-draft-inspector.js": ("npc-draft-inspector.js", "text/javascript"),
                 "/npc-presets.js": ("npc-presets.js", "text/javascript"),
                 "/npc-preset-metadata.js": ("npc-preset-metadata.js", "text/javascript"),
                 "/draft-review.js": ("draft-review.js", "text/javascript"),
                 "/script-operand-bundle.js": ("script-operand-bundle.js", "text/javascript"),
                 "/script-capture.js": ("script-capture.js", "text/javascript"),
                 "/animation-range.js": ("animation-range.js", "text/javascript"),
                 "/project-settings.js": ("project-settings.js", "text/javascript"),
                 "/asset-references.js": ("asset-references.js", "text/javascript"),
                 '/actor-animation.js': ('actor-animation.js', 'text/javascript'),
                 "/build-review.js": ("build-review.js", "text/javascript"),
                 "/build-history.js": ("build-history.js", "text/javascript"),
                 "/asset-build-history.js": ("asset-build-history.js", "text/javascript"),
                 "/project-copy.js": ("project-copy.js", "text/javascript"),
                 "/scene-selection-sets.js": ("scene-selection-sets.js", "text/javascript"),
                 "/scene-placement-group.js": ("scene-placement-group.js", "text/javascript"),
                 "/scene-placement-selection.js": ("scene-placement-selection.js", "text/javascript"),
                 "/environment-layout.js": ("environment-layout.js", "text/javascript"),
                 "/environment-rotation.js": ("environment-rotation.js", "text/javascript"),
                 "/environment-rotation-group.js": ("environment-rotation-group.js", "text/javascript"),
                 "/environment-rotation-math.js": ("environment-rotation-math.js", "text/javascript"),
                 "/environment-group.js": ("environment-group.js", "text/javascript"),
                 "/wall-viewport.js": ("wall-viewport.js", "text/javascript"),
                 "/wall-pattern.js": ("wall-pattern.js", "text/javascript"),
                 "/floor-picking.js": ("floor-picking.js", "text/javascript"),
                 "/floor-rectangle.js": ("floor-rectangle.js", "text/javascript"),
                 "/floor-heights.js": ("floor-heights.js", "text/javascript"),
                 "/floor-pattern.js": ("floor-pattern.js", "text/javascript"),
                 "/collision-rectangle.js": ("collision-rectangle.js", "text/javascript"),
                 "/model-normal-length.js": ("model-normal-length.js", "text/javascript"),
                 "/model-normal-users.js": ("model-normal-users.js", "text/javascript"),
                 "/normal-retarget.js": ("normal-retarget.js", "text/javascript"),
                 "/vertex-retarget.js": ("vertex-retarget.js", "text/javascript"),
                 "/model-vertex-users.js": ("model-vertex-users.js", "text/javascript"),
                 "/model-face-removal.js": ("model-face-removal.js", "text/javascript"),
                 "/model-topology-limits.js": ("model-topology-limits.js", "text/javascript"),
                 "/model-face-addition.js": ("model-face-addition.js", "text/javascript"),
                 "/model-vector-allocation.js": ("model-vector-allocation.js", "text/javascript"),
                 "/model-vertex-move.js": ("model-vertex-move.js", "text/javascript"),
                 "/model-vertex-marquee.js": ("model-vertex-marquee.js", "text/javascript"),
                 "/model-group-allocation.js": ("model-group-allocation.js", "text/javascript"),
                 "/model-object-allocation.js": ("model-object-allocation.js", "text/javascript"),
                 "/model-mesh-append.js": ("model-mesh-append.js", "text/javascript"),
                 "/model-mesh-settings.js": ("model-mesh-settings.js", "text/javascript"),
                 "/model-mesh-batch.js": ("model-mesh-batch.js", "text/javascript"),
                 "/model-preview-frame.js": ("model-preview-frame.js", "text/javascript"),
                 "/model-mesh-sources.js": ("model-mesh-sources.js", "text/javascript"),
                 "/model-mesh-origin.js": ("model-mesh-origin.js", "text/javascript"),
                 "/model-mesh-rotation.js": ("model-mesh-rotation.js", "text/javascript"),
                 "/model-allocation.js": ("model-allocation.js", "text/javascript"),
                 "/script-operand-files.js": ("script-operand-files.js", "text/javascript"),
                 "/asset-inspector.js": ("asset-inspector.js", "text/javascript"),
                 "/asset-record-export.js": ("asset-record-export.js", "text/javascript"),
                 "/environment-inspector.js": ("environment-inspector.js", "text/javascript"),
                 '/flag-resource.js': ('flag-resource.js', 'text/javascript'),
                 '/transition-resource.js': ('transition-resource.js', 'text/javascript'),
                 '/transition-graph-entry.js': ('transition-graph-entry.js', 'text/javascript'),
                 '/transition-arrival-preview.js': ('transition-arrival-preview.js', 'text/javascript'),
                 '/field-spatial.js': ('field-spatial.js', 'text/javascript'),
                 '/region-bounds.js': ('region-bounds.js', 'text/javascript'),
                 '/trigger-cells.js': ('trigger-cells.js', 'text/javascript'),
                 '/trigger-group.js': ('trigger-group.js', 'text/javascript'),
                 '/trigger-scripts.js': ('trigger-scripts.js', 'text/javascript'),
                 '/transition-graph.js': ('transition-graph.js', 'text/javascript'),
                 '/transition-graph-workspace.js': ('transition-graph-workspace.js', 'text/javascript'),
                 '/model-primitives.js': ('model-primitives.js', 'text/javascript'),
                 '/model-uv-workspace.js': ('model-uv-workspace.js', 'text/javascript'),
                 '/model-face-picking.js': ('model-face-picking.js', 'text/javascript'),
                 '/uv-rectangle.js': ('uv-rectangle.js', 'text/javascript'),
                 '/model-object-ownership.js': ('model-object-ownership.js', 'text/javascript'),
                 '/model-materials.js': ('model-materials.js', 'text/javascript'),
                 '/model-glb-material-selection.js': ('model-glb-material-selection.js', 'text/javascript'),
                 '/model-face-selection-view.js': ('model-face-selection-view.js', 'text/javascript'),
                 '/model-face-scene-selection.js': ('model-face-scene-selection.js', 'text/javascript'),
                 '/uv-texture-region.js': ('uv-texture-region.js', 'text/javascript'),
                 '/model-material-donor.js': ('model-material-donor.js', 'text/javascript'),
                 '/model-texture-binding.js': ('model-texture-binding.js', 'text/javascript'),
                 '/scene-animation.js': ('scene-animation.js', 'text/javascript'),
                 '/scene-limits.js': ('scene-limits.js', 'text/javascript'),
                 "/component-inspector.js": ("component-inspector.js", "text/javascript"),
                 "/inspector-component-filter.js": ("inspector-component-filter.js", "text/javascript"),
                 "/inspector-sections.js": ("inspector-sections.js", "text/javascript"),
                 "/script-bookmarks.js": ("script-bookmarks.js", "text/javascript"),
                 "/project-script-bookmarks.js": ("project-script-bookmarks.js", "text/javascript"),
                 "/script-inspector-navigation.js": ("script-inspector-navigation.js", "text/javascript"),
                 "/script-component-reset.js": ("script-component-reset.js", "text/javascript"),
                 "/script-owner-inspector.js": ("script-owner-inspector.js", "text/javascript"),
                 "/component-references.js": ("component-references.js", "text/javascript"),
                 "/model-user-selection.js": ("model-user-selection.js", "text/javascript"),
                 "/preset-files.js": ("preset-files.js", "text/javascript"),
                 "/actor-preset-review.js": ("actor-preset-review.js", "text/javascript"),
                 "/preset-animation.js": ("preset-animation.js", "text/javascript"),
                 "/actor-placement-batch.js": ("actor-placement-batch.js", "text/javascript"),
                 "/editor.css": ("editor.css", "text/css"),
                 "/scene-renderer.js": ("scene-renderer.js", "text/javascript"),
                 "/source-normal-view.js": ("source-normal-view.js", "text/javascript"),
                 "/asset-navigation.js": ("asset-navigation.js", "text/javascript"),
                 "/script-paths.js": ("script-paths.js", "text/javascript"),
                 "/script-flow-overview.js": ("script-flow-overview.js", "text/javascript"),
                 "/script-operands.js": ("script-operands.js", "text/javascript"),
                 "/script-branches.js": ("script-branches.js", "text/javascript"),
                 "/worldmap-authoring.js": ("worldmap-authoring.js", "text/javascript"),
                 "/worldmap-geometry.js": ("worldmap-geometry.js", "text/javascript"),
                 "/worldmap-placement-editor.js": ("worldmap-placement-editor.js", "text/javascript"),
                 "/worldmap-placement-gizmo.js": ("worldmap-placement-gizmo.js", "text/javascript"),
                 "/worldmap-placement-yaw.js": ("worldmap-placement-yaw.js", "text/javascript"),
                 "/worldmap-scene.js": ("worldmap-scene.js", "text/javascript"),
                 "/project-assets.js": ("project-assets.js", "text/javascript"),
                 "/script-facing.js": ("script-facing.js", "text/javascript"),
                 "/texture-usage.js": ("texture-usage.js", "text/javascript"),
                 "/runtime-review.js": ("runtime-review.js", "text/javascript"),
                 "/historical-actor-comparison.js": ("historical-actor-comparison.js", "text/javascript"),
                 "/animation-glb.js": ("animation-glb.js", "text/javascript"),
                 "/animation-glb-clips.js": ("animation-glb-clips.js", "text/javascript"),
                 "/animation-glb-mapping.js": ("animation-glb-mapping.js", "text/javascript"),
                 "/animation-glb-sampling.js": ("animation-glb-sampling.js", "text/javascript"),
                 "/animation-sources.js": ("animation-sources.js", "text/javascript"),
                 "/mesh-source-library.js": ("mesh-source-library.js", "text/javascript"),
                 "/model-source-library.js": ("model-source-library.js", "text/javascript"),
                 "/animation-source-library.js": ("animation-source-library.js", "text/javascript"),
                 "/actor-animation-glb-target.js": ("actor-animation-glb-target.js", "text/javascript"),
                 "/animation-allocation.js": ("animation-allocation.js", "text/javascript"),
                 "/animation-record-library.js": ("animation-record-library.js", "text/javascript"),
                 "/retained-animation-assets.js": ("retained-animation-assets.js", "text/javascript"),
                 "/animation-record-edit.js": ("animation-record-edit.js", "text/javascript"),
                 "/animation-record-glb.js": ("animation-record-glb.js", "text/javascript"),
                 "/model-glb.js": ("model-glb.js", "text/javascript"),
                 "/model-glb-mapping.js": ("model-glb-mapping.js", "text/javascript"),
                 "/model-sources.js": ("model-sources.js", "text/javascript"),
                 "/texture-png.js": ("texture-png.js", "text/javascript"),
                 "/texture-comparison.js": ("texture-comparison.js", "text/javascript"),
                 "/texture-resize.js": ("texture-resize.js", "text/javascript"),
                 "/texture-image-conversion.js": ("texture-image-conversion.js", "text/javascript"),
                 "/texture-upload-map.js": ("texture-upload-map.js", "text/javascript"),
                 "/texture-glb-dependencies.js": ("texture-glb-dependencies.js", "text/javascript"),
                 "/texture-slots.js": ("texture-slots.js", "text/javascript"),
                 "/texture-source-retention.js": ("texture-source-retention.js", "text/javascript")}
        if route not in files:
            self._json(404, {"error": "Unknown editor route"})
            return
        name, content_type = files[route]
        path = self.server.editor_root / name
        if not path.is_file():
            self._json(503, {"error": "Editor frontend is not installed"})
            return
        self._send(200, path.read_bytes(), content_type + "; charset=utf-8")

    def do_POST(self) -> None:
        if not self._trusted_request():
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            request_limit = 2 * 1024 * 1024 if urlsplit(self.path).path in ("/api/texture-replacement", "/api/text-json-preview", "/api/text-json-import") else 32768
            if urlsplit(self.path).path in ('/api/model-face-addition-preview', '/api/model-face-addition'):
                request_limit = 256 * 1024
            if urlsplit(self.path).path in ('/api/model-material-preview', '/api/model-material-scene-preview', '/api/model-material-apply'):
                request_limit = 1024 * 1024
            if urlsplit(self.path).path in ('/api/model-shape-replacement', '/api/animation-record-replacement', '/api/animation-record-preview', '/api/animation-file-pose-preview'):
                request_limit = 6 * 1024 * 1024
            if urlsplit(self.path).path in ('/api/model-obj-replacement', '/api/model-json-replacement', '/api/model-file-preview', '/api/model-file-scene-preview', '/api/texture-json-replacement', '/api/texture-file-preview', '/api/texture-file-scene-preview'):
                request_limit = 24 * 1024 * 1024
            if urlsplit(self.path).path in ('/api/texture-slot-review','/api/texture-slot-pixels','/api/texture-slot-apply','/api/texture-slot-edit-source','/api/texture-slot-edit-review','/api/texture-slot-edit-pixels','/api/texture-slot-edit-apply'):
                request_limit = 2 * 1024 * 1024
            if urlsplit(self.path).path in ('/api/texture-slot-review','/api/texture-slot-pixels','/api/texture-slot-apply','/api/texture-slot-edit-review','/api/texture-slot-edit-pixels','/api/texture-slot-edit-apply'):
                request_limit = 68 * 1024 * 1024
            if urlsplit(self.path).path in ('/api/texture-placement','/api/texture-image-convert','/api/texture-slot-source-review','/api/texture-slot-source-apply'):
                request_limit = 68 * 1024 * 1024
            if urlsplit(self.path).path in ('/api/texture-png-preview','/api/texture-png-pixels-preview','/api/texture-png-scene-preview','/api/texture-png-import'):
                request_limit = 68 * 1024 * 1024
            if urlsplit(self.path).path in ('/api/animation-glb-preview', '/api/animation-glb-pose-preview', '/api/animation-glb-import', '/api/model-glb-preview', '/api/model-glb-material-links','/api/model-glb-material-faces', '/api/model-glb-pose-preview', '/api/model-glb-import', '/api/model-mesh-batch-preview', '/api/model-mesh-batch', '/api/model-mesh-batch-scene-preview', '/api/model-mesh-file','/api/model-mesh-scenes','/api/texture-glb-images','/api/texture-glb-image','/api/texture-glb-dependencies','/api/texture-glb-retain-review','/api/texture-glb-retain', '/api/model-mesh-append-preview', '/api/model-mesh-append', '/api/model-mesh-append-scene-preview'):
                request_limit = 44 * 1024 * 1024
            if urlsplit(self.path).path in ('/api/animation-record-glb-review','/api/animation-record-glb-pose','/api/animation-record-glb-import'):
                request_limit = 44 * 1024 * 1024
            if not 0 < length <= request_limit or self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                raise ProjectError(f"Commands require a JSON object of at most {request_limit} bytes")
            content = self.rfile.read(length)
            if len(content) != length:
                raise ProjectError("Incomplete command request body")
            body = json.loads(content)
            if not isinstance(body, dict):
                raise ProjectError("Command body must be an object")
            with self.server.command_lock:
                route = urlsplit(self.path).path
                if route == '/api/project-assets':
                    if body:
                        raise ProjectError('Project resource discovery accepts only an empty object')
                    from .project_assets import inspect
                    self._json(200, inspect(self.server.project))
                    return
                if route == '/api/worldmap-geometry':
                    if set(body) != {'scene', 'source_key'}:
                        raise ProjectError('World ground inspection accepts only scene and source_key')
                    from .worldmap_geometry import inspect
                    self._json(200, inspect(self.server.project, body['scene'], body['source_key']))
                    return
                if route in ('/api/worldmap-placements','/api/worldmap-placement-review'):
                    expected={'scene','source_key'} | ({'record_id','values','shared_record'} if route.endswith('-review') else set())
                    if set(body)!=expected:
                        raise ProjectError('World placement inspection requires exact source scope and reviewed transform fields')
                    from .worldmap_placements import snapshot,review
                    result=(review(self.server.project,body['scene'],body['source_key'],body['record_id'],body['values'],body['shared_record'])[0]
                        if route.endswith('-review') else snapshot(self.server.project,body['scene'],body['source_key']))
                    self._json(200,result)
                    return
                if route == '/api/export/worldmap':
                    selected = body.get('scope') == 'selected'
                    expected = {'scene', 'source_key', 'scope'} | ({'entity_id'} if selected else set())
                    if set(body) != expected:
                        raise ProjectError('World source export requires scene, source key and scope; only selected scope accepts an entity identity')
                    from .worldmap_export import export
                    self._json(200, export(self.server.project, body['scene'], body['source_key'],
                                           body['scope'], body.get('entity_id')))
                    return
                if route == '/api/export/worldmap-placements':
                    if set(body)!={'scene','source_key','proposal'}:
                        raise ProjectError('World placement export requires scene, source identity and optional reviewed proposal')
                    from .worldmap_placement_export import export
                    self._json(200,export(self.server.project,body['scene'],body['source_key'],body['proposal']))
                    return
                if route in ('/api/worldmap-authoring', '/api/worldmap-authoring-review'):
                    expected = set() if route == '/api/worldmap-authoring' else {'entity_id', 'values'}
                    if set(body) != expected:
                        raise ProjectError('World-map authoring requires the exact source row and values')
                    from .worldmap_authoring import snapshot, review
                    self._json(200, snapshot(self.server.project) if not body else
                               review(self.server.project, body['entity_id'], body['values'])[0])
                    return
                if route in ('/api/script-branches', '/api/script-branch-review'):
                    expected = {'entity'} if route == '/api/script-branches' else {'entity', 'branch_id', 'value'}
                    if set(body) != expected or not isinstance(body['entity'], str) or not body['entity']:
                        raise ProjectError('Script branch inspection requires exact owner and destination fields')
                    from .script_branches import snapshot, review
                    self._json(200, snapshot(self.server.project, body['entity']) if route == '/api/script-branches' else review(self.server.project, body['entity'], body['branch_id'], body['value'])[0])
                    return
                if route == '/api/scene-catalog':
                    if set(body) != {'disc', 'offset', 'prefix'} or not isinstance(body['disc'], str) or not body['disc'].strip() or type(body['offset']) is not int or not 0 <= body['offset'] <= 65536 or not isinstance(body['prefix'], str) or len(body['prefix']) > 64:
                        raise ProjectError('Scene catalog requires a disc path, bounded integer offset and name prefix')
                    from importer.pipeline import list_scenes
                    self._json(200, list_scenes(body['disc'], offset=body['offset'], limit=16, prefix=body['prefix']))
                    return
                if route == '/api/texture-file-scene-preview':
                    if set(body)!={'asset_id','format','palette_index','content_base64','candidate_sha256','source_key'} or not isinstance(body['asset_id'],str) or not isinstance(body['content_base64'],str) or len(body['content_base64'])>22369624:
                        raise ProjectError('Texture scene proposal requires inspected file/hash, palette and source key')
                    from .scene_preview import source_key
                    key=source_key(self.server.project)
                    if not key or key!=body['source_key']:
                        raise ProjectError('Scene changed; refresh before inspecting a texture file')
                    try:
                        content=base64.b64decode(body['content_base64'],validate=True)
                    except ValueError as exc:
                        raise ProjectError('Texture scene proposal requires valid base64') from exc
                    candidate,report=self.server.project._prepare_texture_file(body['asset_id'],content,body['format'],body['palette_index'])
                    if report['candidate_sha256']!=body['candidate_sha256']:
                        raise ProjectError('Texture file differs from the inspected candidate hash')
                    self._json(200,self.server.scene_texture_proposal(body['asset_id'],candidate,report,key))
                    return
                if route == '/api/texture-file-preview':
                    if set(body) != {'asset_id','format','palette_index','content_base64'} or not isinstance(body['asset_id'],str) or not isinstance(body['content_base64'],str) or len(body['content_base64']) > 22369624:
                        raise ProjectError('Texture preview requires identity, format, palette and bounded file bytes')
                    try:
                        content = base64.b64decode(body['content_base64'],validate=True)
                    except ValueError as exc:
                        raise ProjectError('Texture preview requires valid base64') from exc
                    self._json(200,self.server.project.preview_texture_file(body['asset_id'],content,body['format'],body['palette_index']))
                    return
                if route == '/api/texture-json-source':
                    if set(body) != {'asset_id','layer'} or not isinstance(body['asset_id'],str):
                        raise ProjectError('Texture JSON download requires texture identity and layer')
                    self._json(200,self.server.project.texture_json_source(body['asset_id'],body['layer']))
                    return
                if route == '/api/texture-json-replacement':
                    if set(body) != {'asset_id','json_base64'} or not isinstance(body['asset_id'],str) or not isinstance(body['json_base64'],str) or len(body['json_base64']) > 22369624:
                        raise ProjectError('Texture JSON import requires identity and at most 16 MiB of JSON')
                    try:
                        content = base64.b64decode(body['json_base64'],validate=True)
                    except ValueError as exc:
                        raise ProjectError('Texture JSON requires valid base64') from exc
                    self.server.project.set_texture_json(body['asset_id'],content)
                    self._json(200,self.server.state())
                    return
                if route == '/api/texture-pixel-source':
                    if set(body) != {'asset_id','palette_index','x','y'} or not isinstance(body['asset_id'], str):
                        raise ProjectError('Pixel inspection requires texture, palette and pixel coordinates')
                    self._json(200, self.server.project.texture_pixel_source(body['asset_id'], body['palette_index'], body['x'], body['y']))
                    return
                if route == '/api/texture-pixel-index':
                    if set(body) != {'asset_id','x','y','palette_entry','expected_sha256'} or not isinstance(body['asset_id'], str):
                        raise ProjectError('Pixel authoring requires texture, coordinates, palette entry and inspected hash')
                    self.server.project.set_texture_pixel_index(body['asset_id'], body['x'], body['y'], body['palette_entry'], body['expected_sha256'])
                    self._json(200, self.server.state())
                    return
                if route == '/api/texture-index-copy':
                    if set(body) != {'asset_id','source_x','source_y','x','y','width','height','expected_sha256'} or not isinstance(body['asset_id'],str):
                        raise ProjectError('Rectangle copy requires texture, source/destination bounds and inspected hash')
                    self.server.project.copy_texture_index_rectangle(body['asset_id'],body['source_x'],body['source_y'],body['x'],body['y'],body['width'],body['height'],body['expected_sha256'])
                    self._json(200,self.server.state())
                    return
                if route == '/api/texture-index-rectangle':
                    if set(body) != {'asset_id','x','y','width','height','palette_entry','expected_sha256'} or not isinstance(body['asset_id'],str):
                        raise ProjectError('Rectangle fill requires texture, image bounds, index and inspected hash')
                    self.server.project.set_texture_index_rectangle(body['asset_id'],body['x'],body['y'],body['width'],body['height'],body['palette_entry'],body['expected_sha256'])
                    self._json(200,self.server.state())
                    return
                if route == '/api/texture-palette-source':
                    if set(body) != {'asset_id','palette_index'} or not isinstance(body['asset_id'], str):
                        raise ProjectError('Palette inspection requires texture identity and palette index')
                    self._json(200, self.server.project.texture_palette_source(body['asset_id'], body['palette_index']))
                    return
                if route == '/api/texture-palette-word':
                    if set(body) != {'asset_id','palette_index','entry_index','word','expected_sha256'} or not isinstance(body['asset_id'], str):
                        raise ProjectError('Palette authoring requires texture, palette/entry, word and inspected hash')
                    self.server.project.set_texture_palette_word(body['asset_id'], body['palette_index'], body['entry_index'], body['word'], body['expected_sha256'])
                    self._json(200, self.server.state())
                    return
                if route == '/api/model-object-scene-preview':
                    if set(body) - {'all_instances'} != {'asset_id','object_index','operation','values','expected_sha256','entity_id','source_key'} or type(body.get('all_instances',False)) is not bool or not isinstance(body['asset_id'],str) or not isinstance(body['entity_id'],str):
                        raise ProjectError('Scene object preview requires inspected operation, instance and scene source key')
                    from .scene_preview import source_key
                    key = source_key(self.server.project)
                    if not key or key != body['source_key']:
                        raise ProjectError('Scene changed; refresh before inspecting a proposed shape')
                    replacement, report = self.server.project._prepare_model_object(body['asset_id'],body['object_index'],body['operation'],body['values'],body['expected_sha256'])
                    report = self.server.scene_shape_proposal(body['asset_id'],body['entity_id'],replacement,report,key,body.get('all_instances',False))
                    self._json(200,report)
                    return
                if route in ('/api/material-texture-catalog','/api/material-texture-source'):
                    fields={'source_key'} if route.endswith('catalog') else {'source_key','asset_id','palette_index'}
                    if set(body)!=fields:raise ProjectError('Material texture inspection requires exact source-qualified fields')
                    from .model_texture_binding import catalog,source
                    self._json(200,catalog(self.server.project,body['source_key']) if route.endswith('catalog') else source(self.server.project,body['asset_id'],body['source_key'],body['palette_index']))
                    return
                if route == '/api/model-material-donor-models':
                    if set(body) != {'source_key'} or not isinstance(body['source_key'], str):
                        raise ProjectError('Material binding catalog requires a source key only')
                    from .model_materials import donor_models
                    self._json(200, donor_models(self.server.project, body['source_key']))
                    return
                if route in ('/api/model-texture-assignment-preview','/api/model-texture-assignment-apply','/api/model-texture-assignment-scene-preview'):
                    expected={'asset_id','primitive_edits','material_edits','expected_sha256','source_key'}
                    if route.endswith('-apply') or route.endswith('-scene-preview'):expected.add('review_key')
                    if route.endswith('-scene-preview'):expected.update(('entity_id','all_instances'))
                    if set(body)!=expected or any(not isinstance(body[k],str) for k in ('asset_id','expected_sha256','source_key')):
                        raise ProjectError('Combined model authoring requires exact source identity and both native drafts')
                    from .model_texture_assignment import prepare,apply,reviewed,scene_binding
                    args=(self.server.project,body['asset_id'],body['primitive_edits'],body['material_edits'],body['expected_sha256'],body['source_key'])
                    if route.endswith('-apply'):
                        report=apply(*args,body['review_key'])
                        self._json(200,dict(self.server.state(),model_texture_assignment_report=report))
                    elif route.endswith('-scene-preview'):
                        if not isinstance(body['entity_id'],str) or type(body['all_instances']) is not bool:
                            raise ProjectError('Combined scene review requires a qualified instance and explicit scope')
                        candidate,report=reviewed(*args,body['review_key'])
                        binding=scene_binding(self.server.project,body['asset_id'],candidate)
                        report=self.server.scene_shape_proposal(body['asset_id'],body['entity_id'],candidate,report,body['source_key'],body['all_instances'],material_content=True,prepared_binding=binding)
                        from .model_materials import _bounded
                        _bounded(report,'Combined scene model preview')
                        self._json(200,report)
                    else:
                        _,report=prepare(*args)
                        asset=self.server.project.assets.records[body['asset_id']]
                        report['preview']=self.server.model_preview(asset,prepared=report['preview'])
                        report['current_preview']=self.server.model_preview(asset,prepared=report['current_preview'])
                        from .model_materials import _bounded
                        _bounded(report,'Combined model preview')
                        from .scene_preview import source_key
                        if source_key(self.server.project)!=body['source_key']:
                            raise ProjectError('Scene changed during combined model preview')
                        self._json(200,report)
                    return
                if route == '/api/model-material-source':
                    if set(body) != {'asset_id'} or not isinstance(body['asset_id'], str):
                        raise ProjectError('Material inspection requires a model identity only')
                    from .model_materials import snapshot
                    self._json(200, snapshot(self.server.project, body['asset_id']))
                    return
                if route in ('/api/model-material-preview', '/api/model-material-scene-preview', '/api/model-material-apply'):
                    expected = {'asset_id', 'expected_sha256', 'source_key', 'edits'}
                    if route != '/api/model-material-preview':
                        expected.add('review_key')
                    if route == '/api/model-material-scene-preview':
                        expected.update(('entity_id', 'all_instances'))
                    if (set(body) != expected or not isinstance(body['asset_id'], str) or
                            not isinstance(body['expected_sha256'], str) or not isinstance(body['source_key'], str)):
                        raise ProjectError('Material authoring requires exact model, source hashes and semantic edits')
                    from .model_materials import apply, prepare, reviewed, _bounded
                    args = (self.server.project, body['asset_id'], body['edits'], body['expected_sha256'], body['source_key'])
                    if route == '/api/model-material-apply':
                        report = apply(*args, body['review_key'])
                        self._json(200, dict(self.server.state(), model_material_report=report))
                        return
                    if route == '/api/model-material-scene-preview':
                        if not isinstance(body['entity_id'], str) or type(body['all_instances']) is not bool:
                            raise ProjectError('Material scene inspection requires a qualified instance and explicit scope')
                        replacement, report = reviewed(*args, body['review_key'])
                        report = self.server.scene_shape_proposal(body['asset_id'], body['entity_id'], replacement,
                            report, body['source_key'], body['all_instances'], material_content=True)
                    else:
                        replacement, report = prepare(*args)
                        asset = self.server.project.assets.records[body['asset_id']]
                        for key in ('preview', 'current_preview'):
                            report[key].update(semantic_id=asset['semantic_id'], source_record=asset['source_record'],
                                               representation='model-material-proposal')
                            report[key] = self.server.model_preview(asset, prepared=report[key])
                    _bounded(report, 'Model material preview')
                    from .scene_preview import source_key
                    if source_key(self.server.project) != report['project_source_key']:
                        raise ProjectError('Scene changed while preparing the material preview')
                    self._json(200, report)
                    return
                if route == '/api/model-primitive-source':
                    if set(body) != {'asset_id'} or not isinstance(body['asset_id'], str):
                        raise ProjectError('Face inspection requires a model identity only')
                    self._json(200, self.server.project.model_primitive_source(body['asset_id']))
                    return
                if route in ('/api/model-primitive-preview', '/api/model-primitives', '/api/model-primitive-scene-preview'):
                    expected = {'asset_id', 'expected_sha256', 'source_key', 'edits'}
                    if route == '/api/model-primitives':
                        expected.add('proposed_sha256')
                    if route == '/api/model-primitive-scene-preview':
                        expected.update(('proposed_sha256', 'entity_id', 'all_instances'))
                    if (set(body) != expected or not isinstance(body['asset_id'], str)
                            or not isinstance(body['expected_sha256'], str) or not isinstance(body['source_key'], str)):
                        raise ProjectError('Face authoring requires exact model, inspected hashes and packet edits')
                    project = self.server.project
                    if route == '/api/model-primitives':
                        project.set_model_primitives(body['asset_id'], body['edits'], body['expected_sha256'],
                                                     body['source_key'], body['proposed_sha256'])
                        self._json(200, self.server.state())
                        return
                    replacement, report = project._prepare_model_primitives(body['asset_id'], body['edits'],
                                                                           body['expected_sha256'], body['source_key'])
                    if route == '/api/model-primitive-scene-preview':
                        if (not isinstance(body['entity_id'], str) or type(body['all_instances']) is not bool
                                or body['proposed_sha256'] != report['proposed_sha256']):
                            raise ProjectError('Scene face proposal differs from the reviewed model or instance')
                        report = self.server.scene_shape_proposal(body['asset_id'], body['entity_id'], replacement,
                                                                 report, body['source_key'], body['all_instances'])
                    else:
                        asset = project.assets.records[body['asset_id']]
                        for key in ('preview', 'current_preview'):
                            report[key].update(semantic_id=asset['semantic_id'], source_record=asset['source_record'])
                            report[key] = self.server.model_preview(asset, prepared=report[key])
                    self._json(200, report)
                    return
                if route in ('/api/model-vector-preview', '/api/model-vector-scene-preview'):
                    fields = {'asset_id','object_index','kind','vector_index','values','expected_sha256'}
                    scene_request = route.endswith('scene-preview')
                    if scene_request:fields.update({'entity_id','source_key'})
                    if (set(body) - ({'all_instances'} if scene_request else set()) != fields
                            or not isinstance(body['asset_id'],str)
                            or scene_request and (not isinstance(body['entity_id'],str) or type(body.get('all_instances',False)) is not bool)):
                        raise ProjectError('Vector preview requires exact model/object/kind/vector, XYZ, hash and optional scene instance context')
                    if scene_request:
                        from .scene_preview import source_key
                        if source_key(self.server.project) != body['source_key']:
                            raise ProjectError('Scene changed; refresh before inspecting the vertex draft')
                    candidate,report = self.server.project.preview_model_vector(body['asset_id'],body['object_index'],body['kind'],body['vector_index'],body['values'],body['expected_sha256'])
                    if scene_request:
                        report = self.server.scene_shape_proposal(body['asset_id'],body['entity_id'],candidate,report,body['source_key'],body.get('all_instances',False))
                    else:
                        asset = self.server.project.assets.records[body['asset_id']]
                        for key in ('preview','current_preview'):report[key] = self.server.model_preview(asset,prepared=report[key])
                    self._json(200,report)
                    return
                if route == '/api/model-object-preview':
                    if set(body) != {'asset_id','object_index','operation','values','expected_sha256'} or not isinstance(body['asset_id'],str):
                        raise ProjectError('Object preview requires model, object, operation, values and inspected hash')
                    report = self.server.project.preview_model_object(body['asset_id'],body['object_index'],body['operation'],body['values'],body['expected_sha256'])
                    asset = self.server.project.assets.records[body['asset_id']]
                    for key in ('preview', 'current_preview'):
                        report[key] = self.server.model_preview(asset, prepared=report[key])
                    self._json(200,report)
                    return
                if route == '/api/model-object-rotation':
                    if set(body) != {'asset_id','object_index','axis','quarter_turns','expected_sha256'} or not isinstance(body['asset_id'],str):
                        raise ProjectError('Object rotation requires model, object, axis, quarter turns and inspected hash')
                    self.server.project.rotate_model_object(body['asset_id'],body['object_index'],body['axis'],body['quarter_turns'],body['expected_sha256'])
                    self._json(200,self.server.state())
                    return
                if route == '/api/model-object-scale':
                    if set(body) != {'asset_id','object_index','percent','expected_sha256'} or not isinstance(body['asset_id'],str):
                        raise ProjectError('Object scale requires model, object, percent and inspected hash')
                    self.server.project.scale_model_object(body['asset_id'],body['object_index'],body['percent'],body['expected_sha256'])
                    self._json(200,self.server.state())
                    return
                if route == '/api/model-object-normal-length':
                    if set(body) != {'asset_id','object_index','length','expected_sha256'} or not isinstance(body['asset_id'],str):
                        raise ProjectError('Normal rescaling requires model, object, length and inspected hash')
                    self.server.project.rescale_model_normals(body['asset_id'],body['object_index'],body['length'],body['expected_sha256'])
                    self._json(200,self.server.state())
                    return
                if route == '/api/model-object-normal-references':
                    if set(body) != {'asset_id','object_index','from_index','to_index','expected_sha256','proposed_sha256'} or not isinstance(body['asset_id'],str):
                        raise ProjectError('Normal retargeting requires exact model/object/from/to and reviewed hashes')
                    self.server.project.retarget_model_normals(body['asset_id'],body['object_index'],body['from_index'],body['to_index'],body['expected_sha256'],body['proposed_sha256'])
                    self._json(200,self.server.state())
                    return
                if route == '/api/model-normal-users':
                    if set(body) != {'asset_id','object_index','normal_index','expected_sha256','source_key'}:
                        raise ProjectError('Normal users require model, object, vector, inspected hash and source key only')
                    from .model_normal_users import inspect
                    self._json(200,inspect(self.server.project,body['asset_id'],body['object_index'],body['normal_index'],body['expected_sha256'],body['source_key']))
                    return
                if route == '/api/model-object-vertex-references':
                    if set(body) != {'asset_id','object_index','from_index','to_index','expected_sha256','proposed_sha256'} or not isinstance(body['asset_id'],str):
                        raise ProjectError('Vertex retargeting requires exact model/object/from/to and reviewed hashes')
                    self.server.project.retarget_model_vertices(body['asset_id'],body['object_index'],body['from_index'],body['to_index'],body['expected_sha256'],body['proposed_sha256'])
                    self._json(200,self.server.state())
                    return
                if route == '/api/model-allocation-source':
                    if set(body) != {'asset_id','source_key'} or not isinstance(body['asset_id'], str) or not isinstance(body['source_key'], str):
                        raise ProjectError('Model allocation inspection requires model and source key only')
                    from .model_allocation import source
                    self._json(200,source(self.server.project,body['asset_id'],body['source_key']))
                    return
                if route in ('/api/model-mesh-batch-preview','/api/model-mesh-batch','/api/model-mesh-batch-scene-preview'):
                    fields={'asset_id','content_base64','mappings','expected_sha256','source_key'}
                    if 'replace_objects' in body:fields.add('replace_objects')
                    if 'material_colors' in body:fields.add('material_colors')
                    if 'uv_set' in body:fields.add('uv_set')
                    if 'source_scale' in body:fields.add('source_scale')
                    if 'source_offset' in body:fields.add('source_offset')
                    if 'source_rotation' in body:fields.add('source_rotation')
                    if 'scene_index' in body:fields.add('scene_index')
                    if route!='/api/model-mesh-batch-preview':fields.add('review_key')
                    if route.endswith('-scene-preview'):fields.update(('proposed_sha256','entity_id','all_instances'))
                    if set(body)!=fields or any(type(body.get(choice,False)) is not bool for choice in ('material_colors','replace_objects')) or not isinstance(body['asset_id'],str) or not 0<len(body['asset_id'])<=512 or any(not isinstance(body[key],str) or len(body[key])!=64 or any(c not in '0123456789abcdef' for c in body[key]) for key in fields & {'source_key','expected_sha256','review_key','proposed_sha256'}):
                        raise ProjectError('Mesh donor mapping requires exact model, source and review identities')
                    if not isinstance(body['content_base64'],str) or not 0<len(body['content_base64'])<=44739244:
                        raise ProjectError('Mesh donor mapping requires bounded GLB bytes')
                    try:payload=base64.b64decode(body['content_base64'],validate=True)
                    except ValueError as exc:raise ProjectError('Mesh donor mapping requires valid base64') from exc
                    if not 28<=len(payload)<=32*1024*1024:raise ProjectError('Mesh donor mapping GLB exceeds byte bounds')
                    from . import model_mesh_batch
                    args=(body['asset_id'],payload,body['mappings'],body['expected_sha256'],body['source_key'])
                    if route=='/api/model-mesh-batch':
                        model_mesh_batch.apply(self.server.project,*args,review_key=body['review_key'],material_colors=body.get('material_colors',False),scene_index=body.get('scene_index'),uv_set=body.get('uv_set',0),source_scale=body.get('source_scale',1),source_offset=body.get('source_offset',(0,0,0)),source_rotation=body.get('source_rotation',(0,0,0)),replace_objects=body.get('replace_objects',False))
                        self._json(200,self.server.state())
                    else:
                        candidate,binding,report=model_mesh_batch.prepare(self.server.project,*args,material_colors=body.get('material_colors',False),scene_index=body.get('scene_index'),uv_set=body.get('uv_set',0),source_scale=body.get('source_scale',1),source_offset=body.get('source_offset',(0,0,0)),source_rotation=body.get('source_rotation',(0,0,0)),replace_objects=body.get('replace_objects',False))
                        if route.endswith('-scene-preview'):
                            if type(body['all_instances']) is not bool or not isinstance(body['entity_id'],str) or not 0<len(body['entity_id'])<=512 or report['review_key']!=body['review_key'] or report['proposed_sha256']!=body['proposed_sha256']:
                                raise ProjectError('Mesh donor mapping scene proposal differs from Review')
                            self._json(200,self.server.scene_shape_proposal(body['asset_id'],body['entity_id'],candidate,report,body['source_key'],body['all_instances'],prepared_binding=binding))
                        else:self._json(200,report)
                    return
                if route in ('/api/model-mesh-file','/api/model-mesh-scenes'):
                    if (not {'content_base64'}<=set(body) or not set(body)<={'content_base64','scene_index','source_scale','source_offset','source_rotation'}) or not isinstance(body['content_base64'],str) or not 0<len(body['content_base64'])<=44739244:
                        raise ProjectError('Mesh file inspection requires bounded GLB bytes and an optional source scene')
                    if route=='/api/model-mesh-scenes' and set(body)!={'content_base64'}:
                        raise ProjectError('Scene catalog requires file bytes only; it does not qualify geometry')
                    try:payload=base64.b64decode(body['content_base64'],validate=True)
                    except ValueError as exc:raise ProjectError('Mesh file requires valid base64') from exc
                    if not 28<=len(payload)<=32*1024*1024:raise ProjectError('Mesh file exceeds its byte bounds')
                    if route=='/api/model-mesh-scenes':
                        from importer.model_mesh_scene import inspect_source_scenes
                        self._json(200,inspect_source_scenes(payload))
                    else:
                        from importer.model_mesh_append import inspect_append_mesh
                        self._json(200,inspect_append_mesh(payload,scene_index=body.get('scene_index'),source_scale=body.get('source_scale',1),source_offset=body.get('source_offset',(0,0,0)),source_rotation=body.get('source_rotation',(0,0,0))))
                    return
                if route=='/api/model-mesh-append-source':
                    if set(body)!={'asset_id','source_key'} or not isinstance(body['asset_id'],str) or not isinstance(body['source_key'],str):
                        raise ProjectError('Mesh source requires exact model and source identities')
                    from .model_mesh_append import source
                    self._json(200,source(self.server.project,body['asset_id'],body['source_key']))
                    return
                if route in ('/api/model-mesh-append-preview','/api/model-mesh-append','/api/model-mesh-append-scene-preview'):
                    fields={'asset_id','content_base64','donor_face_id','expected_sha256','source_key'}
                    if 'new_group' in body:fields.add('new_group')
                    if 'replace_group' in body:fields.add('replace_group')
                    if 'replace_object' in body:fields.add('replace_object')
                    if 'preserve_primitives' in body:fields.add('preserve_primitives')
                    if 'primitive_index' in body:fields.add('primitive_index')
                    if 'material_colors' in body:fields.add('material_colors')
                    if 'uv_set' in body:fields.add('uv_set')
                    if 'source_scale' in body:fields.add('source_scale')
                    if 'source_offset' in body:fields.add('source_offset')
                    if 'source_rotation' in body:fields.add('source_rotation')
                    if 'scene_index' in body:fields.add('scene_index')
                    if route=='/api/model-mesh-append':fields.add('review_key')
                    if route=='/api/model-mesh-append-scene-preview':fields.update(('review_key','proposed_sha256','entity_id','all_instances'))
                    if (set(body)!=fields or any(type(body.get(choice,False)) is not bool for choice in ('new_group','replace_group','replace_object','preserve_primitives','material_colors')) or not isinstance(body['asset_id'],str) or not 0<len(body['asset_id'])<=512
                            or not isinstance(body['donor_face_id'],str) or not 0<len(body['donor_face_id'])<=512
                            or any(not isinstance(body[key],str) or len(body[key])!=64 or any(c not in '0123456789abcdef' for c in body[key])
                                   for key in fields & {'source_key','expected_sha256','review_key','proposed_sha256'})):
                        raise ProjectError('Mesh append requires exact source, donor, model and review identities')
                    encoded=body['content_base64']
                    if not isinstance(encoded,str) or not 0<len(encoded)<=44739244:
                        raise ProjectError('Mesh append requires GLB bytes of at most 32 MiB')
                    try:payload=base64.b64decode(encoded,validate=True)
                    except ValueError as exc:raise ProjectError('Mesh append requires valid base64') from exc
                    if not 28<=len(payload)<=32*1024*1024:raise ProjectError('Mesh append GLB exceeds its byte bounds')
                    args=(body['asset_id'],payload,body['donor_face_id'],body['expected_sha256'],body['source_key'])
                    if route=='/api/model-mesh-append-scene-preview':
                        if not isinstance(body['entity_id'],str) or not 0<len(body['entity_id'])<=512 or type(body['all_instances']) is not bool:
                            raise ProjectError('Mesh scene inspection requires an exact instance and boolean scope')
                        from .model_mesh_append import prepare
                        candidate,binding,report=prepare(self.server.project,*args,new_group=body.get('new_group',False),replace_group=body.get('replace_group',False),replace_object=body.get('replace_object',False),preserve_primitives=body.get('preserve_primitives',False),primitive_index=body.get('primitive_index'),material_colors=body.get('material_colors',False),scene_index=body.get('scene_index'),uv_set=body.get('uv_set',0),source_scale=body.get('source_scale',1),source_offset=body.get('source_offset',(0,0,0)),source_rotation=body.get('source_rotation',(0,0,0)))
                        if report['review_key']!=body['review_key'] or report['proposed_sha256']!=body['proposed_sha256']:
                            raise ProjectError('Mesh scene proposal differs from the reviewed file or mode')
                        self._json(200,self.server.scene_shape_proposal(body['asset_id'],body['entity_id'],candidate,report,body['source_key'],body['all_instances'],prepared_binding=binding))
                    elif route.endswith('-preview'):
                        from .model_mesh_append import review
                        self._json(200,review(self.server.project,*args,new_group=body.get('new_group',False),replace_group=body.get('replace_group',False),replace_object=body.get('replace_object',False),preserve_primitives=body.get('preserve_primitives',False),primitive_index=body.get('primitive_index'),material_colors=body.get('material_colors',False),scene_index=body.get('scene_index'),uv_set=body.get('uv_set',0),source_scale=body.get('source_scale',1),source_offset=body.get('source_offset',(0,0,0)),source_rotation=body.get('source_rotation',(0,0,0))))
                    else:
                        self.server.project.apply_model_mesh_append(*args,body['review_key'],new_group=body.get('new_group',False),replace_group=body.get('replace_group',False),replace_object=body.get('replace_object',False),preserve_primitives=body.get('preserve_primitives',False),primitive_index=body.get('primitive_index'),material_colors=body.get('material_colors',False),scene_index=body.get('scene_index'),uv_set=body.get('uv_set',0),source_scale=body.get('source_scale',1),source_offset=body.get('source_offset',(0,0,0)),source_rotation=body.get('source_rotation',(0,0,0)))
                        self._json(200,self.server.state())
                    return
                if route in ('/api/model-object-allocation-source','/api/model-object-allocation-preview','/api/model-object-allocation'):
                    fields={'asset_id','source_key'}
                    if route!='/api/model-object-allocation-source':fields.update({'requests','expected_sha256'})
                    if route=='/api/model-object-allocation':fields.add('review_key')
                    if (set(body)!=fields or not isinstance(body['asset_id'],str) or not 0<len(body['asset_id'])<=512
                            or any(not isinstance(body[key],str) or len(body[key])!=64 or any(c not in '0123456789abcdef' for c in body[key])
                                   for key in fields & {'source_key','expected_sha256','review_key'})
                            or 'requests' in fields and (not isinstance(body['requests'],list) or not 0<len(body['requests'])<=64)):
                        raise ProjectError('Object allocation requires exact model, stable requests, source and review key')
                    from .model_object_allocation import source,review
                    if route.endswith('-source'):
                        self._json(200,source(self.server.project,body['asset_id'],body['source_key']))
                    elif route.endswith('-preview'):
                        self._json(200,review(self.server.project,body['asset_id'],body['requests'],body['expected_sha256'],body['source_key']))
                    else:
                        self.server.project.apply_model_object_allocations(body['asset_id'],body['requests'],body['expected_sha256'],body['source_key'],body['review_key'])
                        self._json(200,self.server.state())
                    return
                if route in ('/api/model-group-allocation-source','/api/model-group-allocation-preview','/api/model-group-allocation'):
                    fields={'asset_id','source_key'}
                    if route!='/api/model-group-allocation-source':fields.update({'requests','expected_sha256'})
                    if route=='/api/model-group-allocation':fields.add('review_key')
                    if (set(body)!=fields or not isinstance(body['asset_id'],str) or not 0<len(body['asset_id'])<=512
                            or any(not isinstance(body[key],str) or len(body[key])!=64 or any(c not in '0123456789abcdef' for c in body[key])
                                   for key in fields & {'source_key','expected_sha256','review_key'})
                            or 'requests' in fields and (not isinstance(body['requests'],list) or not 0<len(body['requests'])<=64)):
                        raise ProjectError('Group allocation requires exact model, stable requests, source and review key')
                    from .model_group_allocation import source,review
                    if route.endswith('-source'):
                        self._json(200,source(self.server.project,body['asset_id'],body['source_key']))
                    elif route.endswith('-preview'):
                        self._json(200,review(self.server.project,body['asset_id'],body['requests'],body['expected_sha256'],body['source_key']))
                    else:
                        self.server.project.apply_model_group_allocations(body['asset_id'],body['requests'],body['expected_sha256'],body['source_key'],body['review_key'])
                        self._json(200,self.server.state())
                    return
                if route in ('/api/model-vector-allocation-source','/api/model-vector-allocation-preview','/api/model-vector-allocation'):
                    fields={'asset_id','source_key'}
                    if route!='/api/model-vector-allocation-source':fields.update({'requests','expected_sha256'})
                    if route=='/api/model-vector-allocation':fields.add('proposed_sha256')
                    if (set(body)!=fields or not isinstance(body['asset_id'],str) or not 0<len(body['asset_id'])<=512
                            or any(not isinstance(body[key],str) or len(body[key])!=64 or any(c not in '0123456789abcdef' for c in body[key])
                                   for key in fields & {'source_key','expected_sha256','proposed_sha256'})
                            or 'requests' in fields and (not isinstance(body['requests'],list) or not 0<len(body['requests'])<=2048)):
                        raise ProjectError('Vector allocation requires exact typed model, requests, source and reviewed hashes')
                    from .model_vector_allocation import source,review
                    if route.endswith('-source'):
                        self._json(200,source(self.server.project,body['asset_id'],body['source_key']))
                    elif route.endswith('-preview'):
                        self._json(200,review(self.server.project,body['asset_id'],body['requests'],body['expected_sha256'],body['source_key']))
                    else:
                        self.server.project.apply_model_vector_allocations(body['asset_id'],body['requests'],body['expected_sha256'],body['source_key'],body['proposed_sha256'])
                        self._json(200,self.server.state())
                    return
                if route in ('/api/model-face-addition-source', '/api/model-face-addition-preview', '/api/model-face-addition'):
                    fields = {'asset_id', 'source_key'}
                    if route != '/api/model-face-addition-source':
                        fields.update({'requests', 'expected_sha256'})
                    if route == '/api/model-face-addition':
                        fields.add('proposed_sha256')
                    if (set(body) != fields or not isinstance(body['asset_id'], str)
                            or not 0 < len(body['asset_id']) <= 512
                            or any(not isinstance(body[key], str) or len(body[key]) != 64
                                   or any(c not in '0123456789abcdef' for c in body[key])
                                   for key in fields & {'source_key', 'expected_sha256', 'proposed_sha256'})
                            or 'requests' in fields and (not isinstance(body['requests'], list)
                                                        or not 0 < len(body['requests']) <= 128)):
                        raise ProjectError('Face addition requires exact typed model, source, requests and reviewed hashes')
                    if route == '/api/model-face-addition-source':
                        from .model_face_addition import source
                        self._json(200, source(self.server.project, body['asset_id'], body['source_key']))
                    else:
                        args = (body['asset_id'], body['requests'], body['expected_sha256'], body['source_key'])
                        if route.endswith('-preview'):
                            from .model_face_addition import review
                            self._json(200, review(self.server.project, *args))
                        else:
                            self.server.project.apply_model_face_additions(*args, body['proposed_sha256'])
                            self._json(200, self.server.state())
                    return
                if route == '/api/model-face-removal-source':
                    if set(body) != {'asset_id','source_key'}:
                        raise ProjectError('Face removal inspection requires model and source key only')
                    from .model_face_removal import source
                    self._json(200,source(self.server.project,body['asset_id'],body['source_key']))
                    return
                if route in ('/api/model-face-removal-preview','/api/model-face-removal','/api/model-face-restoration-preview','/api/model-face-restoration'):
                    fields = {'asset_id','selections','expected_sha256','source_key'}
                    if route in ('/api/model-face-removal','/api/model-face-restoration'):
                        fields.add('proposed_sha256')
                    if set(body) != fields:
                        raise ProjectError('Face removal requires exact selections and reviewed source hashes')
                    args = (body['asset_id'],body['selections'],body['expected_sha256'],body['source_key'])
                    if route.endswith('-preview'):
                        from .model_face_removal import review
                        self._json(200,review(self.server.project,*args,restore='restoration' in route))
                    else:
                        self.server.project.apply_model_face_removal(*args,body['proposed_sha256'],restore='restoration' in route)
                        self._json(200,self.server.state())
                    return
                if route == '/api/model-vertex-users':
                    if set(body) != {'asset_id','object_index','vertex_index','expected_sha256','source_key'}:
                        raise ProjectError('Vertex users require model, object, vector, inspected hash and source key only')
                    from .model_vertex_users import inspect
                    self._json(200,inspect(self.server.project,body['asset_id'],body['object_index'],body['vertex_index'],body['expected_sha256'],body['source_key']))
                    return
                if route == '/api/model-vertex-group-review':
                    if set(body)!={'group_id','review_key','source_key'}:raise ProjectError('Saved group recall requires identity, review key and current scene source')
                    from .model_vertex_groups import review
                    self._json(200,review(self.server.project,body['group_id'],body['review_key'],body['source_key']))
                    return
                if route == '/api/model-vertices-alignment':
                    if set(body)!={'asset_id','object_index','indices','axis','anchor','expected_sha256'} or not isinstance(body['asset_id'],str):raise ProjectError('Vertex alignment requires model, object, indices, axis, anchor and inspected hash')
                    self.server.project.align_model_vertices(body['asset_id'],body['object_index'],body['indices'],body['axis'],body['anchor'],body['expected_sha256'])
                    self._json(200,self.server.state())
                    return
                if route == '/api/model-vertices-distribution':
                    if set(body)!={'asset_id','object_index','indices','axis','expected_sha256'} or not isinstance(body['asset_id'],str):raise ProjectError('Vertex distribution requires model, object, indices, axis and inspected hash')
                    self.server.project.distribute_model_vertices(body['asset_id'],body['object_index'],body['indices'],body['axis'],body['expected_sha256'])
                    self._json(200,self.server.state())
                    return
                if route == '/api/model-vertices-rotation':
                    if set(body)!={'asset_id','object_index','indices','axis','quarter_turns','pivot','expected_sha256'} or not isinstance(body['asset_id'],str):raise ProjectError('Vertex rotation requires model, object, indices, axis, quarter turns, pivot and inspected hash')
                    self.server.project.rotate_model_vertices(body['asset_id'],body['object_index'],body['indices'],body['axis'],body['quarter_turns'],body['pivot'],body['expected_sha256'])
                    self._json(200,self.server.state())
                    return
                if route == '/api/model-vertices-scaling':
                    if set(body)!={'asset_id','object_index','indices','percent','pivot','expected_sha256'} or not isinstance(body['asset_id'],str):raise ProjectError('Vertex scaling requires model, object, indices, percent, pivot and inspected hash')
                    self.server.project.scale_model_vertices(body['asset_id'],body['object_index'],body['indices'],body['percent'],body['pivot'],body['expected_sha256'])
                    self._json(200,self.server.state())
                    return
                if route == '/api/model-vertices-translation':
                    if set(body) != {'asset_id','object_index','indices','offset','expected_sha256'} or not isinstance(body['asset_id'],str):
                        raise ProjectError('Vertex group translation requires model, object, indices, XYZ offset and inspected hash')
                    self.server.project.translate_model_vertices(body['asset_id'],body['object_index'],body['indices'],body['offset'],body['expected_sha256'])
                    self._json(200,self.server.state())
                    return
                if route == '/api/model-object-translation':
                    if set(body) != {'asset_id','object_index','offset','expected_sha256'} or not isinstance(body['asset_id'], str):
                        raise ProjectError('Object translation requires asset, object, XYZ offset and inspected hash')
                    self.server.project.translate_model_object(body['asset_id'], body['object_index'],
                                                               body['offset'], body['expected_sha256'])
                    self._json(200, self.server.state())
                    return
                if route == '/api/model-vector':
                    if set(body) != {'asset_id','object_index','kind','vector_index','values','expected_sha256'} or not isinstance(body['asset_id'], str):
                        raise ProjectError('Model vector editing requires asset, object/kind/vector, XYZ and inspected hash')
                    self.server.project.set_model_vector(body['asset_id'], body['object_index'], body['kind'],
                                                         body['vector_index'], body['values'], body['expected_sha256'])
                    self._json(200, self.server.state())
                    return
                if route == '/api/model-file-scene-preview':
                    if set(body) - {'all_instances'} != {'asset_id','format','content_base64','entity_id','source_key','proposed_sha256'} or type(body.get('all_instances',False)) is not bool or not isinstance(body['asset_id'],str) or not isinstance(body['entity_id'],str):
                        raise ProjectError('File scene preview requires model, file, inspected hash, instance and source key')
                    from .scene_preview import source_key
                    key = source_key(self.server.project)
                    if not key or key != body['source_key']:
                        raise ProjectError('Scene changed; refresh before inspecting a proposed file')
                    encoded = body['content_base64']
                    if not isinstance(encoded,str) or len(encoded) > 22369624:
                        raise ProjectError('Model preview exceeds the 16 MiB file limit')
                    try:
                        payload = base64.b64decode(encoded,validate=True)
                    except ValueError as exc:
                        raise ProjectError('Model preview requires valid base64') from exc
                    replacement, report = self.server.project._prepare_model_file(body['asset_id'],payload,body['format'])
                    if report['proposed_sha256'] != body['proposed_sha256']:
                        raise ProjectError('Proposed file differs from the inspected model hash')
                    report = self.server.scene_shape_proposal(body['asset_id'],body['entity_id'],replacement,report,key,body.get('all_instances',False))
                    self._json(200,report)
                    return
                if route == '/api/model-file-preview':
                    if set(body) != {'asset_id', 'format', 'content_base64'} or not isinstance(body['asset_id'], str):
                        raise ProjectError('Model preview requires asset identity, format and content_base64')
                    encoded = body['content_base64']
                    if not isinstance(encoded, str) or len(encoded) > 22369624:
                        raise ProjectError('Model preview exceeds the 16 MiB file limit')
                    try:
                        payload = base64.b64decode(encoded, validate=True)
                    except ValueError as exc:
                        raise ProjectError('Model preview requires valid base64') from exc
                    self._json(200, self.server.project.preview_model_file(body['asset_id'], payload, body['format']))
                    return
                if route in ('/api/model-shape-replacement', '/api/model-obj-replacement', '/api/model-json-replacement'):
                    json_upload = route == '/api/model-json-replacement'
                    obj_upload = route == '/api/model-obj-replacement'
                    payload_key = 'json_base64' if json_upload else 'obj_base64' if obj_upload else 'tmd_base64'
                    if set(body) != {'asset_id',payload_key} or not isinstance(body['asset_id'], str):
                        raise ProjectError('Model shape upload requires asset_id and the selected format payload only')
                    encoded = body[payload_key]
                    if not isinstance(encoded, str) or len(encoded) > (22369624 if obj_upload or json_upload else 5592408):
                        raise ProjectError('Model shape exceeds the format size limit')
                    try:
                        payload = base64.b64decode(encoded, validate=True)
                    except ValueError as exc:
                        raise ProjectError('Model shape requires valid base64') from exc
                    if json_upload:
                        self.server.project.set_model_json(body['asset_id'], payload)
                    elif obj_upload:
                        self.server.project.set_model_obj(body['asset_id'], payload)
                    else:
                        self.server.project.set_model_replacement(body['asset_id'], payload)
                    self._json(200, self.server.state())
                    return
                if route in ('/api/model-shape-preview', '/api/export/model-shape'):
                    if set(body) != {'asset_id'} or not isinstance(body['asset_id'], str):
                        raise ProjectError('Authored model preview accepts an asset identity only')
                    from importer.assets import decode_tmd
                    project = self.server.project
                    binding = project.model_overrides.get(body['asset_id'])
                    if binding is None or binding['source_scene_id'] != project.active_scene:
                        raise ProjectError('No authored model shape in the active scene')
                    asset = project.assets.records.get(body['asset_id'])
                    if asset is None:
                        raise ProjectError('Unknown model asset')
                    content = project.read_model_replacement(body['asset_id'], binding)
                    preview = decode_tmd(content)
                    preview.update(semantic_id=body['asset_id'], source_record=asset['source_record'],
                                   representation='authored-shape', authored_shape=dict(binding))
                    preview = self.server.model_preview(asset, prepared=preview)
                    self._json(200, self.server.export_preview(preview, None) if route.endswith('model-shape') else preview)
                    return
                if route in ("/api/texture-source", "/api/texture-replacement"):
                    expected = {"asset_id", "tim_base64"} if route.endswith("replacement") else {"asset_id"}
                    if set(body) != expected or not isinstance(body.get("asset_id"), str) or not body["asset_id"]:
                        raise ProjectError("Texture requests accept a resource identity and optional authored TIM only")
                    if route.endswith("source"):
                        from .resources import texture_source
                        self._json(200, texture_source(self.server.project, body["asset_id"]))
                    else:
                        encoded = body["tim_base64"]
                        if not isinstance(encoded, str) or len(encoded) > 1398104:
                            raise ProjectError("Authored TIM exceeds the 1 MiB limit")
                        try:
                            content = base64.b64decode(encoded, validate=True)
                        except ValueError as exc:
                            raise ProjectError("Authored TIM requires valid base64") from exc
                        self.server.project.set_texture_replacement(body["asset_id"], content)
                        self._json(200, self.server.state())
                    return
                if route == "/api/worldmap-menu":
                    if body or not self.server.project.disc_path:
                        raise ProjectError('World-map inspection requires the project disc and no supplied source data')
                    from importer.worldmap_menu import load_worldmap_menu
                    self._json(200, load_worldmap_menu(self.server.project.disc_path))
                    return
                if route == '/api/project-flags':
                    if body:
                        raise ProjectError('Project flag discovery uses imported sources only')
                    from .resources import project_flag_index
                    self._json(200,project_flag_index(self.server.project))
                    return
                if route == "/api/scene-flags":
                    if body:
                        raise ProjectError("Flag discovery uses the active scene; no client source bindings are accepted")
                    from .resources import scene_flag_index
                    from .flags import observed_node_flags
                    result = scene_flag_index(self.server.project)
                    result["runtime_snapshot"] = observed_node_flags(self.server.live_status, result["scene_id"])
                    self._json(200, result)
                    return
                if route == '/api/scene-text':
                    if body:
                        raise ProjectError('Text discovery uses the active scene only')
                    from .resources import scene_text_index
                    self._json(200, scene_text_index(self.server.project))
                    return
                if route == '/api/project-text':
                    if body:
                        raise ProjectError('Project text discovery uses imported scenes only')
                    from .resources import project_text_index
                    self._json(200, project_text_index(self.server.project))
                    return
                if route == '/api/actor-preset-file':
                    if set(body)!={'template_id'}:raise ProjectError('Preset export requires a template identity only')
                    from .template_files import export_file
                    self._json(200,export_file(self.server.project,body['template_id']))
                    return
                if route == '/api/actor-preset-import-review':
                    if set(body)!={'content','name'}:raise ProjectError('Preset import review requires file content and name only')
                    from .template_files import review
                    self._json(200,review(self.server.project,body['content'],body['name']))
                    return
                if route == '/api/script-operand-bundle-export':
                    if body:raise ProjectError('Operand bundle export takes no fields')
                    from .script_operand_bundle import export_file
                    self._json(200,export_file(self.server.project))
                    return
                if route == '/api/asset-references':
                    if set(body) not in ({'asset_id'}, {'asset_id','scope'}):raise ProjectError('Asset references require a stable asset ID and optional scope')
                    scope=body.get('scope','active')
                    if scope not in ('active','project'):raise ProjectError('Asset reference scope must be active or project')
                    from .asset_references import inspect,inspect_project
                    self._json(200,(inspect_project if scope=='project' else inspect)(self.server.project,body['asset_id']))
                    return
                if route == '/api/build-review':
                    if body:raise ProjectError('Build review takes no fields')
                    from .build_review import review
                    self._json(200,review(self.server.project))
                    return
                if route == '/api/scene-selection-binding':
                    if set(body)!={'scene_id','entity_ids'}:raise ProjectError('Scene selection binding requires scene and placement identities only')
                    from .scene_selection_sets import source_binding
                    from .project_copy import source_key
                    key=source_key(self.server.project)
                    binding=source_binding(self.server.project,body['scene_id'],body['entity_ids'])
                    if source_key(self.server.project)!=key:raise ProjectError('Project changed while verifying selection sources')
                    self._json(200,dict(schema_version='legaia.scene-selection-binding.v1',project_source_key=key,scene_id=body['scene_id'],entity_ids=sorted(body['entity_ids']),read_only=True,**binding))
                    return
                if route == '/api/scene-selection-review':
                    if set(body)!={'selection_set_id','review_key'}:raise ProjectError('Scene selection recall requires saved identity and review key only')
                    from .scene_selection_sets import review
                    self._json(200,review(self.server.project,body['selection_set_id'],body['review_key']))
                    return
                if route == '/api/scene-placement-layout-review':
                    if set(body)!={'entity_id','entity_ids','operation'}:raise ProjectError('Mixed layout review requires scene, selection and operation only')
                    from .scene_placement_group import layout_review
                    self._json(200,layout_review(self.server.project,body['entity_id'],body['entity_ids'],body['operation']))
                    return
                if route == '/api/scene-placement-group-review':
                    if set(body)!={'entity_id','entity_ids','delta'}:raise ProjectError('Scene placement review requires scene, selected identities and X/Z offset only')
                    from .scene_placement_group import review
                    self._json(200,review(self.server.project,body['entity_id'],body['entity_ids'],body['delta']))
                    return
                if route == '/api/environment-layout-review':
                    if set(body)!={'entity_id','entity_ids','operation'}:raise ProjectError('Scenery layout review requires scene, selected identities and operation only')
                    from .environment_layout import review
                    self._json(200,review(self.server.project,body['entity_id'],body['entity_ids'],body['operation']))
                    return
                if route == '/api/environment-rotation-group-review':
                    if set(body)!={'entity_id','entity_ids','operation'}:raise ProjectError('Scenery rotation review requires scene, selected identities and operation only')
                    from .environment_rotation_group import review
                    self._json(200,review(self.server.project,body['entity_id'],body['entity_ids'],body['operation']))
                    return
                if route == '/api/environment-group-review':
                    if set(body)!={'entity_id','entity_ids','delta'}:raise ProjectError('Scenery group review requires scene, selected identities and X/Z delta only')
                    from .environment_group import review
                    self._json(200,review(self.server.project,body['entity_id'],body['entity_ids'],body['delta']))
                    return
                if route == '/api/floor-rectangle-scene':
                    if set(body) not in ({'entity_id','rectangle','review_key'},{'entity_id','rectangle','review_key','cell_edits'}):raise ProjectError('Floor scene requires exact reviewed fields')
                    if 'cell_edits' in body and not isinstance(body['cell_edits'],list):raise ProjectError('Floor paint scene requires a selector list')
                    from .floor_rectangle import review,proposal_view
                    from .scene_preview import source_key as preview_source_key
                    from .project_copy import source_key
                    from importer.scene_animation import load_scene_actor_animation_catalog
                    from importer.environment import load_environment_preview_catalog
                    from .terrain_preview import terrain_preview
                    project=self.server.project;report=review(project,body['entity_id'],body['rectangle'],body.get('cell_edits'))
                    if report['review_key']!=body['review_key']:raise ProjectError('Floor inputs changed since Review')
                    scene_key=preview_source_key(project);view=proposal_view(project,report)
                    proposed=self.server.scene_previews.preview(view,lambda asset,*args,**kwargs:self.server.model_preview(asset,*args,effective_shape=True,project_view=view,**kwargs),load_scene_actor_animation_catalog,load_environment_preview_catalog,terrain_preview)
                    if source_key(project)!=report['project_source_key'] or preview_source_key(project)!=scene_key:raise ProjectError('Project changed during floor scene inspection')
                    self._json(200,dict(schema_version='legaia.floor-rectangle-scene.v1',review=report,scene_preview_source_key=scene_key,scene=dict(proposed,representation='authored')));return
                if route == '/api/floor-height-context':
                    if set(body)!={'entity_id'}:raise ProjectError('Floor height context requires exact scene identity')
                    from .floor_heights import inspect
                    self._json(200,inspect(self.server.project,body['entity_id']));return
                if route == '/api/floor-height-scene':
                    if set(body)!={'entity_id','heights','review_key'}:raise ProjectError('Floor height scene requires exact reviewed fields')
                    from .floor_heights import review,proposal_view
                    from .scene_preview import source_key as preview_source_key
                    from .project_copy import source_key
                    from importer.scene_animation import load_scene_actor_animation_catalog
                    from importer.environment import load_environment_preview_catalog
                    from .terrain_preview import terrain_preview
                    project=self.server.project
                    if body['entity_id']!=project.active_scene:raise ProjectError('Floor height scene must match the active scene')
                    report=review(project,body['entity_id'],body['heights'])
                    if report['review_key']!=body['review_key']:raise ProjectError('Floor height inputs changed since Review')
                    scene_key=preview_source_key(project);view=proposal_view(project,report)
                    proposed=self.server.scene_previews.preview(view,lambda asset,*args,**kwargs:self.server.model_preview(asset,*args,effective_shape=True,project_view=view,**kwargs),load_scene_actor_animation_catalog,load_environment_preview_catalog,terrain_preview)
                    if source_key(project)!=report['project_source_key'] or preview_source_key(project)!=scene_key:raise ProjectError('Project changed during floor height scene inspection')
                    self._json(200,dict(schema_version='legaia.floor-height-scene.v1',review=report,scene_preview_source_key=scene_key,scene=dict(proposed,representation='authored')));return
                if route == '/api/floor-height-review':
                    if set(body)!={'entity_id','heights'}:raise ProjectError('Floor height Review requires scene and height list only')
                    from .floor_heights import review
                    self._json(200,review(self.server.project,body['entity_id'],body['heights']));return
                if route == '/api/floor-rectangle-review':
                    if set(body) not in ({'entity_id','rectangle'},{'entity_id','rectangle','cell_edits'}):raise ProjectError('Floor Review requires scene, rectangle and optional selectors only')
                    if 'cell_edits' in body and not isinstance(body['cell_edits'],list):raise ProjectError('Floor paint requires a selector list')
                    from .floor_rectangle import review
                    self._json(200,review(self.server.project,body['entity_id'],body['rectangle'],body.get('cell_edits')))
                    return
                if route == '/api/collision-rectangle-review':
                    if set(body) not in ({'entity_id','rectangle'},{'entity_id','rectangle','cell_edits'}):raise ProjectError('Wall rectangle review requires scene, rectangle and optional quadrant edits only')
                    if 'cell_edits' in body and not isinstance(body['cell_edits'],list):raise ProjectError('Wall paint requires a quadrant edit list')
                    from .collision_rectangle import review
                    self._json(200,review(self.server.project,body['entity_id'],body['rectangle'],body.get('cell_edits')))
                    return
                if route == '/api/project/copies':
                    if body:raise ProjectError('Project copy listing takes no fields')
                    from .project_copy_history import list_copies
                    self._json(200,list_copies(self.server.project))
                    return
                if route in ('/api/project/copy-review','/api/project/copy'):
                    from .project_copy import review as copy_review,create_copy
                    if route.endswith('copy-review'):
                        if body:raise ProjectError('Copy review takes no fields')
                        result=copy_review(self.server.project)
                    else:
                        if set(body)!={'name','review_key'}:raise ProjectError('Project copy takes a name and current review key only')
                        result=create_copy(self.server.project,body['name'],body['review_key'])
                    self._json(200,result)
                    return
                if route in ('/api/builds','/api/builds/verify'):
                    from .build_history import list_builds, verify_build
                    if route == '/api/builds':
                        if body:raise ProjectError('Build history takes no fields')
                        result=list_builds(self.server.project)
                    else:
                        if set(body)!={'id'}:raise ProjectError('Build verification requires saved Build identity only')
                        result=verify_build(self.server.project,body['id'])
                    self._json(200,result)
                    return
                if route == '/api/builds/compare':
                    if set(body)!={'left_id','right_id'}:raise ProjectError('Build comparison requires two saved identities only')
                    from .build_compare import compare_builds
                    self._json(200,compare_builds(self.server.project,body['left_id'],body['right_id']))
                    return
                if route == '/api/script-operand-bundle-review':
                    if set(body)!={'content'}:raise ProjectError('Operand bundle review requires file only')
                    from .script_operand_bundle import review
                    self._json(200,review(self.server.project,body['content']))
                    return
                if route == '/api/script-operand-export':
                    if set(body)!={'entity_id'}:raise ProjectError('Operand export requires script owner only')
                    from .script_operand_files import export_file
                    self._json(200,export_file(self.server.project,body['entity_id']))
                    return
                if route == '/api/script-operand-review':
                    if set(body)!={'entity_id','content'}:raise ProjectError('Operand review requires script owner and file only')
                    from .script_operand_files import review
                    self._json(200,review(self.server.project,body['entity_id'],body['content']))
                    return
                if route == '/api/actor-preset-batch-scene':
                    if set(body) != {'template_id', 'actor_ids', 'review_key'}:
                        raise ProjectError('Group preset scene inspection requires preset, actors and reviewed key only')
                    from .preset_batch import review, proposal_view
                    from .scene_preview import source_key
                    from importer.scene_animation import load_scene_actor_animation_catalog
                    from importer.environment import load_environment_preview_catalog
                    from .terrain_preview import terrain_preview
                    project=self.server.project;report=review(project,body['template_id'],body['actor_ids'])
                    if body['review_key']!=report['review_key']:
                        raise ProjectError('Preset or group changed since review')
                    original_key=source_key(project);view=proposal_view(project,report)
                    proposed=self.server.scene_previews.preview(
                        view,lambda asset,*args,**kwargs:self.server.model_preview(asset,*args,effective_shape=True,project_view=view,**kwargs),
                        load_scene_actor_animation_catalog,load_environment_preview_catalog,terrain_preview)
                    if source_key(project)!=original_key or review(project,body['template_id'],body['actor_ids'])!=report:
                        raise ProjectError('Scene, preset or group changed during inspection')
                    self._json(200,{'schema_version':'legaia.actor-preset-batch-scene.v1','scene_id':project.active_scene,
                                    'project_source_key':original_key,'review_key':report['review_key'],
                                    'scene':dict(proposed,representation='authored')})
                    return
                if route == '/api/actor-preset-batch':
                    if set(body) != {'template_id', 'actor_ids'}:
                        raise ProjectError('Group preset review requires preset and actor IDs only')
                    from .preset_batch import review
                    self._json(200, review(self.server.project, body['template_id'], body['actor_ids']))
                    return
                if route == '/api/actor-preset-review':
                    if set(body)!={'template_id','entity_id'}:raise ProjectError('Preset review requires a template and existing target only')
                    from .actor_presets import preview
                    self._json(200,preview(self.server.project,body['template_id'],body['entity_id']))
                    return
                if route == '/api/actor-preset-scene':
                    if set(body)!={'template_id','entity_id','review_key'}:
                        raise ProjectError('Preset scene inspection requires template, target and reviewed key only')
                    from .actor_presets import preview,proposal_view
                    from .scene_preview import source_key
                    from importer.scene_animation import load_scene_actor_animation_catalog
                    from importer.environment import load_environment_preview_catalog
                    from .terrain_preview import terrain_preview
                    project=self.server.project;report=preview(project,body['template_id'],body['entity_id'])
                    if body['review_key']!=report['review_key']:
                        raise ProjectError('Preset or target changed since review')
                    original_key=source_key(project);view=proposal_view(project,report)
                    proposed=self.server.scene_previews.preview(
                        view,lambda asset,*args,**kwargs:self.server.model_preview(asset,*args,effective_shape=True,project_view=view,**kwargs),
                        load_scene_actor_animation_catalog,load_environment_preview_catalog,terrain_preview)
                    if source_key(project)!=original_key or preview(project,body['template_id'],body['entity_id'])!=report:
                        raise ProjectError('Scene, preset or target changed during inspection')
                    self._json(200,{'schema_version':'legaia.actor-preset-scene.v1','scene_id':project.active_scene,
                                    'project_source_key':original_key,'review_key':report['review_key'],
                                    'scene':dict(proposed,representation='authored')})
                    return
                if route == '/api/transition-arrival-review':
                    if set(body)!={'asset_id','project_state_key','destination_source_key','arrival'}:
                        raise ProjectError('Arrival Review requires source identity, project/destination keys and arrival only')
                    from .transition_arrival import review
                    self._json(200,review(self.server.project,body['asset_id'],body['project_state_key'],body['destination_source_key'],body['arrival']))
                    return
                if route == '/api/transition-arrival-apply':
                    from .transition_arrival import apply
                    apply(self.server.project,body)
                    self._json(200,self.server.state())
                    return
                if route == "/api/transition-arrival-preview":
                    if set(body) != {'asset_id','source_key'}:
                        raise ProjectError('Transition arrival inspection requires only asset_id and source_key')
                    from .transition_arrival import inspect
                    self._json(200,inspect(self.server.project,body['asset_id'],body['source_key']))
                    return
                if route == "/api/project-transitions":
                    if body:
                        raise ProjectError("Project transition discovery accepts no client source bindings")
                    from .resources import project_transition_graph
                    self._json(200,project_transition_graph(self.server.project))
                    return
                if route == "/api/scene-transitions":
                    if body:
                        raise ProjectError("Transition discovery uses the active scene; no client source bindings are accepted")
                    from .resources import scene_transition_graph
                    self._json(200, scene_transition_graph(self.server.project))
                    return
                if route == "/api/resource-catalog":
                    if body:
                        raise ProjectError("Resource discovery takes no client source bindings")
                    from .resources import refresh_resource_catalog
                    self._json(200, refresh_resource_catalog(self.server.project))
                    return
                if route == "/api/partition-two-script":
                    if set(body) != {"entity_id"} or not isinstance(body["entity_id"], str) or not body["entity_id"]:
                        raise ProjectError("Partition-two inspection accepts a structural entity_id only")
                    from .resources import partition_two_script_preview
                    report = partition_two_script_preview(self.server.project, body["entity_id"])
                    report["dialogue_authoring"] = self.server.project.dialogue_options(body["entity_id"])
                    report["transition_authoring"] = _transition_authoring_report(self.server.project, body["entity_id"])
                    report["movement_authoring"] = _movement_authoring_report(self.server.project, body["entity_id"])
                    report['facing_authoring'] = _facing_authoring_report(self.server.project, body["entity_id"])
                    report["flag_authoring"] = _flag_authoring_report(self.server.project, body["entity_id"])
                    report["wait_authoring"] = _wait_authoring_report(self.server.project, body["entity_id"])
                    report["model_selector_authoring"] = _model_selector_authoring_report(self.server.project, body["entity_id"])
                    self._json(200, report)
                    return
                if route == "/api/trigger-script":
                    if set(body) != {"asset_id"} or not isinstance(body["asset_id"], str) or not body["asset_id"]:
                        raise ProjectError("Trigger script inspection accepts a catalog identity only; partition and source spans are source-controlled")
                    from .resources import trigger_script_preview
                    report = trigger_script_preview(self.server.project, body["asset_id"])
                    identifier = "scene://" + report["script_id"].removeprefix("script://")
                    report["dialogue_authoring"] = self.server.project.dialogue_options(identifier)
                    report["transition_authoring"] = _transition_authoring_report(self.server.project, identifier)
                    report["movement_authoring"] = _movement_authoring_report(self.server.project, identifier)
                    report['facing_authoring'] = _facing_authoring_report(self.server.project, identifier)
                    report["flag_authoring"] = _flag_authoring_report(self.server.project, identifier)
                    report["wait_authoring"] = _wait_authoring_report(self.server.project, identifier)
                    report["model_selector_authoring"] = _model_selector_authoring_report(self.server.project, identifier)
                    self._json(200, report)
                    return
                if route == "/api/model-shape-source":
                    if set(body) - {"asset_id", "format", "layer"} or not isinstance(body.get("asset_id"), str) or not body["asset_id"]:
                        raise ProjectError("Model source accepts a catalog identity only")
                    from .resources import model_shape_source
                    self._json(200, model_shape_source(self.server.project, body["asset_id"], body.get('format','tmd'), body.get('layer','imported')))
                    return
                if route == '/api/region-bounds-review':
                    if set(body) != {'region_id', 'values', 'action'}:
                        raise ProjectError('Region review requires region identity, complete corners and action only')
                    from .region_bounds import review
                    self._json(200, review(self.server.project, body['region_id'], body['values'], body['action']))
                    return
                if route == '/api/region-bounds-apply':
                    from .region_bounds import apply
                    apply(self.server.project, body)
                    self._json(200, self.server.state())
                    return
                if route == '/api/trigger-scripts-review':
                    if set(body) != {'trigger_id', 'script_id', 'action'}:
                        raise ProjectError('Trigger script review requires exact trigger, script and action fields')
                    from .trigger_scripts import review
                    self._json(200, review(self.server.project, body['trigger_id'], body['script_id'], body['action']))
                    return
                if route == '/api/trigger-scripts-apply':
                    from .trigger_scripts import apply
                    apply(self.server.project, body)
                    self._json(200, self.server.state())
                    return
                if route == '/api/trigger-group-review':
                    if set(body) != {'scene_id','trigger_ids','delta','action'}:
                        raise ProjectError('Trigger group review accepts scene, selected identities, delta and action only')
                    from .trigger_group import review
                    self._json(200, review(self.server.project, body['scene_id'], body['trigger_ids'], body['delta'], body['action']))
                    return
                if route == '/api/trigger-group-apply':
                    from .trigger_group import apply
                    apply(self.server.project, body)
                    self._json(200, self.server.state())
                    return
                if route == '/api/trigger-cells-review':
                    if set(body) != {'trigger_id', 'values', 'action'}:
                        raise ProjectError('Trigger review requires trigger identity, complete cell coordinates and action only')
                    from .trigger_cells import review
                    self._json(200, review(self.server.project, body['trigger_id'], body['values'], body['action']))
                    return
                if route == '/api/trigger-cells-apply':
                    from .trigger_cells import apply
                    apply(self.server.project, body)
                    self._json(200, self.server.state())
                    return
                if route == "/api/field-map-preview":
                    if set(body) - {"asset_id", "layer"} or not isinstance(body.get("asset_id"), str) or not body["asset_id"]:
                        raise ProjectError("Field map preview accepts a catalog identity only; coordinates and paths are source-controlled")
                    from .resources import field_map_preview
                    self._json(200, field_map_preview(self.server.project, body["asset_id"], body.get("layer", "imported")))
                    return
                if route == "/api/texture-preview":
                    if (not {"asset_id", "palette_index"} <= set(body) or set(body) - {"asset_id", "palette_index", "layer"} or
                            not isinstance(body.get("asset_id"), str) or not body["asset_id"] or
                            type(body.get("palette_index")) is not int or body["palette_index"] < 0):
                        raise ProjectError("Texture preview requires a resource identity and nonnegative palette index only")
                    from .resources import texture_preview
                    self._json(200, texture_preview(self.server.project, body["asset_id"], body["palette_index"], body.get("layer", "effective")))
                    return
                if route in ('/api/model-mesh-sources','/api/model-mesh-source-download'):
                    fields={'asset_id','source_key'}
                    if route.endswith('-download'):fields.add('receipt_key')
                    if set(body)!=fields:raise ProjectError('Mesh source recovery requires exact Current model identity and context')
                    from .model_mesh_sources import catalog,download
                    result=download(self.server.project,body['asset_id'],body['source_key'],body['receipt_key']) if route.endswith('-download') else catalog(self.server.project,body['asset_id'],body['source_key'])
                    self._json(200,result)
                    return
                if route=='/api/texture-slot-source-download':
                    if set(body)!={'asset_id','expected_sha256','source_key'}:raise ProjectError('Source download requires exact Current identity and context')
                    from .texture_slot_sources import download
                    self._json(200,download(self.server.project,body['asset_id'],body['expected_sha256'],body['source_key']))
                    return
                if route in ('/api/texture-slot-source-review','/api/texture-slot-source-apply'):
                    fields={'asset_id','expected_sha256','source_key','png_base64','stp_png_base64','options'}
                    if route.endswith('-apply'):fields.add('review_key')
                    if set(body) not in (fields,fields|{'glb_source'}):raise ProjectError('Source retention requires exact PNG, recipe and Current context')
                    def decode_source(value):
                        if not isinstance(value,str) or not 1<=len(value)<=11184812:raise ProjectError('Choose PNG sources up to eight MiB each')
                        try:return base64.b64decode(value,validate=True)
                        except ValueError as exc:raise ProjectError('Retained PNG requires valid base64') from exc
                    if 'glb_source' in body and body['glb_source'] is None:raise ProjectError('Selected GLB source cannot be null')
                    png=decode_source(body['png_base64']);stp=decode_source(body['stp_png_base64']) if body['stp_png_base64'] is not None else None
                    from .texture_slot_sources import review,apply
                    args=(self.server.project,body['asset_id'],body['expected_sha256'],body['source_key'],png,body['options'],stp)
                    if route.endswith('-review'):self._json(200,review(*args,glb_source=body.get('glb_source')))
                    else:
                        report=apply(*args,body['review_key'],glb_source=body.get('glb_source'))
                        self._json(200,dict(self.server.state(),texture_source_report=report))
                    return
                if route=='/api/texture-upload-map':
                    if set(body)!={'asset_id','source_key'}:
                        raise ProjectError('Static upload map requires exact texture and source context')
                    from .texture_placement import upload_map
                    self._json(200,upload_map(self.server.project,body['asset_id'],body['source_key']))
                    return
                if route=='/api/texture-placement':
                    if set(body)!={'asset_id','source_key','png_base64','bpp'}:
                        raise ProjectError('Texture placement requires exact texture, source PNG, native mode and context')
                    value=body['png_base64']
                    if not isinstance(value,str) or not 1<=len(value)<=11184812:
                        raise ProjectError('Placement PNG exceeds its eight MiB source budget')
                    try:content=base64.b64decode(value,validate=True)
                    except ValueError as exc:raise ProjectError('Placement PNG requires valid base64') from exc
                    from .texture_placement import suggest
                    self._json(200,suggest(self.server.project,body['asset_id'],body['source_key'],content,body['bpp']))
                    return
                if route=='/api/texture-image-convert':
                    if set(body) not in ({'asset_id','source_key','png_base64','stp_png_base64','options'},{'asset_id','source_key','png_base64','stp_png_base64','options','glb_source'}):
                        raise ProjectError('Image conversion requires exact source, PNG and native options')
                    def decode_image(value):
                        if not isinstance(value,str) or not 1<=len(value)<=11184812:
                            raise ProjectError('Choose a PNG no larger than eight MiB')
                        try:return base64.b64decode(value,validate=True)
                        except ValueError as exc:raise ProjectError('PNG conversion requires valid base64') from exc
                    if 'glb_source' in body and body['glb_source'] is None:raise ProjectError('Selected GLB source cannot be null')
                    png=decode_image(body['png_base64'])
                    stp=decode_image(body['stp_png_base64']) if body['stp_png_base64'] is not None else None
                    from .texture_image_conversion import convert
                    self._json(200,convert(self.server.project,body['asset_id'],body['source_key'],png,body['options'],stp,glb_source=body.get('glb_source')))
                    return
                if route=='/api/texture-slot-edit-source':
                    if set(body)!={'asset_id','source_key'}:raise ProjectError('Authored slot source requires exact identity and context')
                    from .texture_slot_edit import source
                    content,report=source(self.server.project,body['asset_id'],body['source_key'])
                    self._json(200,dict(report,content_base64=base64.b64encode(content).decode('ascii')))
                    return
                if route in ('/api/texture-slot-edit-review','/api/texture-slot-edit-pixels','/api/texture-slot-edit-apply'):
                    fields={'asset_id','expected_sha256','source_key','label','accept_potential_overlap','content_base64'}
                    if route!='/api/texture-slot-edit-review':fields.add('review_key')
                    if route=='/api/texture-slot-edit-pixels':fields.add('palette_index')
                    if set(body) not in (fields,fields|{'conversion_source'}) or not isinstance(body['content_base64'],str) or not 1<=len(body['content_base64'])<=1398104:
                        raise ProjectError('Edited texture slot requires exact context and bounded complete TIM bytes')
                    try:payload=base64.b64decode(body['content_base64'],validate=True)
                    except ValueError as exc:raise ProjectError('Edited TIM requires valid base64') from exc
                    from .texture_slot_edit import review,pixels,apply
                    args=(self.server.project,body['asset_id'],payload,body['expected_sha256'],body['source_key'],body['label'],body['accept_potential_overlap'])
                    conversion_source=_slot_conversion_source(body)
                    if route=='/api/texture-slot-edit-review':self._json(200,review(*args,conversion_source=conversion_source))
                    elif route=='/api/texture-slot-edit-pixels':self._json(200,pixels(*args,body['review_key'],body['palette_index'],conversion_source=conversion_source))
                    else:
                        report=apply(*args,body['review_key'],conversion_source=conversion_source)
                        self._json(200,dict(self.server.state(),texture_slot_report=report))
                    return
                if route in ('/api/texture-slot-review','/api/texture-slot-pixels','/api/texture-slot-apply'):
                    fields={'anchor_asset_id','source_key','label','accept_potential_overlap','content_base64'}
                    if route!='/api/texture-slot-review':fields.add('review_key')
                    if route=='/api/texture-slot-pixels':fields.add('palette_index')
                    if set(body) not in (fields,fields|{'conversion_source'}) or not isinstance(body['content_base64'],str) or not 1<=len(body['content_base64'])<=1398104:
                        raise ProjectError('New texture slot requires exact context and bounded complete TIM bytes')
                    try:payload=base64.b64decode(body['content_base64'],validate=True)
                    except ValueError as exc:raise ProjectError('New texture TIM requires valid base64') from exc
                    from .texture_slots import review,apply,pixels
                    args=(self.server.project,body['anchor_asset_id'],payload,body['source_key'],body['label'],body['accept_potential_overlap'])
                    conversion_source=_slot_conversion_source(body)
                    if route=='/api/texture-slot-review':self._json(200,review(*args,conversion_source=conversion_source))
                    elif route=='/api/texture-slot-pixels':self._json(200,pixels(*args,body['review_key'],body['palette_index'],conversion_source=conversion_source))
                    else:
                        report=apply(*args,body['review_key'],conversion_source=conversion_source)
                        self._json(200,dict(self.server.state(),texture_slot_report=report))
                    return
                if route == '/api/texture-resize-source':
                    if set(body)!={'asset_id','source_key'} or not isinstance(body['asset_id'],str) or not 1<=len(body['asset_id'])<=512:
                        raise ProjectError('Texture resize source requires an asset and source key')
                    from .texture_resize import source
                    self._json(200,source(self.server.project,body['asset_id'],body['source_key']))
                    return
                if route in ('/api/texture-resize-preview','/api/texture-resize','/api/texture-resize-pixels-preview','/api/texture-resize-scene-preview'):
                    fields={'asset_id','expected_sha256','source_key','width','height','fill_value','accept_potential_overlap'}
                    if route!='/api/texture-resize-preview':fields.add('review_key')
                    if route=='/api/texture-resize-pixels-preview':fields.add('palette_index')
                    if set(body) not in (fields,fields|{'resize_mode'}) or not isinstance(body['asset_id'],str) or not 1<=len(body['asset_id'])<=512:
                        raise ProjectError('Texture resize requires exact current texture context and encoded dimensions')
                    from .texture_resize import review,apply,pixels,reviewed
                    args=(self.server.project,body['asset_id'],body['expected_sha256'],body['source_key'],
                          body['width'],body['height'],body['fill_value'],body['accept_potential_overlap'])
                    mode=body.get('resize_mode','crop-fill')
                    if route=='/api/texture-resize-preview':self._json(200,review(*args,resize_mode=mode))
                    elif route=='/api/texture-resize-pixels-preview':self._json(200,pixels(*args,body['review_key'],body['palette_index'],resize_mode=mode))
                    elif route=='/api/texture-resize-scene-preview':
                        candidate,report=reviewed(*args,body['review_key'],resize_mode=mode)
                        self._json(200,self.server.scene_texture_proposal(body['asset_id'],candidate,report,body['source_key']))
                    else:
                        report=apply(*args,body['review_key'],resize_mode=mode)
                        self._json(200,dict(self.server.state(),resize_report=report))
                    return
                if route in ('/api/texture-glb-retain-review','/api/texture-glb-retain'):
                    fields={'asset_id','expected_sha256','source_key','content_base64'}
                    if route.endswith('retain'):fields.add('review_key')
                    if set(body)!=fields or not isinstance(body['content_base64'],str) or not 1<=len(body['content_base64'])<=44739244:
                        raise ProjectError('Original GLB retention requires bounded file bytes and current texture context')
                    try:payload=base64.b64decode(body['content_base64'],validate=True)
                    except ValueError as exc:raise ProjectError('Original GLB requires valid base64') from exc
                    from .texture_source_retention import review,apply
                    args=(self.server.project,body['asset_id'],body['expected_sha256'],body['source_key'],payload)
                    if route.endswith('review'):self._json(200,review(*args))
                    else:
                        report=apply(*args,body['review_key'])
                        self._json(200,dict(self.server.state(),retention_report=report))
                    return
                if route == '/api/texture-glb-source':
                    if set(body)!={'asset_id','expected_sha256'} or not isinstance(body['asset_id'],str) or not 1<=len(body['asset_id'])<=512:
                        raise ProjectError('Retained texture source requires a current texture identity and hash')
                    project=self.server.project;binding=project.texture_overrides.get(body['asset_id'])
                    if not binding or binding['asset_sha256']!=body['expected_sha256']:
                        raise ProjectError('Authored texture changed; reopen its retained source')
                    content=project.read_texture_glb_source(binding)
                    self._json(200,dict(schema_version='legaia.texture-glb-source.v1',asset_id=body['asset_id'],
                        effective_sha256=binding['asset_sha256'],source=binding['glb_source'],glb_base64=base64.b64encode(content).decode(),
                        read_only=True,project_changed=False))
                    return
                if route=='/api/texture-glb-dependencies':
                    if set(body)!={'content_base64'} or not isinstance(body['content_base64'],str) or not 0<len(body['content_base64'])<=44739244:
                        raise ProjectError('GLB dependencies require exact bounded source bytes')
                    try:payload=base64.b64decode(body['content_base64'],validate=True)
                    except ValueError as exc:raise ProjectError('GLB dependencies require valid base64') from exc
                    from importer.texture_glb_dependencies import inspect_glb_dependencies
                    self._json(200,inspect_glb_dependencies(payload))
                    return
                if route in ('/api/texture-glb-images','/api/texture-glb-image'):
                    fields={'content_base64'} if route.endswith('images') else {'content_base64','image_index','glb_sha256','png_sha256'}
                    if set(body)!=fields or not isinstance(body['content_base64'],str) or not 0<len(body['content_base64'])<=44739244:
                        raise ProjectError('GLB image extraction requires bounded file bytes and exact source selection')
                    try:payload=base64.b64decode(body['content_base64'],validate=True)
                    except ValueError as exc:raise ProjectError('GLB image file requires valid base64') from exc
                    from importer.texture_glb import inspect_glb_pngs,extract_glb_png
                    result=(inspect_glb_pngs(payload) if route.endswith('images') else
                            extract_glb_png(payload,body['image_index'],body['glb_sha256'],body['png_sha256']))
                    self._json(200,result)
                    return
                if route == '/api/texture-png-export':
                    if set(body) != {'asset_id', 'palette_index'} or not isinstance(body['asset_id'], str) or type(body['palette_index']) is not int:
                        raise ProjectError('Texture PNG export requires a texture asset and integer palette')
                    from .texture_png import export_texture, _json_size
                    from .build import _guard_output
                    from .project import atomic_write
                    from uuid import uuid4
                    png, stp, binding, report = export_texture(self.server.project, body['asset_id'], body['palette_index'])
                    output = self.server.project.root / 'Exports'
                    stem = 'texture-' + uuid4().hex
                    paths = [output / (stem + suffix) for suffix in ('.png', '.stp.png', '.binding.json')]
                    _guard_output(output / '.gitignore', self.server.project.root)
                    for path in paths:
                        _guard_output(path, self.server.project.root)
                    output.mkdir(parents=True, exist_ok=True)
                    for path, content in zip(paths, (png, stp, (json.dumps(binding, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8'))):
                        with path.open('xb') as handle:
                            handle.write(content)
                    if not (output / '.gitignore').exists():
                        atomic_write(output / '.gitignore', b'*\n')
                    result = dict(path=str(paths[0]), filename=paths[0].name, stp_path=str(paths[1]), stp_filename=paths[1].name,
                                  binding_path=str(paths[2]), binding_filename=paths[2].name, binding=binding, report=report,
                                  png_base64=base64.b64encode(png).decode('ascii'), stp_png_base64=base64.b64encode(stp).decode('ascii'))
                    _json_size(result, 24 * 1024 * 1024, 'Texture PNG export')
                    self._json(200, result)
                    return
                if route in ('/api/texture-png-preview', '/api/texture-png-pixels-preview', '/api/texture-png-scene-preview', '/api/texture-png-import'):
                    expected = {'asset_id', 'png_base64', 'stp_png_base64', 'binding', 'palette_mode'}
                    if 'glb_source' in body:expected.add('glb_source')
                    if route in ('/api/texture-png-scene-preview', '/api/texture-png-import'):
                        expected.add('review_key')
                    from .texture_png import _json_size, preview_import, pixels_import, scene_import, apply_import
                    if set(body) != expected or not isinstance(body['asset_id'], str) or not isinstance(body['binding'], dict) or body['palette_mode'] not in ('existing', 'rebuild'):
                        raise ProjectError('Texture PNG requires an asset, bounded binding, palette mode and PNG bytes')
                    _json_size(body['binding'], 128 * 1024, 'Texture PNG binding')
                    if 'review_key' in expected and (not isinstance(body['review_key'], str) or len(body['review_key']) != 64):
                        raise ProjectError('Texture PNG requires a reviewed proposal key')
                    payloads = []
                    for field in ('png_base64', 'stp_png_base64'):
                        encoded = body[field]
                        if field == 'stp_png_base64' and encoded is None:
                            payloads.append(None)
                            continue
                        if not isinstance(encoded, str) or len(encoded) > 11184812:
                            raise ProjectError('Texture PNG files must be at most 8 MiB each')
                        try:
                            payload = base64.b64decode(encoded, validate=True)
                        except ValueError as exc:
                            raise ProjectError('Texture PNG requires valid base64') from exc
                        if not 1 <= len(payload) <= 8 * 1024 * 1024:
                            raise ProjectError('Texture PNG files must contain at most 8 MiB each')
                        payloads.append(payload)
                    args = (self.server.project, body['asset_id'], payloads[0], body['binding'], body['palette_mode'], payloads[1])
                    if route == '/api/texture-png-preview':
                        self._json(200, preview_import(*args,glb_source=body.get('glb_source')))
                    elif route == '/api/texture-png-pixels-preview':
                        self._json(200, pixels_import(*args,glb_source=body.get('glb_source')))
                    elif route == '/api/texture-png-scene-preview':
                        candidate, report = scene_import(*args, body['review_key'],glb_source=body.get('glb_source'))
                        self._json(200, self.server.scene_texture_proposal(body['asset_id'], candidate, report, report['project_source_key']))
                    else:
                        report = apply_import(*args, body['review_key'],glb_source=body.get('glb_source'))
                        self._json(200, dict(self.server.state(), texture_png_report=report))
                    return
                if route == '/api/model-glb-export':
                    if set(body) != {'asset_id'} or not isinstance(body['asset_id'], str):
                        raise ProjectError('Model GLB export requires a model asset only')
                    from .model_glb import export_model
                    from .build import _guard_output
                    from .project import atomic_write
                    from importer.export import write_encoded_glb
                    payload, binding, report = export_model(self.server.project, body['asset_id'])
                    output = self.server.project.root / 'Exports'
                    _guard_output(output / '.gitignore', self.server.project.root)
                    result = write_encoded_glb(payload, report, output)
                    binding_path = Path(result['path']).with_suffix('.binding.json')
                    _guard_output(binding_path, self.server.project.root)
                    with binding_path.open('xb') as handle:
                        handle.write((json.dumps(binding, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8'))
                    if not (output / '.gitignore').exists():
                        atomic_write(output / '.gitignore', b'*\n')
                    self._json(200, dict(path=result['path'], filename=result['filename'],
                                         binding=binding, binding_path=str(binding_path),
                                         binding_filename=binding_path.name, report=report,
                                         content_base64=base64.b64encode(payload).decode('ascii')))
                    return
                if route in ('/api/model-glb-material-links','/api/model-glb-material-faces'):
                    fields={'asset_id','content_base64','binding','source_key'}
                    if route.endswith('-faces'):fields.update(('material_index','role','image_index'))
                    if set(body)!=fields or not isinstance(body['binding'],dict) or len(json.dumps(body['binding'],allow_nan=False).encode('utf-8'))>128*1024:
                        raise ProjectError('GLB native selection requires exact current source and bounded SDK binding')
                    encoded=body['content_base64']
                    if not isinstance(encoded,str) or not 1<=len(encoded)<=44739244:raise ProjectError('Choose a source-qualified GLB up to 32 MiB')
                    try:content=base64.b64decode(encoded,validate=True)
                    except ValueError as exc:raise ProjectError('GLB selection requires valid base64') from exc
                    from .model_glb_material_selection import links,faces
                    args=(self.server.project,body['asset_id'],content,body['binding'],body['source_key'])
                    self._json(200,links(*args) if route.endswith('-links') else faces(*args,body['material_index'],body['role'],body['image_index']))
                    return
                if route in ('/api/model-glb-preview', '/api/model-glb-pose-preview', '/api/model-glb-import'):
                    expected = {'asset_id', 'content_base64', 'binding'}
                    if route == '/api/model-glb-import':
                        expected.add('review_key')
                    if (set(body) != expected or not isinstance(body['asset_id'], str) or
                            not isinstance(body['binding'], dict) or
                            len(json.dumps(body['binding'], allow_nan=False).encode('utf-8')) > 128 * 1024):
                        raise ProjectError('Model GLB requires a model asset, bounded binding and GLB bytes')
                    encoded = body['content_base64']
                    if not isinstance(encoded, str) or len(encoded) > 44739244:
                        raise ProjectError('Model GLB exceeds 32 MiB')
                    try:
                        payload = base64.b64decode(encoded, validate=True)
                    except ValueError as exc:
                        raise ProjectError('Model GLB requires valid base64') from exc
                    if not 1 <= len(payload) <= 32 * 1024 * 1024:
                        raise ProjectError('Model GLB must contain at most 32 MiB')
                    from .model_glb import apply_import, pose_import, preview_import
                    if route == '/api/model-glb-preview':
                        self._json(200, preview_import(self.server.project, body['asset_id'], payload, body['binding']))
                    elif route == '/api/model-glb-pose-preview':
                        from importer.assets import decode_tmd
                        candidate, report = pose_import(self.server.project, body['asset_id'], payload, body['binding'])
                        project = self.server.project
                        asset = next(item for item in project.imports[project.active_scene]['assets']['models']
                                     if item['semantic_id'] == body['asset_id'])
                        preview = decode_tmd(candidate)
                        preview.update(semantic_id=body['asset_id'], source_record=asset['source_record'],
                                       representation='model-glb-proposal', model_glb_proposal=True)
                        preview = self.server.model_preview(asset, prepared=preview)
                        from .scene_preview import source_key
                        if source_key(project) != report['project_source_key']:
                            raise ProjectError('Project changed while preparing the proposed model; review again')
                        self._json(200, dict(preview=preview, report=report))
                    else:
                        report = apply_import(self.server.project, body['asset_id'], payload, body['binding'], body['review_key'])
                        self._json(200, dict(self.server.state(), model_glb_report=report))
                    return
                if route=='/api/animation-library-native-comparison':
                    if set(body)!={'receipt_key','expected_project_path','expected_library_key'}:raise ProjectError('Native animation comparison requires exact fields')
                    from .animation_sources import compare_native
                    self._json(200,compare_native(self.server.project,**body));return
                if route in ('/api/animation-source-library','/api/animation-library-download','/api/animation-library-removal-review','/api/animation-library-remove'):
                    expected={'expected_project_path'}
                    if route!='/api/animation-source-library':expected.update({'receipt_key','expected_library_key'})
                    if route.endswith('/animation-library-remove'):expected.add('review_key')
                    if set(body)!=expected:raise ProjectError('Animation input library requires exact fields')
                    from .animation_sources import library,library_download,library_removal_review
                    if route.endswith('/animation-library-remove'):
                        self.server.project.command(dict(body,type='remove_project_animation_source'))
                        self._json(200,self.server.state())
                    else:
                        operation=library if route=='/api/animation-source-library' else library_download if route.endswith('download') else library_removal_review
                        self._json(200,operation(self.server.project,**body))
                    return
                if route=='/api/mesh-library-native-comparison':
                    if set(body)!={'receipt_key','expected_project_path','expected_library_key'}:raise ProjectError('Mesh native comparison requires exact fields')
                    from .model_mesh_library import compare_native
                    self._json(200,compare_native(self.server.project,**body));return
                if route in ('/api/mesh-source-library','/api/mesh-library-download'):
                    expected={'expected_project_path'}
                    if route.endswith('download'):expected.update({'receipt_key','expected_library_key'})
                    if set(body)!=expected:raise ProjectError('Mesh input library requires exact fields')
                    from .model_mesh_library import library,download
                    self._json(200,(library if route=='/api/mesh-source-library' else download)(self.server.project,**body));return
                if route=='/api/model-library-native-comparison':
                    if set(body)!={'receipt_key','expected_project_path','expected_library_key'}:raise ProjectError('Native model comparison requires exact fields')
                    from .model_glb_sources import compare_native
                    self._json(200,compare_native(self.server.project,**body));return
                if route in ('/api/model-source-library','/api/model-library-download','/api/model-library-removal-review','/api/model-library-remove'):
                    expected={'expected_project_path'}
                    if route!='/api/model-source-library':expected.update({'receipt_key','expected_library_key'})
                    if route.endswith('/model-library-remove'):expected.add('review_key')
                    if set(body)!=expected:raise ProjectError('Model input library requires exact fields')
                    from .model_glb_sources import library,library_download,library_removal_review
                    if route.endswith('/model-library-remove'):
                        self.server.project.command(dict(body,type='remove_project_model_source'));self._json(200,self.server.state())
                    else:
                        operation=library if route=='/api/model-source-library' else library_download if route.endswith('download') else library_removal_review
                        self._json(200,operation(self.server.project,**body))
                    return
                if route in ('/api/model-source-removal-review','/api/model-source-remove'):
                    expected={'asset_id','expected_source_key','receipt_key'}
                    if route.endswith('/model-source-remove'):expected.add('review_key')
                    if set(body)!=expected:raise ProjectError('Model source removal requires exact reviewed fields')
                    if route.endswith('/model-source-remove'):
                        self.server.project.command(dict(body,type='remove_model_source'));self._json(200,self.server.state())
                    else:
                        from .model_glb_sources import review_removal
                        self._json(200,review_removal(self.server.project,**body))
                    return
                if route in ('/api/model-sources','/api/model-source-download'):
                    expected={'asset_id','expected_source_key'}
                    if route.endswith('download'):expected.add('receipt_key')
                    if set(body)!=expected:raise ProjectError('Model sources require an exact recovery context')
                    from .model_glb_sources import catalog,download
                    self._json(200,(download if route.endswith('download') else catalog)(self.server.project,**body))
                    return
                if route in ('/api/animation-sources','/api/animation-source-download'):
                    expected={'scene_id','target_id','kind','expected_source_key'}
                    if route.endswith('download'):expected.add('receipt_key')
                    if set(body)!=expected:raise ProjectError('Animation sources require an exact recovery context')
                    from .animation_sources import catalog,download
                    self._json(200,(download if route.endswith('download') else catalog)(self.server.project,**body))
                    return
                if route in ('/api/animation-source-removal-review','/api/animation-source-remove'):
                    expected={'scene_id','target_id','kind','expected_source_key','receipt_key'}
                    if route.endswith('remove'):expected.add('review_key')
                    if set(body)!=expected:raise ProjectError('Animation source removal requires exact fields')
                    from .animation_sources import review_removal
                    if route.endswith('remove'):
                        self.server.project.command(dict(body,type='remove_animation_source'))
                        self._json(200,self.server.state())
                    else:self._json(200,review_removal(self.server.project,**body))
                    return
                if route == '/api/animation-glb-export':
                    if set(body) != {'entity_id', 'clip_fps'} or not isinstance(body['entity_id'], str):
                        raise ProjectError('Animation GLB export requires an actor and explicit interchange rate only')
                    from .animation_glb import export_clip, preview_import
                    from .build import _guard_output
                    from .project import atomic_write
                    from importer.export import encode_model_glb, write_encoded_glb
                    animation, asset, binding = export_clip(self.server.project, body['entity_id'], body['clip_fps'])
                    preview = self.server.model_preview(asset, prepared=animation.pop('geometry'))
                    preview['frames'] = animation.pop('frames')
                    preview['animation'] = animation
                    payload, audit = encode_model_glb(preview, clip_fps=body['clip_fps'])
                    check = preview_import(self.server.project, body['entity_id'], payload, binding)
                    if check['changed_axes']:
                        raise ProjectError('Animation GLB export did not preserve its source channels')
                    output = self.server.project.root / 'Exports'
                    _guard_output(output / '.gitignore', self.server.project.root)
                    result = write_encoded_glb(payload, audit, output)
                    binding_path = Path(result['path']).with_suffix('.binding.json')
                    _guard_output(binding_path, self.server.project.root)
                    with binding_path.open('xb') as handle:
                        handle.write((json.dumps(binding, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8'))
                    if not (output / '.gitignore').exists():
                        atomic_write(output / '.gitignore', b'*\n')
                    self._json(200, dict(result, binding=binding, binding_path=str(binding_path),
                                         binding_filename=binding_path.name, byte_length=len(payload),
                                         glb_base64=base64.b64encode(payload).decode('ascii')))
                    return
                if route in ('/api/animation-glb-preview', '/api/animation-glb-pose-preview', '/api/animation-glb-import'):
                    selection={'animation_index':body['animation_index']} if 'animation_index' in body else {}
                    expected = {'entity_id', 'glb_base64', 'binding'}
                    if route == '/api/animation-glb-import':
                        expected.add('review_key')
                    if (set(body)-set(selection) != expected or not isinstance(body['entity_id'], str) or
                            not isinstance(body['binding'], dict) or
                            len(json.dumps(body['binding'], allow_nan=False).encode('utf-8')) > 128 * 1024):
                        raise ProjectError('Animation GLB import requires an actor, bounded binding sidecar and GLB bytes')
                    encoded = body['glb_base64']
                    if not isinstance(encoded, str) or len(encoded) > 44739244:
                        raise ProjectError('Animation GLB exceeds 32 MiB')
                    try:
                        payload = base64.b64decode(encoded, validate=True)
                    except ValueError as exc:
                        raise ProjectError('Animation GLB requires valid base64') from exc
                    if not 1 <= len(payload) <= 32 * 1024 * 1024:
                        raise ProjectError('Animation GLB must contain at most 32 MiB')
                    from .animation_glb import apply_import, pose_import, preview_import
                    if route == '/api/animation-glb-preview':
                        self._json(200, preview_import(self.server.project, body['entity_id'], payload, body['binding'], **selection))
                    elif route == '/api/animation-glb-pose-preview':
                        animation, asset = pose_import(self.server.project, body['entity_id'], payload, body['binding'], **selection)
                        preview = self.server.model_preview(asset, prepared=animation.pop('geometry'))
                        preview['frames'] = animation.pop('frames')
                        animation.update(source_clip_id=body['binding']['animation_id'], clip_id='file-preview', entity_id=body['entity_id'])
                        preview['report'] = animation['proposal']
                        preview['animation'] = animation
                        preview['animation_support'] = {'supported': True, 'clips': [{'id': 'file-preview', 'label': 'Proposed GLB animation'}], 'evidence': 'reviewed_glb_not_applied_or_runtime_verified'}
                        self._json(200, preview)
                    else:
                        apply_import(self.server.project, body['entity_id'], payload, body['binding'], body['review_key'], **selection)
                        self._json(200, self.server.state())
                    return
                if route == '/api/animation-record-allocation-options':
                    if set(body) != {'entity_id','expected_source_key'}:
                        raise ProjectError('Animation allocation options require actor and current scene source')
                    from .animation_allocation import allocation_options
                    self._json(200,allocation_options(self.server.project,body['entity_id'],body['expected_source_key']))
                    return
                if route in ('/api/animation-record-allocation-preview','/api/animation-record-allocation',
                             '/api/animation-record-allocation-pose-preview'):
                    expected = {'entity_id', 'source_frame_indices', 'edits', 'expected_source_key'}
                    if route != '/api/animation-record-allocation-preview':
                        expected.add('review_key')
                    if (set(body) != expected or
                            not isinstance(body['entity_id'], str) or not 1 <= len(body['entity_id']) <= 512 or
                            not isinstance(body['expected_source_key'], str) or
                            len(body['expected_source_key']) != 64 or
                            any(c not in '0123456789abcdef' for c in body['expected_source_key'])):
                        raise ProjectError('Animation allocation review requires actor, frame sequence, edits and current source key')
                    from .animation_allocation import preview_record_allocation
                    if route == '/api/animation-record-allocation-preview':
                        self._json(200, preview_record_allocation(self.server.project, body['entity_id'],
                            body['source_frame_indices'], body['edits'], body['expected_source_key']))
                    elif route == '/api/animation-record-allocation-pose-preview':
                        from .animation_allocation import pose_record_allocation
                        animation,asset = pose_record_allocation(self.server.project,body['entity_id'],
                            body['source_frame_indices'],body['edits'],body['expected_source_key'],body['review_key'])
                        geometry = animation.pop('geometry')
                        geometry['frames'] = animation.pop('frames')
                        preview = self.server.model_preview(asset,prepared=geometry,effective_shape=True)
                        preview['report'] = animation['proposal']
                        preview['animation'] = animation
                        preview['animation_support'] = dict(supported=True,
                            clips=[dict(id='allocation-preview',label='Proposed allocated clip')],
                            evidence='reviewed_unassigned_clip_not_applied_or_runtime_verified')
                        self._json(200,preview)
                    else:
                        self.server.project.command(dict(type='allocate_animation_record',**body))
                        self._json(200,self.server.state())
                    return
                if route in ('/api/animation-record-activation-preview','/api/animation-record-activation'):
                    expected = {'scene_id','record_id','active','expected_source_key'}
                    if route == '/api/animation-record-activation':
                        expected.add('review_key')
                    if set(body) != expected:
                        raise ProjectError('Animation activation requires scene, record, boolean and current source key')
                    from .animation_allocation import prepare_record_activation
                    if route == '/api/animation-record-activation-preview':
                        self._json(200,prepare_record_activation(self.server.project,body['scene_id'],
                            body['record_id'],body['active'],body['expected_source_key'])[1])
                    else:
                        self.server.project.command(dict(type='set_animation_record_active',**body))
                        self._json(200,self.server.state())
                    return
                if route in ('/api/animation-record-glb-review','/api/animation-record-glb-pose','/api/animation-record-glb-import'):
                    expected={'scene_id','record_id','source_frame_indices','expected_source_key','glb_base64','binding'}
                    if route!='/api/animation-record-glb-review':expected.add('review_key')
                    if set(body)-{'animation_index'}!=expected or not isinstance(body['binding'],dict) or len(json.dumps(body['binding'],allow_nan=False).encode('utf-8'))>128*1024:
                        raise ProjectError('Retained GLB requires exact scene, clip, output mapping, source, bounded sidecar and bytes')
                    encoded=body['glb_base64']
                    if not isinstance(encoded,str) or len(encoded)>44739244:raise ProjectError('Retained GLB exceeds 32 MiB')
                    try:payload=base64.b64decode(encoded,validate=True)
                    except ValueError as exc:raise ProjectError('Retained GLB requires valid base64') from exc
                    if not 1<=len(payload)<=32*1024*1024:raise ProjectError('Retained GLB must contain at most 32 MiB')
                    from .animation_record_glb import prepare_import,pose_import,apply_import
                    request={k:v for k,v in body.items() if k!='glb_base64'};request['content']=payload
                    if route=='/api/animation-record-glb-review':
                        self._json(200,prepare_import(self.server.project,**request)[1])
                    elif route=='/api/animation-record-glb-pose':
                        animation,asset,report=pose_import(self.server.project,**request)
                        preview=self.server.model_preview(asset,prepared=animation.pop('geometry'),effective_shape=True)
                        preview['frames']=animation.pop('frames');preview['animation']=animation;preview['report']=report
                        preview['animation_support']=dict(supported=True,clips=[dict(id='allocated-record-edit-preview',label='Proposed retained GLB content')],evidence='reviewed_retained_glb_not_applied')
                        self._json(200,preview)
                    else:
                        report=apply_import(self.server.project,**request)
                        self._json(200,dict(self.server.state(),retained_glb_report=report))
                    return
                if route=='/api/animation-record-edit-options':
                    if set(body)!={'scene_id','record_id','expected_source_key'}:raise ProjectError('Retained editor options require exact scene, clip and source')
                    from .animation_record_edit import options
                    self._json(200,options(self.server.project,**body))
                    return
                if route in ('/api/animation-record-edit-review','/api/animation-record-edit-pose','/api/animation-record-edit'):
                    fields={'scene_id','record_id','source_frame_indices','edits','expected_source_key'}
                    if not route.endswith('-review'):fields.add('review_key')
                    if set(body)!=fields:raise ProjectError('Retained edit requires exact scene, identity, frame mapping, axes and current source')
                    from .animation_record_edit import prepare,pose
                    if route.endswith('-review'):
                        self._json(200,prepare(self.server.project,**body)[1])
                    elif route.endswith('-pose'):
                        animation,asset,report=pose(self.server.project,body)
                        geometry=animation.pop('geometry');geometry['frames']=animation.pop('frames')
                        preview=self.server.model_preview(asset,prepared=geometry,effective_shape=True)
                        preview['animation']=animation
                        preview['animation_support']=dict(supported=True,clips=[dict(id='allocated-record-edit-preview',label='Proposed retained clip content')])
                        self._json(200,preview)
                    else:
                        self.server.project.command(dict(type='edit_animation_record',**body))
                        self._json(200,self.server.state())
                    return
                if route in ('/api/allocated-animation-assignment-review','/api/allocated-animation-assignment-pose','/api/allocated-animation-assignment'):
                    expected={'entity_id','record_id','expected_source_key'}
                    if not route.endswith('-review'):
                        expected.add('review_key')
                    if set(body)!=expected:
                        raise ProjectError('Allocated clip assignment review requires exact actor, record and current source fields')
                    from .allocated_animation_assignment import review,pose_preview
                    if route.endswith('-review'):
                        self._json(200,review(self.server.project,body['entity_id'],body['record_id'],body['expected_source_key']))
                    elif route.endswith('-pose'):
                        animation,asset,report=pose_preview(self.server.project,body['entity_id'],body['record_id'],body['expected_source_key'],body['review_key'])
                        geometry=animation.pop('geometry');geometry['frames']=animation.pop('frames')
                        preview=self.server.model_preview(asset,prepared=geometry,effective_shape=True)
                        preview['animation']=animation;preview['report']=report
                        preview['animation_support']=dict(supported=True,clips=[dict(id='allocated-assignment-preview',label='Proposed initial allocated clip')],
                            evidence='reviewed_initial_header_proposal_not_applied_or_runtime_verified')
                        self._json(200,preview)
                    else:
                        self.server.project.command(dict(type='set_actor_allocated_animation',**body))
                        self._json(200,self.server.state())
                    return
                if route=='/api/retained-animation-preview':
                    if set(body)!={'asset_id','expected_source_key'}:raise ProjectError('Retained preview requires exact asset identity and current source')
                    from .retained_animation_assets import preview as retained_preview
                    animation,asset,view=retained_preview(self.server.project,**body)
                    geometry=animation.pop('geometry');geometry['frames']=animation.pop('frames')
                    preview=self.server.model_preview(asset,prepared=geometry,effective_shape=True,project_view=view)
                    preview['animation']=animation
                    preview['animation_support']=dict(supported=True,clips=[dict(id='allocated-record',label='Retained clip source')])
                    self._json(200,preview)
                    return
                if route in ('/api/animation-record-duplicate-review','/api/animation-record-duplicate'):
                    expected={'scene_id','record_id','expected_source_key'}
                    if route=='/api/animation-record-duplicate':expected.add('review_key')
                    if set(body)!=expected:raise ProjectError('Clip duplication requires exact scene, record and current source')
                    from .animation_record_duplicate import prepare
                    if route.endswith('-review'):
                        self._json(200,prepare(self.server.project,**body)[1])
                    else:
                        self.server.project.command(dict(type='duplicate_animation_record',**body))
                        self._json(200,self.server.state())
                    return
                if route in ('/api/animation-record-library','/api/animation-record-pose'):
                    expected = {'scene_id','expected_source_key'}
                    if route == '/api/animation-record-pose':
                        expected.add('record_id')
                    if set(body) != expected:
                        raise ProjectError('Allocated clip inspection requires exact scene, source and record fields')
                    from .animation_allocation import record_library, pose_saved_record
                    if route == '/api/animation-record-library':
                        self._json(200,record_library(self.server.project,body['scene_id'],body['expected_source_key']))
                    else:
                        animation,asset = pose_saved_record(self.server.project,body['scene_id'],body['record_id'],body['expected_source_key'])
                        geometry = animation.pop('geometry')
                        geometry['frames'] = animation.pop('frames')
                        preview = self.server.model_preview(asset,prepared=geometry,effective_shape=True)
                        preview['animation'] = animation
                        preview['animation_support'] = dict(supported=True,
                            clips=[dict(id='allocated-record',label='Saved allocated clip')],
                            evidence='retained_unassigned_clip_not_runtime_verified')
                        self._json(200,preview)
                    return
                if route == '/api/animation-record-source':
                    if set(body) - {'entity_id', 'layer', 'format'} or not isinstance(body.get('entity_id'), str) or not body['entity_id'].strip():
                        raise ProjectError('Animation source requires actor identity and optional layer and format only')
                    payload, binding = self.server.project.animation_record_source(body['entity_id'], body.get('layer', 'retail'), body.get('format', 'record'))
                    self._json(200, {'entity_id': body['entity_id'], 'binding': binding,
                                     'representation': body.get('layer', 'retail'), 'byte_length': len(payload),
                                     'record_base64': base64.b64encode(payload).decode('ascii')})
                    return
                if route in ('/api/animation-record-replacement', '/api/animation-record-preview', '/api/animation-file-pose-preview'):
                    if not {'entity_id', 'record_base64'} <= set(body) or set(body) - {'entity_id', 'record_base64', 'format'} or not isinstance(body['entity_id'], str) or not body['entity_id'].strip():
                        raise ProjectError('Animation upload requires actor identity and record_base64 and optional format')
                    encoded = body['record_base64']
                    if not isinstance(encoded, str) or len(encoded) > 5592408:
                        raise ProjectError('Animation record exceeds the 4 MiB limit')
                    try:
                        payload = base64.b64decode(encoded, validate=True)
                    except ValueError as exc:
                        raise ProjectError('Animation record requires valid base64') from exc
                    if route == '/api/animation-file-pose-preview':
                        animation, asset = self.server.project.animation_file_pose_preview(body['entity_id'], payload, body.get('format', 'record'))
                        preview = self.server.model_preview(asset, prepared=animation.pop('geometry'))
                        preview['frames'] = animation.pop('frames')
                        animation.update(source_clip_id=animation['clip_id'], clip_id='file-preview', entity_id=body['entity_id'])
                        preview['animation'] = animation
                        preview['animation_support'] = {'supported': True, 'clips': [], 'evidence': 'proposed_file_not_applied_or_runtime_verified'}
                        self._json(200, preview)
                        return
                    if route == '/api/animation-record-preview':
                        self._json(200, self.server.project.preview_animation_record(body['entity_id'], payload, body.get('format', 'record')))
                        return
                    self.server.project.import_animation_record(body['entity_id'], payload, body.get('format', 'record'))
                    self._json(200, self.server.state())
                    return
                if route == "/api/animation-channel-values":
                    if set(body) != {"entity_id", "frame_index", "object_index"} or not isinstance(body.get("entity_id"), str):
                        raise ProjectError("Channel inspection requires an actor, frame and object index only")
                    self._json(200, self.server.project.animation_channel_values(body["entity_id"], body["frame_index"], body["object_index"]))
                    return
                if route == "/api/animation-authoring-options":
                    if set(body) != {"entity_id"} or not isinstance(body.get("entity_id"), str):
                        raise ProjectError("Animation options require an actor identity only")
                    self._json(200, self.server.project.animation_authoring_options(body["entity_id"]))
                    return
                if route == '/api/actor-animation-options':
                    if (set(body) != {'entity_id'} or not isinstance(body.get('entity_id'), str) or
                            not any(a['semantic_id'] == body['entity_id'] for a in
                                    self.server.project.imports.get(self.server.project.active_scene, {}).get('actors', []))):
                        raise ProjectError('Initial animation options require an actor identity only')
                    from .actor_animation import options
                    self._json(200, options(self.server.project, body['entity_id']))
                    return
                if route == '/api/actor-animation-review':
                    if (set(body) != {'entity_id', 'animation_asset_id', 'source_key'} or not isinstance(body.get('entity_id'), str) or
                            not isinstance(body.get('source_key'), str) or len(body['source_key']) != 64 or
                            any(c not in '0123456789abcdef' for c in body['source_key'])):
                        raise ProjectError('Initial animation review requires actor, clip and source identity only')
                    from .actor_animation import review
                    self._json(200, review(self.server.project, body['entity_id'], body['animation_asset_id'], body['source_key']))
                    return
                if route in ("/api/actor-appearance-options", "/api/actor-appearance-preview", "/api/export/actor-appearance"):
                    exporting = route == "/api/export/actor-appearance"
                    expected = {"entity_id", "clip_fps" if "clip_fps" in body else "frame_index"} if exporting else {"entity_id"}
                    if set(body) != expected or not isinstance(body.get("entity_id"), str) or not body["entity_id"]:
                        raise ProjectError("Appearance requests accept only an imported entity_id and export frame or clip rate; source bindings are project-controlled")
                    if not any(a["semantic_id"] == body["entity_id"] for a in self.server.project.imports.get(self.server.project.active_scene, {}).get("actors", [])):
                        raise ProjectError("Appearance request requires an actor in the active scene")
                    if route == "/api/actor-appearance-options":
                        self._json(200, self.server.project.appearance_options(body["entity_id"]))
                        return
                    frame_index = body.get("frame_index")
                    clip_fps = None
                    if exporting:
                        frame_index, clip_fps = _animation_export_choice(body)
                    preview = self.server.actor_appearance_preview(body["entity_id"])
                    self._json(200, self.server.export_preview(preview, frame_index, clip_fps) if exporting else preview)
                    return
                if route in ('/api/actor-initial-animation-preview', '/api/export/actor-initial-animation'):
                    exporting = route.startswith('/api/export/')
                    expected = {'entity_id', 'clip_fps' if 'clip_fps' in body else 'frame_index'} if exporting else {'entity_id'}
                    if set(body) != expected or not isinstance(body.get('entity_id'), str) or not body['entity_id']:
                        raise ProjectError('Initial animation requests accept only an active actor and export frame/rate')
                    frame_index, clip_fps = _animation_export_choice(body) if exporting else (None, None)
                    preview = self.server.actor_initial_animation_preview(body['entity_id'])
                    self._json(200, self.server.export_preview(preview, frame_index, clip_fps) if exporting else preview)
                    return
                if route == '/api/draft-output-review':
                    if set(body) != {'source_key'}:
                        raise ProjectError('NPC output review accepts only the current source_key')
                    self._json(200, self.server.review_actor_drafts(body['source_key']))
                    return
                if route == "/api/export/actor-drafts":
                    if set(body) != {"entity_id"} or not isinstance(body["entity_id"], str) or not body["entity_id"]:
                        raise ProjectError("Draft export accepts only a draft entity_id")
                    self._json(200, self.server.export_actor_drafts(body["entity_id"]))
                    return
                if route == '/api/export/project':
                    if body:
                        raise ProjectError('Project export accepts no fields')
                    self._json(200, self.server.export_actor_drafts())
                    return
                if route in ('/api/exports', '/api/exports/verify'):
                    from .export_history import list_exports, verify_export
                    if route == '/api/exports':
                        if body:
                            raise ProjectError('Export history accepts no fields')
                        result = list_exports(self.server.project)
                    else:
                        if set(body) != {'id'}:
                            raise ProjectError('Export verification requires an export id')
                        result = verify_export(self.server.project, body['id'])
                    self._json(200, result)
                    return
                if route == '/api/exports/open-copy':
                    from .export_history import copy_export_inputs
                    if set(body)!={'id'}:
                        raise ProjectError('Open export copy requires an export id')
                    if self.server.project.mode!='edit' or self.server.project.dirty:
                        raise ProjectError('Save the current project in Edit mode before opening an export copy')
                    destination=copy_export_inputs(self.server.project,body['id'])
                    self._command('/api/project/open',{'path':str(destination)})
                    self._json(200,self.server.state())
                    return
                if route == "/api/actor-candidate-inspection":
                    if set(body) != {"entity_id"} or not isinstance(body["entity_id"], str) or not body["entity_id"]:
                        raise ProjectError("Actor candidate inspection accepts only an imported entity_id")
                    self._json(200, self.server.actor_candidate_inspection(body["entity_id"]))
                    return
                if route == "/api/text-font":
                    if set(body) != {"entity_id"}:
                        raise ProjectError("Text font preview accepts only entity_id")
                    self._json(200, self.server.project.dialogue_font(body["entity_id"]))
                    return
                if route == "/api/text-json-source":
                    if set(body) != {"entity_id"}:
                        raise ProjectError("Text JSON export accepts only entity_id")
                    self._json(200, self.server.project.dialogue_json_source(body["entity_id"]))
                    return
                if route in ("/api/text-json-preview", "/api/text-json-import"):
                    if set(body) != {"entity_id", "json_base64"} or not isinstance(body["json_base64"], str) or len(body["json_base64"]) > 1398104:
                        raise ProjectError("Text JSON accepts only owner and bounded base64 file")
                    try:
                        content = base64.b64decode(body["json_base64"], validate=True)
                    except ValueError as exc:
                        raise ProjectError("Text JSON requires valid base64") from exc
                    project = self.server.project
                    result = (project.preview_dialogue_json if route.endswith("preview") else project.import_dialogue_json)(body["entity_id"], content)
                    self._json(200, self.server.state() if route.endswith("import") else result)
                    return
                if route=='/api/npc-script-comparison':
                    if set(body)!={'entity_id','build_id'}:raise ProjectError('NPC script comparison accepts authored NPC and saved Build identities only')
                    from .npc_script_compare import compare as compare_npc_scripts
                    self._json(200,compare_npc_scripts(self.server.project,body['entity_id'],body['build_id']));return
                if route=='/api/npc-movement-source':
                    from .npc_movement import source
                    if set(body)!={'entity_id'}:raise ProjectError('NPC movement source requires identity only')
                    self._json(200,source(self.server.project,body['entity_id']));return
                if route=='/api/npc-movement-review':
                    from .npc_movement import review
                    self._json(200,review(self.server.project,body));return
                if route=='/api/npc-branches-source':
                    from .npc_branches import source
                    if set(body)!={'entity_id'}:raise ProjectError('NPC branches source requires identity only')
                    self._json(200,source(self.server.project,body['entity_id']));return
                if route=='/api/npc-branches-review':
                    from .npc_branches import review
                    self._json(200,review(self.server.project,body));return
                if route=='/api/npc-model-selectors-source':
                    from .npc_model_selectors import source
                    if set(body)!={'entity_id'}:raise ProjectError('NPC model selectors source requires identity only')
                    self._json(200,source(self.server.project,body['entity_id']));return
                if route=='/api/npc-model-selectors-review':
                    from .npc_model_selectors import review
                    self._json(200,review(self.server.project,body));return
                if route=='/api/npc-flags-source':
                    from .npc_flags import source
                    if set(body)!={'entity_id'}:raise ProjectError('NPC flags source requires identity only')
                    self._json(200,source(self.server.project,body['entity_id']));return
                if route=='/api/npc-flags-review':
                    from .npc_flags import review
                    self._json(200,review(self.server.project,body));return
                if route=='/api/npc-facing-source':
                    from .npc_facing import source
                    if set(body)!={'entity_id'}:raise ProjectError('NPC facing source requires identity only')
                    self._json(200,source(self.server.project,body['entity_id']));return
                if route=='/api/npc-facing-review':
                    from .npc_facing import review
                    self._json(200,review(self.server.project,body));return
                if route=='/api/npc-waits-source':
                    from .npc_waits import source
                    if set(body)!={'entity_id'}:raise ProjectError('NPC wait source requires identity only')
                    self._json(200,source(self.server.project,body['entity_id']));return
                if route=='/api/npc-waits-review':
                    from .npc_waits import review
                    self._json(200,review(self.server.project,body));return
                if route=='/api/npc-appearance-source':
                    from .npc_appearance import source
                    if set(body)!={'entity_id'}:raise ProjectError('NPC appearance source requires identity only')
                    self._json(200,source(self.server.project,body['entity_id']));return
                if route=='/api/npc-appearance-review':
                    from .npc_appearance import review
                    self._json(200,review(self.server.project,body));return
                if route=='/api/npc-appearance-scene':
                    from .npc_appearance import review,proposal_view
                    from .project_copy import source_key
                    from .scene_preview import source_key as preview_source_key
                    from importer.scene_animation import load_scene_actor_animation_catalog
                    from importer.environment import load_environment_preview_catalog
                    from .terrain_preview import terrain_preview
                    if set(body)!={'entity_id','donor_entity_id','review_key'}:raise ProjectError('NPC appearance scene requires exact reviewed fields')
                    project=self.server.project;report=review(project,{k:body[k] for k in ('entity_id','donor_entity_id')})
                    if body['review_key']!=report['review_key']:raise ProjectError('NPC appearance changed since review')
                    scene_key=preview_source_key(project);view=proposal_view(project,report)
                    proposed=self.server.scene_previews.preview(view,lambda asset,*args,**kwargs:self.server.model_preview(asset,*args,effective_shape=True,project_view=view,**kwargs),load_scene_actor_animation_catalog,load_environment_preview_catalog,terrain_preview)
                    if source_key(project)!=report['project_source_key'] or preview_source_key(project)!=scene_key:raise ProjectError('Project changed during NPC appearance scene inspection')
                    self._json(200,dict(schema_version='legaia.npc-appearance-scene.v1',review=report,scene_preview_source_key=scene_key,scene=dict(proposed,representation='authored')));return
                if route=='/api/npc-dialogue-source':
                    from .npc_dialogue import source
                    if set(body)!={'entity_id'}:raise ProjectError('NPC dialogue source requires identity only')
                    self._json(200,source(self.server.project,body['entity_id']));return
                if route=='/api/npc-dialogue-review':
                    from .npc_dialogue import review
                    self._json(200,review(self.server.project,body));return
                if route=='/api/npc-build-script':
                    if set(body)!={'entity_id','build_id'}:raise ProjectError('Saved NPC script accepts authored NPC and saved Build identities only')
                    from .npc_build_script import inspect as inspect_npc_build_script
                    self._json(200,inspect_npc_build_script(self.server.project,body['entity_id'],body['build_id']));return
                if route=='/api/npc-donor-script':
                    if set(body)!={'entity_id'} or not isinstance(body['entity_id'],str):raise ProjectError('NPC donor script accepts only an authored entity identity')
                    from .npc_donor_script import inspect as inspect_npc_donor_script
                    self._json(200,inspect_npc_donor_script(self.server.project,body['entity_id']));return
                if route == "/api/actor-script":
                    if set(body) != {"entity_id"} or not isinstance(body["entity_id"], str) or not body["entity_id"]:
                        raise ProjectError("Script inspection accepts only an imported entity_id; bytes, addresses and paths are not accepted")
                    self._json(200, self.server.actor_script_preview(body["entity_id"]))
                    return
                if route=='/api/export/allocated-animation':
                    self._json(200,self.server.export_allocated_animation(body))
                    return
                if route in ("/api/actor-animation-preview", "/api/export/actor-animation"):
                    exporting = route == "/api/export/actor-animation"
                    allowed = {"entity_id", "representation", "frame_index", "clip_fps"} if exporting else {"entity_id", "representation"}
                    if set(body) - allowed or not isinstance(body.get("entity_id"), str) or not body["entity_id"]:
                        raise ProjectError("Actor animation accepts an imported entity_id and export frame or clip rate only; source bindings and output paths are project-controlled")
                    frame_index = body.get("frame_index")
                    clip_fps = None
                    if exporting:
                        frame_index, clip_fps = _animation_export_choice(body)
                    preview = self.server.actor_animation_preview(body["entity_id"], body.get("representation", "imported"))
                    self._json(200, self.server.export_preview(preview, frame_index, clip_fps) if exporting else preview)
                    return
                if route == '/api/scene-animation-preview':
                    if set(body) != {'representation', 'source_key'} or body['representation'] not in ('retail', 'authored') or not isinstance(body['source_key'], str):
                        raise ProjectError('Scene animation requires an explicit representation and current source key')
                    self._json(200, self.server.scene_animation_preview(body['representation'], body['source_key']))
                    return
                if route in ("/api/scene-preview", "/api/export/scene"):
                    exporting = route == "/api/export/scene"
                    if set(body) - ({'representation', 'source_key', 'entity_id'} if exporting else {'representation'}):
                        raise ProjectError("Scene preview uses the active imported scene; client geometry and paths are not accepted")
                    from .scene_preview import preview_project, source_key
                    from importer.scene_animation import load_scene_actor_animation_catalog
                    from importer.environment import load_environment_preview_catalog
                    from .terrain_preview import terrain_preview
                    representation = body.get('representation', 'authored')
                    original_key = source_key(self.server.project)
                    if exporting and (not original_key or body.get("source_key") != original_key):
                        raise ProjectError("Scene export source changed; refresh the scene before exporting")
                    view = preview_project(self.server.project, representation)
                    preview = self.server.scene_previews.preview(
                        view, lambda asset, *args, **kwargs: self.server.model_preview(asset, *args, effective_shape=True, project_view=view, **kwargs),
                        load_scene_actor_animation_catalog, load_environment_preview_catalog, terrain_preview)
                    if source_key(self.server.project) != original_key:
                        raise ProjectError('Project changed during scene comparison preview')
                    preview['representation'] = representation
                    preview['project_source_key'] = original_key
                    if exporting:
                        from importer.scene_export import encode_scene_glb, select_scene_export_instance
                        if "entity_id" in body:
                            preview = select_scene_export_instance(preview, body["entity_id"])
                        from importer.export import write_encoded_glb
                        data, audit = encode_scene_glb(preview)
                        if source_key(self.server.project) != original_key:
                            raise ProjectError('Scene changed during export; refresh and retry')
                        self._json(200, write_encoded_glb(data, audit, self.server.project.root / 'Exports', 'scene'))
                    else:
                        self._json(200, preview)
                    return
                if route == '/api/terrain-point':
                    from .scene_preview import source_key, sample_preview_ground
                    from .terrain_preview import terrain_preview
                    import math
                    if (set(body)!={'x','z','source_key'} or any(type(body[a]) not in (int,float) or not math.isfinite(body[a]) or not 0<=body[a]<=16384 for a in ('x','z'))):
                        raise ProjectError('Terrain point requires bounded X/Z and a preview source key')
                    key=source_key(self.server.project)
                    if not key or body['source_key']!=key:
                        raise ProjectError('Terrain point source changed; refresh the scene')
                    sample=sample_preview_ground(terrain_preview(self.server.project),body['x'],body['z'])
                    if source_key(self.server.project)!=key:
                        raise ProjectError('Terrain source changed during sampling')
                    self._json(200,dict(source_key=key,scene_id=self.server.project.active_scene,
                        position=dict(x=body['x'],y=sample['y'] if sample else None,z=body['z']),
                        sample=sample,evidence='source terrain preview; runtime elevation unverified'))
                    return
                if route in ("/api/preview", "/api/animation-preview", "/api/export/model"):
                    project = self.server.project
                    if not project.disc_path:
                        raise ProjectError("Model preview requires the project's user-owned disc")
                    if not isinstance(body.get("asset_id"), str):
                        raise ProjectError("asset_id must be a model asset string")
                    asset = project.assets.records.get(body.get("asset_id"))
                    if asset is None:
                        raise ProjectError("Unknown model asset")
                    clip_id = body.get("clip_id") if route != "/api/preview" else None
                    if route == "/api/animation-preview" or clip_id is not None:
                        from importer.animation import animation_capabilities
                        clips = [clip['id'] for clip in animation_capabilities(asset)['clips']]
                        if not clips:
                            raise ProjectError("This model does not support animation preview with a verified clip")
                        if clip_id not in clips:
                            raise ProjectError("Choose a supported animation clip for this model: " + ", ".join(clips))
                    if route == "/api/export/model":
                        if set(body) - {"asset_id", "clip_id", "frame_index", "clip_fps"}:
                            raise ProjectError("Export accepts asset, clip and frame or clip rate only; geometry and output paths are project-controlled")
                        frame_index = body.get("frame_index")
                        if clip_id is None and (frame_index is not None or "clip_fps" in body):
                            raise ProjectError("A frame export requires a supported animation clip")
                        clip_fps = None
                        if clip_id is not None:
                            frame_index, clip_fps = _animation_export_choice(body)
                        preview = self.server.model_preview(asset, clip_id)
                        self._json(200, self.server.export_preview(preview, frame_index, clip_fps))
                        return
                    self._json(200, self.server.model_preview(asset, clip_id))
                    return
                if route in ('/api/npc-preset-review','/api/npc-preset-scene'):
                    from .npc_presets import review,proposal_view
                    fields={'template_id','name','position','expected_source_key'}
                    if set(body)!=(fields|{'review_key'} if route.endswith('-scene') else fields):raise ProjectError('NPC preset request has unsupported fields')
                    report=review(self.server.project,{k:body[k] for k in fields})
                    if route.endswith('-review'):
                        self._json(200,report);return
                    if body['review_key']!=report['review_key']:raise ProjectError('NPC preset changed since review')
                    from .project_copy import source_key
                    from importer.scene_animation import load_scene_actor_animation_catalog
                    from importer.environment import load_environment_preview_catalog
                    from .terrain_preview import terrain_preview
                    view=proposal_view(self.server.project,report)
                    proposed=self.server.scene_previews.preview(view,lambda asset,*args,**kwargs:self.server.model_preview(asset,*args,effective_shape=True,project_view=view,**kwargs),load_scene_actor_animation_catalog,load_environment_preview_catalog,terrain_preview)
                    if source_key(self.server.project)!=report['project_source_key']:raise ProjectError('Project changed during NPC preset scene inspection')
                    self._json(200,dict(schema_version='legaia.npc-preset-scene.v1',review=report,scene=dict(proposed,representation='authored')));return
                if route=='/api/draft-donor-group':
                    from .draft_donor_group import review as donor_review,proposal_view
                    from .project_copy import source_key as project_source_key
                    from importer.scene_animation import load_scene_actor_animation_catalog
                    from importer.environment import load_environment_preview_catalog
                    from .terrain_preview import terrain_preview
                    project=self.server.project;report=donor_review(project,body);view=proposal_view(project,report)
                    proposed=self.server.scene_previews.preview(view,lambda asset,*args,**kwargs:self.server.model_preview(asset,*args,effective_shape=True,project_view=view,**kwargs),load_scene_actor_animation_catalog,load_environment_preview_catalog,terrain_preview)
                    if project_source_key(project)!=report['project_source_key']:raise ProjectError('Project changed during NPC donor proposal')
                    self._json(200,dict(schema_version='legaia.draft-donor-group-proposal.v1',review=report,scene=dict(proposed,representation='authored')));return
                if route in ('/api/draft-group','/api/draft-group-scene'):
                    from .draft_group import review as draft_group_review, proposal_view
                    fields={'entity_ids','remove' if 'remove' in body else 'layout' if 'layout' in body else 'delta'}
                    if set(body)!=(fields|{'review_key'} if route.endswith('-scene') else fields):
                        raise ProjectError('NPC draft group request has unsupported fields')
                    project=self.server.project
                    report=draft_group_review(project,{key:body[key] for key in fields})
                    if route=='/api/draft-group':
                        self._json(200,report)
                        return
                    if body['review_key']!=report['review_key']:
                        raise ProjectError('NPC draft group changed since review')
                    from .project_copy import source_key as project_source_key
                    from importer.scene_animation import load_scene_actor_animation_catalog
                    from importer.environment import load_environment_preview_catalog
                    from .terrain_preview import terrain_preview
                    view=proposal_view(project,report)
                    proposed=self.server.scene_previews.preview(
                        view,lambda asset,*args,**kwargs:self.server.model_preview(asset,*args,effective_shape=True,project_view=view,**kwargs),
                        load_scene_actor_animation_catalog,load_environment_preview_catalog,terrain_preview)
                    if project_source_key(project)!=report['project_source_key']:
                        raise ProjectError('Project changed during NPC draft group scene inspection')
                    self._json(200,dict(schema_version='legaia.draft-group-scene.v1',scene_id=report['scene_id'],
                        project_source_key=report['project_source_key'],scene_preview_source_key=report['scene_preview_source_key'],
                        review_key=report['review_key'],scene=dict(proposed,representation='authored')))
                    return
                if route in ('/api/draft-repeat','/api/draft-repeat-scene'):
                    from .draft_repeat import preview as draft_repeat_preview, proposal_view
                    if 'entity_ids' in body:
                        from .draft_repeat_group import preview as draft_repeat_preview,proposal_view
                    fields={'entity_ids','count','step'} if 'entity_ids' in body else {'entity_id','count','step','name'}
                    if 'columns' in body:fields.add('columns')
                    if set(body)!=(fields|{'review_key'} if route.endswith('-scene') else fields):
                        raise ProjectError('Draft repeat request has unsupported fields')
                    project=self.server.project
                    report=draft_repeat_preview(project,{key:body[key] for key in fields})
                    if route=='/api/draft-repeat':
                        self._json(200,report)
                        return
                    if body['review_key']!=report['review_key']:
                        raise ProjectError('NPC drafts changed since preview; review the copies again')
                    from .scene_preview import source_key
                    from importer.scene_animation import load_scene_actor_animation_catalog
                    from importer.environment import load_environment_preview_catalog
                    from .terrain_preview import terrain_preview
                    original_key=source_key(project);view=proposal_view(project,report)
                    proposed=self.server.scene_previews.preview(
                        view,lambda asset,*args,**kwargs:self.server.model_preview(asset,*args,effective_shape=True,project_view=view,**kwargs),
                        load_scene_actor_animation_catalog,load_environment_preview_catalog,terrain_preview)
                    if source_key(project)!=original_key:
                        raise ProjectError('Scene changed during repeated draft inspection')
                    self._json(200,{'schema_version':'legaia.draft-repeat-scene.v1','scene_id':report['scene_id'],
                                    'project_source_key':original_key,'review_key':report['review_key'],
                                    'scene':dict(proposed,representation='authored')})
                    return
                if route in ("/api/actor-placement-batch-scene", "/api/actor-placement-layout-scene"):
                    is_layout = route == "/api/actor-placement-layout-scene"
                    field = 'layout' if is_layout else 'delta'
                    if set(body) != {'actor_ids', field, 'review_key'}:
                        raise ProjectError('Actor group scene inspection requires actors, a placement operation and reviewed identity only')
                    from .scene_preview import actor_placement_proposal_view, source_key
                    from importer.scene_animation import load_scene_actor_animation_catalog
                    from importer.environment import load_environment_preview_catalog
                    from .terrain_preview import terrain_preview
                    project = self.server.project
                    report = (project.actor_placement_layout(body['actor_ids'], body['layout']) if is_layout
                              else project.actor_placement_batch(body['actor_ids'], body['delta']))
                    if body['review_key'] != report['review_key']:
                        raise ProjectError('Actor group changed since preview; preview it again')
                    original_key = source_key(project)
                    view = actor_placement_proposal_view(project, report)
                    proposed = self.server.scene_previews.preview(
                        view, lambda asset, *args, **kwargs: self.server.model_preview(asset, *args, effective_shape=True, project_view=view, **kwargs),
                        load_scene_actor_animation_catalog, load_environment_preview_catalog, terrain_preview)
                    if source_key(project) != original_key:
                        raise ProjectError('Scene changed during group inspection')
                    targets = {row['entity_id'] for row in report['targets']}
                    self._json(200, {'schema_version': 'legaia.actor-placement-scene.v1',
                                     'scene_id': report['scene_id'], 'project_source_key': original_key,
                                     'review_key': report['review_key'],
                                     'positions': [{key: deepcopy(entity[key]) for key in
                                                    ('entity_id', 'position', 'preview_position', 'display_position', 'preview_height_status')}
                                                   for entity in proposed['entities'] if entity['entity_id'] in targets]})
                    return
                if route == "/api/actor-appearance-batch-scene":
                    if set(body) != {'actor_ids', 'donor_entity_id', 'review_key'}:
                        raise ProjectError('Group appearance scene inspection requires actors, donor and review identity only')
                    if not isinstance(body['donor_entity_id'], str) or not isinstance(body['review_key'], str):
                        raise ProjectError('Choose a reviewed donor before scene inspection')
                    from .scene_preview import actor_appearance_proposal_view, source_key
                    from importer.scene_animation import load_scene_actor_animation_catalog
                    from importer.environment import load_environment_preview_catalog
                    from .terrain_preview import terrain_preview
                    project = self.server.project
                    report = project.actor_appearance_batch(body['actor_ids'], body['donor_entity_id'])
                    if body['review_key'] != report['review_key']:
                        raise ProjectError('Actor group appearance changed since review')
                    original_key = source_key(project)
                    view = actor_appearance_proposal_view(project, report)
                    proposed = self.server.scene_previews.preview(
                        view, lambda asset, *args, **kwargs: self.server.model_preview(asset, *args, effective_shape=True, project_view=view, **kwargs),
                        load_scene_actor_animation_catalog, load_environment_preview_catalog, terrain_preview)
                    if source_key(project) != original_key:
                        raise ProjectError('Scene changed during group appearance inspection')
                    self._json(200, {'schema_version': 'legaia.actor-appearance-scene.v1',
                                     'scene_id': report['scene_id'], 'project_source_key': original_key,
                                     'review_key': report['review_key'],
                                     'scene': dict(proposed, representation='authored')})
                    return
                if route == "/api/actor-appearance-batch":
                    if set(body) != {"actor_ids", "donor_entity_id"}:
                        raise ProjectError("Group appearance preview accepts actor identities and donor only")
                    self._json(200, self.server.project.actor_appearance_batch(body['actor_ids'], body['donor_entity_id']))
                    return
                if route == "/api/actor-component-batch":
                    if set(body) != {"actor_ids", "component"}:
                        raise ProjectError("Group component review accepts actor identities and component only")
                    self._json(200, self.server.project.actor_component_batch(body['actor_ids'], body['component']))
                    return
                if route == "/api/actor-placement-layout":
                    if set(body) != {'actor_ids', 'layout'}:
                        raise ProjectError('Group layout preview accepts actors and layout only')
                    self._json(200, self.server.project.actor_placement_layout(body['actor_ids'], body['layout']))
                    return
                if route == "/api/actor-placement-batch":
                    if set(body) != {"actor_ids", "delta"}:
                        raise ProjectError("Actor group preview accepts actor identities and X/Z delta only")
                    self._json(200, self.server.project.actor_placement_batch(body['actor_ids'], body['delta']))
                    return
                self._command(urlsplit(self.path).path, body)
                self._json(200, self.server.state())
        except (RetailImportError, ProjectError, ValueError, KeyError, TypeError, OSError) as exc:
            self._json(400, {"error": str(exc)})

    def _command(self, route: str, body: dict) -> None:
        project = self.server.project
        # Reject malformed field types before they reach filesystem/importer services.
        required_strings = {"/api/project/new": ("path",), "/api/project/open": ("path",),
                            "/api/import": ("disc",), "/api/scene": ("scene_id",)}
        if route == '/api/command' and body.get('type') == 'set_branch':
            if set(body) != {'type', 'entity', 'branch_id', 'value', 'review_key'}:
                raise ProjectError('Branch Apply requires reviewed source identity and destination only')
            required_strings[route] = ('entity', 'branch_id', 'review_key')
        if route == '/api/command' and body.get('type') == 'set_worldmap_menu':
            if set(body) != {'type', 'entity_id', 'values', 'review_key'}:
                raise ProjectError('World-map Apply requires reviewed source row, values and key only')
            required_strings[route] = ('entity_id', 'review_key')
        if route == "/api/command" and body.get("type") == "layout_actor_placements":
            if set(body) != {'type', 'scene_id', 'actor_ids', 'layout', 'review_key'}:
                raise ProjectError('Group layout accepts scene, actors, layout and reviewed identity only')
            required_strings[route] = ('scene_id', 'review_key')
        if route == "/api/command" and body.get("type") == "offset_actor_placements":
            if set(body) != {"type", "scene_id", "actor_ids", "delta", "review_key"}:
                raise ProjectError("Actor group offset requires scene, actors, delta and reviewed identity only")
            required_strings[route] = ("scene_id", "review_key")
        if route == "/api/command" and body.get("type") == "set_actor_group_appearance":
            if set(body) != {"type", "scene_id", "actor_ids", "donor_entity_id", "review_key"}:
                raise ProjectError("Group appearance accepts scene, actors, donor and reviewed identity only")
            required_strings[route] = ("scene_id", "donor_entity_id", "review_key")
        if route == "/api/command" and body.get("type") == "revert_actor_group_component":
            if set(body) != {"type", "scene_id", "actor_ids", "component", "review_key"}:
                raise ProjectError("Group component revert accepts scene, actors, component and review identity only")
            required_strings[route] = ("scene_id", "component", "review_key")
        if route == "/api/command" and body.get("type") == "revert_authored_component":
            if set(body) != {"type", "entity_id", "component", "review_key"}:
                raise ProjectError("Component revert accepts only owner, component and review identity")
            required_strings[route] = ("entity_id", "component", "review_key")
        if route == "/api/command" and body.get("type") == "clear_texture_replacement":
            if set(body) != {"type", "asset_id"}:
                raise ProjectError("Texture clear accepts only an asset identity")
            required_strings[route] = ("asset_id",)
        if route == "/api/command" and body.get("type") in (
                "set_transform", "clear_transform", "create_actor_template", "apply_actor_template", "set_actor_appearance", "clear_actor_appearance", "set_dialogue_text", "clear_dialogue_text"):
            required_strings[route] = ("entity_id",)
        if route == "/api/command" and body.get("type") in ("set_actor_appearance", "clear_actor_appearance"):
            allowed = {"type", "entity_id", "donor_entity_id"} if body["type"] == "set_actor_appearance" else {"type", "entity_id"}
            if set(body) != allowed:
                raise ProjectError("Appearance commands accept an entity and donor identity only")
        if route == "/api/command" and body.get("type") in ("set_dialogue_text", "clear_dialogue_text"):
            allowed = {"type", "entity_id", "run_id", "text"} if body["type"] == "set_dialogue_text" else {"type", "entity_id", "run_id"}
            if set(body) != allowed:
                raise ProjectError("Dialogue commands accept only entity/run identities and authored text")
        if route == "/api/command" and body.get("type") in ("set_movement_target", "clear_movement_target"):
            allowed = {"type", "entity_id", "movement_id"}
            if body["type"] == "set_movement_target":
                allowed.add("values")
            if set(body) != allowed:
                raise ProjectError("Movement commands accept only owner/target identities and supported operand values")
            required_strings[route] = ("entity_id", "movement_id")
        if route == "/api/command" and body.get("type") in ("set_flag_bit", "clear_flag_bit"):
            allowed = {"type", "entity_id", "flag_id"}
            if body["type"] == "set_flag_bit":
                allowed.add("values")
            if set(body) != allowed:
                raise ProjectError("Flag commands accept only owner/target identities and supported operand values")
            required_strings[route] = ("entity_id", "flag_id")
        if route == "/api/command" and body.get("type") in ("set_wait_target", "clear_wait_target"):
            allowed = {"type", "entity_id", "wait_id"}
            if body["type"] == "set_wait_target":
                allowed.add("values")
            if set(body) != allowed:
                raise ProjectError("Wait commands accept only owner/target identities and supported operand values")
            required_strings[route] = ("entity_id", "wait_id")
        if route == "/api/command" and body.get("type") in ("set_model_selector_target", "clear_model_selector_target"):
            allowed = {"type", "entity_id", "model_selector_id"}
            if body["type"] == "set_model_selector_target":
                allowed.add("values")
            if set(body) != allowed:
                raise ProjectError("Model-selector commands accept only owner/target identities and supported operand values")
            required_strings[route] = ("entity_id", "model_selector_id")
        if route == "/api/command" and body.get("type") in ("set_transition_entry", "clear_transition_entry"):
            allowed = {"type", "entity_id", "transition_id"}
            if body["type"] == "set_transition_entry":
                allowed.add("values")
            if set(body) != allowed:
                raise ProjectError("Transition commands accept only owner/transition identities and encoded values")
            required_strings[route] = ("entity_id", "transition_id")
        if route == "/api/command" and body.get("type") == "set_transition_arrival":
            if set(body) != {"type", "entity_id", "transition_id", "arrival"}:
                raise ProjectError("Arrival commands accept only owner/transition identities and arrival fields")
            required_strings[route] = ("entity_id", "transition_id")
        for key in required_strings.get(route, ()):
            if not isinstance(body.get(key), str) or not body[key].strip():
                raise ProjectError(f"{key} must be a nonempty string")
        for key in ("scene", "profile_id", "expected_epoch_id", "entity_id"):
            if key in body and body[key] is not None and not isinstance(body[key], str):
                raise ProjectError(f"{key} must be a string or null")
        if route in ("/api/project/new", "/api/project/open"):
            if project.dirty and (project.imports or project.overrides):
                raise ProjectError("Save current project before opening or creating another")
            path = Path(body["path"]).expanduser()
            if route.endswith("/open"):
                self.server.project = ProjectService.open(path)
            else:
                if path.exists() and not path.is_dir():
                    raise ProjectError("Project path must be a directory")
                if (path / "project.legaia.json").exists():
                    raise ProjectError("A project already exists at this path; open it instead")
                name = body.get("name", "Legaia project")
                if not isinstance(name, str) or not name.strip() or len(name) > 128:
                    raise ProjectError("Project name must contain 1 to 128 characters")
                self.server.project = ProjectService(path, name.strip())
        elif route == "/api/project/save":
            project.save()
        elif route == "/api/build":
            from .build import build_project,authored_state_key
            if set(body)-{'review_key'} or ('review_key' in body and body['review_key']!=authored_state_key(project)):
                raise ProjectError('Build inputs differ from the reviewed project; review again')
            if project.mode != "edit":
                raise ProjectError("Build requires Edit mode")
            self.server.last_build = None
            self.server.last_build = build_project(project)
        elif route == "/api/run/configure":
            self.server.runs.configure(project, body)
        elif route == "/api/run":
            from .build import build_project
            if project.mode != "edit":
                raise ProjectError("Build & Run requires Edit mode")
            self.server.last_build = build_project(project)
            self.server.runs.start(project, self.server.last_build)
        elif route == "/api/run/stop":
            run = self.server.runs.status()
            self.server.runs.stop()
            if run and self.server.observer.port == run.get("debug_port"):
                self.server.observer.close()
                self.server.live_status = {"available": False, "state": "unavailable", "reason": {"message": "Owned runtime stopped"}}
                project.mode = "edit"
                project.correlate_runtime(self.server.live_status)
        elif route == "/api/run/attach":
            run = self.server.runs.status()
            if not run or not run.get("ready") or run.get("project") != str(project.root):
                raise ProjectError("This project's owned runtime has not passed readiness checks")
            from integrations.legaia.observer.service import ObserverService
            self.server.observer.close()
            self.server.observer = ObserverService(port=run["debug_port"])
            self.server.live_status = self.server.observer.discover(body.get("profile_id"))
            observed = (self.server.live_status.get("runtime") or {}).get("runtime", {})
            expected = run["runtime_identity"]["runtime"]["process_instance_id"]
            if observed.get("process_instance_id") != expected:
                self.server.observer.close()
                self.server.live_status = {"available": False, "state": "unavailable", "reason": {"message": "Runtime identity changed before attach"}}
                project.mode = "edit"
                project.correlate_runtime(self.server.live_status)
                raise ProjectError("Runtime identity changed before attach")
        elif route == "/api/import":
            from importer.pipeline import import_scene
            metadata = import_scene(Path(body["disc"]), body.get("scene", "town01"))
            project.import_metadata(metadata, body["disc"])
        elif route == "/api/selection":
            project.select(body.get("entity_id"))
        elif route == "/api/scene":
            project.set_scene(body["scene_id"])
        elif route == "/api/command":
            project.command(body)
        elif route == "/api/undo":
            project.undo()
        elif route == "/api/redo":
            project.redo()
        elif route == "/api/runtime/discover":
            self.server.live_status = self.server.observer.discover(body.get("profile_id"))
            if not self.server.live_status["available"]:
                project.mode = "edit"
        elif route == "/api/runtime/observe":
            if type(body.get("include_actors", False)) is not bool:
                raise ProjectError("include_actors must be a boolean")
            self.server.live_status = self.server.observer.observe(
                body.get("profile_id"), expected_epoch_id=body.get("expected_epoch_id"),
                include_actors=body.get("include_actors", False))
            if not self.server.live_status["available"]:
                project.mode = "edit"
        elif route == "/api/mode":
            mode = body.get("mode")
            if mode not in ("edit", "live"):
                raise ProjectError("Mode must be edit or live")
            if mode == "live":
                self.server.live_status = self.server.observer.observe(body.get("profile_id"))
                if not self.server.live_status["available"]:
                    project.mode = "edit"
                    project.correlate_runtime(self.server.live_status)
                    raise ProjectError(self.server.live_status["reason"]["message"])
            project.mode = mode
        else:
            raise ProjectError("Unsupported editor command route")
        if route in ("/api/project/new", "/api/project/open"):
            self.server.last_build = None
        if route in ("/api/project/new", "/api/project/open", "/api/import"):
            self.server.texture_catalogs.clear()
        if route in ("/api/runtime/discover", "/api/runtime/observe", "/api/run/attach", "/api/mode"):
            project.correlate_runtime(self.server.live_status)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Open the local Legaia Trace authoring editor")
    parser.add_argument("--project", type=Path, required=True, help="Project directory; existing projects are reopened")
    parser.add_argument("--port", type=int, default=4388)
    parser.add_argument("--runtime-port", type=int, default=4370)
    args = parser.parse_args(argv)
    project = ProjectService.open(args.project) if (args.project / "project.legaia.json").exists() else ProjectService(args.project)
    with EditorServer(("127.0.0.1", args.port), project, runtime_port=args.runtime_port) as server:
        print(f"Legaia Trace: http://127.0.0.1:{server.server_port} | {project.root}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0
