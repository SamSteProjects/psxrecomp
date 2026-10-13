import os,tempfile,json,base64,struct,unittest,zipfile
from pathlib import Path
from copy import deepcopy
from sdk.project import ProjectService,ProjectError
from sdk.project_assets import source_key
from sdk.build import build_project
from importer.pipeline import import_scene
from importer.core import decompress_lzs
from test_model_primitive_workflow import http_server

@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
class MonsterPaletteTests(unittest.TestCase):
 def test_review_canonical_history_current_and_native_package(self):
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();asset='texture://legaia/monster-archive/0063/pool'
   def ctx():return dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=asset,palette_index=0)
   with http_server(p) as (_,post):
    status,inspection=post('/api/monster-palette-inspect',ctx());self.assertEqual(status,200,inspection);held=deepcopy((p._document(),p.undo_stack));word=inspection['preview']['words'][1]^1;args=dict(ctx(),entry_index=1,word=word,expected_current_sha256=inspection['current_pool_sha256']);status,r=post('/api/monster-palette-review',args);self.assertEqual(status,200,r);self.assertEqual((p._document(),p.undo_stack),held);before=base64.b64decode(r['current_pool_base64']);expected=bytearray(before);struct.pack_into('<H',expected,2,word);self.assertEqual(base64.b64decode(r['proposed_pool_base64']),bytes(expected));self.assertEqual(post('/api/monster-palette-apply',dict(args,review_key='0'*64))[0],400);status,v=post('/api/monster-palette-apply',dict(args,review_key=r['review_key']));self.assertEqual(status,200,v);self.assertEqual(len(p.undo_stack),1)
   after=deepcopy(p._document());p.undo();self.assertEqual(p._document(),held[0]);p.redo();p.save();p=ProjectService.open(p.root);self.assertEqual(p._document(),after)
   from sdk.monster_palettes import snapshot
   catalog,record,original,current,raw,used=snapshot(p,asset);at=record['source_record']['byte_offset']+2;changed=bytearray(original);struct.pack_into('<H',changed,at,word);self.assertEqual(current,bytes(changed))
   with http_server(p) as (_,post):
    args=dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id='asset://legaia/models/monster-archive/0063',catalog_source_key=catalog['source_key']);status,retail=post('/api/monster-preview',args);self.assertEqual(status,200,retail);status,preview=post('/api/monster-current-preview',args);self.assertEqual(status,200,preview);self.assertEqual(preview['source_tmd_base64'],retail['source_tmd_base64']);self.assertNotEqual(preview['source_pool_base64'],retail['source_pool_base64']);self.assertEqual(preview['layer'],'current_palette')
   p.import_metadata(import_scene(p.disc_path,'town01'));p.save();built=build_project(p);audit=json.loads(Path(built['audit']).read_text(encoding='utf-8'))
   with zipfile.ZipFile(built['path']) as package:
    overlay=next(o for o in audit['overlays'] if o.get('source_kind')=='fixed_span_monster_palette');payload=package.read(overlay['file']);self.assertEqual(len(payload),used);self.assertEqual(decompress_lzs(payload,len(original))[0],current);self.assertEqual((Path(built['package_directory'])/overlay['file']).read_bytes(),payload)
   invalid=deepcopy(p.monster_palette_overrides);invalid[asset]['current_pool_sha256']='0'*64
   from sdk.monster_palettes import validate
   with self.assertRaises(ProjectError):validate(p,invalid)
   if os.getenv('LEGAIA_MONSTER_PALETTE_CASES'):Path(os.environ['LEGAIA_MONSTER_PALETTE_CASES']).write_text(json.dumps(dict(inspection=inspection,review=r,retail=retail,current=preview,history=True,save_open=True,protected_block_bytes=True,package_readback=True,package_sha256=built['sha256'],gameplay_verified=False)),encoding='utf-8')
