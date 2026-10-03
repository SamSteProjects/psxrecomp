"""Entry identity must come from the decoder input, never the first sorted node."""
import unittest
from importer.script_inspection import inspect_record
from importer.branch_authoring import _graph_candidate


class ScriptFlowEntryTests(unittest.TestCase):
    def test_entry_preserved_with_lower_branch_target(self):
        # JMP at 1 has word base 2, delta -2 -> 0. The prefix is outside
        # this entry's qualified bounds and must not replace the entry identity.
        report = inspect_record(bytes.fromhex('2126feff'), 1)
        self.assertEqual(report['entry_pc'], 1)
        self.assertEqual([row['pc'] for row in report['instructions']], [1])
        self.assertEqual(report['instructions'][0]['successors'][0]['pc'], 0)

    def test_unknown_entry_retains_offset_without_fake_nodes(self):
        report = inspect_record(bytes.fromhex('000000'), 2)
        self.assertEqual(report['entry_pc'], 2)
        self.assertEqual(report['instructions'], [])
        self.assertEqual(report['stops'][0]['pc'], 2)

    def test_message_entry_is_a_real_source_boundary(self):
        report = inspect_record(bytes.fromhex('001f48690021'), 1)
        self.assertEqual(report['entry_pc'], 1)
        self.assertEqual(report['dialogues'][0]['pc'], 1)

    def test_candidate_keeps_qualified_unvisited_anchors(self):
        original = bytes.fromhex('2602002126fbff')
        candidate = bytes.fromhex('2603002126fbff')
        source = inspect_record(original, 0)
        report = _graph_candidate(original, candidate, 0, source)
        self.assertEqual(report['entry_pc'], 0)
        self.assertEqual([row['pc'] for row in report['instructions']], [0, 4])
        self.assertEqual(report['unreachable_source_pcs'], [3])
        self.assertEqual(report['unvisited_instructions'], [source['instructions'][1]])
        self.assertEqual(report['unvisited_dialogues'], [])


if __name__ == '__main__':
    unittest.main()
