"""One atomic GLB import can preserve its distinct primitive group boundaries."""
from copy import deepcopy
import base64,tomllib,unittest,zipfile
import json,shutil,subprocess
from pathlib import Path
from unittest.mock import patch
from importer.model_mesh_append import decode_append_mesh
from importer.core import ImportError,_pack_ranges,parse_scene_assets,decompress_lzs
from importer.disc_relocation_package import decode_relocation_package
from importer.model_pack_archive import _archive
from sdk import model_mesh_append,model_object_allocation
from sdk.project import ProjectService,ProjectError
from sdk.build import build_project
from sdk.scene_preview import preview_shape_instances
from importer.assets import decode_tmd
from importer.model_authoring import preview_model_shape
from test_model_object_ledger import clone_request
from test_model_primitive_workflow import http_server
import test_model_mesh_append as fixtures
import test_model_mesh_append_normals as normal_fixtures


def mesh():
    def duplicate(doc):
        doc['meshes'][0]['primitives'].append(deepcopy(doc['meshes'][0]['primitives'][0]))
        # Each primitive has independent attributes, sharing its POSITION accessor.
        doc['meshes'][0]['primitives'][1]['attributes'].pop('TEXCOORD_0')
    return fixtures.glb(duplicate,uvs=[[0,0],[1,0],[0,1],[1,1]])


