"""Native unresolved references stay visible and inspection is immutable."""
from copy import deepcopy
from pathlib import Path
import os,tempfile,unittest
from importer.pipeline import import_scene
from sdk.project import ProjectService,ProjectError
from sdk.asset_references import source_key
from sdk.model_resolution import inspect

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'Private Retail disc required')
class ModelResolution(unittest.TestCase):
    def test_native_initial_references_npc_independence_and_stale_refusal(self):
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'],'taiku2'),os.environ['LEGAIA_DISC_BIN'])
            before=deepcopy((p._document(),p.undo_stack,p.redo_stack,p.imports));key=source_key(p)
            report=inspect(p,p.active_scene,key)
            self.assertEqual(report['counts']['retail_unresolved'],6);self.assertEqual(report['counts']['current_unresolved'],6)
            self.assertEqual(len(report['rows']),6)
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack,p.imports),before)
            for row in report['rows']:
                self.assertEqual(row['retail'],row['current']);self.assertIsNone(row['retail']['asset_id'])
                self.assertGreaterEqual(row['retail']['slot_index'],47)
            donor=report['rows'][0]['entity_id']
            p.command(dict(type='create_actor_draft',donor_entity_id=donor,name='Unresolved donor probe',position=dict(x=128,z=256)))
            with self.assertRaises(ProjectError):inspect(p,p.active_scene,key)
            fresh=inspect(p,p.active_scene,source_key(p));self.assertEqual(fresh['counts']['npc_drafts'],1)
            npc=next(row for row in fresh['rows'] if row['kind']=='npc');self.assertIsNone(npc['retail']);self.assertEqual(npc['current']['source_actor_id'],donor)
            p.save();self.assertEqual(inspect(ProjectService.open(p.root),p.active_scene,source_key(p)),fresh)
            with self.assertRaises(ProjectError):inspect(p,'scene://taiku',source_key(p))
            p.imports[p.active_scene]['actors'][0]['model_reference']['model_index']^=1
            with self.assertRaisesRegex(ProjectError,'freshly verified'):inspect(p,p.active_scene,source_key(p))

if __name__=='__main__':unittest.main()
