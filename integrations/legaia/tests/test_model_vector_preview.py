"""Enlarged object tables retain rigid pose ownership and prefix exclusions."""
from copy import deepcopy
from hashlib import sha256
import unittest
from importer.core import ImportError
from importer.assets import decode_tmd
from importer.animation import pose_vertices
from importer.model_authoring import preview_model_shape
from importer.model_face_ledger import create_face_ledger,append_vector_ledger,append_face_ledger,append_content_ledger
from sdk.scene_preview import preview_shape_instance
from test_model_primitives import synthetic


class VectorPreviewTests(unittest.TestCase):
    def fixture(self):
        original=synthetic(((0x22,),(0x22,),(0x22,)))
        requests=[dict(object_index=0,kind='vertices',vectors=[[1,2,3],[4,5,6]]),
                  dict(object_index=1,kind='vertices',vectors=[[7,8,9]]),
                  dict(object_index=2,kind='vertices',vectors=[[30000,30000,30000]]*3),
                  dict(object_index=0,kind='normals',vectors=[[4096,0,0]])]
        current,ledger,audit=append_vector_ledger(original,create_face_ledger(original),requests)
        donor=next(row for row in audit['faces'] if row['object_index']==1)
        current,ledger,_=append_face_ledger(original,ledger,[dict(
            face_id='face://authored/00000000-0000-4000-8000-000000000001',
            donor_face_id=donor['face_id'],fields=dict(vertices=[5,0,1,2]))])
        binding=dict(format='tmd-face-addition-v1',ledger=ledger,asset_sha256=sha256(current).hexdigest(),byte_length=len(current))
        return original,current,binding

    def test_unposed_and_posed_prefix_update_ranges_frames_and_new_face_indices(self):
        original,current,binding=self.fixture();preview=decode_tmd(original);shape=decode_tmd(current)
        raw=preview_model_shape(preview,current,binding)
        self.assertEqual(raw['vertices'],shape['vertices']);self.assertEqual(raw['triangles'],shape['triangles'])
        self.assertEqual([row['vertex_start'] for row in raw['objects']],[0,7,13])
        # Party-style prefix excludes the third equipment object, even if it grows.
        preview['objects']=preview['objects'][:2];preview['vertices']=preview['vertices'][:10]
        triangle_count=sum(row['triangle_count'] for row in preview['objects'])
        for name in ('triangles','triangle_colors','triangle_uvs','triangle_materials','triangle_normals'):
            preview[name]=preview[name][:triangle_count]
        transforms=[dict(object_index=0,translation=[10,20,30],rotation_psx=[0,0,1024]),
                    dict(object_index=1,translation=[100,200,300],rotation_psx=[0,0,0])]
        frame_transforms=[dict(object_index=0,translation=[1,2,3],rotation_psx=[0,0,0]),
                          dict(object_index=1,translation=[4,5,6],rotation_psx=[0,0,1024])]
        preview.update(posed=True,pose=dict(object_transforms=transforms),
            frames=[dict(object_transforms=frame_transforms,vertices=pose_vertices(preview['vertices'],preview['objects'],frame_transforms))])
        preview['vertices']=pose_vertices(preview['vertices'],preview['objects'],transforms)
        saved=deepcopy(preview);saved_binding=deepcopy(binding)
        result=preview_model_shape(preview,current,binding)
        self.assertEqual(preview,saved);self.assertEqual(binding,saved_binding)
        self.assertEqual(len(result['vertices']),13)
        self.assertEqual([obj['vertex_count'] for obj in result['objects']],[7,6])
        self.assertEqual(result['pose'],preview['pose'])
        self.assertEqual(result['frames'][0]['object_transforms'],frame_transforms)
        self.assertEqual(result['vertices'],pose_vertices(shape['vertices'][:13],result['objects'],transforms))
        for actual,expected in ((result['vertices'][5],[8,21,33]),(result['vertices'][12],[107,208,309]),
                                (result['frames'][0]['vertices'][5],[2,4,6]),(result['frames'][0]['vertices'][12],[-4,12,15])):
            for a,b in zip(actual,expected):self.assertAlmostEqual(a,b)
        self.assertLess(max(result['bounds']['max']),1000)
        self.assertEqual(result['objects'][1]['vertex_start'],7)
        self.assertEqual(result['triangles'][-1],shape['triangles'][sum(row['triangle_count'] for row in result['objects'])-1])
        self.assertTrue(all(index<13 for triangle in result['triangles'] for index in triangle))

    def test_scene_instance_uses_qualified_growth_without_mutating_shared_assets(self):
        original,current,binding=self.fixture();preview=decode_tmd(original)
        scene=dict(entities=[dict(entity_id=name,asset_id='model',renderable=True,geometry_key='shared',model_to_scene=[1]*16) for name in ('one','two')],
                   assets=[dict(geometry_key='shared',asset_id='model',preview=preview)])
        saved=deepcopy(scene)
        proposed=preview_shape_instance(scene,'model','one',current,binding)
        self.assertEqual(proposed['vertices'],decode_tmd(current)['vertices'])
        self.assertEqual(proposed['representation'],'proposed-shape');self.assertNotIn('authored_shape',proposed)
        self.assertEqual(scene,saved)

    def test_current_v5_geometry_applies_only_additional_growth_and_later_content(self):
        original,current,binding=self.fixture()
        preview=preview_model_shape(decode_tmd(original),current,binding)
        enlarged,ledger,_=append_vector_ledger(original,binding['ledger'],[
            dict(object_index=1,kind='vertices',vectors=[[12,13,14]])])
        next_binding=dict(binding,ledger=ledger,
            asset_sha256=sha256(enlarged).hexdigest(),byte_length=len(enlarged))
        next_preview=preview_model_shape(preview,enlarged,next_binding)
        self.assertEqual(next_preview['vertices'],decode_tmd(enlarged)['vertices'])
        self.assertEqual([obj['vertex_count'] for obj in next_preview['objects']],[7,7,8])
        import struct
        edited=bytearray(enlarged);at=12+struct.unpack_from('<I',enlarged,12)[0]
        struct.pack_into('<h',edited,at,15)
        edited,ledger,_=append_content_ledger(original,ledger,bytes(edited))
        content_binding=dict(next_binding,ledger=ledger,asset_sha256=sha256(edited).hexdigest())
        self.assertEqual(preview_model_shape(next_preview,edited,content_binding)['vertices'],decode_tmd(edited)['vertices'])
        bad=deepcopy(preview);bad['authored_shape']['ledger']['source_sha256']='0'*64
        with self.assertRaises(ImportError):preview_model_shape(bad,enlarged,next_binding)
        bad=deepcopy(preview);bad['authored_shape']['asset_sha256']='0'*64
        with self.assertRaises(ImportError):preview_model_shape(bad,enlarged,next_binding)

    def test_binding_counts_owner_and_pose_channel_tampering_reject_without_mutation(self):
        original,current,binding=self.fixture();preview=decode_tmd(original);saved=deepcopy(preview)
        for mutate in (lambda v:v.update(asset_sha256='0'*64),lambda v:v.update(byte_length=len(current)-1),
                       lambda v:v['ledger']['operations'][0]['requests'][0]['vectors'].pop(),
                       lambda v:v['ledger']['operations'][0]['requests'][0].update(object_index=1),
                       lambda v:v['ledger']['operations'][0]['requests'][0].update(object_index=True),
                       lambda v:v['ledger'].update(schema_version='legaia.model-face-addition-ledger.v4')):
            bad=deepcopy(binding);mutate(bad)
            with self.assertRaises(ImportError):preview_model_shape(preview,current,bad)
            self.assertEqual(preview,saved)
        wrong=deepcopy(preview);wrong['objects'][1]['vertex_start']=0
        with self.assertRaises(ImportError):preview_model_shape(wrong,current,binding)
        transforms=[dict(object_index=i,translation=[0,0,0],rotation_psx=[0,0,0]) for i in range(3)]
        preview.update(posed=True,pose=dict(object_transforms=transforms),frames=[dict(object_transforms=transforms[:2])])
        with self.assertRaises(ImportError):preview_model_shape(preview,current,binding)
        preview['frames']=[];preview['pose']['object_transforms'][0]['object_index']=2
        with self.assertRaises(ImportError):preview_model_shape(preview,current,binding)


if __name__=='__main__':unittest.main()
