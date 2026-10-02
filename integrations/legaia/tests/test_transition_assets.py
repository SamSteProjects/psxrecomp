"""Transition assets preserve source identity and static arrival layers only."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.script_catalog import _catalog
from integrations.legaia.tests.test_importer_dialogue_authoring import fixture
from integrations.legaia.tests.test_importer_script_catalog import catalog, forbidden_fields
from sdk.project import ProjectError
from sdk.transition_assets import build_transition_assets, validate_transition_asset


def warp(name=b"town02", entry=(1, 130, 3), extended=None):
    prefix = b"\x3f" if extended is None else bytes((0xbf, extended))
    return prefix + b"\0\0" + bytes((len(name),)) + name + bytes(entry)


def two_partitions():
    _, original = fixture(warp())
    region = 0x2b + 12
    section = int.from_bytes(original[0x28:0x2b], "little")
    p2 = bytes(4) + warp(b"dolk2", (128, 127, 231), 7)
    man = bytearray(original[:region + section] + p2 + original[region + section:])
    man[0x34:0x37] = section.to_bytes(3, "little")
    man[0x28:0x2b] = (section + len(p2)).to_bytes(3, "little")
    return _catalog(bytes(man), "fixture", {"synthetic": True}, {"town02", "dolk2"})


def authored(record, value):
    return {record["owner_id"]: {"Transitions": {"entries": {
        record["entry_layers"]["transition_id"]: value}}}}


def replace_at(record, path, value):
    parent = record
    for key in path[:-1]:
        parent = parent[key]
    parent[path[-1]] = value


class TransitionAssets(unittest.TestCase):
    def test_partition_identities_static_arrival_and_detached_determinism(self):
        source = two_partitions()
        source_before = deepcopy(source)
        records = build_transition_assets(source, ["scene://fixture", "scene://town02"])
        self.assertEqual(len(records), 2)
        p1, p2 = records
        self.assertEqual(p1["id"], "transition://fixture/actors/man-p1/0001/0005")
        self.assertEqual(p2["id"], "transition://fixture/scripts/man-p2/0000/0004")
        self.assertEqual((p2["partition"], p2["owner_id"], p2["reference"]["extended_target"]),
                         (2, "scene://fixture/scripts/man-p2/0000", 7))
        self.assertEqual(p2["arrival_layers"]["imported"]["x"], 128)
        self.assertEqual(p2["arrival_layers"]["imported"]["z"], 16320)
        self.assertEqual(p2["arrival_layers"]["imported"]["facing_angle_12bit"], 3584)
        for record in records:
            self.assertEqual(record["reference"]["byte_offset"],
                             record["source_record"]["byte_offset"] + record["reference"]["pc"])
            self.assertEqual(record["reachability"], "not_evaluated")
            self.assertFalse(record["runtime_verified"])
            self.assertIsNone(record["trigger_position"])
            self.assertIs(validate_transition_asset(record), record)
        wrapper = dict(p2, kind="transition", layer="derived", scene_id="scene://fixture")
        self.assertIs(validate_transition_asset(wrapper), wrapper)
        reversed_catalog = deepcopy(source)
        reversed_catalog["assets"].reverse()
        self.assertEqual(records, build_transition_assets(reversed_catalog, ["scene://town02", "scene://fixture"]))
        self.assertEqual(forbidden_fields(records), set())
        records[0]["source_record"].clear()
        records[1]["reference"].clear()
        records[1]["arrival_layers"]["effective"].clear()
        self.assertEqual(source, source_before)

    def test_unknown_destinations_and_stops_reject_authored_layers_without_scanning(self):
        unknown = build_transition_assets(catalog(warp(b"Town02")), [])[0]
        self.assertEqual(unknown["target"], unknown["id"] + "/unresolved-target")
        self.assertIsNone(unknown["reference"]["target_scene_name"])
        self.assertIsNone(unknown["reference"]["target_in_scene_index"])
        self.assertEqual(unknown["arrival_layers"]["imported"]["x"], 192)
        with self.assertRaises(ProjectError):
            build_transition_assets(catalog(warp(b"Town02")), [], authored(unknown, {"entry_x_encoded": 2}))

        # One encoded flag branch reaches an unsupported instruction; the other
        # reaches a named transition. This is a real decoded stop, not tail data.
        stopped_catalog = catalog(b"\x4c\xa0\x01\x17\0" + warp() + b"\x2a")
        stopped = build_transition_assets(stopped_catalog, [])[0]
        self.assertEqual((stopped["script_status"], stopped["script_stop_count"]), ("partial", 1))
        with self.assertRaises(ProjectError):
            build_transition_assets(stopped_catalog, [], authored(stopped, {"entry_x_encoded": 2}))
        self.assertEqual(build_transition_assets(catalog(b"\x2a" + warp()), []), [])

    def test_partial_without_stops_accepts_encoded_override_and_retains_source(self):
        # SCENE_CHANGE has no encoded continuation; its tail remains unvisited.
        source = catalog(warp() + b"\x2a" + warp(b"dolk2"))
        record = build_transition_assets(source, [])[0]
        self.assertEqual((record["script_status"], record["script_stop_count"]), ("partial", 0))
        edits = authored(record, {"entry_x_encoded": 128, "direction_encoded": 231})
        before_source, before_edits = deepcopy(source), deepcopy(edits)
        changed = build_transition_assets(source, [], edits)[0]
        self.assertEqual(changed["reference"], record["reference"])
        self.assertEqual(changed["entry_layers"]["imported"], record["entry_layers"]["imported"])
        self.assertEqual(changed["entry_layers"]["effective"],
                         {"entry_x_encoded": 128, "entry_z_encoded": 130, "direction_encoded": 231})
        self.assertEqual(changed["entry_layers"]["validation"], "reverified_on_build")
        self.assertEqual(changed["arrival_layers"]["effective"]["x"], 128)
        self.assertEqual(changed["arrival_layers"]["effective"]["z"], 384)
        self.assertEqual(changed["arrival_layers"]["effective"]["facing_angle_12bit"], 3584)
        changed["entry_layers"]["authored"].clear()
        self.assertEqual((source, edits), (before_source, before_edits))
        for value in ({"entry_x_encoded": True}, {"x": 3}, {"direction_encoded": 256}, {}):
            with self.subTest(value=value), self.assertRaises(ProjectError):
                build_transition_assets(source, [], authored(record, value))
        missing = authored(record, {"entry_x_encoded": 1})
        entries = missing[record["owner_id"]]["Transitions"]["entries"]
        entries[record["script_id"] + "/transition/ffff"] = entries.pop(record["entry_layers"]["transition_id"])
        with self.assertRaises(ProjectError):
            build_transition_assets(source, [], missing)

    def test_record_rejects_fabricated_runtime_identity_source_and_layers(self):
        original = build_transition_assets(catalog(warp()), [])[0]
        bad_values = [
            (("id",), original["id"] + "/extra"),
            (("semantic_id",), "transition://wrong/actors/man-p1/0001/0005"),
            (("owner_id",), "scene://fixture/actors/man-p1/0002"),
            (("partition",), True),
            (("source",), "scene://other"),
            (("script_status",), "verified_runtime"),
            (("script_stop_count",), True),
            (("source_record", "partition"), 2),
            (("source_record", "record_index"), 2),
            (("source_record", "sha256"), "g" * 64),
            (("source_record", "byte_length"), 1),
            (("source_record", "byte_offset"), 4 * 1024 * 1024),
            (("reference", "byte_offset"), original["reference"]["byte_offset"] + 1),
            (("reference", "extended_target"), -1),
            (("reference", "name_sha256"), "f" * 64),
            (("reference", "entry_x_encoded"), True),
            (("entry_layers", "effective", "entry_x_encoded"), 2),
            (("entry_layers", "transition_id"), original["id"]),
            (("entry_layers", "validation"), "verified_runtime"),
            (("arrival_layers", "effective", "x"), 1),
            (("arrival_layers", "effective", "runtime_verified"), True),
            (("trigger_position",), {"x": 1, "z": 2}),
            (("runtime_verified",), True),
            (("reachability",), "reachable"),
            (("coverage", "script_count"), True),
        ]
        for path, value in bad_values:
            with self.subTest(path=path):
                record = deepcopy(original)
                replace_at(record, path, value)
                with self.assertRaises(ProjectError):
                    validate_transition_asset(record)
        for addition in ({"kind": "scene"}, {"layer": "authored"}, {"scene_id": "scene://other"},
                         {"payload": "private"}, {"runtime_route": []}):
            with self.subTest(addition=addition), self.assertRaises(ProjectError):
                validate_transition_asset(dict(original, **addition))
        for private_value in ({"payload": "private"}, {"raw_hex": "deadbeef"}, {"bytes": b"private"}):
            record = deepcopy(original)
            record["source_record"]["optional_locator"] = private_value
            with self.subTest(private_value=private_value), self.assertRaises(ProjectError):
                validate_transition_asset(record)

    def test_catalog_compatibility_stop_evidence_and_bounded_discovery(self):
        self.assertEqual(build_transition_assets({"assets": [{"asset_kind": "script"}]}, []), [])
        source = catalog(warp())
        source["assets"][0]["source_record"]["optional_locator"] = {"name": "source.man", "section": 3}
        asset = build_transition_assets(source, [])[0]
        self.assertEqual(asset["source_record"]["optional_locator"], {"name": "source.man", "section": 3})
        del source["assets"][0]["stop_count"]
        self.assertEqual(build_transition_assets(source, [])[0]["script_stop_count"], 0)
        invalid_catalogs = []
        missing_lists = deepcopy(source)
        del missing_lists["assets"][0]["transitions"]
        invalid_catalogs.append(missing_lists)
        missing_stops = deepcopy(source)
        del missing_stops["assets"][0]["stops"]
        invalid_catalogs.append(missing_stops)
        incorrect_stops = deepcopy(source)
        incorrect_stops["assets"][0]["stop_count"] = 1
        invalid_catalogs.append(incorrect_stops)
        incorrect_counts = deepcopy(source)
        incorrect_counts["transition_count"] += 1
        invalid_catalogs.append(incorrect_counts)
        duplicate = deepcopy(source)
        duplicate["assets"].append(deepcopy(duplicate["assets"][0]))
        duplicate["script_count"] += 1
        duplicate["transition_count"] += 1
        invalid_catalogs.append(duplicate)
        for invalid in invalid_catalogs:
            with self.subTest(invalid=invalid), self.assertRaises(ProjectError):
                build_transition_assets(invalid, [])
        for identities in ("scene://fixture", ["fixture"], ["scene://fixture"] * 65):
            with self.subTest(identities=identities), self.assertRaises(ProjectError):
                build_transition_assets(source, identities)
        for limit in ("MAX_TRANSITION_ASSETS", "MAX_TRANSITION_REFERENCES"):
            with self.subTest(limit=limit), patch("sdk.transition_assets." + limit, 1), self.assertRaises(ProjectError):
                build_transition_assets(two_partitions(), [])


if __name__ == "__main__":
    unittest.main()
