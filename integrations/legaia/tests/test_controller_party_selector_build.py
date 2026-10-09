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
from importer.controller_party_selectors import ControllerPartySelectorAuthoringContext
from test_controller_branches import source,OWNER
from test_project_workflow import synthetic_scene

ID='script://fixture/controllers/man-p1/0000/party-selector/000e'
VALUES=dict(party_selector=7)


class ControllerPartySelectorBuild(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.p=ProjectService(Path(self.temp.name));self.p.import_metadata(synthetic_scene())
        src,self.man=source(b'\x61\x23\x4c\x83\x01\x02\x03\x04\x05\x4c\x2a\x26\xf4\xff');self.ctx=ControllerSystemFlagAuthoringContext(src)
        self.hash=sha256(src.verified_record(OWNER)[1]).hexdigest();self.p.overrides[OWNER]={'ControllerPartySelectors':dict(source_record_sha256=self.hash,entries={ID:VALUES})}
        mock=patch('sdk.controller_selector_build.load_controller_system_flag_context',return_value=self.ctx);mock.start();self.addCleanup(mock.stop)

    def mixed(self):
        self.p.overrides[OWNER]['ControllerTileRects']=dict(source_record_sha256=self.hash,entries={'script://fixture/controllers/man-p1/0000/tile-rect/0007':dict(column_start=1,row_start=2,column_end=3,row_end=4,value=255)})
        self.p.overrides[OWNER]['ControllerSystemFlags']=dict(source_record_sha256=self.hash,entries={'script://fixture/controllers/man-p1/0000/system-flag/0005':{'index':3}})
        self.p.overrides[OWNER]['ControllerBranches']=dict(source_record_sha256=self.hash,entries={'script://fixture/controllers/man-p1/0000/branch/0010':{'target_pc':7}})

    def test_party_selector_only_and_four_families_have_literal_complete_man_and_receipts(self):
        for mixed in (False,True):
            if mixed:self.mixed()
            result,audit=compose(self.p,'scene://fixture',self.man,self.man);expected=bytearray(self.man);expected[72]=0x2f
            if mixed:expected[62:64]=b'\x60\x03';expected[70]=255;expected[74:76]=b'\xf6\xff'
            self.assertEqual(result,bytes(expected));self.assertEqual(len(audit),4 if mixed else 1)
            triplet=next(r for r in audit if r['field']=='script.party_selector');self.assertEqual(triplet['byte_length'],1);self.assertEqual(triplet['owner_kind'],'scene_controller')
            self.assertEqual(triplet['changed_bytes'],[dict(decoded_byte_offset=72,before_byte=0x2a,after_byte=0x2f)])
            pre_triplet=bytearray(expected);pre_triplet[72]=0x2a;self.assertEqual(triplet['effective_record_sha256'],sha256(bytes(pre_triplet)[57:-18]).hexdigest())

    def test_relocated_mixed_receipts_and_noop_overlap(self):
        self.mixed();candidate=bytearray(self.man[:57]+b'0123'+self.man[57:]);candidate[40:43]=(int.from_bytes(self.man[40:43],'little')+4).to_bytes(3,'little');candidate[46:49]=(12).to_bytes(3,'little')
        result,audit=compose(self.p,'scene://fixture',self.man,bytes(candidate),appended=True);expected=bytearray(candidate);expected[66:68]=b'\x60\x03';expected[74]=255;expected[76]=0x2f;expected[78:80]=b'\xf6\xff';self.assertEqual(result,bytes(expected))
        triplet=next(r for r in audit if r['field']=='script.party_selector');self.assertEqual(triplet['source_decoded_byte_offset'],72);self.assertEqual(triplet['decoded_byte_offset'],76)
        self.assertEqual(triplet['appended_man_sha256'],sha256(bytes(expected[:76])+bytes([0x2a])+bytes(expected[77:])).hexdigest())
        self.p.overrides[OWNER]={'ControllerPartySelectors':dict(source_record_sha256=self.hash,entries={ID:dict(party_selector=2)})}
        self.assertEqual(compose(self.p,'scene://fixture',self.man,self.man),(self.man,[]))
        with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.man,self.man,[dict(decoded_byte_offset=72,byte_length=1)])

    def test_forged_missing_duplicate_receipts_and_unaudited_bytes_refuse(self):
        native,audit=ControllerPartySelectorAuthoringContext(self.ctx._source).patch({ID:VALUES})
        for receipts in ([],audit+audit,[dict(audit[0],source_record_sha256='f'*64)],[dict(audit[0],sub_op=True)],[dict(audit[0],selector_mask=True)],[dict(audit[0],preserved_bits=0)],[dict(audit[0],after_hex='0f')],[dict(audit[0],before_values=dict(party_selector=True))],[dict(audit[0],after_hex='000000000000')],[dict(audit[0],decoded_byte_offset=66.0)],[dict(audit[0],after_values=dict(party_selector=True))]):
            with patch.object(ControllerPartySelectorAuthoringContext,'patch',return_value=(native,receipts)):
                with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.man,self.man)
        forged=bytearray(native);forged[50]=1
        with patch.object(ControllerPartySelectorAuthoringContext,'patch',return_value=(bytes(forged),audit)):
            with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.man,self.man)
        forged=bytearray(self.man);forged[72]=0x23
        with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.man,bytes(forged))

    def test_all_eleven_families_build_from_one_record(self):
        src,man=source(b'\x61\x23\x4c\x83\x01\x02\x03\x04\x05\x4c\x90\x00'+bytes(6)+b'\x4c\x9e'+bytes(32)+b'\x4c\xd8\x00'+bytes(6)+b'\x4c\xe6'+bytes(6)+b'\x43\x11'+bytes(10)+b'\x43\x03'+bytes(8)+b'\x4c\xdf\x01\x4c\x2a\x26\x9f\xff')
        ctx=ControllerSystemFlagAuthoringContext(src)
        source_hash=sha256(src.verified_record(OWNER)[1]).hexdigest()
        root=OWNER.replace('scene://','script://',1)
        fields={
            'ControllerSystemFlags':('system-flag/0005',{'index':4095}),
            'ControllerBranches':('branch/0065',{'target_pc':7}),
            'ControllerTileRects':('tile-rect/0007',dict(column_start=1,row_start=2,column_end=3,row_end=4,value=255)),
            'ControllerFades':('fade/000e',dict(selector=1,signed_words=[1,2,3])),
            'ControllerTableCopies':('table-copy/0017',dict(signed_words=list(range(1,17)))),
            'ControllerWordTriplets':('word-triplet/0039',dict(selector=255,signed_words=[-32768,32767,-1])),
            'ControllerThreeWords':('three-word/0042',dict(signed_words=[-32768,32767,-1])),
            'ControllerFiveWords':('five-word/004a',dict(signed_words=[-32768,32767,-1,0,1])),
            'ControllerGlobalBytes':('global-byte/0056',dict(byte_values=[0,255,31,64],parameters_i16=[-32768,32767])),
            'ControllerSceneBytes':('scene-byte/0060',dict(value=255)),
            'ControllerPartySelectors':('party-selector/0063',VALUES),
        }
        self.p.overrides[OWNER]={family:dict(source_record_sha256=source_hash,entries={root+'/'+suffix:value}) for family,(suffix,value) in fields.items()}
        expected=bytearray(man)
        expected[62:64]=b'\x6f\xff';expected[70]=255
        expected[73:80]=bytes.fromhex('01010002000300')
        expected[82:114]=b''.join(word.to_bytes(2,'little',signed=True) for word in range(1,17))
        expected[116:123]=bytes.fromhex('ff0080ff7fffff');expected[125:131]=bytes.fromhex('0080ff7fffff');expected[133:143]=bytes.fromhex('0080ff7fffff00000100');expected[145:153]=bytes.fromhex('00ff1f400080ff7f');expected[155]=255;expected[157]=0x2f;expected[159:161]=b'\xa1\xff'
        with patch('sdk.controller_selector_build.load_controller_system_flag_context',return_value=ctx):
            result,audit=compose(self.p,'scene://fixture',man,man)
        self.assertEqual(result,bytes(expected));self.assertEqual(len(audit),11)
        triplet=next(r for r in audit if r['field']=='script.party_selector')
        self.assertEqual(triplet['party_selector_id'],root+'/party-selector/0063')
        self.assertEqual(triplet['scope'],'controller-party-selector-only')
        from sdk.build import build_report,package_change_kinds
        report=build_report(dict(edits=[dict(triplet,scene='fixture')],validation={},overlays=[]))
        self.assertEqual(report['changes'][0]['after'],VALUES)
        self.assertEqual(report['changes'][0]['asset_id'],triplet['party_selector_id'])
        self.assertEqual(package_change_kinds([triplet]),['controller party selector'])
