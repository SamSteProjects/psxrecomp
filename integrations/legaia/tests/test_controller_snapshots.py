"""Combined workspace snapshots preserve every family contract and request isolation."""
from copy import deepcopy
from contextlib import nullcontext
from importlib import import_module
from unittest.mock import patch
import unittest
import test_controller_global_byte_workflow as fixtures
from sdk.project import ProjectError
from sdk.controller_snapshots import snapshot, FAMILIES, _request_preparation
from sdk.controller_system_flags import prepare, state_key

class ControllerSnapshots(unittest.TestCase):
    def setUp(self):
        fixture=fixtures.ControllerGlobalByteWorkflow()
        fixture.setUp();self.addCleanup(fixture.doCleanups)
        self.p=fixture.p;self.owner=fixtures.OWNER

    def test_complete_batch_matches_individual_families_with_one_preparation(self):
        before=deepcopy((self.p._document(),self.p.imports,self.p.undo_stack,self.p.redo_stack))
        expected={family:import_module('sdk.'+module).snapshot(self.p,self.owner) for family,module in FAMILIES}
        with patch('sdk.resources._verify') as verify, patch('sdk.controller_system_flags.load_controller_system_flag_context',return_value=self.context()) as loader:
            value=snapshot(self.p,self.owner,state_key(self.p))
            self.assertEqual(verify.call_count,1);self.assertEqual(loader.call_count,1)
        self.assertEqual(value['families'],expected);self.assertEqual(len(value['families']),12)
        self.assertTrue(value['read_only']);self.assertFalse(value['project_changed']);self.assertFalse(value['gameplay_verified'])
        self.assertEqual(before,(self.p._document(),self.p.imports,self.p.undo_stack,self.p.redo_stack))
        value['families']['ControllerGlobalBytes']['targets'][0]['values']['byte_values'][0]=42
        self.assertEqual(snapshot(self.p,self.owner,state_key(self.p))['families'],expected)
        self.assertIsNone(_request_preparation.get())

    def context(self):
        from sdk.controller_system_flags import load_controller_system_flag_context
        return load_controller_system_flag_context(None,None)

    def test_scope_is_withdrawn_on_family_failure_and_next_request_is_fresh(self):
        with patch('sdk.controller_global_bytes.snapshot',side_effect=ProjectError('family failure')):
            with self.assertRaisesRegex(ProjectError,'family failure'):snapshot(self.p,self.owner,state_key(self.p))
        self.assertIsNone(_request_preparation.get())
        with patch('sdk.resources._verify') as verify:
            prepare(self.p,self.owner)
            self.assertEqual(verify.call_count,1)

    def test_changed_key_owner_mode_and_mid_request_state_refuse(self):
        with self.assertRaises(ProjectError):snapshot(self.p,self.owner,'f'*64)
        with self.assertRaises(ProjectError):snapshot(self.p,self.owner.replace('fixture','foreign'),state_key(self.p))
        self.p.mode='live'
        with self.assertRaises(ProjectError):snapshot(self.p,self.owner,state_key(self.p))
        self.p.mode='edit'
        module=import_module('sdk.controller_global_bytes');original=module.snapshot
        def changed(project,owner):
            result=original(project,owner);project.mode='live';return result
        with patch.object(module,'snapshot',side_effect=changed):
            with self.assertRaisesRegex(ProjectError,'changed during shared preparation'):snapshot(self.p,self.owner,state_key(self.p))
        self.assertIsNone(_request_preparation.get())

    def test_family_binding_and_registry_completeness_refuse(self):
        module=import_module('sdk.controller_global_bytes');original=module.snapshot
        for field,value in [('owner_id','foreign'),('state_key','f'*64),('source_record_sha256','f'*64),('current_record_sha256','f'*64),('gameplay_verified',True)]:
            def forged(project,owner):
                result=original(project,owner);result[field]=value;return result
            with patch.object(module,'snapshot',side_effect=forged):
                with self.assertRaisesRegex(ProjectError,'lost its source binding'):snapshot(self.p,self.owner,state_key(self.p))
            self.assertIsNone(_request_preparation.get())
        with patch('sdk.controller_snapshots.FAMILIES',FAMILIES[:-1]):
            with self.assertRaisesRegex(ProjectError,'registry is incomplete'):snapshot(self.p,self.owner,state_key(self.p))
