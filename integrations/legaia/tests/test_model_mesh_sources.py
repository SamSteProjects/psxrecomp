"""Static mesh instances retain node ownership across selection and delivery."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import tomllib
import unittest
from unittest.mock import patch
import zipfile
from importer.core import ImportError,_pack_ranges,parse_scene_assets,decompress_lzs
from importer.disc_relocation_package import decode_relocation_package
from importer.model_pack_archive import _archive
from importer.model_mesh_append import decode_append_mesh,inspect_append_mesh
from sdk import model_mesh_append,model_mesh_batch
from sdk.project import ProjectService
from sdk.build import build_project
import test_model_mesh_append as fixtures


def instances(distinct_mesh=False):
    def change(doc):
        doc['nodes'].append(dict(mesh=0,translation=[500,0,0],scale=[-1,2,1]))
        if distinct_mesh:
            doc['meshes'].append(deepcopy(doc['meshes'][0]));doc['nodes'][1]['mesh']=1
        doc['scenes'][0]['nodes']=[1,0]
    return fixtures.glb(change,uvs=[[0,0],[1,0],[0,1],[1,1]])


class MeshSourceTests(unittest.TestCase):
    def test_instances_keep_root_order_and_separate_shared_accessor_vertices(self):
        content=instances();geometry=decode_append_mesh(content,preserve_primitives=True)
        self.assertEqual(len(geometry['vertices']),8)
        self.assertEqual(geometry['vertices'][:4],[[500,0,0],[400,0,0],[500,-200,0],[400,-200,0]])
        self.assertEqual([row['node_index'] for row in geometry['node_sources']],[1,0])
        self.assertEqual([row['mesh_index'] for row in geometry['node_sources']],[0,0])
        self.assertEqual(geometry['triangles'],[[0,1,2],[1,3,2],[4,5,6],[6,5,7]])
        selected=decode_append_mesh(content,primitive_index=1)
        self.assertEqual(selected['vertices'],decode_append_mesh(fixtures.glb())['vertices'])
        self.assertEqual(selected['node_sources'][0]['primitive_index'],1)
        self.assertEqual(selected['node_sources'][0]['node_index'],0)
        self.assertEqual(inspect_append_mesh(content)['node_sources'],geometry['node_sources'])
        for change in (lambda d:d['scenes'][0].update(nodes=[0,0]),lambda d:d['scenes'][0].update(nodes=[2]),lambda d:d['nodes'][0].update(mesh=True),lambda d:d['nodes'][0].update(children=[1])):
            with self.assertRaises(ImportError):decode_append_mesh(fixtures.glb(change))

    def test_multi_node_batch_browser_history_reopen_and_exact_build(self):
        helper=fixtures.MeshAppendTests();self.addCleanup(helper.doCleanups)
        p,asset,donor=helper.fixture();self.enterContext(patch('sdk.model_mesh_batch.source_key',return_value='a'*64))
        source=model_mesh_append.source(p,asset,'a'*64);content=instances(distinct_mesh=True)
        mappings=[dict(primitive_index=i,donor_face_id=donor,replace_group=False) for i in range(2)]
        args=(asset,content,mappings,source['effective_sha256'],'a'*64)
        before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        candidate,_,report=model_mesh_batch.prepare(p,*args)
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
        self.assertEqual([step['review']['geometry']['node_sources'][0]['node_index'] for step in report['steps']],[1,0])
        node=shutil.which('node');self.assertIsNotNone(node)
        script="""import {decodeMeshBatchReview} from './integrations/legaia/editor/model-mesh-batch.js';
import assert from 'node:assert/strict';let data='';for await(const c of process.stdin)data+=c;const {source,report}=JSON.parse(data);
decodeMeshBatchReview(report,source,report.glb_sha256,report.mappings);
for(const mutate of [r=>r.steps[0].review.geometry.node_sources[0].node_index=0,r=>r.steps[1].review.geometry.node_sources[0].mesh_index=1,r=>r.inventory.node_sources.reverse(),r=>r.steps[0].review.geometry.node_sources[0].node_transform.normal_matrix[0][0]++]){const r=structuredClone(report);mutate(r);assert.throws(()=>decodeMeshBatchReview(r,source,report.glb_sha256,report.mappings));}"""
        out=subprocess.run([node,'--input-type=module','-e',script],input=json.dumps(dict(source=source,report=report)),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3])
        self.assertEqual(out.returncode,0,out.stderr)
        model_mesh_batch.apply(p,*args,review_key=report['review_key']);self.assertEqual(len(p.undo_stack),len(before[1])+1)
        p.undo();self.assertEqual(p._document(),before[0]);p.redo();p.save()
        with patch.object(ProjectService,'_model_source',side_effect=p._model_source):
            reopened=ProjectService.open(p.root);self.assertEqual(reopened.read_model_replacement(asset,reopened.model_overrides[asset]),candidate)
        out=build_project(p)
        with zipfile.ZipFile(out['path']) as package:
            manifest=tomllib.loads(package.read('manifest.toml').decode());entry=manifest['disc_relocation'][0]
            archive=_archive(decode_relocation_package(package.read(entry['file']),entry['sha256'])['replacement'])
        carrier=archive.read_entry(archive.entry(1));d=parse_scene_assets(carrier,1).descriptors[1]
        pack,_=decompress_lzs(carrier[d.data_offset:],d.size);start,_=_pack_ranges(pack)[0]
        self.assertEqual(pack[start:start+len(candidate)],candidate)


if __name__=='__main__':unittest.main()
