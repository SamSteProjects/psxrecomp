"""Topology-changing group mesh replacement retires exact stable faces atomically."""
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
from sdk import model_mesh_append,model_face_removal,model_object_allocation
from test_model_object_ledger import clone_request
from sdk.model_reference_faces import addition_group_ownership
from sdk.project import ProjectService,ProjectError
from sdk.build import build_project
import test_model_mesh_append as fixtures
from test_model_primitive_workflow import http_server


class MeshGroupReplacementTests(unittest.TestCase):
    def fixture(self):
        h=fixtures.MeshAppendTests();self.addCleanup(h.doCleanups)
        p,asset,donor=h.fixture()
        content=fixtures.glb(positions=[[0,0,0],[100,0,0],[0,100,0],[100,100,0],[200,0,0]],indices=[0,1,2,1,3,2,1,4,3])
        return p,asset,donor,content

    def test_topology_replacement_one_history_reopen_build_and_restoration(self):
        p,asset,donor,content=self.fixture();source=model_mesh_append.source(p,asset,'a'*64)
        before=p.read_model_replacement(asset,p.model_overrides[asset]);state=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        files=set((p.root/'Authored'/'Models').iterdir());args=(asset,content,donor,source['effective_sha256'],'a'*64)
        report=model_mesh_append.review(p,*args,new_group=True,replace_group=True)
        append=model_mesh_append.review(p,*args,new_group=True)
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack),state);self.assertEqual(set((p.root/'Authored'/'Models').iterdir()),files)
        self.assertEqual(report['schema_version'],'legaia.model-mesh-append-review.v6')
        self.assertEqual(report['removed_face_ids'],[face['face_id'] for face in source['topology']['faces']])
        self.assertEqual(len(report['topology']['faces']),3);self.assertEqual(len(report['preview']['triangles']),3)
        self.assertEqual(report['topology']['operation_count'],3)
        for choices,key in ((dict(new_group=True),report['review_key']),(dict(new_group=True,replace_group=True),append['review_key'])):
            with self.assertRaises(ProjectError):p.apply_model_mesh_append(*args,key,**choices)
        p.apply_model_mesh_append(*args,report['review_key'],new_group=True,replace_group=True)
        final=p.read_model_replacement(asset,p.model_overrides[asset]);self.assertEqual(len(p.undo_stack),len(state[1])+1)
        self.assertEqual([op['kind'] for op in p.model_overrides[asset]['ledger']['operations']],['allocate_vectors','allocate_groups','remove_faces'])
        current=model_mesh_append.source(p,asset,'a'*64);self.assertEqual(len(current['packet_groups'][0]),1)
        self.assertEqual(current['topology']['allocated_groups'][0]['current_group_index'],0)
        ownership=addition_group_ownership(p,asset,p._model_source(asset,p.active_scene),final,p.model_overrides[asset])
        self.assertEqual(ownership[0],[[None]])
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
        selections=[dict(face_id=identity) for identity in report['removed_face_ids']]
        with patch('sdk.model_face_removal.source_key',return_value='a'*64):
            candidate,_,restoration=model_face_removal.prepare(p,asset,selections,report['proposed_sha256'],'a'*64,restore=True)
            p.apply_model_face_removal(asset,selections,report['proposed_sha256'],'a'*64,restoration['proposed_sha256'],restore=True)
        self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),candidate)
        restored=model_mesh_append.source(p,asset,'a'*64);self.assertEqual(len(restored['objects'][0]['primitives']),5)
        self.assertEqual(restored['topology']['removed_face_ids'],[]);self.assertEqual(len(restored['packet_groups'][0]),2)

    def test_http_exact_replace_mode_and_review_binding(self):
        p,asset,donor,content=self.fixture();source=model_mesh_append.source(p,asset,'a'*64)
        body=dict(asset_id=asset,content_base64=base64.b64encode(content).decode(),donor_face_id=donor,
            expected_sha256=source['effective_sha256'],source_key='a'*64,new_group=True,replace_group=True)
        with http_server(p) as (server,post),patch.object(server,'state',return_value={'applied':True}):
            for changes in (dict(replace_group='true'),dict(replace_group=1),dict(new_group=False)):
                self.assertEqual(post('/api/model-mesh-append-preview',{**body,**changes})[0],400)
            status,report=post('/api/model-mesh-append-preview',body);self.assertEqual(status,200)
            self.assertEqual(report['allocation_mode'],'replace_group')
            self.assertEqual(post('/api/model-mesh-append',{**body,'replace_group':False,'review_key':report['review_key']})[0],400)
            self.assertEqual(post('/api/model-mesh-append',{**body,'review_key':report['review_key']})[0],200)
            self.assertEqual(post('/api/model-mesh-append',{**body,'review_key':report['review_key']})[0],400)

    def test_replacement_of_copied_group_retains_v7_and_inspectable_tombstones(self):
        p,asset,_,content=self.fixture()
        with patch('sdk.model_object_allocation.source_key',return_value='a'*64):
            source=model_object_allocation.source(p,asset,'a'*64)
            requests=[clone_request(source['topology'],source['object_identities'][0],2600)]
            clone=model_object_allocation.review(p,asset,requests,source['effective_sha256'],'a'*64)
            p.apply_model_object_allocations(asset,requests,source['effective_sha256'],'a'*64,clone['review_key'])
        source=model_mesh_append.source(p,asset,'a'*64);donor=next(face['face_id'] for face in source['topology']['faces'] if face['object_index']==1)
        args=(asset,content,donor,source['effective_sha256'],'a'*64)
        report=model_mesh_append.review(p,*args,new_group=True,replace_group=True)
        p.apply_model_mesh_append(*args,report['review_key'],new_group=True,replace_group=True)
        self.assertEqual(p.model_overrides[asset]['ledger']['schema_version'],'legaia.model-face-addition-ledger.v7')
        self.assertEqual(report['topology']['objects'],source['topology']['objects'])
        current=model_mesh_append.source(p,asset,'a'*64);groups=current['topology']['allocated_groups']
        self.assertIsNone(groups[0]['current_group_index']);self.assertEqual(groups[0]['face_ids'],[])
        self.assertEqual(groups[-1]['current_group_index'],0)
        self.assertEqual(current['next_group_origin_indices'],[1,2])
        node=shutil.which('node')
        if node:
            script="""import {decodeMeshAppendSource} from './integrations/legaia/editor/model-mesh-append.js';let data='';for await(const chunk of process.stdin)data+=chunk;const source=JSON.parse(data);decodeMeshAppendSource(source,source.asset_id,source.project_source_key);"""
            result=subprocess.run([node,'--input-type=module','-e',script],input=json.dumps(current),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3])
            self.assertEqual(result.returncode,0,result.stderr)


if __name__=='__main__':unittest.main()
