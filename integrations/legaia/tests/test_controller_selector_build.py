from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.build import BuildError
from sdk.controller_selector_build import compose,collect
from test_controller_system_flags import context,fixture,OWNER,ID
from integrations.legaia.tests.test_project_workflow import synthetic_scene
from hashlib import sha256


class ControllerBuild(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.p=ProjectService(Path(temp.name));self.p.import_metadata(synthetic_scene());self.ctx=context(fixture());self.baseline=self.ctx._man
        self.p.overrides[OWNER]={'ControllerSystemFlags':{'source_record_sha256':sha256(self.ctx._source.verified_record(OWNER)[1]).hexdigest(),'entries':{ID:{'index':292}}}}
        mock=patch('sdk.controller_selector_build.load_controller_system_flag_context',return_value=self.ctx);mock.start();self.addCleanup(mock.stop)

    def test_normal_and_relocated_equal_span_receipts(self):
        for appended in (False,True):
            actual,receipts=compose(self.p,'scene://fixture',self.baseline,self.baseline,appended=appended)
            expected=bytearray(self.baseline);expected[63]=0x24;self.assertEqual(actual,bytes(expected))
            self.assertEqual(receipts[0]['owner_kind'],'scene_controller')
            self.assertEqual(receipts[0]['source_record_sha256'],self.p.overrides[OWNER]['ControllerSystemFlags']['source_record_sha256'])

    def test_forged_receipts_overlap_and_unknown_preimages_refuse(self):
        changed,audit=self.ctx.patch({ID:{'index':292}})
        for receipt in ([],[dict(audit[0],owner_id=OWNER.replace('fixture','other'))],[dict(audit[0],after_hex='ffff')]):
            with patch.object(self.ctx,'patch',return_value=(changed,receipt)):
                with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.baseline,self.baseline)
        forged=bytearray(changed);forged[50]=1
        with patch.object(self.ctx,'patch',return_value=(bytes(forged),audit)):
            with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.baseline,self.baseline)
        with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.baseline,self.baseline,[{'decoded_byte_offset':62,'byte_length':2}])
        forged=bytearray(self.baseline);forged[58]=1
        with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.baseline,bytes(forged),appended=True)

    def test_source_hash_and_mixed_owner_components_refuse(self):
        self.p.overrides[OWNER]['ControllerSystemFlags']['source_record_sha256']='f'*64
        with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.baseline,self.baseline)
        with self.assertRaises(ProjectError):collect(self.p,OWNER,{**self.p.overrides[OWNER],'Transform':{}})

    def test_appended_receipt_retains_original_source_and_candidate_proof(self):
        changed,audit=self.ctx.patch_appended(self.baseline,{ID:{'index':292}})
        for field,value in [('source_decoded_man_sha256','f'*64),('appended_man_sha256','f'*64),('source_decoded_byte_offset',0)]:
            forged=[dict(audit[0],**{field:value})]
            with patch.object(self.ctx,'patch_appended',return_value=(changed,forged)):
                with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.baseline,self.baseline,appended=True)
