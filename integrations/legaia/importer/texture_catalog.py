"""Metadata-only TIM asset discovery and freshly verified private pixel previews.

This adapter reuses textures.py's pinned TIM/scene-pack decoder; it adds no
carrier discovery, upload-order inference or palette association rules.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from .core import ImportError
from .pipeline import REFERENCE_COMMIT, _disc_context
from .textures import TextureCatalog, Tim, decode_tim, load_scene_texture_catalog


LIMITATIONS = [
    "Partial structural scene TIM catalog; shared character/UI and conditional resources are outside this catalog.",
    "Palette choices are TIM-local contiguous palettes, not reconstructed runtime palette selection.",
    "Transparent-zero alpha and STP are separate; previews do not emulate PSX blending or animated palettes.",
    "Catalog entries identify source images, not proven current VRAM residency or material use.",
]


def _scene_name(scene: Any) -> str:
    if not isinstance(scene, str) or not scene or len(scene) > 128 or any(
            not ("a" <= c <= "z" or "A" <= c <= "Z" or "0" <= c <= "9" or c in "_-") for c in scene):
        raise ImportError("texture catalog requires a structural scene name")
    return scene


def _metadata(catalog: TextureCatalog, tim: Tim, source: dict) -> dict:
    palettes = len(tim.clut.data) // ((1 << tim.bpp) * 2) if tim.bpp in (4, 8) and tim.clut else 0
    limitations = list(LIMITATIONS)
    supported = tim.bpp not in (4, 8) or palettes > 0
    if not supported:
        limitations.append("Indexed TIM has no complete local palette; cross-TIM palette selection is unsupported here.")
    locator = deepcopy(source)
    locator["disc"] = {"sha256": catalog.disc_sha256, "serial": "SCUS-94254"}
    locator["iso_file"] = "PROT.DAT"
    return {"semantic_id": source["semantic_id"], "asset_kind": "texture",
            "name": f"TIM {source['prot_entry_index']} / {source.get('descriptor_index', 'raw')} / {source['pack_slot']}",
            "source_record": locator, "width": tim.width, "height": tim.image.height,
            "dimensions": {"width": tim.width, "height": tim.image.height},
            "bpp": tim.bpp, "palette_count": palettes, "preview_supported": supported,
            "image": tim.image.metadata(), "clut": tim.clut.metadata() if tim.clut else None,
            "reference_commit": REFERENCE_COMMIT, "limitations": limitations}


def _load(disc: Any, scene: str) -> tuple[TextureCatalog, list[dict]]:
    catalog = load_scene_texture_catalog(disc, _scene_name(scene))
    assets = [_metadata(catalog, tim, source) for tim, source in catalog.textures]
    ids = [asset["semantic_id"] for asset in assets]
    if len(set(ids)) != len(ids):
        raise ImportError("texture catalog contains ambiguous structural identifiers")
    return catalog, assets


def load_texture_asset_catalog(disc: Any, scene: str = "town01") -> dict:
    """Return deterministic source metadata only; never retain or return pixels."""
    _scene_name(scene)
    with _disc_context(disc):
        catalog, assets = _load(disc, scene)
        return {"schema_version": "legaia.texture-assets.v1", "scene": catalog.scene,
                "disc_sha256": catalog.disc_sha256, "reference_commit": REFERENCE_COMMIT,
                "assets": assets, "limitations": list(LIMITATIONS) + list(catalog.diagnostics)}


def preview_texture_asset(disc: Any, scene: str, asset_id: str, palette_index: int = 0) -> dict:
    """Resolve a structural ID from the freshly verified disc, then decode it.

    RGBA and STP bytes are private response payload. Callers must not persist
    these in source metadata or confuse STP with conventional alpha blending.
    No client-provided source locator or image data is accepted.
    """
    _scene_name(scene)
    if not isinstance(asset_id, str) or not asset_id.startswith("texture://") or len(asset_id) > 512:
        raise ImportError("texture preview requires a catalog asset identifier")
    if type(palette_index) is not int or palette_index < 0:
        raise ImportError("palette index must be a non-negative integer")
    with _disc_context(disc):
        catalog, assets = _load(disc, scene)
        index = next((i for i, asset in enumerate(assets) if asset["semantic_id"] == asset_id), None)
        if index is None:
            raise ImportError("texture identifier is not present in the verified scene catalog")
        asset = assets[index]
        if not asset["preview_supported"]:
            raise ImportError("indexed TIM has no complete local palette")
        if palette_index >= max(asset["palette_count"], 1):
            raise ImportError("palette index exceeds the verified TIM-local palette count")
        decoded = decode_tim(catalog.textures[index][0], palette_index)
        return {"asset": asset, "palette_index": palette_index, **decoded,
                "limitations": list(asset["limitations"])}
