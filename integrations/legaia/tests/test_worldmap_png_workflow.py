from contextlib import nullcontext
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
from importer.texture_authoring import _validate
from importer.texture_png import decode_png
from sdk.project import ProjectService,ProjectError
from sdk.texture_png import export_texture,preview_import,apply_import
from sdk.worldmap_authoring import state_key
from test_texture_png_workflow import png_rgba
from test_importer_textures import tim,block

class WorldPngWorkflow(TestCase):
 def test_global_ownership_empty_project_history_and_stale_binding(self):
  original=tim(image=block(0,0,1,1,[0x3210]));identifier='texture://map01/kingdom/0000';ctx=SimpleNamespace(options=lambda _:dict(supported=True),original_tim=lambda _:original,validate_replacement=lambda _,value:_validate(original,value),_source=lambda _:dict(disc=dict(sha256='a'*64)))
  with TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=str(Path(root)/'fixture.bin');Path(p.disc_path).write_bytes(b'fixture')
   with patch.object(p,'_texture_context',return_value=ctx),patch('importer.pipeline._disc_context',side_effect=lambda _:nullcontext()):
    held=deepcopy(p._document());png,stp,binding,report=export_texture(p,identifier,0);self.assertEqual(p._document(),held);self.assertEqual(binding['scene_id'],'worldmap://map01/textures');self.assertEqual(binding['project_source_key'],state_key(p));self.assertIsNone(p.active_scene)
    image=decode_png(png);rgba=bytearray(image['rgba']);rgba[4:8]=bytes([0,255,0,255]);edited=png_rgba(image['width'],image['height'],rgba);review=preview_import(p,identifier,edited,binding,'existing',stp);self.assertEqual(review['pending_changes']['pixel_indices_changed'],1);self.assertEqual(p._document(),held)
    with self.assertRaises(ProjectError):apply_import(p,identifier,edited,binding,'existing',stp,'0'*64)
    apply_import(p,identifier,edited,binding,'existing',stp,review['review_key']);self.assertEqual(p.read_texture_replacement(p.texture_overrides[identifier]),original[:-2]+b'\x20\x32')
    with self.assertRaises(ProjectError):preview_import(p,identifier,edited,binding,'existing',stp)
    p.undo();self.assertEqual(p.texture_overrides,{})
    p.redo();reopened=ProjectService.open(p.save());self.assertEqual(reopened.texture_overrides,p.texture_overrides)
