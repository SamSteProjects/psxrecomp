from copy import deepcopy
from hashlib import sha256
import unittest
from unittest.mock import patch
from importer.model_primitives import inspect_model_primitives
from importer.core import ImportError as NativeImportError
from sdk import model_texture_assignment as combined
from sdk.project import ProjectError
from sdk.scene_preview import source_key
from sdk.model_face_addition import source as addition_source,review as addition_review
from test_model_primitive_workflow import http_server
import test_model_glb_material_selection as fixtures

ASSET=fixtures.ASSET

class CombinedModelTextureAssignment(unittest.TestCase):
    def fixture(self):
        helper=fixtures.GlbMaterialSelection();self.addCleanup(helper.doCleanups)
        p,native,_,_=helper.setup_project();return p,native

    def drafts(self,content):
        row=inspect_model_primitives(content,include_normal_references=True)['objects'][0]['primitives'][0]
        uv=deepcopy(row['uvs']);uv[0][0]=(uv[0][0]+1)%256
        primitive=[dict(object_index=0,primitive_index=0,vertices=row['vertices'],uvs=uv,colors=row['colors'])]
        material=[dict(kind='primitive',object_index=0,primitive_index=0,values=dict(page_column=5,page_row=1,texture_bpp=16)),dict(kind='group',object_index=0,group_index=0,values=dict(semi_transparent=not row['material']['semi_transparent']))]
        return primitive,material

    def test_combined_actual_native_audits_readonly_and_one_history_step(self):
        p,native=self.fixture();faces,materials=self.drafts(native);key=source_key(p);before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        candidate,r=combined.prepare(p,ASSET,faces,materials,sha256(native).hexdigest(),key)
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
        self.assertEqual(r['effective_sha256'],sha256(native).hexdigest());self.assertEqual(r['proposed_sha256'],sha256(candidate).hexdigest())
        self.assertTrue(any(row['field']=='uv' for row in r['changes_from_current']));self.assertTrue(any(row['field']=='tpage' for row in r['changes_from_current']))
        self.assertEqual(len(r['changes_from_current']),len(r['face_changes_from_current'])+len(r['material_changes_from_current']))
        report=combined.apply(p,ASSET,faces,materials,sha256(native).hexdigest(),key,r['review_key']);self.assertNotIn('preview',report)
        self.assertEqual(len(p.undo_stack),1);self.assertEqual(p.read_model_replacement(ASSET,p.model_overrides[ASSET]),candidate)
        p.undo();self.assertFalse(p.model_overrides);p.redo();self.assertEqual(p.read_model_replacement(ASSET,p.model_overrides[ASSET]),candidate)

    def test_stale_changed_invalid_and_no_change_drafts_reject_without_publication(self):
        p,native=self.fixture();faces,materials=self.drafts(native);key=source_key(p);h=sha256(native).hexdigest();_,r=combined.prepare(p,ASSET,faces,materials,h,key);before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        for f,m,k in [(faces,materials,'stale'),([],materials,key),(faces,[],key),(faces,[dict(materials[0],values=dict(texture_bpp=16,clut_row=4))],key)]:
            with self.assertRaises((ProjectError,ValueError,NativeImportError)):combined.prepare(p,ASSET,f,m,h,k)
        changed=deepcopy(materials);changed[0]['values']['page_column']=6
        with self.assertRaises(ProjectError):combined.apply(p,ASSET,faces,changed,h,key,r['review_key'])
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
        row=inspect_model_primitives(native)['objects'][0]['primitives'][0]
        unchanged=[dict(object_index=0,primitive_index=0,vertices=row['vertices'],uvs=row['uvs'],colors=row['colors'])]
        from importer.model_materials import inspect_model_materials
        material=inspect_model_materials(native)['objects'][0]['groups'][0]['primitives'][0]
        noop=[dict(kind='primitive',object_index=0,primitive_index=0,values=dict(page_column=material['page_column']))]
        _,r=combined.prepare(p,ASSET,unchanged,noop,h,key);self.assertEqual(r['changes_from_current'],[])
        with self.assertRaises(ProjectError):combined.apply(p,ASSET,unchanged,noop,h,key,r['review_key'])

    def test_existing_addition_ledger_is_retained_for_one_combined_step(self):
        p,native=self.fixture();key=source_key(p);info=addition_source(p,ASSET,key)
        requests=[dict(face_id='face://authored/00000000-0000-4000-8000-000000000001',donor_face_id=info['topology']['faces'][0]['face_id'],fields={'vertices':[3,2,1,0]})]
        r=addition_review(p,ASSET,requests,sha256(native).hexdigest(),key);p.apply_model_face_additions(ASSET,requests,sha256(native).hexdigest(),key,r['proposed_sha256'])
        stable=[r['face_id'] for r in addition_source(p,ASSET,source_key(p))['topology']['faces']];old=deepcopy(p.model_overrides[ASSET]);content=p.read_model_replacement(ASSET,old);faces,materials=self.drafts(content);key=source_key(p)
        candidate,r=combined.prepare(p,ASSET,faces,materials,sha256(content).hexdigest(),key);self.assertEqual(r['comparison'],'current_addition_topology')
        combined.apply(p,ASSET,faces,materials,sha256(content).hexdigest(),key,r['review_key']);new=p.model_overrides[ASSET]
        self.assertEqual(new['format'],'tmd-face-addition-v1');self.assertEqual([r['face_id'] for r in addition_source(p,ASSET,source_key(p))['topology']['faces']],stable);self.assertEqual(p.read_model_replacement(ASSET,new),candidate);self.assertEqual(len(p.undo_stack),2)
        p.undo();self.assertEqual(p.model_overrides[ASSET],old);p.redo();self.assertEqual(p.read_model_replacement(ASSET,p.model_overrides[ASSET]),candidate)

    def test_exact_http_preview_and_fresh_review_apply(self):
        p,native=self.fixture();faces,materials=self.drafts(native);body=dict(asset_id=ASSET,primitive_edits=faces,material_edits=materials,expected_sha256=sha256(native).hexdigest(),source_key=source_key(p))
        with patch('sdk.server.EditorServer.model_preview',side_effect=lambda a,prepared=None:prepared),http_server(p) as (_,post):
            for bad in [dict(body,extra=True),dict(body,source_key='stale'),dict(body,primitive_edits=[])]:
                status,_=post('/api/model-texture-assignment-preview',bad);self.assertEqual(status,400)
            status,r=post('/api/model-texture-assignment-preview',body);self.assertEqual(status,200,r);self.assertFalse(p.model_overrides)
            status,_=post('/api/model-texture-assignment-apply',dict(body,review_key='0'*64));self.assertEqual(status,400);self.assertFalse(p.model_overrides)
            status,state=post('/api/model-texture-assignment-apply',dict(body,review_key=r['review_key']));self.assertEqual(status,200,state);self.assertEqual(len(p.undo_stack),1);self.assertEqual(state['model_texture_assignment_report']['proposed_sha256'],r['proposed_sha256'])

if __name__=='__main__':unittest.main()
