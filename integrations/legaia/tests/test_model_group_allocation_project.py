"""Actual new-group commands qualify review identity, history and normal Build."""
from copy import deepcopy
from hashlib import sha256
import tomllib
import unittest
import zipfile
import json
import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from importer.core import _pack_ranges,parse_scene_assets,decompress_lzs
from importer.disc_relocation_package import decode_relocation_package
from importer.model_pack_archive import _archive
from sdk import model_group_allocation
from sdk.project import ProjectService,ProjectError
from sdk.build import build_project
import test_model_growth_normal_build as fixtures
from test_model_primitive_workflow import http_server


class GroupAllocationProjectTests(unittest.TestCase):
    def fixture(self):
        helper=fixtures.ModelGrowthNormalBuildTests();self.addCleanup(helper.doCleanups)
        p,asset,*_=helper.fixture()
        self.enterContext(patch('sdk.model_group_allocation.source_key',return_value='a'*64))
        return p,asset

    def requests(self,source,index=99):
        donor=source['topology']['faces'][0]
        row=source['objects'][donor['object_index']]['primitives'][donor['current_primitive_index']]
        return [dict(group_id=f'group://authored/00000000-0000-4000-8000-{index:012x}',
            donor_face_id=donor['face_id'],faces=[dict(
                face_id=f'face://authored/00000000-0000-4000-8000-{index:012x}',
                donor_face_id=donor['face_id'],fields={'vertices':list(reversed(row['vertices']))})])]

    def test_actual_command_one_history_step_save_open_and_normal_build(self):
        p,asset=self.fixture();source=model_group_allocation.source(p,asset,'a'*64)
        self.assertEqual(source['remaining_group_budget'],64)
        requests=self.requests(source);base=deepcopy(p.model_overrides[asset]['base_binding'])
        before=p.read_model_replacement(asset,p.model_overrides[asset])
        state=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack));files=set((p.root/'Authored'/'Models').iterdir())
        report=model_group_allocation.review(p,asset,requests,source['effective_sha256'],'a'*64)
        self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)
        self.assertEqual(set((p.root/'Authored'/'Models').iterdir()),files)
        with self.assertRaises(ProjectError):p.apply_model_group_allocations(asset,requests,source['effective_sha256'],'a'*64,'0'*64)
        self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)
        self.assertEqual(set((p.root/'Authored'/'Models').iterdir()),files)
        changed=deepcopy(requests);changed[0]['group_id']='group://authored/00000000-0000-4000-8000-000000000098'
        same_bytes=model_group_allocation.review(p,asset,changed,source['effective_sha256'],'a'*64)
        self.assertEqual(same_bytes['proposed_sha256'],report['proposed_sha256'])
        self.assertNotEqual(same_bytes['review_key'],report['review_key'])
        with self.assertRaises(ProjectError):p.apply_model_group_allocations(asset,changed,source['effective_sha256'],'a'*64,report['review_key'])
        self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)
        p.apply_model_group_allocations(asset,requests,source['effective_sha256'],'a'*64,report['review_key'])
        final=p.read_model_replacement(asset,p.model_overrides[asset])
        self.assertEqual(sha256(final).hexdigest(),report['proposed_sha256'])
        self.assertEqual(len(p.undo_stack),len(state[1])+1)
        self.assertEqual(p.model_overrides[asset]['base_binding'],base)
        fresh=model_group_allocation.source(p,asset,'a'*64)
        self.assertEqual(fresh['allocated_group_count'],1);self.assertEqual(fresh['remaining_group_budget'],63)
        self.assertEqual(fresh['remaining_face_budget'],source['remaining_face_budget']-1)
        self.assertEqual(fresh['remaining_batch_budget'],source['remaining_batch_budget']-1)
        p.undo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),before)
        p.redo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),final)
        p.save();saved=deepcopy(p.model_overrides[asset])
        with patch.object(ProjectService,'_model_source',side_effect=p._model_source):
            reopened=ProjectService.open(p.root)
            self.assertEqual(reopened.read_model_replacement(asset,saved),final)
            self.assertEqual(model_group_allocation.source(reopened,asset,'a'*64)['topology'],fresh['topology'])
        out=build_project(p)
        with zipfile.ZipFile(out['path']) as package:
            manifest=tomllib.loads(package.read('manifest.toml').decode());entry=manifest['disc_relocation'][0]
            replacement=decode_relocation_package(package.read(entry['file']),entry['sha256'])['replacement']
        archive=_archive(replacement);carrier=archive.read_entry(archive.entry(1))
        descriptor=parse_scene_assets(carrier,1).descriptors[1]
        pack,_=decompress_lzs(carrier[descriptor.data_offset:],descriptor.size)
        start,_=_pack_ranges(pack)[1];self.assertEqual(pack[start:start+len(final)],final)
        self.assertEqual(p.model_overrides[asset],saved)

    def test_HTTP_exact_source_requests_review_key_and_repeated_apply(self):
        from urllib.request import urlopen
        p,asset=self.fixture()
        with http_server(p) as (server,post),patch.object(server,'state',return_value={'applied':True}):
            with urlopen(f'http://127.0.0.1:{server.server_port}/model-group-allocation.js') as response:
                self.assertEqual(response.status,200)
                self.assertIn(b'export async function openModelGroupAllocation',response.read())
            status,source=post('/api/model-group-allocation-source',dict(asset_id=asset,source_key='a'*64))
            self.assertEqual(status,200)
            requests=self.requests(source)
            body=dict(asset_id=asset,source_key='a'*64,expected_sha256=source['effective_sha256'],requests=requests)
            state=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack))
            status,report=post('/api/model-group-allocation-preview',body);self.assertEqual(status,200)
            self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)
            for changes in (dict(extra=True),dict(source_key='0'*64),dict(expected_sha256='0'*64),dict(requests=[]),
                    dict(requests=requests*65),dict(requests=[dict(requests[0],object_index=0)]),
                    dict(requests=[dict(requests[0],donor_face_id='missing')]),dict(requests=[dict(requests[0],group_id=True)])):
                self.assertEqual(post('/api/model-group-allocation-preview',{**body,**changes})[0],400)
                self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)
            self.assertEqual(post('/api/model-group-allocation',{**body,'review_key':'0'*64})[0],400)
            self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)
            self.assertEqual(post('/api/model-group-allocation',{**body,'review_key':report['review_key']})[0],200)
            state=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack))
            self.assertEqual(post('/api/model-group-allocation',{**body,'review_key':report['review_key']})[0],400)
            self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)

    def test_independent_base_wrapping_and_late_source_change(self):
        p,asset=self.fixture();base=deepcopy(p.model_overrides[asset]['base_binding'])
        p.model_overrides[asset]=base
        source=model_group_allocation.source(p,asset,'a'*64);requests=self.requests(source)
        report=model_group_allocation.review(p,asset,requests,source['effective_sha256'],'a'*64)
        state=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack))
        with patch('sdk.scene_preview.source_key',return_value='0'*64):
            with self.assertRaises(ProjectError):p.apply_model_group_allocations(asset,requests,source['effective_sha256'],'a'*64,report['review_key'])
        self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)
        p.apply_model_group_allocations(asset,requests,source['effective_sha256'],'a'*64,report['review_key'])
        self.assertEqual(p.model_overrides[asset]['base_binding'],base)
        self.assertEqual(p.model_overrides[asset]['ledger']['operations'][0]['kind'],'allocate_groups')

    def test_group_browser_all_native_packet_families_and_objects(self):
        from importer.model_face_ledger import create_face_ledger,replay_face_ledger
        from test_model_primitives import synthetic
        node=shutil.which('node')
        if not node:self.skipTest('Node unavailable')
        reports=[]
        for flags in range(0x10,0x28):
            data=synthetic(((flags,),(flags,)),count=2);ledger=create_face_ledger(data)
            _,audit=replay_face_ledger(data,ledger)
            with patch.object(model_group_allocation,'_context',return_value=(data,data,data,None,ledger,audit)),patch.object(model_group_allocation,'source_key',return_value='a'*64):
                p=SimpleNamespace(active_scene='fixture');source=model_group_allocation.source(p,'model://fixture','a'*64)
                requests=self.requests(source)
                other=deepcopy(requests[0]);other['group_id']=other['group_id'].replace('000000000063','000000000064')
                other['faces'][0]['face_id']=other['faces'][0]['face_id'].replace('000000000063','000000000064')
                donor=next(row for row in source['topology']['faces'] if row['object_index']==1)
                other['donor_face_id']=other['faces'][0]['donor_face_id']=donor['face_id'];requests.append(other)
                report=model_group_allocation.review(p,'model://fixture',requests,source['effective_sha256'],'a'*64)
                reports.append(dict(source=source,requests=requests,report=report))
        script="""import {decodeGroupAllocationSource,decodeGroupAllocationReview} from './integrations/legaia/editor/model-group-allocation.js';
let text='';for await(const chunk of process.stdin)text+=chunk;
for(const {source,requests,report} of JSON.parse(text)){decodeGroupAllocationSource(source,source.asset_id,source.project_source_key);decodeGroupAllocationReview(report,source,requests);}
"""
        result=subprocess.run([node,'--input-type=module','-e',script],input=json.dumps(reports),text=True,
            capture_output=True,cwd=Path(__file__).resolve().parents[3])
        self.assertEqual(result.returncode,0,result.stderr)

    def test_group_creation_browser_adapter_qualifies_actual_reports(self):
        p,asset=self.fixture();source=model_group_allocation.source(p,asset,'a'*64)
        requests=self.requests(source)
        second=self.requests(source,100)[0];requests.append(second)
        second['faces'].append(deepcopy(self.requests(source,101)[0]['faces'][0]))
        report=model_group_allocation.review(p,asset,requests,source['effective_sha256'],'a'*64)
        node=shutil.which('node')
        if not node:self.skipTest('Node unavailable')
        script="""import {decodeGroupAllocationSource,decodeGroupAllocationReview} from './integrations/legaia/editor/model-group-allocation.js';
import assert from 'node:assert/strict';let text='';for await(const chunk of process.stdin)text+=chunk;
const {source,requests,report}=JSON.parse(text),decode=s=>decodeGroupAllocationSource(s,s.asset_id,s.project_source_key);
decode(source);decodeGroupAllocationReview(report,source,requests);
for(const mutate of [s=>s.remaining_group_budget--,s=>s.packet_groups[0][0].stride+=4,s=>s.preview.triangles[0][0]++,s=>s.normal_vectors.push([])]){
 const bad=structuredClone(source);mutate(bad);assert.throws(()=>decode(bad));
}
for(const mutate of [r=>r.allocation.new_groups[0].footer_sha256='0'.repeat(64),r=>r.allocation.new_groups[0].byte_offset++,r=>r.allocation.new_faces[0].byte_offset++,r=>r.preview.triangles.at(-1)[0]++,r=>r.topology.faces[0].current_primitive_index++,r=>r.requests[0].group_id='bad',r=>r.allocation.pointer_relocations[0].current_offset++,r=>r.allocation.pointer_relocations.pop()]){
 const bad=structuredClone(report);mutate(bad);assert.throws(()=>decodeGroupAllocationReview(bad,source,requests));
}
"""
        result=subprocess.run([node,'--input-type=module','-e',script],input=json.dumps(dict(source=source,requests=requests,report=report)),text=True,
            capture_output=True,cwd=Path(__file__).resolve().parents[3])
        self.assertEqual(result.returncode,0,result.stderr)

    def test_actual_new_group_face_source_qualifies_shared_browser_donors(self):
        from sdk import model_face_addition
        p,asset=self.fixture();source=model_group_allocation.source(p,asset,'a'*64)
        requests=self.requests(source)
        report=model_group_allocation.review(p,asset,requests,source['effective_sha256'],'a'*64)
        p.apply_model_group_allocations(asset,requests,source['effective_sha256'],'a'*64,report['review_key'])
        faces=model_face_addition.source(p,asset,'a'*64)
        node=shutil.which('node')
        if not node:self.skipTest('Node unavailable')
        script="""import {decodeFaceAdditionSource} from './integrations/legaia/editor/model-face-addition.js';
import assert from 'node:assert/strict';let text='';for await(const chunk of process.stdin)text+=chunk;
const source=JSON.parse(text);decodeFaceAdditionSource(source,source.asset_id,source.project_source_key);
for(const mutate of [s=>s.topology.allocated_groups[0].face_ids=[],s=>s.topology.allocated_groups[0].current_group_index=0,s=>s.topology.allocated_groups[0].group_id='bad',s=>s.topology.allocated_groups[0].flags^=1,s=>s.topology.allocated_group_count++,s=>s.topology.allocated_groups[0].donor_face_id='missing']){
 const bad=structuredClone(source);mutate(bad);assert.throws(()=>decodeFaceAdditionSource(bad,source.asset_id,source.project_source_key));
}
"""
        result=subprocess.run([node,'--input-type=module','-e',script],input=json.dumps(faces),text=True,
            capture_output=True,cwd=Path(__file__).resolve().parents[3])
        self.assertEqual(result.returncode,0,result.stderr)


if __name__=='__main__':unittest.main()
