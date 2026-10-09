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
from importer.controller_three_words import ControllerThreeWordAuthoringContext
from test_controller_branches import source,OWNER
from test_project_workflow import synthetic_scene

ID='script://fixture/controllers/man-p1/0000/three-word/000e'
VALUES=dict(signed_words=[-32768,32767,-1])


class ControllerThreeWordBuild(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.p=ProjectService(Path(self.temp.name));self.p.import_metadata(synthetic_scene())
        src,self.man=source(b'\x61\x23\x4c\x83\x01\x02\x03\x04\x05\x4c\xe6'+bytes(6)+b'\x26\xee\xff');self.ctx=ControllerSystemFlagAuthoringContext(src)
        self.hash=sha256(src.verified_record(OWNER)[1]).hexdigest();self.p.overrides[OWNER]={'ControllerThreeWords':dict(source_record_sha256=self.hash,entries={ID:VALUES})}
        mock=patch('sdk.controller_selector_build.load_controller_system_flag_context',return_value=self.ctx);mock.start();self.addCleanup(mock.stop)

    def mixed(self):
        self.p.overrides[OWNER]['ControllerTileRects']=dict(source_record_sha256=self.hash,entries={'script://fixture/controllers/man-p1/0000/tile-rect/0007':dict(column_start=1,row_start=2,column_end=3,row_end=4,value=255)})
        self.p.overrides[OWNER]['ControllerSystemFlags']=dict(source_record_sha256=self.hash,entries={'script://fixture/controllers/man-p1/0000/system-flag/0005':{'index':3}})
        self.p.overrides[OWNER]['ControllerBranches']=dict(source_record_sha256=self.hash,entries={'script://fixture/controllers/man-p1/0000/branch/0016':{'target_pc':7}})

    def test_three_word_only_and_four_families_have_literal_complete_man_and_receipts(self):
        for mixed in (False,True):
            if mixed:self.mixed()
            result,audit=compose(self.p,'scene://fixture',self.man,self.man);expected=bytearray(self.man);expected[73:79]=bytes.fromhex('0080ff7fffff')
            if mixed:expected[62:64]=b'\x60\x03';expected[70]=255;expected[80:82]=b'\xf0\xff'
            self.assertEqual(result,bytes(expected));self.assertEqual(len(audit),4 if mixed else 1)
            triplet=next(r for r in audit if r['field']=='script.three_word_operands');self.assertEqual(triplet['byte_length'],6);self.assertEqual(triplet['owner_kind'],'scene_controller')
            self.assertEqual(triplet['changed_bytes'],[dict(decoded_byte_offset=at,before_byte=0,after_byte=value) for at,value in [(74,128),(75,255),(76,127),(77,255),(78,255)]])
            pre_triplet=bytearray(expected);pre_triplet[73:79]=bytes(6);self.assertEqual(triplet['effective_record_sha256'],sha256(bytes(pre_triplet)[57:-18]).hexdigest())

    def test_relocated_mixed_receipts_and_noop_overlap(self):
        self.mixed();candidate=bytearray(self.man[:57]+b'0123'+self.man[57:]);candidate[40:43]=(int.from_bytes(self.man[40:43],'little')+4).to_bytes(3,'little');candidate[46:49]=(12).to_bytes(3,'little')
        result,audit=compose(self.p,'scene://fixture',self.man,bytes(candidate),appended=True);expected=bytearray(candidate);expected[66:68]=b'\x60\x03';expected[74]=255;expected[77:83]=bytes.fromhex('0080ff7fffff');expected[84:86]=b'\xf0\xff';self.assertEqual(result,bytes(expected))
        triplet=next(r for r in audit if r['field']=='script.three_word_operands');self.assertEqual(triplet['source_decoded_byte_offset'],73);self.assertEqual(triplet['decoded_byte_offset'],77)
        self.assertEqual(triplet['appended_man_sha256'],sha256(bytes(expected[:77])+bytes(6)+bytes(expected[83:])).hexdigest())
        self.p.overrides[OWNER]={'ControllerThreeWords':dict(source_record_sha256=self.hash,entries={ID:dict(signed_words=[0,0,0])})}
        self.assertEqual(compose(self.p,'scene://fixture',self.man,self.man),(self.man,[]))
        with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.man,self.man,[dict(decoded_byte_offset=73,byte_length=1)])

    def test_forged_missing_duplicate_receipts_and_unaudited_bytes_refuse(self):
        native,audit=ControllerThreeWordAuthoringContext(self.ctx._source).patch({ID:VALUES})
        for receipts in ([],audit+audit,[dict(audit[0],source_record_sha256='f'*64)],[dict(audit[0],sub_op=True)],[dict(audit[0],before_values=dict(signed_words=[False,0,0]))],[dict(audit[0],after_hex='000000000000')],[dict(audit[0],decoded_byte_offset=66.0)],[dict(audit[0],after_values=dict(VALUES,signed_words=[True,32767,-1]))]):
            with patch.object(ControllerThreeWordAuthoringContext,'patch',return_value=(native,receipts)):
                with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.man,self.man)
        forged=bytearray(native);forged[50]=1
        with patch.object(ControllerThreeWordAuthoringContext,'patch',return_value=(bytes(forged),audit)):
            with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.man,self.man)
        forged=bytearray(self.man);forged[73]=6
        with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.man,bytes(forged))

    def test_all_seven_families_build_from_one_record(self):
        src,man=source(b'\x61\x23\x4c\x83\x01\x02\x03\x04\x05\x4c\x90\x00'+bytes(6)+b'\x4c\x9e'+bytes(32)+b'\x4c\xd8\x00'+bytes(6)+b'\x4c\xe6'+bytes(6)+b'\x26\xba\xff')
        ctx=ControllerSystemFlagAuthoringContext(src)
        source_hash=sha256(src.verified_record(OWNER)[1]).hexdigest()
        root=OWNER.replace('scene://','script://',1)
        fields={
            'ControllerSystemFlags':('system-flag/0005',{'index':4095}),
            'ControllerBranches':('branch/004a',{'target_pc':7}),
            'ControllerTileRects':('tile-rect/0007',dict(column_start=1,row_start=2,column_end=3,row_end=4,value=255)),
            'ControllerFades':('fade/000e',dict(selector=1,signed_words=[1,2,3])),
            'ControllerTableCopies':('table-copy/0017',dict(signed_words=list(range(1,17)))),
            'ControllerWordTriplets':('word-triplet/0039',dict(selector=255,signed_words=[-32768,32767,-1])),
            'ControllerThreeWords':('three-word/0042',VALUES),
        }
        self.p.overrides[OWNER]={family:dict(source_record_sha256=source_hash,entries={root+'/'+suffix:value}) for family,(suffix,value) in fields.items()}
        expected=bytearray(man)
        expected[62:64]=b'\x6f\xff';expected[70]=255
        expected[73:80]=bytes.fromhex('01010002000300')
        expected[82:114]=b''.join(word.to_bytes(2,'little',signed=True) for word in range(1,17))
        expected[116:123]=bytes.fromhex('ff0080ff7fffff');expected[125:131]=bytes.fromhex('0080ff7fffff');expected[132:134]=b'\xbc\xff'
        with patch('sdk.controller_selector_build.load_controller_system_flag_context',return_value=ctx):
            result,audit=compose(self.p,'scene://fixture',man,man)
        self.assertEqual(result,bytes(expected));self.assertEqual(len(audit),7)
        triplet=next(r for r in audit if r['field']=='script.three_word_operands')
        self.assertEqual(triplet['three_word_id'],root+'/three-word/0042')
        self.assertEqual(triplet['scope'],'controller-three-word-operands-only')
        from sdk.build import build_report,package_change_kinds
        report=build_report(dict(edits=[dict(triplet,scene='fixture')],validation={},overlays=[]))
        self.assertEqual(report['changes'][0]['after'],VALUES)
        self.assertEqual(report['changes'][0]['asset_id'],triplet['three_word_id'])
        self.assertEqual(package_change_kinds([triplet]),['controller three-word operands'])
