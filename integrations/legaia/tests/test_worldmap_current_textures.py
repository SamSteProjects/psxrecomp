from pathlib import Path
from copy import deepcopy
from hashlib import sha256
from types import SimpleNamespace
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
import struct
from importer.textures import TextureCatalog,parse_tim
from importer.texture_authoring import _validate
from sdk.project import ProjectService,ProjectError
from sdk.worldmap_current_textures import compose
from test_worldmap_texture import fixture

class CurrentWorldTextureTests(TestCase):
 def test_literal_pixels_and_unchanged_geometry_provenance(self):
  tim,_,_=fixture();raw=struct.pack('<II',16,8)+struct.pack('<IHHHH',12+len(tim.clut.data),0,1,32,1)+tim.clut.data+struct.pack('<IHHHH',14,0,0,1,1)+tim.image.data
  changed=bytearray(raw);struct.pack_into('<H',changed,22,0x7fff);changed=bytes(changed);identifier='texture://map01/kingdom/0000';catalog=TextureCatalog('map01','a'*64);catalog.textures=[(parse_tim(raw),dict(semantic_id=identifier))]
  preview=dict(vertices=[[0,0,0],[1,0,0],[0,0,1]],triangles=[[0,1,2]],triangle_materials=[0],triangle_uvs=[[[0,0],[3,0],[0,0]]],materials=[dict(textured=True,tpage=0,clut=64)],textures=[dict(status='address_match',material_index=0,rgba=b'retail',stp=b'0000')])
  geometry=dict(scene='map01',source_record=dict(disc_sha256='a'*64,map_sha256='b'*64),preview=preview,metrics=dict(texture_output_bytes=10,matched_texture_count=1,unsupported_texture_count=0),scene_graph=dict(assets=[dict(asset_id='ground',preview=preview),dict(asset_id='model',preview=deepcopy(preview))],entities=[dict(entity_id='native')],metrics=dict(texture_output_bytes=20)))
  before=deepcopy(geometry)
  with TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path='fixture';p.texture_overrides[identifier]=dict(source_scene_id='worldmap://map01/textures',format='tim',asset_sha256=sha256(changed).hexdigest(),source_sha256=sha256(raw).hexdigest(),source_disc_sha256='a'*64,byte_length=len(changed))
   ctx=SimpleNamespace(_digest='a'*64,_catalog=catalog,original_tim=lambda _:raw,validate_replacement=lambda _,value:_validate(raw,value))
   with patch('sdk.worldmap_current_textures.context',return_value=ctx),patch.object(p,'read_texture_replacement',return_value=changed):
    result=compose(p,geometry)
    for asset in result['scene_graph']['assets']:
     self.assertEqual(asset['preview']['textures'][0]['rgba'],bytes([0,0,0,0,255,255,255,255,0,255,0,255,0,0,255,255]))
    self.assertEqual(result['scene_graph']['metrics']['texture_output_bytes'],40)
    self.assertEqual(result['source_record'],before['source_record']);self.assertEqual(result['scene_graph']['entities'],before['scene_graph']['entities'])
    for asset,old in zip(result['scene_graph']['assets'],before['scene_graph']['assets']):
     self.assertEqual({k:v for k,v in asset['preview'].items() if k!='textures'},{k:v for k,v in old['preview'].items() if k!='textures'})
    p.texture_overrides[identifier]['source_sha256']='0'*64
    with self.assertRaises(ProjectError):compose(p,deepcopy(before))
 def test_no_overrides_preserve_retail_pixels(self):
  with TemporaryDirectory() as root:
   p=ProjectService(Path(root));geometry=dict(scene='map01',source_record=dict(disc_sha256='a'*64),scene_graph=dict(metrics=dict(texture_output_bytes=0)))
   with patch('sdk.worldmap_current_textures.context',side_effect=AssertionError('no native reread needed')):compose(p,geometry)
   self.assertEqual(geometry['texture_authoring']['edits'],[])
