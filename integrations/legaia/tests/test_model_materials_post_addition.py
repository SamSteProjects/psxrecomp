"""Material reviews preserve stable added faces and replayable content history."""
from contextlib import nullcontext
from copy import deepcopy
from hashlib import sha256
import unittest
from unittest.mock import patch

from sdk import model_materials
from sdk.project import ProjectError, ProjectService
from sdk.model_face_addition import source
from importer.core import ImportError as ModelImportError
import test_model_growth as fixtures
from test_model_primitive_workflow import http_server
import test_model_face_addition_project as addition_fixtures


class AddedMaterialTests(unittest.TestCase):
    def fixture(self):
        helper = fixtures.ModelGrowthTests(); self.addCleanup(helper.doCleanups)
        project, asset, *_ = helper.fixture()
        project.disc_path = 'synthetic-disc.bin'
        self.enterContext(patch('importer.pipeline._disc_context', side_effect=lambda _: nullcontext()))
        return project, asset

    def test_review_apply_undo_save_and_repeated_review_preserve_added_identity(self):
        p, asset = self.fixture()
        stable = source(p, asset, 'a'*64)['topology']['faces']
        before = p.read_model_replacement(asset, p.model_overrides[asset])
        catalog = model_materials.snapshot(p, asset)
        self.assertEqual(catalog['schema_version'], 'legaia.model-material-source.v3')
        added = catalog['authored_faces'][0][0]
        self.assertEqual(catalog['group_mappings'], [[0]])
        owned = {row['current_index'] for row in catalog['face_mappings'][0] if row['current_index'] is not None}
        owned.update(row['current_index'] for row in catalog['authored_faces'][0])
        self.assertEqual(owned, set(range(3)))
        edits = [dict(kind='primitive', object_index=0, primitive_index=added['current_index'], values={'clut_column':7}),
                 dict(kind='group', object_index=0, group_index=0, values={'semi_transparent':False})]
        saved = deepcopy((p.model_overrides, p.undo_stack, p.redo_stack))
        candidate, report = model_materials.prepare(p, asset, edits, sha256(before).hexdigest(), 'a'*64)
        self.assertEqual((p.model_overrides, p.undo_stack, p.redo_stack), saved)
        self.assertEqual(report['schema_version'], 'legaia.model-material-review.v2')
        self.assertEqual(report['comparison'], 'current_addition_topology')
        self.assertEqual(report['coordinate_changes'], report['changes_from_current'])
        group = next(row for row in report['changes_from_current'] if row['kind']=='primitive_group')
        self.assertEqual(group['primitive_indices'], [0,1,2])
        with self.assertRaises(ProjectError):
            model_materials.apply(p, asset, edits, sha256(before).hexdigest(), 'a'*64, '0'*64)
        self.assertEqual((p.model_overrides, p.undo_stack, p.redo_stack), saved)
        model_materials.apply(p, asset, edits, sha256(before).hexdigest(), 'a'*64, report['review_key'])
        binding = deepcopy(p.model_overrides[asset])
        self.assertEqual(binding['ledger']['schema_version'], 'legaia.model-face-addition-ledger.v2')
        self.assertEqual(source(p, asset, 'a'*64)['topology']['faces'], stable)
        self.assertEqual(p.read_model_replacement(asset, binding), candidate)
        with self.assertRaises(ProjectError):
            model_materials.prepare(p, asset, edits, sha256(before).hexdigest(), 'a'*64)
        p.undo(); self.assertEqual(p.read_model_replacement(asset, p.model_overrides[asset]), before)
        p.redo(); self.assertEqual(p.read_model_replacement(asset, p.model_overrides[asset]), candidate)
        _, noop = model_materials.prepare(p, asset, edits, sha256(candidate).hexdigest(), 'a'*64)
        self.assertEqual(noop['coordinate_changes'], [])
        with self.assertRaises(ProjectError):
            model_materials.apply(p, asset, edits, sha256(candidate).hexdigest(), 'a'*64, noop['review_key'])
        p.save()
        with patch.object(ProjectService, '_model_source', side_effect=p._model_source):
            reopened = ProjectService.open(p.root)
            self.assertEqual(reopened.model_overrides[asset], binding)
            self.assertEqual(reopened.read_model_replacement(asset, binding), candidate)
            self.assertEqual(model_materials.snapshot(reopened, asset)['authored_faces'], catalog['authored_faces'])

    def test_stale_or_invalid_material_draft_does_not_mutate_topology(self):
        p, asset = self.fixture(); catalog=model_materials.snapshot(p,asset)
        saved=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack))
        edits=[dict(kind='primitive',object_index=0,primitive_index=catalog['authored_faces'][0][0]['current_index'],values={'clut_column':5})]
        for expected,key,draft in [('0'*64,'a'*64,edits),(catalog['effective_sha256'],'0'*64,edits),
                                   (catalog['effective_sha256'],'a'*64,[{**edits[0],'values':{'tpage':1}}])]:
            with self.assertRaises((ProjectError,ModelImportError)):
                model_materials.prepare(p,asset,draft,expected,key)
            self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),saved)

    def test_HTTP_source_review_apply_and_stale_repeat(self):
        p,asset=self.fixture()
        p.assets.records[asset]=dict(semantic_id=asset,source_record={})
        with http_server(p) as (server,post), patch.object(server,'state',return_value={'applied':True}), \
                patch.object(server,'model_preview',side_effect=lambda asset,prepared:prepared):
            status,catalog=post('/api/model-material-source',dict(asset_id=asset))
            self.assertEqual(status,200)
            face=catalog['authored_faces'][0][0]
            edits=[dict(kind='primitive',object_index=0,primitive_index=face['current_index'],values={'clut_column':7})]
            body=dict(asset_id=asset,source_key='a'*64,expected_sha256=catalog['effective_sha256'],edits=edits)
            before=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack))
            status,report=post('/api/model-material-preview',body)
            self.assertEqual(status,200)
            self.assertEqual(report['comparison'],'current_addition_topology')
            self.assertEqual(report['preview']['semantic_id'],asset)
            self.assertEqual(report['current_preview']['semantic_id'],asset)
            self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),before)
            self.assertEqual(post('/api/model-material-apply',dict(body,review_key='0'*64))[0],400)
            self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),before)
            status,response=post('/api/model-material-apply',dict(body,review_key=report['review_key']))
            self.assertEqual(status,200)
            applied=response['model_material_report']
            self.assertEqual(applied['schema_version'],'legaia.model-material-review.v2')
            self.assertNotIn('preview',applied)
            self.assertEqual(sha256(p.read_model_replacement(asset,p.model_overrides[asset])).hexdigest(),report['proposed_sha256'])
            saved=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack))
            self.assertEqual(post('/api/model-material-apply',dict(body,review_key=report['review_key']))[0],400)
            self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),saved)

    def test_material_mapping_composes_with_retained_removal_base(self):
        helper=addition_fixtures.ModelFaceAdditionProjectTests();self.addCleanup(helper.doCleanups)
        helper.context();p,asset,_,current=helper.project('tmd-face-removal-v1')
        p.disc_path='synthetic-disc.bin'
        p.imports[p.active_scene]={'assets':{'models':[{'semantic_id':asset}]}}
        self.enterContext(patch('importer.pipeline._disc_context',side_effect=lambda _:nullcontext()))
        donor=source(p,asset,'a'*64)['topology']['faces'][0]['face_id']
        from sdk.model_face_addition import review
        requests=[helper.request(donor)]
        proposal=review(p,asset,requests,sha256(current).hexdigest(),'a'*64)
        p.apply_model_face_additions(asset,requests,sha256(current).hexdigest(),'a'*64,proposal['proposed_sha256'])
        catalog=model_materials.snapshot(p,asset)
        self.assertEqual(catalog['face_mappings'],[[dict(retail_index=0,current_index=None),dict(retail_index=1,current_index=0)]])
        self.assertEqual(catalog['group_mappings'],[[0]])
        self.assertEqual(catalog['authored_faces'][0][0]['current_index'],1)
        edits=[dict(kind='group',object_index=0,group_index=0,values={'semi_transparent':False})]
        _,report=model_materials.prepare(p,asset,edits,catalog['effective_sha256'],'a'*64)
        model_materials.apply(p,asset,edits,catalog['effective_sha256'],'a'*64,report['review_key'])
        self.assertEqual(p.model_overrides[asset]['base_binding']['format'],'tmd-face-removal-v1')
        self.assertEqual(model_materials.snapshot(p,asset)['face_mappings'],catalog['face_mappings'])


if __name__=='__main__': unittest.main()
