"""town01 import pipeline and deterministic metadata projection."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .core import (
    ImportError,
    Mode2Image,
    ProtArchive,
    SUPPORTED_DISC_SHA256,
    canonical_json,
    claim,
    decompress_lzs,
    find_scene_bundle,
    global_special_tmd_pool,
    normalize_claims,
    parse_cdname,
    parse_man,
    scene_range,
    scene_tmd_pool,
    sha256_file,
    stable_actor_id,
    stable_model_asset_id,
    validate_metadata_only,
)

SCHEMA_VERSION = "legaia.scene-import.v2"
IMPORTER_VERSION = "0.2.0"
REFERENCE_REPOSITORY = "AndrewAltimit/legend-of-legaia-re"
REFERENCE_COMMIT = "d6e64c68ede25813d35db20980da82a1a025549b"
SUPPORTED_SCENE = "town01"


def _evidence(kind: str, locator: str, observation: str) -> list[dict[str, str]]:
    return [{"kind": kind, "source": REFERENCE_REPOSITORY, "locator": locator, "observation": observation}]


def _source_locator(
    disc_digest: str,
    entry_index: int,
    bundle: dict[str, Any],
    record_index: int,
    byte_offset: int,
    byte_length: int,
    decoded_size: int,
) -> dict[str, Any]:
    return {
        "disc": {"sha256": disc_digest, "serial": "SCUS-94254"},
        "iso_file": "PROT.DAT",
        "prot_entry_index": entry_index,
        "prot_entry_name": "town01",
        "scene_bundle": bundle,
        "record_kind": "man_partition_1_actor_placement",
        "record_index": record_index,
        "byte_offset": byte_offset,
        "byte_length": byte_length,
        "byte_coordinate_space": "decoded_man_payload",
        "containing_decoded_size": decoded_size,
    }


def _model_source_locator(disc_digest: str, scene: str, record: Any) -> dict[str, Any]:
    source = {
        "disc": {"sha256": disc_digest, "serial": "SCUS-94254"},
        "iso_file": "PROT.DAT",
        "prot_entry_index": record.entry_index,
        "prot_entry_name": scene if record.pool == "scene_tmd" else "befect_data",
        "record_kind": record.source_kind,
        "byte_offset": record.byte_offset,
        "byte_length": record.byte_length,
        "byte_coordinate_space": (
            "prot_entry" if record.source_kind == "raw_prot_entry" else "decoded_lzs_section"
        ),
        "containing_size": record.containing_size,
        "object_count": record.object_count,
    }
    if record.container_section is not None:
        source["container_section"] = record.container_section
    if record.stream_offset is not None:
        source["compressed_stream_offset"] = record.stream_offset
        source["compressed_stream_coordinate_space"] = "prot_entry"
    if record.pack_slot is not None:
        source["pack_slot"] = record.pack_slot
    if record.tmd_byte_length is not None:
        source["tmd_byte_length"] = record.tmd_byte_length
    return source


def _project_model_assets(
    disc_digest: str,
    scene: str,
    scene_models: Any,
    global_models: Any,
) -> tuple[list[dict[str, Any]], dict[tuple[str, int], dict[str, Any]]]:
    assets = []
    lookup = {}
    for record in (*scene_models, *global_models):
        semantic_id = stable_model_asset_id(scene, record.pool, record.pool_index)
        encoded_index = record.pool_index if record.pool == "scene_tmd" else 0xF0 + record.pool_index
        source_record = _model_source_locator(disc_digest, scene, record)
        evidence = _evidence(
            "parser_span",
            (
                "crates/engine-core/src/scene_resources.rs::SceneResources::build_targeted_with_options"
                if record.pool == "scene_tmd"
                else "crates/asset/src/character_pack.rs::parse"
            ),
            "bounded TMD record in the structurally ordered model pool",
        )
        model = {
            "semantic_id": semantic_id,
            "asset_kind": "tmd_model",
            "scope": "scene" if record.pool == "scene_tmd" else "global",
            "model_pool": record.pool,
            "encoded_model_index": encoded_index,
            "normalized_pool_index": record.pool_index,
            "source_record": source_record,
            "claims": normalize_claims(
                [
                    claim(
                        "semantic_id",
                        semantic_id,
                        "confirmed",
                        evidence,
                        source_record,
                        "Identity derives from the structural pool and slot, never a character name.",
                    ),
                    claim(
                        "source_record",
                        source_record,
                        "confirmed",
                        evidence,
                        source_record,
                        "Offsets are explicitly scoped to raw or decoded coordinates and remain bounded.",
                    ),
                    claim(
                        "model_pool_index",
                        {
                            "pool": record.pool,
                            "encoded_index": encoded_index,
                            "normalized_index": record.pool_index,
                        },
                        "confirmed",
                        _evidence(
                            "runtime_trace",
                            "crates/web-viewer/src/field_npc.rs::build_npc_catalog_impl",
                            "scene indices are direct; global-special indices normalize by subtracting 0xF0",
                        ),
                        source_record,
                        "Pool-slot identity does not imply character or animation identity.",
                    ),
                ]
            ),
            "dependencies": [],
            "aliases": [],
            "unresolved": [
                "character or object identity",
                "animation and texture bindings",
                "runtime pointer or mutable asset state",
            ],
        }
        assets.append(model)
        lookup[(record.pool, record.pool_index)] = model
    return assets, lookup


def project_metadata(
    *,
    disc_digest: str,
    scene: str,
    bundle_entry: int,
    table_offset: int,
    descriptor_index: int,
    descriptor_offset: int,
    descriptor_size: int,
    compressed_consumed: int,
    parsed_man: Any,
    scene_models: Any,
    global_models: Any,
) -> dict[str, Any]:
    bundle_ref = {
        "kind": "scene_asset_table",
        "table_offset": table_offset,
        "table_coordinate_space": "prot_entry",
        "man_descriptor_index": descriptor_index,
        "man_stream_offset": table_offset + descriptor_offset,
        "man_stream_coordinate_space": "prot_entry",
        "compressed_bytes_consumed": compressed_consumed,
        "decoded_size": descriptor_size,
    }
    model_assets, model_lookup = _project_model_assets(disc_digest, scene, scene_models, global_models)
    actors = []
    for actor in parsed_man.actors:
        source_record = _source_locator(
            disc_digest,
            bundle_entry,
            bundle_ref,
            actor.record_index,
            actor.byte_offset,
            actor.byte_length,
            descriptor_size,
        )
        special = actor.model_index >= 0xF0
        model_pool = "global_special" if special else "scene_tmd"
        normalized_index = actor.model_index - 0xF0 if special else actor.model_index
        asset = model_lookup.get((model_pool, normalized_index))
        asset_semantic_id = asset["semantic_id"] if asset is not None else None
        model_reference = {
            "source_entry": asset["source_record"]["prot_entry_index"] if asset is not None else None,
            "model_index": actor.model_index,
            "normalized_pool_index": normalized_index,
            "model_pool": model_pool,
            "asset_semantic_id": asset_semantic_id,
            "referenced_asset_record": asset_semantic_id,
            "resolution_status": "resolved" if asset is not None else "pool_index_out_of_bounds",
        }
        imported_transform = {
            "position": {"x": actor.world_x, "y": None, "z": actor.world_z},
            "rotation": None,
            "coordinate_system": "retail_field_world_units",
            "placement_tile": {"x": actor.tile_x, "z": actor.tile_z},
        }
        claims = [
            claim(
                "source_record",
                source_record,
                "confirmed",
                _evidence(
                    "parser_span",
                    "crates/asset/src/man_section.rs::ManFile::actor_placement",
                    "partition-1 record offset and bounded placement prefix decode",
                ),
                source_record,
                "Record zero is the scene controller; structural record index is retained.",
            ),
            claim(
                "imported_transform.position",
                imported_transform["position"],
                "confirmed",
                _evidence(
                    "runtime_trace",
                    "crates/asset/src/man_section.rs::ActorPlacement",
                    "tile bytes and half-tile bit reproduce the retail world-position formula",
                ),
                source_record,
                "Y is unresolved because the placement prefix stores X/Z only.",
            ),
            claim(
                "imported_transform.rotation",
                None,
                "unknown",
                _evidence(
                    "negative_evidence",
                    "docs/subsystems/field-locomotion.md#actor-placement-records",
                    "the confirmed four-byte placement header contains no facing field",
                ),
                source_record,
                "Facing may be established later by actor script execution; it is not fabricated here.",
            ),
            claim(
                "model_reference.model_index",
                {"index": actor.model_index, "pool": model_reference["model_pool"]},
                "confirmed",
                _evidence(
                    "runtime_trace",
                    "crates/asset/src/man_section.rs::ActorPlacement::model_index",
                    "placement byte selects scene TMD pool below 0xF0 and global special pool otherwise",
                ),
                source_record,
                "The pool selector is known; this slice intentionally does not export or decode TMD assets.",
            ),
            claim(
                "model_reference.referenced_asset_record",
                asset_semantic_id,
                "confirmed" if asset is not None else "unknown",
                _evidence(
                    "negative_evidence",
                    "crates/web-viewer/src/field_npc.rs::build_npc_catalog_impl",
                    "actor selector resolves through the separately constructed scene/global TMD pool",
                ),
                source_record,
                (
                    "Reference is the stable structural asset ID; no TMD bytes are embedded."
                    if asset is not None
                    else "The placement selector is outside the structurally enumerated pool."
                ),
            ),
            claim(
                "placement_fields.animation_id",
                actor.animation_id,
                "confirmed",
                _evidence(
                    "runtime_trace",
                    "crates/asset/src/man_section.rs::ActorPlacement::anim_id",
                    "disc byte seeds the actor animation record id plus one; zero means none",
                ),
                source_record,
                "Animation asset resolution is outside this metadata slice.",
            ),
            claim(
                "placement_fields.local_count",
                actor.local_count,
                "confirmed",
                _evidence(
                    "parser_span",
                    "crates/asset/src/man_section.rs::ManFile::actor_placement",
                    "record prefix count bounds the two-byte local entries before placement fields",
                ),
                source_record,
                "Structural prefix metadata only; local values are not emitted.",
            ),
        ]
        actors.append(
            {
                "semantic_id": stable_actor_id(scene, 1, actor.record_index),
                "source_record": source_record,
                "imported_transform": imported_transform,
                "model_reference": model_reference,
                "placement_fields": {
                    "animation_id": actor.animation_id,
                    "local_count": actor.local_count,
                },
                "claims": normalize_claims(claims),
                "unresolved": [
                    "imported_transform.position.y",
                    "imported_transform.rotation",
                    *([] if asset is not None else ["model_reference.asset_semantic_id"]),
                ],
            }
        )
    output = {
        "schema_version": SCHEMA_VERSION,
        "importer_version": IMPORTER_VERSION,
        "source": {
            "disc_build": "Legend of Legaia (North America), SCUS-94254",
            "disc_identity": f"sha256:{disc_digest}",
            "scene_name": scene,
            "imported_at_tool_version": IMPORTER_VERSION,
            "reference_repositories": [
                {"repository": REFERENCE_REPOSITORY, "commit": REFERENCE_COMMIT, "role": "development_reference_and_parity_oracle"}
            ],
        },
        "scene": {
            "semantic_id": f"scene://{scene}",
            "name": scene,
            "source": {"iso_file": "PROT.DAT", "prot_entry_range_label": scene, "bundle_entry": bundle_entry},
            "man_partition_counts": list(parsed_man.partition_counts),
        },
        "actors": actors,
        "assets": {"models": model_assets},
        "diagnostics": [],
        "unresolved": [
            "actor facing/rotation before script execution",
            "vertical placement coordinate",
            "interaction, dialogue, story flags, runtime slots, and live RAM correlation",
        ],
    }
    validate_metadata_only(output)
    return output


def import_scene(disc: Path | str, scene: str = SUPPORTED_SCENE) -> dict[str, Any]:
    if scene != SUPPORTED_SCENE:
        raise ImportError(f"unsupported scene {scene!r}; this importer currently supports only {SUPPORTED_SCENE}")
    with Mode2Image(Path(disc)) as image:
        # Confirm the structural build marker without reading or emitting its bytes.
        image.find("SCUS_942.54")
        digest = sha256_file(image.path)
        if digest != SUPPORTED_DISC_SHA256:
            raise ImportError(
                "unsupported disc build: expected the North American SCUS-94254 Mode 2/2352 image "
                f"with SHA-256 {SUPPORTED_DISC_SHA256}, got {digest}"
            )
        prot_node = image.find("PROT.DAT")
        cdname_node = image.find("CDNAME.TXT")
        try:
            cdname_text = image.read_file(cdname_node).decode("ascii")
        except UnicodeDecodeError as exc:
            raise ImportError("CDNAME.TXT is not valid ASCII metadata") from exc
        mapping = parse_cdname(cdname_text)
        start, end = scene_range(mapping, scene)
        archive = ProtArchive(image, prot_node)
        bundle, entry_bytes = find_scene_bundle(archive, start, end)
        descriptor = next(item for item in bundle.descriptors if item.type_byte == 3 and item.size > 0)
        stream_offset = bundle.table_offset + descriptor.data_offset
        if stream_offset >= len(entry_bytes):
            raise ImportError(
                f"{scene} MAN descriptor offset 0x{stream_offset:X} exceeds containing PROT entry {bundle.entry_index}"
            )
        man_bytes, consumed = decompress_lzs(entry_bytes[stream_offset:], descriptor.size)
        parsed = parse_man(man_bytes, scene)
        if not parsed.actors:
            raise ImportError(f"{scene} MAN contains no actor placement records")
        scene_models = scene_tmd_pool(archive, start, end)
        global_models = global_special_tmd_pool(archive)
        if not scene_models or not global_models:
            raise ImportError(f"{scene} model pools did not enumerate structural assets")
        return project_metadata(
            disc_digest=digest,
            scene=scene,
            bundle_entry=bundle.entry_index,
            table_offset=bundle.table_offset,
            descriptor_index=descriptor.index,
            descriptor_offset=descriptor.data_offset,
            descriptor_size=descriptor.size,
            compressed_consumed=consumed,
            parsed_man=parsed,
            scene_models=scene_models,
            global_models=global_models,
        )


def write_metadata(path: Path, value: dict[str, Any]) -> None:
    validate_metadata_only(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value, pretty=True) + "\n", encoding="utf-8", newline="\n")
