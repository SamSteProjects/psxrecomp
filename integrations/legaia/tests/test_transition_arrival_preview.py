from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from sdk.project import ProjectError
from sdk.scene_preview import source_key
from sdk.transition_arrival import inspect
import test_transition_resource_workflow as workflow
from test_importer_script_catalog import catalog


class TransitionArrivalPreview(unittest.TestCase):
    def test_destination_binding_and_read_only_comparison(self):
        helper=workflow.TransitionResourceWorkflow()
        with tempfile.TemporaryDirectory() as raw:
            p=helper.project(raw)
            disc=Path(raw)/'disc.bin';disc.write_bytes(bytes(512));p.disc_path=str(disc)
            destination=deepcopy(p.imports[p.active_scene])
            destination['scene']={'semantic_id':'scene://town02','name':'town02'}
            p.imports['scene://town02']=destination
            source=catalog(b'\x3f\0\0\x06town02\x01\x82\x03')
            before=deepcopy((p._document(),p.undo_stack,p.redo_stack,p.active_scene))
            with helper.discovery(p,source),patch('sdk.transition_arrival._verify') as verify:
                report=inspect(p,'transition://fixture/actors/man-p1/0001/0005',source_key(p))
                verify.assert_called_once_with(p,destination)
            self.assertEqual(report['destination_scene_id'],'scene://town02')
            self.assertEqual(report['resource']['arrival_layers']['effective']['x'],192)
            self.assertFalse(report['height_known'])
            self.assertFalse(report['runtime_verified'])
            self.assertEqual(before,(p._document(),p.undo_stack,p.redo_stack,p.active_scene))
            with helper.discovery(p,source),patch('sdk.transition_arrival._verify',side_effect=ProjectError('Destination source changed')):
                with self.assertRaisesRegex(ProjectError,'Destination source changed'):
                    inspect(p,report['asset_id'],source_key(p))
            self.assertEqual(before,(p._document(),p.undo_stack,p.redo_stack,p.active_scene))
            with helper.discovery(p,source),patch('sdk.transition_arrival._verify'):
                with self.assertRaisesRegex(ProjectError,'one verified source resource'):
                    inspect(p,'transition://fixture/missing',source_key(p))
            from test_model_primitive_workflow import http_server
            with helper.discovery(p,source),patch('sdk.transition_arrival._verify'),http_server(p) as (_,post):
                body={'asset_id':report['asset_id'],'source_key':source_key(p)}
                status,value=post('/api/transition-arrival-preview',body)
                self.assertEqual(status,200);self.assertEqual(value['destination_scene_id'],'scene://town02')
                for invalid in ({**body,'runtime_position':{}},{'asset_id':report['asset_id']},{**body,'source_key':'0'*64}):
                    self.assertEqual(post('/api/transition-arrival-preview',invalid)[0],400)
            with self.assertRaisesRegex(ProjectError,'source changed'):
                inspect(p,report['asset_id'],'0'*64)
            p.mode='live'
            with self.assertRaisesRegex(ProjectError,'Edit mode'):
                inspect(p,report['asset_id'],source_key(p))
            p.mode='edit';del p.imports['scene://town02']
            with helper.discovery(p,source):
                with self.assertRaisesRegex(ProjectError,'Import the named destination'):
                    inspect(p,report['asset_id'],source_key(p))
