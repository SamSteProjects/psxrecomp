from copy import deepcopy
from unittest.mock import patch
import unittest
from sdk.project import ProjectError
from sdk.npc_donor_script import inspect
from test_draft_repeat import DraftRepeatTests
class DonorScriptTests(unittest.TestCase):
    def setUp(self):DraftRepeatTests.setUp(self);self.p.disc_path='private-disc.bin'
    def test_retail_only_binding_source_change_and_no_mutation(self):
        before=deepcopy((self.p.actor_drafts,self.p.imports,self.p.overrides,self.p.undo_stack));donor=self.doc['actors'][0];raw=dict(schema_version='legaia.actor-script-inspection.v1',read_only=True,actor_semantic_id=donor['semantic_id'],source_record=deepcopy(donor['source_record']),instructions=[],dialogues=[])
        with patch('importer.script_inspection.inspect_actor_script',return_value=raw) as load:
            report=inspect(self.p,self.original);self.assertEqual(report['inspection'],raw);self.assertFalse(report['generated_code']);self.assertEqual(report['runtime_binding'],'not_asserted');self.assertEqual(load.call_args.args[2],donor)
        report['draft']['name']='Detached';self.assertEqual((self.p.actor_drafts,self.p.imports,self.p.overrides,self.p.undo_stack),before)
        with patch('importer.script_inspection.inspect_actor_script',side_effect=lambda *args:(self.p.command(dict(type='rename_actor_draft',entity_id=self.original,name='Changed')) or raw)):
            with self.assertRaisesRegex(ProjectError,'changed during'):inspect(self.p,self.original)
    def test_unknown_other_scene_and_missing_disc_reject(self):
        with self.assertRaises(ProjectError):inspect(self.p,'missing')
        self.p.active_scene='scene://other'
        with self.assertRaises(ProjectError):inspect(self.p,self.original)
        self.p.active_scene=self.doc['scene']['semantic_id'];self.p.disc_path=None
        with self.assertRaises(ProjectError):inspect(self.p,self.original)
if __name__=='__main__':unittest.main()
