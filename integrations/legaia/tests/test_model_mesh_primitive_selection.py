"""Selected GLB sections keep reviewed native ownership through delivery."""
import base64
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import tomllib
import unittest
from unittest.mock import patch
import zipfile
from importer.core import ImportError,parse_scene_assets,decompress_lzs,_pack_ranges
from importer.disc_relocation_package import decode_relocation_package
from importer.model_pack_archive import _archive
from importer.model_mesh_append import inspect_append_mesh,decode_append_mesh
from sdk import model_mesh_append
from sdk.build import build_project
from sdk.project import ProjectService,ProjectError
import test_model_mesh_append as fixtures
from test_model_primitive_workflow import http_server


def sections(transform=None):
    def change(doc):
        if transform is not None:doc['nodes'][0].update(transform)
        first=doc['meshes'][0]['primitives'][0]
        second=deepcopy(first);second['attributes'].pop('TEXCOORD_0')
        first['material']=0;second['material']=1
        doc['meshes'][0]['primitives'].append(second)
        doc['materials']=[dict(name='Stone'),dict(name='Trim')]
    return fixtures.glb(change,uvs=[[0,0],[1,0],[0,1],[1,1]])


class MeshPrimitiveSelectionTests(unittest.TestCase):
    def test_file_inventory_and_selected_attribute_ownership(self):
        content=sections();report=inspect_append_mesh(content)
        self.assertEqual(report['triangle_count'],4)
        self.assertEqual([row['material_name'] for row in report['primitives']],['Stone','Trim'])
        geometry=decode_append_mesh(content,primitive_index=1,preserve_primitives=True)
        self.assertEqual(len(geometry['triangles']),2)
        self.assertEqual(geometry['triangle_uvs'],[None,None])
        self.assertEqual(geometry['primitive_ranges'],[dict(primitive_index=0,first_triangle=0,triangle_count=2,source_mode=4)])
        for invalid in (-1,2,True,1.0,'1'):
            with self.assertRaises(ImportError):decode_append_mesh(content,primitive_index=invalid)

    def test_http_review_selection_rejects_stale_apply_and_delivers_exact_model(self):
        helper=fixtures.MeshAppendTests();self.addCleanup(helper.doCleanups)
        p,asset,donor=helper.fixture();content=sections();source=model_mesh_append.source(p,asset,'a'*64)
        args=(asset,content,donor,source['effective_sha256'],'a'*64)
        candidate,_,report=model_mesh_append.prepare(p,*args,new_group=True,preserve_primitives=True,primitive_index=1)
        before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        self.assertEqual(len(report['additions']),2);self.assertEqual(report['selected_primitive_index'],1)
        with http_server(p) as (_,post):
            status,inventory=post('/api/model-mesh-file',dict(content_base64=base64.b64encode(content).decode()))
            self.assertEqual(status,200,inventory)
            body=dict(asset_id=asset,content_base64=base64.b64encode(content).decode(),donor_face_id=donor,
                expected_sha256=source['effective_sha256'],source_key='a'*64,new_group=True,preserve_primitives=True,primitive_index=1)
            status,review=post('/api/model-mesh-append-preview',body);self.assertEqual(status,200,review)
            self.assertEqual(review['review_key'],report['review_key'])
            status,_=post('/api/model-mesh-append',dict(body,primitive_index=0,review_key=report['review_key']))
            self.assertEqual(status,400)
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
        node=shutil.which('node');self.assertIsNotNone(node)
        script="""import {decodeMeshFile,decodeMeshAppendSource,decodeMeshAppendReview} from './integrations/legaia/editor/model-mesh-append.js';
import assert from 'node:assert/strict';let data='';for await(const c of process.stdin)data+=c;
const {source,report,inventory}=JSON.parse(data);decodeMeshFile(inventory,report.geometry.glb_sha256);
const s=decodeMeshAppendSource(source,source.asset_id,source.project_source_key);
decodeMeshAppendReview(report,s,report.donor_face_id,report.geometry.glb_sha256,true,false,true,1);
assert.throws(()=>decodeMeshAppendReview(report,s,report.donor_face_id,report.geometry.glb_sha256,true,false,true,0));
const bad=structuredClone(inventory);bad.primitives[1].triangle_count--;assert.throws(()=>decodeMeshFile(bad,report.geometry.glb_sha256));"""
        out=subprocess.run([node,'--input-type=module','-e',script],input=json.dumps(dict(source=source,report=report,inventory=inventory)),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3])
        self.assertEqual(out.returncode,0,out.stderr)
        p.apply_model_mesh_append(*args,report['review_key'],new_group=True,preserve_primitives=True,primitive_index=1)
        self.assertEqual(len(p.undo_stack),len(before[1])+1)
        self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),candidate)
        p.undo();self.assertEqual(p._document(),before[0]);p.redo();p.save()
        with patch.object(ProjectService,'_model_source',side_effect=p._model_source):
            reopened=ProjectService.open(p.root)
            self.assertEqual(reopened.read_model_replacement(asset,reopened.model_overrides[asset]),candidate)
        out=build_project(p)
        with zipfile.ZipFile(out['path']) as package:
            manifest=tomllib.loads(package.read('manifest.toml').decode());entry=manifest['disc_relocation'][0]
            replacement=decode_relocation_package(package.read(entry['file']),entry['sha256'])['replacement']
        archive=_archive(replacement);carrier=archive.read_entry(archive.entry(1))
        d=parse_scene_assets(carrier,1).descriptors[1];pack,_=decompress_lzs(carrier[d.data_offset:],d.size)
        start,_=_pack_ranges(pack)[0];self.assertEqual(pack[start:start+len(candidate)],candidate)


if __name__=='__main__':unittest.main()
