"""Encoded flag operands must not become fabricated runtime identities."""
from copy import deepcopy
import unittest
from integrations.legaia.tests.test_importer_script_catalog import catalog, forbidden_fields
from sdk.flags import build_flag_index


class SceneFlags(unittest.TestCase):
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
