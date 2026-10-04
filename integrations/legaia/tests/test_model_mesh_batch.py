"""Multi-section native donor maps publish one complete ledger."""
from copy import deepcopy
import base64
import json
from pathlib import Path
import shutil
import subprocess
import tomllib
import unittest
from unittest.mock import patch
import zipfile
from importer.core import _pack_ranges,parse_scene_assets,decompress_lzs
from importer.disc_relocation_package import decode_relocation_package
from importer.model_pack_archive import _archive
from sdk import model_mesh_append,model_mesh_batch,model_object_allocation
from sdk.build import build_project
from sdk.project import ProjectService,ProjectError
import test_model_mesh_append as fixtures
from test_model_mesh_primitive_selection import sections
from test_model_object_ledger import clone_request
from test_model_primitive_workflow import http_server


class MeshBatchTests(unittest.TestCase):
    def test_distinct_object_replacements_and_http_apply_are_atomic(self):
        helper=fixtures.MeshAppendTests();self.addCleanup(helper.doCleanups)
        p,asset,donor=helper.fixture();self.enterContext(patch('sdk.model_mesh_batch.source_key',return_value='a'*64))
        self.enterContext(patch('sdk.model_object_allocation.source_key',return_value='a'*64))
        source=model_object_allocation.source(p,asset,'a'*64)
        requests=[clone_request(source['topology'],source['object_identities'][0],6200)]
        clone=model_object_allocation.review(p,asset,requests,source['effective_sha256'],'a'*64)
        p.apply_model_object_allocations(asset,requests,source['effective_sha256'],'a'*64,clone['review_key'])
        source=model_mesh_append.source(p,asset,'a'*64)
        other=next(face['face_id'] for face in source['topology']['faces'] if face['object_index']==1)
        mappings=[dict(primitive_index=0,donor_face_id=donor,replace_group=True),dict(primitive_index=1,donor_face_id=other,replace_group=True)]
        content=sections();before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        args=(asset,content,mappings,source['effective_sha256'],'a'*64)
        candidate,_,report=model_mesh_batch.prepare(p,*args)
        self.assertEqual([row['review']['object_index'] for row in report['steps']],[0,1])
        self.assertTrue(all(len(row['review']['removed_face_ids'])==2 for row in report['steps']))
        with http_server(p) as (_,post):
            body=dict(asset_id=asset,content_base64=base64.b64encode(content).decode(),mappings=mappings,expected_sha256=source['effective_sha256'],source_key='a'*64)
            status,review=post('/api/model-mesh-batch-preview',body);self.assertEqual(status,200,review)
            self.assertEqual(review['review_key'],report['review_key'])
            status,_=post('/api/model-mesh-batch',dict(body,review_key='0'*64));self.assertEqual(status,400)
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
            status,state=post('/api/model-mesh-batch',dict(body,review_key=report['review_key']));self.assertEqual(status,200,state)
        self.assertEqual(len(p.undo_stack),len(before[1])+1)
        self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),candidate)
        p.undo();self.assertEqual(p._document(),before[0])

    def test_review_history_persistence_and_exact_build(self):
        helper=fixtures.MeshAppendTests();self.addCleanup(helper.doCleanups)
        p,asset,donor=helper.fixture();self.enterContext(patch('sdk.model_mesh_batch.source_key',return_value='a'*64))
        source=model_mesh_append.source(p,asset,'a'*64);content=sections()
        mappings=[dict(primitive_index=i,donor_face_id=donor,replace_group=False) for i in range(2)]
        args=(asset,content,mappings,source['effective_sha256'],'a'*64)
        before=deepcopy((p._document(),p.undo_stack,p.redo_stack));files=set((p.root/'Authored'/'Models').iterdir())
        candidate,binding,report=model_mesh_batch.prepare(p,*args)
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
        self.assertEqual(set((p.root/'Authored'/'Models').iterdir()),files)
        self.assertEqual(len(report['steps']),2)
        self.assertEqual(report['steps'][1]['source']['effective_sha256'],report['steps'][0]['review']['proposed_sha256'])
        self.assertEqual(report['topology']['allocated_group_count'],2)
        self.assertEqual(report['topology']['authored_face_count'],4)
        bad=deepcopy(mappings);bad[1]['replace_group']=True
        with self.assertRaises(ProjectError):model_mesh_batch.prepare(p,asset,content,bad,source['effective_sha256'],'a'*64)
        with self.assertRaises(ProjectError):model_mesh_batch.apply(p,*args,review_key='0'*64)
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
        model_mesh_batch.apply(p,*args,review_key=report['review_key'])
        self.assertEqual(len(p.undo_stack),len(before[1])+1)
        self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),candidate)
        p.undo();self.assertEqual(p._document(),before[0]);p.redo();p.save()
        with patch.object(ProjectService,'_model_source',side_effect=p._model_source):
            reopened=ProjectService.open(p.root)
            self.assertEqual(reopened.read_model_replacement(asset,reopened.model_overrides[asset]),candidate)
        out=build_project(p)
        with zipfile.ZipFile(out['path']) as package:
            manifest=tomllib.loads(package.read('manifest.toml').decode());entry=manifest['disc_relocation'][0]
            archive=_archive(decode_relocation_package(package.read(entry['file']),entry['sha256'])['replacement'])
        carrier=archive.read_entry(archive.entry(1));d=parse_scene_assets(carrier,1).descriptors[1]
        pack,_=decompress_lzs(carrier[d.data_offset:],d.size);start,_=_pack_ranges(pack)[0]
        self.assertEqual(pack[start:start+len(candidate)],candidate)
        node=shutil.which('node');self.assertIsNotNone(node)
        script="""import {decodeMeshBatchReview} from './integrations/legaia/editor/model-mesh-batch.js';
import assert from 'node:assert/strict';let data='';for await(const c of process.stdin)data+=c;
const {source,report}=JSON.parse(data);decodeMeshBatchReview(report,source,report.glb_sha256,report.mappings);
for(const mutate of [r=>r.steps[1].source.effective_sha256='0'.repeat(64),r=>r.mappings.reverse(),r=>r.preview.vertices[0][0]++,r=>r.steps[1].review.selected_primitive_index=0]){const r=structuredClone(report);mutate(r);assert.throws(()=>decodeMeshBatchReview(r,source,report.glb_sha256,report.mappings));}"""
        out=subprocess.run([node,'--input-type=module','-e',script],input=json.dumps(dict(source=source,report=report)),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3])
        self.assertEqual(out.returncode,0,out.stderr)


if __name__=='__main__':unittest.main()
