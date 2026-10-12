import base64,json,os,tempfile,unittest,struct,zipfile
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from importer.pipeline import import_scene,_disc_context
from importer.animation_glb import _read_glb
from importer.model_glb import _write_glb
from importer.player_battle import actions,decode_part
from sdk.project import ProjectService,ProjectError
from sdk.project_assets import source_key
from sdk.player_battle import resources
from sdk.player_model_authoring import current,current_export,current_pose
from sdk.player_action_authoring import inspect,review as numeric_review,apply as numeric_apply
from sdk.build import build_project
from test_model_primitive_workflow import http_server

@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc is private')
class PlayerActionGLBWorkflowTests(unittest.TestCase):
    def test_review_retention_history_current_and_package(self):
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.import_metadata(import_scene(p.disc_path,'town01'));p.save();report=resources(p,str(p.root),source_key(p));record=report['catalog']['models'][0];asset=record['semantic_id']
            def ctx():return dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=asset,catalog_source_key=report['catalog']['source_key'],equipped=[0]*5)
            raw=current(p,**ctx());exported=current_export(p,**ctx(),expected_current_sha256=raw['effective_file_sha256'],mode='clip',action_slot=0,frame_index=None,fps=17.5);doc,binary=_read_glb(base64.b64decode(exported['glb_base64']));binary=bytearray(binary);sampler=doc['animations'][0]['samplers'][0];accessor=doc['accessors'][sampler['output']];view=doc['bufferViews'][accessor['bufferView']];at=view['byteOffset'];x=struct.unpack_from('<f',binary,at)[0];struct.pack_into('<f',binary,at,x+7);content=_write_glb(doc,bytes(binary));observed=inspect(p,**ctx(),action_slot=0)
            args=dict(ctx(),action_slot=0,expected_current_sha256=observed['current_file_sha256'],expected_action_sha256=observed['current_clip']['source_record']['sha256'],glb_base64=base64.b64encode(content).decode(),fps=17.5,animation_index=None,object_node_indices=None);before=deepcopy((p._document(),p.undo_stack))
            with http_server(p) as (_,post):
                status,r=post('/api/player-action-glb-review',args);self.assertEqual(status,200,r);self.assertEqual((p._document(),p.undo_stack),before);self.assertEqual(r['operation'],'import_player_action_glb');self.assertEqual(r['glb_import']['edits'],[dict(frame_index=0,part_index=0,translation=dict(x=int(x)+7))]);self.assertFalse((p.root/'Authored'/'PLAYER'/'ActionInputs').exists())
                self.assertEqual(post('/api/player-action-glb-apply',dict(args,review_key='0'*64))[0],400);self.assertEqual((p._document(),p.undo_stack),before)
                status,result=post('/api/player-action-glb-apply',dict(args,review_key=r['review_key']));self.assertEqual(status,200,result);self.assertEqual(len(p.undo_stack),len(before[1])+1);self.assertEqual(post('/api/player-action-glb-apply',dict(args,review_key=r['review_key']))[0],400)
            path=p.root/'Authored'/'PLAYER'/'ActionInputs'/(sha256(content).hexdigest()+'.glb');self.assertEqual(path.read_bytes(),content);authored=deepcopy(p._document());p.undo();self.assertEqual(p._document(),before[0]);p.redo();self.assertEqual(p._document(),authored);p.save();p=ProjectService.open(p.root);self.assertEqual(p._document(),authored);self.assertFalse(p.dirty)
            raw=current(p,**ctx());pose=current_pose(p,**ctx(),expected_current_sha256=raw['effective_file_sha256'],action_slot=0,frame_index=0);self.assertEqual(pose['object_transforms'][0]['translation'][0],int(x)+7)
            # Later numeric edits retain the earlier GLB provenance independently.
            observed2=inspect(p,**ctx(),action_slot=0);body=dict(ctx(),action_slot=0,expected_current_sha256=observed2['current_file_sha256'],expected_action_sha256=observed2['current_clip']['source_record']['sha256'],edits=[dict(frame_index=1,part_index=0,rotation_psx=dict(x=17))]);nr=numeric_review(p,**body);numeric_apply(p,review_key=nr['review_key'],**body);self.assertEqual(p.player_action_overrides[asset]['actions']['0000']['glb_import'],r['retained_input']);p.save();p=ProjectService.open(p.root)
            built=build_project(p);audit=json.loads(Path(built['audit']).read_text(encoding='utf-8'))
            with zipfile.ZipFile(built['path']) as package:
                payload=package.read(audit['overlays'][0]['file']);_,bank=actions(payload,0,'0'*64);self.assertEqual(decode_part(bank[record['actions'][0]['source_record']['byte_offset']+2:][:9])['translation'][0],int(x)+7)
            original=path.read_bytes();path.write_bytes(original[:-1]+bytes([original[-1]^1]))
            with self.assertRaisesRegex(ProjectError,'retained GLB'):ProjectService.open(p.root)
            output=os.getenv('LEGAIA_PLAYER_ACTION_GLB_CASES')
            if output:Path(output).write_text(json.dumps(dict(report=report,record=dict(id=asset,data=record),inspection=observed,review=r,input=dict(sha256=sha256(content).hexdigest(),byteLength=len(content),fps=17.5,equipped=[0]*5),history=True,save_open=True,retained_exact=True,tamper_refused=True,numeric_provenance_retained=True,build_sha256=built['sha256'],gameplay_verified=False)),encoding='utf-8')
