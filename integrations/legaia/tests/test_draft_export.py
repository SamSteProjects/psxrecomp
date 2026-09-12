"""Export completion and source freshness without proprietary disc bytes."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from sdk.project import ProjectService, ProjectError
from sdk.build import authored_state_key
from sdk.draft_build import export_draft_disc


class DraftExportTests(unittest.TestCase):
    def test_report_only_after_unchanged_successful_write(self):
        with tempfile.TemporaryDirectory() as root:
            project=ProjectService(Path(root)/'project')
            audit={'authored_state_key':authored_state_key(project),
                   'source_disc_sha256':'disc','source_prot_sha256':'prot'}
            def writer(*args):
                args[-1].write_bytes(b'fixture')
                return {'reopened_prot_verified':True}
            with patch('sdk.draft_build.prepare_draft_archive',return_value=(b'archive',audit)), \
                 patch('importer.disc_rebuild.write_grown_prot_disc',side_effect=writer):
                destination=Path(root)/'success'
                report=export_draft_disc(project,'draft',destination)
                self.assertTrue((destination/'report.json').is_file())
                self.assertFalse(report['gameplay_verified'])
                self.assertTrue(report['input_snapshot']['readback_verified'])
                restored=ProjectService.open(destination/'Inputs')
                self.assertEqual(restored._document(),project._document())
                with self.assertRaisesRegex(ProjectError,'new output'):
                    export_draft_disc(project,'draft',destination)
            def stale_writer(*args):
                result=writer(*args)
                project.texture_overrides['new']={}
                return result
            with patch('sdk.draft_build.prepare_draft_archive',return_value=(b'archive',audit)), \
                 patch('importer.disc_rebuild.write_grown_prot_disc',side_effect=stale_writer):
                destination=Path(root)/'stale'
                with self.assertRaisesRegex(ProjectError,'changed during'):
                    export_draft_disc(project,'draft',destination)
                self.assertTrue((destination/'draft.bin').exists())
                self.assertFalse((destination/'report.json').exists())

    def test_snapshot_preserves_unsaved_draft_without_saving_source(self):
        from sdk.export_snapshot import capture_export_inputs, write_export_inputs
        from test_project_workflow import synthetic_scene
        with tempfile.TemporaryDirectory() as root:
            project=ProjectService(Path(root)/'project')
            scene=synthetic_scene()
            project.import_metadata(scene)
            project.save()
            saved=(project.root/'project.legaia.json').read_bytes()
            project.command({'type':'create_actor_draft',
                'donor_entity_id':scene['actors'][0]['semantic_id'],
                'position':{'x':128,'z':256},'name':'Deferred NPC'})
            key,files=capture_export_inputs(project)
            directory=Path(root)/'export';directory.mkdir()
            report=write_export_inputs(directory,key,files)
            restored=ProjectService.open(directory/'Inputs')
            self.assertEqual(restored.actor_drafts,project.actor_drafts)
            self.assertEqual(restored.imports,project.imports)
            self.assertTrue(project.dirty)
            self.assertEqual((project.root/'project.legaia.json').read_bytes(),saved)
            self.assertEqual(report['source_authored_state_key'],authored_state_key(project))
            project.undo()
            self.assertFalse(project.actor_drafts)
            self.assertTrue(ProjectService.open(directory/'Inputs').actor_drafts)
            with self.assertRaises(FileExistsError):
                write_export_inputs(directory,key,files)


if __name__=='__main__':
    unittest.main()
