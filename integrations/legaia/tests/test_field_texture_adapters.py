import os,struct,tempfile,unittest,time,json,base64
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from importer.pipeline import import_scene
from importer.textures import parse_tim
from importer.assets import load_model_preview
from sdk.project import ProjectService
from sdk.server import EditorServer
from sdk.scene_preview import preview_project
from sdk.model_glb import _texture_preview

@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
class FieldTextureAdapterTests(unittest.TestCase):
 def test_general_model_and_glb_current_retail_composition(self):
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.import_metadata(import_scene(p.disc_path,'town01'));p.save()
   for slot in range(8):
    identifier=f'texture://legaia/field-party/874/2/{slot}';ctx=p._texture_context(identifier);source=ctx.original_tim(identifier);tim=parse_tim(source);candidate=bytearray(source);candidate[20:20+len(tim.clut.data)]=struct.pack('<H',0x03e0)*(len(tim.clut.data)//2);p.set_texture_replacement(identifier,bytes(candidate))
   held=deepcopy((p._document(),p.undo_stack));server=EditorServer(('127.0.0.1',0),p,runtime_port=65533);proof=[]
   try:
    for slot in range(3):
     asset=p.assets.records[f'asset://legaia/models/global-special/{240+slot:04x}'];start=time.perf_counter()
     # Field routes must not load an unrelated scene TIM bank.
     with patch('importer.textures.load_scene_texture_catalog',side_effect=AssertionError('Unrelated scene bank loaded')):
      current=server.model_preview(asset);retail=server.model_preview(asset,project_view=preview_project(p,'retail'));glb=_texture_preview(p,asset,load_model_preview(p.disc_path,asset))
     self.assertEqual(current['texture_layer'],'current');self.assertEqual(retail['texture_layer'],'retail');self.assertEqual(len(current['texture_bindings']),8);self.assertFalse(retail['texture_bindings']);self.assertEqual(current['textures'],glb['textures']);self.assertNotEqual(current['textures'],retail['textures']);pixels=0
     for t in current['textures']:
      if t['status']!='address_match':continue
      rgba=base64.b64decode(t['rgba_base64']);self.assertEqual(set(tuple(rgba[i:i+4]) for i in range(0,len(rgba),4)),{(0,255,0,255)});pixels+=len(rgba)//4
     proof.append(dict(slot=slot,current_pixels=pixels,adapter_seconds=time.perf_counter()-start,scene_bank_skipped=True))
    self.assertEqual((p._document(),p.undo_stack),held)
   finally:server.server_close()
   if os.getenv('LEGAIA_FIELD_ADAPTER_PROOF'):Path(os.environ['LEGAIA_FIELD_ADAPTER_PROOF']).write_text(json.dumps(dict(models=proof,retail_current_separate=True,glb_scene_adapter_match=True,unchanged=True,gameplay_verified=False),indent=2),encoding='utf-8')
