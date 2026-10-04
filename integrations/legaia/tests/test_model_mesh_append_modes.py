"""Standard strip/fan winding survives reviewed native packet publication."""
import unittest
from unittest.mock import patch
from importer.core import ImportError
from importer.model_mesh_append import decode_append_mesh
import test_model_mesh_append as mesh_tests
from test_model_mesh_append import glb


class MeshAppendModeTests(unittest.TestCase):
    def test_strip_parity_and_fan_anchor_preserve_corner_attributes(self):
        positions=[[0,0,0],[100,0,0],[0,100,0],[100,100,0],[0,200,0]]
        normals=[[1,0,0],[0,1,0],[0,0,1],[-1,0,0],[0,-1,0]]
        uvs=[[0,0],[1,0],[0,.5],[1,.5],[0,1]]
        colors=[[1,0,0],[0,1,0],[0,0,1],[1,1,0],[1,0,1]]
        for mode,indices,expected in (
                (5,[0,1,2,3,4],[[0,2,1],[2,3,1],[2,4,3]]),
                (6,[0,1,3,2,4],[[0,3,1],[0,2,3],[0,4,2]])):
            # The fan's last triangle above is collinear; use a noncollinear tail.
            source=[row[:] for row in positions]
            if mode==6:source[4]=[-100,200,0]
            report=decode_append_mesh(glb(positions=source,indices=indices,mode=mode,
                normals=normals,uvs=uvs,colors=colors))
            for ordinal,corners in enumerate(expected):
                self.assertEqual([report['vertices'][i] for i in report['triangles'][ordinal]],
                    [[source[i][0],-source[i][1],source[i][2]] for i in corners])
                self.assertEqual(report['triangle_normals'][ordinal],
                    [[normals[i][0]*4096,-normals[i][1]*4096,normals[i][2]*4096] for i in corners])
                self.assertEqual(report['triangle_uvs'][ordinal],[uvs[i] for i in corners])
                self.assertEqual(report['triangle_colors'][ordinal],[colors[i] for i in corners])
        nonindexed=decode_append_mesh(glb(positions=positions,mode=5,
            changes=lambda d:d['meshes'][0]['primitives'][0].pop('indices')))
        self.assertEqual(len(nonindexed['triangles']),3)
        fan=decode_append_mesh(glb(positions=[positions[i] for i in (0,1,3,2)],mode=6,
            changes=lambda d:d['meshes'][0]['primitives'][0].pop('indices')))
        self.assertEqual(len(fan['triangles']),2)

    def test_modes_bounds_degeneracy_and_expanded_face_budget(self):
        for mode in (5,6):
            for indices in ([0,1],[0,1,4],[0,1,1,2]):
                with self.subTest(mode=mode,indices=indices),self.assertRaises(ImportError):
                    decode_append_mesh(glb(mode=mode,indices=indices))
            with self.assertRaisesRegex(ImportError,'face budget'):
                decode_append_mesh(glb(mode=mode,indices=[0,1,2]*44))
        for mode in (0,1,2,3,7,True,5.0):
            with self.subTest(mode=mode),self.assertRaises(ImportError):
                decode_append_mesh(glb(mode=mode))

    def test_actual_commands_undo_persistence_build_and_browser_for_both_modes(self):
        for mode,indices in ((5,[0,1,2,3]),(6,[0,1,3,2])):
            for method in ('test_one_command_undo_save_reopen_and_normal_build',
                           'test_actual_reviews_qualify_browser_geometry_and_ownership'):
                with self.subTest(mode=mode,method=method):
                    case=mesh_tests.MeshAppendTests(method)
                    try:
                        with patch('test_model_mesh_append.glb',side_effect=lambda **kw:glb(mode=mode,indices=indices,**kw)):
                            getattr(case,method)()
                    finally:case.doCleanups()


if __name__=='__main__':unittest.main()
