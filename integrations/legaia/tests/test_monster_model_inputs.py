import base64,json,os,tempfile,unittest
from pathlib import Path
from copy import deepcopy
from sdk.project import ProjectService,ProjectError
from sdk.project_assets import source_key
from sdk.monster_archive import resources
from sdk.monster_model_authoring import export,review,apply
from sdk.monster_models import path
from sdk.monster_model_inputs import download
from test_monster_model_authoring import shifted_glb
from test_model_primitive_workflow import http_server


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
class MonsterModelInputTests(unittest.TestCase):
 def test_saved_multi_import_recovery_history_and_refusals(self):
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();model='asset://legaia/models/monster-archive/0063'
   def fresh():return dict(expected_project_path=str(p.root),expected_source_key=source_key(p))
   catalog=resources(p,**fresh())['catalog'];originals=[]
   for _ in range(2):
    ctx=dict(fresh(),asset_id=model,catalog_source_key=catalog['source_key']);e=export(p,**ctx);content=shifted_glb(base64.b64decode(e['glb_base64']));originals.append(content);args=dict(ctx,binding=e['binding'],glb_base64=base64.b64encode(content).decode());plan=review(p,**args);apply(p,review_key=plan['review_key'],**args)
   library=resources(p,**fresh());self.assertEqual(len(library['retained_model_inputs']),2);p.undo();self.assertEqual(len(resources(p,**fresh())['retained_model_inputs']),1);p.redo();p.save();p=ProjectService.open(p.root);library=resources(p,**fresh());held=deepcopy((p._document(),p.undo_stack));downloads=[]
   with http_server(p) as (_,post):
    for index,row in enumerate(library['retained_model_inputs']):
     args=dict(fresh(),asset_id=model,expected_current_tmd_sha256=row['current_tmd_sha256'],import_index=index,expected_input_sha256=row['sha256']);status,v=post('/api/monster-model-input-download',args);self.assertEqual(status,200,v);self.assertEqual(base64.b64decode(v['glb_base64']),originals[index]);downloads.append(v)
    for change in (dict(import_index=-1),dict(import_index=True),dict(import_index=2),dict(expected_input_sha256='0'*64),dict(expected_current_tmd_sha256='0'*64),dict(expected_source_key='0'*64),dict(asset_id='asset://legaia/models/monster-archive/0062'),dict(extra='refused')):self.assertEqual(post('/api/monster-model-input-download',dict(args,**change))[0],400)
   self.assertEqual((p._document(),p.undo_stack),held)
   receipt=p.monster_model_overrides[model]['inputs'][1];target=path(p,receipt['glb_sha256'],'glb');target.write_bytes(originals[1][:-1])
   try:
    with self.assertRaises(ProjectError):resources(p,**fresh())
    with self.assertRaises(ProjectError):download(p,**args)
   finally:target.write_bytes(originals[1])
   if os.getenv('LEGAIA_MONSTER_MODEL_INPUT_CASES'):Path(os.environ['LEGAIA_MONSTER_MODEL_INPUT_CASES']).write_text(json.dumps(dict(report=library,downloads=downloads,save_open=True,history_membership=True,exact_originals=True,tamper_refused=True,gameplay_verified=False)),encoding='utf-8')
