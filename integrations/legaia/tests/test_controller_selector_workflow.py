from copy import deepcopy
from contextlib import nullcontext
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.controller_system_flags import snapshot,review,COMPONENT
from test_controller_system_flags import context,fixture,OWNER,ID
from integrations.legaia.tests.test_project_workflow import synthetic_scene


class ControllerWorkflow(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.p=ProjectService(Path(self.temp.name));self.p.import_metadata(synthetic_scene())
        for name,value in [('importer.pipeline._disc_context',nullcontext()),('sdk.resources._verify',None),('sdk.controller_system_flags.load_controller_system_flag_context',context(fixture()))]:
            mock=patch(name,return_value=value);mock.start();self.addCleanup(mock.stop)

    def apply(self,value):
        r=review(self.p,OWNER,ID,value);self.p.command(dict(type='set_controller_system_flag_selector',entity_id=OWNER,operand_id=ID,value=value,review_key=r['review_key']));return r

    def test_review_history_save_open_clear_and_asset_layers(self):
        before=deepcopy((self.p._document(),self.p.undo_stack,self.p.redo_stack))
        r=review(self.p,OWNER,ID,{'index':4095});self.assertEqual((self.p._document(),self.p.undo_stack,self.p.redo_stack),before)
        self.assertFalse(r['project_changed']);self.assertFalse(r['gameplay_verified'])
        self.apply({'index':4095});authored=deepcopy(self.p.overrides)
        self.assertEqual(snapshot(self.p,OWNER)['targets'][0]['values'],{'index':291})
        self.assertEqual(snapshot(self.p,OWNER)['targets'][0]['current_index'],4095)
        self.assertEqual(self.p.authored_assets()[0]['kind'],'controller')
        self.p.undo();self.assertFalse(self.p.overrides);self.p.redo();self.assertEqual(self.p.overrides,authored)
        opened=ProjectService.open(self.p.save());self.assertEqual(opened.overrides,authored);self.assertEqual(opened.imports,self.p.imports)
        self.apply(None);self.assertFalse(self.p.overrides);self.p.undo();self.assertEqual(self.p.overrides,authored)

    def test_stale_invalid_mode_and_identity_refusals_are_atomic(self):
        stale=review(self.p,OWNER,ID,{'index':1});self.apply({'index':2})
        before=deepcopy((self.p._document(),self.p.undo_stack,self.p.redo_stack))
        with self.assertRaises(ProjectError):self.p.command(dict(type='set_controller_system_flag_selector',entity_id=OWNER,operand_id=ID,value={'index':1},review_key=stale['review_key']))
        for value in ({'index':True},{'index':4096},{'bit':1}):
            with self.assertRaises(ProjectError):review(self.p,OWNER,ID,value)
        for owner,operand in [(OWNER.replace('fixture','other'),ID),(OWNER.replace('/controllers/','/actors/'),ID),(OWNER,ID.replace('0005','0006'))]:
            with self.assertRaises(ProjectError):review(self.p,owner,operand,{'index':1})
        self.assertEqual((self.p._document(),self.p.undo_stack,self.p.redo_stack),before)
        self.p.mode='live'
        with self.assertRaises(ProjectError):self.apply({'index':1})

    def test_saved_hash_and_mixed_components_refuse(self):
        self.apply({'index':1});self.p.overrides[OWNER][COMPONENT]['source_record_sha256']='f'*64
        with self.assertRaises(ProjectError):snapshot(self.p,OWNER)
        self.p.overrides[OWNER]['Transform']={'position':{'x':1}}
        with self.assertRaises(ProjectError):ProjectService.open(self.p.save())
