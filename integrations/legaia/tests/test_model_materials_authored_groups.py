"""Authored material groups have stable allocation ownership and no Retail reset."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import unittest
from unittest.mock import patch
from importer.model_face_ledger import (append_group_ledger,append_removal_ledger,
    append_restoration_ledger,replay_face_ledger)
from sdk import model_materials,model_glb
from sdk.model_face_addition import base_content
from sdk.project import ProjectService,ProjectError
import test_model_editors_allocated_vectors as fixtures

GROUP='group://authored/00000000-0000-4000-8000-000000000077'
FACE='face://authored/00000000-0000-4000-8000-000000000077'


class AuthoredGroupMaterialTests(unittest.TestCase):
    def install(self,p,asset,binding,candidate,ledger):
        binding=deepcopy(binding)
        binding.update(ledger=ledger,asset_sha256=sha256(candidate).hexdigest(),byte_length=len(candidate))
        (p.root/'Authored'/'Models'/(binding['asset_sha256']+'.tmd')).write_bytes(candidate)
        p.model_overrides[asset]=binding

    def fixture(self,removed=False):
        helper=fixtures.AllocatedEditorTests();self.addCleanup(helper.doCleanups)
        p,asset=helper.fixture(removed);binding=p.model_overrides[asset]
        from test_project_workflow import synthetic_scene
        document=synthetic_scene();document['assets']['models']=p.imports[p.active_scene]['assets']['models']
        p.imports[p.active_scene]=document
        original=p._model_source(asset);base=base_content(p,asset,original,binding)
        _,audit=replay_face_ledger(base,binding['ledger']);donor=audit['faces'][0]['face_id']
        candidate,ledger,_=append_group_ledger(base,binding['ledger'],[dict(group_id=GROUP,donor_face_id=donor,
            faces=[dict(face_id=FACE,donor_face_id=donor,fields=dict(vertices=[5,6,0,1],normal_indices=[4,5,4,5]))])])
        self.install(p,asset,binding,candidate,ledger)
        return p,asset,base

    def test_review_apply_history_save_reopen_and_fixed_layout_GLB_roundtrip(self):
        for removed in (False,True):
            with self.subTest(removed=removed):
                p,asset,base=self.fixture(removed);source=model_materials.snapshot(p,asset)
                self.assertEqual(source['schema_version'],'legaia.model-material-source.v4')
                self.assertEqual(source['group_mappings'],[[0,None]])
                owner=source['authored_groups'][0][0]
                self.assertEqual(owner['group_id'],GROUP);self.assertEqual(owner['current_index'],1)
                packet=source['objects'][0]['groups'][1]['primitives'][0]
                edits=[dict(kind='primitive',object_index=0,primitive_index=packet['primitive_index'],values={'clut_column':7}),
                    dict(kind='group',object_index=0,group_index=1,values={'semi_transparent':False})]
                before=p.read_model_replacement(asset,p.model_overrides[asset])
                state=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack));files=set((p.root/'Authored'/'Models').iterdir())
                candidate,report=model_materials.prepare(p,asset,edits,source['effective_sha256'],'a'*64)
                self.assertEqual(report['coordinate_changes'],report['changes_from_current'])
                self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)
                self.assertEqual(set((p.root/'Authored'/'Models').iterdir()),files)
                group=next(row for row in report['changes_from_current'] if row['kind']=='primitive_group')
                self.assertEqual(group['primitive_indices'],[packet['primitive_index']])
                with self.assertRaises(ProjectError):model_materials.apply(p,asset,edits,source['effective_sha256'],'a'*64,'0'*64)
                self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)
                model_materials.apply(p,asset,edits,source['effective_sha256'],'a'*64,report['review_key'])
                self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),candidate)
                self.assertEqual(len(p.undo_stack),len(state[1])+1)
                fresh=model_materials.snapshot(p,asset)
                self.assertEqual(fresh['authored_groups'],source['authored_groups'])
                self.assertEqual(fresh['objects'][0]['groups'][0],source['objects'][0]['groups'][0])
                p.undo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),before)
                p.redo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),candidate)
                content,binding,export=model_glb.export_model(p,asset)
                self.assertEqual(export['pending_changes'],[])
                self.assertEqual(model_glb.preview_import(p,asset,content,binding)['pending_changes'],[])
                p.save();saved=deepcopy(p.model_overrides[asset])
                with patch.object(ProjectService,'_model_source',side_effect=p._model_source):
                    reopened=ProjectService.open(p.root)
                    self.assertEqual(reopened.read_model_replacement(asset,saved),candidate)
                    self.assertEqual(model_materials.snapshot(reopened,asset)['authored_groups'],source['authored_groups'])

    def test_absent_authored_group_and_restored_identity_remain_explicit(self):
        p,asset,base=self.fixture();binding=p.model_overrides[asset]
        candidate,ledger,_=append_removal_ledger(base,binding['ledger'],[FACE])
        self.install(p,asset,binding,candidate,ledger)
        source=model_materials.snapshot(p,asset)
        self.assertEqual(source['authored_groups'],[[]]);self.assertEqual(source['group_mappings'],[[0]])
        candidate,ledger,_=append_restoration_ledger(base,ledger,[FACE])
        self.install(p,asset,p.model_overrides[asset],candidate,ledger)
        restored=model_materials.snapshot(p,asset)
        self.assertEqual(restored['group_mappings'],[[0,None]])
        self.assertEqual(restored['authored_groups'][0][0]['group_id'],GROUP)

    def test_actual_v4_sources_reviews_and_tamper_rejection_in_javascript(self):
        node=shutil.which('node')
        if not node:self.skipTest('Node unavailable')
        cases=[]
        for removed in (False,True):
            p,asset,_=self.fixture(removed);source=model_materials.snapshot(p,asset)
            edits=[dict(kind='group',object_index=0,group_index=1,values={'semi_transparent':False})]
            _,report=model_materials.prepare(p,asset,edits,source['effective_sha256'],'a'*64)
            report.pop('preview');report.pop('current_preview')
            cases.append(dict(source=source,report=report,edits=edits))
        script="""import {decodeModelMaterialSource,decodeModelMaterialReview} from './integrations/legaia/editor/model-materials.js';
