import base64,json,os,tempfile,unittest
from copy import deepcopy
from pathlib import Path
from sdk.project import ProjectService
from sdk.project_assets import source_key
from sdk.player_battle import resources
from sdk.player_action_authoring import inspect
from importer.player_battle import decode_part
from test_model_primitive_workflow import http_server


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc is private')
class PlayerActionRangeTests(unittest.TestCase):
    def test_range_offset_set_bounds_and_one_history_step(self):
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();report=resources(p,str(p.root),source_key(p));record=report['catalog']['models'][0];cases=[]
            def ctx():return dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=record['semantic_id'],catalog_source_key=report['catalog']['source_key'],equipped=[0]*5,action_slot=0)
            with http_server(p) as (_,post):
                for mode,field,value in [('offset','translation',5),('set','rotation_psx',4095)]:
                    observed=inspect(p,**ctx());spec=dict(frame_start=1,frame_end=3,part_index=0,field=field,axis='x',mode=mode,value=value);args=dict(ctx(),expected_current_sha256=observed['current_file_sha256'],expected_action_sha256=observed['current_clip']['source_record']['sha256'],range_spec=spec);before=deepcopy((p._document(),p.undo_stack));status,r=post('/api/player-action-range-review',args);self.assertEqual(status,200,r);self.assertEqual((p._document(),p.undo_stack),before);self.assertEqual(r['operation'],'native_channel_range');old=base64.b64decode(observed['current_action_base64']);new=base64.b64decode(r['proposed_action_base64']);parts=record['actions'][0]['part_count'];allowed=set()
                    for frame in range(1,4):
                        at=2+frame*parts*9;expected=decode_part(old[at:at+9])[field][0]+value if mode=='offset' else value;self.assertEqual(decode_part(new[at:at+9])[field][0],expected);allowed.update(range(at,at+9))
                    self.assertTrue(all(a==b or i in allowed for i,(a,b) in enumerate(zip(old,new))));cases.append(dict(report=dict(report,project_source_key=args['expected_source_key']),inspection=observed,review=r,spec=spec));self.assertEqual(post('/api/player-action-range-apply',dict(args,review_key='0'*64))[0],400);self.assertEqual((p._document(),p.undo_stack),before);status,result=post('/api/player-action-range-apply',dict(args,review_key=r['review_key']));self.assertEqual(status,200,result);self.assertEqual(len(p.undo_stack),len(before[1])+1)
                observed=inspect(p,**ctx());args=dict(ctx(),expected_current_sha256=observed['current_file_sha256'],expected_action_sha256=observed['current_clip']['source_record']['sha256'],range_spec=spec);held=deepcopy((p._document(),p.undo_stack))
                for mutation in (dict(frame_start=True),dict(frame_end=999),dict(part_index=-1),dict(field='unknown'),dict(axis='q'),dict(mode='wrap'),dict(value=.5),dict(value=True),dict(mode='offset',value=1)):
                    self.assertEqual(post('/api/player-action-range-review',dict(args,range_spec=dict(spec,**mutation)))[0],400)
                self.assertEqual((p._document(),p.undo_stack),held)
            after=deepcopy(p._document());p.undo();p.undo();self.assertFalse(p.player_action_overrides);p.redo();p.redo();self.assertEqual(p._document(),after);p.save();p=ProjectService.open(p.root);self.assertEqual(p._document(),after);self.assertFalse(p.dirty)
            out=os.getenv('LEGAIA_PLAYER_ACTION_RANGE_CASES')
            if out:Path(out).write_text(json.dumps(cases),encoding='utf-8')
