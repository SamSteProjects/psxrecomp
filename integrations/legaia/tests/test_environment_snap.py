from copy import deepcopy
from pathlib import Path
import struct,tempfile,unittest
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.environment_layout import review,apply
from test_environment_group import SCENE,IDS,source_map
from test_project_workflow import synthetic_scene

class EnvironmentSnapTests(unittest.TestCase):
    def test_signed_half_snap_single_axis_and_history(self):
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.import_metadata(synthetic_scene());source=bytearray(source_map());struct.pack_into('<h',source,4*32,-320)
            with patch.object(ProjectService,'_environment_source',return_value=bytes(source)):
                held=deepcopy(p.overrides);depth=len(p.undo_stack);op=dict(kind='snap',axes=['x'],spacing=256);r=review(p,SCENE,IDS,op)
                self.assertEqual([t['proposed'] for t in r['targets']],[dict(x=-256,z=162),dict(x=0,z=290)]);self.assertEqual(p.overrides,held)
                apply(p,dict(type='apply_environment_layout',entity_id=SCENE,entity_ids=IDS,operation=op,review_key=r['review_key']));self.assertEqual(len(p.undo_stack),depth+1)
                p.undo();self.assertEqual(p.overrides,held)
                for bad in [dict(kind='snap',axes=a,spacing=s) for a,s in [([],128),(['z','x'],128),(['x','x'],128),(['y'],128),(['x'],True),(['x'],0),(['x'],4097),(['x'],1.5)]]:
                    with self.assertRaises(ProjectError):review(p,SCENE,IDS,bad)

    def test_offset_overflow_refuses_complete_group(self):
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.import_metadata(synthetic_scene());source=bytearray(source_map());struct.pack_into('<h',source,4*32,32767)
            held=deepcopy((p.overrides,p.undo_stack,p.redo_stack))
            with patch.object(ProjectService,'_environment_source',return_value=bytes(source)):
                with self.assertRaises(ProjectError):review(p,SCENE,IDS,dict(kind='snap',axes=['x'],spacing=256))
            self.assertEqual((p.overrides,p.undo_stack,p.redo_stack),held)
