"""Mapped materials survive one final retirement of original object geometry."""
from copy import deepcopy
from pathlib import Path
import base64,json,shutil,subprocess,tomllib,unittest,zipfile
from unittest.mock import patch
from sdk import model_mesh_append,model_mesh_batch,model_object_allocation
from sdk.project import ProjectError,ProjectService
from sdk.build import build_project
from importer.core import _pack_ranges,parse_scene_assets,decompress_lzs
from importer.disc_relocation_package import decode_relocation_package
from importer.model_pack_archive import _archive
from test_model_object_ledger import clone_request
from test_model_mesh_batch_selection import sections
from test_model_primitive_workflow import http_server
import test_model_mesh_scene_preview as scene_fixtures
from sdk.scene_preview import preview_shape_instances
import test_model_mesh_append as fixtures


class MappedObjectReplacementTests(unittest.TestCase):
    def test_mapped_object_scene_review_preserves_pose_and_project(self):
        helper=scene_fixtures.MeshScenePreviewTests();self.addCleanup(helper.doCleanups)
        p,asset,donor,content,scene=helper.fixture(True)
        source=model_mesh_append.source(p,asset,'a'*64)
        mappings=[dict(primitive_index=0,donor_face_id=donor,replace_group=False)]
        with patch('sdk.model_mesh_batch.source_key',return_value='a'*64),patch('sdk.model_face_removal.source_key',return_value='a'*64):
            candidate,binding,report=model_mesh_batch.prepare(p,asset,content,mappings,source['effective_sha256'],'a'*64,replace_objects=True)
            body=dict(asset_id=asset,content_base64=base64.b64encode(content).decode(),mappings=mappings,
                expected_sha256=source['effective_sha256'],source_key='a'*64,replace_objects=True,
                review_key=report['review_key'],proposed_sha256=report['proposed_sha256'],entity_id='one',all_instances=True)
            before=deepcopy((p._document(),p.undo_stack,p.redo_stack,scene))
            with http_server(p) as (server,post),patch.dict(p.assets.records,{asset:dict(id=asset)}),patch('sdk.scene_preview.source_key',return_value='a'*64),patch.object(server.scene_previews,'preview',return_value=scene),patch.object(server,'model_preview',side_effect=lambda asset,**kw:kw['prepared']):
                status,posed=post('/api/model-mesh-batch-scene-preview',body)
                self.assertEqual(status,200,posed)
                self.assertEqual(posed['proposal_assets'],preview_shape_instances(scene,asset,candidate,binding)['proposal_assets'])
                self.assertEqual(post('/api/model-mesh-batch-scene-preview',{**body,'replace_objects':False})[0],400)
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack,scene),before)

    def fixture(self):
        helper=fixtures.MeshAppendTests();self.addCleanup(helper.doCleanups)
        p,asset,donor=helper.fixture();self.enterContext(patch('sdk.model_mesh_batch.source_key',return_value='a'*64))
        self.enterContext(patch('sdk.model_face_removal.source_key',return_value='a'*64))
        self.enterContext(patch('sdk.model_object_allocation.source_key',return_value='a'*64))
        source=model_object_allocation.source(p,asset,'a'*64)
        requests=[clone_request(source['topology'],source['object_identities'][0],7300)]
        review=model_object_allocation.review(p,asset,requests,source['effective_sha256'],'a'*64)
        p.apply_model_object_allocations(asset,requests,source['effective_sha256'],'a'*64,review['review_key'])
        return p,asset

    def qualify(self,source,report):
        script="""import {decodeMeshBatchReview} from './integrations/legaia/editor/model-mesh-batch.js';
import assert from 'node:assert/strict';let data='';for await(const c of process.stdin)data+=c;
const {source,report}=JSON.parse(data);const check=r=>decodeMeshBatchReview(r,source,r.glb_sha256,r.mappings,false,null,0,1,true);check(report);
for(const mutate of [r=>r.removed_face_ids.pop(),r=>r.replaced_object_indices.push(999),r=>r.retirement.review.topology.operation_count++,r=>r.retirement.review.preview.triangles[0].reverse(),r=>r.retirement.review.topology.allocated_groups.at(-1).face_ids.pop(),r=>r.retirement.source.face_topology.pop(),r=>r.retirement.mesh_source.effective_sha256='0'.repeat(64),r=>r.retirement.review.selections.pop()]){const r=structuredClone(report);mutate(r);assert.throws(()=>check(r));}
assert.throws(()=>decodeMeshBatchReview(report,source,report.glb_sha256,report.mappings));"""
        r=subprocess.run([shutil.which('node'),'--input-type=module','-e',script],input=json.dumps(dict(source=source,report=report)),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3])
        self.assertEqual(r.returncode,0,r.stderr)

    def test_multiple_mapped_objects_replay_and_normal_build(self):
        p,asset=self.fixture();source=model_mesh_append.source(p,asset,'a'*64)
        donors=[next(f['face_id'] for f in source['topology']['faces'] if f['object_index']==owner) for owner in (0,1)]
        mappings=[dict(primitive_index=i,donor_face_id=donor,replace_group=False) for i,donor in zip((0,2),donors)]
        args=(asset,sections(3),mappings,source['effective_sha256'],'a'*64)
        state=deepcopy((p._document(),p.undo_stack,p.redo_stack));files=set((p.root/'Authored'/'Models').iterdir())
        candidate,_,report=model_mesh_batch.prepare(p,*args,replace_objects=True)
        self.assertEqual(report['schema_version'],'legaia.model-mesh-batch-review.v2')
        self.assertEqual(report['replaced_object_indices'],[0,1]);self.assertEqual(report['skipped_primitive_indices'],[1])
        self.assertEqual(report['removed_face_ids'],[f['face_id'] for f in source['topology']['faces']])
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack),state);self.assertEqual(set((p.root/'Authored'/'Models').iterdir()),files)
        self.qualify(source,report)
        with self.assertRaises(ProjectError):model_mesh_batch.apply(p,*args,review_key=report['review_key'])
        model_mesh_batch.apply(p,*args,review_key=report['review_key'],replace_objects=True)
        self.assertEqual(len(p.undo_stack),len(state[1])+1);self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),candidate)
        self.assertEqual(report['topology']['objects'],source['topology']['objects'])
        p.undo();self.assertEqual(p._document(),state[0]);p.redo();p.save()
        with patch.object(ProjectService,'_model_source',side_effect=p._model_source):
            reopened=ProjectService.open(p.root);self.assertEqual(reopened.read_model_replacement(asset,reopened.model_overrides[asset]),candidate)
        out=build_project(p)
        with zipfile.ZipFile(out['path']) as z:
            entry=tomllib.loads(z.read('manifest.toml').decode())['disc_relocation'][0]
            archive=_archive(decode_relocation_package(z.read(entry['file']),entry['sha256'])['replacement'])
        carrier=archive.read_entry(archive.entry(1));d=parse_scene_assets(carrier,1).descriptors[1]
        pack,_=decompress_lzs(carrier[d.data_offset:],d.size);start,_=_pack_ranges(pack)[0]
        self.assertEqual(pack[start:start+len(candidate)],candidate)

    def test_unmapped_object_held_and_exact_http_choices(self):
        p,asset=self.fixture();source=model_mesh_append.source(p,asset,'a'*64);donor=source['topology']['faces'][0]['face_id']
        mappings=[dict(primitive_index=i,donor_face_id=donor,replace_group=False) for i in range(2)]
        body=dict(asset_id=asset,content_base64=base64.b64encode(sections(2)).decode(),mappings=mappings,expected_sha256=source['effective_sha256'],source_key='a'*64,replace_objects=True)
        state=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        with http_server(p) as (server,post),patch.object(server,'state',return_value={'applied':True}):
            for choice in (1,'true'):
                self.assertEqual(post('/api/model-mesh-batch-preview',{**body,'replace_objects':choice})[0],400)
            conflicting=deepcopy(mappings);conflicting[0]['replace_group']=True
            self.assertEqual(post('/api/model-mesh-batch-preview',{**body,'mappings':conflicting})[0],400)
            status,report=post('/api/model-mesh-batch-preview',body);self.assertEqual(status,200,report)
            self.qualify(source,report)
            self.assertEqual(report['replaced_object_indices'],[0]);self.assertEqual((p._document(),p.undo_stack,p.redo_stack),state)
            self.assertEqual([f for f in report['topology']['faces'] if f['object_index']==1],[f for f in source['topology']['faces'] if f['object_index']==1])
            self.assertEqual(post('/api/model-mesh-batch',{**body,'replace_objects':False,'review_key':report['review_key']})[0],400)
            self.assertEqual(post('/api/model-mesh-batch',{**body,'review_key':report['review_key']})[0],200)

    def test_existing_tombstones_and_allocated_groups_remain_historical(self):
        p,asset=self.fixture();source=model_mesh_append.source(p,asset,'a'*64);donor=source['topology']['faces'][0]['face_id']
        args=(asset,sections(1),donor,source['effective_sha256'],'a'*64)
        first=model_mesh_append.review(p,*args,new_group=True,replace_group=True)
        p.apply_model_mesh_append(*args,first['review_key'],new_group=True,replace_group=True)
        source=model_mesh_append.source(p,asset,'a'*64);donor=next(f['face_id'] for f in source['topology']['faces'] if f['object_index']==0)
        mappings=[dict(primitive_index=i,donor_face_id=donor,replace_group=False) for i in range(2)]
        _,_,report=model_mesh_batch.prepare(p,asset,sections(2),mappings,source['effective_sha256'],'a'*64,replace_objects=True)
        self.qualify(source,report)
        self.assertEqual(report['topology']['removed_face_ids'],source['topology']['removed_face_ids']+report['removed_face_ids'])
        self.assertGreater(report['topology']['authored_face_count'],len(report['topology']['faces']))


if __name__=='__main__':unittest.main()
