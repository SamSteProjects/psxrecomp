from pathlib import Path
from tempfile import TemporaryDirectory
from copy import deepcopy
from hashlib import sha256
from unittest import TestCase
from unittest.mock import patch
import base64,struct,json
from test_importer_assets import model
from importer.model_json import export_shape_json
from sdk.project import ProjectService,ProjectError
from sdk.worldmap_model_replacement import review,apply

class WorldModelReplacementTests(TestCase):
 def test_shared_history_source_owner_json_tmd_and_stale(self):
  original=model(0x22);candidate=bytearray(original);at=12+struct.unpack_from('<I',original,12)[0];struct.pack_into('<h',candidate,at,struct.unpack_from('<h',original,at)[0]+1);candidate=bytes(candidate);identifier='asset://map01/worldmap/models/0000';native=dict(disc_sha256='a'*64)
  with TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path='fixture'
   with patch('sdk.worldmap_model_binding.source',return_value=(original,native)),patch('sdk.worldmap_model_replacement.source',return_value=(original,native)),patch('sdk.worldmap_model_replacement.state_key',return_value='b'*64):
    request=dict(asset_id=identifier,source_key='b'*64,member_sha256=sha256(original).hexdigest(),effective_sha256=sha256(original).hexdigest(),format='tmd',content_base64=base64.b64encode(candidate).decode());held=deepcopy(p._document());receipt=review(p,request);self.assertTrue(receipt['changed']);self.assertEqual(p._document(),held)
    with self.assertRaises(ProjectError):apply(p,request,'0'*64)
    apply(p,request,receipt['review_key']);binding=deepcopy(p.model_overrides[identifier]);self.assertEqual(binding['source_scene_id'],'worldmap://map01/models');self.assertEqual(binding['format'],'tmd-shape');self.assertEqual(p.read_model_replacement(identifier,binding),candidate);self.assertEqual(len(p.undo_stack),1)
    with self.assertRaises(ProjectError):apply(p,request,receipt['review_key'])
    p.undo();self.assertEqual(p.model_overrides,{});p.redo();self.assertEqual(p.model_overrides[identifier],binding);reopened=ProjectService.open(p.save());self.assertEqual(reopened.model_overrides,p.model_overrides)
    current={**request,'effective_sha256':sha256(candidate).hexdigest()};noop=review(p,current);self.assertFalse(noop['changed']);before=len(p.undo_stack);apply(p,current,noop['review_key']);self.assertEqual(len(p.undo_stack),before)
    shape=json.loads(export_shape_json(candidate));shape['objects'][0]['vertices'][0][0]+=1;request_json={**current,'format':'json','content_base64':base64.b64encode(json.dumps(shape).encode()).decode()};receipt=review(p,request_json);apply(p,request_json,receipt['review_key']);self.assertEqual(len(p.undo_stack),2)
    with self.assertRaises(ProjectError):p.read_model_replacement(identifier,{**binding,'source_scene_id':'scene://town01'})
    corrupt=bytearray(original);corrupt[0]^=1
    with self.assertRaises(Exception):p.set_model_replacement(identifier,bytes(corrupt))
    latest=p.read_model_replacement(identifier,p.model_overrides[identifier]);restore={**request,'effective_sha256':sha256(latest).hexdigest(),'content_base64':base64.b64encode(original).decode()};receipt=review(p,restore);apply(p,restore,receipt['review_key']);self.assertNotIn(identifier,p.model_overrides);p.undo();self.assertEqual(p.read_model_replacement(identifier,p.model_overrides[identifier]),latest)
    p.mode='live'
    with self.assertRaises(ProjectError):review(p,current)
