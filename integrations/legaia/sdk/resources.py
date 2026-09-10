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
    document, key = _scene(project)
    # Remove stale metadata before attempting a new source read. A failed refresh
    # must never leave a prior catalog presented as the current verified result.
    project.assets.resource_catalogs.pop(project.active_scene, None)
    records, limitations = [], []
    with _disc_context(project.disc_path):
        _verify(project, document)
        for kind, loader in (("Textures", load_texture_asset_catalog), ("Animations", load_animation_asset_catalog)):
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


def texture_preview(project, asset_id: str, palette_index: int) -> dict:
    from importer.texture_catalog import preview_texture_asset
    document, key = _scene(project)
    with _disc_context(project.disc_path):
        _verify(project, document)
        preview = preview_texture_asset(project.disc_path, document["scene"]["name"], asset_id, palette_index)
    if key != source_key(project):
        raise ProjectError("Texture source changed during preview; refresh again")
    asset = preview["asset"]
    return {**asset, "source_key": key, "scene_id": project.active_scene,
            "width": preview["width"], "height": preview["height"], "palette_index": palette_index,
            "rgba_base64": base64.b64encode(preview["rgba"]).decode("ascii"),
            "stp_base64": base64.b64encode(preview["stp"]).decode("ascii"),
            "limitations": preview.get("limitations", asset.get("limitations", []))}
