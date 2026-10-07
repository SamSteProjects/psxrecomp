"""Independent native-reference rigid-motion alignment oracles."""
from copy import deepcopy
import math
import unittest
from unittest.mock import patch
from importer.animation_glb import import_animation_glb, pose_alignment_config
from importer.core import ImportError
from importer.animation import decode_animation_record
from test_animation_glb import document, encode, record


class PoseAlignment(unittest.TestCase):
    def candidate(self, native, external, *, frame=0, seconds=0, **kw):
        doc,payload=document(external)
        return import_animation_glb(record(native),encode(doc,payload),fps=15,
            object_node_indices=list(range(len(native[0]))),external_pose_alignment=dict(mode='native_reference_local',source_frame_index=frame,reference_seconds=seconds),**kw)

    def test_offset_external_rig_preserves_native_reference_pose_and_opaque_bytes(self):
        native=[[([10,-20,30],[16,32,48])],[([10,-20,30],[16,32,48])]]
        external=[[([600,700,-400],[64,0,0])],[([600,700,-400],[64,0,0])]]
        candidate,report=self.candidate(native,external)
        self.assertEqual(candidate,record(native));self.assertEqual(report['changes'],[])
        self.assertEqual(report['external_pose_alignment'],dict(mode='native_reference_local',source_frame_index=0,reference_seconds=0.0))

    def test_translation_delta_rotates_into_native_reference_axes(self):
        native=[[([10,-20,30],[0,0,64])],[([10,-20,30],[0,0,64])]]
        external=[[([500,600,700],[0,0,0])],[([503,600,700],[0,0,0])]]
        expected=deepcopy(native);expected[1][0][0][1]=-17
        self.assertEqual(self.candidate(native,external)[0],record(expected))

    def test_external_rotation_reference_is_removed_before_motion_composition(self):
        native=[[([10,20,30],[0,0,16])],[([10,20,30],[0,0,16])]]
        external=[[([0,0,0],[0,0,64])],[([0,0,0],[0,0,80])]]
        expected=deepcopy(native);expected[1][0][1][2]=32
        self.assertEqual(self.candidate(native,external)[0],record(expected))

    def test_selected_native_frame_external_reference_time_and_reverse_sampling(self):
        native=[[([1,2,3],[0,0,0])],[([10,20,30],[0,0,0])]]
        external=[[([100,0,0],[0,0,0])],[([105,0,0],[0,0,0])]]
        expected=deepcopy(native);expected[0][0][0][:]=[5,20,30];expected[1][0][0][:]=[10,20,30]
        self.assertEqual(self.candidate(native,external,frame=1,seconds=1/15)[0],record(expected))
        expected[0][0][0][:]=[10,20,30];expected[1][0][0][:]=[5,20,30]
        self.assertEqual(self.candidate(native,external,frame=1,seconds=1/15,external_sampling=dict(start_seconds=1/15,rate=-1))[0],record(expected))

    def test_each_object_uses_its_own_native_and_external_reference(self):
        native=[[([10,0,0],[0,0,0]),([0,20,0],[0,0,0])]]*2
        external=[[([100,0,0],[0,0,0]),([200,0,0],[0,0,0])],[([103,0,0],[0,0,0]),([205,0,0],[0,0,0])]]
        expected=[deepcopy(native[0]),[([13,0,0],[0,0,0]),([5,20,0],[0,0,0])]]
        self.assertEqual(self.candidate(native,external)[0],record(expected))

    def test_invalid_settings_mapping_requirement_and_native_overflow(self):
        valid=dict(mode='native_reference_local',source_frame_index=0,reference_seconds=0)
        for bad in (None,{},dict(valid,extra=True),dict(valid,mode='guess'),dict(valid,source_frame_index=True),dict(valid,source_frame_index=2),dict(valid,reference_seconds=math.inf),dict(valid,reference_seconds=-1)):
            with self.subTest(bad=bad),self.assertRaises(ImportError):pose_alignment_config(bad,2)
        frames=[[([0,0,0],[0,0,0])]]*2;doc,payload=document(frames)
        with self.assertRaisesRegex(ImportError,'explicit'):import_animation_glb(record(frames),encode(doc,payload),fps=15,external_pose_alignment=valid)
        native=[[([2047,0,0],[0,0,0])]]*2;external=[[([0,0,0],[0,0,0])],[([1,0,0],[0,0,0])]]
        with self.assertRaisesRegex(ImportError,'signed twelve'):self.candidate(native,external)

    def test_noncommuting_rotations_match_independent_matrix_composition(self):
        def multiply(a,b):return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
        def matrix(ticks):
            x,y,z=[v*math.tau/256 for v in ticks];cx,sx,cy,sy,cz,sz=math.cos(x),math.sin(x),math.cos(y),math.sin(y),math.cos(z),math.sin(z)
            return multiply(multiply([[cz,-sz,0],[sz,cz,0],[0,0,1]],[[cy,0,sy],[0,1,0],[-sy,0,cy]]),[[1,0,0],[0,cx,-sx],[0,sx,cx]])
        n=[40,24,8];e0=[32,48,64];e1=[64,16,48]
        native=[[([10,20,30],n)],[([10,20,30],n)]];external=[[([100,200,300],e0)],[([103,204,305],e1)]]
        candidate,_=self.candidate(native,external);actual=decode_animation_record(candidate)['frames'][1]['object_transforms'][0]
        inverse=list(map(list,zip(*matrix(e0))));correction=multiply(matrix(n),inverse);expected=multiply(correction,matrix(e1));rotation=matrix([v/16 for v in actual['rotation_psx']]);error=multiply(rotation,list(map(list,zip(*expected))));angle=math.acos(max(-1,min(1,(sum(error[i][i] for i in range(3))-1)/2)))
        self.assertLessEqual(math.degrees(angle),2.2)
        position=[prior+sum(correction[i][j]*[3,4,5][j] for j in range(3)) for i,prior in enumerate([10,20,30])]
        rounded=[math.floor(v+.5) if v>=0 else math.ceil(v-.5) for v in position]
        self.assertEqual(actual['translation'],rounded)

    def test_reference_sample_participates_in_the_hierarchy_budget(self):
        frames=[[([0,0,0],[0,0,0])]]*2;doc,payload=document(frames)
        with patch('importer.animation_glb.MAX_HIERARCHY_SAMPLES',2):
            self.assertEqual(import_animation_glb(record(frames),encode(doc,payload),fps=15)[0],record(frames))
            with self.assertRaises(ImportError):self.candidate(frames,frames)


if __name__=='__main__':unittest.main()
