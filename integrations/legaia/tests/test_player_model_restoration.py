import base64,json,os,struct,tempfile,unittest,zipfile
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.project_assets import source_key
from sdk.player_model_restoration import review,proposed_preview,apply

MODEL='asset://legaia/models/player-battle/0000'
OTHER='asset://legaia/models/player-battle/0001'


def context(p,catalog,asset=MODEL,equipped=None):
 return dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=asset,catalog_source_key=catalog['source_key'],equipped=[0]*5 if equipped is None else equipped)


def author_coauthors(p):
 from sdk.player_battle import resources
 from sdk.player_model_authoring import export as me,review as mr,apply as ma,current,current_export
 from sdk.player_action_authoring import inspect as ai,review as ar,apply as aa
 from sdk.player_action_glb import review as gr,apply as ga
 from importer.animation_glb import _read_glb
 from importer.model_glb import _write_glb
 p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();catalog=resources(p,str(p.root),source_key(p))['catalog'];record=catalog['models'][0]
 first=me(p,**context(p,catalog));section=first['binding']['native_binding']['assembly']['object_sources'][0]['section_index'];variant=next(r for r in record['descriptors'] if r['item_id'] and r['section_index']!=section);equipped=[0]*5;equipped[variant['section_index']]=variant['item_id']
 for asset,selection,delta,target in ((MODEL,[0]*5,10,None),(MODEL,equipped,1,variant['section_index']),(OTHER,[0]*5,1,None)):
  exported=me(p,**context(p,catalog,asset,selection));doc,binary=_read_glb(base64.b64decode(exported['glb_base64']));index=0 if target is None else next(i for i,r in enumerate(exported['binding']['native_binding']['assembly']['object_sources']) if r['section_index']==target);doc['nodes'][index]['translation']=[delta,0,0];content=_write_glb(doc,binary);args=dict(context(p,catalog,asset,selection),binding=exported['binding'],glb_base64=base64.b64encode(content).decode());value=mr(p,**args);ma(p,review_key=value['review_key'],**args)
 raw=current(p,**context(p,catalog));exported=current_export(p,**context(p,catalog),expected_current_sha256=raw['effective_file_sha256'],mode='clip',action_slot=0,frame_index=None,fps=17.5);doc,binary=_read_glb(base64.b64decode(exported['glb_base64']));binary=bytearray(binary);sampler=doc['animations'][0]['samplers'][0];accessor=doc['accessors'][sampler['output']];at=doc['bufferViews'][accessor['bufferView']]['byteOffset'];x=struct.unpack_from('<f',binary,at)[0];struct.pack_into('<f',binary,at,x+7);content=_write_glb(doc,bytes(binary));observed=ai(p,**context(p,catalog),action_slot=0)
 args=dict(context(p,catalog),action_slot=0,expected_current_sha256=observed['current_file_sha256'],expected_action_sha256=observed['current_clip']['source_record']['sha256'],glb_base64=base64.b64encode(content).decode(),fps=17.5,animation_index=None,object_node_indices=None);value=gr(p,**args);ga(p,review_key=value['review_key'],**args);receipt=deepcopy(p.player_action_overrides[MODEL]['actions']['0000']['glb_import'])
 observed=ai(p,**context(p,catalog),action_slot=0);args=dict(context(p,catalog),action_slot=0,expected_current_sha256=observed['current_file_sha256'],expected_action_sha256=observed['current_clip']['source_record']['sha256'],edits=[dict(frame_index=1,part_index=0,rotation_psx=dict(x=17))]);value=ar(p,**args);aa(p,review_key=value['review_key'],**args);assert p.player_action_overrides[MODEL]['actions']['0000']['glb_import']==receipt
 p.save();return catalog,equipped


