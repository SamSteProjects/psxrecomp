"""Retail-gated normal Build regression for compressed and raw animation banks."""
import os,tempfile,unittest,zipfile,json
from pathlib import Path
from importer.pipeline import _disc_context,import_scene
from importer.scene_animation import load_scene_actor_animation_catalog
from importer.core import decompress_lzs
from sdk.project import ProjectService
from sdk.build import build_project

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class NormalAnimationBuild(unittest.TestCase):
 def test_existing_channel_serializes_exact_bank_for_both_source_layouts(self):
  for scene,index,extension in [('town01',11,'lzs'),('dolk2',1,'bin')]:
   with self.subTest(scene=scene),tempfile.TemporaryDirectory() as directory,_disc_context(os.environ['LEGAIA_DISC_BIN']):
    p=ProjectService(Path(directory));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.import_metadata(import_scene(p.disc_path,scene));owner=f'scene://{scene}/actors/man-p1/{index:04d}'
    options=p.animation_authoring_options(owner);binding=options['binding'];values=p.animation_channel_values(owner,0,0);value=values['retail']['translation']['x']^1
    catalog=load_scene_actor_animation_catalog(p.disc_path,scene);expected=bytearray(catalog._body);expected[binding['source_record']['byte_offset']+8]^=1
    p.command(dict(type='set_animation_channels',entity_id=owner,value=dict(animation_id=binding['semantic_id'],source_record_sha256=binding['source_record']['record_sha256'],edits=[dict(frame_index=0,object_index=0,translation={'x':value})])))
    output=build_project(p)
    with zipfile.ZipFile(output['path']) as archive:
     payload=archive.read(f'assets/{scene}-animation.{extension}');actual=decompress_lzs(payload,len(expected))[0] if extension=='lzs' else payload
     self.assertEqual(actual,bytes(expected))
    overlay=next(row for row in json.loads(Path(output['audit']).read_text())['overlays'] if row['file'].endswith(f'-animation.{extension}'))
    if extension=='bin':
     self.assertEqual(overlay['source_kind'],'raw_streaming_anm');self.assertNotIn('decoded_after_sha256',overlay)
    else:self.assertIn('decoded_after_sha256',overlay)
