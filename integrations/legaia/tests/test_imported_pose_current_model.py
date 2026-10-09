"""Imported animation previews compose Current mesh content before posing frames."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
from importer.assets import decode_tmd
from importer.core import ImportError
from sdk.project import ProjectService, ProjectError
from sdk.server import EditorServer
from test_importer_assets import model

class ImportedPoseCurrentModel(unittest.TestCase):
    def test_all_frames_repose_current_geometry_and_leave_project_exact(self):
        original=model();changed=bytearray(original);at=12+struct.unpack_from('<I',original,12)[0];struct.pack_into('<h',changed,at,20)
        geometry=decode_tmd(original);geometry['semantic_id']='asset';binding={'source_sha256':sha256(original).hexdigest(),'asset_sha256':sha256(changed).hexdigest()}
        frames=[{'frame_index':i,'object_transforms':[{'object_index':0,'translation':[3,4,5],'rotation_psx':[0,0,i*1024]}],'vertices':deepcopy(geometry['vertices'])} for i in range(2)]
        animation={'geometry':geometry,'frames':frames,'clip_id':'placement'};held=deepcopy(animation)
        with tempfile.TemporaryDirectory() as directory:
            project=ProjectService(Path(directory));project.model_overrides['asset']=binding;before=deepcopy((project.model_overrides,project.undo_stack,project.redo_stack,project.imports))
            server=EditorServer(('127.0.0.1',0),project)
            try:
                with patch.object(project,'read_model_replacement',return_value=bytes(changed)) as read:
                    result=server.posed_model_preview({'semantic_id':'asset','source_record':{}},deepcopy(animation))
                read.assert_called_once_with('asset',binding)
                self.assertEqual(result['vertices'][0],[20,0,0])
                for row,expected in zip(result['frames'],[[23,4,5],[3,24,5]]):
                    for actual,wanted in zip(row['vertices'][0],expected):self.assertAlmostEqual(actual,wanted)
                self.assertEqual(result['authored_shape'],binding)
                self.assertEqual(animation,held)
                self.assertEqual((project.model_overrides,project.undo_stack,project.redo_stack,project.imports),before)
            finally:server.server_close()

    def test_source_change_during_current_mesh_preparation_refuses(self):
        with tempfile.TemporaryDirectory() as directory:
            project=ProjectService(Path(directory));server=EditorServer(('127.0.0.1',0),project)
            try:
                with patch('sdk.scene_preview.source_key',side_effect=['a'*64,'b'*64]),patch.object(server,'model_preview',return_value={}):
                    with self.assertRaisesRegex(ProjectError,'Project changed'):
                        server.posed_model_preview({}, {'geometry':{},'frames':[]})
            finally:server.server_close()

    def test_unmodified_geometry_and_incompatible_pose_layout(self):
        original=model();geometry=decode_tmd(original);frames=[{'object_transforms':[{'object_index':0,'translation':[1,0,0],'rotation_psx':[0,0,0]}],'vertices':deepcopy(geometry['vertices'])}]
        with tempfile.TemporaryDirectory() as directory:
            project=ProjectService(Path(directory));server=EditorServer(('127.0.0.1',0),project)
            try:
                animation={'geometry':geometry,'frames':frames};held=deepcopy(animation)
                result=server.posed_model_preview({'semantic_id':'asset','source_record':{}},deepcopy(animation))
                self.assertNotIn('authored_shape',result);self.assertEqual(result['frames'],frames);self.assertEqual(animation,held)
                project.model_overrides['asset']={'source_sha256':sha256(original).hexdigest()}
                broken=deepcopy(animation);broken['geometry']['objects'][0]['vertex_count']-=1
                with patch.object(project,'read_model_replacement',return_value=original),self.assertRaises(ImportError):
                    server.posed_model_preview({'semantic_id':'asset','source_record':{}},broken)
            finally:server.server_close()

if __name__=='__main__':unittest.main()
