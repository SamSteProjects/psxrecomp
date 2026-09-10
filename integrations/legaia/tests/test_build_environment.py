"""Private retail acceptance for source-bound MAP overlays."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from hashlib import sha256
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sdk.project import ProjectService
from sdk.build import build_project
from importer.pipeline import import_scene


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
class EnvironmentBuildTests(unittest.TestCase):
    def test_saved_shared_record_emits_exact_guarded_map(self):
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            project.disc_path = os.environ['LEGAIA_DISC_BIN']
            project.import_metadata(import_scene(project.disc_path, 'town01'))
            original = project._environment_source('scene://town01')
            project.command({'type':'set_environment_transforms', 'entity_id':'scene://town01',
                             'value':{'source_sha256':sha256(original).hexdigest(),
                                      'edits':[{'record_index':194,'offset':{'x':128}}]}})
            reopened = ProjectService.open(project.save())
            result = build_project(reopened)
            audit = json.loads(Path(result['audit']).read_text())
            self.assertEqual(result['overlay_count'], 1)
            overlay = audit['overlays'][0]
            changed = (Path(result['package_directory']) / overlay['file']).read_bytes()
            self.assertEqual(len(changed),len(original))
            self.assertEqual([i for i,(a,b) in enumerate(zip(original,changed)) if a!=b], [194*32])
            self.assertEqual(changed[194*32],128)
            self.assertEqual(overlay['expected_sha256'],sha256(original).hexdigest())
            self.assertEqual(overlay['sha256'],sha256(changed).hexdigest())
            self.assertEqual(audit['edits'][0]['affected_grid_cells'],[14*128+41,16*128+41])
            self.assertEqual(result['report']['changes'][0]['affected_grid_cell_count'],2)
            self.assertEqual(audit['validation']['lz_decode_round_trip'],'not_required_no_MAN_overlay')
            self.assertEqual(audit['validation']['live_runtime'],'not_run')


if __name__ == '__main__':
    unittest.main()
