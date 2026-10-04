"""Reviewed vector allocation commands retain history, base ownership and Build."""
from copy import deepcopy
from hashlib import sha256
import struct,tomllib,unittest,zipfile
from unittest.mock import patch
from importer.core import parse_scene_assets,decompress_lzs,_pack_ranges
from importer.disc_relocation_package import decode_relocation_package
from importer.model_pack_archive import _archive
from importer.model_primitives import inspect_model_primitives
from sdk.project import ProjectService,ProjectError
from sdk import model_vector_allocation,model_face_addition
from sdk.build import build_project
import test_model_growth_normal_build as fixtures
from test_model_primitive_workflow import http_server


class VectorAllocationProjectTests(unittest.TestCase):
    def fixture(self):
        helper=fixtures.ModelGrowthNormalBuildTests();self.addCleanup(helper.doCleanups)
        p,asset,*_=helper.fixture()
        self.enterContext(patch('sdk.model_vector_allocation.source_key',return_value='a'*64))
        return p,asset

    def requests(self):return [dict(object_index=0,kind=kind,vectors=[[100,200,300],[400,500,600]]) for kind in ('vertices','normals')]

    def test_actual_command_history_new_face_save_open_and_normal_build(self):
        p,asset=self.fixture();base=deepcopy(p.model_overrides[asset]['base_binding'])
        source=model_vector_allocation.source(p,asset,'a'*64);requests=self.requests()
        self.assertEqual(source['remaining_vector_budget'],4096)
        state=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack));files=set((p.root/'Authored'/'Models').iterdir())
        report=model_vector_allocation.review(p,asset,requests,source['effective_sha256'],'a'*64)
        self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)
        self.assertEqual(set((p.root/'Authored'/'Models').iterdir()),files)
        self.assertEqual(report['topology']['faces'],source['topology']['faces'])
        self.assertEqual(report['allocation']['growth_bytes'],32)
        with self.assertRaises(ProjectError):p.apply_model_vector_allocations(asset,requests,source['effective_sha256'],'a'*64,'0'*64)
        self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)
        self.assertEqual(set((p.root/'Authored'/'Models').iterdir()),files)
        before=p.read_model_replacement(asset,p.model_overrides[asset])
        p.apply_model_vector_allocations(asset,requests,source['effective_sha256'],'a'*64,report['proposed_sha256'])
        current=p.read_model_replacement(asset,p.model_overrides[asset])
        self.assertEqual(p.model_overrides[asset]['base_binding'],base)
        self.assertEqual(p.model_overrides[asset]['ledger']['schema_version'],'legaia.model-face-addition-ledger.v5')
        p.undo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),before)
        p.redo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),current)
        next_source=model_vector_allocation.source(p,asset,'a'*64)
        self.assertEqual(next_source['allocated_vector_count'],4);self.assertEqual(next_source['remaining_vector_budget'],4092)
        nv=source['objects'][0]['vertex_count'];nn=source['objects'][0]['normal_count']
        p.set_model_vector(asset,0,'normals',nn+1,[2048,0,0],sha256(current).hexdigest())
        current=p.read_model_replacement(asset,p.model_overrides[asset])
        donor=model_face_addition.source(p,asset,'a'*64)['topology']['faces'][0]
        corners=inspect_model_primitives(current)['objects'][0]['primitives'][donor['current_primitive_index']]['corner_count']
        new=[dict(face_id='face://authored/00000000-0000-4000-8000-000000000099',donor_face_id=donor['face_id'],fields=dict(vertices=[nv,nv+1,0,1][:corners]))]
        review=model_face_addition.review(p,asset,new,sha256(current).hexdigest(),'a'*64)
        p.apply_model_face_additions(asset,new,sha256(current).hexdigest(),'a'*64,review['proposed_sha256'])
        final=p.read_model_replacement(asset,p.model_overrides[asset]);saved=deepcopy(p.model_overrides[asset]);p.save()
        with patch.object(ProjectService,'_model_source',side_effect=p._model_source):
            reopened=ProjectService.open(p.root)
            self.assertEqual(reopened.model_overrides[asset],saved);self.assertEqual(reopened.read_model_replacement(asset,saved),final)
        out=build_project(p)
        with zipfile.ZipFile(out['path']) as package:
            manifest=tomllib.loads(package.read('manifest.toml').decode());entry=manifest['disc_relocation'][0]
            decoded=decode_relocation_package(package.read(entry['file']),entry['sha256'])
        archive=_archive(decoded['replacement']);carrier=archive.read_entry(archive.entry(1))
        descriptor=parse_scene_assets(carrier,1).descriptors[1];pack,_=decompress_lzs(carrier[descriptor.data_offset:],descriptor.size)
        start,_=_pack_ranges(pack)[1];self.assertEqual(pack[start:start+len(final)],final)
        self.assertEqual(p.model_overrides[asset],saved)

    def test_HTTP_exact_fields_stale_hashes_and_repeat_apply_preserve_history(self):
        p,asset=self.fixture()
        with http_server(p) as (server,post),patch.object(server,'state',return_value={'applied':True}):
            status,source=post('/api/model-vector-allocation-source',dict(asset_id=asset,source_key='a'*64));self.assertEqual(status,200)
            body=dict(asset_id=asset,source_key='a'*64,expected_sha256=source['effective_sha256'],requests=self.requests())
            state=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack))
            status,report=post('/api/model-vector-allocation-preview',body);self.assertEqual(status,200)
            self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)
            for changes in (dict(source_key='0'*64),dict(expected_sha256='0'*64),dict(requests=[]),
                            dict(requests=self.requests()*2),dict(requests=[dict(object_index=True,kind='vertices',vectors=[[1,2,3]])]),
                            dict(requests=[dict(object_index=0,kind='vertices',vectors=[[True,2,3]])]),
                            dict(requests=[dict(object_index=0,kind='vertices',vectors=[[1,2,3]],padding=1)]),dict(extra=True)):
                self.assertEqual(post('/api/model-vector-allocation-preview',dict(body,**changes))[0],400)
                self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)
            self.assertEqual(post('/api/model-vector-allocation',dict(body,proposed_sha256='0'*64))[0],400)
            self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)
            self.assertEqual(post('/api/model-vector-allocation',dict(body,proposed_sha256=report['proposed_sha256']))[0],200)
            state=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack))
            self.assertEqual(post('/api/model-vector-allocation',dict(body,proposed_sha256=report['proposed_sha256']))[0],400)
            self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)

    def test_first_allocation_wraps_existing_independently_qualified_base(self):
        p,asset=self.fixture()
        base=deepcopy(p.model_overrides[asset]['base_binding']);p.model_overrides[asset]=base
        source=model_vector_allocation.source(p,asset,'a'*64)
        report=model_vector_allocation.review(p,asset,self.requests(),source['effective_sha256'],'a'*64)
        p.apply_model_vector_allocations(asset,self.requests(),source['effective_sha256'],'a'*64,report['proposed_sha256'])
        self.assertEqual(p.model_overrides[asset]['base_binding'],base)
        self.assertEqual(p.model_overrides[asset]['ledger']['operations'][0]['kind'],'allocate_vectors')
        self.assertEqual(model_vector_allocation.source(p,asset,'a'*64)['allocated_vector_count'],4)

    def test_source_change_before_publication_preserves_binding_and_history(self):
        p,asset=self.fixture();source=model_vector_allocation.source(p,asset,'a'*64)
        report=model_vector_allocation.review(p,asset,self.requests(),source['effective_sha256'],'a'*64)
        state=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack))
        with patch('sdk.scene_preview.source_key',side_effect=['a'*64,'0'*64]):
            with self.assertRaises(ProjectError):p.apply_model_vector_allocations(asset,self.requests(),source['effective_sha256'],'a'*64,report['proposed_sha256'])
        self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)

    def test_editor_server_serves_allocation_module(self):
        from urllib.request import urlopen
        p,_=self.fixture()
        with http_server(p) as (server,_):
            with urlopen(f'http://127.0.0.1:{server.server_port}/model-vector-allocation.js',timeout=10) as response:
                self.assertEqual(response.status,200)
                self.assertIn('openModelVectorAllocation',response.read().decode('utf-8'))


if __name__=='__main__':unittest.main()
