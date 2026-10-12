import base64,json,os,tempfile,unittest,zipfile
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from importer.animation_glb import _read_glb
from importer.model_glb import _write_glb
from importer.pipeline import import_scene,_disc_context
from importer.player_battle import actions,decode_part,assemble_tmd
from sdk.project import ProjectService,ProjectError
from sdk.project_assets import source_key
from sdk.player_battle import resources,playback
from sdk.player_model_authoring import export,review,apply,current,current_pose,current_export
from sdk.player_action_authoring import inspect
from sdk.player_action_store import effective
from sdk.build import build_project,_build_project
from test_model_primitive_workflow import http_server


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc is private')
class PlayerActionWorkflowTests(unittest.TestCase):
    def test_action_history_current_and_composed_model_package(self):
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.import_metadata(import_scene(p.disc_path,'town01'));p.save();report=resources(p,str(p.root),source_key(p));record=report['catalog']['models'][0];asset=record['semantic_id']
            def ctx():return dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=asset,catalog_source_key=report['catalog']['source_key'],equipped=[0]*5)
            e=export(p,**ctx());doc,binary=_read_glb(base64.b64decode(e['glb_base64']));doc['nodes'][0]['translation']=[10,0,0];encoded=base64.b64encode(_write_glb(doc,binary)).decode();r=review(p,**ctx(),binding=e['binding'],glb_base64=encoded);apply(p,**ctx(),binding=e['binding'],glb_base64=encoded,review_key=r['review_key']);model_only=deepcopy(p._document());values=[]
            with http_server(p) as (_,post):
                for slot in (0,1):
                    args=dict(ctx(),action_slot=slot);status,observed=post('/api/player-action-inspect',args);self.assertEqual(status,200,observed);first=decode_part(base64.b64decode(observed['current_action_base64'])[2:11]);edit=dict(frame_index=0,part_index=0,translation=dict(x=first['translation'][0]+5),rotation_psx=dict(y=4095));body=dict(args,expected_current_sha256=observed['current_file_sha256'],expected_action_sha256=observed['current_clip']['source_record']['sha256'],edits=[edit]);held=deepcopy((p._document(),p.undo_stack));status,proposal=post('/api/player-action-review',body);self.assertEqual(status,200,proposal);self.assertEqual((p._document(),p.undo_stack),held);self.assertEqual(proposal['layer'],'proposed')
                    status,value=post('/api/player-action-apply',dict(body,review_key='0'*64));self.assertEqual(status,400);self.assertEqual((p._document(),p.undo_stack),held);status,value=post('/api/player-action-apply',dict(body,review_key=proposal['review_key']));self.assertEqual(status,200,value);self.assertEqual(value['player_action_apply']['history_steps'],1);self.assertEqual(post('/api/player-action-apply',dict(body,review_key=proposal['review_key']))[0],400);values.append(edit)
            self.assertEqual(len(p.undo_stack),3);self.assertIn('PLAYER action channels',p.unsaved_sections);combined=deepcopy(p._document());p.undo();p.undo();self.assertEqual(p._document(),model_only);p.redo();p.redo();self.assertEqual(p._document(),combined);p.save();p=ProjectService.open(p.root);self.assertFalse(p.dirty)
            raw=current(p,**ctx());poses=[]
            for slot,edit in enumerate(values):
                posed=current_pose(p,**ctx(),expected_current_sha256=raw['effective_file_sha256'],action_slot=slot,frame_index=0);self.assertEqual(posed['object_transforms'][0]['translation'][0],edit['translation']['x']);self.assertEqual(posed['object_transforms'][0]['rotation_psx'][1],4095);self.assertNotEqual(posed['current_action_clip']['source_record']['sha256'],record['actions'][slot]['source_record']['sha256']);poses.append(posed)
            stream=playback(p,**ctx(),layer='current',expected_current_sha256=raw['effective_file_sha256'],action_slot=0);self.assertEqual(decode_part(base64.b64decode(stream['action_base64'])[2:11])['rotation_psx'][1],4095)
            exported=current_export(p,**ctx(),expected_current_sha256=raw['effective_file_sha256'],mode='clip',action_slot=0,frame_index=None,fps=30);self.assertEqual(exported['audit']['animation']['source_record'],raw['action_clips'][0]['source_record'])
            held=deepcopy((p._document(),p.undo_stack));preview=_build_project(p,None,review_only=True);built=build_project(p);audit=json.loads(Path(built['audit']).read_text(encoding='utf-8'));self.assertEqual(built['overlay_count'],1);self.assertEqual({r['scope'] for r in audit['edits']},{'PLAYER-native-model-pools-only','PLAYER-action-channel-content-only'});self.assertEqual(preview['audit_sha256'],sha256(Path(built['audit']).read_bytes()).hexdigest());self.assertEqual((p._document(),p.undo_stack),held)
            with zipfile.ZipFile(built['path']) as package,_disc_context(p.disc_path) as (image,digest,_,archive):
                overlay=audit['overlays'][0];payload=package.read(overlay['file']);retail=image.read_user(0,overlay['offset'],overlay['size'],image.size//2352*2048);action_file,replays=effective(p,record,retail);_,expected_bank=actions(action_file,0,digest);_,actual_bank=actions(payload,0,digest);self.assertEqual(actual_bank,expected_bank);self.assertEqual(assemble_tmd(payload,[0]*5)[2],base64.b64decode(raw['tmd_base64']));self.assertEqual(payload[:16],retail[:16]);self.assertEqual((Path(built['package_directory'])/overlay['file']).read_bytes(),payload)
            # Restore selected actions after Open, preserving other actions/models.
            restored_proposals=[]
            with http_server(p) as (_,post):
                for slot in (0,1):
                    observed=inspect(p,**ctx(),action_slot=slot);body=dict(ctx(),action_slot=slot,expected_current_sha256=observed['current_file_sha256'],expected_action_sha256=observed['current_clip']['source_record']['sha256']);held=deepcopy((p._document(),p.undo_stack));status,restore=post('/api/player-action-restore-review',body);self.assertEqual(status,200,restore);self.assertEqual((p._document(),p.undo_stack),held);self.assertEqual(restore['proposed_action_base64'],observed['original_action_base64']);self.assertEqual(restore['operation'],'restore_retail_action')
                    self.assertEqual(post('/api/player-action-restore-apply',dict(body,review_key='0'*64))[0],400);self.assertEqual((p._document(),p.undo_stack),held);status,result=post('/api/player-action-restore-apply',dict(body,review_key=restore['review_key']));self.assertEqual(status,200,result);restored_proposals.append(dict(inspection=observed,review=restore,report=dict(report,project_source_key=body['expected_source_key'])))
                    if slot==0:self.assertEqual(set(p.player_action_overrides[asset]['actions']),{'0001'})
            self.assertEqual(p._document(),model_only);self.assertEqual(len(p.undo_stack),2);p.save();reverted=build_project(p);reverted_audit=json.loads(Path(reverted['audit']).read_text(encoding='utf-8'));self.assertEqual({r['scope'] for r in reverted_audit['edits']},{'PLAYER-native-model-pools-only'})
            with zipfile.ZipFile(reverted['path']) as package:self.assertEqual(sha256(package.read(reverted_audit['overlays'][0]['file'])).hexdigest(),p.player_model_overrides[asset]['current_sha256'])
            p.undo();p.undo();self.assertEqual(p._document(),combined);p.redo();p.redo();self.assertEqual(p._document(),model_only);p.save();p=ProjectService.open(p.root);self.assertFalse(p.player_action_overrides)
            p.player_action_overrides=deepcopy(combined['player_action_overrides']);p.save()
            # Source cache integrity gates Open, not only a later Build.
            source=p.root/'Authored'/'PLAYER'/'ActionSources'/(record['source_record']['sha256']+'.bin');original=source.read_bytes();source.write_bytes(original[:-1]+bytes([original[-1]^1]))
            with self.assertRaises(ProjectError):ProjectService.open(p.root)
            out=os.getenv('LEGAIA_PLAYER_ACTION_WORKFLOW_PROOF')
            if out:Path(out).write_text(json.dumps(dict(report=dict(report,project_source_key=raw['project_source_key']),raw=raw,poses=poses,playback=stream,exported=exported,package_sha256=built['sha256'],undo_redo=True,save_open=True,stale_apply_refused=True,source_tamper_refused=True,composed_model_action_readback=True,restoration_preserves_other_owners=True,restore_reviews=restored_proposals,restored_build_model_only=True,gameplay_verified=False)),encoding='utf-8')
