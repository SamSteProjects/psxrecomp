from contextlib import nullcontext
from hashlib import sha256
from types import SimpleNamespace
import struct
import unittest
from unittest.mock import patch
from importer.core import ImportError
from importer.model_vertex_references import vertex_users, retarget_object_vertices
from importer.model_primitives import inspect_model_primitives, patch_model_primitives
from sdk.model_vertex_users import inspect
from sdk.project import ProjectError, ProjectService
from test_model_primitives import synthetic, TRI_VI, QUAD_VI


class VertexReferenceTests(unittest.TestCase):
    def test_all_packet_families_exact_words_and_object_boundary(self):
        for flags in range(0x10, 0x28):
            with self.subTest(flags=flags):
                source = synthetic(((flags, flags), (flags,)), count=2)
                current = patch_model_primitives(source, sha256(source).hexdigest(),
                    [dict(object_index=0, primitive_index=0, vertices=[0] * (4 if flags & 2 else 3))])[0]
                users = vertex_users(current, 0, 0)
                expected = bytearray(current)
                primitive_rows = inspect_model_primitives(current)['objects'][0]['primitives']
                vi = (QUAD_VI if flags & 2 else TRI_VI)[(flags - 0x10) // 4]
                offsets = []
                for row in primitive_rows:
                    for corner, value in enumerate(row['vertices']):
                        if value == 0:
                            at = row['byte_offset'] + vi + corner * 2
                            offsets.append(at)
                            struct.pack_into('<H', expected, at, 32)
                self.assertEqual([row['byte_offset'] for row in users], offsets)
                self.assertTrue(all(row['affected_corners'] == [row['corner_index']] for row in users))
                result = retarget_object_vertices(source, current, sha256(current).hexdigest(), 0, 0, 4)
                self.assertEqual(result, bytes(expected))
                self.assertEqual(vertex_users(result, 0, 0), [])
                self.assertEqual(retarget_object_vertices(source, result, sha256(result).hexdigest(), 0, 0, 4), result)
                self.assertEqual(retarget_object_vertices(source, result, sha256(result).hexdigest(), 0, 4, 4), result)

    def test_domain_stale_and_malformed_words(self):
        source = synthetic(); key = sha256(source).hexdigest()
        for obj, old, new in [(True,0,1),(1,0,1),(0,True,1),(0,0,True),(0,0,5),(0,-1,1)]:
            with self.subTest(indices=(obj,old,new)), self.assertRaises(ImportError):
                retarget_object_vertices(source, source, key, obj, old, new)
        with self.assertRaises(ImportError): retarget_object_vertices(source, source, '0'*64, 0, 0, 1)
        users = vertex_users(source, 0, 0); damaged = bytearray(source)
        struct.pack_into('<H', damaged, users[0]['byte_offset'], 1)
        with self.assertRaises(ImportError): vertex_users(bytes(damaged), 0, 0)

    def test_source_layers_detached_and_stale_binding(self):
        source = synthetic(); current = retarget_object_vertices(source, source, sha256(source).hexdigest(), 0, 0, 4)
        asset='asset://fixture/models/0'; scene='scene://fixture'; key='a'*64
        project=SimpleNamespace(mode='edit', active_scene=scene, disc_path='private',
            imports={scene:{'assets':{'models':[{'semantic_id':asset}]}}}, model_overrides={asset:{}},
            _model_source=lambda *args:source, read_model_replacement=lambda *args:current)
        with patch('sdk.model_vertex_users._disc_context', return_value=nullcontext()), patch('sdk.model_vertex_users.source_key', return_value=key):
            report=inspect(project,asset,0,0,sha256(current).hexdigest(),key)
            self.assertEqual(len(report['retail_users']),2); self.assertEqual(report['current_users'],[])
            self.assertEqual(report['current_coordinates'],[0,0,0])
            with self.assertRaises(ProjectError): inspect(project,asset,0,0,'0'*64,key)
            project.mode='live'
            with self.assertRaises(ProjectError): inspect(project,asset,0,0,sha256(current).hexdigest(),key)
            project.mode='edit'
        with patch('sdk.model_vertex_users._disc_context', return_value=nullcontext()), patch('sdk.model_vertex_users.source_key', side_effect=[key,'b'*64]):
            with self.assertRaisesRegex(ProjectError,'changed while'): inspect(project,asset,0,0,sha256(current).hexdigest(),key)

    def test_apply_requires_reviewed_candidate_and_skips_noop(self):
        project=SimpleNamespace(_prepare_model_object=lambda *args:(b'candidate',{'proposed_sha256':'b'*64,'changes_from_current':[1]}),set_model_replacement=lambda *args: calls.append(args))
        calls=[]
        with self.assertRaises(ProjectError): ProjectService.retarget_model_vertices(project,'asset',0,0,1,'a'*64,'c'*64)
        self.assertEqual(calls,[])
        ProjectService.retarget_model_vertices(project,'asset',0,0,1,'a'*64,'b'*64)
        self.assertEqual(calls,[('asset',b'candidate')])
        project._prepare_model_object=lambda *args:(b'candidate',{'proposed_sha256':'b'*64,'changes_from_current':[]})
        ProjectService.retarget_model_vertices(project,'asset',0,0,1,'a'*64,'b'*64)
        self.assertEqual(calls,[('asset',b'candidate')])
