from hashlib import sha256
from pathlib import Path
import struct,tempfile,unittest
from unittest.mock import patch
from importer.model_allocation import inspect_model_allocation
from importer.model_face_removal import remove_faces
from importer.core import ImportError
from sdk.model_allocation import source
from sdk.project import ProjectService,ProjectError
from sdk.scene_preview import source_key
from test_model_primitives import synthetic
class ModelAllocationTests(unittest.TestCase):
    def test_group_extents_terminator_vectors_and_empty_streams(self):
        original=synthetic(((0x22,0x14),(0x22,)),count=2)
        report=inspect_model_allocation(original)
        self.assertEqual(report['source_sha256'],sha256(original).hexdigest())
        for obj in report['objects']:
            stream=obj['primitive_stream'];self.assertEqual(original[stream['terminator_offset']:stream['terminator_offset']+4],bytes(4))
            self.assertEqual(sum(g['primitive_count'] for g in obj['groups']),obj['primitive_count'])
            self.assertEqual(stream['encoded_byte_length'],sum(g['byte_length'] for g in obj['groups'])+4)
            self.assertEqual(stream['byte_limit']-stream['byte_offset'],stream['encoded_byte_length']+stream['uninterpreted_tail_bytes'])
            for group in obj['groups']:self.assertEqual(group['byte_length'],8+(group['primitive_count']+1)*group['packet_stride'])
            for vector in obj['vectors']:self.assertEqual(vector['byte_length'],vector['count']*8)
        empty=remove_faces(original,original,[],[dict(object_index=0,primitive_index=i) for i in range(4)])[0]
        current=inspect_model_allocation(empty)['objects'][0]
        self.assertEqual(current['groups'],[]);self.assertEqual(current['primitive_stream']['encoded_byte_length'],4)
        self.assertEqual(current['vectors'],report['objects'][0]['vectors'])
    def test_compacted_bytes_are_uninterpreted_not_free_allocation(self):
        original=synthetic(((0x22,),),count=3)
        current=remove_faces(original,original,[],[dict(object_index=0,primitive_index=0)])[0]
        before,after=(inspect_model_allocation(data) for data in (original,current))
        a,b=(r['objects'][0]['primitive_stream'] for r in (before,after))
        self.assertEqual(b['uninterpreted_tail_bytes']-a['uninterpreted_tail_bytes'],before['objects'][0]['groups'][0]['packet_stride'])
        self.assertIn('not authorized',after['tail_policy']);self.assertEqual(before['byte_length'],after['byte_length'])
        self.assertNotIn('free_bytes',b)
    def test_malformed_layout_and_declared_counts_fail_closed(self):
        data=synthetic(((0x22,),),count=2)
        changed=bytearray(data);struct.pack_into('<I',changed,32,3)
        for bad in (b'',data[:10],bytes(changed)):
            with self.assertRaises(ImportError):inspect_model_allocation(bad)
    def test_source_mode_freshness_detachment_and_no_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=ProjectService(Path(tmp));p.active_scene='scene://fixture';original=synthetic(((0x22,),),count=2)
            p.mode='edit';key='fixture-fresh'
            with patch.object(p,'_model_source',return_value=original), patch('sdk.model_allocation.source_key',return_value=key):
                report=source(p,'asset://fixture/model/0',key);report['retail']['objects'][0]['groups'].clear()
                self.assertTrue(source(p,'asset://fixture/model/0',key)['retail']['objects'][0]['groups'])
                for stale in ('','stale'):
                    with self.assertRaises(ProjectError):source(p,'asset://fixture/model/0',stale)
                with patch('sdk.model_allocation.source_key',side_effect=[key,'changed']):
                    with self.assertRaises(ProjectError):source(p,'asset://fixture/model/0',key)
                p.mode='play'
                with self.assertRaises(ProjectError):source(p,'asset://fixture/model/0',key)
            self.assertEqual(p.model_overrides,{})
            self.assertEqual(list(Path(tmp).iterdir()),[])
if __name__=='__main__':unittest.main()
