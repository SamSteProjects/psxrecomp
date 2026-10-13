"""Image/palette persistence, paired history and restoration composition."""
import os,tempfile,unittest,struct,json
from pathlib import Path
from copy import deepcopy
from sdk.project import ProjectService
from sdk.project_assets import source_key
from sdk.battle_character_resources import resources
from sdk.battle_pack_png_inputs import retain_import,validate,prepare
from sdk import battle_pack_palettes as palettes,battle_pack_palette_restoration as restore,battle_pack_model_authoring as models
from importer.pipeline import _disc_context
from importer.battle_pack_palettes import source,preview
from importer.export import _png


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
class PackImageOwnershipTests(unittest.TestCase):
 def test_pair_history_open_word_edit_palette_restore_and_model_context(self):
  with _disc_context(os.environ['LEGAIA_DISC_BIN']) as (_,disc,_,archive):original=archive.read_entry(archive.entry(1204))
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();catalog=resources(p,expected_project_path=str(p.root),expected_source_key=source_key(p))['catalog'];record=catalog['textures'][0];baseline=bytearray(source(original,catalog,record))
   for i in range(16):struct.pack_into('<H',baseline,20+i*2,0x8000+i+1)
   baseline=bytes(baseline);shown=preview(baseline,0);rgba=bytearray(shown['rgba']);i=((baseline[544]&15)+1)%16;r=i+1;rgba[:4]=bytes([r*8+r//4,0,0,255]);png=_png(256,256,bytes(rgba));mask=_png(256,256,b'\xff'*262144)
   image,candidate,_=retain_import(p,original,catalog,record,0,png,'existing',mask,baseline)
   retail=source(original,catalog,record);edits=[dict(palette_index=0,entry_index=i,word=0x8000+i+1) for i in range(16) if struct.unpack_from('<H',retail,20+i*2)[0]!=0x8000+i+1]
   from hashlib import sha256
   palette_only=candidate[:544]+retail[544:];owner=dict(schema_version='legaia.battle-pack-palette-override.v1',asset_id=record['semantic_id'],source_record=deepcopy(record['source_record']),edits=edits,current_tim_sha256=sha256(palette_only).hexdigest())
   before=dict(palettes={},images={});after=dict(palettes={record['semantic_id']:owner},images={record['semantic_id']:image});palettes.validate(p,after['palettes']);validate(p,after['images']);p.battle_pack_palette_overrides=deepcopy(after['palettes']);p.battle_pack_image_overrides=deepcopy(after['images']);p.undo_stack.append(dict(target='battle_pack_texture_state',before=before,after=deepcopy(after),label='Pack PNG'))
   p.undo();self.assertEqual(p.battle_pack_image_overrides,{});p.redo();p.save();p=ProjectService.open(p.root);self.assertEqual(p.battle_pack_image_overrides,after['images'])
   def ctx(rec):return dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=rec['semantic_id'],catalog_source_key=catalog['source_key'])
   current=palettes.inspect(p,palette_index=0,**ctx(record));self.assertEqual(current['current_tim_base64'],__import__('base64').b64encode(candidate).decode())
   args=dict(ctx(record),palette_index=0,entry_index=2,word=current['preview']['words'][2]^1,expected_current_tim_sha256=current['current_tim_sha256'],expected_current_entry_sha256=current['current_entry_sha256']);review=palettes.review(p,**args);palettes.apply(p,review_key=review['review_key'],**args)
   current=palettes.inspect(p,palette_index=0,**ctx(record));self.assertEqual(__import__('base64').b64decode(current['current_tim_base64'])[544:],candidate[544:])
   args=dict(ctx(record),palette_index=0,expected_current_tim_sha256=current['current_tim_sha256'],expected_current_entry_sha256=current['current_entry_sha256']);review=restore.review(p,**args);restore.apply(p,review_key=review['review_key'],**args);self.assertEqual(p.battle_pack_image_overrides,after['images']);self.assertEqual(p.battle_pack_palette_overrides,{})
   model=models.current(p,**ctx(catalog['models'][0]));
   if os.getenv('LEGAIA_PACK_IMAGE_CASES'):Path(os.environ['LEGAIA_PACK_IMAGE_CASES']).write_text(json.dumps(dict(model=model,report=dict(project_path=model['project_path'],project_source_key=model['project_source_key'],catalog=catalog,native_palette_context_required=True),record=dict(id=catalog['models'][0]['semantic_id'],data=catalog['models'][0],type='model'))),encoding='utf-8')
   self.assertEqual(model['palette_context']['image_owners'],after['images']);p.save();self.assertEqual(ProjectService.open(p.root)._document(),p._document())
   with _disc_context(p.disc_path) as (_,disc,_,archive):overlays,_=prepare(p,archive,disc)
   self.assertEqual(len(overlays),1);self.assertEqual(overlays[0]['payload'],candidate[544:]);self.assertEqual(overlays[0]['size'],32768)


if __name__=='__main__':unittest.main()
