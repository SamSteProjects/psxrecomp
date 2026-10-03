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

    def test_retained_face_preview_apply_retail_identity_and_undo(self):
        from unittest.mock import patch
        from importer.model_primitives import inspect_model_primitives
        key='a'*64
        row=inspect_model_primitives(self.current,include_normal_references=True)['objects'][0]['primitives'][0]
        edit=dict(object_index=0,primitive_index=0,vertices=row['vertices'],uvs=row['uvs'],colors=[[7,8,9]])
        with patch('sdk.scene_preview.source_key',return_value=key):
            source=self.project.model_primitive_source(self.asset)
            self.assertEqual(source['schema_version'],'legaia.model-primitives.v3')
            self.assertEqual(source['face_mappings'][0][1],dict(retail_index=1,current_index=0))
            report=self.project.preview_model_primitives(self.asset,[edit],sha256(self.current).hexdigest(),key)
            self.assertTrue(any(r['kind']=='primitive' and r['primitive_index']==1 for r in report['coordinate_changes']))
            with self.assertRaises(ProjectError):self.project.set_model_primitives(self.asset,[edit],sha256(self.current).hexdigest(),key,'0'*64)
            self.project.set_model_primitives(self.asset,[edit],sha256(self.current).hexdigest(),key,report['proposed_sha256'])
            updated=self.effective();self.assertNotEqual(updated,self.current)
            self.project.undo();self.assertEqual(self.effective(),self.current)
            self.project.redo();self.assertEqual(self.effective(),updated)

    def test_removal_retarget_complete_current_words_and_review_guards(self):
        from importer.model_primitives import inspect_model_primitives, _layout
        for operation,field,method in [('vertex_references','vertices',self.project.retarget_model_vertices),('normal_references','normal_indices',self.project.retarget_model_normals)]:
            with self.subTest(operation=operation):
                expected=bytearray(self.current);words=[]
                for row in inspect_model_primitives(self.current,include_normal_references=True)['objects'][0]['primitives']:
                    values=row[field]
                    if values is None:continue
                    start=_layout(row['flags'])[1] if field=='vertices' else ((18 if row['corner_count']==3 else 20) if row['gouraud'] else (12 if row['corner_count']==3 else 20))
                    for corner,value in enumerate(values):
                        if value==0:
                            at=row['byte_offset']+start+corner*2;struct.pack_into('<H',expected,at,24);words.append(at)
                self.assertTrue(words)
                candidate,report=self.project._prepare_model_object(self.asset,0,operation,{'from_index':0,'to_index':3},sha256(self.current).hexdigest())
                self.assertEqual(candidate,bytes(expected));self.assertEqual({r['byte_offset'] for r in report['changes_from_current']},set(words))
                with self.assertRaises(ProjectError):method(self.asset,0,0,3,sha256(self.current).hexdigest(),'0'*64)
                method(self.asset,0,0,3,sha256(self.current).hexdigest(),report['proposed_sha256'])
                self.assertEqual(self.effective(),bytes(expected))
                self.project.undo();self.assertEqual(self.effective(),self.current)
                self.project.redo();self.assertEqual(self.effective(),bytes(expected));self.project.undo()

    def test_material_review_after_dropped_group_preserves_removal(self):
        from contextlib import nullcontext
        from unittest.mock import patch
        from sdk.model_materials import snapshot,prepare,apply
        current,removed=remove_faces(self.original,self.current,self.removed,[dict(object_index=0,primitive_index=0)])
        self.current=current;self.removed=removed
        binding=self.project.model_overrides[self.asset];binding.update(asset_sha256=sha256(current).hexdigest(),removed_faces=removed)
        (self.project.root/'Authored'/'Models'/(binding['asset_sha256']+'.tmd')).write_bytes(current)
        self.project.disc_path='private';self.project.imports[self.project.active_scene]={'assets':{'models':[{'semantic_id':self.asset}]}}
        key='a'*64
        edits=[dict(kind='primitive',object_index=0,primitive_index=0,values={'page_column':3}),dict(kind='group',object_index=0,group_index=0,values={'semi_transparent':False})]
        with patch('importer.pipeline._disc_context',return_value=nullcontext()),patch('sdk.scene_preview.source_key',return_value=key):
            source=snapshot(self.project,self.asset)
            self.assertEqual(source['schema_version'],'legaia.model-material-source.v2');self.assertEqual(source['group_mappings'],[[1]])
            self.assertEqual(source['face_mappings'][0][2],dict(retail_index=2,current_index=0))
            candidate,report=prepare(self.project,self.asset,edits,sha256(current).hexdigest(),key)
            self.assertTrue(any(row['kind']=='primitive_removal' for row in report['coordinate_changes']))
            self.assertTrue(any(row['kind']=='primitive' and row['primitive_index']==2 for row in report['coordinate_changes']))
            with self.assertRaises(ProjectError):apply(self.project,self.asset,edits,sha256(current).hexdigest(),key,'0'*64)
            apply(self.project,self.asset,edits,sha256(current).hexdigest(),key,report['review_key'])
            self.assertEqual(self.effective(),candidate);self.project.undo();self.assertEqual(self.effective(),current);self.project.redo();self.assertEqual(self.effective(),candidate)

    def test_glb_removal_profile_roundtrip_and_actual_retail_audit(self):
        from importer.model_glb import export_model_glb,import_model_glb,VERTEX_ID
        from test_model_glb import rewrite,rows
        from sdk.model_glb import _audits
        glb,profile=export_model_glb(self.current,decode_tmd(self.current))
        self.assertEqual(import_model_glb(self.current,glb,profile)[0],self.current)
        def edit(doc,binary):
            for mesh in doc['meshes']:
                for primitive in mesh['primitives']:
                    for (at,xyz),(_,identity) in zip(rows(doc,binary,primitive,'POSITION'),rows(doc,binary,primitive,VERTEX_ID)):
                        if identity[0]==0:struct.pack_into('<f',binary,at,xyz[0]+2)
        changed=rewrite(glb,edit);candidate,_=import_model_glb(self.current,changed,profile)
        expected=bytearray(self.current);at=12+struct.unpack_from('<I',self.current,12)[0];struct.pack_into('<h',expected,at,struct.unpack_from('<h',self.current,at)[0]+2)
        self.assertEqual(candidate,bytes(expected))
        snapshot=dict(retail=self.original,effective=self.current,binding=dict(schema_version='legaia.model-glb-binding.v2',source_sha256=sha256(self.original).hexdigest(),effective_sha256=sha256(self.current).hexdigest(),removed_faces=self.removed))
        changes,pending=_audits(snapshot,candidate);self.assertTrue(any(row['kind']=='primitive_removal' for row in changes));self.assertEqual(len(pending),1)
        self.project.set_model_replacement(self.asset,candidate);self.assertEqual(self.effective(),candidate);self.project.undo();self.assertEqual(self.effective(),self.current)
