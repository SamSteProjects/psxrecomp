"""Read-only AssetDB membership and source freshness for binding selection."""
from copy import deepcopy
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from sdk.model_materials import donor_models
from sdk.project import ProjectError


class MaterialDonorCatalogTests(TestCase):
    def fixture(self):
        identifier = 'asset://global/models/0001'
        document = dict(source=dict(disc_identity='disc'), assets=dict(models=[dict(semantic_id=identifier)]))
        records = {identifier: dict(kind='model', layer='imported', disc_identity='disc', name='Imported model')}
        return SimpleNamespace(mode='edit', active_scene='scene://town01', imports={'scene://town01': document},
                               assets=SimpleNamespace(records=records)), identifier

    @patch('sdk.scene_preview.source_key', return_value='a' * 64)
    def test_assetdb_global_identity_and_no_mutation(self, key):
        project, identifier = self.fixture()
        before = deepcopy(project.__dict__)
        result = donor_models(project, 'a' * 64)
        self.assertEqual(result['models'], [dict(asset_id=identifier, label='Imported model')])
        self.assertFalse(result['project_changed'])
        result['models'][0]['label'] = 'changed'
        self.assertEqual(project.__dict__, before)

    @patch('sdk.scene_preview.source_key', return_value='a' * 64)
    def test_unqualified_stale_duplicate_and_budget_rejected(self, key):
        for change in ('stale', 'live', 'missing', 'disc', 'duplicate', 'budget'):
            with self.subTest(change=change):
                project, identifier = self.fixture()
                expected = 'a' * 64
                if change == 'stale': expected = 'b' * 64
                if change == 'live': project.mode = 'live'
                if change == 'missing': project.assets.records.clear()
                if change == 'disc': project.assets.records[identifier]['disc_identity'] = 'other'
                if change == 'duplicate': project.imports[project.active_scene]['assets']['models'] *= 2
                if change == 'budget': project.imports[project.active_scene]['assets']['models'] *= 2049
                with self.assertRaises(ProjectError): donor_models(project, expected)

    @patch('sdk.scene_preview.source_key', side_effect=['a' * 64, 'a' * 64, 'b' * 64])
    def test_source_drift_withdraws_catalog(self, key):
        project, _ = self.fixture()
        with self.assertRaises(ProjectError): donor_models(project, 'a' * 64)
