from contextlib import contextmanager
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
from importer.core import _pack_ranges
from sdk.project import ProjectService, ProjectError
from sdk.worldmap_model_allocation import prepare, review
from test_model_pack_growth import pack_source, container_for
from test_model_primitive_workflow import http_server


class WorldModelAllocationTests(TestCase):
    def test_review_is_read_only_and_http_requires_current_source(self):
        pack, _ = pack_source(); raw = container_for(pack); start, stop = _pack_ranges(pack)[0]
        original = pack[start:stop]; native = dict(disc_sha256='a'*64, prot_entry_index=86,
            slot_index=1, pack_slot=0, decoded_member_offset=start, decoded_member_span_end=stop)
        @contextmanager
        def disc(_):
            yield None, 'a'*64, None, None
        with TemporaryDirectory() as root:
            project = ProjectService(Path(root)); project.disc_path = 'fixture'
            request = dict(asset_id='asset://map01/worldmap/models/0000', source_key='b'*64,
                member_sha256=sha256(original).hexdigest(), effective_sha256=sha256(original).hexdigest(),
                requests=[dict(object_index=0,kind='vertices',vectors=[[1,2,3]])])
            held = deepcopy(project._document())
            with patch('sdk.worldmap_model_allocation.source',return_value=(original,native)),                  patch('sdk.worldmap_model_allocation.state_key',return_value='b'*64),                  patch('sdk.worldmap_model_allocation._disc_context',disc),                  patch('sdk.worldmap_model_allocation._kingdom_table',return_value=(None,86,0,SimpleNamespace(table_offset=0),raw)),                  patch('sdk.worldmap_model_allocation._slot',return_value=(pack,{})):
                candidate,ledger,report=prepare(project,request)
                self.assertEqual(len(candidate),len(original)+8)
                self.assertEqual(report['request'],request)
                self.assertFalse(report['build_ready']);self.assertFalse(report['project_changed'])
                self.assertTrue(report['read_only']);self.assertEqual(project._document(),held)
                for bad in [dict(request,source_key='0'*64),dict(request,member_sha256='0'*64),dict(request,extra=True)]:
                    with self.assertRaises(ProjectError):review(project,bad)
                with patch('sdk.worldmap_model_allocation.state_key',side_effect=['b'*64,'0'*64]):
                    with self.assertRaisesRegex(ProjectError,'changed during'):review(project,request)
                with http_server(project) as (_,post):
                    self.assertEqual(post('/api/worldmap-model-vector-allocation-review',request),(200,report))
                    self.assertEqual(post('/api/worldmap-model-vector-allocation-review',dict(request,source_key='0'*64))[0],400)
                    self.assertEqual(post('/api/worldmap-model-vector-allocation-review',dict(request,requests=[dict(object_index=0,kind='vertices',vectors=[[32768,0,0]])]))[0],400)
                self.assertEqual(project._document(),held);self.assertEqual(project.undo_stack,[])
