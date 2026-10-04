"""Static parent transforms bake through native delivery without scene parenting."""
from copy import deepcopy
import json,math,shutil,subprocess,tomllib,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
from importer.core import ImportError,_pack_ranges,parse_scene_assets,decompress_lzs
from importer.model_mesh_append import decode_append_mesh,inspect_append_mesh
from importer.model_pack_archive import _archive
from importer.disc_relocation_package import decode_relocation_package
from sdk import model_mesh_append,model_mesh_batch
from sdk.project import ProjectService
from sdk.build import build_project
import test_model_mesh_append as fixtures


def hierarchy():
    def change(doc):
        doc['nodes'][0].update(translation=[5,0,0],rotation=[0,0,math.sin(math.pi/8),math.cos(math.pi/8)])
        doc['nodes'].extend([dict(mesh=0,translation=[200,0,0]),dict(translation=[10,20,30],scale=[2,3,1],children=[0,1])])
        doc['scenes'][0]['nodes']=[2]
    return fixtures.glb(change,normals=[[1,0,0]]*4)


class MeshHierarchyTests(unittest.TestCase):
    def test_composed_shear_positions_normals_and_ancestry(self):
        content=hierarchy();geometry=decode_append_mesh(content)
        self.assertEqual(geometry['vertices'][:4],[[20,-20,30],[-121,-232,30],[161,-232,30],[20,-444,30]])
        normal=[round(3/math.sqrt(13)*4096),round(-2/math.sqrt(13)*4096),0]
        self.assertEqual(geometry['triangle_normals'][0],[normal]*3)
        self.assertEqual([row['node_path'] for row in geometry['node_sources']],[[2,0],[2,1]])
        self.assertEqual(inspect_append_mesh(content)['node_sources'],geometry['node_sources'])
        selected=decode_append_mesh(content,primitive_index=1)
        self.assertEqual(selected['vertices'][0],[410,-20,30])
        self.assertEqual(selected['node_sources'][0]['node_path'],[2,1])

    def test_invalid_forests_reject_before_geometry(self):
        for mutation in (lambda d:d['nodes'][2].update(children=[0,0]),lambda d:d['nodes'][0].update(children=[2]),lambda d:d['nodes'][1].update(children=[0]),lambda d:d['scenes'][0].update(nodes=[2,0]),lambda d:d['nodes'][2].update(children=[True]),lambda d:d['nodes'][2].update(children=[3])):
            # Build the same valid source via fixture changes, then mutate its graph.
            def change(doc):
                doc['nodes']=[dict(mesh=0),dict(mesh=0),dict(children=[0,1])];doc['scenes'][0]['nodes']=[2];mutation(doc)
            with self.assertRaises(ImportError):decode_append_mesh(fixtures.glb(change))

    def test_review_browser_persistence_and_exact_build(self):
        helper=fixtures.MeshAppendTests();self.addCleanup(helper.doCleanups)
        p,asset,donor=helper.fixture();self.enterContext(patch('sdk.model_mesh_batch.source_key',return_value='a'*64))
        source=model_mesh_append.source(p,asset,'a'*64);content=hierarchy()
        mappings=[dict(primitive_index=i,donor_face_id=donor,replace_group=False) for i in range(2)]
        args=(asset,content,mappings,source['effective_sha256'],'a'*64)
        before=deepcopy((p._document(),p.undo_stack,p.redo_stack));candidate,_,report=model_mesh_batch.prepare(p,*args)
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
        script="""import {decodeMeshBatchReview} from './integrations/legaia/editor/model-mesh-batch.js';
import assert from 'node:assert/strict';let text='';for await(const c of process.stdin)text+=c;const {source,report}=JSON.parse(text);
decodeMeshBatchReview(report,source,report.glb_sha256,report.mappings);
for(const mutate of [r=>r.steps[0].review.geometry.node_sources[0].node_path.reverse(),r=>r.steps[0].review.geometry.node_sources[0].node_path=[0],r=>r.inventory.node_sources[0].node_path=[3,0],r=>r.steps[0].review.geometry.node_sources[0].node_transform.normal_matrix[0][0]++]){const r=structuredClone(report);mutate(r);assert.throws(()=>decodeMeshBatchReview(r,source,report.glb_sha256,report.mappings));}"""
        node=shutil.which('node');self.assertIsNotNone(node)
        out=subprocess.run([node,'--input-type=module','-e',script],input=json.dumps(dict(source=source,report=report)),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3]);self.assertEqual(out.returncode,0,out.stderr)
        model_mesh_batch.apply(p,*args,review_key=report['review_key']);self.assertEqual(len(p.undo_stack),len(before[1])+1)
        p.undo();self.assertEqual(p._document(),before[0]);p.redo();p.save()
        with patch.object(ProjectService,'_model_source',side_effect=p._model_source):
            reopened=ProjectService.open(p.root);self.assertEqual(reopened.read_model_replacement(asset,reopened.model_overrides[asset]),candidate)
        out=build_project(p)
        with zipfile.ZipFile(out['path']) as package:
            manifest=tomllib.loads(package.read('manifest.toml').decode());entry=manifest['disc_relocation'][0]
            archive=_archive(decode_relocation_package(package.read(entry['file']),entry['sha256'])['replacement'])
        carrier=archive.read_entry(archive.entry(1));d=parse_scene_assets(carrier,1).descriptors[1]
        pack,_=decompress_lzs(carrier[d.data_offset:],d.size);start,_=_pack_ranges(pack)[0];self.assertEqual(pack[start:start+len(candidate)],candidate)


if __name__=='__main__':unittest.main()
