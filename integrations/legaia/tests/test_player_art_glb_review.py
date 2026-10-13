import base64
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from importer.me_archive import entries
from importer.player_art_authoring import owner
from importer.player_battle import decode_part
from sdk.project import ProjectService, ProjectError
from sdk.project_assets import source_key
from sdk.player_art_store import context, composed_slots
from sdk.player_art_glb import apply as import_apply
from sdk.player_art_animation import export as original_export
from test_model_primitive_workflow import http_server
from test_player_art_workflow import check_literal_pose


@unittest.skipUnless(os.getenv('PLAYER_ART_CURRENT_EXPORT_CASES') and os.getenv('LEGAIA_DISC_BIN'),
                     'Private qualified exports and source disc required')
class ArtGlbReviewTests(unittest.TestCase):
    def test_http_preview_apply_freshness_rollback_and_retail_restoration(self):
        cases=json.loads(Path(os.environ['PLAYER_ART_CURRENT_EXPORT_CASES']).read_text(encoding='utf-8'))['cases']
        case=next(c for c in cases if c['selection']['mode']=='clip' and c['selection']['layer']=='retail')
        base=case['inspection']['base_playback'];stream=base['stream']
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save()
            raw,catalog,_=context(p);at=stream['source_record']['slot_offset'];original=raw[at:at+0x10800]
            neighbor=next(s for s in catalog['streams'] if s['archive_asset_id']==stream['archive_asset_id'] and s['semantic_id']!=stream['semantic_id'])
            channels=decode_part(entries(original)[neighbor['stream_index']]['decoded'][2:11]);channels['translation'][0]^=1
            neighbor_owner=owner(original,catalog,stream['archive_asset_id'],neighbor['semantic_id'],[dict(frame_index=0,part_index=0,**channels)])
            p.player_art_overrides={neighbor['semantic_id']:neighbor_owner};p.save()
            source=dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=stream['model_asset_id'],
                catalog_source_key=base['catalog_source_key'],equipped=base['base_inspection']['assembly']['equipped'],
                art_source_key=catalog['source_key'],stream_id=stream['semantic_id'],art_record_id=None,layer='retail',expected_current_sha256=None)
            held=deepcopy((p._document(),p.undo_stack,p.redo_stack))
            with http_server(p) as (_,post):
                status,inspection=post('/api/player-art-frame-inspect',dict(source,frame_index=0,part_index=0));self.assertEqual(status,200,inspection)
                args=dict(source,frame_index=0,part_index=0,expected_current_slot_sha256=inspection['current_slot_sha256'],
                    glb_base64=case['export']['glb_base64'],fps=23.5,animation_index=None,object_node_indices=None)
                status,value=post('/api/player-art-glb-review',args);self.assertEqual(status,200,value)
                self.assertEqual(value['retained_input']['baseline_owners'],p.player_art_overrides)
                self.assertTrue(value['projection']['retail_relative_part_frames'])
                status,pose=post('/api/player-art-glb-pose',dict(args,review_key=value['review_key']));self.assertEqual(status,200,pose)
                for name,decoded in [('current_pose',inspection['current_decoded_base64']),('proposed_pose',value['candidate_decoded_base64'])]:
                    check_literal_pose(self,inspection['base_playback']['base_inspection'],stream,base64.b64decode(decoded),0,pose[name]['geometry'],pose[name]['object_transforms'])
                self.assertEqual((p._document(),p.undo_stack,p.redo_stack),held)
                self.assertFalse((p.root/'Authored').exists())
                for changed in [dict(args,extra=True),dict(args,expected_current_slot_sha256='0'*64),dict(args,glb_base64='%%%'),dict(args,fps=True)]:
                    status,error=post('/api/player-art-glb-review',changed);self.assertEqual(status,400,error)
                status,error=post('/api/player-art-glb-apply',dict(args,review_key='0'*64));self.assertEqual(status,400,error)
                status,error=post('/api/player-art-glb-apply',dict(args,part_index=1,review_key=value['review_key']));self.assertEqual(status,400,error)
                self.assertFalse((p.root/'Authored').exists());self.assertEqual((p._document(),p.undo_stack,p.redo_stack),held)
                # A failure after retention must roll back this attempt's files.
                with patch('sdk.player_art_store.validate',side_effect=ProjectError('simulated publication refusal')):
                    with self.assertRaises(ProjectError):import_apply(p,review_key=value['review_key'],**args)
                self.assertFalse(list((p.root/'Authored').rglob('*.glb')));self.assertFalse(list((p.root/'Authored').rglob('*.bin')))
                self.assertEqual((p._document(),p.undo_stack,p.redo_stack),held)
                status,result=post('/api/player-art-glb-apply',dict(args,review_key=value['review_key']));self.assertEqual(status,200,result)
                self.assertEqual(result['player_art_apply']['history_steps'],1);self.assertEqual(len(p.undo_stack),1)
                self.assertEqual(p.player_art_overrides[neighbor['semantic_id']],neighbor_owner)
                self.assertEqual(composed_slots(raw,catalog,p.player_art_overrides,project=p)[stream['archive_asset_id']],base64.b64decode(value['candidate_slot_base64']))
                status,error=post('/api/player-art-glb-apply',dict(args,review_key=value['review_key']));self.assertEqual(status,400,error)
                source['expected_source_key']=source_key(p)
                status,now=post('/api/player-art-frame-inspect',dict(source,frame_index=0,part_index=0));self.assertEqual(status,200,now)
                status,error=post('/api/player-art-glb-review',dict(args,expected_source_key=source_key(p),expected_current_slot_sha256=now['current_slot_sha256']));self.assertEqual(status,400,error)
            p.save();p=ProjectService.open(p.root);self.assertIn('glb_import',p.player_art_overrides[stream['semantic_id']])
            source['expected_source_key']=source_key(p)
            original_clip=original_export(p,mode='clip',frame_index=None,fps=23.5,**source)
            retained=sorted(str(path.relative_to(p.root)) for path in (p.root/'Authored').rglob('*') if path.is_file())
            with http_server(p) as (_,post):
                status,now=post('/api/player-art-frame-inspect',dict(source,frame_index=0,part_index=0));self.assertEqual(status,200,now)
                restore_args=dict(args,expected_source_key=source_key(p),expected_current_slot_sha256=now['current_slot_sha256'],glb_base64=original_clip['glb_base64'])
                status,restoration=post('/api/player-art-glb-review',restore_args);self.assertEqual(status,200,restoration)
                self.assertIsNone(restoration['ownership_after']);self.assertEqual(restoration['projection']['retail_relative_part_frames'],0)
                self.assertGreater(restoration['projection']['canonicalized_body_bytes'],0)
                status,result=post('/api/player-art-glb-apply',dict(restore_args,review_key=restoration['review_key']));self.assertEqual(status,200,result)
                self.assertIsNone(result['player_art_apply']['retained_input'])
            self.assertEqual(p.player_art_overrides,{neighbor['semantic_id']:neighbor_owner})
            self.assertEqual(sorted(str(path.relative_to(p.root)) for path in (p.root/'Authored').rglob('*') if path.is_file()),retained)
            p.undo();self.assertIn('glb_import',p.player_art_overrides[stream['semantic_id']]);p.redo();self.assertNotIn(stream['semantic_id'],p.player_art_overrides)
            print('Art GLB HTTP Review/Proposed/Apply: literal poses, no preview writes, stale/no-op/input refusals, post-retention rollback, one-step history/Open and neighbor-preserving import restoration passed',flush=True)


if __name__=='__main__':unittest.main()
