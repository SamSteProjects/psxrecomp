import base64,json,os,struct,tempfile,unittest,zipfile
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from importer.monster_record_authoring import FIELDS,patch,header_values
from importer.core import ImportError as NativeError
from sdk.monster_records import compose
from sdk.project import ProjectService,ProjectError


def literal_record(data):
 stats=('hp','agility','mp','attack','defense_high','defense_low','intelligence','speed')
 return dict(semantic_id='monster-record://legaia/867/0001',asset_kind='monster_record',monster_id=1,
  stored_stats={name:data[12+i*2]+data[13+i*2]*256 for i,name in enumerate(stats)},stored_rewards=dict(gold=data[68]+data[69]*256,experience=data[70]+data[71]*256,drop_item=data[72],drop_chance=data[73]),
  source_record=dict(byte_offset=0,byte_length=76,containing_size=len(data),sha256=sha256(data[:76]).hexdigest()))


class MonsterRecordCodecTests(unittest.TestCase):
 def test_literal_all_widths_endian_limits_and_complete_neighbors(self):
  original=bytes(range(200));record=literal_record(original)
  requested=dict(zip(('stored_stats.hp','stored_stats.agility','stored_stats.mp','stored_stats.attack','stored_stats.defense_high','stored_stats.defense_low','stored_stats.intelligence','stored_stats.speed'),(0x1234,0x5678,0x9abc,0xdef0,0xffff,0,0x01fe,0xfe01)))
  requested.update({'stored_rewards.gold':0xabcd,'stored_rewards.experience':0xef01,'stored_rewards.drop_item':255,'stored_rewards.drop_chance':0})
  candidate,audit=patch(original,original,record,requested);expected=bytearray(original);expected[12:28]=bytes.fromhex('34127856bc9af0deffff0000fe0101fe');expected[68:74]=bytes.fromhex('cdab01efff00');self.assertEqual(candidate,bytes(expected));self.assertEqual(len(audit),12)
  for row in audit:self.assertEqual(row['byte_width'],1 if row['field'].endswith(('drop_item','drop_chance')) else 2)
  self.assertEqual(header_values(candidate),requested);self.assertEqual(candidate[:12],original[:12]);self.assertEqual(candidate[28:68],original[28:68]);self.assertEqual(candidate[74:],original[74:])
  for values in ({},{'element_byte':1},{'stored_stats.hp':-1},{'stored_stats.hp':65536},{'stored_rewards.drop_item':256},{'stored_rewards.drop_chance':-1},{'stored_stats.hp':True},{'stored_stats.hp':1.5}):
   with self.assertRaises(NativeError):patch(original,original,record,values)
  for changes in (None,dict(record,stored_stats={}),dict(record,source_record=dict(record['source_record'],sha256='0'*64))):
   with self.assertRaises(NativeError):patch(original,original,changes,requested)
  self.assertEqual(patch(original,original,record,header_values(original))[1],[])

 def test_sparse_canonical_owner_duplicate_unknown_and_protected_header_refusal(self):
  original=bytes(range(200));record=literal_record(original);values={'stored_stats.hp':65535,'stored_rewards.drop_chance':255};candidate,_=patch(original,original,record,values)
  binding=dict(schema_version='legaia.monster-record-override.v1',asset_id=record['semantic_id'],source_record=record['source_record'],edits=[dict(field=k,value=v) for k,v in sorted(values.items())],current_header_sha256=sha256(candidate[:76]).hexdigest());catalog=dict(records=[record]);self.assertEqual(compose(original,catalog,1,{record['semantic_id']:binding}),candidate)
  current=original[:100]+b'authored-neighbor'+original[117:];self.assertEqual(len(current),len(original));mixed=compose(original,catalog,1,{record['semantic_id']:binding},current);self.assertEqual(mixed[76:],current[76:]);self.assertEqual(mixed[:76],candidate[:76])
  for mutate in (lambda b:b['edits'].append(deepcopy(b['edits'][0])),lambda b:b['edits'].reverse(),lambda b:b['edits'][0].update(field='element_byte'),lambda b:b['edits'][0].update(value=True),lambda b:b.update(current_header_sha256='0'*64),lambda b:b.update(source_record={})):
   bad=deepcopy(binding);mutate(bad)
   with self.assertRaises(ProjectError):compose(original,catalog,1,{record['semantic_id']:bad})
  unknown=bytearray(current);unknown[29]^=1
  with self.assertRaises(ProjectError):compose(original,catalog,1,{record['semantic_id']:binding},bytes(unknown))


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Private Retail source is required')
class MonsterRecordWorkflowTests(unittest.TestCase):
 def test_subset_history_model_after_record_png_motion_restore_and_package(self):
  from sdk.project_assets import source_key
  from sdk.monster_archive import resources
  from sdk.monster_record_authoring import inspect,review,apply
  from sdk.monster_model_authoring import export as model_export,review as model_review,apply as model_apply,snapshot
  from sdk.monster_models import read as model_read
  from sdk.monster_png import download as png_download,review as png_review,apply as png_apply,validate_input as png_replay
  from sdk.monster_palettes import inspect as palette_inspect
  from sdk.monster_motion_authoring import inspect as motion_inspect,review as motion_review,apply as motion_apply
  from sdk.build import build_project
  from importer.pipeline import import_scene
  from importer.texture_png import decode_png,_encode_png
  from importer.core import decompress_lzs
  from test_monster_model_authoring import shifted_glb
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();model='asset://legaia/models/monster-archive/0063';catalog=resources(p,expected_project_path=str(p.root),expected_source_key=source_key(p))['catalog']
   def ctx():return dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=model,catalog_source_key=catalog['source_key'])
   i=inspect(p,**ctx());values={'stored_stats.hp':i['current_values']['stored_stats.hp']+1,'stored_rewards.gold':i['current_values']['stored_rewards.gold']+2};args=dict(ctx(),expected_current_block_sha256=i['current_block_sha256'],values=values);v=review(p,**args);held=deepcopy((p._document(),p.undo_stack,p.redo_stack));self.assertEqual((p._document(),p.undo_stack,p.redo_stack),held)
   for changed in ({'review_key':'0'*64},{'review_key':v['review_key'],'expected_current_block_sha256':'0'*64}):
    with self.assertRaises(ProjectError):apply(p,**dict(args,**changed))
    self.assertEqual((p._document(),p.undo_stack,p.redo_stack),held)
   apply(p,review_key=v['review_key'],**args);self.assertEqual(len(p.undo_stack),1);after=deepcopy(p._document());p.undo();self.assertEqual(p._document(),held[0]);p.redo();p.save();p=ProjectService.open(p.root);self.assertEqual(p._document(),after)
   current=inspect(p,**ctx());self.assertEqual(current['current_values']['stored_stats.hp'],values['stored_stats.hp']);self.assertEqual(len(current['binding']['edits']),2)
   with self.assertRaises(ProjectError):review(p,**dict(ctx(),expected_current_block_sha256=current['current_block_sha256'],values=current['current_values']))
   exported=model_export(p,**ctx());margs=dict(ctx(),binding=exported['binding'],glb_base64=base64.b64encode(shifted_glb(base64.b64decode(exported['glb_base64']))).decode());mv=model_review(p,**margs);model_apply(p,review_key=mv['review_key'],**margs)
   record,texture,original,_,_,_=snapshot(p,**ctx());receipt=p.monster_model_overrides[model]['inputs'][-1];baseline=model_read(p,receipt['baseline_sha256'],receipt['baseline_byte_length'],'block');self.assertEqual(baseline[:76],original[:76])
   asset='texture://legaia/monster-archive/0063/pool';tctx=dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=asset,palette_index=0);pi=palette_inspect(p,**tctx);pa=dict(tctx,expected_current_sha256=pi['current_pool_sha256']);download=png_download(p,**pa);image=decode_png(base64.b64decode(download['png_base64']));rgba=bytearray(image['rgba']);rgba[:4]=bytes([0,255,0,255]);png=_encode_png(image['width'],image['height'],bytes(rgba));pa.update(png_base64=base64.b64encode(png).decode(),stp_base64=None,palette_mode='rebuild');pv=png_review(p,**pa);png_apply(p,review_key=pv['review_key'],**pa)
   clip=next(c for c in catalog['animations'] if c['model_asset_id']==model and c['preview_supported']);mi=motion_inspect(p,**ctx(),animation_id=clip['semantic_id'],frame_index=0,part_index=0);t=mi['channels']['translation'].copy();t[0]+=1;ma=dict(ctx(),animation_id=clip['semantic_id'],frame_index=0,part_index=0,expected_current_block_sha256=mi['current_block_sha256'],translation=t,rotation_psx=mi['channels']['rotation_psx']);mr=motion_review(p,**ma);motion_apply(p,review_key=mr['review_key'],**ma)
   p.save();p=ProjectService.open(p.root);other_ctx=dict(ctx(),asset_id='asset://legaia/models/monster-archive/0062');oi=inspect(p,**other_ctx);other_args=dict(other_ctx,expected_current_block_sha256=oi['current_block_sha256'],values={'stored_stats.hp':oi['current_values']['stored_stats.hp']+1});ov=review(p,**other_args);apply(p,review_key=ov['review_key'],**other_args);other_records={oi['record']['semantic_id']:deepcopy(p.monster_record_overrides[oi['record']['semantic_id']])};current=inspect(p,**ctx());self.assertEqual(current['current_values']['stored_rewards.gold'],values['stored_rewards.gold']);model_owner=deepcopy(p.monster_model_overrides);palette_owner=deepcopy(p.monster_palette_overrides);motion_owner=deepcopy(p.monster_motion_overrides);before=snapshot(p,**ctx())[3]
   stale=dict(ctx(),expected_current_block_sha256=i['current_block_sha256'],values={'stored_stats.mp':1})
   with self.assertRaises(ProjectError):review(p,**stale)
   restore_args=dict(ctx(),expected_current_block_sha256=current['current_block_sha256'],values=current['retail_values']);restoration=review(p,**restore_args);self.assertIsNone(restoration['binding']);count=len(p.undo_stack);apply(p,review_key=restoration['review_key'],**restore_args);self.assertEqual(len(p.undo_stack),count+1);self.assertEqual(p.monster_record_overrides,other_records);self.assertEqual(p.monster_model_overrides,model_owner);self.assertEqual(p.monster_palette_overrides,palette_owner);self.assertEqual(p.monster_motion_overrides,motion_owner)
   after=snapshot(p,**ctx())[3];self.assertEqual(after[:76],original[:76]);self.assertEqual(after[76:],before[76:]);self.assertEqual(png_replay(p,texture,p.monster_palette_overrides[asset]['png_import'])[0],png)
   p.undo();self.assertTrue(p.monster_record_overrides);p.redo();p.save();p=ProjectService.open(p.root);self.assertEqual(snapshot(p,**ctx())[3],after)
   # Reapply one field after other owners, proving both authored and restored
   # headers survive complete native directory/ZIP package composition.
   restored=inspect(p,**ctx());aa=dict(ctx(),expected_current_block_sha256=restored['current_block_sha256'],values={'stored_rewards.drop_chance':(restored['current_values']['stored_rewards.drop_chance']+1)%256});av=review(p,**aa);apply(p,review_key=av['review_key'],**aa);final=snapshot(p,**ctx())[3];self.assertEqual(final[76:],after[76:]);other_final=snapshot(p,**dict(ctx(),asset_id='asset://legaia/models/monster-archive/0062'))[3];p.import_metadata(import_scene(p.disc_path,'town01'));p.save();built=build_project(p);audit=json.loads(Path(built['audit']).read_text(encoding='utf-8'));overlays=[o for o in audit['overlays'] if o.get('source_kind')=='fixed_span_monster_slot'];self.assertEqual(len(overlays),2)
   with zipfile.ZipFile(built['path']) as package:
    for overlay in overlays:
     target=final if overlay['source_record']['monster_id']==63 else other_final;payload=package.read(overlay['file']);self.assertEqual(decompress_lzs(payload,len(target))[0],target);self.assertEqual(payload,(Path(built['package_directory'])/overlay['file']).read_bytes())
   self.assertEqual(ProjectService.open(p.root)._document(),p._document())
   if os.getenv('LEGAIA_MONSTER_RECORD_CASES'):Path(os.environ['LEGAIA_MONSTER_RECORD_CASES']).write_text(json.dumps(dict(inspection=i,review=v,requested=values,current_inspection=current,restoration=restoration,restore_values=restore_args['values'],subset=True,history=True,save_open=True,model_after_record=True,retail_model_header_baseline=True,png_motion_coexistence=True,restore_preserves_other_owners=True,other_record_owner_preserved=True,two_slot_package_exact=True,package_readback=True,package_sha256=built['sha256'],gameplay_verified=False)),encoding='utf-8')
