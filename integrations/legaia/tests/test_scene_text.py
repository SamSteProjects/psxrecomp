"""Text discovery preserves source layers, exclusions and stale-source gates."""
from contextlib import nullcontext
from copy import deepcopy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from importer.core import ImportError
from sdk.project import ProjectService, ProjectError
from sdk.resources import scene_text_index
from test_project_workflow import synthetic_scene

ACTOR='scene://fixture/actors/man-p1/0001'
P2='scene://fixture/scripts/man-p2/0000'

def options(owner):
    return dict(supported=True,reason=None,runs=[dict(semantic_id='script://'+owner[8:]+'/dialogue/0008/run/0009',
                text='Hello',pc=9,max_length=5)],unresolved_overrides=[])

class SceneTextTests(unittest.TestCase):
    def run_index(self, project, callback, *, keys=('source','source')):
        scripts=[dict(asset_kind='script',owner_semantic_id=owner,name=owner,source_record={'partition':partition},status='partial')
                 for owner,partition in ((ACTOR,1),(P2,2))]
        catalog=dict(assets=scripts,partial_script_count=2,unavailable_script_count=0)
        with patch('sdk.resources._scene',return_value=(synthetic_scene(),'source')), \
             patch('sdk.resources._verify'),patch('sdk.resources._disc_context',return_value=nullcontext()), \
             patch('sdk.resources.source_key',side_effect=keys), \
             patch('importer.script_catalog.load_script_asset_catalog',return_value=catalog), \
             patch('importer.dialogue_authoring.load_dialogue_authoring_context',return_value=SimpleNamespace(options=callback)):
            return scene_text_index(project)

    def test_layers_legacy_restrictions_and_no_project_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.import_metadata(synthetic_scene());p.disc_path='fixture-disc'
            run=options(ACTOR)['runs'][0]['semantic_id'];p.overrides={ACTOR:{'Dialogue':{'runs':{run:'OK'}}}}
            before=deepcopy(p.state());result=self.run_index(p,options)
            self.assertEqual(result['runs'][0]['retail_text'],'Hello')
            self.assertEqual(result['runs'][0]['effective_text'],'OK   ')
            self.assertEqual(result['runs'][1]['effective_text'],'Hello')
            self.assertEqual(result['runs'][1]['partition'],2)
            self.assertEqual(p.state(),before)
            p.overrides[ACTOR]['Dialogue']['runs'][run]='A|B'
            legacy=self.run_index(p,options)['runs'][0]
            self.assertIsNone(legacy['effective_text']);self.assertIn('newline',legacy['validation_error'])
            def unsupported(owner):
                if owner==P2:raise ImportError('Unknown record boundary')
                return options(owner)
            result=self.run_index(p,unsupported)
            self.assertEqual(len(result['runs']),1);self.assertEqual(result['coverage']['script_count'],2)
            self.assertEqual(result['restrictions'][0]['reason'],'Unknown record boundary')

    def test_stale_source_and_text_budget_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.import_metadata(synthetic_scene());p.disc_path='fixture-disc'
            with self.assertRaisesRegex(ProjectError,'changed'):
                self.run_index(p,options,keys=('changed',))
            def huge(owner):
                result=options(owner);result['runs']*=8193;return result
            with self.assertRaisesRegex(ProjectError,'budget'):
                self.run_index(p,huge)
            def changed(owner):
                p.overrides[ACTOR]={'Dialogue':{'runs':{'unresolved':'changed'}}}
                return options(owner)
            with self.assertRaisesRegex(ProjectError,'changed'):
                self.run_index(p,changed)

if __name__=='__main__':unittest.main()
