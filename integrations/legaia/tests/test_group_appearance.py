"""Reviewed group appearance uses a shared verified initial donor pair."""
from copy import deepcopy
from contextlib import nullcontext
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from sdk.project import ProjectService, ProjectError
from test_project_appearance import appearance_scene

class GroupAppearanceTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.doc=appearance_scene()
        for n,actor in enumerate(self.doc['actors'],1):actor['source_record']['record_index']=n
        self.ids=[a['semantic_id'] for a in self.doc['actors']]
        self.p=ProjectService(Path(self.directory.name));self.p.import_metadata(self.doc);self.p.disc_path='fixture'
        class Context:
            def options(_,index):return {'supported':True,'reason':None,'pairs':[{'donor_records':[2]}]}
            def provenance(_):return {'source':'fixture'}
        for mocked in [patch('importer.man_assignments.load_man_assignment_context',return_value=Context()),patch('importer.pipeline._disc_context',return_value=nullcontext()),patch('importer.pipeline.import_scene',side_effect=lambda *a:deepcopy(self.doc))]:
            mocked.start();self.addCleanup(mocked.stop)

    def command(self):
        r=self.p.actor_appearance_batch(self.ids,self.ids[1]);return dict(type='set_actor_group_appearance',scene_id=self.p.active_scene,actor_ids=self.ids.copy(),donor_entity_id=self.ids[1],review_key=r['review_key'])

    def test_preview_atomic_history_source_and_unrelated_preservation(self):
        p=self.p;p.overrides[self.ids[0]]={'Transform':{'position':{'x':150}}};before=deepcopy(p.overrides);source=deepcopy(p.imports)
        report=p.actor_appearance_batch(self.ids);self.assertEqual(len(report['options']),1);self.assertEqual(p.overrides,before)
        p.command(self.command());self.assertEqual(len(p.undo_stack),1);self.assertEqual(p.overrides[self.ids[0]]['Transform'],before[self.ids[0]]['Transform'])
        for id in self.ids:self.assertEqual(p.overrides[id]['ActorAppearance'],{'donor_entity_id':self.ids[1]})
        p.undo();self.assertEqual(p.overrides,before);p.redo();self.assertEqual(p.imports,source)
        p.command(self.command());self.assertEqual(len(p.undo_stack),1)

    def test_scene_projection_is_detached_and_rejects_stale_or_discovery_report(self):
        from sdk.scene_preview import actor_appearance_proposal_view
        p=self.p;p.overrides[self.ids[0]]={'Transform':{'position':{'x':150}}}
        before=deepcopy(p.overrides);source=deepcopy(p.imports)
        report=p.actor_appearance_batch(self.ids,self.ids[1]);view=actor_appearance_proposal_view(p,report)
        self.assertEqual(view.overrides[self.ids[0]]['Transform'],before[self.ids[0]]['Transform'])
        for identifier in self.ids:self.assertEqual(view.overrides[identifier]['ActorAppearance'],{'donor_entity_id':self.ids[1]})
        view.overrides[self.ids[0]]['Transform']['position']['x']=200
        self.assertEqual(p.overrides,before);self.assertEqual(p.imports,source);self.assertFalse(p.undo_stack)
        with self.assertRaises(ProjectError):actor_appearance_proposal_view(p,p.actor_appearance_batch(self.ids))
        p.overrides[self.ids[1]]={'ActorAppearance':{'donor_entity_id':self.ids[0]}}
        with self.assertRaises(ProjectError):actor_appearance_proposal_view(p,report)

    def test_last_member_stale_rejects_whole_group_and_replay(self):
        p=self.p;cmd=self.command();p.overrides[self.ids[1]]={'ActorAppearance':{'donor_entity_id':self.ids[0]}};before=deepcopy(p.overrides)
        with self.assertRaises(ProjectError):p.command(cmd)
        self.assertEqual(p.overrides,before);self.assertFalse(p.undo_stack)
        p.overrides.clear();cmd=self.command();p.command(cmd);before=deepcopy(p.overrides)
        with self.assertRaises(ProjectError):p.command(cmd)
        self.assertEqual(p.overrides,before);self.assertEqual(len(p.undo_stack),1)

    def test_no_common_pair_or_last_actor_incompatible_fails_before_mutation(self):
        p=self.p;asset=p.assets.records[self.doc['actors'][1]['model_reference']['asset_semantic_id']];asset['source_record']['object_count']=11
        self.assertEqual(p.actor_appearance_batch(self.ids)['options'],[])
        with self.assertRaises(ProjectError):p.actor_appearance_batch(self.ids,self.ids[1])
        self.assertFalse(p.overrides);self.assertFalse(p.undo_stack)

    def test_malformed_and_live_commands_reject(self):
        p=self.p
        for changes in [{'review_key':'old'},{'actor_ids':[self.ids[0],self.ids[0]]},{'donor_entity_id':None},{'bytes':'00'}]:
            cmd={**self.command(),**changes}
            with self.assertRaises(ProjectError):p.command(cmd)
            self.assertFalse(p.overrides)
        cmd=self.command();p.mode='live'
        with self.assertRaises(ProjectError):p.command(cmd)

    def test_http_preview_and_command_reject_unknown_fields_atomically(self):
        import json,threading
        from urllib.error import HTTPError
        from urllib.request import Request,urlopen
        from sdk.server import EditorServer
        p=self.p;server=EditorServer(('127.0.0.1',0),p);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        def post(route,body):
            with urlopen(Request(f'http://127.0.0.1:{server.server_port}'+route,data=json.dumps(body).encode(),headers={'Content-Type':'application/json'}),timeout=30) as response:return json.load(response)
        try:
            report=post('/api/actor-appearance-batch',{'actor_ids':self.ids,'donor_entity_id':None});self.assertEqual(len(report['options']),1)
            for route,body in [('/api/actor-appearance-batch',{'actor_ids':self.ids,'donor_entity_id':None,'path':'other'}),('/api/actor-appearance-batch-scene',{'actor_ids':self.ids,'donor_entity_id':self.ids[1],'review_key':'stale'}),('/api/actor-appearance-batch-scene',{'actor_ids':self.ids,'donor_entity_id':None,'review_key':report['review_key']}),('/api/actor-appearance-batch-scene',{'actor_ids':self.ids,'donor_entity_id':self.ids[1],'review_key':report['review_key'],'path':'other'}),('/api/command',{**self.command(),'bytes':'00'}),('/api/command',{**self.command(),'review_key':None})]:
                with self.assertRaises(HTTPError) as error:post(route,body)
                self.assertEqual(error.exception.code,400);error.exception.close();self.assertFalse(p.overrides)
            post('/api/command',self.command());self.assertEqual(len(p.undo_stack),1);post('/api/undo',{});self.assertFalse(p.overrides)
        finally:server.shutdown();server.server_close();thread.join(timeout=5)
        self.assertFalse(thread.is_alive())

