"""Reviewed GLB geometry can allocate an independent native material group."""
from copy import deepcopy
from hashlib import sha256
import base64
import json
from pathlib import Path
import shutil
import subprocess
import tomllib
import unittest
import zipfile
from unittest.mock import patch
from importer.core import _pack_ranges,parse_scene_assets,decompress_lzs
from importer.disc_relocation_package import decode_relocation_package
from importer.model_pack_archive import _archive
from importer.model_primitives import inspect_model_primitives
from sdk import model_mesh_append,model_object_allocation,model_face_addition
from test_model_object_ledger import clone_request
from sdk.project import ProjectError,ProjectService
from sdk.build import build_project
import test_model_mesh_append as fixtures
import test_model_mesh_append_normals as normal_fixtures
from test_model_primitive_workflow import http_server


class MeshAppendGroupTests(unittest.TestCase):
    def fixture(self):
        helper=fixtures.MeshAppendTests();self.addCleanup(helper.doCleanups)
        return helper.fixture()

    def test_new_group_complete_geometry_atomic_history_reopen_build(self):
        p,asset,donor=self.fixture();binding=deepcopy(p.model_overrides[asset])
        before=p.read_model_replacement(asset,binding);old=inspect_model_primitives(before,include_normal_references=True)['objects'][0]['primitives']
        content=fixtures.glb(uvs=[[0,0],[1,0],[0,1],[1,1]],colors=[[1,1,1]]*4)
        state=deepcopy((p._document(),p.undo_stack,p.redo_stack));files=set((p.root/'Authored'/'Models').iterdir())
        args=(p,asset,content,donor,sha256(before).hexdigest(),'a'*64)
        report=model_mesh_append.review(*args,new_group=True)
        legacy=model_mesh_append.review(*args)
        self.assertEqual(report['schema_version'],'legaia.model-mesh-append-review.v5')
        self.assertNotEqual(report['review_key'],legacy['review_key']);self.assertNotEqual(report['proposed_sha256'],legacy['proposed_sha256'])
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack),state);self.assertEqual(set((p.root/'Authored'/'Models').iterdir()),files)
        with self.assertRaises(ProjectError):p.apply_model_mesh_append(*args[1:],legacy['review_key'],new_group=True)
        with self.assertRaises(ProjectError):p.apply_model_mesh_append(*args[1:],report['review_key'])
        p.apply_model_mesh_append(*args[1:],report['review_key'],new_group=True)
        final=p.read_model_replacement(asset,p.model_overrides[asset]);new=inspect_model_primitives(final,include_normal_references=True)['objects'][0]['primitives']
        self.assertEqual(len(p.undo_stack),len(state[1])+1)
        self.assertEqual([op['kind'] for op in p.model_overrides[asset]['ledger']['operations']],['allocate_vectors','allocate_groups'])
        self.assertEqual(p.model_overrides[asset]['base_binding'],binding.get('base_binding',binding))
        for retained,current in zip(old,new):
            for key in ('group_index','flags','vertices','normal_indices','uvs','colors','material'):self.assertEqual(retained[key],current[key])
        self.assertEqual([row['group_index'] for row in new[len(old):]],[1,1])
        self.assertEqual(report['topology']['allocated_group_count'],1)
        self.assertEqual(report['topology']['allocated_groups'][0]['group_id'],report['group_requests'][0]['group_id'])
        self.assertEqual(report['group_requests'][0]['faces'],report['additions'])
        p.undo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),before)
        p.redo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),final)
        p.save()
        with patch.object(ProjectService,'_model_source',side_effect=p._model_source):
            reopened=ProjectService.open(p.root);self.assertEqual(reopened.read_model_replacement(asset,reopened.model_overrides[asset]),final)
        out=build_project(p)
        with zipfile.ZipFile(out['path']) as package:
            manifest=tomllib.loads(package.read('manifest.toml').decode());entry=manifest['disc_relocation'][0]
            replacement=decode_relocation_package(package.read(entry['file']),entry['sha256'])['replacement']
        archive=_archive(replacement);carrier=archive.read_entry(archive.entry(1));d=parse_scene_assets(carrier,1).descriptors[1]
        pack,_=decompress_lzs(carrier[d.data_offset:],d.size);start,_=_pack_ranges(pack)[0]
        self.assertEqual(pack[start:start+len(final)],final)

    def test_http_boolean_mode_bound_review_and_one_apply(self):
        p,asset,donor=self.fixture();before=p.read_model_replacement(asset,p.model_overrides[asset])
        body=dict(asset_id=asset,content_base64=base64.b64encode(fixtures.glb()).decode(),donor_face_id=donor,
            expected_sha256=sha256(before).hexdigest(),source_key='a'*64,new_group=True)
        with http_server(p) as (server,post),patch.object(server,'state',return_value={'applied':True}):
            status,source=post('/api/model-mesh-append-source',dict(asset_id=asset,source_key='a'*64))
            self.assertEqual(status,200);self.assertEqual(source['next_group_origin_indices'],[1])
            for value in (None,1,'true',[],{}):
                self.assertEqual(post('/api/model-mesh-append-preview',{**body,'new_group':value})[0],400)
            status,report=post('/api/model-mesh-append-preview',body);self.assertEqual(status,200)
            self.assertEqual(report['allocation_mode'],'new_group')
            self.assertEqual(post('/api/model-mesh-append',{**body,'new_group':False,'review_key':report['review_key']})[0],400)
            self.assertEqual(post('/api/model-mesh-append',{**body,'review_key':report['review_key']})[0],200)
            self.assertEqual(post('/api/model-mesh-append',{**body,'review_key':report['review_key']})[0],400)

    def test_new_group_in_copied_object_retains_v7_ownership(self):
        p,asset,_=self.fixture()
        with patch('sdk.model_object_allocation.source_key',return_value='a'*64):
            source=model_object_allocation.source(p,asset,'a'*64)
            requests=[clone_request(source['topology'],source['object_identities'][0],900)]
            clone=model_object_allocation.review(p,asset,requests,source['effective_sha256'],'a'*64)
            p.apply_model_object_allocations(asset,requests,source['effective_sha256'],'a'*64,clone['review_key'])
        source=model_face_addition.source(p,asset,'a'*64)
        donor=next(face['face_id'] for face in source['topology']['faces'] if face['object_index']==1)
        args=(asset,fixtures.glb(),donor,source['effective_sha256'],'a'*64)
        report=model_mesh_append.review(p,*args,new_group=True)
        p.apply_model_mesh_append(*args,report['review_key'],new_group=True)
        self.assertEqual(p.model_overrides[asset]['ledger']['schema_version'],'legaia.model-face-addition-ledger.v7')
        self.assertEqual(report['topology']['objects'],source['topology']['objects'])
        self.assertEqual(report['topology']['allocated_group_count'],source['topology']['allocated_group_count']+1)
        group=report['topology']['allocated_groups'][-1];self.assertEqual(group['object_index'],1)
        self.assertEqual(group['face_ids'],[face['face_id'] for face in report['additions']])

    def test_actual_browser_new_group_review_and_mode_qualification(self):
        node=shutil.which('node')
        if not node:self.skipTest('Node unavailable')
        p,asset,donor=self.fixture();content=fixtures.glb();cases=[]
        for _ in range(2):
            source=model_mesh_append.source(p,asset,'a'*64)
            report=model_mesh_append.review(p,asset,content,donor,source['effective_sha256'],'a'*64,new_group=True)
            legacy=model_mesh_append.review(p,asset,content,donor,source['effective_sha256'],'a'*64)
            cases.append(dict(source=source,report=report,legacy=legacy,donor=donor))
            p.apply_model_mesh_append(asset,content,donor,source['effective_sha256'],'a'*64,report['review_key'],new_group=True)
            donor=report['additions'][0]['face_id']
        with patch('sdk.model_object_allocation.source_key',return_value='a'*64):
            object_source=model_object_allocation.source(p,asset,'a'*64)
            requests=[clone_request(object_source['topology'],object_source['object_identities'][0],1800)]
            clone=model_object_allocation.review(p,asset,requests,object_source['effective_sha256'],'a'*64)
            p.apply_model_object_allocations(asset,requests,object_source['effective_sha256'],'a'*64,clone['review_key'])
        source=model_mesh_append.source(p,asset,'a'*64);donor=next(face['face_id'] for face in source['topology']['faces'] if face['object_index']==1)
        report=model_mesh_append.review(p,asset,content,donor,source['effective_sha256'],'a'*64,new_group=True)
        legacy=model_mesh_append.review(p,asset,content,donor,source['effective_sha256'],'a'*64)
        cases.append(dict(source=source,report=report,legacy=legacy,donor=donor))
        helper=normal_fixtures.MeshAppendNormalTests();self.addCleanup(helper.doCleanups)
        p,asset,donor=helper.fixture(0x14);content=fixtures.glb(normals=normal_fixtures.NORMALS)
        source=model_mesh_append.source(p,asset,'a'*64)
        report=model_mesh_append.review(p,asset,content,donor,source['effective_sha256'],'a'*64,new_group=True)
        legacy=model_mesh_append.review(p,asset,content,donor,source['effective_sha256'],'a'*64)
        cases.append(dict(source=source,report=report,legacy=legacy,donor=donor))
        script="""import assert from 'node:assert/strict';import {decodeMeshAppendSource,decodeMeshAppendReview} from './integrations/legaia/editor/model-mesh-append.js';
let data='';for await(const chunk of process.stdin)data+=chunk;for(const {source,report,legacy,donor} of JSON.parse(data)){
decodeMeshAppendSource(source,source.asset_id,source.project_source_key);decodeMeshAppendReview(report,source,donor,report.geometry.glb_sha256,true);decodeMeshAppendReview(legacy,source,donor,legacy.geometry.glb_sha256);
assert.throws(()=>decodeMeshAppendReview(report,source,donor,report.geometry.glb_sha256));assert.throws(()=>decodeMeshAppendReview(legacy,source,donor,legacy.geometry.glb_sha256,true));
for(const mutate of [r=>r.group_requests[0].group_id='bad',r=>r.topology.allocated_groups.at(-1).origin_group_index++,r=>r.topology.allocated_groups.at(-1).current_group_index++,r=>r.topology.allocated_groups.at(-1).mode++,r=>r.topology.operation_count--,r=>r.topology.faces.at(-1).group_index--,r=>r.preview.triangles.at(-1)[0]++,r=>r.preview.triangle_normals[0]=[[1,0,0],[1,0,0],[1,0,0]],r=>r.preview.bounds.max[0]++,r=>r.allocation_mode='existing']){const bad=structuredClone(report);mutate(bad);assert.throws(()=>decodeMeshAppendReview(bad,source,donor,report.geometry.glb_sha256,true));}}
"""
        result=subprocess.run([node,'--input-type=module','-e',script],input=json.dumps(cases),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3])
        self.assertEqual(result.returncode,0,result.stderr)


if __name__=='__main__':unittest.main()
