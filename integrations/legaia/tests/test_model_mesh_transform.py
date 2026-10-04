"""Static glTF TRS/matrix baking preserves positions, normals and corner order."""
import math
import unittest
from importer.core import ImportError
from importer.model_mesh_append import decode_append_mesh,inspect_append_mesh
from importer.model_mesh_transform import IDENTITY
from test_model_mesh_append import glb


class MeshTransformTests(unittest.TestCase):
    def test_trs_matches_column_major_matrix_and_inverse_transpose(self):
        rotation=[0,0,math.sqrt(.5),math.sqrt(.5)]
        trs=glb(lambda doc:doc['nodes'][0].update(translation=[10,20,30],rotation=rotation,scale=[2,3,4]),normals=[[1,1,0]]*4)
        matrix=[0,2,0,0,-3,0,0,0,0,0,4,0,10,20,30,1]
        explicit=glb(lambda doc:doc['nodes'][0].update(matrix=matrix),normals=[[1,1,0]]*4)
        a,b=decode_append_mesh(trs),decode_append_mesh(explicit)
        self.assertEqual(a['vertices'],[[10,-20,30],[-290,-20,30],[10,-220,30],[-290,-220,30]])
        for key in ('vertices','triangles','triangle_normals'):self.assertEqual(a[key],b[key])
        expected=[round(-2/math.sqrt(13)*4096),round(-3/math.sqrt(13)*4096),0]
        self.assertEqual(a['triangle_normals'],[[expected]*3]*2)
        self.assertTrue(a['node_transform']['winding_reversed'])
        self.assertAlmostEqual(a['node_transform']['determinant'],24)
        self.assertEqual(inspect_append_mesh(trs)['node_transform'],a['node_transform'])

    def test_mirrored_scale_preserves_matching_uv_normal_corner_order(self):
        content=glb(lambda doc:doc['nodes'][0].update(translation=[10,20,30],scale=[-1,2,1]),
            normals=[[1,1,0]]*4,uvs=[[0,0],[1,0],[0,1],[1,1]])
        geometry=decode_append_mesh(content)
        self.assertEqual(geometry['vertices'],[[10,-20,30],[-90,-20,30],[10,-220,30],[-90,-220,30]])
        self.assertEqual(geometry['triangles'],[[0,1,2],[1,3,2]])
        self.assertEqual(geometry['triangle_uvs'][0],[[0,0],[1,0],[0,1]])
        self.assertFalse(geometry['node_transform']['winding_reversed'])
        self.assertEqual(geometry['triangle_normals'][0][0],[round(-2/math.sqrt(5)*4096),round(-1/math.sqrt(5)*4096),0])

    def test_invalid_transform_rejects_and_identity_preserves_existing_contract(self):
        self.assertNotIn('node_transform',decode_append_mesh(glb()))
        self.assertEqual(decode_append_mesh(glb())['vertices'],decode_append_mesh(glb(lambda doc:doc['nodes'][0].update(matrix=IDENTITY)))['vertices'])
        bad_affine=list(IDENTITY);bad_affine[15]=2
        shear=list(IDENTITY);shear[4]=.1
        for transform in (dict(scale=[0,1,1]),dict(scale=[True,1,1]),dict(rotation=[0,0,0,0]),dict(rotation=[1,1,1,1]),dict(matrix=bad_affine),dict(matrix=shear),dict(matrix=IDENTITY,translation=[0,0,0]),dict(translation=[40000,0,0])):
            with self.assertRaises(ImportError):decode_append_mesh(glb(lambda doc:doc['nodes'][0].update(transform)))


if __name__=='__main__':unittest.main()
