"""Reviewed removals retain the added-model ledger through project and Build."""
from copy import deepcopy
from hashlib import sha256
import tomllib,unittest,zipfile
from unittest.mock import patch
from importer.core import parse_scene_assets,decompress_lzs,_pack_ranges
from importer.disc_relocation_package import decode_relocation_package
from importer.model_pack_archive import _archive
from sdk.project import ProjectService,ProjectError
from sdk import model_face_removal
from sdk.build import build_project
import test_model_growth_normal_build as fixtures
from test_model_primitive_workflow import http_server


class AddedRemovalProjectTests(unittest.TestCase):
    def fixture(self):
        helper=fixtures.ModelGrowthNormalBuildTests();self.addCleanup(helper.doCleanups)
        p,asset,*_=helper.fixture()
        self.enterContext(patch('sdk.model_face_removal.source_key',return_value='a'*64))
        return p,asset

    def remove(self,p,asset,index):
        current=p.read_model_replacement(asset,p.model_overrides[asset]);selections=[dict(object_index=0,primitive_index=index)]
        report=model_face_removal.review(p,asset,selections,sha256(current).hexdigest(),'a'*64)
        p.apply_model_face_removal(asset,selections,sha256(current).hexdigest(),'a'*64,report['proposed_sha256'])
        return current,report

    def test_history_save_content_and_normal_build_keep_ledger(self):
        p,asset=self.fixture();base=deepcopy(p.model_overrides[asset]['base_binding'])
        before,report=self.remove(p,asset,0)
        self.assertEqual(report['schema_version'],'legaia.model-face-removal.v2')
        self.assertNotIn('_binding',report);self.assertNotIn('_effective',report)
        current=p.read_model_replacement(asset,p.model_overrides[asset])
        self.assertEqual(p.model_overrides[asset]['ledger']['schema_version'],'legaia.model-face-addition-ledger.v3')
        self.assertEqual(p.model_overrides[asset]['base_binding'],base)
        p.undo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),before)
        p.redo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),current)
        p.set_model_vector(asset,0,'vertices',0,[17,23,-5],sha256(current).hexdigest())
        final=p.read_model_replacement(asset,p.model_overrides[asset]);saved=deepcopy(p.model_overrides[asset])
        self.assertEqual(model_face_removal.source(p,asset,'a'*64)['schema_version'],'legaia.model-face-removal-source.v3')
        p.save()
        with patch.object(ProjectService,'_model_source',side_effect=p._model_source):
            reopened=ProjectService.open(p.root)
            self.assertEqual(reopened.model_overrides[asset],saved)
            self.assertEqual(reopened.read_model_replacement(asset,saved),final)
        build=build_project(p)
        with zipfile.ZipFile(build['path']) as package:
            manifest=tomllib.loads(package.read('manifest.toml').decode());entry=manifest['disc_relocation'][0]
            decoded=decode_relocation_package(package.read(entry['file']),entry['sha256'])
        archive=_archive(decoded['replacement']);carrier=archive.read_entry(archive.entry(1))
        descriptor=parse_scene_assets(carrier,1).descriptors[1];pack,_=decompress_lzs(carrier[descriptor.data_offset:],descriptor.size)
        start,_=_pack_ranges(pack)[1];self.assertEqual(pack[start:start+len(final)],final)
        self.assertEqual(p.model_overrides[asset],saved)

    def test_authored_removal_HTTP_and_stale_apply_reject_transactionally(self):
        p,asset=self.fixture()
        with http_server(p) as (server,post),patch.object(server,'state',return_value={'applied':True}):
            status,source=post('/api/model-face-removal-source',dict(asset_id=asset,source_key='a'*64));self.assertEqual(status,200)
            added=next(row for row in source['face_topology'] if row['origin']=='authored')
            body=dict(asset_id=asset,source_key='a'*64,expected_sha256=source['effective_sha256'],selections=[dict(object_index=0,primitive_index=added['current_primitive_index'])])
            state=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack))
            status,report=post('/api/model-face-removal-preview',body);self.assertEqual(status,200)
            self.assertEqual(report['removed_face_ids'],[added['face_id']])
            self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)
            self.assertEqual(post('/api/model-face-removal',dict(body,proposed_sha256='0'*64))[0],400)
            self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)
            self.assertEqual(post('/api/model-face-removal',dict(body,proposed_sha256=report['proposed_sha256']))[0],200)
            state=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack))
            self.assertEqual(post('/api/model-face-removal',dict(body,proposed_sha256=report['proposed_sha256']))[0],400)
            self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)
        source=model_face_removal.source(p,asset,'a'*64)
        self.assertEqual(source['removed_face_ids'],[added['face_id']]);self.assertFalse(source['restoration_available'])
        self.assertFalse(any(row['origin']=='authored' for row in source['face_topology']))
        current=p.read_model_replacement(asset,p.model_overrides[asset])
        noop=model_face_removal.review(p,asset,[],sha256(current).hexdigest(),'a'*64)
        p.apply_model_face_removal(asset,[],sha256(current).hexdigest(),'a'*64,noop['proposed_sha256'])
        self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)
        with self.assertRaises(ProjectError):model_face_removal.review(p,asset,[],sha256(current).hexdigest(),'a'*64,restore=True)


if __name__=='__main__':unittest.main()
