from contextlib import contextmanager
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
from importer.core import _pack_ranges, ImportError
from importer.assets import decode_tmd
from importer.model_authoring import preview_model_shape
from sdk.worldmap_model_allocation import prepare as prepare_vectors, apply as apply_vectors
from sdk.worldmap_model_replacement import prepare as prepare_content, apply as apply_content
import base64,struct
from sdk.project import ProjectService, ProjectError
from sdk.worldmap_authoring import state_key
from sdk.worldmap_model_faces import source, prepare, review, apply
from test_model_pack_growth import pack_source, container_for
from test_model_primitive_workflow import http_server


class WorldModelFaceTests(TestCase):
    def test_source_and_review_preserve_project_and_qualify_complete_carrier(self):
        pack,_=pack_source();raw=container_for(pack);start,stop=_pack_ranges(pack)[0];original=pack[start:stop]
        native=dict(disc_sha256='a'*64,prot_entry_index=86,slot_index=1,pack_slot=0,
            decoded_member_offset=start,decoded_member_span_end=stop,decoded_byte_length=len(pack),compressed_stream_offset=44)
        @contextmanager
        def disc(_):yield None,'a'*64,None,None
        with TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.disc_path='fixture'
            request=dict(asset_id='asset://map01/worldmap/models/0000',source_key=state_key(p),
                member_sha256=sha256(original).hexdigest(),effective_sha256=sha256(original).hexdigest())
            held=deepcopy(p._document());history=deepcopy((p.undo_stack,p.redo_stack))
            with patch('sdk.worldmap_model_faces.native_source',return_value=(original,native)), \
                 patch('sdk.worldmap_model_binding.source',return_value=(original,native)), \
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
                with self.assertRaises(ProjectError):apply(p,proposal,'0'*64)
                self.assertEqual(p._document(),held)
                with http_server(p) as (_,post):
                    status,body=post('/api/worldmap-model-face-addition-apply',dict(request=proposal,review_key=result['review_key']))
                    self.assertEqual(status,200,body)
                    self.assertEqual(post('/api/worldmap-model-face-addition-apply',dict(request=proposal,review_key=result['review_key']))[0],400)
                binding=deepcopy(p.model_overrides[request['asset_id']])
                self.assertEqual(binding['format'],'world-tmd-face-addition-v1')
                self.assertEqual(p.read_model_replacement(request['asset_id'],binding),candidate)
                self.assertEqual(len(p.undo_stack),1)
                forged=deepcopy(binding);forged['ledger']['batches']=[]
                with self.assertRaises(ImportError):p.read_model_replacement(request['asset_id'],forged)
                p.undo();self.assertEqual(p._document(),held)
                p.redo();self.assertEqual(p.model_overrides[request['asset_id']],binding)
                reopened=ProjectService.open(p.save())
                self.assertEqual(reopened.model_overrides,p.model_overrides)
                self.assertEqual(reopened.read_model_replacement(request['asset_id'],binding),candidate)
                self.assertEqual(preview_model_shape(decode_tmd(original),candidate,binding)['triangles'],decode_tmd(candidate)['triangles'])
                allocation=dict(request,source_key=state_key(p),effective_sha256=sha256(candidate).hexdigest(),
                    requests=[dict(object_index=0,kind='vertices',vectors=[[9,8,7]])])
                with patch('sdk.worldmap_model_allocation.source',return_value=(original,native)):
                    enlarged,_,allocation_review=prepare_vectors(p,allocation)
                    self.assertEqual(allocation_review['binding']['format'],binding['format'])
                    apply_vectors(p,allocation,allocation_review['review_key'])
                edited=bytearray(enlarged);at=12+struct.unpack_from('<I',edited,12)[0];struct.pack_into('<h',edited,at,7)
                content=dict(request,source_key=state_key(p),effective_sha256=sha256(enlarged).hexdigest(),
                    format='content-tmd',content_base64=base64.b64encode(edited).decode('ascii'))
                with patch('sdk.worldmap_model_replacement.source',return_value=(original,native)):
                    candidate_edit,content_review=prepare_content(p,content)
                    self.assertEqual(content_review['proposed_binding']['format'],binding['format'])
                    apply_content(p,content,content_review['review_key'])
                final=p.model_overrides[request['asset_id']]
                self.assertEqual([op['kind'] for op in final['ledger']['operations']],['add_faces','allocate_vectors','edit_content'])
                self.assertEqual(p.read_model_replacement(request['asset_id'],final),bytes(edited))
                reopened=ProjectService.open(p.save())
                self.assertEqual(reopened.read_model_replacement(request['asset_id'],final),bytes(edited))
                second=dict(request,source_key=state_key(p),effective_sha256=sha256(edited).hexdigest(),
                    requests=[dict(face_id='face://authored/00000000-0000-4000-8000-000000000002',
                        donor_face_id=proposal['requests'][0]['face_id'],fields=dict(vertices=[0,1,2]))])
                second_candidate,second_review=prepare(p,second)
                self.assertEqual(second_review['topology']['authored_face_count'],2)
                self.assertEqual(second_review['binding']['ledger']['operations'][:-1],final['ledger']['operations'])
                apply(p,second,second_review['review_key'])
                self.assertEqual(p.read_model_replacement(request['asset_id'],p.model_overrides[request['asset_id']]),second_candidate)
