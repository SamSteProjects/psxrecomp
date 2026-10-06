from copy import deepcopy
from pathlib import Path
import tempfile, unittest
from sdk.project import ProjectService, ProjectError
from sdk.npc_presets import review, proposal_view
from sdk.project_copy import source_key
from importer.core import ImportError as NativeError
from contextlib import nullcontext
from unittest.mock import patch
import json
from sdk.template_files import export_file, review as transfer_review, parse, NPC_SCHEMA
from test_project_workflow import synthetic_scene

class NpcPresetTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.p=ProjectService(Path(self.directory.name));self.doc=synthetic_scene();self.p.import_metadata(self.doc)
        self.donor=self.doc['actors'][0]['semantic_id']
        self.p.command(dict(type='create_actor_draft',donor_entity_id=self.donor,name='Original',position=dict(x=128,z=512)))
        self.original=next(iter(self.p.actor_drafts))
        self.p.command(dict(type='create_npc_preset',entity_id=self.original,name='Village guard'))
        self.preset=next(iter(self.p.actor_templates));self.p.save()
    def request(self):
        return dict(template_id=self.preset,name='New guard',position=dict(x=192,z=576),expected_source_key=source_key(self.p))
    def test_frozen_library_and_reviewed_instance_persist_atomic_history(self):
        p=self.p;frozen=deepcopy(p.actor_templates);p.command(dict(type='rename_actor_draft',entity_id=self.original,name='Changed'))
        p.command(dict(type='delete_actor_draft',entity_id=self.original));self.assertEqual(p.actor_templates,frozen)
        p=ProjectService.open(p.save());self.p=p
        before=deepcopy(p._document());depth=len(p.undo_stack);report=review(p,self.request());view=proposal_view(p,report)
        self.assertEqual(p._document(),before);self.assertEqual(view.actor_drafts[report['entity_id']],report['draft'])
        p.command(dict(type='instantiate_npc_preset',**report['request'],review_key=report['review_key']))
        self.assertEqual(len(p.undo_stack),depth+1);self.assertEqual(p.imports[self.doc['scene']['semantic_id']],self.doc)
        after=deepcopy(p.actor_drafts);p.undo();self.assertEqual(p._document(),before);p.redo();self.assertEqual(p.actor_drafts,after)
        restored=ProjectService.open(p.save());self.assertEqual(restored.actor_drafts,after);self.assertEqual(restored.actor_templates,frozen)
    def test_owned_dialogue_freezes_transfers_and_instances_independently(self):
        from test_importer_dialogue_authoring import fixture
        from sdk.npc_dialogue import review as text_review
        from sdk.template_files import NPC_DIALOGUE_SCHEMA
        context,_=fixture();p=self.p;run=context.options(self.donor)['runs'][0]['semantic_id']
        disc=p.root/'fixture.bin';disc.write_bytes(b'synthetic');p.disc_path=str(disc)
        with patch.object(ProjectService,'_dialogue_context',return_value=context), patch('importer.pipeline._disc_context',side_effect=lambda _:nullcontext()), patch('importer.pipeline.import_scene',return_value=self.doc):
            request=dict(entity_id=self.original,runs={run:'Yo'});text=text_review(p,request)
            p.command(dict(type='set_actor_draft_dialogue',**request,review_key=text['review_key']))
            p.command(dict(type='create_npc_preset',entity_id=self.original,name='Speaking resident'))
            captured=next(t for t in p.actor_templates.values() if t['name']=='Speaking resident');frozen=deepcopy(captured)
            p.command(dict(type='delete_actor_draft',entity_id=self.original));self.assertEqual(p.actor_templates[captured['id']],frozen)
            value=export_file(p,captured['id']);self.assertEqual(value['schema_version'],NPC_DIALOGUE_SCHEMA)
            content=json.dumps(value)+' '*9000;self.assertEqual(parse(content),value)
            legacy=export_file(p,self.preset)
            with self.assertRaises(ProjectError):parse(json.dumps(legacy)+' '*9000)
            wrong=deepcopy(value);wrong['schema_version']=NPC_SCHEMA
            with self.assertRaises(ProjectError):parse(json.dumps(wrong))
            target=ProjectService(p.root/'text-recipient');target.import_metadata(self.doc);target.disc_path=p.disc_path
            transfer=transfer_review(target,content,'Transferred speaker');target.command(dict(type='import_actor_template',content=content,name='Transferred speaker',review_key=transfer['review_key']))
            target=ProjectService.open(target.save());template_id=transfer['template']['id']
            placement_request=dict(template_id=template_id,name='Speaker instance',position=dict(x=256,z=640),expected_source_key=source_key(target))
            placement=review(target,placement_request);target.command(dict(type='instantiate_npc_preset',**placement_request,review_key=placement['review_key']))
            instance=placement['entity_id'];self.assertEqual(target.actor_drafts[instance]['dialogue'],frozen['components']['NpcDraft']['dialogue'])
            after=deepcopy(target.actor_drafts);target.undo();self.assertFalse(target.actor_drafts);target.redo();self.assertEqual(target.actor_drafts,after)
            edit=dict(entity_id=instance,runs={run:'Hey'});new=text_review(target,edit);target.command(dict(type='set_actor_draft_dialogue',**edit,review_key=new['review_key']))
            self.assertEqual(target.actor_templates[template_id]['components']['NpcDraft']['dialogue']['runs'][run],'Yo')
            self.assertEqual(ProjectService.open(target.save()).actor_drafts,target.actor_drafts)
            bad=deepcopy(value);bad['template']['components']['NpcDraft']['dialogue']['runs'][run]='Too long'
            with self.assertRaises(NativeError):transfer_review(target,json.dumps(bad),'Invalid speaker')

    def test_stale_malformed_live_and_imported_apply_reject_without_mutation(self):
        p=self.p;request=self.request();report=review(p,request);before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        for change in ({'template_id':[]},{'expected_source_key':[]},{'position':{'x':32,'z':576}},{'position':{'x':True,'z':576}},{'extra':True}):
            with self.assertRaises((ProjectError,NativeError)):review(p,{**request,**change})
        with self.assertRaises(ProjectError):p.command(dict(type='apply_actor_template',template_id=self.preset,entity_id=self.donor))
        tampered=deepcopy(report);tampered['draft']['name']='Tampered'
        with self.assertRaises(ProjectError):proposal_view(p,tampered)
        template=deepcopy(p.actor_templates[self.preset]);template['source']['scene_id']=[]
        with self.assertRaises(ProjectError):p._validate_template(self.preset,template)
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
        p.command(dict(type='rename_actor_template',template_id=self.preset,name='Changed preset'))
        with self.assertRaises(ProjectError):p.command(dict(type='instantiate_npc_preset',**request,review_key=report['review_key']))
        p.mode='live'
        with self.assertRaises(ProjectError):review(p,self.request())
        with self.assertRaises(ProjectError):p.command(dict(type='create_npc_preset',entity_id=self.original,name='Live'))
    def test_capture_library_undo_redo(self):
        p=self.p;frozen=deepcopy(p.actor_templates);p.undo();self.assertFalse(p.actor_templates);p.redo();self.assertEqual(p.actor_templates,frozen)
        p.command(dict(type='delete_actor_template',template_id=self.preset));self.assertFalse(p.actor_templates);p.undo();self.assertEqual(p.actor_templates,frozen)

    def test_portable_transfer_without_original_draft_and_independent_placement(self):
        p=self.p;disc=p.root/'fixture.bin';disc.write_bytes(b'synthetic');p.disc_path=str(disc)
        with patch('importer.pipeline._disc_context',side_effect=lambda _:nullcontext()), patch('importer.pipeline.import_scene',return_value=self.doc):
            value=export_file(p,self.preset);self.assertEqual(value['schema_version'],NPC_SCHEMA)
            target=ProjectService(Path(self.directory.name)/'recipient');target.import_metadata(self.doc);target.disc_path=p.disc_path
            before=deepcopy(target._document());report=transfer_review(target,json.dumps(value),'Transferred guard')
            self.assertEqual(target._document(),before);self.assertFalse(target.actor_drafts)
            target.command(dict(type='import_actor_template',content=json.dumps(value),name='Transferred guard',review_key=report['review_key']))
            transferred=report['template']['id'];self.assertNotEqual(transferred,self.preset)
            self.assertEqual(target.actor_templates[transferred]['source'],value['template']['source'])
            self.assertFalse(target.actor_drafts);target.undo();self.assertFalse(target.actor_templates);target.redo()
            target=ProjectService.open(target.save());self.assertEqual(target.actor_templates[transferred]['components'],value['template']['components'])
            request=dict(template_id=transferred,name='Transferred instance',position=dict(x=256,z=640),expected_source_key=source_key(target))
            placement=review(target,request);target.command(dict(type='instantiate_npc_preset',**request,review_key=placement['review_key']))
            self.assertEqual(target.actor_drafts[placement['entity_id']],placement['draft']);self.assertEqual(target.imports[self.doc['scene']['semantic_id']],self.doc)

    def test_portable_schema_source_payload_and_stale_rejection(self):
        p=self.p;disc=p.root/'fixture.bin';disc.write_bytes(b'synthetic');p.disc_path=str(disc)
        with patch('importer.pipeline._disc_context',side_effect=lambda _:nullcontext()), patch('importer.pipeline.import_scene',return_value=self.doc):
            value=export_file(p,self.preset);before=deepcopy((p._document(),p.undo_stack))
            for change in (lambda v:v.update(schema_version='legaia.actor-preset-file.v1'),lambda v:v.update(payload='private'),lambda v:v.update(source_import_sha256='0'*64),lambda v:v['template']['source'].update(import_sha256='0'*64),lambda v:v['template']['components']['NpcDraft'].update(donor_entity_id='wrong')):
                bad=deepcopy(value);change(bad)
                with self.assertRaises(ProjectError):transfer_review(p,json.dumps(bad),'Forged')
            self.assertEqual((p._document(),p.undo_stack),before)
            content=json.dumps(value);report=transfer_review(p,content,'New guard');p.command(dict(type='rename_actor_template',template_id=self.preset,name='Changed library'))
            with self.assertRaises(ProjectError):p.command(dict(type='import_actor_template',content=content,name='New guard',review_key=report['review_key']))
        with patch('importer.pipeline._disc_context',side_effect=lambda _:nullcontext()), patch('importer.pipeline.import_scene',return_value={}):
            with self.assertRaisesRegex(ProjectError,'freshly'):export_file(p,self.preset)

    def test_owned_waits_v4_transfer_capture_frozen_and_independent_placement(self):
        from importer.wait_authoring import WaitAuthoringContext
        from test_importer_dialogue_authoring import fixture
        from test_wait_authoring import END
        from sdk.npc_waits import review as wait_review
        context=WaitAuthoringContext(fixture(b'\x4a\1\1'+END)[0]);wait=context.options(self.donor)['targets'][0]['semantic_id'];p=self.p;disc=p.root/'fixture.bin';disc.write_bytes(b'synthetic');p.disc_path=str(disc)
        with patch.object(ProjectService,'_wait_context',return_value=context),patch('importer.pipeline._disc_context',side_effect=lambda _:nullcontext()),patch('importer.pipeline.import_scene',return_value=self.doc):
            request=dict(entity_id=self.original,entries={wait:dict(duration_ticks=512)});result=wait_review(p,request);p.command(dict(type='set_actor_draft_waits',**request,review_key=result['review_key']));p.command(dict(type='create_npc_preset',entity_id=self.original,name='Waiting guard'));template=next(t for t in p.actor_templates.values() if t['name']=='Waiting guard');frozen=deepcopy(template)
            reset=dict(entity_id=self.original,entries={});result=wait_review(p,reset);p.command(dict(type='set_actor_draft_waits',**reset,review_key=result['review_key']));self.assertEqual(p.actor_templates[template['id']],frozen)
            value=export_file(p,template['id']);self.assertEqual(value['schema_version'],'legaia.npc-preset-file.v4');content=json.dumps(value);self.assertEqual(parse(content),value)
            with self.assertRaises(ProjectError):parse(json.dumps(dict(value,schema_version='legaia.npc-preset-file.v3')))
            target=ProjectService(p.root/'waiting-recipient');target.import_metadata(self.doc);target.disc_path=p.disc_path;before=deepcopy(target._document());report=transfer_review(target,content,'Transferred wait');self.assertEqual(target._document(),before);target.command(dict(type='import_actor_template',content=content,name='Transferred wait',review_key=report['review_key']));identifier=report['template']['id'];self.assertFalse(target.actor_drafts)
            request=dict(template_id=identifier,name='Wait instance',position=dict(x=192,z=576),expected_source_key=source_key(target));instance=review(target,request);self.assertEqual(instance['draft']['waits'],frozen['components']['NpcDraft']['waits']);target.command(dict(type='instantiate_npc_preset',**request,review_key=instance['review_key']));self.assertEqual(ProjectService.open(target.save()).actor_drafts,target.actor_drafts);target.undo();self.assertFalse(target.actor_drafts);target.redo();self.assertEqual(target.actor_drafts[instance['entity_id']],instance['draft'])
            malformed=deepcopy(value);malformed['template']['components']['NpcDraft']['waits']['entries'][wait]['duration_ticks']=True
            with self.assertRaises(ProjectError):transfer_review(target,json.dumps(malformed),'Forged wait')

if __name__=='__main__':unittest.main()
