"""Full rigid clip export checked against the independently posed source vertices."""
from copy import deepcopy
import math
import struct
import unittest
from importer.animation import pose_vertices
from importer.core import ImportError
from importer.export import encode_model_glb
from test_importer_export import preview, parse_glb


def values(doc,binary,index):
    a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
    n={'SCALAR':1,'VEC3':3,'VEC4':4}[a['type']]
    return list(struct.iter_unpack('<'+'f'*n,binary[v['byteOffset']:v['byteOffset']+v['byteLength']]))


def clip():
    p=preview();p['frames']=[]
    for angles in ([0,0,0],[512,1024,1536],[-130,2070,3500]):
        t={'object_index':0,'translation':[17,-21,43],'rotation_psx':angles}
        p['frames'].append({'object_transforms':[t],'vertices':pose_vertices(p['vertices'],p['objects'],[t]),'posed':True,'coordinate_system':'retail_psx_actor_local_y_down'})
    return p


class AnimationClipExportTests(unittest.TestCase):
    def test_quaternion_tracks_reproduce_y_reflected_source_frames(self):
        p=clip();before=deepcopy(p);raw,audit=encode_model_glb(p,clip_fps=15)
        doc,binary=parse_glb(raw);animation=doc['animations'][0]
        self.assertEqual(len(animation['channels']),2)
        samplers=animation['samplers'];self.assertTrue(all(s['interpolation']=='STEP' for s in samplers))
        times=values(doc,binary,samplers[0]['input'])
        self.assertEqual(len(times),4);self.assertAlmostEqual(times[-1][0],3/15)
        for sampler in samplers:
            for index in (sampler['input'],sampler['output']):
                self.assertNotIn('target',doc['bufferViews'][doc['accessors'][index]['bufferView']])
        ts=values(doc,binary,samplers[0]['output']);qs=values(doc,binary,samplers[1]['output'])
        self.assertEqual(ts[-1],ts[-2]);self.assertEqual(qs[-1],qs[-2])
        for i,frame in enumerate(p['frames']):
            x,y,z,w=qs[i];self.assertAlmostEqual(x*x+y*y+z*z+w*w,1,places=6)
            for original,posed in zip(p['vertices'],frame['vertices']):
                v=[original[0],-original[1],original[2]]
                cross=[2*(y*v[2]-z*v[1]),2*(z*v[0]-x*v[2]),2*(x*v[1]-y*v[0])]
                rotated=[v[0]+w*cross[0]+y*cross[2]-z*cross[1],v[1]+w*cross[1]+z*cross[0]-x*cross[2],v[2]+w*cross[2]+x*cross[1]-y*cross[0]]
                for actual,expected in zip([a+b for a,b in zip(rotated,ts[i])],[posed[0],-posed[1],posed[2]]):self.assertAlmostEqual(actual,expected,places=5)
        self.assertEqual(p,before);self.assertEqual(audit['frame_count'],3)
        self.assertEqual(audit['timing_evidence'],'caller_selected_rate_not_verified_retail_timing')

    def test_invalid_rate_pose_and_channel_mapping_reject(self):
        for fps in (True,0,121,float('nan')):
            with self.assertRaises(ImportError):encode_model_glb(clip(),clip_fps=fps)
        for change in (lambda p:p.update(posed=True),lambda p:p['frames'][0]['object_transforms'][0].update(object_index=9),lambda p:p.update(frames=[])):
            p=clip();change(p)
            with self.assertRaises(ImportError):encode_model_glb(p,clip_fps=10)
        with self.assertRaises(ImportError):encode_model_glb(clip(),0,clip_fps=10)

if __name__=='__main__':unittest.main()
