from copy import deepcopy
from contextlib import nullcontext
import json
import unittest
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.template_files import export_file,review,parse,MAX_FILE_BYTES
from integrations.legaia.tests import test_project_appearance as fixture

class TemplateFiles(unittest.TestCase):
    def setUp(self):
        fixture.ProjectAppearanceTests.setUp(self)
        self.project.disc_path='fixture.bin'
        for target,kwargs in [('importer.pipeline._disc_context',{'side_effect':lambda _:nullcontext()}),('importer.pipeline.import_scene',{'side_effect':lambda *_:deepcopy(self.document)})]:
            mock=patch(target,**kwargs);mock.start();self.addCleanup(mock.stop)
    def capture(self,scope):
        p=self.project;fixture.ProjectAppearanceTests.assign(self)
        p.command({'type':'set_transform','entity_id':self.target,'position':{'x':512}})
        p.command({'type':'create_actor_template','entity_id':self.target,'capture':scope,'name':scope})
        return next(key for key,value in p.actor_templates.items() if value['name']==scope)
    def test_all_scopes_independent_import_one_history_and_reopen(self):
        p=self.project
        for scope in ('position','appearance','combined'):
            with self.subTest(scope=scope):
                key=self.capture(scope);value=export_file(p,key);content=json.dumps(value);before=deepcopy(p.overrides);depth=len(p.undo_stack)
                report=review(p,content,scope+' copy');new=report['template']['id'];self.assertNotEqual(key,new);self.assertNotIn(new,p.actor_templates)
                self.assertEqual(p.overrides,before);self.assertEqual(len(p.undo_stack),depth)
                p.command({'type':'import_actor_template','content':content,'name':scope+' copy','review_key':report['review_key']})
                self.assertEqual(len(p.undo_stack),depth+1);self.assertEqual(p.actor_templates[new]['components'],value['template']['components']);self.assertEqual(p.overrides,before)
                p.undo();self.assertNotIn(new,p.actor_templates);p.redo();self.assertIn(new,p.actor_templates)
        p.save();self.assertEqual(ProjectService.open(p.root).actor_templates,p.actor_templates)
    def test_cross_project_transfer_and_saved_library_source_reimport_guard(self):
        import tempfile
        from pathlib import Path
        key=self.capture('combined');content=json.dumps(export_file(self.project,key))
        with tempfile.TemporaryDirectory() as directory:
            target=ProjectService(Path(directory));target.import_metadata(self.document);target.disc_path='fixture.bin'
            with patch.object(target,'appearance_options',return_value={'options':[{'donor_entity_id':self.donor}]}):
                report=review(target,content,'Transferred preset')
                target.command({'type':'import_actor_template','content':content,'name':'Transferred preset','review_key':report['review_key']})
            self.assertNotEqual(report['template']['id'],key);self.assertEqual(target.overrides,{})
            target.save();opened=ProjectService.open(target.root)
            changed=deepcopy(self.document);changed['actors'][0]['imported_transform']['position']['x']=128
            with self.assertRaisesRegex(ProjectError,'actor presets'):opened.import_metadata(changed)
            self.assertEqual(opened.imports[target.active_scene],self.document)

    def test_source_name_schema_payload_and_stale_review_rejected(self):
        p=self.project;key=self.capture('combined');value=export_file(p,key);content=json.dumps(value)
        for mutate in [lambda v:v.update(raw_prefix_base64='payload'),lambda v:v.update(source_import_sha256='0'*64),lambda v:v['template']['source'].update(scene_id='scene://wrong'),lambda v:v['template']['components']['Transform']['position'].update(x=True),lambda v:v['template'].update(application={'available':True})]:
            forged=deepcopy(value);mutate(forged);before=deepcopy(p.actor_templates)
            with self.assertRaises(ProjectError):review(p,json.dumps(forged),'copy')
            self.assertEqual(p.actor_templates,before)
        with self.assertRaises(ProjectError):review(p,content,'combined')
        report=review(p,content,'copy');p.command({'type':'rename_actor_template','template_id':key,'name':'renamed'})
        before=deepcopy(p.actor_templates);depth=len(p.undo_stack)
        with self.assertRaises(ProjectError):p.command({'type':'import_actor_template','content':content,'name':'copy','review_key':report['review_key']})
        self.assertEqual(p.actor_templates,before);self.assertEqual(len(p.undo_stack),depth)
        p.mode='live'
        with self.assertRaises(ProjectError):p.command({'type':'import_actor_template','content':content,'name':'copy','review_key':report['review_key']})
    def test_json_bounds_duplicates_nonfinite_and_fresh_source(self):
        for content in [' '* (MAX_FILE_BYTES+1),'{}','\ud800','{"schema_version":1,"schema_version":2}','{"value":NaN}']:
            with self.assertRaises(ProjectError):parse(content)
        key=self.capture('position')
        with patch('importer.pipeline.import_scene',return_value={}):
            with self.assertRaisesRegex(ProjectError,'freshly'):export_file(self.project,key)
        # Position-only transfer must also bind the actor to the declared scene.
        self.project.actor_templates[key]['source']['entity_id']='scene://missing/actor'
        with self.assertRaises(ProjectError):export_file(self.project,key)

if __name__=='__main__':unittest.main()
