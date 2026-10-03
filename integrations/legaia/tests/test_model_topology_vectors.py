from hashlib import sha256
import json,struct,tempfile
from pathlib import Path
import unittest
from importer.assets import decode_tmd
from importer.model_face_removal import remove_faces
from importer.model_json import export_shape_json
from importer.model_obj import export_shape_obj
from importer.core import ImportError
from sdk.project import ProjectService,ProjectError
from test_model_primitives import synthetic

class ModelTopologyVectorTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.original=synthetic(((0x22,0x14),),count=2)
        self.current,self.removed=remove_faces(self.original,self.original,[],[dict(object_index=0,primitive_index=0)])
        self.asset='asset://fixture/model/0';self.project=ProjectService(Path(self.temp.name));self.project.active_scene='scene://fixture'
        self.project._model_source=lambda *args:self.original
        binding=dict(format='tmd-face-removal-v1',source_scene_id='scene://fixture',source_sha256=sha256(self.original).hexdigest(),asset_sha256=sha256(self.current).hexdigest(),byte_length=len(self.current),removed_faces=self.removed)
        self.project.model_overrides[self.asset]=binding
        path=self.project.root/'Authored'/'Models'/(binding['asset_sha256']+'.tmd');path.parent.mkdir(parents=True);path.write_bytes(self.current)

    def effective(self):
        binding=self.project.model_overrides[self.asset]
        self.assertEqual(binding['format'],'tmd-face-removal-v1');self.assertEqual(binding['removed_faces'],self.removed)
        return self.project.read_model_replacement(self.asset,binding)

    def test_vector_edit_binding_and_undo_redo(self):
        expected=bytearray(self.current);at=12+struct.unpack_from('<I',self.current,12)[0];struct.pack_into('<3h',expected,at,7,8,9)
        self.project.set_model_vector(self.asset,0,'vertices',0,[7,8,9],sha256(self.current).hexdigest())
        self.assertEqual(self.effective(),bytes(expected));self.project.undo();self.assertEqual(self.effective(),self.current)
        self.project.redo();self.assertEqual(self.effective(),bytes(expected))
        with self.assertRaises(ProjectError):self.project.set_model_vector(self.asset,0,'vertices',0,[1,2,3],sha256(self.current).hexdigest())

    def test_object_operations_preserve_topology_and_noop_history(self):
        for operation,values in [('translation',{'offset':[1,2,3]}),('rotation',{'axis':'z','quarter_turns':1}),('scale',{'percent':200}),('normal_length',{'length':2048})]:
            with self.subTest(operation=operation):
                candidate,report=self.project._prepare_model_object(self.asset,0,operation,values,sha256(self.current).hexdigest())
                self.assertEqual(decode_tmd(candidate)['triangles'],decode_tmd(self.current)['triangles'])
                self.assertTrue(any(row['kind']=='primitive_removal' for row in report['coordinate_changes']))
                self.project._model_candidate_changes(self.asset,self.original,candidate)
        self.project.translate_model_object(self.asset,0,[0,0,0],sha256(self.current).hexdigest());self.assertEqual(self.project.undo_stack,[])

    def test_json_obj_tmd_and_foreign_layout_rejection(self):
        doc=json.loads(export_shape_json(self.current));doc['source_sha256']=sha256(self.original).hexdigest();doc['objects'][0]['vertices'][0]=[11,12,13]
        candidate,report=self.project._prepare_model_file(self.asset,json.dumps(doc).encode(),'json')
        self.project.set_model_replacement(self.asset,candidate);self.assertEqual(decode_tmd(self.effective())['vertices'][0],[11,12,13])
        obj=export_shape_obj(candidate).replace(b'v 11 12 13',b'v 14 15 16',1)
        candidate,_=self.project._prepare_model_file(self.asset,obj,'obj');self.project.set_model_replacement(self.asset,candidate)
        self.assertEqual(decode_tmd(self.effective())['vertices'][0],[14,15,16])
        self.assertEqual(self.project._prepare_model_file(self.asset,candidate,'tmd')[0],candidate)
        with self.assertRaises(ImportError):self.project._prepare_model_file(self.asset,self.original,'tmd')
        damaged=bytearray(candidate);damaged[-1]^=1
        with self.assertRaises(ImportError):self.project.set_model_replacement(self.asset,bytes(damaged))
