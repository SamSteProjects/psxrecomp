from copy import deepcopy
import unittest
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.actor_presets import preview
from integrations.legaia.tests import test_project_appearance as appearance_fixture
class ActorPresets(unittest.TestCase):
    setUp=appearance_fixture.ProjectAppearanceTests.setUp
    assign=appearance_fixture.ProjectAppearanceTests.assign
    def capture(self):
        p=self.project;self.assign();p.command({'type':'set_transform','entity_id':self.target,'position':{'x':512}})
        p.command({'type':'create_actor_template','capture':'combined','entity_id':self.target,'name':'Resident preset'})
        return next(iter(p.actor_templates))
    def test_capture_review_atomic_apply_undo_redo_save_and_noop(self):
        p=self.project;key=self.capture();p.command({'type':'clear_actor_appearance','entity_id':self.target});p.command({'type':'set_transform','entity_id':self.target,'position':{'x':256,'z':768}})
        before=deepcopy(p.overrides);imports=deepcopy(p.imports);depth=len(p.undo_stack)
        report=preview(p,key,self.target);self.assertEqual(p.overrides,before)
        cmd={'type':'apply_actor_template','template_id':key,'entity_id':self.target,'review_key':report['review_key']};p.command(cmd)
        self.assertEqual(len(p.undo_stack),depth+1);self.assertEqual(p.overrides[self.target]['Transform']['position'],{'x':512,'z':768});self.assertEqual(p.overrides[self.target]['ActorAppearance']['donor_entity_id'],self.donor)
        p.undo();self.assertEqual(p.overrides,before);p.redo();self.assertEqual(p.imports,imports)
        restored=ProjectService.open(p.save());self.assertEqual(restored.actor_templates,p.actor_templates);self.assertEqual(restored.overrides,p.overrides)
        report=preview(p,key,self.target);self.assertFalse(report['changed']);depth=len(p.undo_stack);p.command({**cmd,'review_key':report['review_key']});self.assertEqual(len(p.undo_stack),depth)
    def test_stale_target_template_incompatible_and_live_reject_without_partial_edit(self):
        p=self.project;key=self.capture();report=preview(p,key,self.target);cmd={'type':'apply_actor_template','template_id':key,'entity_id':self.target,'review_key':report['review_key']}
        p.command({'type':'set_transform','entity_id':self.target,'position':{'z':1024}});before=deepcopy(p.overrides);depth=len(p.undo_stack)
        with self.assertRaisesRegex(ProjectError,'changed'):p.command(cmd)
        self.assertEqual(p.overrides,before);self.assertEqual(len(p.undo_stack),depth)
        report=preview(p,key,self.target);p.command({'type':'rename_actor_template','template_id':key,'name':'Changed'})
        with self.assertRaises(ProjectError):p.command({**cmd,'review_key':report['review_key']})
        with patch.object(p,'appearance_options',return_value={'options':[]}):
            with self.assertRaises(ProjectError):preview(p,key,self.target)
        self.assertEqual(p.overrides,before)
        p.mode='live'
        with self.assertRaises(ProjectError):p.command(cmd)
    def test_missing_half_and_forged_scope_rejected(self):
        p=self.project;self.assign()
        with self.assertRaises(ProjectError):p.command({'type':'create_actor_template','capture':'combined','entity_id':self.target,'name':'Missing'})
        key=self.capture();bad=deepcopy(p.actor_templates[key]);bad['components'].pop('Transform')
        with self.assertRaises(ProjectError):p._validate_template(key,bad)
        with self.assertRaises(ProjectError):preview(p,[],self.target)
if __name__=='__main__':unittest.main()
