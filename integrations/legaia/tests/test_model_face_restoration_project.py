"""Stable restoration uses actual reviewed project/HTTP commands and normal Build."""
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
import test_model_face_post_addition_removal_project as fixtures
from test_model_primitive_workflow import http_server


class RestorationProjectTests(unittest.TestCase):
    def fixture(self):
        helper=fixtures.AddedRemovalProjectTests();self.addCleanup(helper.doCleanups)
        p,asset=helper.fixture()
        return helper,p,asset

    def test_reviewed_restore_history_content_save_open_and_build(self):
        helper,p,asset=self.fixture();before,removed=helper.remove(p,asset,0)
        current=p.read_model_replacement(asset,p.model_overrides[asset]);binding=deepcopy(p.model_overrides[asset])
        source=model_face_removal.source(p,asset,'a'*64)
        self.assertEqual(source['schema_version'],'legaia.model-face-removal-source.v4')
        record=source['restorable_faces'][0]
        self.assertEqual(record['face']['face_id'],removed['removed_face_ids'][0])
        self.assertNotIn('packet',record)
        selections=[dict(face_id=record['face']['face_id'])]
        state=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack))
        report=model_face_removal.review(p,asset,selections,sha256(current).hexdigest(),'a'*64,restore=True)
        self.assertEqual(report['schema_version'],'legaia.model-face-restoration.v2')
        self.assertEqual(report['restored_face_ids'],removed['removed_face_ids'])
        self.assertNotIn('_binding',report);self.assertNotIn('_effective',report)
        self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)
        with self.assertRaises(ProjectError):p.apply_model_face_removal(asset,selections,sha256(current).hexdigest(),'a'*64,'0'*64,restore=True)
        self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)
        p.apply_model_face_removal(asset,selections,sha256(current).hexdigest(),'a'*64,report['proposed_sha256'],restore=True)
        restored=p.read_model_replacement(asset,p.model_overrides[asset])
        self.assertEqual(p.model_overrides[asset]['base_binding'],binding['base_binding'])
        p.undo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),current)
        p.redo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),restored)
        p.set_model_vector(asset,0,'vertices',0,[49,13,-8],sha256(restored).hexdigest())
        final=p.read_model_replacement(asset,p.model_overrides[asset]);saved=deepcopy(p.model_overrides[asset]);p.save()
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

    def test_authored_HTTP_restoration_rejects_stale_and_injected_requests(self):
        helper,p,asset=self.fixture()
        source=model_face_removal.source(p,asset,'a'*64)
        authored=next(row for row in source['face_topology'] if row['origin']=='authored')
        helper.remove(p,asset,authored['current_primitive_index'])
        with http_server(p) as (server,post),patch.object(server,'state',return_value={'applied':True}):
            status,source=post('/api/model-face-removal-source',dict(asset_id=asset,source_key='a'*64));self.assertEqual(status,200)
            body=dict(asset_id=asset,source_key='a'*64,expected_sha256=source['effective_sha256'],selections=[dict(face_id=authored['face_id'])])
            state=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack))
            status,report=post('/api/model-face-restoration-preview',body);self.assertEqual(status,200)
            self.assertEqual(report['restored_face_ids'],[authored['face_id']])
            for changes in (dict(expected_sha256='0'*64),dict(source_key='0'*64),dict(selections=[dict(face_id='missing')]),
                            dict(selections=body['selections']*2),dict(selections=[dict(face_id=authored['face_id'],packet_hex='00')])):
                self.assertEqual(post('/api/model-face-restoration-preview',dict(body,**changes))[0],400)
                self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)
            self.assertEqual(post('/api/model-face-restoration',dict(body,proposed_sha256='0'*64))[0],400)
            self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)
            self.assertEqual(post('/api/model-face-restoration',dict(body,proposed_sha256=report['proposed_sha256']))[0],200)
            state=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack))
            self.assertEqual(post('/api/model-face-restoration',dict(body,proposed_sha256=report['proposed_sha256']))[0],400)
            self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)


if __name__=='__main__':unittest.main()
