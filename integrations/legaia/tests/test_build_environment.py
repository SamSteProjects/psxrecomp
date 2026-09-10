"""Private retail acceptance for source-bound MAP overlays."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from hashlib import sha256
import json
import struct

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sdk.project import ProjectService
from sdk.build import build_project
from importer.pipeline import import_scene
from importer.environment import load_environment_preview_catalog
from sdk.scene_preview import environment_effective_transforms


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
class EnvironmentBuildTests(unittest.TestCase):
    def test_individual_decoration_persists_previews_and_builds(self):
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            project.disc_path = os.environ['LEGAIA_DISC_BIN']
            project.import_metadata(import_scene(project.disc_path, 'town01'))
            original = project._environment_source('scene://town01')
            value = {'source_sha256':sha256(original).hexdigest(),
                     'edits':[{'record_index':194,'offset':{'x':64}}],
                     'instances':[{'cell_index':1833,'offset':{'x':128}}]}
            project.command({'type':'set_environment_transforms','entity_id':'scene://town01','value':value})
            project.undo()
            self.assertEqual(project.overrides, {})
            project.redo()
            reopened = ProjectService.open(project.save())
            self.assertEqual(reopened.overrides['scene://town01']['Environment'],value)
            catalog = load_environment_preview_catalog(project.disc_path,'town01')
            effective = environment_effective_transforms(reopened,catalog.metadata)
            self.assertEqual(effective['environment://town01/field-map/decorations/01833']['position']['x'],5440)
            self.assertEqual(effective['environment://town01/field-map/decorations/02089']['position']['x'],5376)
            result = build_project(reopened)
            audit = json.loads(Path(result['audit']).read_text())
            overlay = audit['overlays'][0]
            changed = (Path(result['package_directory']) / overlay['file']).read_bytes()
            instance = next(row for row in audit['edits'] if 'allocation' in row)
            allocation = instance['allocation']
            self.assertEqual(instance['affected_grid_cells'],[1833])
            self.assertEqual(allocation['allocated_record_index'],5)
            self.assertEqual(struct.unpack_from('<H',changed,0x8000+2089*2)[0],0x20c2)
            self.assertEqual(struct.unpack_from('<H',changed,0x8000+1833*2)[0],0x2005)
            self.assertEqual(struct.unpack_from('<h',changed,194*32)[0],64)
            self.assertEqual(struct.unpack_from('<h',changed,5*32)[0],128)
            allowed = set(range(5*32,6*32)) | {194*32,194*32+1,0x8000+1833*2,0x8000+1833*2+1}
            self.assertTrue(all(a==b or i in allowed for i,(a,b) in enumerate(zip(original,changed))))

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
