from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from sdk.project import ProjectService
from sdk.build import BuildError
from sdk.controller_selector_build import compose
from importer.controller_system_flags import ControllerSystemFlagAuthoringContext
from importer.controller_branches import ControllerBranchAuthoringContext
from test_controller_branches import source,OWNER,ID
from test_branch_authoring import family_script
from test_project_workflow import synthetic_scene


class ControllerBranchBuild(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.p=ProjectService(Path(self.temp.name));self.p.import_metadata(synthetic_scene());src,self.man=source(family_script('SYSFLAG_TEST')[0]);self.ctx=ControllerSystemFlagAuthoringContext(src)
        h=sha256(src.verified_record(OWNER)[1]).hexdigest();self.p.overrides[OWNER]={'ControllerBranches':{'source_record_sha256':h,'entries':{ID:{'target_pc':5}}}}
        self.selector=ID.replace('/branch/','/system-flag/');self.selector_value={'source_record_sha256':h,'entries':{self.selector:{'index':3}}}
        mock=patch('sdk.controller_selector_build.load_controller_system_flag_context',return_value=self.ctx);mock.start();self.addCleanup(mock.stop)

    def test_branch_only_and_mixed_have_literal_bytes_and_separate_receipts(self):
        for mixed in [False,True]:
            if mixed:self.p.overrides[OWNER]['ControllerSystemFlags']=self.selector_value
            actual,audit=compose(self.p,'scene://fixture',self.man,self.man)
            expected=bytearray(self.man);expected[64:66]=b'\xfe\xff'
            if mixed:expected[63]=3
            self.assertEqual(actual,bytes(expected));self.assertEqual(len(audit),2 if mixed else 1)
            branch=next(r for r in audit if r['field']=='script.branch_target');self.assertEqual(branch['owner_kind'],'scene_controller');self.assertEqual(branch['record_index'],0)
            self.assertEqual(branch['source_record_sha256'],self.selector_value['source_record_sha256'])

    def test_appended_rebinding_retains_original_and_composed_preimage_hashes(self):
        self.p.overrides[OWNER]['ControllerSystemFlags']=self.selector_value
        candidate=bytearray(self.man[:57]+b'0123'+self.man[57:]);candidate[40:43]=(int.from_bytes(self.man[40:43],'little')+4).to_bytes(3,'little');candidate[46:49]=(12).to_bytes(3,'little')
        actual,audit=compose(self.p,'scene://fixture',self.man,bytes(candidate),appended=True)
        expected=bytearray(candidate);expected[67]=3;expected[68:70]=b'\xfe\xff';self.assertEqual(actual,bytes(expected))
        branch=next(r for r in audit if r['field']=='script.branch_target');self.assertEqual(branch['source_decoded_byte_offset'],64);self.assertEqual(branch['decoded_byte_offset'],68)
        self.assertEqual(branch['source_decoded_man_sha256'],sha256(self.man).hexdigest())
        selected=bytearray(candidate);selected[67]=3;self.assertEqual(branch['appended_man_sha256'],sha256(selected).hexdigest())

    def test_forged_missing_duplicate_and_unaudited_receipts_refuse(self):
        context=ControllerBranchAuthoringContext(self.ctx._source);native,audit=context.patch({ID:{'target_pc':5}})
        for receipts in [[],audit+audit,[dict(audit[0],source_record_sha256='f'*64)],[dict(audit[0],after_hex='ffff')],[dict(audit[0],changed_bytes=[])],[dict(audit[0],decoded_byte_offset=float(audit[0]['decoded_byte_offset']))]]:
            with patch.object(ControllerBranchAuthoringContext,'patch_composed',return_value=(native,receipts)):
                with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.man,self.man)
        forged=bytearray(native);forged[50]=1
        with patch.object(ControllerBranchAuthoringContext,'patch_composed',return_value=(bytes(forged),audit)):
            with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.man,self.man)
        with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.man,self.man,[{'decoded_byte_offset':64,'byte_length':2}])

    def test_unknown_controller_preimages_and_noop_overlap_refuse(self):
        forged=bytearray(self.man);forged[58]=1
        with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.man,bytes(forged))
        self.p.overrides[OWNER]['ControllerBranches']['entries'][ID]={'target_pc':10}
        self.assertEqual(compose(self.p,'scene://fixture',self.man,self.man),(self.man,[]))
        with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.man,self.man,[{'decoded_byte_offset':64,'byte_length':2}])
