"""Verified resource discovery shared by the asset browser and inspectors."""
from __future__ import annotations

import base64
from importer.core import ImportError as RetailImportError
from importer.pipeline import _disc_context, import_scene
from .project import ProjectError
from .scene_preview import source_key


def _scene(project):
    document = project.imports.get(project.active_scene)
    if not project.disc_path or document is None:
        raise ProjectError("Resource discovery requires an imported scene and its user-owned disc")
    return document, source_key(project)


def _verify(project, document):
    if import_scene(project.disc_path, document["scene"]["name"]) != document:
        raise ProjectError("Resource source differs from freshly verified imported evidence")


def refresh_resource_catalog(project) -> dict:
    from importer.texture_catalog import load_texture_asset_catalog
    from importer.animation_catalog import load_animation_asset_catalog
    from importer.script_catalog import load_script_asset_catalog
    from importer.field_map import load_field_map_catalog
    document, key = _scene(project)
    # Remove stale metadata before attempting a new source read. A failed refresh
    # must never leave a prior catalog presented as the current verified result.
    project.assets.resource_catalogs.pop(project.active_scene, None)
    records, limitations = [], []
    with _disc_context(project.disc_path):
        _verify(project, document)
        for kind, loader in (("Textures", load_texture_asset_catalog), ("Animations", load_animation_asset_catalog),
                             ("Scripts and dialogue", load_script_asset_catalog),
                             ("Field collision and triggers", load_field_map_catalog)):
            try:
                catalog = loader(project.disc_path, document["scene"]["name"])
                records.extend(catalog["assets"])
                limitations.extend(catalog.get("limitations", []))
            except RetailImportError as exc:
                limitations.append(f"{kind} unavailable: {exc}")
    if key != source_key(project):
        raise ProjectError("Resource source changed during discovery; refresh again")
    if len(records) > 4096:
        raise ProjectError("Resource catalog exceeds the bounded record budget")
    return project.assets.register_resources(project.active_scene, key, records, limitations)


def trigger_script_preview(project, asset_id: str) -> dict:
    from importer.trigger_scripts import inspect_trigger_script
    document, key = _scene(project)
    with _disc_context(project.disc_path):
        _verify(project, document)
        report = inspect_trigger_script(project.disc_path, document["scene"]["name"], asset_id)
    if key != source_key(project):
        raise ProjectError("Trigger script source changed during inspection; refresh again")
    return {**report, "scene_id": project.active_scene, "source_key": key}


def field_map_preview(project, asset_id: str) -> dict:
    from importer.field_map import preview_field_map
    document, key = _scene(project)
    with _disc_context(project.disc_path):
        _verify(project, document)
        preview = preview_field_map(project.disc_path, document["scene"]["name"], asset_id)
    if key != source_key(project):
        raise ProjectError("Field map source changed during preview; refresh again")
    return {**preview, "semantic_id": preview["asset"]["semantic_id"], "asset_kind": "collision",
            "scene_id": project.active_scene, "source_key": key}


def texture_preview(project, asset_id: str, palette_index: int, layer: str = "effective") -> dict:
    from importer.texture_catalog import preview_texture_asset
    from importer.textures import decode_tim
    if layer not in ("imported", "effective"):
        raise ProjectError("Choose imported or effective texture preview")
    document, key = _scene(project)
    with _disc_context(project.disc_path):
        _verify(project, document)
        preview = preview_texture_asset(project.disc_path, document["scene"]["name"], asset_id, palette_index)
        authored = project.texture_overrides.get(asset_id)
        if authored is not None and layer == "effective":
            content = project.read_texture_replacement(authored)
            project._texture_context(asset_id).validate_replacement(asset_id, content)
            preview.update(decode_tim(content, palette_index))
    if key != source_key(project):
        raise ProjectError("Texture source changed during preview; refresh again")
    asset = preview["asset"]
    return {**asset, "source_key": key, "scene_id": project.active_scene, "layer": layer,
            "authored": authored,
            "width": preview["width"], "height": preview["height"], "palette_index": palette_index,
            "rgba_base64": base64.b64encode(preview["rgba"]).decode("ascii"),
            "stp_base64": base64.b64encode(preview["stp"]).decode("ascii"),
            "limitations": preview.get("limitations", asset.get("limitations", []))}


def texture_source(project, asset_id: str) -> dict:
    context = project._texture_context(asset_id)
    content = context.original_tim(asset_id)
    return {"tim_base64": base64.b64encode(content).decode("ascii"),
            "filename": "retail-" + asset_id.removeprefix("texture://").replace("/", "-") + ".tim"}


def apply_texture_overrides(project, catalog):
    """Return an effective private catalog; imported texture facts stay intact."""
    from copy import deepcopy
    from importer.texture_authoring import load_texture_authoring_context
    from importer.textures import parse_tim
    bindings = {identifier: binding for identifier, binding in project.texture_overrides.items()
                if binding["source_scene_id"] == "scene://" + catalog.scene}
    if not bindings:
        return catalog
    context = load_texture_authoring_context(project.disc_path, catalog.scene)
    replacements = {}
    for identifier, binding in bindings.items():
        content = project.read_texture_replacement(binding)
        context.validate_replacement(identifier, content)
        replacements[identifier] = parse_tim(content)
    result = deepcopy(catalog)
    result.textures = [(replacements.get(source["semantic_id"], tim), source)
                       for tim, source in result.textures]
    result.diagnostics.append(f"Effective preview applies {len(replacements)} project-authored TIM replacements; source locators remain retail provenance.")
    return result
