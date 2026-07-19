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
    normalize_claims,
    parse_cdname,
    parse_man,
    scene_range,
    sha256_file,
    stable_actor_id,
    validate_metadata_only,
)

SCHEMA_VERSION = "legaia.scene-import.v1"
IMPORTER_VERSION = "0.1.0"
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
        model_reference = {
            "source_entry": bundle_entry,
            "model_index": actor.model_index,
            "model_pool": "global_special" if special else "scene_tmd",
            "referenced_asset_record": None,
            "resolution_status": "pool_index_only",
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
                None,
                "unknown",
                _evidence(
                    "negative_evidence",
                    "crates/web-viewer/src/field_npc.rs::build_npc_catalog_impl",
                    "full resolution requires the separately built scene/global TMD pool",
                ),
                source_record,
                "Deferred until scene resource records have stable semantic asset identities.",
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
                "unresolved": ["imported_transform.position.y", "imported_transform.rotation", "model_reference.referenced_asset_record"],
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
        "diagnostics": [],
        "unresolved": [
            "actor facing/rotation before script execution",
            "vertical placement coordinate",
            "stable model asset-record identity",
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
        )


def write_metadata(path: Path, value: dict[str, Any]) -> None:
    validate_metadata_only(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value, pretty=True) + "\n", encoding="utf-8", newline="\n")
