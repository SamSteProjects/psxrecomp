"""Real GLB codec roundtrips and imports retain authored face ownership."""
from contextlib import nullcontext
from copy import deepcopy
from hashlib import sha256
import unittest
from unittest.mock import patch
import base64
from importer.assets import decode_tmd
from sdk import model_glb
from sdk.project import ProjectService,ProjectError
from sdk.model_face_addition import source
import test_model_growth as fixtures
from test_model_glb_workflow import move_exported_source_vertex,move_exported_source_rgb
from test_model_primitive_workflow import http_server
import test_model_reference_users_post_addition as reference_fixtures


class AddedModelGlbTests(unittest.TestCase):
    def fixture(self, removed=False):
        helper=reference_fixtures.AddedReferenceUsersTests() if removed else fixtures.ModelGrowthTests()
        self.addCleanup(helper.doCleanups)
        if removed:p,asset=helper.fixture(removed=True)
        else:p,asset,*_=helper.fixture()
        p.disc_path='synthetic-disc.bin'
        self.enterContext(patch('importer.pipeline._disc_context',side_effect=lambda _:nullcontext()))
        self.enterContext(patch('importer.assets.load_model_preview',side_effect=lambda _,row:decode_tmd(p._model_source(row['semantic_id']))))
        return p,asset

    def test_real_export_import_content_and_authored_RGB_preserve_history(self):
        p,asset=self.fixture();before=p.read_model_replacement(asset,p.model_overrides[asset])
        stable=source(p,asset,'a'*64)['topology']['faces']
        content,binding,report=model_glb.export_model(p,asset)
        self.assertEqual(binding['schema_version'],'legaia.model-glb-binding.v3')
        self.assertEqual(binding['authored_face_count'],1)
        self.assertEqual(report['schema_version'],'legaia.model-glb-review.v3')
        self.assertEqual(report['changes'],[])
        with self.assertRaises(ProjectError):model_glb.apply_import(p,asset,content,binding,report['review_key'])
        moved=move_exported_source_vertex(content,dx=1)
        report=model_glb.preview_import(p,asset,moved,binding)
        self.assertEqual(report['comparison'],'current_addition_topology')
        self.assertEqual(report['changes'],report['pending_changes'])
        model_glb.apply_import(p,asset,moved,binding,report['review_key'])
        moved_bytes=p.read_model_replacement(asset,p.model_overrides[asset])
        self.assertNotEqual(moved_bytes,before)
        self.assertEqual(source(p,asset,'a'*64)['topology']['faces'],stable)
        self.assertEqual(p.model_overrides[asset]['ledger']['schema_version'],'legaia.model-face-addition-ledger.v2')
        p.undo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),before)
        p.redo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),moved_bytes)
        content,binding,_=model_glb.export_model(p,asset)
        face=next(row for row in stable if row['origin']=='authored')
        colored=move_exported_source_rgb(content,primitive_index=face['current_primitive_index'])
        report=model_glb.preview_import(p,asset,colored,binding)
        self.assertTrue(all(row['field']=='color' and row['primitive_index']==face['current_primitive_index'] for row in report['pending_changes']))
        model_glb.apply_import(p,asset,colored,binding,report['review_key'])
        final=p.read_model_replacement(asset,p.model_overrides[asset]);saved=deepcopy(p.model_overrides[asset])
        self.assertEqual(source(p,asset,'a'*64)['topology']['faces'],stable)
        p.save()
        with patch.object(ProjectService,'_model_source',side_effect=p._model_source):
            reopened=ProjectService.open(p.root)
            self.assertEqual(reopened.read_model_replacement(asset,saved),final)

    def test_forged_topology_binding_and_stale_export_reject_without_mutation(self):
        p,asset=self.fixture();content,binding,_=model_glb.export_model(p,asset)
        before=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack))
        for change in ({'topology_sha256':'0'*64},{'authored_face_count':2},{'authored_face_count':True},{'schema_version':'legaia.model-glb-binding.v1'}):
            with self.assertRaises(ProjectError):model_glb.preview_import(p,asset,content,{**binding,**change})
            self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),before)
        moved=move_exported_source_vertex(content,dx=1);report=model_glb.preview_import(p,asset,moved,binding)
        with self.assertRaises(ProjectError):model_glb.apply_import(p,asset,moved,binding,'0'*64)
        self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),before)

        model_glb.apply_import(p,asset,moved,binding,report['review_key'])
        before=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack))
        with self.assertRaises(ProjectError):model_glb.preview_import(p,asset,moved,binding)
        self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),before)

    def test_HTTP_export_review_apply_retains_topology_binding(self):
        p,asset=self.fixture()
        with http_server(p) as (server,post),patch.object(server,'state',return_value={'applied':True}):
            status,exported=post('/api/model-glb-export',dict(asset_id=asset))
            self.assertEqual(status,200)
            binding=exported['binding'];self.assertEqual(binding['schema_version'],'legaia.model-glb-binding.v3')
            moved=move_exported_source_vertex(base64.b64decode(exported['content_base64']),dx=1)
            body=dict(asset_id=asset,binding=binding,content_base64=base64.b64encode(moved).decode('ascii'))
            before=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack))
            status,report=post('/api/model-glb-preview',body);self.assertEqual(status,200)
            self.assertEqual(report['topology_sha256'],binding['topology_sha256'])
            self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),before)
            self.assertEqual(post('/api/model-glb-import',dict(body,review_key='0'*64))[0],400)
            self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),before)
            status,response=post('/api/model-glb-import',dict(body,review_key=report['review_key']))
            self.assertEqual(status,200);self.assertEqual(response['model_glb_report']['comparison'],'current_addition_topology')
            self.assertEqual(p.model_overrides[asset]['format'],'tmd-face-addition-v1')
            self.assertEqual(post('/api/model-glb-import',dict(body,review_key=report['review_key']))[0],400)

    def test_sidecar_identity_changes_invalidate_byte_identical_model(self):
        p,asset=self.fixture();content,binding,_=model_glb.export_model(p,asset)
        ledger=p.model_overrides[asset]['ledger']
        self.assertEqual(ledger['schema_version'],'legaia.model-face-addition-ledger.v1')
        ledger['batches'][0]['additions'][0]['face_id']='face://authored/00000000-0000-4000-8000-000000000099'
        _,fresh,_=model_glb.export_model(p,asset)
        self.assertEqual(fresh['effective_sha256'],binding['effective_sha256'])
        self.assertNotEqual(fresh['topology_sha256'],binding['topology_sha256'])
        before=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack))
        with self.assertRaises(ProjectError):model_glb.preview_import(p,asset,content,binding)
        self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),before)

    def test_real_GLB_import_keeps_retained_removal_base(self):
        p,asset=self.fixture(removed=True);content,binding,report=model_glb.export_model(p,asset)
        self.assertEqual(report['pending_changes'],[])
        self.assertEqual(binding['authored_face_count'],1)
        moved=move_exported_source_vertex(content,dx=1)
        report=model_glb.preview_import(p,asset,moved,binding)
        model_glb.apply_import(p,asset,moved,binding,report['review_key'])
        self.assertEqual(p.model_overrides[asset]['base_binding']['format'],'tmd-face-removal-v1')
        _,fresh,roundtrip=model_glb.export_model(p,asset)
        self.assertEqual(fresh['topology_sha256'],binding['topology_sha256'])
        self.assertEqual(roundtrip['pending_changes'],[])

    def test_reflected_import_keeps_allocated_faces_and_retired_base(self):
        from test_model_glb import rewrite
        from test_model_glb_hierarchy import group
        from test_model_glb_reflection import mirrored_native
        for removed in (False, True):
            with self.subTest(removed=removed):
                p,asset=self.fixture(removed=removed)
                before=p.read_model_replacement(asset,p.model_overrides[asset])
                topology=source(p,asset,'a'*64)['topology']['faces']
                content,binding,_=model_glb.export_model(p,asset)
                reflected=rewrite(content,lambda d,b:group(d,dict(scale=[-1,1,1])))
                report=model_glb.preview_import(p,asset,reflected,binding)
                history=len(p.undo_stack)
                model_glb.apply_import(p,asset,reflected,binding,report['review_key'])
                candidate=p.read_model_replacement(asset,p.model_overrides[asset])
                self.assertEqual(candidate,mirrored_native(before,[-1,1,1]))
                self.assertEqual(len(p.undo_stack),history+1)
                self.assertEqual(source(p,asset,'a'*64)['topology']['faces'],topology)
                if removed:self.assertEqual(p.model_overrides[asset]['base_binding']['format'],'tmd-face-removal-v1')
                p.undo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),before)
                p.redo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),candidate)
                _,fresh,roundtrip=model_glb.export_model(p,asset)
                self.assertEqual(fresh['topology_sha256'],binding['topology_sha256'])
                self.assertEqual(roundtrip['pending_changes'],[])


if __name__=='__main__':unittest.main()
