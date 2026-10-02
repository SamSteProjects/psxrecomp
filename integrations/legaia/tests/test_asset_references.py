import os,tempfile,unittest
from pathlib import Path
from copy import deepcopy
from sdk.project import ProjectService,ProjectError
from sdk.asset_references import assemble,inspect,source_key
from test_project_workflow import synthetic_scene

class AssetReferences(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.p=ProjectService(Path(self.temp.name));self.p.import_metadata(synthetic_scene());self.actor='scene://fixture/actors/man-p1/0001';self.model='asset://fixture/model/0'
  self.catalog={'source_key':'a'*64,'records':[
   dict(id='script://fixture/actor',kind='script',actor_semantic_id=self.actor,transitions=[dict(target_scene_name='missing',pc=12)],model_selection_references=[dict(selector=0)]),
   dict(id='dialogue://fixture/0',kind='dialogue',script_id='script://fixture/actor',pc=8),
   dict(id='animation://fixture/0',kind='animation',bindings=[dict(actor_semantic_id=self.actor,model_asset_semantic_id=self.model)]),
   dict(id='collision://fixture/0',kind='collision'),
   dict(id='trigger://fixture/0',kind='trigger',collision_id='collision://fixture/0',script_reference=dict(partition=2,record_index=0))]}
 def test_explicit_edges_scope_and_detachment(self):
  before=deepcopy((self.p.imports,self.p.overrides,self.p.actor_drafts,self.p.undo_stack));result=assemble(self.p,self.catalog,self.actor)
  self.assertEqual({e['kind'] for e in result['outgoing']},{'initial_model','effective_initial_model','actor_script_record','initial_animation_binding'})
  self.assertEqual(result['coverage']['unresolved_reference_count'],2)
  script=assemble(self.p,self.catalog,'script://fixture/actor');destination=next(n for n in script['nodes'] if n['id']=='scene://missing');self.assertFalse(destination['available'])
  self.assertEqual({e['kind'] for e in script['outgoing']},{'encoded_scene_change','script_dialogue_segment'})
  self.assertTrue(all(e['runtime_binding']=='not_asserted' for e in script['incoming']+script['outgoing']))
  self.assertTrue(all(e['source_catalog_key']=='a'*64 for e in script['incoming']+script['outgoing']))
  clip=assemble(self.p,self.catalog,'animation://fixture/0');self.assertEqual(clip['incoming'][0]['kind'],'initial_animation_binding');self.assertEqual(clip['outgoing'][0]['target_id'],self.model)
  collision=assemble(self.p,self.catalog,'collision://fixture/0');self.assertEqual(collision['incoming'][0]['kind'],'field_map_table_source');self.assertEqual(collision['outgoing'],[])
  result['nodes'][0]['label']='changed';self.assertEqual(before,(self.p.imports,self.p.overrides,self.p.actor_drafts,self.p.undo_stack))
 def test_invalid_identity_duplicate_type_and_source_changes(self):
  for value in [[],None,'','x'*1025,'asset://unknown']:
   with self.assertRaises(ProjectError):assemble(self.p,self.catalog,value)
  bad=deepcopy(self.catalog);bad['records'].append(dict(id=self.actor,kind='model'))
  with self.assertRaises(ProjectError):assemble(self.p,bad,self.actor)
  key=source_key(self.p);self.p.overrides[self.actor]={'Transform':{'position':{'x':200}}};self.assertNotEqual(key,source_key(self.p))
  with self.assertRaises(ProjectError):inspect(self.p,[])

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class RetailAssetReferences(unittest.TestCase):
 def test_fresh_sources_and_read_only_active_catalog(self):
  from importer.pipeline import import_scene
  with tempfile.TemporaryDirectory() as directory:
   p=ProjectService(Path(directory));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.import_metadata(import_scene(p.disc_path,'town01'));actor=p.imports[p.active_scene]['actors'][3]['semantic_id'];before=deepcopy((p.imports,p.overrides,p.actor_drafts,p.undo_stack,p.active_scene));result=inspect(p,actor)
   self.assertEqual(result['source_key'],source_key(p));self.assertIn('actor_script_record',{e['kind'] for e in result['outgoing']});self.assertTrue(any(e['kind']=='initial_model' for e in result['outgoing']));self.assertEqual(before,(p.imports,p.overrides,p.actor_drafts,p.undo_stack,p.active_scene))
