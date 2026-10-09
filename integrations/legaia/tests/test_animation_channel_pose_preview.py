"""Private proposed channels pose the shared bank without applying a command."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from sdk.project import ProjectService, ProjectError
from test_importer_scene_animation import fixture
from test_model_primitive_workflow import http_server

class ChannelPosePreview(unittest.TestCase):
    def test_native_proposal_preserves_other_contributions_and_project(self):
        catalog,actor,asset,model=fixture();other=deepcopy(actor);other['semantic_id']+='-shared';catalog._actors[other['semantic_id']]=other
        source=sha256(catalog._body[8:]).hexdigest();binding={'animation_id':'animation://synthetic/scene-anm/0000','source_record_sha256':source}
        proposed={**binding,'edits':[{'frame_index':1,'object_index':0,'translation':{'x':100}}]}
        with tempfile.TemporaryDirectory() as directory:
            project=ProjectService(Path(directory));project.active_scene='scene://synthetic';project.imports[project.active_scene]={'scene':{'name':'synthetic'},'actors':[actor,other],'assets':{'models':[asset]}}
            project.overrides[other['semantic_id']]={'AnimationChannels':{**binding,'edits':[{'frame_index':1,'object_index':0,'translation':{'y':200}}]}}
            held=deepcopy((project.overrides,project.undo_stack,project.redo_stack,project.imports,proposed,catalog._body))
            with patch.object(project,'_validate_animation_override') as validate,patch('importer.scene_animation.load_scene_actor_animation_catalog',return_value=catalog),patch('importer.scene_animation.load_model_preview',return_value=deepcopy(model)):
                preview,returned=project.animation_channels_pose_preview(actor['semantic_id'],proposed)
            validate.assert_called_once_with(actor['semantic_id'],proposed)
            self.assertEqual(preview['frames'][1]['vertices'],[[101,202,3]])
            self.assertEqual(preview['frames'][1]['object_transforms'][0]['translation'],[100,200,0])
            self.assertEqual(preview['representation'],'channel_preview')
            self.assertEqual(preview['proposal'],{'value':proposed,'project_changed':False,'gameplay_verified':False})
            self.assertEqual((project.overrides,project.undo_stack,project.redo_stack,project.imports,proposed,catalog._body),held)
            preview['proposal']['value']['edits'].clear();returned['source_record'].clear()
            self.assertEqual((project.overrides,project.undo_stack,project.redo_stack,project.imports,proposed,catalog._body),held)

    def test_other_scene_refuses_before_source_resolution(self):
        with tempfile.TemporaryDirectory() as directory:
            project=ProjectService(Path(directory))
            with patch.object(project,'_validate_animation_override',side_effect=AssertionError('No source work')):
                with self.assertRaisesRegex(ProjectError,'active scene'):
                    project.animation_channels_pose_preview('other',{})

    def test_http_request_and_before_after_source_guard(self):
        with tempfile.TemporaryDirectory() as directory:
            project=ProjectService(Path(directory));body={'entity_id':'actor','value':{},'expected_source_key':'a'*64}
            candidate={'geometry':{},'frames':[],'clip_id':'placement','proposal':{'value':{},'project_changed':False,'gameplay_verified':False}}
            with http_server(project) as (server,post),patch.object(project,'animation_channels_pose_preview',side_effect=lambda *args:(deepcopy(candidate),{})) as read,patch.object(server,'model_preview',return_value={}):
                for update in ({'entity_id':None},{'value':[]},{'extra':1}):
                    self.assertEqual(post('/api/animation-channels-pose-preview',{**body,**update})[0],400)
                read.assert_not_called()
                with patch('sdk.scene_preview.source_key',return_value='b'*64):
                    self.assertEqual(post('/api/animation-channels-pose-preview',body)[0],400)
                read.assert_not_called()
                with patch('sdk.scene_preview.source_key',side_effect=['a'*64,'b'*64]):
                    self.assertEqual(post('/api/animation-channels-pose-preview',body)[0],400)
                read.assert_called_once_with('actor',{});read.reset_mock()
                with patch('sdk.scene_preview.source_key',return_value='a'*64):
                    status,report=post('/api/animation-channels-pose-preview',body)
                self.assertEqual(status,200);self.assertEqual(report['animation']['clip_id'],'channel-preview')
                self.assertEqual(report['animation']['proposal']['project_source_key'],'a'*64)
                self.assertIs(report['animation']['proposal']['project_changed'],False)
                read.assert_called_once_with('actor',{})

if __name__=='__main__': unittest.main()
