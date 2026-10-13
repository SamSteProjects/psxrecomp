import base64,json,os,tempfile,unittest,zipfile
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.project_assets import source_key
from sdk.monster_motion_restoration import review,apply,proposed_pose
from importer.serialization import compress_lzs


class MonsterRestorationBoundaryTests(unittest.TestCase):
 def test_literal_whole_stream_neighbors_owner_removal_and_atomic_refusals(self):
  retail=bytes([1,2])+bytes.fromhex('010234050678090abc')+bytes.fromhex('112233445566778899')
  original=b'HEADER'+retail+b'NEIGHBORS';current=bytearray(original);current[9]^=1;current[21]^=2;current=bytes(current)
  packed=compress_lzs(original);source=dict(byte_offset=6,byte_length=len(retail),compressed_stream_offset=0,entry_offset=0,entry_end=len(original))
  clip=dict(semantic_id='action',part_count=1,frame_count=2,source_record=source)
  owner=dict(edits=[dict(frame_index=0,part_index=0)],glb_import=dict(glb_sha256='a'*64));other=dict(edits=['untouched'])
  project=SimpleNamespace(root=Path('literal-project'),monster_motion_overrides={'action':owner,'other':other},undo_stack=[],redo_stack=['redo'])
  args=dict(animation_id='action',frame_index=0,expected_current_block_sha256=sha256(current).hexdigest(),expected_project_path=str(project.root),expected_source_key='source',asset_id='model',catalog_source_key='catalog')
  snapshot=(clip,original,current,packed,len(packed),{},current[6:6+len(retail)])
  with patch('sdk.monster_motion_restoration.snapshot',return_value=snapshot),patch('sdk.monster_motion_restoration.validate',side_effect=lambda p,v:deepcopy(v)),patch('sdk.monster_motion_restoration._fresh'):
   held=deepcopy(project.__dict__);v=review(project,**args);self.assertEqual(project.__dict__,held)
   candidate=base64.b64decode(v['candidate_block_base64']);self.assertEqual(candidate,original);self.assertEqual(candidate[:6],current[:6]);self.assertEqual(candidate[6+len(retail):],current[6+len(retail):]);self.assertEqual(v['projection']['byte_change_count'],2)
   for changes in ({'review_key':'0'*64},{'review_key':v['review_key'],'expected_current_block_sha256':'0'*64}):
    with self.assertRaises(ProjectError):apply(project,**dict(args,**changes))
    self.assertEqual(project.__dict__,held)
   result=apply(project,review_key=v['review_key'],**args);self.assertEqual(result['history_steps'],1);self.assertEqual(project.monster_motion_overrides,{'other':other});self.assertEqual(project.undo_stack[0]['before']['action'],owner);self.assertEqual(project.redo_stack,[])
   with self.assertRaises(ProjectError):review(project,**args)
  project.monster_motion_overrides={'action':owner};unchanged=(clip,original,original,packed,len(packed),{},retail)
  with patch('sdk.monster_motion_restoration.snapshot',return_value=unchanged):
   with self.assertRaises(ProjectError):review(project,**dict(args,expected_current_block_sha256=sha256(original).hexdigest()))


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN') and os.getenv('LEGAIA_MONSTER_EDITED_GLB'),'Private disc and edited native monster clip are required')
class MonsterRestorationWorkflowTests(unittest.TestCase):
 def test_glb_numeric_other_action_model_texture_recovery_history_open_and_package(self):
  from sdk.monster_archive import resources
  from sdk.monster_motion_authoring import inspect,review as numeric_review,apply as numeric_apply
  from sdk.monster_motion_glb import review as glb_review,apply as glb_apply,path
  from sdk.monster_motion_inputs import records as input_records
  from sdk.monster_model_authoring import snapshot,export as model_export,review as model_review,apply as model_apply
  from sdk.monster_palettes import inspect as palette_inspect,review as palette_review,apply as palette_apply
  from sdk.build import build_project
  from importer.pipeline import import_scene
  from importer.core import decompress_lzs
  from test_monster_model_authoring import shifted_glb
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();model='asset://legaia/models/monster-archive/0063'
   catalog=resources(p,expected_project_path=str(p.root),expected_source_key=source_key(p))['catalog'];clips=[c for c in catalog['animations'] if c['model_asset_id']==model and c['preview_supported']];selected=next(c for c in clips if c['entry_index']==0);other=next(c for c in clips if c['entry_index']!=0)
   def ctx():return dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=model,catalog_source_key=catalog['source_key'])
   def numeric(clip,frame=0,amount=1):
    i=inspect(p,**ctx(),animation_id=clip['semantic_id'],frame_index=frame,part_index=0);t=i['channels']['translation'].copy();t[0]+=amount
    args=dict(ctx(),animation_id=clip['semantic_id'],frame_index=frame,part_index=0,expected_current_block_sha256=i['current_block_sha256'],translation=t,rotation_psx=i['channels']['rotation_psx']);v=numeric_review(p,**args);numeric_apply(p,review_key=v['review_key'],**args)
   i=inspect(p,**ctx(),animation_id=selected['semantic_id'],frame_index=0,part_index=0);no_owner=dict(ctx(),animation_id=selected['semantic_id'],frame_index=0,expected_current_block_sha256=i['current_block_sha256'])
   with self.assertRaises(ProjectError):review(p,**no_owner)
   content=Path(os.environ['LEGAIA_MONSTER_EDITED_GLB']).read_bytes();gargs=dict(ctx(),animation_id=selected['semantic_id'],expected_current_block_sha256=i['current_block_sha256'],glb_base64=base64.b64encode(content).decode(),fps=24,animation_index=None,object_node_indices=None);g=glb_review(p,**gargs);glb_apply(p,review_key=g['review_key'],**gargs)
   receipt=deepcopy(p.monster_motion_overrides[selected['semantic_id']]['glb_import']);numeric(selected,1,3);self.assertEqual(p.monster_motion_overrides[selected['semantic_id']]['glb_import'],receipt);numeric(other,0,2)
   exported=model_export(p,**ctx());margs=dict(ctx(),binding=exported['binding'],glb_base64=base64.b64encode(shifted_glb(base64.b64decode(exported['glb_base64']))).decode());m=model_review(p,**margs);model_apply(p,review_key=m['review_key'],**margs)
   texture='texture://legaia/monster-archive/0063/pool';pctx=dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=texture,palette_index=0);palette=palette_inspect(p,**pctx);pargs=dict(pctx,entry_index=1,word=palette['preview']['words'][1]^1,expected_current_sha256=palette['current_pool_sha256']);pv=palette_review(p,**pargs);palette_apply(p,review_key=pv['review_key'],**pargs)
   p.save();p=ProjectService.open(p.root);i=inspect(p,**ctx(),animation_id=selected['semantic_id'],frame_index=1,part_index=0);args=dict(ctx(),animation_id=selected['semantic_id'],frame_index=1,expected_current_block_sha256=i['current_block_sha256']);v=review(p,**args)
   held=deepcopy((p._document(),p.undo_stack,p.redo_stack));comparison=proposed_pose(p,review_key=v['review_key'],**args);self.assertEqual((p._document(),p.undo_stack,p.redo_stack),held)
   for change in ({'review_key':'0'*64},{'review_key':v['review_key'],'expected_current_block_sha256':'0'*64}):
    with self.assertRaises(ProjectError):apply(p,**dict(args,**change))
    self.assertEqual((p._document(),p.undo_stack,p.redo_stack),held)
   numeric(other,0,1)
   stale=deepcopy((p._document(),p.undo_stack,p.redo_stack))
   with self.assertRaises(ProjectError):apply(p,review_key=v['review_key'],**args)
   self.assertEqual((p._document(),p.undo_stack,p.redo_stack),stale)
   i=inspect(p,**ctx(),animation_id=selected['semantic_id'],frame_index=1,part_index=0);args=dict(ctx(),animation_id=selected['semantic_id'],frame_index=1,expected_current_block_sha256=i['current_block_sha256']);v=review(p,**args);comparison=proposed_pose(p,review_key=v['review_key'],**args)
   before=deepcopy(p._document());other_binding=deepcopy(p.monster_motion_overrides[other['semantic_id']]);models=deepcopy(p.monster_model_overrides);palettes=deepcopy(p.monster_palette_overrides);original,current=snapshot(p,**ctx())[2:4]
   start=selected['source_record']['byte_offset'];end=start+selected['source_record']['byte_length'];candidate=base64.b64decode(v['candidate_block_base64']);self.assertEqual(candidate[start:end],original[start:end]);self.assertEqual(candidate[:start],current[:start]);self.assertEqual(candidate[end:],current[end:]);self.assertEqual(candidate[start-0x8c:start],current[start-0x8c:start])
   retained={path(p,receipt[k+'_sha256'],suffix):path(p,receipt[k+'_sha256'],suffix).read_bytes() for k,suffix in [('glb','glb'),('source_motion','motion')]};self.assertEqual(len(input_records(p,catalog)),1)
   history=len(p.undo_stack);result=apply(p,review_key=v['review_key'],**args);self.assertEqual(result['removed_active_input_sha256'],receipt['glb_sha256']);self.assertEqual(len(p.undo_stack),history+1);self.assertNotIn(selected['semantic_id'],p.monster_motion_overrides);self.assertEqual(p.monster_motion_overrides[other['semantic_id']],other_binding);self.assertEqual(p.monster_model_overrides,models);self.assertEqual(p.monster_palette_overrides,palettes);self.assertEqual(input_records(p,catalog),[])
   for target,data in retained.items():self.assertEqual(target.read_bytes(),data)
   self.assertEqual(snapshot(p,**ctx())[3],candidate);after=deepcopy(p._document());p.undo();self.assertEqual(p._document(),before);self.assertEqual(len(input_records(p,catalog)),1);p.redo();self.assertEqual(p._document(),after);p.save();p=ProjectService.open(p.root);self.assertEqual(p._document(),after)
   with self.assertRaises(ProjectError):review(p,**dict(ctx(),animation_id=selected['semantic_id'],frame_index=1,expected_current_block_sha256=sha256(candidate).hexdigest()))
   p.import_metadata(import_scene(p.disc_path,'town01'));p.save();built=build_project(p);audit=json.loads(Path(built['audit']).read_text(encoding='utf-8'));overlays=[o for o in audit['overlays'] if o.get('source_kind')=='fixed_span_monster_slot'];self.assertEqual(len(overlays),1);overlay=overlays[0]
   with zipfile.ZipFile(built['path']) as package:
    payload=package.read(overlay['file']);self.assertEqual(decompress_lzs(payload,len(original))[0],candidate);self.assertEqual(payload,(Path(built['package_directory'])/overlay['file']).read_bytes())
   if os.getenv('LEGAIA_MONSTER_RESTORATION_CASES'):Path(os.environ['LEGAIA_MONSTER_RESTORATION_CASES']).write_text(json.dumps(dict(inspection=i,review=v,comparison=comparison,whole_stream_exact=True,neighbors_exact=True,other_owner_preservation=True,retained_glb_numeric=True,recovery_bytes_preserved=True,active_input_membership_removed=True,history=True,save_open=True,package_readback=True,package_sha256=built['sha256'],gameplay_verified=False)),encoding='utf-8')
