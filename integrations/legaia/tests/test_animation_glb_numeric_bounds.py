"""Untrusted JSON integers reject through normal SDK errors, without overflow."""
from copy import deepcopy
import base64
from pathlib import Path
import tempfile
import unittest

from importer.animation_glb import import_animation_glb
from importer.core import ImportError
from importer.export import encode_model_glb
from sdk.animation_glb import export_clip
from sdk.animation_record_glb import export_binding
from sdk.project import ProjectError, ProjectService
from test_animation_glb import document, encode, record
from test_importer_export import preview
from test_model_primitive_workflow import http_server


class NumericBounds(unittest.TestCase):
    def fixture(self):
        frames = [[([0,0,0],[0,0,0])]]*3
        doc, payload = document(frames)
        return record(frames), doc, payload

    def test_huge_json_node_vectors_and_integer_quaternions_reject_normally(self):
        source, doc, payload = self.fixture()
        for field, vector in [('translation',[10**400,0,0]),
                              ('scale',[1,-10**400,1]),
                              ('rotation',[10**200,0,0,1]),
                              ('rotation',[0,0,0,10**400]),
                              ('matrix',[10**400]+[0]*15)]:
            with self.subTest(field=field, digits=len(str(vector[0]))):
                bad = deepcopy(doc); bad['nodes'][0][field] = vector
                with self.assertRaises(ImportError):
                    import_animation_glb(source, encode(bad,payload), fps=15)
        self.assertEqual(import_animation_glb(source, encode(doc,payload), fps=15)[0], source)

    def test_huge_rates_reject_at_import_export_and_both_sdk_boundaries(self):
        source, doc, payload = self.fixture(); content=encode(doc,payload)
        with tempfile.TemporaryDirectory() as directory:
            project=ProjectService(Path(directory))
            for rate in [10**400,-10**400,True,float('inf'),float('nan')]:
                with self.subTest(rate_type=type(rate).__name__):
                    with self.assertRaises(ImportError): import_animation_glb(source,content,fps=rate)
                    with self.assertRaises(ImportError): encode_model_glb(preview(),clip_fps=rate)
                    with self.assertRaises(ProjectError): export_clip(project,'scene://town01/actors/man-p1/0011',rate)
                    with self.assertRaises(ProjectError): export_binding(project,'scene://town01','unused','a'*64,rate)

    def test_http_huge_rates_return_400_and_leave_service_usable(self):
        _,doc,payload=self.fixture();content=base64.b64encode(encode(doc,payload)).decode()
        with tempfile.TemporaryDirectory() as directory:
            project=ProjectService(Path(directory));before=deepcopy((project.overrides,project.undo_stack,project.redo_stack))
            with http_server(project) as (_,post):
                for rate in [10**400,-10**400]:
                    status,result=post('/api/animation-glb-export',dict(entity_id='scene://town01/actors/man-p1/0011',clip_fps=rate))
                    self.assertEqual(status,400,result);self.assertIn('rate',result['error'])
                    request=dict(scene_id='scene://town01',record_id='unused',expected_source_key='a'*64,
                                 source_frame_indices=[0],glb_base64=content,
                                 binding=dict(schema_version='legaia.animation-record-glb-binding.v1',clip_fps=rate))
                    status,result=post('/api/animation-record-glb-review',request)
                    self.assertEqual(status,400,result);self.assertIn('rate',result['error'])
                status,result=post('/api/animation-glb-export',dict(entity_id='missing',clip_fps=15))
                self.assertEqual(status,400,result);self.assertIn('imported actor',result['error'])
            self.assertEqual((project.overrides,project.undo_stack,project.redo_stack),before)
