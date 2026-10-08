"""Complete imported frame snapshots keep rigid ownership and shared composition."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch
import tempfile
import unittest
from importer.core import ImportError
from test_importer_scene_animation import fixture
from sdk.project import ProjectService, ProjectError
from test_model_primitive_workflow import http_server

class AnimationFrameValues(unittest.TestCase):
    def test_complete_ordered_layers_single_composition_no_geometry(self):
        catalog, actor, asset, _ = fixture(bones=2)
        asset['source_record']['object_count'] = 2
        catalog._assets[asset['semantic_id']] = deepcopy(asset)
        source = sha256(catalog._body[8:]).hexdigest()
        overrides = {actor['semantic_id']: {'animation_id':'animation://synthetic/scene-anm/0000',
                     'source_record_sha256':source, 'edits':[{'frame_index':1,'object_index':1,'translation':{'x':-12}}]}}
        held = deepcopy((catalog._body, overrides, actor, asset))
        with patch.object(catalog, 'authored_bank', wraps=catalog.authored_bank) as compose, patch('importer.scene_animation.load_model_preview', side_effect=AssertionError('No geometry for frame snapshots')):
            report = catalog.frame_values(actor, asset, 1, overrides)
            compose.assert_called_once()
        self.assertEqual([r['object_index'] for r in report['effective']], [0,1])
        self.assertEqual([r['translation']['x'] for r in report['retail']], [10,11])
        self.assertEqual([r['translation']['x'] for r in report['effective']], [10,-12])
        self.assertEqual(report['source_record_sha256'], source)
        self.assertEqual(report['effective_record_sha256'], sha256(catalog.authored_bank(overrides)[0][8:]).hexdigest())
        self.assertEqual((catalog._body, overrides, actor, asset), held)
        report['effective'][1]['translation']['x'] = 999
        self.assertEqual(catalog.frame_values(actor, asset, 1, overrides)['effective'][1]['translation']['x'], -12)
        retail = catalog.frame_values(actor, asset, 0)
        self.assertEqual(retail['retail'], retail['effective'])
        self.assertEqual(retail['source_record_sha256'], retail['effective_record_sha256'])

    def test_invalid_frames_and_shared_conflicts_reject(self):
        catalog, actor, asset, _ = fixture()
        for frame in (True,-1,2,0.0,None):
            with self.subTest(frame=frame), self.assertRaises(ImportError):
                catalog.frame_values(actor, asset, frame)
        other = deepcopy(actor); other['semantic_id'] += '-shared'; catalog._actors[other['semantic_id']] = other
        binding = {'animation_id':'animation://synthetic/scene-anm/0000','source_record_sha256':sha256(catalog._body[8:]).hexdigest()}
        overrides = {owner:{**binding,'edits':[{'frame_index':0,'object_index':0,'translation':{'x':x}}]} for owner,x in ((actor['semantic_id'],1),(other['semantic_id'],2))}
        with self.assertRaisesRegex(ImportError,'Conflicting'):
            catalog.frame_values(actor, asset, 0, overrides)

    def test_http_exact_typed_request_and_stale_source_refusal(self):
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            body = {'entity_id':'actor','frame_index':0,'expected_source_key':'a'*64}
            with http_server(project) as (_, post), patch.object(project,'animation_frame_values',return_value={'frame_index':0}) as read:
                for update in ({'frame_index':True},{'entity_id':None},{'extra':1}):
                    self.assertEqual(post('/api/animation-frame-values',{**body,**update})[0],400)
                read.assert_not_called()
                with patch('sdk.scene_preview.source_key',return_value='b'*64):
                    self.assertEqual(post('/api/animation-frame-values',body)[0],400)
                read.assert_not_called()
                with patch('sdk.scene_preview.source_key',side_effect=['a'*64,'b'*64]):
                    self.assertEqual(post('/api/animation-frame-values',body)[0],400)
                read.assert_called_once_with('actor',0);read.reset_mock()
                with patch('sdk.scene_preview.source_key',return_value='a'*64):
                    status,report = post('/api/animation-frame-values',body)
                self.assertEqual(status,200)
                self.assertEqual(report['schema_version'],'legaia.imported-animation-frame.v1')
                self.assertEqual(report['project_source_key'],'a'*64)
                self.assertIs(report['project_changed'],False)
                self.assertIs(report['gameplay_verified'],False)
                read.assert_called_once_with('actor',0)

    def test_project_frame_requires_active_scene_owner_before_disc_work(self):
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            with patch.object(project,'animation_authoring_options',side_effect=AssertionError('No disc work for another scene')):
                with self.assertRaisesRegex(ProjectError,'active scene'):
                    project.animation_frame_values('actor',0)

if __name__ == '__main__': unittest.main()
