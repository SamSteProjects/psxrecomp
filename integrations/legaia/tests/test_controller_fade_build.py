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
from importer.controller_fades import ControllerFadeAuthoringContext
from test_controller_branches import source,OWNER
from test_project_workflow import synthetic_scene

ID='script://fixture/controllers/man-p1/0000/fade/000e'
VALUES=dict(selector=255,signed_words=[-32768,32767,-1])


class ControllerFadeBuild(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.p=ProjectService(Path(self.temp.name));self.p.import_metadata(synthetic_scene())
        src,self.man=source(b'\x61\x23\x4c\x83\x01\x02\x03\x04\x05\x4c\x90\x00'+bytes(6)+b'\x26\xed\xff');self.ctx=ControllerSystemFlagAuthoringContext(src)
        self.hash=sha256(src.verified_record(OWNER)[1]).hexdigest();self.p.overrides[OWNER]={'ControllerFades':dict(source_record_sha256=self.hash,entries={ID:VALUES})}
        mock=patch('sdk.controller_selector_build.load_controller_system_flag_context',return_value=self.ctx);mock.start();self.addCleanup(mock.stop)

    def mixed(self):
        self.p.overrides[OWNER]['ControllerTileRects']=dict(source_record_sha256=self.hash,entries={'script://fixture/controllers/man-p1/0000/tile-rect/0007':dict(column_start=1,row_start=2,column_end=3,row_end=4,value=255)})
        self.p.overrides[OWNER]['ControllerSystemFlags']=dict(source_record_sha256=self.hash,entries={'script://fixture/controllers/man-p1/0000/system-flag/0005':{'index':3}})
        self.p.overrides[OWNER]['ControllerBranches']=dict(source_record_sha256=self.hash,entries={'script://fixture/controllers/man-p1/0000/branch/0017':{'target_pc':7}})

    def test_fade_only_and_four_families_have_literal_complete_man_and_receipts(self):
        for mixed in (False,True):
            if mixed:self.mixed()
            result,audit=compose(self.p,'scene://fixture',self.man,self.man);expected=bytearray(self.man);expected[73:80]=bytes.fromhex('ff0080ff7fffff')
            if mixed:expected[62:64]=b'\x60\x03';expected[70]=255;expected[81:83]=b'\xef\xff'
            self.assertEqual(result,bytes(expected));self.assertEqual(len(audit),4 if mixed else 1)
            tile=next(r for r in audit if r['field']=='script.fade_operands');self.assertEqual(tile['byte_length'],7);self.assertEqual(tile['owner_kind'],'scene_controller')
            self.assertEqual(tile['changed_bytes'],[dict(decoded_byte_offset=at,before_byte=0,after_byte=value) for at,value in [(73,255),(75,128),(76,255),(77,127),(78,255),(79,255)]])
            pre_tile=bytearray(expected);pre_tile[73:80]=bytes(7);self.assertEqual(tile['effective_record_sha256'],sha256(bytes(pre_tile)[57:-18]).hexdigest())

    def test_relocated_mixed_receipts_and_noop_overlap(self):
        self.mixed();candidate=bytearray(self.man[:57]+b'0123'+self.man[57:]);candidate[40:43]=(int.from_bytes(self.man[40:43],'little')+4).to_bytes(3,'little');candidate[46:49]=(12).to_bytes(3,'little')
        result,audit=compose(self.p,'scene://fixture',self.man,bytes(candidate),appended=True);expected=bytearray(candidate);expected[66:68]=b'\x60\x03';expected[74]=255;expected[77:84]=bytes.fromhex('ff0080ff7fffff');expected[85:87]=b'\xef\xff';self.assertEqual(result,bytes(expected))
        tile=next(r for r in audit if r['field']=='script.fade_operands');self.assertEqual(tile['source_decoded_byte_offset'],73);self.assertEqual(tile['decoded_byte_offset'],77)
        self.assertEqual(tile['appended_man_sha256'],sha256(bytes(expected[:77])+bytes(7)+bytes(expected[84:])).hexdigest())
        self.p.overrides[OWNER]={'ControllerFades':dict(source_record_sha256=self.hash,entries={ID:dict(selector=0,signed_words=[0,0,0])})}
        self.assertEqual(compose(self.p,'scene://fixture',self.man,self.man),(self.man,[]))
        with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.man,self.man,[dict(decoded_byte_offset=73,byte_length=1)])

    def test_forged_missing_duplicate_receipts_and_unaudited_bytes_refuse(self):
        native,audit=ControllerFadeAuthoringContext(self.ctx._source).patch({ID:VALUES})
        for receipts in ([],audit+audit,[dict(audit[0],source_record_sha256='f'*64)],[dict(audit[0],sub_op=True)],[dict(audit[0],before_values=dict(selector=False,signed_words=[0,0,0]))],[dict(audit[0],after_hex='00000000000000')],[dict(audit[0],decoded_byte_offset=66.0)],[dict(audit[0],after_values=dict(VALUES,signed_words=[True,32767,-1]))]):
            with patch.object(ControllerFadeAuthoringContext,'patch',return_value=(native,receipts)):
                with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.man,self.man)
        forged=bytearray(native);forged[50]=1
        with patch.object(ControllerFadeAuthoringContext,'patch',return_value=(bytes(forged),audit)):
            with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.man,self.man)
        forged=bytearray(self.man);forged[73]=6
        with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.man,bytes(forged))
