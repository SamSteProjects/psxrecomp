"""Native-qualified operands coexist with partial general catalog coverage."""
from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch
import test_flag_asset_integration as fixtures
from sdk.resources import refresh_resource_catalog,scene_flag_index,project_flag_index
from sdk.asset_references import assemble
from sdk.flag_assets import validate_flag_asset
from sdk.project import ProjectError


class FlagQualification(TestCase):
    def setUp(self):
        fixtures.FlagAssetIntegration.setUp(self)
        script=next(row for row in self.catalog['assets'] if row['asset_kind']=='script' and row['semantic_id']=='script://'+fixtures.ACTOR[8:])
        script['status']='partial';self.catalog['partial_script_count']+=1
        self.project.command(dict(type='set_flag_bit',entity_id=fixtures.ACTOR,flag_id=self.key,values={'bit':3}))

    def test_partial_catalog_keeps_current_bits_and_independent_native_proof(self):
        before=deepcopy((self.project._document(),self.project.undo_stack,self.project.redo_stack))
        catalog=refresh_resource_catalog(self.project);flag=next(row for row in catalog['records'] if row['kind']=='flag')
        self.assertEqual(flag['script_status'],'partial');self.assertEqual(flag['references'][0]['effective_index'],3)
        proof=flag['references'][0]['authored_qualification'];self.assertEqual(proof['source_record_sha256'],flag['source_record']['sha256']);self.assertEqual(proof['retail_index'],2);self.assertEqual(proof['authored_index'],3)
        self.assertNotIn('authored_qualification',flag['references'][1]);validate_flag_asset(flag)
        current=next(edge for edge in assemble(self.project,catalog,flag['id'])['incoming'] if edge['kind']=='effective_script_flag_reference')
        self.assertEqual(current['flag_binding_evidence']['native_operand_qualification'],proof)
        self.assertEqual(scene_flag_index(self.project)['groups'][0]['references'][0]['authored_qualification'],proof)
        with patch('sdk.resources._verify'):
            self.assertEqual(project_flag_index(self.project)['groups'][0]['references'][0]['authored_qualification'],proof)
        self.assertEqual(before,(self.project._document(),self.project.undo_stack,self.project.redo_stack))
        self.project.undo();retail=next(row for row in refresh_resource_catalog(self.project)['records'] if row['kind']=='flag');self.assertEqual(retail['id'],flag['id']);self.assertTrue(all('authored_qualification' not in ref for ref in retail['references']))
        self.project.redo();self.assertEqual(refresh_resource_catalog(self.project),catalog)

    def test_missing_forged_and_unowned_proofs_reject(self):
        flag=next(row for row in refresh_resource_catalog(self.project)['records'] if row['kind']=='flag')
        for mutate in [lambda r:r['references'][0].pop('authored_qualification'),lambda r:r['references'][0]['authored_qualification'].update(source_record_sha256='b'*64),lambda r:r['references'][0]['authored_qualification'].update(pc=7),lambda r:r['references'][0]['authored_qualification'].update(authored_index=2),lambda r:r['references'][0]['authored_qualification'].update(maximum=15),lambda r:r['references'][0]['authored_qualification'].update(extended_target=7),lambda r:r['references'][0]['authored_qualification'].update(runtime_value=1),lambda r:r['references'][1].update(authored_qualification=deepcopy(r['references'][0]['authored_qualification']))]:
            broken=deepcopy(flag);mutate(broken)
            with self.assertRaises(ProjectError):validate_flag_asset(broken)