class PlayerModelRestorationBoundaryTests(unittest.TestCase):
 def test_literal_composition_reverse_model_pools_and_atomic_refusal(self):
  retail=bytes(0x8000+2048);model=bytearray(retail);model[0x8000+44]=7;model=bytes(model);action=bytearray(retail);action[24]=5;action=bytes(action);descriptor=128;composed=model[:16]+action[16:descriptor]+model[descriptor:];row=dict(record_index=0,item_id=0,section_index=0,descriptor_offset=descriptor,byte_offset=0x8000,byte_length=2048);source=dict(disc=dict(sha256='a'*64),sha256=sha256(retail).hexdigest());record=dict(semantic_id=MODEL,player_index=0,source_record=source)
  owner=dict(inputs=[dict(sha256='b'*64,byte_length=28)]);p=SimpleNamespace(root=Path('literal-player'),disc_path='literal-disc',player_model_overrides={MODEL:owner,OTHER:{'untouched':True}},undo_stack=[],redo_stack=['redo']);inspection=dict(record=record,effective_file_sha256=sha256(model).hexdigest(),action_binding={'held':True},tmd_base64='native',retail_tmd_base64='retail')
  original=b'X'*40+b'abcdefgh'+b'Z'*16;owned=bytearray(original);owned[44]=7;owned=bytes(owned)
  args=dict(expected_project_path=str(p.root),expected_source_key='source',asset_id=MODEL,catalog_source_key='catalog',equipped=[0]*5,expected_current_sha256=sha256(model).hexdigest(),expected_current_composed_sha256=sha256(composed).hexdigest())
  def section(raw,r):return (owned if raw==model else original),100,40,8,0
  with patch('sdk.player_model_restoration.current',return_value=inspection),patch('sdk.player_model_restoration._sources',return_value=('a'*64,[(863,0,0,retail)])),patch('sdk.player_model_restoration.effective',return_value=model),patch('sdk.player_model_restoration.effective_actions',return_value=(action,[])),patch('sdk.player_model_restoration.table',return_value=[row]),patch('sdk.player_model_restoration._section',side_effect=section),patch('sdk.player_model_restoration.replace_model_content'),patch('sdk.player_model_restoration.validate'),patch('sdk.player_model_restoration._fresh'):
   held=deepcopy(p.__dict__);value=review(p,**args);self.assertEqual(p.__dict__,held);candidate=base64.b64decode(value['candidate_composed_file_base64']);self.assertEqual(candidate,action);self.assertEqual(candidate[:0x8000],composed[:0x8000]);self.assertEqual(candidate[0x8000:],retail[0x8000:])
   for changes in ({'review_key':'0'*64},{'review_key':value['review_key'],'expected_current_sha256':'0'*64},{'review_key':value['review_key'],'expected_current_composed_sha256':'0'*64}):
    with self.assertRaises(ProjectError):apply(p,**dict(args,**changes))
    self.assertEqual(p.__dict__,held)
   with patch('sdk.player_model_restoration._section',side_effect=lambda raw,r:(b'Q'+owned[1:] if raw==model else original,100,40,8,0)):
    with self.assertRaises(ProjectError):review(p,**args)
    self.assertEqual(p.__dict__,held)
   result=apply(p,review_key=value['review_key'],**args);self.assertEqual(result['history_steps'],1);self.assertEqual(p.player_model_overrides,{OTHER:{'untouched':True}});self.assertEqual(p.redo_stack,[])
   with self.assertRaises(ProjectError):review(p,**args)


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Private Retail source required')
class PlayerModelRestorationWorkflowTests(unittest.TestCase):
 def test_reverse_import_retail_geometry_and_valid_ownership_only_restoration(self):
  from sdk.player_battle import resources
  from sdk.player_model_authoring import export as me,review as mr,apply as ma,current
  from sdk.player_model_store import _retain,effective
  from importer.player_battle import _sources
  from importer.animation_glb import _read_glb
  from importer.model_glb import _write_glb
  from importer.pipeline import import_scene
  from sdk.build import build_project
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();catalog=resources(p,str(p.root),source_key(p))['catalog']
   for delta in (1,-1):
    exported=me(p,**context(p,catalog));doc,binary=_read_glb(base64.b64decode(exported['glb_base64']));doc['nodes'][0]['translation']=[delta,0,0];args=dict(context(p,catalog),binding=exported['binding'],glb_base64=base64.b64encode(_write_glb(doc,binary)).decode());v=mr(p,**args);ma(p,review_key=v['review_key'],**args)
   inspected=current(p,**context(p,catalog));self.assertEqual(inspected['tmd_base64'],inspected['retail_tmd_base64']);args=dict(context(p,catalog),expected_current_sha256=inspected['effective_file_sha256'],expected_current_composed_sha256=inspected['current_composed_sha256']);v=review(p,**args);self.assertEqual(v['projection']['decoded_pool_byte_change_count'],0);before=deepcopy(p._document());files={f:f.read_bytes() for f in (p.root/'Authored').rglob('*') if f.is_file()};history=len(p.undo_stack);apply(p,review_key=v['review_key'],**args);self.assertEqual(len(p.undo_stack),history+1);self.assertNotIn(MODEL,p.player_model_overrides);after=deepcopy(p._document());p.undo();self.assertEqual(p._document(),before);p.redo();self.assertEqual(p._document(),after);p.save();self.assertEqual(ProjectService.open(p.root)._document(),after)
   for path,data in files.items():self.assertEqual(path.read_bytes(),data)
  # A persisted owner can be completely valid while retaining a no-op native
  # roundtrip input. Replay, retained hashes and Save/Open all verify this owner.
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();catalog=resources(p,str(p.root),source_key(p))['catalog'];exported=me(p,**context(p,catalog));roundtrip=mr(p,**context(p,catalog),binding=exported['binding'],glb_base64=exported['glb_base64']);self.assertEqual(roundtrip['projection']['changes'],[]);_,sources=_sources(p.disc_path);retail=sources[0][3];key=_retain(p,'Candidates',retail);content=base64.b64decode(exported['glb_base64']);input_key=_retain(p,'Inputs',content);record=catalog['models'][0]
   p.player_model_overrides[MODEL]=dict(schema_version='legaia.player-model-override.v1',asset_id=MODEL,source_record=deepcopy(record['source_record']),current_sha256=key,byte_length=len(retail),inputs=[dict(sha256=input_key,byte_length=len(content),binding=deepcopy(exported['binding']),review_key=roundtrip['review_key'],base_sha256=key,proposed_sha256=key)])
   self.assertEqual(effective(p,record,retail),retail);p.import_metadata(import_scene(p.disc_path,'town01'));p.save();p=ProjectService.open(p.root);before_build=build_project(p);before_package=Path(before_build['path']).read_bytes();inspection=current(p,**context(p,catalog));args=dict(context(p,catalog),expected_current_sha256=inspection['effective_file_sha256'],expected_current_composed_sha256=inspection['current_composed_sha256']);held=deepcopy((p._document(),p.undo_stack,p.redo_stack));v=review(p,**args);comparison=proposed_preview(p,review_key=v['review_key'],**args);self.assertEqual((p._document(),p.undo_stack,p.redo_stack),held);self.assertTrue(v['projection']['ownership_only']);self.assertFalse(v['projection']['native_content_changed']);self.assertEqual(v['projection']['byte_change_count'],0);self.assertEqual(v['projection']['restored_sections'],[]);self.assertEqual(v['current_composed_file_base64'],v['candidate_composed_file_base64']);history=len(p.undo_stack);apply(p,review_key=v['review_key'],**args);self.assertEqual(len(p.undo_stack),history+1);self.assertNotIn(MODEL,p.player_model_overrides);after=deepcopy(p._document());p.undo();self.assertEqual(p._document(),held[0]);p.redo();self.assertEqual(p._document(),after);p.save();self.assertEqual(ProjectService.open(p.root)._document(),after);self.assertEqual((p.root/'Authored'/'PLAYER'/'Candidates'/(key+'.bin')).read_bytes(),retail);self.assertEqual((p.root/'Authored'/'PLAYER'/'Inputs'/(input_key+'.glb')).read_bytes(),content);after_build=build_project(p);self.assertEqual(Path(after_build['path']).read_bytes(),before_package);self.assertEqual(after_build['sha256'],before_build['sha256'])
   if os.getenv('LEGAIA_PLAYER_MODEL_RESTORATION_OWNERSHIP_CASES'):Path(os.environ['LEGAIA_PLAYER_MODEL_RESTORATION_OWNERSHIP_CASES']).write_text(json.dumps(dict(inspection=inspection,review=v,comparison=comparison,report=dict(project_path=inspection['project_path'],project_source_key=inspection['project_source_key'],catalog=catalog),record=dict(id=MODEL,data=record),ownership_only=True,native_file_unchanged=True,package_unchanged=True,package_sha256=after_build['sha256'],valid_input_replay=True,one_history=True,undo_redo=True,save_open=True,historical_files_exact=True,gameplay_verified=False)),encoding='utf-8')

 def test_multiple_equipment_inputs_glb_numeric_motion_other_owner_history_and_package(self):
  from sdk.player_model_authoring import current
  from sdk.player_model_store import _path
  from sdk.player_action_authoring import inspect as ai,review as ar,apply as aa
  from sdk.player_action_glb import input_records
  from sdk.player_model_build import prepare
  from sdk.build import build_project
  from importer.pipeline import import_scene,_disc_context
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));catalog,equipped=author_coauthors(p);p=ProjectService.open(p.root);inspection=current(p,**context(p,catalog));args=dict(context(p,catalog),expected_current_sha256=inspection['effective_file_sha256'],expected_current_composed_sha256=inspection['current_composed_sha256']);value=review(p,**args);comparison=proposed_preview(p,review_key=value['review_key'],**args);self.assertGreaterEqual(len(value['projection']['restored_sections']),2);self.assertEqual(len(value['projection']['removed_active_inputs']),2)
   held=deepcopy((p._document(),p.undo_stack,p.redo_stack));retained={f:f.read_bytes() for f in (p.root/'Authored').rglob('*') if f.is_file()};self.assertEqual((p._document(),p.undo_stack,p.redo_stack),held)
   for changes in ({'review_key':'0'*64},{'review_key':value['review_key'],'expected_current_sha256':'0'*64},{'review_key':value['review_key'],'expected_current_composed_sha256':'0'*64}):
    with self.assertRaises(ProjectError):apply(p,**dict(args,**changes))
    self.assertEqual((p._document(),p.undo_stack,p.redo_stack),held)
   target=_path(p,'Inputs',p.player_model_overrides[MODEL]['inputs'][0]['sha256']);original=target.read_bytes();target.write_bytes(original[:-1])
   try:
    with self.assertRaises(ProjectError):apply(p,review_key=value['review_key'],**args)
    self.assertEqual((p._document(),p.undo_stack,p.redo_stack),held)
   finally:target.write_bytes(original)
   observed=ai(p,**context(p,catalog),action_slot=0);nargs=dict(context(p,catalog),action_slot=0,expected_current_sha256=observed['current_file_sha256'],expected_action_sha256=observed['current_clip']['source_record']['sha256'],edits=[dict(frame_index=2,part_index=0,rotation_psx=dict(x=18))]);nv=ar(p,**nargs);aa(p,review_key=nv['review_key'],**nargs);stale=deepcopy((p._document(),p.undo_stack,p.redo_stack))
   with self.assertRaises(ProjectError):apply(p,review_key=value['review_key'],**args)
   self.assertEqual((p._document(),p.undo_stack,p.redo_stack),stale)
   inspection=current(p,**context(p,catalog));args=dict(context(p,catalog),expected_current_sha256=inspection['effective_file_sha256'],expected_current_composed_sha256=inspection['current_composed_sha256']);value=review(p,**args);comparison=proposed_preview(p,review_key=value['review_key'],**args);before=deepcopy(p._document());actions=deepcopy(p.player_action_overrides);other=deepcopy(p.player_model_overrides[OTHER]);motion_inputs=input_records(p,catalog);candidate=base64.b64decode(value['candidate_composed_file_base64']);current_file=base64.b64decode(value['current_composed_file_base64']);retail=base64.b64decode(value['retail_file_base64']);self.assertEqual(current_file[:0x8000],candidate[:0x8000]);self.assertEqual(candidate[0x8000:],retail[0x8000:]);self.assertNotEqual(candidate,retail)
   history=len(p.undo_stack);result=apply(p,review_key=value['review_key'],**args);self.assertEqual(result['history_steps'],1);self.assertEqual(len(p.undo_stack),history+1);self.assertNotIn(MODEL,p.player_model_overrides);self.assertEqual(p.player_model_overrides[OTHER],other);self.assertEqual(p.player_action_overrides,actions);self.assertEqual(input_records(p,catalog),motion_inputs)
   for path,data in retained.items():self.assertEqual(path.read_bytes(),data)
   after=deepcopy(p._document());p.undo();self.assertEqual(p._document(),before);p.redo();self.assertEqual(p._document(),after);p.save();p=ProjectService.open(p.root);self.assertEqual(p._document(),after)
   for selection in ([0]*5,equipped):
    view=current(p,**context(p,catalog,equipped=selection));self.assertEqual(view['effective_file_sha256'],value['projection']['candidate_model_sha256']);self.assertEqual(view['tmd_base64'],view['retail_tmd_base64']);self.assertEqual(view['current_composed_sha256'],value['projection']['candidate_composed_sha256'])
   with self.assertRaises(ProjectError):review(p,**dict(context(p,catalog),expected_current_sha256=value['projection']['candidate_model_sha256'],expected_current_composed_sha256=value['projection']['candidate_composed_sha256']))
   p.import_metadata(import_scene(p.disc_path,'town01'));p.save()
   with _disc_context(p.disc_path) as (_,disc,_,archive):overlays,_=prepare(p,archive,disc)
   self.assertEqual(len(overlays),2);selected=next(o for o in overlays if o['source_record']['prot_entry_index']==863);self.assertEqual(selected['payload'],candidate);self.assertEqual(selected['retained_input_sha256'],[]);self.assertTrue(selected['action_ledger_replay'])
   built=build_project(p);directory=Path(built['package_directory'])
   with zipfile.ZipFile(built['path']) as package:
    files={f.relative_to(directory).as_posix():f.read_bytes() for f in directory.rglob('*') if f.is_file()};self.assertEqual(set(files),set(package.namelist()))
    for name,data in files.items():self.assertEqual(package.read(name),data)
    for overlay in overlays:self.assertEqual(package.read(overlay['file']),overlay['payload']);self.assertEqual(files[overlay['file']],overlay['payload'])
   for path,data in retained.items():self.assertEqual(path.read_bytes(),data)
   if os.getenv('LEGAIA_PLAYER_MODEL_RESTORATION_CASES'):Path(os.environ['LEGAIA_PLAYER_MODEL_RESTORATION_CASES']).write_text(json.dumps(dict(inspection=inspection,review=value,comparison=comparison,report=dict(project_path=inspection['project_path'],project_source_key=inspection['project_source_key'],catalog=catalog),record=dict(id=MODEL,data=catalog['models'][0]),multi_equipment_sections_restored=True,multiple_glb_inputs_removed=True,retained_motion_glb_numeric_exact=True,other_model_owner_exact=True,protected_record0_descriptors_loaders_textures=True,no_mutation_review_preview=True,stale_and_tampered_input_refused=True,one_history=True,undo_redo=True,save_open=True,whole_directory_zip_exact=True,composed_action_only_native_file_exact=True,historical_files_exact=True,package_sha256=built['sha256'],gameplay_verified=False)),encoding='utf-8')
