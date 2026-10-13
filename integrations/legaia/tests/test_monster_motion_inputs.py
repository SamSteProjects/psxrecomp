import base64,json,os,tempfile,unittest
from pathlib import Path
from copy import deepcopy
from sdk.project import ProjectService,ProjectError
from sdk.project_assets import source_key
from sdk.monster_archive import resources
from sdk.monster_motion_authoring import inspect,review as numeric_review,apply as numeric_apply
from sdk.monster_motion_glb import review,apply,path
from sdk.monster_motion_inputs import download
from test_model_primitive_workflow import http_server


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN') and os.getenv('LEGAIA_MONSTER_EDITED_GLB'),'Private retail/edited fixture is required')
class MonsterMotionInputTests(unittest.TestCase):
 def test_recover_after_numeric_edit_and_history_with_source_guards(self):
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();model='asset://legaia/models/monster-archive/0063';content=Path(os.environ['LEGAIA_MONSTER_EDITED_GLB']).read_bytes()
   def fresh():return dict(expected_project_path=str(p.root),expected_source_key=source_key(p))
   catalog=resources(p,**fresh())['catalog'];clip=next(c for c in catalog['animations'] if c['model_asset_id']==model and c['entry_index']==0);ctx=dict(fresh(),asset_id=model,catalog_source_key=catalog['source_key']);observed=inspect(p,**ctx,animation_id=clip['semantic_id'],frame_index=0,part_index=0);args=dict(ctx,animation_id=clip['semantic_id'],expected_current_block_sha256=observed['current_block_sha256'],glb_base64=base64.b64encode(content).decode(),fps=24,animation_index=None,object_node_indices=None);plan=review(p,**args);apply(p,review_key=plan['review_key'],**args);self.assertEqual(len(resources(p,**fresh())['retained_motion_inputs']),1);p.undo();self.assertEqual(resources(p,**fresh())['retained_motion_inputs'],[]);p.redo()
   ctx=dict(fresh(),asset_id=model,catalog_source_key=catalog['source_key']);observed=inspect(p,**ctx,animation_id=clip['semantic_id'],frame_index=0,part_index=0);t=observed['channels']['translation'].copy();t[2]+=1;args=dict(ctx,animation_id=clip['semantic_id'],frame_index=0,part_index=0,expected_current_block_sha256=observed['current_block_sha256'],translation=t,rotation_psx=observed['channels']['rotation_psx']);plan=numeric_review(p,**args);numeric_apply(p,review_key=plan['review_key'],**args);p.save();p=ProjectService.open(p.root);report=resources(p,**fresh());row=report['retained_motion_inputs'][0];held=deepcopy((p._document(),p.undo_stack));body=dict(fresh(),animation_id=clip['semantic_id'],expected_current_motion_sha256=row['current_motion_sha256'],expected_input_sha256=row['sha256'])
   with http_server(p) as (_,post):
    status,v=post('/api/monster-motion-input-download',body);self.assertEqual(status,200,v);self.assertEqual(base64.b64decode(v['glb_base64']),content)
    for change in (dict(expected_input_sha256='0'*64),dict(expected_current_motion_sha256='0'*64),dict(expected_source_key='0'*64),dict(animation_id='animation://legaia/monster-archive/0063/entry/0001'),dict(extra='refused')):self.assertEqual(post('/api/monster-motion-input-download',dict(body,**change))[0],400)
   self.assertEqual((p._document(),p.undo_stack),held);target=path(p,row['sha256'],'glb');target.write_bytes(content[:-1])
   try:
    with self.assertRaises(ProjectError):resources(p,**fresh())
    with self.assertRaises(ProjectError):download(p,**body)
   finally:target.write_bytes(content)
   if os.getenv('LEGAIA_MONSTER_MOTION_INPUT_CASES'):Path(os.environ['LEGAIA_MONSTER_MOTION_INPUT_CASES']).write_text(json.dumps(dict(report=report,download=v,exact_original_recovery=True,numeric_composition=True,history_membership=True,save_open=True,tamper_refused=True,gameplay_verified=False)),encoding='utf-8')
