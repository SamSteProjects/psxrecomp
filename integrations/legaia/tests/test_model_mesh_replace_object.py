"""Whole-object geometry replacement retires all groups without replacing identity."""
from copy import deepcopy
import base64,json,shutil,subprocess,unittest,tomllib,zipfile
from pathlib import Path
from unittest.mock import patch
from sdk import model_mesh_append,model_object_allocation,model_face_removal
from sdk.project import ProjectError,ProjectService
from sdk.build import build_project
from importer.core import _pack_ranges,parse_scene_assets,decompress_lzs
from importer.disc_relocation_package import decode_relocation_package
from importer.model_pack_archive import _archive
from test_model_object_ledger import clone_request
from test_model_primitive_workflow import http_server
import test_model_mesh_append as fixtures
import test_model_mesh_replace_group as group_fixtures


class MeshObjectReplacementTests(unittest.TestCase):
    def fixture(self):
        helper=group_fixtures.MeshGroupReplacementTests();self.addCleanup(helper.doCleanups)
        return helper.fixture()

    def multigroup(self):
        p,asset,donor,content=self.fixture()
        source=model_mesh_append.source(p,asset,'a'*64)
        args=(asset,content,donor,source['effective_sha256'],'a'*64)
        report=model_mesh_append.review(p,*args,new_group=True)
        p.apply_model_mesh_append(*args,report['review_key'],new_group=True)
        with patch('sdk.model_object_allocation.source_key',return_value='a'*64):
            source=model_object_allocation.source(p,asset,'a'*64)
            requests=[clone_request(source['topology'],source['object_identities'][0],3300)]
            report=model_object_allocation.review(p,asset,requests,source['effective_sha256'],'a'*64)
            p.apply_model_object_allocations(asset,requests,source['effective_sha256'],'a'*64,report['review_key'])
        return p,asset,content

    def test_all_groups_retired_other_object_held_and_history_preserved(self):
        p,asset,content=self.multigroup();source=model_mesh_append.source(p,asset,'a'*64)
        owner=1;donor=next(f['face_id'] for f in source['topology']['faces'] if f['object_index']==owner)
        args=(asset,content,donor,source['effective_sha256'],'a'*64)
        state=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        report=model_mesh_append.review(p,*args,new_group=True,replace_object=True)
        self.assertEqual(report['schema_version'],'legaia.model-mesh-append-review.v8')
        retired=[f['face_id'] for f in source['topology']['faces'] if f['object_index']==owner]
        self.assertEqual(len(set(f['group_index'] for f in source['topology']['faces'] if f['object_index']==owner)),2)
        self.assertEqual(report['removed_face_ids'],retired)
        self.assertEqual(report['topology']['objects'],source['topology']['objects'])
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack),state)
        script="""import {decodeMeshAppendReview} from './integrations/legaia/editor/model-mesh-append.js';
import assert from 'node:assert/strict';let data='';for await(const c of process.stdin)data+=c;
const {source,report}=JSON.parse(data);const check=r=>decodeMeshAppendReview(r,source,r.donor_face_id,r.geometry.glb_sha256,true,false,false,null,false,null,0,1,true);
check(report);
for(const mutate of [r=>r.removed_face_ids.pop(),r=>r.replaced_object.object_index=0,r=>r.replaced_group={object_index:1,group_index:0},r=>r.replace_object=false,r=>r.preview.triangles[0].reverse(),r=>r.topology.allocated_groups[0].current_group_index=null]){const r=structuredClone(report);mutate(r);assert.throws(()=>check(r));}
assert.throws(()=>decodeMeshAppendReview(report,source,report.donor_face_id,report.geometry.glb_sha256,true,true));"""
        result=subprocess.run([shutil.which('node'),'--input-type=module','-e',script],input=json.dumps(dict(source=source,report=report)),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3])
        self.assertEqual(result.returncode,0,result.stderr)
        group=model_mesh_append.review(p,*args,new_group=True,replace_group=True)
        with self.assertRaises(ProjectError):p.apply_model_mesh_append(*args,group['review_key'],new_group=True,replace_object=True)
        p.apply_model_mesh_append(*args,report['review_key'],new_group=True,replace_object=True)
        final=p.read_model_replacement(asset,p.model_overrides[asset]);self.assertEqual(len(p.undo_stack),len(state[1])+1)
        fresh=model_mesh_append.source(p,asset,'a'*64)
        self.assertEqual(len(fresh['packet_groups'][owner]),1)
        self.assertEqual([f for f in fresh['topology']['faces'] if f['object_index']==0],[f for f in source['topology']['faces'] if f['object_index']==0])
        for group in fresh['topology']['allocated_groups'][:-1]:
            if group['object_index']==owner:self.assertIsNone(group['current_group_index']);self.assertEqual(group['face_ids'],[])
        self.assertEqual(fresh['preview']['vertices'][:source['preview']['objects'][owner]['vertex_start']],source['preview']['vertices'][:source['preview']['objects'][owner]['vertex_start']])
        p.undo();self.assertEqual(p._document(),state[0]);p.redo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),final)
        p.save()
        with patch.object(ProjectService,'_model_source',side_effect=p._model_source):
            reopened=ProjectService.open(p.root)
            self.assertEqual(reopened.read_model_replacement(asset,reopened.model_overrides[asset]),final)
        output=build_project(p)
        with zipfile.ZipFile(output['path']) as package:
            entry=tomllib.loads(package.read('manifest.toml').decode())['disc_relocation'][0]
            archive=_archive(decode_relocation_package(package.read(entry['file']),entry['sha256'])['replacement'])
        carrier=archive.read_entry(archive.entry(1));descriptor=parse_scene_assets(carrier,1).descriptors[1]
        pack,_=decompress_lzs(carrier[descriptor.data_offset:],descriptor.size);start,_=_pack_ranges(pack)[0]
        self.assertEqual(pack[start:start+len(final)],final)
        with patch('sdk.model_face_removal.source_key',return_value='a'*64):
            restored,_,audit=model_face_removal.prepare(p,asset,[dict(face_id=f) for f in retired],report['proposed_sha256'],'a'*64,restore=True)
        self.assertEqual(len(audit['topology']['faces']),len(source['topology']['faces'])+len(report['additions']))

    def test_preserved_source_sections_and_exact_http_modes(self):
        p,asset,content=self.multigroup();source=model_mesh_append.source(p,asset,'a'*64)
        donor=source['topology']['faces'][0]['face_id']
        content=fixtures.glb(lambda d:d['meshes'][0]['primitives'].append(deepcopy(d['meshes'][0]['primitives'][0])))
        body=dict(asset_id=asset,content_base64=base64.b64encode(content).decode(),donor_face_id=donor,
            expected_sha256=source['effective_sha256'],source_key='a'*64,new_group=True,replace_object=True,preserve_primitives=True)
        with http_server(p) as (server,post),patch.object(server,'state',return_value={'applied':True}):
            state=deepcopy((p._document(),p.undo_stack,p.redo_stack))
            for change in (dict(replace_object=1),dict(replace_object='true'),dict(replace_group=True),dict(new_group=False)):
                self.assertEqual(post('/api/model-mesh-append-preview',{**body,**change})[0],400)
                self.assertEqual((p._document(),p.undo_stack,p.redo_stack),state)
            status,review=post('/api/model-mesh-append-preview',body);self.assertEqual(status,200,review)
            self.assertEqual(len(review['group_requests']),2);self.assertEqual(review['allocation_mode'],'replace_object')
            script="""import {decodeMeshAppendReview} from './integrations/legaia/editor/model-mesh-append.js';let data='';for await(const c of process.stdin)data+=c;const {source,review}=JSON.parse(data);decodeMeshAppendReview(review,source,review.donor_face_id,review.geometry.glb_sha256,true,false,true,null,false,null,0,1,true);"""
            r=subprocess.run([shutil.which('node'),'--input-type=module','-e',script],input=json.dumps(dict(source=source,review=review)),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3])
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertEqual(post('/api/model-mesh-append',{**body,'replace_object':False,'review_key':review['review_key']})[0],400)
            self.assertEqual(post('/api/model-mesh-append',{**body,'review_key':review['review_key']})[0],200)


if __name__=='__main__':unittest.main()
