"""Panel ownership survives deleted donor faces and zero active authored faces."""
from hashlib import sha256
import unittest
from unittest.mock import patch
from importer.assets import decode_tmd
from sdk import model_face_removal,model_face_addition,model_materials,model_glb
from sdk.model_reference_faces import addition_group_mapping
import test_model_materials_post_addition as fixtures
import test_model_face_addition_project as addition_fixtures
from test_model_primitives import synthetic
from contextlib import nullcontext


class PostRemovalPanelTests(unittest.TestCase):
    def fixture(self,authored_only):
        helper=fixtures.AddedMaterialTests();self.addCleanup(helper.doCleanups)
        p,asset=helper.fixture()
        self.enterContext(patch('sdk.model_face_removal.source_key',return_value='a'*64))
        self.enterContext(patch('importer.assets.load_model_preview',side_effect=lambda _,row:decode_tmd(p._model_source(row['semantic_id']))))
        current=p.read_model_replacement(asset,p.model_overrides[asset])
        selections=[dict(object_index=0,primitive_index=index) for index in ([0,1] if authored_only else [2])]
        report=model_face_removal.review(p,asset,selections,sha256(current).hexdigest(),'a'*64)
        p.apply_model_face_removal(asset,selections,sha256(current).hexdigest(),'a'*64,report['proposed_sha256'])
        return p,asset

    def test_authored_only_group_has_original_material_owner_after_deleted_donor(self):
        p,asset=self.fixture(True)
        binding=p.model_overrides[asset];retail=p._model_source(asset);current=p.read_model_replacement(asset,binding)
        self.assertEqual(addition_group_mapping(p,asset,retail,current,binding),[[0]])
        catalog=model_materials.snapshot(p,asset)
        self.assertEqual(catalog['group_mappings'],[[0]])
        self.assertTrue(all(row['current_index'] is None for row in catalog['face_mappings'][0]))
        self.assertEqual(catalog['authored_faces'][0][0]['current_index'],0)
        edits=[dict(kind='primitive',object_index=0,primitive_index=0,values={'clut_column':7})]
        _,review=model_materials.prepare(p,asset,edits,catalog['effective_sha256'],'a'*64)
        model_materials.apply(p,asset,edits,catalog['effective_sha256'],'a'*64,review['review_key'])
        source=model_face_addition.source(p,asset,'a'*64);donor=source['topology']['faces'][0]['face_id']
        request=dict(face_id='face://authored/00000000-0000-4000-8000-000000000099',donor_face_id=donor,fields={'vertices':[0,1,2,3]})
        proposal=model_face_addition.review(p,asset,[request],source['effective_sha256'],'a'*64)
        p.apply_model_face_additions(asset,[request],source['effective_sha256'],'a'*64,proposal['proposed_sha256'])
        self.assertEqual(model_materials.snapshot(p,asset)['group_mappings'],[[0]])
        self.assertEqual(model_face_addition.source(p,asset,'a'*64)['topology']['authored_face_count'],2)

    def test_zero_active_authored_faces_retain_GLB_fingerprint_and_history_budget(self):
        p,asset=self.fixture(False)
        content,binding,report=model_glb.export_model(p,asset)
        self.assertEqual(binding['schema_version'],'legaia.model-glb-binding.v3')
        self.assertEqual(binding['authored_face_count'],0)
        self.assertEqual(report['pending_changes'],[])
        self.assertEqual(model_glb.preview_import(p,asset,content,binding)['pending_changes'],[])
        catalog=model_materials.snapshot(p,asset);self.assertEqual(catalog['authored_faces'],[[]])
        self.assertEqual(catalog['group_mappings'],[[0]])
        source=model_face_addition.source(p,asset,'a'*64)
        self.assertEqual(source['topology']['authored_face_count'],1)
        self.assertFalse(any(row['origin']=='authored' for row in source['topology']['faces']))

    def test_authored_only_second_group_compacts_to_first_with_actual_Retail_owner(self):
        helper=addition_fixtures.ModelFaceAdditionProjectTests();self.addCleanup(helper.doCleanups)
        helper.context();p,asset,*_=helper.project()
        original=synthetic(((0x12,0x22),),count=2);p._model_source=lambda *args:original
        p.disc_path='synthetic-disc.bin';p.imports[p.active_scene]={'assets':{'models':[{'semantic_id':asset}]}}
        self.enterContext(patch('importer.pipeline._disc_context',side_effect=lambda _:nullcontext()))
        self.enterContext(patch('sdk.model_face_removal.source_key',return_value='a'*64))
        source=model_face_addition.source(p,asset,'a'*64)
        donor=next(row['face_id'] for row in source['topology']['faces'] if row['source_primitive_index']==2)
        request=helper.request(donor)
        proposal=model_face_addition.review(p,asset,[request],source['effective_sha256'],'a'*64)
        p.apply_model_face_additions(asset,[request],source['effective_sha256'],'a'*64,proposal['proposed_sha256'])
        current=p.read_model_replacement(asset,p.model_overrides[asset])
        selections=[dict(object_index=0,primitive_index=i) for i in range(4)]
        proposal=model_face_removal.review(p,asset,selections,sha256(current).hexdigest(),'a'*64)
        p.apply_model_face_removal(asset,selections,sha256(current).hexdigest(),'a'*64,proposal['proposed_sha256'])
        catalog=model_materials.snapshot(p,asset)
        self.assertEqual(catalog['group_mappings'],[[1]])
        self.assertEqual(catalog['objects'][0]['groups'][0]['flags'],0x22)
        self.assertEqual(catalog['authored_faces'][0][0]['current_index'],0)


if __name__=='__main__':unittest.main()
