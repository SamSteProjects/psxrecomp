from copy import deepcopy
from contextlib import nullcontext
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.controller_branches import snapshot,review,COMPONENT
from sdk.controller_system_flags import review as selector_review,snapshot as selector_snapshot
from importer.controller_system_flags import ControllerSystemFlagAuthoringContext
from test_controller_branches import source,OWNER,ID
from test_branch_authoring import family_script
from test_project_workflow import synthetic_scene


class ControllerBranchWorkflow(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.p=ProjectService(Path(self.temp.name));self.p.import_metadata(synthetic_scene())
        src,_=source(family_script('SYSFLAG_TEST')[0]);self.context=ControllerSystemFlagAuthoringContext(src)
        for name,value in [('importer.pipeline._disc_context',nullcontext()),('sdk.resources._verify',None),('sdk.controller_system_flags.load_controller_system_flag_context',self.context)]:
            mock=patch(name,return_value=value);mock.start();self.addCleanup(mock.stop)

    def apply(self,value):
        r=review(self.p,OWNER,ID,value);self.p.command(dict(type='set_controller_branch',entity_id=OWNER,operand_id=ID,value=value,review_key=r['review_key']));return r

    def selector(self,value):
        operand=ID.replace('/branch/','/system-flag/');r=selector_review(self.p,OWNER,operand,value)
        self.p.command(dict(type='set_controller_system_flag_selector',entity_id=OWNER,operand_id=operand,value=value,review_key=r['review_key']))

    def test_read_only_review_history_save_open_reset_and_authored_asset(self):
        before=deepcopy((self.p._document(),self.p.undo_stack,self.p.redo_stack));r=review(self.p,OWNER,ID,{'target_pc':5})
        self.assertEqual(before,(self.p._document(),self.p.undo_stack,self.p.redo_stack));self.assertFalse(r['project_changed']);self.assertFalse(r['gameplay_verified'])
        self.assertTrue(all(at in (64,65) for at in r['changed_decoded_byte_offsets']))
        self.apply({'target_pc':5});saved=deepcopy(self.p.overrides)
        target=next(t for t in snapshot(self.p,OWNER)['targets'] if t['semantic_id']==ID)
        self.assertEqual(target['values'],{'target_pc':10});self.assertEqual(target['current_target_pc'],5)
        self.assertIn(COMPONENT,self.p.authored_assets()[0]['authored'])
        self.p.undo();self.assertFalse(self.p.overrides);self.p.redo();self.assertEqual(self.p.overrides,saved)
        opened=ProjectService.open(self.p.save());self.assertEqual(opened._document(),self.p._document())
        self.apply(None);self.assertFalse(self.p.overrides);self.p.undo();self.assertEqual(self.p.overrides,saved)

    def test_selector_and_branch_edits_preserve_each_other_and_source_layers(self):
        self.selector({'index':4095});self.apply({'target_pc':5})
        saved=deepcopy(self.p.overrides);self.assertEqual(set(saved[OWNER]),{'ControllerSystemFlags',COMPONENT})
        self.assertEqual(selector_snapshot(self.p,OWNER)['targets'][0]['current_index'],4095)
        self.selector({'index':4094});self.assertEqual(self.p.overrides[OWNER][COMPONENT],saved[OWNER][COMPONENT])
        self.apply(None);self.assertEqual(set(self.p.overrides[OWNER]),{'ControllerSystemFlags'})
        self.p.undo();self.selector(None);self.assertEqual(set(self.p.overrides[OWNER]),{COMPONENT})
        target=next(t for t in snapshot(self.p,OWNER)['targets'] if t['semantic_id']==ID);self.assertEqual(target['current_target_pc'],5)
        self.p.undo();opened=ProjectService.open(self.p.save());self.assertEqual(opened.overrides,self.p.overrides)

    def test_stale_bad_values_wrong_owners_source_hash_and_modes_refuse_atomically(self):
        stale=review(self.p,OWNER,ID,{'target_pc':5});self.selector({'index':4095});before=deepcopy((self.p._document(),self.p.undo_stack,self.p.redo_stack))
        with self.assertRaises(ProjectError):self.p.command(dict(type='set_controller_branch',entity_id=OWNER,operand_id=ID,value={'target_pc':5},review_key=stale['review_key']))
        for value in [{'target_pc':True},{'target_pc':6},{'target_pc':32768},{'index':1}]:
            with self.assertRaises(ProjectError):review(self.p,OWNER,ID,value)
        for owner,operand in [(OWNER.replace('/controllers/','/actors/'),ID),(OWNER.replace('fixture','other'),ID),(OWNER,ID.replace('/0005','/0006'))]:
            with self.assertRaises(ProjectError):review(self.p,owner,operand,{'target_pc':5})
        self.assertEqual(before,(self.p._document(),self.p.undo_stack,self.p.redo_stack))
        self.apply({'target_pc':5});self.p.overrides[OWNER][COMPONENT]['source_record_sha256']='f'*64
        with self.assertRaises(ProjectError):snapshot(self.p,OWNER)
        with self.assertRaises(ProjectError):ProjectService.open(self.p.save())
        self.p.overrides[OWNER][COMPONENT]['source_record_sha256']=self.p.overrides[OWNER]['ControllerSystemFlags']['source_record_sha256'];self.p.mode='live'
        with self.assertRaises(ProjectError):review(self.p,OWNER,ID,None)

    def test_pending_build_refuses_before_any_output(self):
        from sdk.build import _build_project,BuildError
        self.apply({'target_pc':5})
        with self.assertRaisesRegex(BuildError,'Controller branch native Build integration is pending'):_build_project(self.p,None,review_only=True)
        self.assertFalse((self.p.root/'Builds').exists())

    def test_unknown_controller_paths_remain_explicitly_unsupported(self):
        src,_=source(b'\x2a')
        with patch('sdk.controller_system_flags.load_controller_system_flag_context',return_value=ControllerSystemFlagAuthoringContext(src)):
            report=snapshot(self.p,OWNER);self.assertFalse(report['supported']);self.assertIsNone(report['current_report']);self.assertTrue(report['reason'])
            with self.assertRaises(ProjectError):review(self.p,OWNER,ID,{'target_pc':5})
