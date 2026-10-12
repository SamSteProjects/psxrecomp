import base64,json,os,unittest
from copy import deepcopy
from pathlib import Path
from sdk.project import ProjectService
from sdk.project_assets import source_key
from sdk.player_battle import resources
from test_model_primitive_workflow import http_server

@unittest.skipUnless(os.getenv('LEGAIA_PLAYER_RETAINED_PROJECT'),'Private retained motion fixture')
class PlayerMotionInputTests(unittest.TestCase):
 def test_registration_and_download(self):
  p=ProjectService.open(Path(os.environ['LEGAIA_PLAYER_RETAINED_PROJECT']));before=deepcopy((p._document(),p.undo_stack));report=resources(p,str(p.root),source_key(p));self.assertEqual(len(report['retained_motion_inputs']),1);r=report['retained_motion_inputs'][0];self.assertEqual(r['references'],[r['model_asset_id'],r['action_asset_id']]);args=dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=r['semantic_id'])
  with http_server(p) as (_,post):
   status,receipt=post('/api/player-motion-input-export',args);self.assertEqual(status,200,receipt);self.assertEqual(receipt['record'],r);self.assertEqual(base64.b64decode(receipt['glb_base64']),(p.root/'Authored'/'PLAYER'/'ActionInputs'/(r['source_record']['glb_sha256']+'.glb')).read_bytes());self.assertEqual(post('/api/player-motion-input-export',dict(args,expected_source_key='0'*64))[0],400);self.assertEqual(post('/api/player-motion-input-export',dict(args,asset_id=r['model_asset_id']))[0],400)
  self.assertEqual((p._document(),p.undo_stack),before)
  if os.getenv('LEGAIA_PLAYER_MOTION_INPUT_CASES'):Path(os.environ['LEGAIA_PLAYER_MOTION_INPUT_CASES']).write_text(json.dumps(dict(report=report,receipt=receipt,unchanged=True,stale_refused=True,wrong_asset_refused=True,gameplay_verified=False)),encoding='utf-8')
