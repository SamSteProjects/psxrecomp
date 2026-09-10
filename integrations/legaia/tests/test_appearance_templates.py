from copy import deepcopy
import unittest
from unittest.mock import patch
from integrations.legaia.tests import test_project_appearance as appearance_fixture
from sdk.project import ProjectService, ProjectError

class AppearanceTemplateTests(unittest.TestCase):
    setUp = appearance_fixture.ProjectAppearanceTests.setUp
    assign = appearance_fixture.ProjectAppearanceTests.assign
    def test_template_capture_apply_history_and_reopen(self):
        p=self.project
        self.assign()
        p.command({'type':'create_actor_template','capture':'appearance','entity_id':self.target,'name':'Worker appearance'})
        identifier=next(iter(p.actor_templates))
        self.assertEqual(p.actor_templates[identifier]['scope'],'authored-appearance-v1')
        original=deepcopy(p.imports)
        p.command({'type':'clear_actor_appearance','entity_id':self.target})
        p.command({'type':'set_transform','entity_id':self.target,'position':{'x':512}})
        before=deepcopy(p.overrides)
        p.command({'type':'apply_actor_template','template_id':identifier,'entity_id':self.target})
        self.assertEqual(p.overrides[self.target]['ActorAppearance'],{'donor_entity_id':self.donor})
        self.assertEqual(p.overrides[self.target]['Transform'],before[self.target]['Transform'])
        p.undo();self.assertEqual(p.overrides,before)
        p.redo();p.save();opened=ProjectService.open(p.root)
        self.assertEqual(opened.actor_templates,p.actor_templates)
        self.assertEqual(opened.overrides,p.overrides)
        self.assertEqual(p.imports,original)
        self.assertIn('Appearance template',next(r for r in p.authored_assets() if r['id']==identifier)['changes'])
        with patch.object(p,'appearance_options',return_value={'options':[]}):
            snapshot=deepcopy(p.state())
            with self.assertRaises(ProjectError):p.command({'type':'apply_actor_template','template_id':identifier,'entity_id':self.target})
            self.assertEqual(p.state(),snapshot)

    def test_missing_and_forged_appearance_template_rejected(self):
        p=self.project
        with self.assertRaises(ProjectError):p.command({'type':'create_actor_template','capture':'appearance','entity_id':self.target,'name':'Missing'})
        self.assign();p.command({'type':'create_actor_template','capture':'appearance','entity_id':self.target,'name':'Pair'})
        key=next(iter(p.actor_templates));template=deepcopy(p.actor_templates[key])
        template['source']['scene_id']='scene://wrong'
        with self.assertRaises(ProjectError):p._validate_template(key,template)
        template=deepcopy(p.actor_templates[key]);template['components']['ActorAppearance']['donor_entity_id']='scene://other/actors/0001'
        with self.assertRaises(ProjectError):p._validate_template(key,template)

if __name__=='__main__':unittest.main()
