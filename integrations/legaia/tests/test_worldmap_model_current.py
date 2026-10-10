from pathlib import Path
from copy import deepcopy
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from hashlib import sha256
import struct,base64,json
from test_importer_assets import model
from importer.model_json import export_shape_json
from sdk.project import ProjectService,ProjectError
from sdk.worldmap_model_source import inspect

class WorldModelCurrentTests(TestCase):
 def test_layers_exact_vectors_and_no_project_mutation(self):
  original=model(0x22);candidate=bytearray(original);at=12+struct.unpack_from('<I',original,12)[0];struct.pack_into('<h',candidate,at,struct.unpack_from('<h',original,at)[0]+1);candidate=bytes(candidate);identifier='asset://map01/worldmap/models/0000';native=dict(disc_sha256='a'*64,decoded_member_sha256=sha256(original).hexdigest())
  with TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path='fixture'
   with patch('sdk.worldmap_model_binding.source',return_value=(original,native)),patch('sdk.worldmap_model_source.read_worldmap_model',return_value=(original,export_shape_json(original),native)),patch('sdk.worldmap_model_source.state_key',return_value='b'*64):
    p.set_model_replacement(identifier,candidate);held=deepcopy(p._document());history=deepcopy(p.undo_stack);request=dict(asset_id=identifier,source_key='b'*64,member_sha256=sha256(original).hexdigest())
    for layer,expected in [('retail',original),('current',candidate)]:
     value=inspect(p,{**request,'layer':layer});self.assertEqual(value['schema_version'],'legaia.worldmap-model-source.v2');self.assertEqual(base64.b64decode(value['tmd_base64']),expected);self.assertEqual(base64.b64decode(value['retail_tmd_base64']),original);self.assertEqual(value['effective_tmd_sha256'],sha256(candidate).hexdigest());self.assertTrue(value['authored']);self.assertEqual(base64.b64decode(value['shape_base64']),export_shape_json(expected));self.assertEqual(p._document(),held);self.assertEqual(p.undo_stack,history)
    self.assertEqual(inspect(p,request)['schema_version'],'legaia.worldmap-model-source.v1')
    for extra in [{'layer':'live'},{'layer':None},{'layer':'current','extra':1}]:
     with self.subTest(extra=extra),self.assertRaises(ProjectError):inspect(p,{**request,**extra})
    p.undo();value=inspect(p,{**request,'layer':'current'});self.assertFalse(value['authored']);self.assertEqual(value['tmd_sha256'],request['member_sha256'])
