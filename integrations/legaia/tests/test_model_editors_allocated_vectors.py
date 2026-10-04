"""Existing face, material and GLB edits preserve allocated vector ownership."""
from contextlib import nullcontext
from copy import deepcopy
from hashlib import sha256
import json,shutil,subprocess,unittest
from pathlib import Path
from unittest.mock import patch
from importer.assets import decode_tmd
from sdk import model_glb,model_materials
import test_model_reference_users_allocated_vectors as fixtures
from test_model_glb_workflow import move_exported_source_vertex


class AllocatedEditorTests(unittest.TestCase):
    def fixture(self,removed=False):
        helper=fixtures.AllocatedReferenceTests();self.addCleanup(helper.doCleanups)
        p,asset=helper.fixture(removed)
        self.enterContext(patch('importer.pipeline._disc_context',side_effect=lambda _:nullcontext()))
        self.enterContext(patch('importer.assets.load_model_preview',side_effect=lambda _,row:decode_tmd(p._model_source(row['semantic_id']))))
        return p,asset

    def current(self,p,asset):return p.read_model_replacement(asset,p.model_overrides[asset])

    def test_existing_face_can_reference_new_rows_and_reset_retained_face(self):
        for removed in (False,True):
            p,asset=self.fixture(removed);before=self.current(p,asset)
            source=p.model_primitive_source(asset)
            self.assertEqual(source['schema_version'],'legaia.model-primitives.v5')
            self.assertEqual(source['vector_growth'],[dict(object_index=0,vertices=3,normals=3)])
            row=source['objects'][0]['primitives'][0]
            edits=[dict(object_index=0,primitive_index=0,vertices=[5,6,7,0],normal_indices=[4,5,6,0])]
            state=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack))
            review=p.preview_model_primitives(asset,edits,sha256(before).hexdigest(),'a'*64)
            self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)
            p.set_model_primitives(asset,edits,sha256(before).hexdigest(),'a'*64,review['proposed_sha256'])
            after=self.current(p,asset);self.assertNotEqual(after,before)
            p.undo();self.assertEqual(self.current(p,asset),before)
            p.redo();self.assertEqual(self.current(p,asset),after)
            fresh=p.model_primitive_source(asset)
            owner=next(face['retail_index'] for face in fresh['face_mappings'][0] if face['current_index']==0)
            retail=fresh['retail_objects'][0]['primitives'][owner]
            edits=[dict(object_index=0,primitive_index=0,vertices=retail['vertices'],normal_indices=retail['normal_indices'])]
            report=p.preview_model_primitives(asset,edits,sha256(after).hexdigest(),'a'*64)
            p.set_model_primitives(asset,edits,sha256(after).hexdigest(),'a'*64,report['proposed_sha256'])
            self.assertEqual(self.current(p,asset),before)
            self.assertEqual(p.model_primitive_source(asset)['vector_growth'],source['vector_growth'])

    def test_material_and_GLB_roundtrip_keep_added_rows_and_history(self):
        for removed in (False,True):
            p,asset=self.fixture(removed);before=self.current(p,asset)
            catalog=model_materials.snapshot(p,asset)
            authored=catalog['authored_faces'][0][-1]['current_index']
            edits=[dict(kind='primitive',object_index=0,primitive_index=authored,values={'clut_column':7})]
            candidate,review=model_materials.prepare(p,asset,edits,sha256(before).hexdigest(),'a'*64)
            model_materials.apply(p,asset,edits,sha256(before).hexdigest(),'a'*64,review['review_key'])
            self.assertEqual(self.current(p,asset),candidate)
            content,binding,report=model_glb.export_model(p,asset)
            self.assertEqual(report['pending_changes'],[])
            unchanged=model_glb.preview_import(p,asset,content,binding)
            self.assertEqual(unchanged['pending_changes'],[])
            moved=move_exported_source_vertex(content,vertex_index=5,dx=1)
            report=model_glb.preview_import(p,asset,moved,binding)
            model_glb.apply_import(p,asset,moved,binding,report['review_key'])
            final=self.current(p,asset);self.assertNotEqual(final,candidate)
            self.assertEqual(p.model_overrides[asset]['ledger']['schema_version'],'legaia.model-face-addition-ledger.v5')
            source=p.model_primitive_source(asset)
            self.assertEqual(source['objects'][0]['vertex_count'],8)
            self.assertEqual(source['objects'][0]['normal_count'],7)
            p.undo();self.assertEqual(self.current(p,asset),candidate)
            p.redo();self.assertEqual(self.current(p,asset),final)
            _,_,fresh=model_glb.export_model(p,asset);self.assertEqual(fresh['pending_changes'],[])

    def test_actual_sources_decode_in_browser_adapter(self):
        node=shutil.which('node')
        if not node:self.skipTest('Node unavailable')
        reports=[]
        for removed in (False,True):
            p,asset=self.fixture(removed)
            source=p.model_primitive_source(asset)
            row=source['objects'][0]['primitives'][0]
            edits=[dict(object_index=0,primitive_index=0,vertices=[5,6,7,0],uvs=row['uvs'],normal_indices=[4,5,6,0])]
            primitive_review=p.preview_model_primitives(asset,edits,source['effective_sha256'],'a'*64)
            for key in ('preview','current_preview'):primitive_review[key]['semantic_id']=asset
            material_source=model_materials.snapshot(p,asset)
            material_edits=[dict(kind='primitive',object_index=0,primitive_index=0,values={'clut_column':7})]
            _,material_review=model_materials.prepare(p,asset,material_edits,source['effective_sha256'],'a'*64)
            for key in ('preview','current_preview'):material_review.pop(key)
            content,binding,_=model_glb.export_model(p,asset)
            moved=move_exported_source_vertex(content,vertex_index=5,dx=1)
            glb_review=model_glb.preview_import(p,asset,moved,binding)
            reports.append(dict(source=source,edits=edits,primitive_review=primitive_review,
                material_source=material_source,material_edits=material_edits,material_review=material_review,
                binding=binding,glb_review=glb_review))
        script="""import {decodeModelPrimitives,modelPrimitiveDraft,decodeModelPrimitivePreview} from './integrations/legaia/editor/model-primitives.js';
import {decodeModelMaterialSource,decodeModelMaterialReview} from './integrations/legaia/editor/model-materials.js';
import {decodeModelGlbBinding,decodeModelGlbReview} from './integrations/legaia/editor/model-glb.js';
import assert from 'node:assert/strict';
let input='';for await(const chunk of process.stdin)input+=chunk;
for(const data of JSON.parse(input)){
 const {source}=data;
 const context={projectPath:'C:/private/project',sceneId:'scene://fixture',mode:'edit',sourceKey:source.project_source_key};
 const decoded=decodeModelPrimitives(source,source.asset_id,context);
 decodeModelPrimitivePreview(data.primitive_review,decoded,context,data.edits);
 const material=decodeModelMaterialSource(data.material_source,source.asset_id,context);
 decodeModelMaterialReview(data.material_review,material,context,data.material_edits,{previews:false});
 const binding=decodeModelGlbBinding(data.binding,source.asset_id,context);
 decodeModelGlbReview(data.glb_review,binding,source.asset_id,context,data.glb_review.glb_sha256);
 assert.deepEqual(modelPrimitiveDraft(decoded,0,0,{vertices:[5,6,7,0],uvs:decoded.objects[0].primitives[0].uvs,normal_indices:[4,5,6,0]}).vertices,[5,6,7,0]);
 for(const mutate of [s=>s.vector_growth[0].vertices++,s=>s.vector_growth[0].normals=false,s=>s.vector_growth=[],s=>s.schema_version='legaia.model-primitives.v4']){
  const bad=structuredClone(source);mutate(bad);assert.throws(()=>decodeModelPrimitives(bad,source.asset_id,context));
 }
}
"""
        result=subprocess.run([node,'--input-type=module','-e',script],input=json.dumps(reports),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3])
        self.assertEqual(result.returncode,0,result.stderr)


if __name__=='__main__':unittest.main()
