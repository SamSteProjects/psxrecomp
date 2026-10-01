"""Cross-scene text discovery must never switch or mutate the live project."""
from contextlib import nullcontext
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from importer.core import ImportError
from sdk.project import ProjectService, ProjectError
from sdk.resources import project_text_index
from test_project_workflow import synthetic_scene

class ProjectTextSearchTests(unittest.TestCase):
    def project(self, directory):
        p=ProjectService(Path(directory));doc=synthetic_scene();p.import_metadata(doc)
        other=deepcopy(doc);other['scene']={'semantic_id':'scene://other','name':'other'}
        other['actors'][0]['semantic_id']='scene://other/actors/man-p1/0001';p.imports['scene://other']=other
        p.disc_path='fixture-disc';return p

    def result(self, view):
        return dict(runs=[dict(id='script://'+view.active_scene[8:]+'/run',capacity=5,retail_text='Hello',authored_text=None,effective_text='Hello')],
                    restrictions=[],coverage=dict(script_count=1,partial_script_count=0,unavailable_script_count=0))

    def test_detached_layers_coverage_and_unavailable_scene(self):
        with tempfile.TemporaryDirectory() as directory:
            p=self.project(directory);before=deepcopy(p.state());seen=[]
            def inspect(view):
                seen.append(view.active_scene);self.assertIsNot(view,p)
                view.overrides['changed']={};return self.result(view)
            with patch('sdk.resources.source_key',return_value='source'), \
                 patch('sdk.resources._disc_context',return_value=nullcontext()), \
                 patch('sdk.resources.scene_text_index',side_effect=inspect):
                result=project_text_index(p)
            self.assertEqual(result['coverage']['script_count'],2)
            self.assertEqual({r['scene_id'] for r in result['runs']},set(p.imports))
            self.assertEqual(seen,sorted(p.imports));self.assertEqual(p.state(),before)
            def unavailable(view):
                if view.active_scene=='scene://other':raise ImportError('Unsupported carrier')
                return self.result(view)
            with patch('sdk.resources.source_key',return_value='source'), \
                 patch('sdk.resources._disc_context',return_value=nullcontext()), \
                 patch('sdk.resources.scene_text_index',side_effect=unavailable):
                result=project_text_index(p)
            self.assertEqual(len(result['runs']),1);self.assertEqual(result['scenes'][1]['status'],'unavailable')
            self.assertEqual(p.state(),before)

    def test_changed_project_and_aggregate_budget_reject(self):
        with tempfile.TemporaryDirectory() as directory:
            p=self.project(directory)
            def changed(view):
                p.overrides['scene://fixture/actors/man-p1/0001']={'Dialogue':{'runs':{'unknown':'new'}}}
                return self.result(view)
            with patch('sdk.resources.source_key',return_value='source'), \
                 patch('sdk.resources._disc_context',return_value=nullcontext()), \
                 patch('sdk.resources.scene_text_index',side_effect=changed):
                with self.assertRaisesRegex(ProjectError,'changed'):project_text_index(p)
            def huge(view):
                result=self.result(view);result['runs']*=32769;return result
            with patch('sdk.resources.source_key',return_value='source'), \
                 patch('sdk.resources._disc_context',return_value=nullcontext()), \
                 patch('sdk.resources.scene_text_index',side_effect=huge):
                with self.assertRaisesRegex(ProjectError,'budget'):project_text_index(p)

if __name__=='__main__':unittest.main()
