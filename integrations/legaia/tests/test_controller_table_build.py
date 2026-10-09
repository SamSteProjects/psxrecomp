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
from importer.controller_tables import ControllerTableCopyAuthoringContext
from test_controller_branches import source,OWNER
from test_project_workflow import synthetic_scene

ID='script://fixture/controllers/man-p1/0000/table-copy/0017'
VALUES=dict(signed_words=[-32768,32767,-1,*range(13)])


class ControllerTableCopyBuild(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.p=ProjectService(Path(self.temp.name));self.p.import_metadata(synthetic_scene())
        src,self.man=source(b'\x61\x23\x4c\x83\x01\x02\x03\x04\x05\x4c\x90\x00'+bytes(6)+b'\x4c\x9e'+bytes(32)+b'\x26\xcb\xff');self.ctx=ControllerSystemFlagAuthoringContext(src)
        self.hash=sha256(src.verified_record(OWNER)[1]).hexdigest();self.p.overrides[OWNER]={'ControllerTableCopies':dict(source_record_sha256=self.hash,entries={ID:VALUES})}
        mock=patch('sdk.controller_selector_build.load_controller_system_flag_context',return_value=self.ctx);mock.start();self.addCleanup(mock.stop)

    def mixed(self):
        self.p.overrides[OWNER]['ControllerFades']=dict(source_record_sha256=self.hash,entries={'script://fixture/controllers/man-p1/0000/fade/000e':dict(selector=255,signed_words=[-32768,32767,-1])})
        self.p.overrides[OWNER]['ControllerTileRects']=dict(source_record_sha256=self.hash,entries={'script://fixture/controllers/man-p1/0000/tile-rect/0007':dict(column_start=1,row_start=2,column_end=3,row_end=4,value=255)})
        self.p.overrides[OWNER]['ControllerSystemFlags']=dict(source_record_sha256=self.hash,entries={'script://fixture/controllers/man-p1/0000/system-flag/0005':{'index':3}})
        self.p.overrides[OWNER]['ControllerBranches']=dict(source_record_sha256=self.hash,entries={'script://fixture/controllers/man-p1/0000/branch/0039':{'target_pc':7}})

    def test_table_only_and_five_families_have_literal_complete_man_and_receipts(self):
        for mixed in (False,True):
            if mixed:self.mixed()
            result,audit=compose(self.p,'scene://fixture',self.man,self.man);expected=bytearray(self.man);expected[82:114]=b''.join(v.to_bytes(2,'little',signed=True) for v in VALUES['signed_words'])
            if mixed:expected[73:80]=bytes.fromhex('ff0080ff7fffff');expected[62:64]=b'\x60\x03';expected[70]=255;expected[115:117]=b'\xcd\xff'
            self.assertEqual(result,bytes(expected));self.assertEqual(len(audit),5 if mixed else 1)
            table=next(r for r in audit if r['field']=='script.table_copy_operands');self.assertEqual(table['byte_length'],32);self.assertEqual(table['owner_kind'],'scene_controller')
            self.assertEqual(table['changed_bytes'],[dict(decoded_byte_offset=82+i,before_byte=0,after_byte=value) for i,value in enumerate(expected[82:114]) if value])
            pre_table=bytearray(expected);pre_table[82:114]=bytes(32);self.assertEqual(table['effective_record_sha256'],sha256(bytes(pre_table)[57:-18]).hexdigest())

    def test_relocated_mixed_receipts_and_noop_overlap(self):
        self.mixed();candidate=bytearray(self.man[:57]+b'0123'+self.man[57:]);candidate[40:43]=(int.from_bytes(self.man[40:43],'little')+4).to_bytes(3,'little');candidate[46:49]=(12).to_bytes(3,'little')
        result,audit=compose(self.p,'scene://fixture',self.man,bytes(candidate),appended=True);expected=bytearray(candidate);expected[77:84]=bytes.fromhex('ff0080ff7fffff');expected[66:68]=b'\x60\x03';expected[74]=255;expected[86:118]=b''.join(v.to_bytes(2,'little',signed=True) for v in VALUES['signed_words']);expected[119:121]=b'\xcd\xff';self.assertEqual(result,bytes(expected))
        table=next(r for r in audit if r['field']=='script.table_copy_operands');self.assertEqual(table['source_decoded_byte_offset'],82);self.assertEqual(table['decoded_byte_offset'],86)
        self.assertEqual(table['appended_man_sha256'],sha256(bytes(expected[:86])+bytes(32)+bytes(expected[118:])).hexdigest())
        self.p.overrides[OWNER]={'ControllerTableCopies':dict(source_record_sha256=self.hash,entries={ID:dict(signed_words=[0]*16)})}
        self.assertEqual(compose(self.p,'scene://fixture',self.man,self.man),(self.man,[]))
        with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.man,self.man,[dict(decoded_byte_offset=82,byte_length=1)])

    def test_forged_missing_duplicate_receipts_and_unaudited_bytes_refuse(self):
        native,audit=ControllerTableCopyAuthoringContext(self.ctx._source).patch({ID:VALUES})
        for receipts in ([],audit+audit,[dict(audit[0],source_record_sha256='f'*64)],[dict(audit[0],sub_op=True)],[dict(audit[0],before_values=dict(signed_words=[False]+[0]*15))],[dict(audit[0],after_hex='00000000000000')],[dict(audit[0],decoded_byte_offset=66.0)],[dict(audit[0],after_values=dict(VALUES,signed_words=[True]+[0]*15))],[dict(audit[0],after_values=dict(signed_words=[0]*15))],[dict(audit[0],after_values=dict(signed_words=[32768]+[0]*15))],[dict(audit[0],table_copy_id='script://other/controllers/man-p1/0000/table-copy/0017')]):
            with patch.object(ControllerTableCopyAuthoringContext,'patch',return_value=(native,receipts)):
                with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.man,self.man)
        forged=bytearray(native);forged[50]=1
        with patch.object(ControllerTableCopyAuthoringContext,'patch',return_value=(bytes(forged),audit)):
            with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.man,self.man)
        forged=bytearray(self.man);forged[82]=6
        with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.man,bytes(forged))
