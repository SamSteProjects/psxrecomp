"""Retained physical WAV assets remain distinct from historical native targets."""
import base64
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from sdk.audio_input_assets import PREFIX, inspect, inventory
from sdk.audio_sample_sources import source_path
from sdk.project import ProjectError, ProjectService, digest
from sdk.project_assets import assemble, source_key
from test_audio_sample_authoring import wav
from test_project_workflow import synthetic_scene


class AudioInputAssets(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = ProjectService(Path(self.tmp.name))
        scene = synthetic_scene()
        scene['source']['disc_identity'] = 'sha256:' + 'a' * 64
        self.project.import_metadata(scene)
        self.project.import_metadata(json.loads(json.dumps(scene).replace('fixture', 'other')))
        self.content = wav([0] * 28, 32000)
        self.wav_hash = sha256(self.content).hexdigest()
        self.identifier = PREFIX + self.wav_hash
        self.add_receipt('scene://fixture', 0)

    def add_receipt(self, scene, sample):
        row = dict(schema_version='legaia.audio-sample-source.v1', asset_id='audio://legaia/prot/0877',
            source_scene_id=scene, source_record=dict(disc_sha256='a' * 64, iso_file='PROT.DAT',
                prot_entry_index=877, entry_sha256='b' * 64, entry_byte_offset=0,
                entry_size_bytes=32, carrier='standalone-vab',
                pieces=[dict(bank_offset=0, entry_offset=0, size_bytes=32)]),
            bank_sha256='c' * 64, sample_index=sample, source_sample_sha256='d' * 64,
            wav_sha256=self.wav_hash, byte_length=len(self.content), input_wav_rate=32000,
            decoded_frames=28, candidate_sample_sha256='e' * 64, review_key='f' * 64)
        row['receipt_key'] = digest(row)
        self.project.audio_sample_sources[row['receipt_key']] = row
        path = source_path(self.project, row)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.content)
        return row

    def test_historical_graph_targets_are_unavailable_until_catalog_qualified(self):
        from sdk.asset_references import assemble as graph, assemble_project
        self.add_receipt('scene://other', 1)
        self.project.active_scene='scene://fixture'
        empty=dict(source_key=None,records=[],limitations=[])
        report=graph(self.project,empty,self.identifier)
        self.assertEqual(len(report['incoming']),1)
        edge=report['incoming'][0]
        self.assertEqual(edge['kind'],'retained_wav_sample_input')
        self.assertEqual(edge['layer'],'authored')
        self.assertEqual(edge['wav_input_evidence']['relationship'],'historical_capture_target')
        self.assertFalse(next(n for n in report['nodes'] if n['id']==edge['source_id'])['available'])
        catalog=dict(source_key='1'*64,records=[dict(id=edge['source_id'],kind='audio',source_record=dict(sha256='b'*64))],limitations=[])
        qualified=graph(self.project,catalog,self.identifier)
        self.assertTrue(next(n for n in qualified['nodes'] if n['id']==edge['source_id'])['available'])
        catalog['records'][0]['source_record']['sha256']='0'*64
        with self.assertRaises(ProjectError):graph(self.project,catalog,self.identifier)
        shared=assemble_project(self.project,{scene:dict(source_key='1'*64,records=[],limitations=[]) for scene in self.project.imports},self.identifier,{})
        self.assertEqual(len(shared['incoming']),2)
        root=next(n for n in shared['nodes'] if n['id']==self.identifier)
        self.assertEqual(root['scene_ids'],['scene://fixture','scene://other'])
        self.assertTrue(root['available'])

    def test_shared_file_is_one_project_asset_with_exact_scene_variants(self):
        self.add_receipt('scene://other', 1)
        self.add_receipt('scene://fixture', 2)
        before = deepcopy((self.project._document(), self.project.undo_stack, self.project.redo_stack))
        result = assemble(self.project, {})
        assets = [row for row in result['assets'] if row['id'] == self.identifier]
        self.assertEqual(len(assets), 1)
        asset = assets[0]
        self.assertEqual(asset['scene_ids'], ['scene://fixture', 'scene://other'])
        self.assertEqual(asset['kind'], 'audio')
        self.assertEqual(asset['variants'][0]['record'], asset['variants'][1]['record'])
        self.assertTrue(all(v['source_catalog_key'] is None for v in asset['variants']))
        self.assertEqual(asset['variants'][0]['record']['source_record']['sha256'], self.wav_hash)
        self.assertEqual((self.project._document(), self.project.undo_stack, self.project.redo_stack), before)

    def test_inspection_and_download_keep_receipts_and_file_bytes_distinct(self):
        self.add_receipt('scene://other', 1)
        key = source_key(self.project)
        result = inspect(self.project, self.identifier, key)
        self.assertNotIn('wav_base64', result)
        self.assertEqual({row['sample_index'] for row in result['receipts']}, {0, 1})
        self.assertTrue(result['historical_inputs'])
        self.assertFalse(result['project_changed'])
        self.assertFalse(result['gameplay_verified'])
        self.assertEqual(result['runtime_binding'], 'not_asserted')
        result['record']['audio_input']['input_wav_rate'] = 999
        recovered = inspect(self.project, self.identifier, key, include_wav=True)
        self.assertEqual(recovered['record']['audio_input']['input_wav_rate'], 32000)
        self.assertEqual(base64.b64decode(recovered['wav_base64']), self.content)

    def test_missing_changed_files_stale_key_and_foreign_identity_reject(self):
        key = source_key(self.project)
        with self.assertRaises(ProjectError):
            inspect(self.project, self.identifier, 'f' * 64)
        for identifier in (self.identifier + '/sample/0', PREFIX + '0' * 64, 'audio://legaia/prot/0877'):
            with self.subTest(identifier=identifier), self.assertRaises(ProjectError):
                inspect(self.project, identifier, key)
        row = next(iter(self.project.audio_sample_sources.values()))
        path = source_path(self.project, row)
        path.write_bytes(self.content[:-1] + bytes([self.content[-1] ^ 1]))
        with self.assertRaisesRegex(ProjectError, 'hash changed'):
            assemble(self.project, {})
        path.unlink()
        with self.assertRaisesRegex(ProjectError, 'missing or changed size'):
            inspect(self.project, self.identifier, key)

    def test_file_drift_after_first_read_rejects_publication(self):
        from sdk.audio_input_assets import read_source as original
        changed = False
        def mutate_after_read(project, row):
            nonlocal changed
            data = original(project, row)
            if not changed:
                changed = True
                source_path(project, row).write_bytes(data[:-1] + bytes([data[-1] ^ 1]))
            return data
        with patch('sdk.audio_input_assets.read_source', side_effect=mutate_after_read):
            with self.assertRaisesRegex(ProjectError, 'hash changed'):
                assemble(self.project, {})

    def test_receipt_context_must_match_imported_capture_scene_and_disc(self):
        original = next(iter(self.project.audio_sample_sources.values()))
        for change in ('scene', 'disc'):
            row = deepcopy(original)
            row.pop('receipt_key')
            if change == 'scene':
                row['source_scene_id'] = 'scene://missing'
            else:
                row['source_record']['disc_sha256'] = '9' * 64
            row['receipt_key'] = digest(row)
            self.project.audio_sample_sources = {row['receipt_key']: row}
            with self.subTest(change=change), patch('sdk.audio_input_assets.read_source') as read:
                with self.assertRaisesRegex(ProjectError, 'capture'):
                    inventory(self.project)
                read.assert_not_called()

    def test_http_exact_envelopes_readonly_inspection_and_qualified_download(self):
        from sdk.server import EditorServer, EditorHandler
        server = EditorServer(('127.0.0.1', 0), self.project)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        before = deepcopy((self.project._document(), self.project.undo_stack, self.project.redo_stack))
        def post(route, body):
            request = Request('http://127.0.0.1:' + str(server.server_port) + route,
                              data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
            try:
                with urlopen(request) as response:
                    return response.status, json.load(response)
            except HTTPError as error:
                with error:
                    return error.code, json.load(error)
        try:
            args = dict(asset_id=self.identifier, expected_source_key=source_key(self.project))
            with patch.object(EditorHandler, 'log_message'):
                status, result = post('/api/audio-input-inspection', args)
                self.assertEqual(status, 200, result)
                self.assertNotIn('wav_base64', result)
                status, result = post('/api/audio-input-download', args)
                self.assertEqual(status, 200, result)
                self.assertEqual(base64.b64decode(result['wav_base64']), self.content)
                for bad in ({}, {**args, 'include_wav': True}, {**args, 'expected_source_key': '0' * 64}):
                    self.assertEqual(post('/api/audio-input-inspection', bad)[0], 400)
                source_path(self.project, next(iter(self.project.audio_sample_sources.values()))).unlink()
                self.assertEqual(post('/api/audio-input-download', args)[0], 400)
            self.assertEqual((self.project._document(), self.project.undo_stack, self.project.redo_stack), before)
        finally:
            server.shutdown()
            thread.join(3)
            server.server_close()


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'), 'Retail disc not configured')
class RetailAudioInputAssets(unittest.TestCase):
    from test_audio_sample_sources import WavInputs as _base
    setUpClass = classmethod(_base.setUpClass.__func__)
    setUp = _base.setUp
    tearDown = _base.tearDown
    args = _base.args

    def test_current_native_binding_is_separate_from_historical_receipt_and_clears(self):
        from sdk.audio_sample_sources import review as retain_review
        from sdk.audio_sample_authoring import review as sample_review
        from sdk.audio_authoring import source_key as authoring_key
        from sdk.audio_composition import read_entry
        from sdk.asset_references import assemble as graph
        from sdk.resources import refresh_resource_catalog
        args,content=self.args()
        retained=retain_review(self.project,**args)
        self.project.command(dict(type='retain_audio_sample_source',**args,review_key=retained['review_key']))
        receipt=next(iter(self.project.audio_sample_sources.values()))
        identifier=PREFIX+sha256(content).hexdigest()
        metadata=inspect(self.project,identifier,source_key(self.project))
        self.assertEqual(metadata['current_bindings'],[])
        apply=dict(asset_id=self.identifier,expected_entry_sha256=self.entry_hash,sample_index=0,
                   expected_authoring_key=authoring_key(self.project),receipt_key=receipt['receipt_key'])
        proposal=sample_review(self.project,operation='apply',**apply)
        self.project.command(dict(type='set_audio_sample_wav',**apply,review_key=proposal['review_key']))
        before=deepcopy((self.project._document(),self.project.undo_stack,self.project.redo_stack))
        report=inspect(self.project,identifier,source_key(self.project))
        binding=report['current_bindings'][0]
        current=read_entry(self.project,self.identifier)
        at,size=binding['sample_entry_byte_offset'],binding['sample_size_bytes']
        self.assertEqual(binding['current_entry_sha256'],sha256(current).hexdigest())
        self.assertEqual(binding['current_sample_sha256'],sha256(current[at:at+size]).hexdigest())
        self.assertEqual(binding['current_sample_sha256'],receipt['candidate_sample_sha256'])
        self.assertEqual(binding['binding_scene_id'],self.project.active_scene)
        self.assertEqual(binding['capture_scene_id'],receipt['source_scene_id'])
        self.assertEqual(binding['binding_sha256'],digest(self.project.audio_sample_overrides[self.identifier]))
        refs=graph(self.project,refresh_resource_catalog(self.project),identifier)
        self.assertEqual({e['kind'] for e in refs['incoming']},{'retained_wav_sample_input','current_native_sample_wav_binding'})
        effective=next(e for e in refs['incoming'] if e['kind']=='current_native_sample_wav_binding')
        self.assertEqual(effective['layer'],'effective')
        self.assertEqual(effective['current_wav_binding_evidence'],binding)
        self.assertEqual(effective['runtime_binding'],'not_asserted')
        self.assertEqual((self.project._document(),self.project.undo_stack,self.project.redo_stack),before)
        self.project.save()
        reopened=ProjectService.open(self.project.root)
        self.assertEqual(inspect(reopened,identifier,source_key(reopened))['current_bindings'],[binding])
        clear=dict(asset_id=self.identifier,expected_entry_sha256=self.entry_hash,sample_index=0,
                   expected_authoring_key=authoring_key(self.project))
        proposal=sample_review(self.project,operation='clear',**clear)
        self.project.command(dict(type='clear_audio_sample_wav',**clear,review_key=proposal['review_key']))
        self.assertEqual(inspect(self.project,identifier,source_key(self.project))['current_bindings'],[])
        self.assertEqual(len(inspect(self.project,identifier,source_key(self.project))['receipts']),1)
        self.project.undo()
        self.assertEqual(inspect(self.project,identifier,source_key(self.project))['current_bindings'],[binding])
        self.project.redo()
        self.assertEqual(inspect(self.project,identifier,source_key(self.project))['current_bindings'],[])

    def test_retained_retail_wav_is_qualified_readonly_asset_and_recovers_exact_input(self):
        from sdk.audio_sample_sources import review
        from sdk.audio_authoring import source_key as authoring_key
        args, content = self.args()
        proposal = review(self.project, **args)
        self.project.command(dict(type='retain_audio_sample_source', **args, review_key=proposal['review_key']))
        key = source_key(self.project)
        retained_authoring_key = authoring_key(self.project)
        before = deepcopy((self.project._document(), self.project.undo_stack, self.project.redo_stack))
        identifier = PREFIX + sha256(content).hexdigest()
        asset = next(row for row in assemble(self.project, {})['assets'] if row['id'] == identifier)
        self.assertEqual(asset['scene_ids'], [self.project.active_scene])
        result = inspect(self.project, identifier, key, include_wav=True)
        self.assertEqual(base64.b64decode(result['wav_base64']), content)
        self.assertEqual(result['receipts'][0]['asset_id'], self.identifier)
        self.assertEqual(result['receipts'][0]['source_scene_id'], self.project.active_scene)
        self.assertEqual(result['receipts'][0]['source_record']['entry_sha256'], self.entry_hash)
        self.assertEqual((self.project._document(), self.project.undo_stack, self.project.redo_stack), before)
        self.assertEqual(authoring_key(self.project), retained_authoring_key)


if __name__ == '__main__':
    unittest.main()
