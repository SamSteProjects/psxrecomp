from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.worldmap_texture_uses import inspect

class WorldTextureUsesTests(TestCase):
 def test_retail_current_union_read_only_and_stale_refusal(self):
  identifier='texture://map01/kingdom/0000';other='texture://map01/kingdom/0001'
  preview=dict(materials=[dict(textured=True,tpage=0,clut=0)]*3,textures=[dict(status='address_match',source_ids=[identifier]),dict(status='missing',source_ids=[]),dict(status='address_match',source_ids=[other])])
  geometry=dict(scene='map01',source_record=dict(disc_sha256='a'*64),scene_graph=dict(assets=[dict(asset_id='asset://map01/worldmap/walk-ground',preview=preview)],entities=[dict(entity_id='scene://map01/worldmap/ground',asset_id='asset://map01/worldmap/walk-ground')]))
  def compose(project,value):
   value['scene_graph']['assets'][0]['preview']['textures']=[dict(status='ambiguous',source_ids=[identifier,other],reason='Conflicting samples'),dict(status='address_match',source_ids=[identifier]),dict(status='address_match',source_ids=[other])];return value
  with TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path='fixture';held=deepcopy(p._document());request=dict(texture_id=identifier,source_key='b'*64,member_sha256='c'*64,effective_sha256='d'*64)
   ctx=SimpleNamespace(_source=lambda _:dict(disc=dict(sha256='a'*64)))
   with patch('sdk.worldmap_texture_uses.state_key',return_value='b'*64),patch('sdk.worldmap_texture_uses._inspected_current',return_value=(ctx,b'',b'')),patch('sdk.worldmap_texture_uses.load_worldmap_geometry',return_value=geometry),patch('sdk.worldmap_texture_uses.compose',side_effect=compose):
    result=inspect(p,request);self.assertEqual([m['material_index'] for m in result['assets'][0]['materials']],[0,1]);self.assertEqual(result['assets'][0]['materials'][0]['current']['status'],'ambiguous');self.assertEqual(result['assets'][0]['source_instance_ids'],['scene://map01/worldmap/ground']);self.assertEqual(p._document(),held);self.assertEqual(geometry['scene_graph']['assets'][0]['preview']['textures'],preview['textures']);self.assertNotIn('rgba',str(result))
    for field,value in [('source_key','0'*64),('texture_id','foreign'),('member_sha256','bad'),('extra',0)]:
     with self.subTest(field=field),self.assertRaises(ProjectError):inspect(p,{**request,field:value})
    p.mode='live'
    with self.assertRaises(ProjectError):inspect(p,request)
    p.mode='edit'
    with patch('sdk.worldmap_texture_uses.state_key',side_effect=['b'*64,'0'*64]),self.assertRaises(ProjectError):inspect(p,request)
