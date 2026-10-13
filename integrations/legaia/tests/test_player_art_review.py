import base64
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
import unittest
from importer.me_archive import entries
from sdk.project import ProjectService
from sdk.project_assets import source_key
from sdk.player_battle import resources as models
from sdk.player_art_animation import resources
from test_model_primitive_workflow import http_server
from test_player_art_workflow import check_literal_pose


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Private retail disc required')
class PlayerArtReviewTests(unittest.TestCase):
    def test_proposed_motion_uses_saved_authored_current_geometry(self):
        from sdk.player_model_authoring import export as model_export,review as model_review,apply as model_apply,current
        from importer.animation_glb import _read_glb
        from importer.model_glb import _write_glb
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();mr=models(p,str(p.root),source_key(p));model=mr['catalog']['models'][0]
            context=dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=model['semantic_id'],catalog_source_key=mr['catalog']['source_key'],equipped=[0]*5)
            exported=model_export(p,**context);doc,binary=_read_glb(base64.b64decode(exported['glb_base64']));doc['nodes'][0]['translation']=[10,0,0];payload=base64.b64encode(_write_glb(doc,binary)).decode();v=model_review(p,**context,binding=exported['binding'],glb_base64=payload);model_apply(p,**context,binding=exported['binding'],glb_base64=payload,review_key=v['review_key']);p.save();p=ProjectService.open(p.root);context['expected_source_key']=source_key(p)
            saved=current(p,**context);ar=resources(p,str(p.root),source_key(p));stream=next(s for s in ar['catalog']['streams'] if s['player_index']==0 and s['archive_role']=='base');context.update(art_source_key=ar['catalog']['source_key'],stream_id=stream['semantic_id'],art_record_id=None,layer='current',expected_current_sha256=saved['effective_file_sha256'],frame_index=0,part_index=0);held=deepcopy((p._document(),p.undo_stack,p.redo_stack))
            with http_server(p) as (_,post):
                status,inspection=post('/api/player-art-frame-inspect',context);self.assertEqual(status,200,inspection);self.assertEqual(inspection['base_playback']['base_inspection']['geometry']['vertices'],saved['geometry']['vertices']);channels=deepcopy(inspection['channels']);channels['translation'][0]^=1;args=dict(context,expected_current_slot_sha256=inspection['current_slot_sha256'],**channels)
                status,review=post('/api/player-art-frame-review',args);self.assertEqual(status,200,review);status,pose=post('/api/player-art-frame-pose',dict(args,review_key=review['review_key']));self.assertEqual(status,200,pose)
                check_literal_pose(self,inspection['base_playback']['base_inspection'],stream,base64.b64decode(review['candidate_decoded_base64']),0,pose['proposed_pose']['geometry'],pose['proposed_pose']['object_transforms']);self.assertEqual(pose['geometry_layer'],'current');self.assertEqual((p._document(),p.undo_stack,p.redo_stack),held)

    def test_fresh_http_review_pose_apply_restore_and_neighbor_history(self):
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save()
            mr=models(p,str(p.root),source_key(p));ar=resources(p,str(p.root),source_key(p));model=mr['catalog']['models'][0]
            streams=[s for s in ar['catalog']['streams'] if s['player_index']==0 and s['archive_role']=='main'][:2]
            def ctx(stream):return dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=model['semantic_id'],catalog_source_key=mr['catalog']['source_key'],equipped=[0]*5,art_source_key=ar['catalog']['source_key'],stream_id=stream['semantic_id'],art_record_id=None,layer='retail',expected_current_sha256=None,frame_index=0,part_index=0)
            held=deepcopy((p._document(),p.undo_stack,p.redo_stack));cases=[]
            with http_server(p) as (_,post):
                for stream in streams:
                    context=ctx(stream);status,inspection=post('/api/player-art-frame-inspect',context);self.assertEqual(status,200,inspection)
                    channels=deepcopy(inspection['channels']);channels['translation'][0]^=1
                    args=dict(context,expected_current_slot_sha256=inspection['current_slot_sha256'],**channels)
                    status,value=post('/api/player-art-frame-review',args);self.assertEqual(status,200,value)
                    status,pose=post('/api/player-art-frame-pose',dict(args,review_key=value['review_key']));self.assertEqual(status,200,pose)
                    self.assertEqual((p._document(),p.undo_stack,p.redo_stack),held)
                    for layer,decoded in [('current',inspection['current_decoded_base64']),('proposed',value['candidate_decoded_base64'])]:
                        check_literal_pose(self,inspection['base_playback']['base_inspection'],stream,base64.b64decode(decoded),0,pose[layer+'_pose']['geometry'],pose[layer+'_pose']['object_transforms'])
                    original=base64.b64decode(inspection['base_playback']['source_slot_base64']);candidate=base64.b64decode(value['candidate_slot_base64']);source=stream['source_record'];at=source['byte_offset']-source['slot_offset'];end=at+source['byte_length'];current=base64.b64decode(inspection['current_slot_base64'])
                    self.assertEqual(candidate[:at],current[:at]);self.assertEqual(candidate[end:],current[end:])
                    before=deepcopy(p._document());history=len(p.undo_stack)
                    for change in [dict(review_key='stale'),dict(expected_current_slot_sha256='stale'),dict(translation=[True,0,0]),dict(part_index=True),dict(extra=True)]:
                        self.assertEqual(post('/api/player-art-frame-apply',{**args,'review_key':value['review_key'],**change})[0],400);self.assertEqual((p._document(),p.undo_stack,p.redo_stack),held)
                    status,result=post('/api/player-art-frame-apply',dict(args,review_key=value['review_key']));self.assertEqual(status,200,result);self.assertEqual(result['player_art_apply']['history_steps'],1);self.assertEqual(len(p.undo_stack),history+1)
                    after=deepcopy(p._document());p.undo();self.assertEqual(p._document(),before);p.redo();self.assertEqual(p._document(),after)
                    self.assertEqual(post('/api/player-art-frame-apply',dict(args,review_key=value['review_key']))[0],400)
                    held=deepcopy((p._document(),p.undo_stack,p.redo_stack));cases.append(dict(inspection=inspection,review=value,pose=pose))
                other=deepcopy(p.player_art_overrides[streams[1]['semantic_id']]);context=ctx(streams[0]);status,inspection=post('/api/player-art-frame-inspect',context);self.assertEqual(status,200)
                retail=entries(base64.b64decode(inspection['base_playback']['source_slot_base64']))[0]['decoded'];from importer.player_battle import decode_part
                args=dict(context,expected_current_slot_sha256=inspection['current_slot_sha256'],**decode_part(retail[2:11]));status,value=post('/api/player-art-frame-review',args);self.assertEqual(status,200,value);self.assertIsNone(value['ownership_after'])
                status,_=post('/api/player-art-frame-apply',dict(args,review_key=value['review_key']));self.assertEqual(status,200);self.assertNotIn(streams[0]['semantic_id'],p.player_art_overrides);self.assertEqual(p.player_art_overrides[streams[1]['semantic_id']],other)
                held=deepcopy((p._document(),p.undo_stack,p.redo_stack));p.mode='observe'
                self.assertEqual(post('/api/player-art-frame-inspect',ctx(streams[0]))[0],400);p.mode='edit';self.assertEqual((p._document(),p.undo_stack,p.redo_stack),held)
            document=deepcopy(p._document());p.save();p=ProjectService.open(p.root);self.assertEqual(p._document(),document)
            out=os.getenv('PLAYER_ART_REVIEW_CASES')
            if out:Path(out).write_text(json.dumps(dict(cases=cases,whole_neighbor_bytes=True,history=True,retail_restoration=True,other_owner_preserved=True,save_open=True,gameplay_verified=False)),encoding='utf-8')


if __name__=='__main__':unittest.main()
