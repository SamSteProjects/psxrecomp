"""Deleted packets restore without overwriting surviving model edits."""
from copy import deepcopy
from hashlib import sha256
import struct, unittest
from unittest.mock import patch
from importer.core import ImportError
from importer.model_face_ledger import (create_face_ledger, replay_face_ledger,
    append_removal_ledger, append_content_ledger, deleted_face_sources)
from importer.model_face_reinsertion import reinsert_ledger_faces
from importer.model_primitives import inspect_model_primitives
from test_model_primitives import synthetic
import test_model_face_removal_ledger as fixtures


def packet(data, face):
    row=inspect_model_primitives(data)['objects'][face['object_index']]['primitives'][face['current_primitive_index']]
    # Packet stride is independently read from its owning group header.
    at=12+struct.unpack_from('<I',data,12+face['object_index']*28+16)[0]
    for _ in range(face['group_index']):
        count=struct.unpack_from('<H',data,at)[0];at+=8+(count+1)*data[at+5]*4
    return data[row['byte_offset']:row['byte_offset']+data[at+5]*4]


class FaceReinsertionTests(unittest.TestCase):
    def test_all_packet_formats_copy_surviving_and_deleted_bytes_exactly(self):
        for flags in range(0x10,0x28):
            with self.subTest(flags=hex(flags)):
                original=synthetic(((flags,),),count=2);ledger=create_face_ledger(original)
                _,before=replay_face_ledger(original,ledger)
                selected=[before['faces'][0]['face_id']]
                current,ledger,_=append_removal_ledger(original,ledger,selected)
                candidate,after=reinsert_ledger_faces(original,ledger,selected)
                for face in after['faces']:self.assertEqual(packet(candidate,face),packet(original,face))
                start=12+struct.unpack_from('<I',current,28)[0]
                stride=current[start+5]*4;old_end=start+8+2*stride+4
                new_end=old_end+stride
                self.assertEqual(candidate[start:new_end],original[start:new_end])
                self.assertEqual(candidate[new_end:],current[old_end:])
                self.assertEqual(after['growth_bytes'],stride)
                with patch('importer.model_face_reinsertion.MAX_MODEL_BYTES',len(candidate)-1):
                    with self.assertRaises(ImportError):reinsert_ledger_faces(original,ledger,selected)

    def test_missing_group_and_authored_packet_preserve_content_and_inputs(self):
        original,current,ledger,audit,request=fixtures.RemovalLedgerTests().fixture()
        selected=[f['face_id'] for f in audit['faces'] if f['group_index']==0]+[request['face_id']]
        current,ledger,_=append_removal_ledger(original,ledger,selected)
        edited=bytearray(current);vertex=12+struct.unpack_from('<I',edited,12)[0]
        struct.pack_into('<h',edited,vertex,77)
        # Surviving group settings must win over its deleted packet descriptor.
        group=12+struct.unpack_from('<I',edited,28)[0];edited[group+7]^=2
        current,ledger,before=append_content_ledger(original,ledger,bytes(edited))
        saved=deepcopy(ledger);sources=deleted_face_sources(original,ledger)
        candidate,after=reinsert_ledger_faces(original,ledger,selected)
        self.assertEqual(ledger,saved)
        self.assertEqual(after['growth_bytes'],len(candidate)-len(current))
        self.assertEqual(after['source_sha256'],sha256(current).hexdigest())
        by_id={f['face_id']:f for f in after['faces']}
        self.assertEqual(len(by_id),5)
        for identity in selected:self.assertEqual(packet(candidate,by_id[identity]),sources[identity]['packet'])
        for face in before['faces']:self.assertEqual(packet(candidate,by_id[face['face_id']]),packet(current,face))
        moved_vertex=12+struct.unpack_from('<I',candidate,12)[0]
        self.assertEqual(candidate[moved_vertex:],current[vertex:])
        first=12+struct.unpack_from('<I',candidate,28)[0]
        second=first+8+(2+1)*candidate[first+5]*4
        self.assertEqual(candidate[second+2:second+8],current[group+2:group+8])
        self.assertEqual([f['current_primitive_index'] for f in after['faces']],list(range(5)))

    def test_two_objects_rebase_tables_and_preserve_all_outside_stream_bytes(self):
        original=synthetic(((0x12,0x22),(0x22,)),count=2)
        ledger=create_face_ledger(original);_,before=replay_face_ledger(original,ledger)
        selected=[before['faces'][0]['face_id'],before['faces'][-1]['face_id']]
        current,ledger,audit=append_removal_ledger(original,ledger,selected)
        candidate,restored=reinsert_ledger_faces(original,ledger,list(reversed(selected)))
        self.assertEqual(len(restored['faces']),6)
        by_id={f['face_id']:f for f in restored['faces']}
        for face in before['faces']:self.assertEqual(packet(candidate,by_id[face['face_id']]),packet(original,face))
        # Each entire vector block and inter-object gap is copied unchanged.
        for owner in range(2):
            header=12+owner*28
            for field,count_field in ((0,4),(8,12)):
                old=12+struct.unpack_from('<I',current,header+field)[0]
                new=12+struct.unpack_from('<I',candidate,header+field)[0]
                size=8*struct.unpack_from('<I',current,header+count_field)[0]
                self.assertEqual(candidate[new:new+size],current[old:old+size])
            self.assertEqual(candidate[header+24:header+28],current[header+24:header+28])
        self.assertGreater(struct.unpack_from('<I',candidate,56)[0],struct.unpack_from('<I',current,56)[0])

    def test_empty_object_restores_last_group_descriptor_and_footer(self):
        original=synthetic(((0x22,),(0x22,)),count=2);ledger=create_face_ledger(original)
        _,audit=replay_face_ledger(original,ledger);ids=[f['face_id'] for f in audit['faces'] if f['object_index']==0]
        current,ledger,_=append_removal_ledger(original,ledger,ids)
        candidate,restored=reinsert_ledger_faces(original,ledger,ids)
        start=12+struct.unpack_from('<I',original,28)[0]
        end=start+8+3*original[start+5]*4+4
        self.assertEqual(candidate[start:end],original[start:end])
        self.assertEqual(len(restored['faces']),4)

    def test_rejects_invalid_or_active_identities_and_tampered_chain(self):
        original,current,ledger,audit,request=fixtures.RemovalLedgerTests().fixture()
        _,ledger,_=append_removal_ledger(original,ledger,[request['face_id']]);saved=deepcopy(ledger)
        for identities in ([],{},[True],['missing'],[audit['faces'][0]['face_id']],[request['face_id']]*2):
            with self.assertRaises(ImportError):reinsert_ledger_faces(original,ledger,identities)
            self.assertEqual(ledger,saved)
        bad=deepcopy(ledger);bad['operations'][-1]['proposed_sha256']='0'*64
        with self.assertRaises(ImportError):reinsert_ledger_faces(original,bad,[request['face_id']])


if __name__=='__main__':unittest.main()
