"""Encoded scene references remain source-qualified and distinct from routes."""
from copy import deepcopy
import unittest

from integrations.legaia.tests.test_importer_script_catalog import catalog, forbidden_fields
from sdk.transitions import build_transition_graph


class SceneTransitions(unittest.TestCase):
    def test_named_destination_navigation_and_provenance_isolation(self):
        source = catalog(b"\x3f\0\0\x06town02\x01\x82\x03")
        before = deepcopy(source)
        graph = build_transition_graph(source, ["scene://fixture", "scene://town02"])
        self.assertEqual(len(graph["edges"]), 1)
        edge = graph["edges"][0]
        self.assertEqual((edge["source"], edge["target"]), ("scene://fixture", "scene://town02"))
        self.assertEqual(edge["reachability"], "not_evaluated")
        self.assertEqual(edge["owner_id"], "scene://fixture/actors/man-p1/0001")
        self.assertTrue(graph["nodes"][1]["imported"])
        self.assertEqual(edge["reference"]["entry_z_encoded"], 130)
        self.assertEqual(forbidden_fields(graph), set())
        edge["reference"].clear(); edge["source_record"].clear()
        self.assertEqual(source, before)

    def test_authored_entry_layers_do_not_replace_imported_reference(self):
        source = catalog(b"\x3f\0\0\x06town02\x01\x82\x03")
        edge = build_transition_graph(source, [])["edges"][0]
        key = edge["entry_layers"]["transition_id"]
        overrides = {edge["owner_id"]: {"Transitions": {"entries": {key: {"entry_x_encoded": 99}}}}}
        changed = build_transition_graph(source, [], overrides)["edges"][0]
        self.assertEqual(changed["reference"]["entry_x_encoded"], 1)
        self.assertEqual(changed["entry_layers"]["effective"]["entry_x_encoded"], 99)
        self.assertEqual(changed["entry_layers"]["effective"]["entry_z_encoded"], 130)
        self.assertEqual(changed["reachability"], "not_evaluated")
        changed["entry_layers"]["authored"].clear()
        self.assertEqual(overrides[edge["owner_id"]]["Transitions"]["entries"][key]["entry_x_encoded"], 99)

    def test_unknown_names_and_self_references_do_not_invent_scenes(self):
        source = catalog(b"\x3f\0\0\x06Town02\1\2\3")
        graph = build_transition_graph(source, [])
        self.assertIsNone(graph["nodes"][1]["name"])
        self.assertFalse(graph["nodes"][1]["imported"])
        self.assertIn("unresolved-target", graph["edges"][0]["target"])
        source = catalog(b"\x3f\0\0\x07fixture\1\2\3")
        graph = build_transition_graph(source, ["scene://fixture"])
        self.assertEqual(len(graph["nodes"]), 1)
        self.assertEqual(graph["nodes"][0]["roles"], ["source", "destination"])
        empty = build_transition_graph(catalog(b"\x2a"), [])
        self.assertEqual(empty["edges"], [])
        self.assertGreater(empty["coverage"]["partial_script_count"], 0)


if __name__ == "__main__":
    unittest.main()
