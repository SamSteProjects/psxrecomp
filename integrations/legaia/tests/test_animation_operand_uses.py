from copy import deepcopy
from pathlib import Path
import json,os,tempfile,unittest
from sdk.project import ProjectService,ProjectError
from sdk.animation_operand_uses import inspect
from sdk.script_animation_operands import options
from sdk.script_branches import state_key
from sdk.npc_animation_operands import review
from importer.pipeline import import_scene
from test_model_primitive_workflow import http_server

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'Private Retail disc required')
class ArgumentUses(unittest.TestCase):
 def test_native_source_and_independent_clones_readonly_stale_and_http(self):
  with tempfile.TemporaryDirectory() as d:
   p=ProjectService(Path(d));p.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'],'map02'),os.environ['LEGAIA_DISC_BIN']);owner='scene://map02/actors/man-p1/0003'
   target=options(p,owner)['targets'][0];ids=[]
   for value in (target['values']['animation_operand'],255):
    p.command(dict(type='create_actor_draft',donor_entity_id=owner,name='Argument usage',position=dict(x=128,z=256)))
    identity=next(name for name in p.actor_drafts if name not in ids);ids.append(identity)
    request=dict(entity_id=identity,entries={target['semantic_id']:dict(animation_operand=value)});proposal=review(p,request)
    p.command(dict(type='set_actor_draft_animation_operands',**request,review_key=proposal['review_key']))
   key=state_key(p);before=deepcopy((p._document(),p.undo_stack,p.redo_stack,p.imports));report=inspect(p,owner,target['semantic_id'],key)
   self.assertEqual(before,(p._document(),p.undo_stack,p.redo_stack,p.imports));self.assertEqual(report['query_values'],target['values'])
   clone_rows={r['entity_id']:r for r in report['rows'] if r['kind']=='npc'};self.assertTrue(clone_rows[ids[0]]['effective_match']);self.assertFalse(clone_rows[ids[1]]['effective_match']);self.assertTrue(clone_rows[ids[1]]['retail_match'])
   self.assertTrue(any(r['entity_id']==owner for r in report['rows']))
   with http_server(p) as (server,post):
    server.RequestHandlerClass.log_message=lambda *args:None
    request=dict(entity_id=owner,animation_operand_id=target['semantic_id'],expected_state_key=key)
    self.assertEqual(post('/api/animation-operand-uses',request)[0],200)
    self.assertEqual(post('/api/animation-operand-uses',dict(request,extra=1))[0],400)
    self.assertEqual(post('/api/animation-operand-uses',dict(request,entity_id=[]))[0],400)
    self.assertEqual(post('/api/animation-operand-uses',dict(request,expected_state_key='0'*64))[0],400)
    self.assertEqual(post('/api/animation-operand-uses',dict(request,offset=True))[0],400)
    self.assertEqual(post('/api/animation-operand-uses',dict(request,offset=256))[0],400)
   if os.environ.get('LEGAIA_ARGUMENT_USES_EVIDENCE'):
    out=Path(os.environ['LEGAIA_ARGUMENT_USES_EVIDENCE']);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(dict(source=options(p,owner),id=target['semantic_id'],report=report),indent=2)+'\n',encoding='utf-8')
   p.command(dict(type='rename_actor_draft',entity_id=ids[0],name='Changed'))
   with self.assertRaises(ProjectError):inspect(p,owner,target['semantic_id'],key)
   import uuid
   bounded_project=ProjectService(Path(d)/'bounded');bounded_project.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'],'jagaroom'),os.environ['LEGAIA_DISC_BIN'])
   bound_owner='scene://jagaroom/actors/man-p1/0008';bound_targets=options(bounded_project,bound_owner)['targets'];bound_target=bound_targets[0]
   self.assertGreaterEqual(len(bound_targets),2)
   entries={t['semantic_id']:deepcopy(bound_target['values']) for t in bound_targets if t['mnemonic']==bound_target['mnemonic']}
   draft=dict(scene_id=bounded_project.active_scene,donor_entity_id=bound_owner,name='Paged usage probe',position=dict(x=128,z=256),animation_operands=dict(donor_entity_id=bound_owner,entries=entries))
   bounded_project.actor_drafts={'authored-actor://'+str(uuid.UUID(int=i+1)):deepcopy(draft) for i in range(128)}
   bounded_project=ProjectService.open(bounded_project.save())
   bound_key=state_key(bounded_project);bounded=inspect(bounded_project,bound_owner,bound_target['semantic_id'],bound_key)
   self.assertTrue(bounded['truncated']);self.assertEqual(len(bounded['rows']),256);self.assertGreater(bounded['match_count'],256)
   last=inspect(bounded_project,bound_owner,bound_target['semantic_id'],bound_key,256)
   self.assertEqual(last['page_offset'],256);self.assertEqual(len(last['rows']),bounded['match_count']-256)
   self.assertFalse({(r['entity_id'],r['target']['semantic_id']) for r in bounded['rows']}&{(r['entity_id'],r['target']['semantic_id']) for r in last['rows']})
   self.assertEqual(inspect(bounded_project,bound_owner,bound_target['semantic_id'],bound_key)['rows'],bounded['rows'])
   for offset in (-256,1,True,1.5,'256',512,8192):
    with self.assertRaises(ProjectError):inspect(bounded_project,bound_owner,bound_target['semantic_id'],bound_key,offset)
   if os.environ.get('LEGAIA_ARGUMENT_USES_EVIDENCE'):
    content=json.loads(out.read_text(encoding='utf-8'));content.update(bounded_source=options(bounded_project,bound_owner),bounded_report=bounded,last_report=last,bounded_id=bound_target['semantic_id']);out.write_text(json.dumps(content,indent=2)+'\n',encoding='utf-8')
   p.active_scene='scene://foreign'
   with self.assertRaises(ProjectError):inspect(p,owner,target['semantic_id'],state_key(p))

if __name__=='__main__':unittest.main()
