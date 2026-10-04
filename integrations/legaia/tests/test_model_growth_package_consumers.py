"""Saved verification and private run staging; no game process is started."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import tomllib
from sdk.build import build_project
from sdk.build_history import verify_build, list_builds
from sdk.run import RunService
from sdk.project import ProjectError
import test_model_growth_normal_build as fixtures


class GrowthPackageConsumers(unittest.TestCase):
    def fixture(self):
        helper=fixtures.ModelGrowthNormalBuildTests();self.addCleanup(helper.doCleanups)
        project,*_=helper.fixture()
        build=build_project(project)
        return project,build

    def test_saved_history_verifies_relocation_inventory_and_tampering(self):
        project,build=self.fixture()
        identifier=Path(build['audit']).parent.name
        before={str(path):path.read_bytes() for path in (project.root/'Builds').rglob('*') if path.is_file()}
        self.assertEqual(list_builds(project)['builds'][0]['status'],'completed')
        verified=verify_build(project,identifier)
        self.assertEqual(verified['report'],build['report']);self.assertFalse(verified['gameplay_verified'])
        self.assertEqual(before,{str(path):path.read_bytes() for path in (project.root/'Builds').rglob('*') if path.is_file()})
        payload=Path(build['package_directory'])/build['relocation_payload']['file']
        data=payload.read_bytes();payload.write_bytes(data[:-1]+bytes([data[-1]^1]))
        with self.assertRaises(ProjectError):verify_build(project,identifier)

    def test_private_staging_retains_exact_package_and_expected_reader_identity(self):
        _,build=self.fixture()
        with tempfile.TemporaryDirectory() as directory,patch('sdk.run.subprocess.Popen') as process:
            run=Path(directory);service=RunService();service._status={}
            service._install_build(run,Path(build['path']),build)
            process.assert_not_called()
            self.assertEqual(service._status['expected_overlay_count'],0)
            self.assertEqual(service._status['expected_relocation_count'],1)
            self.assertEqual(service._status['expected_relocation_sha256'],build['relocation_payload']['sha256'])
            target=run/'mods/installed'/build['package_id']/build['version']/build['relocation_payload']['file']
            self.assertEqual(target.read_bytes(),(Path(build['package_directory'])/build['relocation_payload']['file']).read_bytes())
            state=tomllib.loads((run/'mods/state.toml').read_text())
            self.assertTrue(state['feature'][0]['enabled'])
            self.assertEqual(state['feature'][0]['id'],'placements')

    def test_wrong_descriptor_size_hash_and_mixed_manifest_reject_before_staging(self):
        _,build=self.fixture()
        for change in (dict(size=build['relocation_payload']['size']+1),dict(sha256='0'*64),dict(file='../escape'),dict(size=256*1024*1024+1)):
            with self.subTest(change=change),tempfile.TemporaryDirectory() as directory:
                service=RunService();service._status={};run=Path(directory)
                bad=dict(build,relocation_payload=dict(build['relocation_payload'],**change))
                with self.assertRaises(ProjectError):
                    service._install_build(run,Path(build['path']),bad)
                self.assertFalse((run/'mods/installed').exists())


if __name__=='__main__':unittest.main()
