"""World object Review checks complete native ownership without publishing."""
from contextlib import contextmanager
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
import base64
from importer.core import _pack_ranges, ImportError
from importer.model_object_allocation import allocate_model_objects
from sdk.project import ProjectService, ProjectError
from sdk.worldmap_authoring import state_key
from sdk.worldmap_model_objects import source, review
from test_model_pack_growth import pack_source, container_for
from test_model_primitive_workflow import http_server


def clone_request(inspected, ordinal=1):
    identity = inspected['object_identities'][0]
    native = inspected['native_objects'][identity['object_index']]
    return dict(object_id=f'object://authored/00000000-0000-4000-8000-{ordinal:012x}',
        donor_object_id=identity['object_id'],groups=[dict(
            group_id=f'group://authored/00000000-0000-4000-8000-{ordinal*10000+index+1:012x}',
            faces=[dict(face_id=f'face://authored/00000000-0000-4000-8000-{ordinal*10000+i+group["first_primitive_index"]+1:012x}',
                        donor_face_id=face) for i,face in enumerate(group['face_ids'])])
            for index,group in enumerate(native['groups'])])


class WorldObjectReviewTests(TestCase):
    def test_complete_donor_clone_http_and_refusals_do_not_publish(self):
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
                inspected=source(p,request);clone=clone_request(inspected)
                proposal=dict(request,requests=[clone]);receipt=review(p,proposal)
                candidate=base64.b64decode(receipt['proposed_model_base64'])
                direct,audit=allocate_model_objects(original,request['effective_sha256'],
                    [dict(object_id=clone['object_id'],donor_object_index=0)])
                self.assertEqual(candidate,direct)
                self.assertEqual(receipt['allocation']['new_objects'],audit['new_objects'])
                self.assertEqual(receipt['topology']['allocated_object_count'],1)
                self.assertEqual(receipt['topology']['objects'][-1]['donor_object_id'],clone['donor_object_id'])
                self.assertFalse(receipt['build_ready']);self.assertTrue(receipt['read_only'])
                self.assertEqual(receipt['binding']['ledger']['schema_version'],'legaia.model-face-addition-ledger.v7')
                for alter in [lambda v:v.update(source_key='0'*64),lambda v:v.update(member_sha256='0'*64),
                    lambda v:v.update(effective_sha256='0'*64),lambda v:v.update(extra=True),
                    lambda v:v['requests'][0].update(donor_object_id='foreign'),
                    lambda v:v['requests'][0]['groups'].clear(),
                    lambda v:v['requests'][0]['groups'][0]['faces'].clear(),
                    lambda v:v['requests'][0]['groups'][0]['faces'][0].update(donor_face_id='foreign'),
                    lambda v:v['requests'].append(deepcopy(v['requests'][0]))]:
                    bad=deepcopy(proposal);alter(bad)
                    with self.assertRaises((ProjectError,ImportError)):review(p,bad)
                with patch('sdk.worldmap_model_faces.state_key',side_effect=[request['source_key'],'0'*64]):
                    with self.assertRaisesRegex(ProjectError,'changed during'):review(p,proposal)
                with http_server(p) as (_,post):
                    self.assertEqual(post('/api/worldmap-model-object-source',request),(200,inspected))
                    self.assertEqual(post('/api/worldmap-model-object-review',proposal),(200,receipt))
                    self.assertEqual(post('/api/worldmap-model-object-source',dict(request,extra=True))[0],400)
                    self.assertEqual(post('/api/worldmap-model-object-apply',dict(request=proposal,review_key=receipt['review_key']))[0],400)
                self.assertEqual(p._document(),held);self.assertEqual((p.undo_stack,p.redo_stack),history)
                p.mode='live'
                with self.assertRaises(ProjectError):source(p,request)
