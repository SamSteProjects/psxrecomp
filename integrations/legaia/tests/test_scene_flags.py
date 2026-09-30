"""Encoded flag operands must not become fabricated runtime identities."""
from copy import deepcopy
import unittest
from integrations.legaia.tests.test_importer_script_catalog import catalog, forbidden_fields
from sdk.flags import build_flag_index, observed_node_flags


class SceneFlags(unittest.TestCase):
    def test_project_discovery_keeps_scene_identity_and_unavailable_coverage(self):
        from contextlib import nullcontext
        from types import SimpleNamespace
        from unittest.mock import patch
        from pathlib import Path
        from importer.core import ImportError
        from sdk.resources import project_flag_index
        documents={f'scene://{name}':{'scene':{'name':name}} for name in ('first','second','missing')}
        project=SimpleNamespace(root=Path('/fixture'),imports=documents,disc_path='synthetic',active_scene='scene://first')
        before=deepcopy(documents)
        def load(disc,name):
            if name=='missing':raise ImportError('No supported script carrier')
            result=catalog(b'\x2b\x02')
            result['scene']=name
            for asset in result['assets']:asset['semantic_id']=asset['semantic_id'].replace('fixture',name)
            return result
        with patch('sdk.resources._disc_context',return_value=nullcontext()),patch('sdk.resources._verify'),patch('importer.script_catalog.load_script_asset_catalog',side_effect=load):
            result=project_flag_index(project)
        self.assertEqual(result['reference_count'],2)
        self.assertEqual(len(result['groups']),2)
        self.assertEqual({g['scene_name'] for g in result['groups']},{'first','second'})
        self.assertEqual(len({g['id'] for g in result['groups']}),2)
        self.assertEqual(next(s for s in result['scenes'] if s['scene_name']=='missing')['status'],'unavailable')
        self.assertTrue(all(g['runtime_value'] is None for g in result['groups']))
        self.assertEqual(project.imports,before)
        self.assertEqual(project.active_scene,'scene://first')

    def test_project_discovery_rejects_stale_import_instead_of_partial_success(self):
        from contextlib import nullcontext
        from types import SimpleNamespace
        from unittest.mock import patch
        from pathlib import Path
        from sdk.project import ProjectError
        from sdk.resources import project_flag_index
        project=SimpleNamespace(root=Path('/fixture'),disc_path='synthetic',imports={'scene://fixture':{'scene':{'name':'fixture'}}})
        with patch('sdk.resources._disc_context',return_value=nullcontext()),patch('sdk.resources._verify',side_effect=ProjectError('stale source')),patch('importer.script_catalog.load_script_asset_catalog') as loader:
            with self.assertRaises(ProjectError):project_flag_index(project)
            loader.assert_not_called()

    def test_captured_node_flags_require_scene_epoch_and_trusted_field(self):
        field = {"property": "flags", "offset": 16, "width": 4,
                 "confidence": "confirmed", "unresolved": False,
                 "raw_numeric_value": 0x80000001, "evidence": ["fixture"]}
        node = {"epoch_scoped_node_id": "runtime://fixture/field-node/80080000", "decoded_fields": [field]}
        status = {"available": True, "state": "observed", "observation": {
            "snapshot_current_at_capture": True, "epoch": {
                "epoch_id": "fixture", "scene_name": "town01", "last_validated_frame": 17},
            "actor_chain": {"nodes": [node]}}}
        result = observed_node_flags(status, "scene://town01")
        self.assertEqual(result["nodes"][0]["set_bits"], [0, 31])
        self.assertEqual(result["freshness"], "captured_snapshot")
        self.assertEqual(result["source_binding"], "unresolved")
        self.assertFalse(observed_node_flags(status, "scene://town0c")["available"])
        node["epoch_scoped_node_id"] = "runtime://other/field-node/80080000"
        self.assertFalse(observed_node_flags(status, "scene://town01")["available"])
        node["epoch_scoped_node_id"] = "runtime://fixture/field-node/80080000"
        field["unresolved"] = True
        self.assertEqual(observed_node_flags(status, "scene://town01")["nodes"], [])
        status["observation"]["snapshot_current_at_capture"] = False
        self.assertFalse(observed_node_flags(status, "scene://town01")["available"])

    def test_contexts_and_script_owners_stay_separate(self):
        source = catalog(b"\x2b\x02\x2b\x02\xab\x07\x02")
        script = next(row for row in source["assets"] if row["asset_kind"] == "script")
        other = deepcopy(script)
        other["semantic_id"] += "-other"
        source["assets"].append(other)
        before = deepcopy(source)
        result = build_flag_index(source)
        self.assertEqual(result["reference_count"], 6)
        self.assertEqual(len(result["groups"]), 4)
        self.assertEqual(len({group["id"] for group in result["groups"]}), 4)
        self.assertEqual(sorted(len(group["references"]) for group in result["groups"]), [1, 1, 2, 2])
        self.assertTrue(all(group["runtime_value"] is None for group in result["groups"]))
        self.assertEqual(forbidden_fields(result), set())
        result["groups"][0]["references"][0].clear()
        result["groups"][0]["source_record"].clear()
        self.assertEqual(source, before)

    def test_unknown_paths_do_not_supply_references(self):
        result = build_flag_index(catalog(b"\x2a\x2b\x02"))
        self.assertEqual(result["reference_count"], 0)
        self.assertEqual(result["groups"], [])
        self.assertGreater(result["coverage"]["partial_script_count"], 0)


if __name__ == "__main__":
    unittest.main()