class RetailGroupAppearanceTests(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'user-owned disc required')
    def test_verified_retail_preview_history_persistence_and_source(self):
        from importer.pipeline import import_scene
        disc=os.environ['LEGAIA_DISC_BIN']
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.disc_path=disc;p.import_metadata(import_scene(disc,'town01'))
            ids=[f'scene://town01/actors/man-p1/{n:04}' for n in (11,12)];source=deepcopy(p.imports)
            options=p.actor_appearance_batch(ids)['options'];self.assertTrue(options);donor=options[0]['donor_entity_id'];r=p.actor_appearance_batch(ids,donor)
            p.command(dict(type='set_actor_group_appearance',scene_id=p.active_scene,actor_ids=ids,donor_entity_id=donor,review_key=r['review_key']))
            saved=ProjectService.open(p.save());self.assertEqual(saved.overrides,p.overrides);self.assertEqual(p.imports,source)
            p.undo();self.assertFalse(p.overrides);p.redo();self.assertEqual(p.overrides,saved.overrides)
            bad=p.actor_appearance_batch([f'scene://town01/actors/man-p1/{n:04}' for n in (1,2)])
            self.assertFalse(bad['options']);self.assertTrue(all(not row['supported'] for row in bad['support']))

if __name__=='__main__':unittest.main()
