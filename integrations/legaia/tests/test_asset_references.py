import os,tempfile,unittest
from unittest.mock import patch
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
   dict(id='animation://fixture/0',kind='animation',bindings=[dict(actor_semantic_id=self.actor,model_asset_semantic_id=self.model,initial_animation_id=2)]),
   dict(id='collision://fixture/0',kind='collision'),
   dict(id='trigger://fixture/0',kind='trigger',collision_id='collision://fixture/0',script_reference=dict(partition=2,record_index=0))]}
 def test_explicit_edges_scope_and_detachment(self):
  before=deepcopy((self.p.imports,self.p.overrides,self.p.actor_drafts,self.p.undo_stack));result=assemble(self.p,self.catalog,self.actor)
  self.assertEqual({e['kind'] for e in result['outgoing']},{'initial_model','effective_initial_model','actor_script_record','initial_animation_binding','effective_initial_animation_binding'})
  self.assertEqual(result['coverage']['unresolved_reference_count'],2)
  script=assemble(self.p,self.catalog,'script://fixture/actor');destination=next(n for n in script['nodes'] if n['id']=='scene://missing');self.assertFalse(destination['available'])
  self.assertEqual({e['kind'] for e in script['outgoing']},{'encoded_scene_change','script_dialogue_segment'})
  self.assertTrue(all(e['runtime_binding']=='not_asserted' for e in script['incoming']+script['outgoing']))
  self.assertTrue(all(e['source_catalog_key']=='a'*64 for e in script['incoming']+script['outgoing']))
  clip=assemble(self.p,self.catalog,'animation://fixture/0');self.assertEqual({e['kind'] for e in clip['incoming']},{'initial_animation_binding','effective_initial_animation_binding'});self.assertEqual(clip['outgoing'][0]['target_id'],self.model)
  collision=assemble(self.p,self.catalog,'collision://fixture/0');self.assertEqual(collision['incoming'][0]['kind'],'field_map_table_source');self.assertEqual(collision['outgoing'],[])
  result['nodes'][0]['label']='changed';self.assertEqual(before,(self.p.imports,self.p.overrides,self.p.actor_drafts,self.p.undo_stack))
 def test_invalid_identity_duplicate_type_and_source_changes(self):
  for value in [[],None,'','x'*1025,'asset://unknown']:
   with self.assertRaises(ProjectError):assemble(self.p,self.catalog,value)
  bad=deepcopy(self.catalog);bad['records'].append(dict(id=self.actor,kind='model'))
  with self.assertRaises(ProjectError):assemble(self.p,bad,self.actor)
  key=source_key(self.p);self.p.overrides[self.actor]={'Transform':{'position':{'x':200}}};self.assertNotEqual(key,source_key(self.p))
  with self.assertRaises(ProjectError):inspect(self.p,[])
 def test_material_edges_preserve_static_evidence_and_unresolved_results(self):
  material=dict(material_index=0,tpage=128,clut=0,uv_bounds=[0,0,1,1],evidence='static_vram_addresses_not_runtime_residency',status='address_match',source_ids=['texture://outside'])
  materials=dict(models=[dict(model_id=self.model,source_sha256='b'*64,materials=[material,dict(material_index=1,status='ambiguous',source_ids=['texture://candidate'])])],unresolved_reference_count=1,limitations=['Static only'])
  result=assemble(self.p,self.catalog,self.model,materials);edges=[e for e in result['outgoing'] if e['kind']=='static_material_texture_source'];self.assertEqual(len(edges),1);self.assertEqual(edges[0]['material_evidence']['model_source_sha256'],'b'*64);self.assertFalse(next(n for n in result['nodes'] if n['id']=='texture://outside')['available']);self.assertNotIn('texture://candidate',{n['id'] for n in result['nodes']});self.assertEqual(result['coverage']['unresolved_reference_count'],3)
 def test_effective_clip_links_follow_exact_donor_and_model_with_draft_layer(self):
  actor2=self.actor[:-1]+'2';copy=deepcopy(self.p.imports[self.p.active_scene]['actors'][0]);copy['semantic_id']=actor2;self.p.imports[self.p.active_scene]['actors'].append(copy);self.p.overrides[actor2]={'ActorAppearance':{'donor_entity_id':self.actor}};draft='draft://fixture/one';self.p.actor_drafts[draft]=dict(scene_id=self.p.active_scene,name='Draft',donor_entity_id=self.actor)
  refs=[dict(source_id=id,target_id=self.model,scene_id=self.p.active_scene,imported=False,effective=True,effective_donor_id=self.actor,kind='draft_initial_model_assignment' if id==draft else 'initial_model_assignment') for id in [actor2,draft]]
  with patch.object(self.p,'model_references',return_value=refs):
   actor_result=assemble(self.p,self.catalog,actor2);draft_result=assemble(self.p,self.catalog,draft)
   self.assertIn('appearance_donor',{e['kind'] for e in actor_result['outgoing']});effective=next(e for e in actor_result['outgoing'] if e['kind']=='effective_initial_animation_binding');self.assertEqual(effective['effective_animation_evidence'],dict(donor_entity_id=self.actor,model_id=self.model,initial_animation_id=2));self.assertEqual(effective['layer'],'effective');self.assertNotIn('initial_animation_binding',{e['kind'] for e in actor_result['outgoing']})
   self.assertEqual(next(e for e in draft_result['outgoing'] if e['kind']=='draft_initial_animation_binding')['layer'],'authored')
   refs[0]['target_id']='asset://different';self.assertNotIn('effective_initial_animation_binding',{e['kind'] for e in assemble(self.p,self.catalog,actor2)['outgoing']})

 def test_current_material_links_keep_retail_and_track_asset_bindings(self):
  original=dict(material_index=0,tpage=256,clut=0,uv_bounds=[0,0,1,1],evidence='static_vram_addresses_not_runtime_residency',status='address_match',source_ids=['texture://fixture/retail'])
  current={**original,'source_ids':['texture-new://fixture/current']};self.catalog['records'].append(dict(id=current['source_ids'][0],kind='texture'))
  materials=dict(models=[dict(model_id=self.model,source_sha256='a'*64,materials=[original])],current_models=[dict(model_id=self.model,retail_sha256='a'*64,source_sha256='b'*64,materials=[current])],current_state_key='c'*64,unresolved_reference_count=0,limitations=[])
  before=deepcopy(self.p._document());result=assemble(self.p,self.catalog,self.model,materials)
  retail=next(e for e in result['outgoing'] if e['kind']=='static_material_texture_source');effective=next(e for e in result['outgoing'] if e['kind']=='effective_material_texture_source')
  self.assertEqual(retail['target_id'],original['source_ids'][0]);self.assertEqual(effective['target_id'],current['source_ids'][0]);self.assertEqual(effective['layer'],'effective');self.assertEqual(effective['material_evidence']['model_current_sha256'],'b'*64);self.assertEqual(effective['source_catalog_key'],'a'*64)
  inverse=assemble(self.p,self.catalog,current['source_ids'][0],materials);self.assertTrue(any(e['source_id']==self.model and e['kind']=='effective_material_texture_source' for e in inverse['incoming']))
  self.assertEqual(self.p._document(),before)
  for attribute in ['model_overrides','texture_overrides','texture_additions']:
   key=source_key(self.p);getattr(self.p,attribute)['fixture']={'hash':'changed'};self.assertNotEqual(source_key(self.p),key)

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class RetailAssetReferences(unittest.TestCase):
 def test_fresh_sources_and_read_only_active_catalog(self):
  from importer.pipeline import import_scene
  with tempfile.TemporaryDirectory() as directory:
   p=ProjectService(Path(directory));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.import_metadata(import_scene(p.disc_path,'town01'));actor=p.imports[p.active_scene]['actors'][3]['semantic_id'];before=deepcopy((p.imports,p.overrides,p.actor_drafts,p.undo_stack,p.active_scene));result=inspect(p,actor)
   self.assertEqual(result['source_key'],source_key(p));self.assertIn('actor_script_record',{e['kind'] for e in result['outgoing']});self.assertTrue(any(e['kind']=='initial_model' for e in result['outgoing']));self.assertEqual(before,(p.imports,p.overrides,p.actor_drafts,p.undo_stack,p.active_scene))
   from sdk.material_references import discover
   from sdk.resources import _verify
   with patch('sdk.material_references.discover',wraps=discover) as decoding,patch('sdk.resources._verify',wraps=_verify) as verify:
    again=inspect(p,actor);self.assertEqual(again,result);self.assertEqual(decoding.call_count,0);self.assertGreaterEqual(verify.call_count,1)
