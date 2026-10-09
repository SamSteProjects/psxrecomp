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
from importer.controller_tile_rects import ControllerTileRectAuthoringContext
from test_controller_branches import source,OWNER
from test_project_workflow import synthetic_scene

ID='script://fixture/controllers/man-p1/0000/tile-rect/0007'
VALUES=dict(column_start=1,row_start=2,column_end=3,row_end=4,value=255)


class ControllerTileBuild(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.p=ProjectService(Path(self.temp.name));self.p.import_metadata(synthetic_scene())
        src,self.man=source(b'\x61\x23\x4c\x83\x01\x02\x03\x04\x05\x26\xf6\xff');self.ctx=ControllerSystemFlagAuthoringContext(src)
        self.hash=sha256(src.verified_record(OWNER)[1]).hexdigest();self.p.overrides[OWNER]={'ControllerTileRects':dict(source_record_sha256=self.hash,entries={ID:VALUES})}
        mock=patch('sdk.controller_selector_build.load_controller_system_flag_context',return_value=self.ctx);mock.start();self.addCleanup(mock.stop)

    def mixed(self):
        self.p.overrides[OWNER]['ControllerSystemFlags']=dict(source_record_sha256=self.hash,entries={'script://fixture/controllers/man-p1/0000/system-flag/0005':{'index':3}})
        self.p.overrides[OWNER]['ControllerBranches']=dict(source_record_sha256=self.hash,entries={'script://fixture/controllers/man-p1/0000/branch/000e':{'target_pc':7}})

    def test_tile_only_and_three_families_have_literal_complete_man_and_receipts(self):
        for mixed in (False,True):
            if mixed:self.mixed()
            result,audit=compose(self.p,'scene://fixture',self.man,self.man);expected=bytearray(self.man);expected[70]=255
            if mixed:expected[62:64]=b'\x60\x03';expected[72:74]=b'\xf8\xff'
            self.assertEqual(result,bytes(expected));self.assertEqual(len(audit),3 if mixed else 1)
            tile=next(r for r in audit if r['field']=='script.tile_rect_operands');self.assertEqual(tile['byte_length'],5);self.assertEqual(tile['owner_kind'],'scene_controller')
            self.assertEqual(tile['changed_bytes'],[dict(decoded_byte_offset=70,before_byte=5,after_byte=255)])
            pre_tile=bytearray(expected);pre_tile[70]=5;self.assertEqual(tile['effective_record_sha256'],sha256(bytes(pre_tile)[57:-18]).hexdigest())

    def test_relocated_mixed_receipts_and_noop_overlap(self):
        self.mixed();candidate=bytearray(self.man[:57]+b'0123'+self.man[57:]);candidate[40:43]=(int.from_bytes(self.man[40:43],'little')+4).to_bytes(3,'little');candidate[46:49]=(12).to_bytes(3,'little')
        result,audit=compose(self.p,'scene://fixture',self.man,bytes(candidate),appended=True);expected=bytearray(candidate);expected[66:68]=b'\x60\x03';expected[74]=255;expected[76:78]=b'\xf8\xff';self.assertEqual(result,bytes(expected))
        tile=next(r for r in audit if r['field']=='script.tile_rect_operands');self.assertEqual(tile['source_decoded_byte_offset'],66);self.assertEqual(tile['decoded_byte_offset'],70)
        self.assertEqual(tile['appended_man_sha256'],sha256(bytes(expected[:74])+b'\x05'+bytes(expected[75:])).hexdigest())
        self.p.overrides[OWNER]={'ControllerTileRects':dict(source_record_sha256=self.hash,entries={ID:dict(VALUES,value=5)})}
        self.assertEqual(compose(self.p,'scene://fixture',self.man,self.man),(self.man,[]))
        with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.man,self.man,[dict(decoded_byte_offset=70,byte_length=1)])

    def test_forged_missing_duplicate_receipts_and_unaudited_bytes_refuse(self):
        native,audit=ControllerTileRectAuthoringContext(self.ctx._source).patch({ID:VALUES})
        for receipts in ([],audit+audit,[dict(audit[0],source_record_sha256='f'*64)],[dict(audit[0],after_hex='0000000000')],[dict(audit[0],decoded_byte_offset=66.0)],[dict(audit[0],after_values=dict(VALUES,value=True))]):
            with patch.object(ControllerTileRectAuthoringContext,'patch',return_value=(native,receipts)):
                with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.man,self.man)
        forged=bytearray(native);forged[50]=1
        with patch.object(ControllerTileRectAuthoringContext,'patch',return_value=(bytes(forged),audit)):
            with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.man,self.man)
        forged=bytearray(self.man);forged[70]=6
        with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.man,bytes(forged))
