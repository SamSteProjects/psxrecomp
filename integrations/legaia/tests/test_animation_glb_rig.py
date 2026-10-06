from copy import deepcopy
import struct,unittest
from importer.animation_glb import import_animation_glb
from importer.core import ImportError
from test_animation_glb import document,encode,record,changed_key

def joint_rig(doc,payload):
    doc=deepcopy(doc);count=len(doc['nodes']);roots=doc['scenes'][doc.get('scene',0)]['nodes']
    for index,node in enumerate(doc['nodes']):node.pop('extras',None);node['name']='Rig joint '+str(index)
    # Node-only animation fixtures need an ignored mesh manifest for the skin instance.
    doc.setdefault('meshes',[{}])
    root=count;mesh=count+1;unused=count+2
    doc['nodes'].extend([dict(name='Rig root',children=roots+[unused]),dict(name='Skin geometry',mesh=0,skin=0,scale=[2,3,4]),dict(name='Unmapped joint')])
    doc['scenes'][doc.get('scene',0)]['nodes']=[root,mesh]
    joints=list(range(count))+[unused];identity=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
    offset=len(payload);payload+=struct.pack('<'+str(len(joints)*16)+'f',*(identity*len(joints)))
    view=len(doc['bufferViews']);doc['bufferViews'].append(dict(buffer=0,byteOffset=offset,byteLength=len(joints)*64))
    accessor=len(doc['accessors']);doc['accessors'].append(dict(bufferView=view,componentType=5126,count=len(joints),type='MAT4'))
    doc['skins']=[dict(joints=joints,skeleton=root,inverseBindMatrices=accessor)]
    if doc.get('animations'):
        channel=deepcopy(doc['animations'][0]['channels'][0]);channel['target']=dict(node=unused,path=channel['target']['path']);doc['animations'][0]['channels'].append(channel)
    return doc,payload

class JointRigTests(unittest.TestCase):
    def fixture(self):
        frames=[[([i*12,3,-2],[i*8,0,0]) for i in range(3)]]*3
        doc,payload=document(frames);return record(frames),doc,payload

    def test_selected_joint_motion_preserves_native_bytes_and_ignores_skin_geometry(self):
        source,doc,payload=self.fixture();rig,data=joint_rig(doc,payload)
        actual,report=import_animation_glb(source,encode(rig,data),fps=15,object_node_indices=[0,1,2],external_skin_index=0)
        self.assertEqual(actual,source);r=report['external_rig'];self.assertEqual(r['mapped_joint_nodes'],[0,1,2]);self.assertEqual(r['skin_mesh_nodes'],[4]);self.assertFalse(r['mesh_skinning_applied']);self.assertEqual(r['inverse_bind_count'],4)
        self.assertEqual(r['ignored_channels'],[dict(node_index=5,path=rig['animations'][0]['channels'][0]['target']['path'])])
        changed=changed_key(doc,payload,'translation',1,[31,-3,-2],obj=2);rig,data=joint_rig(doc,changed)
        expected,_=import_animation_glb(source,encode(doc,changed),fps=15)
        actual,_=import_animation_glb(source,encode(rig,data),fps=15,object_node_indices=[0,1,2],external_skin_index=0);self.assertEqual(actual,expected)

    def test_rig_requires_explicit_mapping_and_valid_scene_joint_witnesses(self):
        source,doc,payload=self.fixture();rig,data=joint_rig(doc,payload)
        for kwargs in ({},{'external_skin_index':0},{'external_skin_index':True,'object_node_indices':[0,1,2]},{'external_skin_index':1,'object_node_indices':[0,1,2]}):
            with self.assertRaises(ImportError):import_animation_glb(source,encode(rig,data),fps=15,**kwargs)
        changes=[lambda d:d['skins'][0].update(joints=[0,0,1]),lambda d:d['skins'][0].update(joints=[0,1]),lambda d:d['skins'][0].update(skeleton=4),lambda d:d['nodes'][3].update(children=[0,1,2]),lambda d:d['nodes'][0].update(scale=[2,1,1]),lambda d:d['accessors'][-1].update(count=1),lambda d:d['accessors'][-1].update(type='VEC4')]
        for change in changes:
            bad=deepcopy(rig);change(bad)
            with self.assertRaises(ImportError):import_animation_glb(source,encode(bad,data),fps=15,object_node_indices=[0,1,2],external_skin_index=0)
        bad=bytearray(data);struct.pack_into('<f',bad,len(payload)+12,1)
        with self.assertRaisesRegex(ImportError,'affine'):import_animation_glb(source,encode(rig,bytes(bad)),fps=15,object_node_indices=[0,1,2],external_skin_index=0)

    def test_optional_inverse_bind_data_does_not_change_rigid_pose_semantics(self):
        source,doc,payload=self.fixture();rig,data=joint_rig(doc,payload);rig['skins'][0].pop('inverseBindMatrices')
        actual,r=import_animation_glb(source,encode(rig,data),fps=15,object_node_indices=[0,1,2],external_skin_index=0);self.assertEqual(actual,source);self.assertIsNone(r['external_rig']['inverse_bind_accessor'])

if __name__=='__main__':unittest.main()
