"""Copied native objects have authored material groups and no Retail reset owner."""
from contextlib import nullcontext
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import json
import shutil
import subprocess
import unittest
from unittest.mock import patch
from sdk import model_materials,model_glb
from sdk.project import ProjectService
import test_model_object_consumers as fixtures


class ObjectMaterialTests(unittest.TestCase):
    def fixture(self):
        helper=fixtures.ObjectConsumerTests();self.addCleanup(helper.doCleanups)
        p,asset=helper.fixture()
        from test_project_workflow import synthetic_scene
        document=synthetic_scene();document['assets']['models']=p.imports[p.active_scene]['assets']['models'];p.imports[p.active_scene]=document
        return p,asset

    def test_material_review_apply_history_reopen_and_browser_reports(self):
        p,asset=self.fixture();source=model_materials.snapshot(p,asset)
        self.assertEqual(source['schema_version'],'legaia.model-material-source.v5')
        self.assertEqual(source['group_mappings'][1],[None]);self.assertEqual(source['face_mappings'][1],[])
        self.assertIsNone(source['object_mappings'][1]['retail_index'])
        edits=[dict(kind='primitive',object_index=1,primitive_index=0,values={'clut_column':7}),dict(kind='group',object_index=1,group_index=0,values={'semi_transparent':False})]
        before=p.read_model_replacement(asset,p.model_overrides[asset]);state=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack));files=set((p.root/'Authored'/'Models').iterdir())
        candidate,report=model_materials.prepare(p,asset,edits,sha256(before).hexdigest(),'a'*64)
        self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state);self.assertEqual(set((p.root/'Authored'/'Models').iterdir()),files)
        node=shutil.which('node')
        if node:
            for key in ('preview','current_preview'):report[key]['semantic_id']=asset
            script="""import {decodeModelMaterialSource,decodeModelMaterialReview} from './integrations/legaia/editor/model-materials.js';
import assert from 'node:assert/strict';let text='';for await(const chunk of process.stdin)text+=chunk;
const {source,report,edits}=JSON.parse(text),context={projectPath:'C:/private/project',sceneId:source.scene_id,mode:'edit',sourceKey:source.project_source_key};
decodeModelMaterialSource(source,source.asset_id,context);decodeModelMaterialReview(report,source,context,edits,{previews:true});
for(const mutate of [s=>s.object_mappings[1].retail_index=0,s=>s.group_mappings[1][0]=0,s=>s.authored_groups[1].pop(),s=>s.object_mappings[1].donor_object_id=s.object_mappings[1].object_id,s=>s.authored_groups[1][0].flags^=1]){const bad=structuredClone(source);mutate(bad);assert.throws(()=>decodeModelMaterialSource(bad,source.asset_id,context));}
"""
            result=subprocess.run([node,'--input-type=module','-e',script],input=json.dumps(dict(source=source,report=report,edits=edits)),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3])
            self.assertEqual(result.returncode,0,result.stderr)
        model_materials.apply(p,asset,edits,sha256(before).hexdigest(),'a'*64,report['review_key'])
        self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),candidate)
        self.assertEqual(p.model_overrides[asset]['ledger']['schema_version'],'legaia.model-face-addition-ledger.v7')
        self.assertEqual(len(p.undo_stack),len(state[1])+1)
        fresh=model_materials.snapshot(p,asset);self.assertEqual(fresh['object_mappings'],source['object_mappings'])
        p.undo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),before)
        p.redo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),candidate)
        p.save()
        with patch.object(ProjectService,'_model_source',side_effect=p._model_source):
            reopened=ProjectService.open(p.root);self.assertEqual(model_materials.snapshot(reopened,asset),fresh)

    def test_fixed_layout_GLB_roundtrip_on_authored_object(self):
        from test_model_glb_workflow import move_exported_source_vertex
        p,asset=self.fixture();before=p.read_model_replacement(asset,p.model_overrides[asset])
        content,binding,report=model_glb.export_model(p,asset)
        unchanged=model_glb.preview_import(p,asset,content,binding)
        self.assertEqual(unchanged['pending_changes'],[])
        self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),before)
        moved=move_exported_source_vertex(content,object_index=1,vertex_index=0,dx=1)
        review=model_glb.preview_import(p,asset,moved,binding)
        self.assertTrue(review['pending_changes'])
        model_glb.apply_import(p,asset,moved,binding,review['review_key'])
        final=p.read_model_replacement(asset,p.model_overrides[asset]);self.assertNotEqual(final,before)
        self.assertEqual(p.model_overrides[asset]['ledger']['schema_version'],'legaia.model-face-addition-ledger.v7')
        self.assertEqual(p.model_primitive_source(asset)['object_mappings'][1]['object_id'],model_materials.snapshot(p,asset)['object_mappings'][1]['object_id'])
        p.undo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),before)
        p.redo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),final)


if __name__=='__main__':unittest.main()


