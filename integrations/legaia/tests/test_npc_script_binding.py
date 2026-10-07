from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from sdk.project import ProjectService, ProjectError
from sdk.npc_script_binding import snapshots, FAMILIES
from test_project_workflow import synthetic_scene

class NpcScriptBinding(unittest.TestCase):
    def test_detached_metadata_without_retail_reads_or_history(self):
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.import_metadata(synthetic_scene())
            p.command(dict(type='create_actor_draft',donor_entity_id='scene://fixture/actors/man-p1/0001',name='NPC',position=dict(x=128,z=256)))
            identifier=next(iter(p.actor_drafts));before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
            row=snapshots(p)[identifier]
            self.assertEqual(row['source_script_id'],'script://fixture/actors/man-p1/0001')
            self.assertEqual(row['authored_counts'],{family:0 for family in FAMILIES})
            self.assertEqual(row['runtime_binding'],'not_asserted')
            self.assertEqual(before,(p._document(),p.undo_stack,p.redo_stack))
            row['authored_counts']['dialogue']=999;self.assertEqual(snapshots(p)[identifier]['authored_counts']['dialogue'],0)
            old=snapshots(p)[identifier]['authored_draft_sha256'];p.command(dict(type='rename_actor_draft',entity_id=identifier,name='Renamed'))
            self.assertNotEqual(old,snapshots(p)[identifier]['authored_draft_sha256'])
            p.actor_drafts[identifier]['effect_colors']=dict(donor_entity_id='scene://wrong',entries={})
            with self.assertRaises(ProjectError):snapshots(p)
