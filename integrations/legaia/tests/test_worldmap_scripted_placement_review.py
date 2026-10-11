from base64 import b64decode
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import tempfile
from unittest import TestCase
from unittest.mock import patch

from sdk.project import ProjectService,ProjectError
from sdk.worldmap_authoring import state_key
from sdk.worldmap_scripted_placement_allocation import source,review,_merge_map
from test_worldmap_scripted_placement_allocation import fixture
from test_project_workflow import synthetic_scene
from test_model_primitive_workflow import http_server


class ScriptedWorldReviewTests(TestCase):
    def test_coauthor_fields_preserve_independent_bits_and_refuse_hybrid_words(self):
        self.assertEqual(_merge_map(b'\x00',b'\x03',b'\x40','Collision',[dict(byte_offset=0,bit_mask=0x40)]),b'\x43')
        self.assertEqual(_merge_map(b'\x00',b'\x40',b'\x03','FloorTiers',[]),b'\x43')
        self.assertEqual(_merge_map(b'\x00',b'\x10',b'\x20','Collision',[dict(byte_offset=0,bit_mask=0x20)]),b'\x30')
        self.assertEqual(_merge_map(b'\x00',b'\x03',b'\x03','Environment',[]),b'\x03')
        for name in ('Environment','TriggerCells','FloorTiers'):
            with self.subTest(name=name),self.assertRaises(ProjectError):
                _merge_map(b'\x00',b'\x01',b'\x02',name,[])

    def test_http_review_is_reproducible_readonly_and_source_bound(self):
        raw,fallback,man,floor,requests=fixture()
        with tempfile.TemporaryDirectory() as root:
            project=ProjectService(Path(root));project.import_metadata(synthetic_scene())
            key=state_key(project);held=deepcopy(project._document());history=deepcopy((project.undo_stack,project.redo_stack))
            provenance=dict(scene='map01',source_disc_sha256='b'*64,source_map_sha256=sha256(raw).hexdigest(),source_floor_lut_sha256=sha256(man[2:34]).hexdigest())
            inputs=(raw,provenance,floor,raw,[],fallback,man,man,{},[])
            with patch('sdk.worldmap_scripted_placement_allocation._inputs',return_value=inputs):
                snapshot=source(project,'map01',key)
                self.assertEqual(b64decode(snapshot['current_map_base64']),raw)
                self.assertEqual(len(snapshot['donors']),1)
                first=review(project,'map01',key,requests)
                self.assertEqual(first,review(project,'map01',key,requests))
                self.assertFalse(first['build_ready']);self.assertFalse(first['project_changed'])
                with http_server(project) as (_,post):
                    self.assertEqual(post('/api/worldmap-scripted-placement-source',dict(scene='map01',source_key=key))[0],200)
                    code,value=post('/api/worldmap-scripted-placement-review',dict(scene='map01',source_key=key,requests=requests))
                    self.assertEqual(code,200);self.assertEqual(value['review_key'],first['review_key'])
                    for route,body in [('/api/worldmap-scripted-placement-source',dict(scene='map01',source_key=key,extra=0)),
                        ('/api/worldmap-scripted-placement-review',dict(scene='map01',source_key=key)),
                        ('/api/worldmap-scripted-placement-review',dict(scene='map01',source_key='0'*64,requests=requests))]:
                        self.assertEqual(post(route,body)[0],400)
                project.mode='live'
                with self.assertRaises(ProjectError):review(project,'map01',state_key(project),requests)
                project.mode='edit'
            self.assertEqual(project._document(),held)
            self.assertEqual((project.undo_stack,project.redo_stack),history)

    def test_retained_identity_collision_refuses(self):
        raw,fallback,man,floor,requests=fixture()
        with tempfile.TemporaryDirectory() as root:
            project=ProjectService(Path(root));project.import_metadata(synthetic_scene())
            inputs=(raw,{},floor,raw,[dict(placement_id=requests[0]['placement_id'])],fallback,man,man,{},[])
            with patch('sdk.worldmap_scripted_placement_allocation._inputs',return_value=inputs),self.assertRaises(ProjectError):
                review(project,'map01',state_key(project),requests)
