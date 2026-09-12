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


if __name__=='__main__':
    unittest.main()
