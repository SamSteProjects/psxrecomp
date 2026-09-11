"""Synthetic source-backed binding reads and non-authoritative candidate joins."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from integrations.legaia.layouts import load_profile
from integrations.legaia.observer.profile import LoadedProfile
from integrations.legaia.observer.correlation import REFERENCE, MAX_NODES, correlate, sample_man_bindings
from integrations.legaia.observer.errors import SnapshotUnstable, ProtocolError
from integrations.legaia.sdk.project import ProjectService

DISC = "a" * 64
TOKEN = "b" * 64
PROFILE = LoadedProfile.from_document(load_profile(Path(__file__).resolve().parents[1] / "layouts/scus94254-na-field-v1.json"))


def imported():
    return {"source": {"disc_identity": "sha256:" + DISC, "reference_repositories": [
        {"repository": "AndrewAltimit/legend-of-legaia-re", "commit": REFERENCE}]},
        "scene": {"name": "town01", "semantic_id": "scene://town01"},
        "actors": [{"semantic_id": "scene://town01/actors/man-p1/0001",
                    "source_record": {"record_kind": "man_partition_1_actor_placement", "record_index": 1},
                    "model_reference": {"asset_semantic_id": "asset://model/4", "model_index": 4,
                        "model_pool": "scene_tmd", "normalized_pool_index": 4, "resolution_status": "resolved"},
                    "placement_fields": {"local_count": 2, "animation_id": 7},
                    "imported_transform": {"position": {"x": 1216, "y": None, "z": 1344}, "rotation": None},
                    "claims": [], "unresolved": []}],
        "assets": {"models": [{"semantic_id": "asset://model/4", "source_record": {"object_count": 3}}]}}


def observation(count=1):
    epoch = {"epoch_id": "epoch-test", "runtime_process_identity": "session-1",
             "observation_guard_token": TOKEN, "scene_name": "town01", "last_validated_frame": 100}
    nodes = []
    for i in range(count):
        address = 0x80010000 + i * 256
        fields = {"field_script_pointer": 0x80020001, "model_object_table_pointer": 0x80030000,
                  "position_x": 500, "position_y": 0, "position_z": 600}
        nodes.append({"epoch_scoped_node_id": f"runtime://epoch-test/field-node/{address:08x}",
                      "node_address": f"0x{address:08X}", "chain_index": i,
                      "decoded_fields": [{"property": key, "raw_numeric_value": value,
                                          "interpreted_value": value} for key, value in fields.items()]})
    return {"epoch": epoch, "profile": {"profile_hash": PROFILE.profile_hash, "selection": {"accepted": True}},
            "snapshot_current_at_capture": True, "boundaries": {"stable": True},
            "actor_chain": {"traversal_complete": True, "nodes": nodes}}


class Client:
    def __init__(self, snapshot, mutate=False):
        self.ram = {}
        self.calls = []
        self.mutate = mutate
        for node in snapshot["actor_chain"]["nodes"]:
            address = int(node["node_address"], 16)
            self.put(address + 144, (0x80020001).to_bytes(4, "little"))
            self.put(address + 68, (0x80030000).to_bytes(4, "little"))
        self.put(0x80020001, bytes([2]))
        self.put(0x80020006, bytes([4, 7, 9, 10]))
        self.put(0x80030000, (3).to_bytes(4, "little"))

    def put(self, address, data):
        self.ram.update({address + i: value for i, value in enumerate(data)})

    def request(self, command):
        assert command == "mod_status"
        return {"disc_identity": {"available": True, "scope": "committed-source-disc", "sha256": DISC}}

    def read_regions(self, regions, guard):
        self.calls.append(regions)
        assert guard["expected_token"] == TOKEN
        if self.mutate and len(self.calls) == 2:
            self.put(0x80010000 + 144, (0x80020100).to_bytes(4, "little"))
        return {"guard": {"valid": True, "stable": True, "compatible": True,
                           "expected_token_matched": True, "token_before": TOKEN, "token_after": TOKEN,
                           "evidence": {"runtime_instance_id": "session-1"}},
                "frame_before": 100 + len(self.calls), "frame_after": 100 + len(self.calls),
                "payload_returned": True, "regions": [dict(region, hex=bytes(
                    self.ram.get(int(region["addr"], 16) + offset, 0)
                    for offset in range(region["len"])).hex()) for region in regions]}


def status(count=1):
    snapshot = observation(count)
    return {"available": True, "observation": snapshot,
            "actor_bindings": sample_man_bindings(Client(snapshot), PROFILE, snapshot)}


class CorrelationTests(unittest.TestCase):
    def test_position_capture_is_separate_from_later_binding_reads(self):
        live = status()
        live["observation"]["actor_chain"]["nodes"][0]["position_capture_frames"] = {"before": 99, "after": 100}
        result = correlate(imported(), live)
        node = result["runtime_nodes"][0]
        candidate = next(iter(result["entities"].values()))["candidates"][0]
        self.assertEqual(node["frame"], 100)
        self.assertEqual(candidate["position_capture_frames"], {"before": 99, "after": 100})
        self.assertGreater(candidate["frame"], node["frame"])
        self.assertEqual(node["observed_position"], {"x": 500, "y": 0, "z": 600})
        legacy = correlate(imported(), status())["runtime_nodes"][0]
        self.assertIsNone(legacy["frame"])
        self.assertIsNone(legacy["position_capture_frames"])

    def test_authored_appearance_preserves_target_structure_and_retail_candidates(self):
        document = imported()
        target = document["actors"][0]["semantic_id"]
        donor = deepcopy(document["actors"][0])
        donor["semantic_id"] = "scene://town01/actors/man-p1/0002"
        donor["model_reference"].update(model_index=5, normalized_pool_index=5,
                                        asset_semantic_id="asset://model/5")
        donor["placement_fields"].update(animation_id=8, local_count=9)
        document["actors"].append(donor)
        document["assets"]["models"].append({"semantic_id": "asset://model/5", "source_record": {"object_count": 3}})
        original = deepcopy(document)
        donors = {target: donor["semantic_id"]}
        live = status()
        live["actor_bindings"]["nodes"][0].update(model_index=5, normalized_pool_index=5, animation_id=8)
        candidate = correlate(document, live, donors)["entities"][target]
        self.assertEqual(candidate["status"], "candidate")
        self.assertFalse(candidate["binding_confirmed"])
        self.assertEqual(candidate["candidates"][0]["appearance_layers"], ["effective"])
        self.assertEqual(correlate(document, status(), donors)["entities"][target]["candidates"][0]["appearance_layers"], ["imported"])
        self.assertEqual(document, original)
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            project.import_metadata(document)
            project.overrides[target] = {"ActorAppearance": {"donor_entity_id": donor["semantic_id"]}}
            self.assertTrue(project.correlate_runtime(live)["available"])
            project.overrides.clear()
            self.assertFalse(project.state()["runtime_correlation"]["available"])
        self.assertFalse(correlate(document, live, {target: "scene://other/actor"})["available"])

    def test_guarded_header_and_independent_model_count_form_candidate(self):
        live = status()
        binding = live["actor_bindings"]
        self.assertEqual(binding["request_count"], 3)
        self.assertEqual(binding["bytes_read"], 30)
        self.assertEqual(binding["nodes"][0]["placement_position"], {"x": 1216, "z": 1344})
        self.assertNotIn("hex", str(binding))
        result = correlate(imported(), live)
        entry = next(iter(result["entities"].values()))
        self.assertEqual(entry["status"], "candidate")
        self.assertFalse(entry["binding_confirmed"])
        self.assertEqual(result["confirmed_match_count"], 0)
        self.assertTrue(entry["candidates"][0]["placement_header_agrees_with_import"])

    def test_positions_order_and_map_record_indices_do_not_bind(self):
        live = status()
        live["observation"]["actor_chain"]["nodes"][0]["chain_index"] = 1
        live["actor_bindings"]["nodes"][0]["object_count"] = 9
        result = correlate(imported(), live)
        self.assertEqual(result["candidate_count"], 0)
        self.assertEqual(next(iter(result["entities"].values()))["status"], "unmatched")

    def test_many_to_many_ambiguity_is_retained(self):
        document = imported()
        second = deepcopy(document["actors"][0]); second["semantic_id"] += "-other"
        second["imported_transform"]["position"]["x"] = 2000
        document["actors"].append(second)
        live = status(2)
        result = correlate(document, live)
        self.assertEqual(result["candidate_count"], 4)
        self.assertTrue(all(entry["status"] == "ambiguous" for entry in result["entities"].values()))
        live["observation"]["actor_chain"]["nodes"].reverse()
        self.assertEqual(correlate(document, live), result)

    def test_pointer_changes_abort_and_bounds_are_explicit(self):
        snapshot = observation()
        with self.assertRaises(SnapshotUnstable):
            sample_man_bindings(Client(snapshot, mutate=True), PROFILE, snapshot)
        snapshot = observation(MAX_NODES)
        binding = sample_man_bindings(Client(snapshot), PROFILE, snapshot)
        self.assertTrue(binding["complete"])
        self.assertEqual(binding["request_count"], 45)
        self.assertEqual(binding["bytes_read"], 3840)
        snapshot = observation(MAX_NODES + 1)
        with self.assertRaises(ProtocolError):
            sample_man_bindings(Client(snapshot), PROFILE, snapshot)

    def test_stale_session_epoch_disc_and_profile_reject(self):
        for field in ("epoch_id", "runtime_process_identity", "guard_token", "profile_hash", "disc_identity"):
            live = status(); live["actor_bindings"][field] = "stale"
            self.assertFalse(correlate(imported(), live)["available"], field)
        live = status(); live["actor_bindings"]["last_frame"] = 99
        self.assertFalse(correlate(imported(), live)["available"])

    def test_project_live_layer_never_authors_and_disconnect_clears(self):
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            document = imported(); project.import_metadata(document); project.save()
            before = deepcopy(project._document())
            project.correlate_runtime(status())
            entry = project.state()["scene"]["entities"][0]
            self.assertEqual(entry["components"]["RuntimeCorrelation"]["status"], "candidate")
            self.assertEqual(project._document(), before)
            self.assertFalse(project.dirty)
            project.command({"type": "set_transform", "entity_id": document["actors"][0]["semantic_id"],
                             "position": {"x": 1216}})
            compared = project.state()["scene"]["entities"][0]["components"]["RuntimeCorrelation"]["candidates"][0]
            self.assertTrue(compared["authored_comparison"]["axes"]["x"]["matches"])
            self.assertFalse(project.state()["scene"]["entities"][0]["components"]["RuntimeCorrelation"]["binding_confirmed"])
            project.correlate_runtime({"available": False})
            self.assertFalse(project.state()["runtime_correlation"]["available"])
            project.correlate_runtime(status()); project.set_scene("scene://town01")
            self.assertFalse(project.state()["runtime_correlation"]["available"])
            project.correlate_runtime(status()); project.save()
            self.assertFalse(ProjectService.open(project.root).state()["runtime_correlation"]["available"])


if __name__ == "__main__":
    unittest.main()
