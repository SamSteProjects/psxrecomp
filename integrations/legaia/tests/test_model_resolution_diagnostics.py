"""Initial-reference warnings are derived, scene scoped and preserve Retail evidence."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from sdk.project import ProjectError, ProjectService
from test_project_appearance import appearance_scene


class ModelResolutionDiagnostics(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = ProjectService(Path(self.tmp.name))
        self.document = appearance_scene()
        self.target, self.donor = [a['semantic_id'] for a in self.document['actors']]

    def warnings(self):
        return [d for d in self.project.state()['diagnostics']
                if isinstance(d, dict) and d.get('code') == 'Unresolved Initial Model References']

    def test_resolved_and_no_active_scene_have_no_warning(self):
        self.project.import_metadata(self.document)
        self.assertEqual(self.warnings(), [])
        self.project.active_scene = None
        self.assertEqual(self.warnings(), [])

    def test_warning_is_detached_and_persists_through_save_open(self):
        self.document['actors'][0]['model_reference'].update(
            asset_semantic_id=None, resolution_status='pool_index_out_of_bounds')
        self.project.import_metadata(self.document)
        before = deepcopy(self.project._document())
        warning = self.warnings()[0]
        self.assertEqual((warning['retail_actor_count'], warning['current_actor_count'], warning['current_npc_count']), (1, 1, 0))
        warning['retail_actor_count'] = 999
        self.assertEqual(self.warnings()[0]['retail_actor_count'], 1)
        self.assertEqual(self.project._document(), before)
        restored = ProjectService.open(self.project.save())
        self.assertEqual(restored.state()['diagnostics'], self.project.state()['diagnostics'])

    def test_warning_does_not_relax_unresolved_appearance_refusal(self):
        self.document['actors'][0]['model_reference'].update(
            asset_semantic_id=None, resolution_status='pool_index_out_of_bounds')
        self.project.import_metadata(self.document)
        before = deepcopy(self.project._document())
        with patch.object(self.project, 'appearance_options', return_value={
                'supported': True, 'options': [{'donor_entity_id': self.donor}]}):
            with self.assertRaises(ProjectError):
                self.project.command({'type': 'set_actor_appearance', 'entity_id': self.target,
                                      'donor_entity_id': self.donor})
        warning = self.warnings()[0]
        self.assertEqual((warning['retail_actor_count'], warning['current_actor_count']), (1, 1))
        self.assertIn('gameplay visibility is unverified', warning['message'])
        self.assertEqual(self.project._document(), before)
        self.assertEqual(self.project.imports['scene://fixture'], self.document)


if __name__ == '__main__':
    unittest.main()
