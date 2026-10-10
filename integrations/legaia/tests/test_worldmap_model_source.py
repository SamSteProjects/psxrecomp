from pathlib import Path
from copy import deepcopy
from tempfile import TemporaryDirectory
from hashlib import sha256
from unittest import TestCase
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.worldmap_model_source import inspect
from importer.model_json import export_shape_json
from test_importer_assets import model

class WorldModelSourceTests(TestCase):
 def test_immutable_exact_source_and_refusal(self):
  content=model(0x22);shape=export_shape_json(content);identifier='asset://map01/worldmap/models/0000';source=dict(disc_sha256='a'*64,decoded_member_sha256=sha256(content).hexdigest())
  with TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path='fixture';held=deepcopy(p._document());request=dict(asset_id=identifier,source_key='b'*64,member_sha256=source['decoded_member_sha256'])
   with patch('sdk.worldmap_model_source.state_key',return_value='b'*64),patch('sdk.worldmap_model_source.read_worldmap_model',return_value=(content,shape,source)):
    result=inspect(p,request);self.assertEqual(result['tmd_byte_length'],len(content));self.assertEqual(result['shape_sha256'],sha256(shape).hexdigest());self.assertEqual(p._document(),held);self.assertEqual(p.undo_stack,[])
    for field,value in [('source_key','0'*64),('asset_id','asset://map01/worldmap/walk-ground'),('member_sha256','0'*64),('extra',1)]:
     with self.subTest(field=field),self.assertRaises(ProjectError):inspect(p,{**request,field:value})
    p.mode='live'
    with self.assertRaises(ProjectError):inspect(p,request)
    p.mode='edit'
    with patch('sdk.worldmap_model_source.state_key',side_effect=['b'*64,'0'*64]),self.assertRaises(ProjectError):inspect(p,request)
    p.imports={'other':{'source':{'disc_identity':'sha256:'+'0'*64}}}
    with self.assertRaises(ProjectError):inspect(p,request)

 def test_native_pack_source_adapter_and_container_refusal(self):
  from contextlib import contextmanager
  from types import SimpleNamespace
  from importer.worldmap_model_authoring import read_worldmap_model
  from importer.core import ImportError
  import struct
  content=model(0x22);pack=struct.pack('<II',1,2)+content;source=dict(slot_index=1)
  @contextmanager
  def context(disc):yield None,'a'*64,None,None
  bundle=SimpleNamespace(table_offset=0)
  with patch('importer.worldmap_model_authoring._disc_context',side_effect=context),patch('importer.worldmap_model_authoring._bounded_scene_range',return_value=(83,100)),patch('importer.worldmap_model_authoring._kingdom_table',return_value=(0,86,0,bundle,b'')),patch('importer.worldmap_model_authoring._slot',return_value=(pack,source)):
   result,shape,record=read_worldmap_model('fixture','asset://map01/worldmap/models/0000');self.assertEqual(result,content);self.assertEqual(shape,export_shape_json(content));self.assertEqual(record['decoded_member_offset'],8);self.assertEqual(record['decoded_member_sha256'],sha256(content).hexdigest())
   with self.assertRaises(ImportError):read_worldmap_model('fixture','asset://map01/worldmap/models/0001')
   bundle.table_offset=4
   with self.assertRaises(ImportError):read_worldmap_model('fixture','asset://map01/worldmap/models/0000')
