from copy import deepcopy
from contextlib import nullcontext
from unittest.mock import patch
import unittest
from sdk.project import ProjectError,ProjectService,digest
from sdk.preset_batch import review
from integrations.legaia.tests import test_project_appearance as fixture

class PresetBatchTests(unittest.TestCase):
    setUp=fixture.ProjectAppearanceTests.setUp
    assign=fixture.ProjectAppearanceTests.assign
    def capture(self,scope='combined'):
        p=self.project;p.disc_path='synthetic-disc.bin';self.assign();p.command(dict(type='set_transform',entity_id=self.target,position={'x':512}))
        p.command(dict(type='create_actor_template',entity_id=self.target,capture=scope,name='Group preset'));return next(iter(p.actor_templates))
    def run_review(self,key,ids=None):return review(self.project,key,ids or [self.target,self.donor])
    def source_patches(self):
        self.enterContext(patch('importer.pipeline._disc_context',return_value=nullcontext()))
        self.enterContext(patch('sdk.template_files._verify_source',return_value=digest(self.document)))
        self.enterContext(patch('sdk.resources._verify'))
    def test_all_scopes_atomic_history_save_open_and_noop(self):
        self.source_patches()
        for scope in ['position','appearance','combined']:
            with self.subTest(scope=scope):
                p=self.project;p.actor_templates={};key=self.capture(scope);p.command(dict(type='clear_actor_appearance',entity_id=self.target));p.command(dict(type='set_transform',entity_id=self.donor,position={'z':768}))
                before=deepcopy(p.overrides);imports=deepcopy(p.imports);depth=len(p.undo_stack);report=self.run_review(key)
                self.assertEqual(p.overrides,before);self.assertEqual(len(p.undo_stack),depth)
                self.assertEqual([row['entity_id'] for row in report['targets']],sorted([self.target,self.donor]))
                cmd=dict(type='apply_actor_preset_batch',template_id=key,actor_ids=[self.donor,self.target],review_key=report['review_key']);p.command(cmd)
                self.assertEqual(len(p.undo_stack),depth+1);self.assertEqual(p.overrides[self.donor]['Transform']['position']['z'],768);after=deepcopy(p.overrides)
                p.undo();self.assertEqual(p.overrides,before);p.redo();self.assertEqual(p.overrides,after);self.assertEqual(p.imports,imports)
                opened=ProjectService.open(p.save());self.assertEqual(opened.overrides,after);self.assertEqual(opened.actor_templates,p.actor_templates)
                report=self.run_review(key);self.assertEqual(report['changed_count'],0);depth=len(p.undo_stack);p.command({**cmd,'review_key':report['review_key']});self.assertEqual(len(p.undo_stack),depth)
    def test_stale_group_preset_membership_and_live_reject(self):
        self.source_patches();p=self.project;key=self.capture();report=self.run_review(key);cmd=dict(type='apply_actor_preset_batch',template_id=key,actor_ids=[self.target,self.donor],review_key=report['review_key'])
        p.command(dict(type='set_transform',entity_id=self.donor,position={'z':1024}));before=deepcopy(p.overrides);depth=len(p.undo_stack)
        with self.assertRaisesRegex(ProjectError,'changed'):p.command(cmd)
        self.assertEqual(p.overrides,before);self.assertEqual(len(p.undo_stack),depth)
        for ids in [[self.target],[self.target,self.target],[self.target,'unknown'],None]:
            with self.assertRaises(ProjectError):review(p,key,ids)
        fresh=self.run_review(key);p.command(dict(type='rename_actor_template',template_id=key,name='Renamed'))
        with self.assertRaises(ProjectError):p.command({**cmd,'review_key':fresh['review_key']})
        p.mode='live'
        with self.assertRaises(ProjectError):self.run_review(key)
        with self.assertRaises(ProjectError):p.command(cmd)
    def test_last_target_incompatible_and_source_failure_leave_no_partial_changes(self):
        self.source_patches();p=self.project;key=self.capture('appearance');before=deepcopy(p.overrides);depth=len(p.undo_stack);self.options.stop()
        def options(project,identifier):return {'options':[{'donor_entity_id':self.donor}] if identifier==self.target else []}
        with patch.object(ProjectService,'appearance_options',autospec=True,side_effect=options):
            with self.assertRaises(ProjectError):self.run_review(key)
        self.assertEqual(p.overrides,before);self.assertEqual(len(p.undo_stack),depth)
        with patch('sdk.resources._verify',side_effect=ProjectError('Changed retail source')):
            with self.assertRaisesRegex(ProjectError,'Changed retail'):self.run_review(key)
        self.assertEqual(p.overrides,before)
    def test_scene_projection_detaches_group_and_rejects_forged_or_stale_reports(self):
        from sdk.preset_batch import proposal_view
        self.source_patches();p=self.project;key=self.capture();report=self.run_review(key);before=deepcopy(p.overrides);history=deepcopy(p.undo_stack)
        view=proposal_view(p,report);self.assertEqual(view.overrides[self.donor],report['targets'][1]['after'])
        view.overrides[self.donor]['Transform']['position']['x']=1024
        self.assertEqual(p.overrides,before);self.assertEqual(p.undo_stack,history)
        forged=deepcopy(report);forged['targets'][1]['after']['Transform']['position']['x']=64
        with self.assertRaises(ProjectError):proposal_view(p,forged)
        p.command(dict(type='set_transform',entity_id=self.donor,position={'z':1024}))
        with self.assertRaises(ProjectError):proposal_view(p,report)

    def test_extra_command_fields_and_unavailable_disc_reject(self):
        self.source_patches();p=self.project;key=self.capture('position');report=self.run_review(key)
        with self.assertRaises(ProjectError):p.command(dict(type='apply_actor_preset_batch',template_id=key,actor_ids=[self.target,self.donor],review_key=report['review_key'],bytes='00'))
        p.disc_path=None
        with self.assertRaises(ProjectError):self.run_review(key)

if __name__=='__main__':unittest.main()