import assert from 'node:assert/strict';let input='';for await(const chunk of process.stdin)input+=chunk;
for(const {source,report,edits} of JSON.parse(input)){
 const context={projectPath:'C:/private/project',sceneId:source.scene_id,mode:'edit',sourceKey:source.project_source_key};
 const decoded=decodeModelMaterialSource(source,source.asset_id,context);
 decodeModelMaterialReview(report,decoded,context,edits,{previews:false});
 for(const mutate of [s=>s.group_mappings[0][1]=0,s=>s.authored_groups[0]=[],s=>s.authored_groups[0][0].current_index=0,s=>s.authored_groups[0][0].flags^=1,s=>s.authored_groups[0][0].mode^=4,s=>s.authored_groups[0][0].group_id='bad',s=>s.authored_groups[0].push({...s.authored_groups[0][0]}),s=>s.authored_faces[0].pop(),s=>s.schema_version='legaia.model-material-source.v3']){
  const bad=structuredClone(source);mutate(bad);assert.throws(()=>decodeModelMaterialSource(bad,source.asset_id,context));
 }
 const bad=structuredClone(report);bad.changes_from_current[0].primitive_indices.push(0);
 assert.throws(()=>decodeModelMaterialReview(bad,decoded,context,edits,{previews:false}));
}
"""
        result=subprocess.run([node,'--input-type=module','-e',script],input=json.dumps(cases),text=True,
            capture_output=True,cwd=Path(__file__).resolve().parents[3])
        self.assertEqual(result.returncode,0,result.stderr)


if __name__=='__main__':unittest.main()
