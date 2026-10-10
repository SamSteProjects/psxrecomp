from contextlib import contextmanager
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
from importer.core import _pack_ranges, ImportError
from sdk.project import ProjectService, ProjectError
from sdk.worldmap_authoring import state_key
from sdk.worldmap_model_faces import source, prepare, review
from test_model_pack_growth import pack_source, container_for
from test_model_primitive_workflow import http_server


class WorldModelFaceTests(TestCase):
    def test_source_and_review_preserve_project_and_qualify_complete_carrier(self):
        pack,_=pack_source();raw=container_for(pack);start,stop=_pack_ranges(pack)[0];original=pack[start:stop]
        native=dict(disc_sha256='a'*64,prot_entry_index=86,slot_index=1,pack_slot=0,
            decoded_member_offset=start,decoded_member_span_end=stop)
        @contextmanager
        def disc(_):yield None,'a'*64,None,None
        with TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.disc_path='fixture'
            request=dict(asset_id='asset://map01/worldmap/models/0000',source_key=state_key(p),
                member_sha256=sha256(original).hexdigest(),effective_sha256=sha256(original).hexdigest())
            held=deepcopy(p._document());history=deepcopy((p.undo_stack,p.redo_stack))
            with patch('sdk.worldmap_model_faces.native_source',return_value=(original,native)), \
                 patch('sdk.worldmap_model_allocation._disc_context',disc), \
                 patch('sdk.worldmap_model_allocation._kingdom_table',return_value=(None,86,0,SimpleNamespace(table_offset=0),raw)), \
                 patch('sdk.worldmap_model_allocation._slot',return_value=(pack,{})):
                inspected=source(p,request);donor=inspected['topology']['faces'][0]
                proposal=dict(request,requests=[dict(face_id='face://authored/00000000-0000-4000-8000-000000000001',
                    donor_face_id=donor['face_id'],fields=dict(vertices=[2,1,0]))])
                candidate,result=prepare(p,proposal)
                self.assertGreater(len(candidate),len(original));self.assertEqual(result['topology']['authored_face_count'],1)
                self.assertFalse(result['build_ready']);self.assertTrue(result['read_only'])
                self.assertEqual(result['addition']['growth_bytes'],len(candidate)-len(original))
                for bad in [dict(proposal,source_key='0'*64),dict(proposal,effective_sha256='0'*64),dict(proposal,extra=True)]:
                    with self.assertRaises(ProjectError):review(p,bad)
                for requests in [[dict(proposal['requests'][0],donor_face_id='foreign')],proposal['requests']*2,
                                 [dict(proposal['requests'][0],fields=dict(vertices=[999,1,0]))]]:
                    with self.assertRaises(ImportError):review(p,dict(proposal,requests=requests))
                with patch('sdk.worldmap_model_faces.state_key',side_effect=[request['source_key'],'0'*64]):
                    with self.assertRaisesRegex(ProjectError,'changed during'):review(p,proposal)
                with http_server(p) as (_,post):
                    self.assertEqual(post('/api/worldmap-model-face-source',request),(200,inspected))
                    self.assertEqual(post('/api/worldmap-model-face-addition-review',proposal),(200,result))
                    self.assertEqual(post('/api/worldmap-model-face-addition-review',dict(proposal,source_key='0'*64))[0],400)
                p.mode='live'
                with self.assertRaises(ProjectError):source(p,request)
                p.mode='edit'
                self.assertEqual(p._document(),held);self.assertEqual((p.undo_stack,p.redo_stack),history)
