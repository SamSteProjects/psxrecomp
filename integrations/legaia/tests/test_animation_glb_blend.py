import math
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from importer.animation_glb import import_animation_glb, pose_blend_config
from importer.core import ImportError
from test_animation_glb import document, encode, record


class PoseBlend(unittest.TestCase):
    def candidate(self,native,external,translation,rotation,**kw):
        doc,payload=document(external)
        return import_animation_glb(record(native),encode(doc,payload),fps=15,
            external_pose_blend=dict(translation_weight=translation,rotation_weight=rotation),**kw)

    def test_zero_influence_keeps_every_native_angle_byte_and_opaque_field(self):
        native=[[([i-128,i%17,-i%11],[i,(i*37)%256,(i*71)%256])] for i in range(256)]
        external=[[([500,600,700],[64,32,16])]]*256
        candidate,report=self.candidate(native,external,0,0)
        self.assertEqual(candidate,record(native));self.assertEqual(report['changes'],[])

    def test_full_influence_matches_legacy_import_exactly(self):
        native=[[([10,20,30],[16,32,48])],[([20,30,40],[17,33,49])]]
        external=[[([12,24,36],[18,34,50])],[([22,34,46],[19,35,51])]]
        doc,payload=document(external);legacy=import_animation_glb(record(native),encode(doc,payload),fps=15)[0]
        self.assertEqual(self.candidate(native,external,1,1)[0],legacy)

    def test_fractional_weights_blend_each_native_frame_independently(self):
        native=[[([10,0,0],[0,0,0])],[([20,0,0],[0,0,16])]]
        external=[[([14,0,0],[0,0,16])],[([28,0,0],[0,0,32])]]
        expected=[[([11,0,0],[0,0,8])],[([22,0,0],[0,0,24])]]
        candidate,report=self.candidate(native,external,.25,.5)
        self.assertEqual(candidate,record(expected));self.assertEqual(report['external_pose_blend'],dict(translation_weight=.25,rotation_weight=.5))

    def test_translation_and_rotation_can_be_imported_separately(self):
        native=[[([10,20,30],[0,0,0])]];external=[[([14,24,34],[0,0,16])]]
        self.assertEqual(self.candidate(native,external,0,1)[0],record([[([10,20,30],[0,0,16])]]))
        self.assertEqual(self.candidate(native,external,1,0)[0],record([[([14,24,34],[0,0,0])]]))

    def test_reference_alignment_precedes_current_frame_blending(self):
        native=[[([10,0,0],[0,0,0])],[([20,0,0],[0,0,32])]]
        external=[[([500,0,0],[0,0,64])],[([508,0,0],[0,0,80])]]
        # Reference correction rotates the external +X displacement to native -Y.
        # Then blend that aligned (10,-8,0) pose with native (20,0,0).
        expected=[[([10,0,0],[0,0,0])],[([15,-4,0],[0,0,24])]]
        candidate,_=self.candidate(native,external,.5,.5,object_node_indices=[0],external_pose_alignment=dict(mode='native_reference_local',source_frame_index=0,reference_seconds=0))
        self.assertEqual(candidate,record(expected))

    def test_rotation_shortest_arc_across_wrap_and_signed_translation_ties(self):
        native=[[([0,0,0],[0,0,248])]];external=[[([-1,1,0],[0,0,8])]]
        self.assertEqual(self.candidate(native,external,.5,.5)[0],record([[([-1,1,0],[0,0,0])]]))

    def test_invalid_weights_zero_still_validates_and_final_native_bounds(self):
        valid=dict(translation_weight=.5,rotation_weight=.5)
        for bad in (None,{},dict(valid,extra=True),dict(valid,rotation_weight=True),dict(valid,translation_weight='0.5'),dict(valid,translation_weight=-.1),dict(valid,rotation_weight=1.01),dict(valid,rotation_weight=math.nan)):
            with self.subTest(bad=bad),self.assertRaises(ImportError):pose_blend_config(bad)
        native=[[([0,0,0],[0,0,0])]];external=[[([5000,0,0],[0,0,0])]]
        self.assertEqual(self.candidate(native,external,.01,0)[0],record([[([50,0,0],[0,0,0])]]))
        with self.assertRaises(ImportError):self.candidate(native,external,1,0)
        doc,payload=document(external);doc['nodes'][0]['scale']=[2,2,2]
        with self.assertRaises(ImportError):import_animation_glb(record(native),encode(doc,payload),fps=15,external_pose_blend=dict(translation_weight=0,rotation_weight=0))

    def test_retained_recipe_validates_weights_even_with_recomputed_receipt_hash(self):
        from sdk.animation_sources import retain, validate_collection
        from sdk.project import ProjectError, digest
        doc,payload=document([[([0,0,0],[0,0,0])]])
        target='scene://town01/actors/man-p1/0011'
        binding=dict(schema_version='legaia.animation-glb-binding.v1',scene_id='scene://town01',entity_id=target,
                     external_pose_blend=dict(translation_weight=.25,rotation_weight=.5))
        with tempfile.TemporaryDirectory() as folder:
            records,receipt=retain(SimpleNamespace(root=Path(folder)),{},encode(doc,payload),kind='imported',target_id=target,
                binding=binding,animation_index=0,source_frame_indices=None,candidate_sha256='a'*64,review_key='b'*64)
            validate_collection(records)
            for bad in [None,{},dict(translation_weight=True,rotation_weight=.5),dict(translation_weight=.25,rotation_weight=2)]:
                altered=dict(receipt,binding=dict(binding,external_pose_blend=bad))
                altered['receipt_key']=digest({k:v for k,v in altered.items() if k!='receipt_key'})
                with self.subTest(bad=bad),self.assertRaises(ProjectError):validate_collection({altered['receipt_key']:altered})


if __name__=='__main__':unittest.main()
