from hashlib import sha256
from pathlib import Path
import tempfile
import unittest
from sdk.project import ProjectService, ProjectError, canonical
from sdk.build import authored_state_key
from sdk.export_history import list_exports, verify_export


class ExportHistoryTests(unittest.TestCase):
    def test_editable_copy_preserves_saved_snapshot(self):
        from sdk.export_snapshot import capture_export_inputs,write_export_inputs
        from sdk.export_history import copy_export_inputs
        with tempfile.TemporaryDirectory() as root:
            project=ProjectService(Path(root));project.save()
            identifier='experimental-drafts-'+'b'*32
            directory=project.root/'Builds'/identifier;directory.mkdir(parents=True)
            key,files=capture_export_inputs(project)
            snapshot=write_export_inputs(directory,key,files)
            report={'schema_version':'legaia.experimental-draft-export.v1',
                    'archive':{},'disc':{'output_sha256':'a'*64,'output_bytes':1,'reopened_prot_verified':True},
                    'input_snapshot':snapshot}
            (directory/'report.json').write_bytes(canonical(report))
            original=(directory/'Inputs/project.legaia.json').read_bytes()
            destination=copy_export_inputs(project,identifier)
            copied=ProjectService.open(destination);copied.name='Review copy';copied.save()
            self.assertEqual((directory/'Inputs/project.legaia.json').read_bytes(),original)
            self.assertEqual(project.name,'Legaia project')
            (directory/'Inputs/project.legaia.json').write_bytes(b'corrupt')
            with self.assertRaises(ProjectError):copy_export_inputs(project,identifier)

    def test_completed_incomplete_and_corrupt_exports(self):
        with tempfile.TemporaryDirectory() as root:
            project=ProjectService(Path(root))
            identifier='experimental-drafts-'+'a'*32
            directory=project.root/'Builds'/identifier
            directory.mkdir(parents=True)
            self.assertEqual(list_exports(project)['exports'][0]['status'],'incomplete_or_invalid')
            payload=b'private disc fixture'
            (directory/'draft.bin').write_bytes(payload)
            report={'schema_version':'legaia.experimental-draft-export.v1',
                'disc':{'output_sha256':sha256(payload).hexdigest(),'output_bytes':len(payload),'reopened_prot_verified':True},
                'archive':{'authored_state_key':authored_state_key(project),'scene_id':'scene://fixture'}}
            (directory/'report.json').write_bytes(canonical(report))
            item=list_exports(project)['exports'][0]
            self.assertEqual(item['status'],'completed')
            self.assertTrue(item['matches_current_inputs'])
            self.assertEqual(item['integrity'],'not_checked')
            self.assertTrue(verify_export(project,identifier)['disc_hash_verified'])
            self.assertFalse(verify_export(project,identifier)['gameplay_verified'])
            (directory/'draft.bin').write_bytes(b'x'*len(payload))
            with self.assertRaisesRegex(ProjectError,'hash differs'):
                verify_export(project,identifier)
            with self.assertRaisesRegex(ProjectError,'identity'):
                verify_export(project,'../outside')
            (directory/'draft.bin').write_bytes(payload)
            report['input_snapshot']={'files':[{'path':'Inputs/../../outside','byte_length':1,'sha256':'bad'}]}
            (directory/'report.json').write_bytes(canonical(report))
            with self.assertRaises(ProjectError):
                verify_export(project,identifier)


if __name__=='__main__':
    unittest.main()
