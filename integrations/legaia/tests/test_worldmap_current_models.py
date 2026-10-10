from pathlib import Path
from copy import deepcopy
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from hashlib import sha256
import struct
from test_importer_assets import model
from importer.assets import decode_tmd
from sdk.project import ProjectService,ProjectError
from sdk.worldmap_current_models import compose

class CurrentWorldModelTests(TestCase):
 def test_literal_shape_history_and_immutable_scene_ownership(self):
  original=model(0x22);candidate=bytearray(original);at=12+struct.unpack_from('<I',original,12)[0];struct.pack_into('<h',candidate,at,123);candidate=bytes(candidate)
  identifier='asset://map01/worldmap/models/0000';native=dict(disc_sha256='a'*64,decoded_member_sha256=sha256(original).hexdigest());preview=decode_tmd(original);preview['textures']=[]
  geometry=dict(scene='map01',source_record=dict(disc_sha256='a'*64),preview=dict(vertices=['ground']),scene_graph=dict(assets=[dict(asset_id=identifier,source_record=deepcopy(native),preview=preview)],entities=[dict(entity_id='seed',source_to_world=[1]*16)]))
  before=deepcopy(geometry)
  with TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path='fixture'
   with patch('sdk.worldmap_model_binding.source',return_value=(original,native)),patch('sdk.worldmap_current_models.source',return_value=(original,native)):
    p.set_model_replacement(identifier,candidate);document=deepcopy(p._document());history=deepcopy(p.undo_stack)
    result=compose(p,deepcopy(geometry));actual=result['scene_graph']['assets'][0]['preview']
    self.assertEqual(actual['vertices'],decode_tmd(candidate)['vertices']);self.assertEqual(actual['triangle_normals'],decode_tmd(candidate)['triangle_normals'])
    for key in ('triangles','triangle_colors','triangle_uvs','triangle_materials','materials','textures'):self.assertEqual(actual[key],preview[key])
    self.assertEqual(result['preview'],before['preview']);self.assertEqual(result['scene_graph']['entities'],before['scene_graph']['entities']);self.assertEqual(result['scene_graph']['assets'][0]['source_record'],native)
    self.assertEqual(result['model_authoring']['edits'][0]['effective_tmd_sha256'],sha256(candidate).hexdigest());self.assertEqual(p._document(),document);self.assertEqual(p.undo_stack,history)
    bad=deepcopy(geometry);bad['scene_graph']['assets'][0]['source_record']['disc_sha256']='b'*64;held=deepcopy(bad)
    with self.assertRaises(ProjectError):compose(p,bad)
    self.assertEqual(bad,held)
    p.undo();self.assertEqual(compose(p,deepcopy(geometry))['model_authoring']['edits'],[])


 def test_allocated_current_preview_and_versioned_source_preserve_retail(self):
  import base64
  from importer.model_face_ledger import create_face_ledger,append_vector_ledger
  from importer.model_json import export_shape_json
  from sdk.worldmap_model_source import inspect
  from sdk.worldmap_authoring import state_key
  original=model(0x22);identifier='asset://map01/worldmap/models/0000'
  native=dict(disc_sha256='a'*64,decoded_member_sha256=sha256(original).hexdigest())
  preview=decode_tmd(original);preview['textures']=[]
  geometry=dict(scene='map01',source_record=dict(disc_sha256='a'*64),preview=dict(vertices=['ground']),scene_graph=dict(assets=[dict(asset_id=identifier,source_record=deepcopy(native),preview=preview)],entities=[dict(entity_id='seed',source_to_world=[1]*16)]))
  with TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path='fixture'
   with patch('sdk.worldmap_model_binding.source',return_value=(original,native)),patch('sdk.worldmap_current_models.source',return_value=(original,native)),patch('sdk.worldmap_model_source.read_worldmap_model',return_value=(original,export_shape_json(original),native)):
    candidate,ledger,_=append_vector_ledger(original,create_face_ledger(original),[dict(object_index=0,kind='vertices',vectors=[[123,456,789]]),dict(object_index=0,kind='normals',vectors=[[4096,0,0]])])
    binding=dict(format='world-tmd-vector-allocation-v1',source_scene_id='worldmap://map01/models',source_sha256=sha256(original).hexdigest(),asset_sha256=sha256(candidate).hexdigest(),byte_length=len(candidate),base_binding=None,ledger=ledger)
    p._publish_model_ledger(identifier,candidate,binding,state_key(p),'World vector allocation')
    held=deepcopy(p._document());history=deepcopy(p.undo_stack)
    current=compose(p,deepcopy(geometry));actual=current['scene_graph']['assets'][0]['preview'];decoded=decode_tmd(candidate)
    self.assertEqual(actual['vertices'],decoded['vertices']);self.assertEqual(actual['objects'],decoded['objects']);self.assertEqual(actual['triangles'],decoded['triangles']);self.assertEqual(actual['triangle_normals'],decoded['triangle_normals']);self.assertEqual(actual['authored_shape'],binding)
    self.assertEqual(current['model_authoring']['schema_version'],'legaia.worldmap-current-models.v3')
    self.assertEqual(current['scene_graph']['entities'],geometry['scene_graph']['entities']);self.assertEqual(geometry['scene_graph']['assets'][0]['preview'],preview)
    request=dict(asset_id=identifier,source_key=state_key(p),member_sha256=native['decoded_member_sha256'])
    source=inspect(p,dict(request,layer='current'));self.assertEqual(source['schema_version'],'legaia.worldmap-model-source.v4');self.assertEqual(source['allocation_binding'],binding);self.assertEqual(base64.b64decode(source['tmd_base64']),candidate);self.assertEqual(base64.b64decode(source['base_tmd_base64']),original)
    source['allocation_binding']['ledger']['operations'][0]['requests'][0]['vectors'][0][0]=0
    self.assertEqual(p.model_overrides[identifier],binding)
    retail=inspect(p,dict(request,layer='retail'));self.assertEqual(base64.b64decode(retail['tmd_base64']),original);self.assertEqual(retail['schema_version'],'legaia.worldmap-model-source.v2')
    self.assertEqual(p._document(),held);self.assertEqual(p.undo_stack,history)
