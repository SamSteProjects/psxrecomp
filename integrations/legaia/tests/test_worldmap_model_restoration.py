from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from importer.model_face_ledger import create_face_ledger, append_vector_ledger
from sdk.project import ProjectService, ProjectError
from sdk.worldmap_authoring import state_key
from sdk.worldmap_model_restoration import review, apply
from test_importer_assets import model


class WorldModelRestorationTests(TestCase):
    def test_allocated_restoration_is_selected_only_reversible_and_noop_without_binding(self):
        original=model(0x22);identifier='asset://map01/worldmap/models/0000'
        native=dict(disc_sha256='a'*64,decoded_member_sha256=sha256(original).hexdigest())
        with TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.disc_path='fixture'
            with patch('sdk.worldmap_model_restoration.source',return_value=(original,native)),patch('sdk.worldmap_model_binding.source',return_value=(original,native)):
                current,ledger,_=append_vector_ledger(original,create_face_ledger(original),[dict(object_index=0,kind='vertices',vectors=[[1,2,3]])])
                binding=dict(format='world-tmd-vector-allocation-v1',source_scene_id='worldmap://map01/models',source_sha256=sha256(original).hexdigest(),asset_sha256=sha256(current).hexdigest(),byte_length=len(current),base_binding=None,ledger=ledger)
                p._publish_model_ledger(identifier,current,binding,state_key(p),'World allocation')
                held=deepcopy(p._document());history=deepcopy((p.undo_stack,p.redo_stack))
                request=dict(asset_id=identifier,source_key=state_key(p),member_sha256=binding['source_sha256'],effective_sha256=binding['asset_sha256'])
                report=review(p,request)
                self.assertTrue(report['changed']);self.assertTrue(report['native_content_changed'])
                self.assertEqual(report['current_byte_length'],len(original)+8)
                self.assertEqual(report['retail_byte_length'],len(original))
                self.assertEqual(p._document(),held);self.assertEqual((p.undo_stack,p.redo_stack),history)
                for bad in [dict(request,source_key='0'*64),dict(request,effective_sha256='0'*64),dict(request,member_sha256='0'*64)]:
                    with self.assertRaises(ProjectError):review(p,bad)
                with self.assertRaises(ProjectError):apply(p,request,'0'*64)
                self.assertEqual(p._document(),held)
                apply(p,request,report['review_key']);self.assertNotIn(identifier,p.model_overrides)
                self.assertEqual(len(p.undo_stack),len(history[0])+1)
                p.undo();self.assertEqual(p._document(),held)
                p.redo();self.assertNotIn(identifier,p.model_overrides)
                with self.assertRaises(ProjectError):apply(p,request,report['review_key'])
                request.update(source_key=state_key(p),effective_sha256=binding['source_sha256'])
                empty=review(p,request);self.assertFalse(empty['changed']);self.assertFalse(empty['native_content_changed'])
                history=deepcopy((p.undo_stack,p.redo_stack));apply(p,request,empty['review_key']);self.assertEqual((p.undo_stack,p.redo_stack),history)
                p.mode='live'
                with self.assertRaises(ProjectError):review(p,request)
