"""Retail MAP Build composition proves complete region/scenery/wall byte audits."""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
import unittest
from importer.pipeline import import_scene
from importer.region_authoring import region_authoring_options
from sdk.project import ProjectService
from sdk.region_bounds import review, apply
from sdk.build import build_project, package_change_kinds

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
class RegionBuildTests(unittest.TestCase):
    def test_saved_regions_compose_one_exact_map_with_walls_and_scenery(self):
        private = Path(__file__).resolve().parents[3] / 'local-output/sdk-20260909'
        with tempfile.TemporaryDirectory(prefix='region-build-', dir=private) as raw:
            project = ProjectService(Path(raw))
            project.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'], 'town01'), os.environ['LEGAIA_DISC_BIN'])
            imported = deepcopy(project.imports)
            scene = project.active_scene
            original = project._environment_source(scene)
            record = region_authoring_options(original, 'town01')['records'][0]
            values = {key:record['encoded'][key] for key in ('x0','z0','x1','z1')}
            values['x0'] += 1
            report = review(project, record['region_id'], values)
            apply(project, dict(type='apply_region_bounds',region_id=record['region_id'], values=values,
                action='set',review_key=report['review_key']))
            for combined in (False, True):
                if combined:
                    project.command(dict(type='set_collision_walls',entity_id=scene,value={
                        'source_sha256':sha256(original).hexdigest(), 'edits':[dict(row=1,column=0,quadrant=0,
                        blocked=not bool(original[0x4080]&16))]}))
                    project.command(dict(type='set_environment_transforms',entity_id=scene,value={
                        'source_sha256':sha256(original).hexdigest(),'edits':[dict(record_index=194,offset={'x':128})]}))
                reopened = ProjectService.open(project.save())
                before = deepcopy(reopened._document())
                result = build_project(reopened)
                self.assertEqual(result['overlay_count'],1)
                audit = json.loads(Path(result['audit']).read_text(encoding='utf-8'))
                overlay = audit['overlays'][0]
                changed = (Path(result['package_directory'])/overlay['file']).read_bytes()
                expected = [record['byte_offset']]
                if combined:expected = [194*32,0x4080,*expected]
                self.assertEqual([i for i,(a,b) in enumerate(zip(original,changed)) if a!=b],expected)
                self.assertEqual(len(changed),0x12000)
                self.assertEqual(changed[record['byte_offset']],values['x0'])
                self.assertEqual(changed[record['byte_offset']+4:record['byte_offset']+8],
                                 original[record['byte_offset']+4:record['byte_offset']+8])
                region_rows = [row for row in audit['edits'] if row['scope']=='source-MAP-region-bounds-only']
                self.assertEqual(len(region_rows),1)
                self.assertEqual(region_rows[0]['semantic_id'],record['region_id'])
                self.assertEqual(region_rows[0]['field'],'region.x0')
                self.assertEqual(len(audit['edits']),len(expected))
                self.assertEqual(overlay['expected_sha256'],sha256(original).hexdigest())
                self.assertEqual(overlay['sha256'],sha256(changed).hexdigest())
                self.assertEqual(audit['validation']['live_runtime'],'not_run')
                self.assertEqual(reopened._document(),before)
                self.assertEqual(reopened.imports,imported)
                self.assertIn('source region bounds', package_change_kinds(audit['edits']))