class MeshPrimitiveGroupTests(unittest.TestCase):
    def qualify(self,source,report):
        node=shutil.which('node')
        if not node:self.skipTest('Node is required for browser qualification')
        script="""import {decodeMeshAppendSource,decodeMeshAppendReview} from './integrations/legaia/editor/model-mesh-append.js';let data='';for await(const chunk of process.stdin)data+=chunk;const {source,report}=JSON.parse(data),s=decodeMeshAppendSource(source,source.asset_id,source.project_source_key),replace=report.allocation_mode==='replace_group';const check=r=>decodeMeshAppendReview(r,s,report.donor_face_id,report.geometry.glb_sha256,true,replace,true);check(report);for(const edit of [r=>r.geometry.primitive_ranges[1].first_triangle--,r=>r.geometry.primitive_ranges[1].triangle_count--,r=>r.geometry.primitive_ranges[0].source_mode=1,r=>r.group_requests.reverse(),r=>r.group_requests[1].group_id=r.group_requests[0].group_id,r=>r.topology.allocated_groups.at(-1).origin_group_index++,r=>r.topology.allocated_group_count--,r=>r.topology.faces.at(-1).group_index--,r=>r.preview.triangle_uvs[0][0][0]++,r=>r.preserve_primitives=false]){const r=structuredClone(report);edit(r);let rejected=false;try{check(r);}catch{rejected=true;}if(!rejected)throw Error('Forged primitive group accepted');}let rejected=false;try{decodeMeshAppendReview(report,s,report.donor_face_id,report.geometry.glb_sha256,true,replace,false);}catch{rejected=true;}if(!rejected)throw Error('Wrong preservation choice accepted');"""
        result=subprocess.run([node,'--input-type=module','-e',script],input=json.dumps(dict(source=source,report=report)),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3])
        self.assertEqual(result.returncode,0,result.stderr)

    def fixture(self):
        h=fixtures.MeshAppendTests();self.addCleanup(h.doCleanups)
        return h.fixture()

    def test_geometry_preserves_contiguous_ranges_and_shared_positions(self):
        report=decode_append_mesh(mesh(),preserve_primitives=True)
        self.assertEqual(report['schema_version'],'legaia.model-mesh-append-geometry.v5')
        self.assertEqual(report['primitive_ranges'],[dict(primitive_index=0,first_triangle=0,triangle_count=2,source_mode=4),dict(primitive_index=1,first_triangle=2,triangle_count=2,source_mode=4)])
        self.assertEqual(len(report['vertices']),4)
        self.assertEqual(report['triangles'][:2],report['triangles'][2:])
        self.assertTrue(all(row is None for row in report['triangle_uvs'][2:]))
        self.assertNotIn('primitive_ranges',decode_append_mesh(mesh()))
        for choice in (1,None,'true'):
            with self.assertRaises(ImportError):decode_append_mesh(mesh(),preserve_primitives=choice)
        def too_many(doc):doc['meshes'][0]['primitives']*=65
        with self.assertRaises(ImportError):decode_append_mesh(fixtures.glb(too_many),preserve_primitives=True)

    def test_browser_qualifies_mixed_imported_and_inherited_normal_groups(self):
        h=normal_fixtures.MeshAppendNormalTests();self.addCleanup(h.doCleanups)
        p,asset,donor=h.fixture(0x15)
        def duplicate(doc):
            second=deepcopy(doc['meshes'][0]['primitives'][0]);second['attributes'].pop('NORMAL');doc['meshes'][0]['primitives'].append(second)
        content=fixtures.glb(duplicate,normals=[[0,1,0],[1,0,0],[0,0,1],[0,1,0]])
        source=model_mesh_append.source(p,asset,'a'*64)
        report=model_mesh_append.review(p,asset,content,donor,source['effective_sha256'],'a'*64,new_group=True,preserve_primitives=True)
        self.assertEqual(report['normal_import']['imported_face_count'],2)
        self.assertEqual(len(report['normal_import']['vectors']),3)
        self.assertEqual(report['normal_import']['references'][2:],[None,None])
        self.qualify(source,report)

    def test_one_command_read_only_review_reopen_undo_and_build(self):
        p,asset,donor=self.fixture();source=model_mesh_append.source(p,asset,'a'*64);content=mesh()
        args=(asset,content,donor,source['effective_sha256'],'a'*64)
        state=deepcopy((p._document(),p.undo_stack,p.redo_stack));files=set((p.root/'Authored'/'Models').iterdir())
        candidate,binding,report=model_mesh_append.prepare(p,*args,new_group=True,replace_group=True,preserve_primitives=True)
        self.qualify(source,report)
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack),state)
        self.assertEqual(set((p.root/'Authored'/'Models').iterdir()),files)
        self.assertEqual(report['schema_version'],'legaia.model-mesh-append-review.v7')
        self.assertEqual(len(report['group_requests']),2)
        self.assertEqual([g['faces'] for g in report['group_requests']],[report['additions'][:2],report['additions'][2:]])
        self.assertEqual(report['topology']['allocated_group_count'],2)
        self.assertEqual([g['current_group_index'] for g in report['topology']['allocated_groups']],[0,1])
        self.assertEqual(report['topology']['operation_count'],3)
        self.assertEqual(len(report['removed_face_ids']),2)
        ordinary=model_mesh_append.review(p,*args,new_group=True,replace_group=True)
        self.assertNotEqual(report['review_key'],ordinary['review_key'])
        with self.assertRaises(ProjectError):p.apply_model_mesh_append(*args,report['review_key'],new_group=True,replace_group=True)
        p.apply_model_mesh_append(*args,report['review_key'],new_group=True,replace_group=True,preserve_primitives=True)
        self.assertEqual(len(p.undo_stack),len(state[1])+1)
        self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),candidate)
        self.assertEqual(len(model_mesh_append.source(p,asset,'a'*64)['packet_groups'][0]),2)
        p.undo();self.assertEqual(p.model_overrides,state[0]['model_overrides'])
        p.redo();p.save()
        with patch.object(ProjectService,'_model_source',side_effect=p._model_source):
            reopened=ProjectService.open(p.root);self.assertEqual(reopened.read_model_replacement(asset,reopened.model_overrides[asset]),candidate)
        out=build_project(p)
        with zipfile.ZipFile(out['path']) as package:
            manifest=tomllib.loads(package.read('manifest.toml').decode());entry=manifest['disc_relocation'][0]
            replacement=decode_relocation_package(package.read(entry['file']),entry['sha256'])['replacement']
        archive=_archive(replacement);carrier=archive.read_entry(archive.entry(1));d=parse_scene_assets(carrier,1).descriptors[1]
        pack,_=decompress_lzs(carrier[d.data_offset:],d.size);start,_=_pack_ranges(pack)[0]
        self.assertEqual(pack[start:start+len(candidate)],candidate)

    def test_http_exact_choice_review_and_scene_binding(self):
        p,asset,donor=self.fixture();source=model_mesh_append.source(p,asset,'a'*64)
        body=dict(asset_id=asset,content_base64=base64.b64encode(mesh()).decode(),donor_face_id=donor,expected_sha256=source['effective_sha256'],source_key='a'*64,new_group=True,preserve_primitives=True)
        with http_server(p) as (server,post),patch.object(server,'state',return_value={'applied':True}),patch.object(server,'scene_shape_proposal',side_effect=lambda *args,**kw:args[3]) as scene:
            for changes in (dict(preserve_primitives=1),dict(preserve_primitives='true'),dict(new_group=False)):
                self.assertEqual(post('/api/model-mesh-append-preview',{**body,**changes})[0],400)
            status,report=post('/api/model-mesh-append-preview',body);self.assertEqual(status,200)
            self.qualify(source,report)
            self.assertEqual(len(report['group_requests']),2)
            proposal={**body,'review_key':report['review_key'],'proposed_sha256':report['proposed_sha256'],'entity_id':'one','all_instances':True}
            self.assertEqual(post('/api/model-mesh-append-scene-preview',proposal)[0],200)
            self.assertEqual(scene.call_args.kwargs['prepared_binding']['ledger']['operations'][-1]['kind'],'allocate_groups')
            self.assertEqual(post('/api/model-mesh-append',{**body,'preserve_primitives':False,'review_key':report['review_key']})[0],400)
            self.assertEqual(post('/api/model-mesh-append',{**body,'review_key':report['review_key']})[0],200)
            self.assertEqual(post('/api/model-mesh-append',{**body,'review_key':report['review_key']})[0],400)

    def test_copied_object_v7_preserves_group_ownership_and_scene_continuation(self):
        p,asset,_=self.fixture()
        with patch('sdk.model_object_allocation.source_key',return_value='a'*64):
            source=model_object_allocation.source(p,asset,'a'*64)
            requests=[clone_request(source['topology'],source['object_identities'][0],3000)]
            report=model_object_allocation.review(p,asset,requests,source['effective_sha256'],'a'*64)
            p.apply_model_object_allocations(asset,requests,source['effective_sha256'],'a'*64,report['review_key'])
        source=model_mesh_append.source(p,asset,'a'*64);donor=next(f['face_id'] for f in source['topology']['faces'] if f['object_index']==1)
        candidate,binding,report=model_mesh_append.prepare(p,asset,mesh(),donor,source['effective_sha256'],'a'*64,new_group=True,replace_group=True,preserve_primitives=True)
        self.qualify(source,report)
        self.assertEqual(binding['ledger']['schema_version'],'legaia.model-face-addition-ledger.v7')
        self.assertEqual(report['topology']['objects'],source['topology']['objects'])
        self.assertIsNone(report['topology']['allocated_groups'][0]['current_group_index'])
        self.assertEqual([g['current_group_index'] for g in report['topology']['allocated_groups'][1:]],[0,1])
        current=p.read_model_replacement(asset,p.model_overrides[asset]);base=p._model_source(asset,p.active_scene)
        preview=preview_model_shape(decode_tmd(base),current,p.model_overrides[asset])
        scene=dict(entities=[dict(entity_id='one',asset_id=asset,renderable=True,geometry_key='shared')],assets=[dict(asset_id=asset,geometry_key='shared',preview=preview)])
        baseline=deepcopy(scene);proposed=preview_shape_instances(scene,asset,candidate,binding)
        self.assertEqual(proposed['proposal_assets'][0]['preview']['vertices'],report['preview']['vertices']);self.assertEqual(scene,baseline)


if __name__=='__main__':unittest.main()
