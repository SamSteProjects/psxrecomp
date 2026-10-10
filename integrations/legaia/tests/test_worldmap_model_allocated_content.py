import base64,struct
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from importer.model_face_ledger import create_face_ledger,append_vector_ledger,replay_face_ledger
from importer.model_primitives import inspect_model_primitives,patch_model_primitives
from sdk.project import ProjectService,ProjectError
from sdk.worldmap_authoring import state_key
from sdk.worldmap_model_replacement import prepare,apply
from sdk.worldmap_model_allocation import validate_ledger
from test_importer_assets import model

class AllocatedWorldContentTests(TestCase):
 def test_content_replays_from_retained_base_and_persists_one_history_step(self):
  original=model(0x22);identifier='asset://map01/worldmap/models/0000';native=dict(disc_sha256='a'*64,decoded_member_sha256=sha256(original).hexdigest())
  with TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path='fixture'
   with patch('sdk.worldmap_model_binding.source',return_value=(original,native)),patch('sdk.worldmap_model_replacement.source',return_value=(original,native)):
    current,ledger,_=append_vector_ledger(original,create_face_ledger(original),[dict(object_index=0,kind='vertices',vectors=[[123,456,789]])])
    binding=dict(format='world-tmd-vector-allocation-v1',source_scene_id='worldmap://map01/models',source_sha256=sha256(original).hexdigest(),asset_sha256=sha256(current).hexdigest(),byte_length=len(current),base_binding=None,ledger=ledger)
    p._publish_model_ledger(identifier,current,binding,state_key(p),'World allocation')
    held=deepcopy(p._document());history=deepcopy((p.undo_stack,p.redo_stack));key=state_key(p)
    request=dict(asset_id=identifier,source_key=key,member_sha256=sha256(original).hexdigest(),effective_sha256=sha256(current).hexdigest(),format='content-tmd',content_base64=base64.b64encode(current).decode())
    _,noop=prepare(p,request);self.assertFalse(noop['changed']);apply(p,request,noop['review_key']);self.assertEqual(p._document(),held);self.assertEqual((p.undo_stack,p.redo_stack),history)
    face=inspect_model_primitives(current)['objects'][0]['primitives'][0];refs=deepcopy(face['vertices']);refs[0]=struct.unpack_from('<I',current,16)[0]-1
    candidate,_=patch_model_primitives(current,sha256(current).hexdigest(),[dict(object_index=0,primitive_index=face['primitive_index'],vertices=refs)])
    request['content_base64']=base64.b64encode(candidate).decode();actual,report=prepare(p,request)
    self.assertEqual(actual,candidate);self.assertIsNone(report['changes_from_retail']);self.assertFalse(report['clears_override']);self.assertEqual(report['proposed_binding']['format'],'world-tmd-vector-content-v1');self.assertEqual(report['proposed_binding']['ledger']['operations'][:-1],ledger['operations']);self.assertEqual(replay_face_ledger(original,report['proposed_binding']['ledger'])[0],candidate)
    for bad in [dict(request,source_key='0'*64),dict(request,effective_sha256='0'*64),dict(request,format='tmd')]:
     with self.assertRaises(Exception):prepare(p,bad)
    with self.assertRaises(ProjectError):apply(p,request,'0'*64)
    self.assertEqual(p._document(),held);self.assertEqual((p.undo_stack,p.redo_stack),history)
    apply(p,request,report['review_key']);self.assertEqual(p.read_model_replacement(identifier,p.model_overrides[identifier]),candidate);self.assertEqual(len(p.undo_stack),len(history[0])+1)
    committed=deepcopy(p._document());p.undo();self.assertEqual(p._document(),held);p.redo();self.assertEqual(p._document(),committed)
    with self.assertRaises(ProjectError):apply(p,request,report['review_key'])
    for kind in ['add_faces','remove_faces','allocate_objects']:
     forged=deepcopy(p.model_overrides[identifier]);forged['ledger']['operations'][-1]['kind']=kind
     with self.assertRaises(ProjectError):validate_ledger(forged)
    reopened=ProjectService.open(p.save());self.assertEqual(reopened.model_overrides,p.model_overrides);self.assertEqual(reopened.read_model_replacement(identifier,p.model_overrides[identifier]),candidate)
