from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import tempfile,unittest
from unittest.mock import patch
from sdk.project import ProjectService
from sdk.build import BuildError
from sdk.controller_selector_build import compose
from importer.controller_system_flags import ControllerSystemFlagAuthoringContext
from importer.controller_flag_bits import ControllerFlagBitAuthoringContext
from test_controller_branches import source,OWNER
from test_project_workflow import synthetic_scene
ID='script://fixture/controllers/man-p1/0000/flag-bit/0005'
class ControllerFlagBitBuild(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.p=ProjectService(Path(self.temp.name));self.p.import_metadata(synthetic_scene())
        src,self.man=source(b'\x2e\xe2\x61\x23\x4c\x2a\x26\xf9\xff');self.ctx=ControllerSystemFlagAuthoringContext(src)
        self.hash=sha256(src.verified_record(OWNER)[1]).hexdigest();self.p.overrides[OWNER]={'ControllerFlagBits':dict(source_record_sha256=self.hash,entries={ID:{'bit':31}})}
        mock=patch('sdk.controller_selector_build.load_controller_system_flag_context',return_value=self.ctx);mock.start();self.addCleanup(mock.stop)
    def mixed(self):
        root=OWNER.replace('scene://','script://')
        self.p.overrides[OWNER].update(ControllerSystemFlags=dict(source_record_sha256=self.hash,entries={root+'/system-flag/0007':{'index':3}}),ControllerPartySelectors=dict(source_record_sha256=self.hash,entries={root+'/party-selector/0009':{'party_selector':7}}),ControllerBranches=dict(source_record_sha256=self.hash,entries={root+'/branch/000b':{'target_pc':7}}))
    def test_literal_mixed_relocated_noop_and_overlap(self):
        self.mixed();expected=bytearray(self.man);expected[63]=255;expected[64:66]=b'\x60\x03';expected[67]=47;expected[69:71]=b'\xfb\xff'
        result,audit=compose(self.p,'scene://fixture',self.man,self.man);self.assertEqual(result,bytes(expected));self.assertEqual(len(audit),4)
        bit=next(c for c in audit if c['field']=='script.flag_bit');self.assertEqual(bit['changed_bytes'],[dict(decoded_byte_offset=63,before_byte=226,after_byte=255)])
        from sdk.build import build_report,package_change_kinds
        report=build_report(dict(edits=[dict(bit,scene='fixture')],validation={},overlays=[]));self.assertEqual(report['changes'][0]['after'],{'bit':31});self.assertEqual(report['changes'][0]['asset_id'],ID);self.assertEqual(package_change_kinds([bit]),['controller flag-bit operands'])
        candidate=bytearray(self.man[:57]+b'0123'+self.man[57:]);candidate[40:43]=(int.from_bytes(self.man[40:43],'little')+4).to_bytes(3,'little');candidate[46:49]=(12).to_bytes(3,'little')
        result,audit=compose(self.p,'scene://fixture',self.man,bytes(candidate),appended=True);literal=bytearray(candidate);literal[67]=255;literal[68:70]=b'\x60\x03';literal[71]=47;literal[73:75]=b'\xfb\xff';self.assertEqual(result,bytes(literal));bit=next(c for c in audit if c['field']=='script.flag_bit');self.assertEqual((bit['source_decoded_byte_offset'],bit['decoded_byte_offset']),(63,67))
        self.p.overrides[OWNER]={'ControllerFlagBits':dict(source_record_sha256=self.hash,entries={ID:{'bit':2}})};self.assertEqual(compose(self.p,'scene://fixture',self.man,self.man),(self.man,[]))
        with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.man,self.man,[dict(decoded_byte_offset=63,byte_length=1)])
    def test_forged_missing_duplicate_and_unaudited_receipts_refuse(self):
        native,audit=ControllerFlagBitAuthoringContext(self.ctx._source).patch({ID:{'bit':31}})
        variants=[[],audit+audit]
        for key,value in [('pc',5.0),('before_bit',True),('bit_mask',True),('after_byte',31),('target_context',1),('preserved_bits',0),('source_record_sha256','f'*64),('decoded_byte_offset',64),('extra',1)]:variants.append([dict(audit[0],**{key:value})])
        for receipts in variants:
            with patch.object(ControllerFlagBitAuthoringContext,'patch',return_value=(native,receipts)):
                with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.man,self.man)
        forged=bytearray(native);forged[50]=1
        with patch.object(ControllerFlagBitAuthoringContext,'patch',return_value=(bytes(forged),audit)):
            with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.man,self.man)
        changed=bytearray(self.man);changed[63]=227
        with self.assertRaises(BuildError):compose(self.p,'scene://fixture',self.man,bytes(changed))

    def test_all_twelve_families_build_from_one_record(self):
        src,man=source(b'\x61\x23\x4c\x83\x01\x02\x03\x04\x05\x4c\x90\x00'+bytes(6)+b'\x4c\x9e'+bytes(32)+b'\x4c\xd8\x00'+bytes(6)+b'\x4c\xe6'+bytes(6)+b'\x43\x11'+bytes(10)+b'\x43\x03'+bytes(8)+b'\x4c\xdf\x01\x4c\x2a\x2e\xe2\x26\x9d\xff')
        ctx=ControllerSystemFlagAuthoringContext(src)
        source_hash=sha256(src.verified_record(OWNER)[1]).hexdigest()
        root=OWNER.replace('scene://','script://',1)
        fields={
            'ControllerSystemFlags':('system-flag/0005',{'index':4095}),
            'ControllerBranches':('branch/0067',{'target_pc':7}),
            'ControllerTileRects':('tile-rect/0007',dict(column_start=1,row_start=2,column_end=3,row_end=4,value=255)),
            'ControllerFades':('fade/000e',dict(selector=1,signed_words=[1,2,3])),
            'ControllerTableCopies':('table-copy/0017',dict(signed_words=list(range(1,17)))),
            'ControllerWordTriplets':('word-triplet/0039',dict(selector=255,signed_words=[-32768,32767,-1])),
            'ControllerThreeWords':('three-word/0042',dict(signed_words=[-32768,32767,-1])),
            'ControllerFiveWords':('five-word/004a',dict(signed_words=[-32768,32767,-1,0,1])),
            'ControllerGlobalBytes':('global-byte/0056',dict(byte_values=[0,255,31,64],parameters_i16=[-32768,32767])),
            'ControllerSceneBytes':('scene-byte/0060',dict(value=255)),
            'ControllerPartySelectors':('party-selector/0063',{'party_selector':7}),
            'ControllerFlagBits':('flag-bit/0065',{'bit':31}),
        }
        self.p.overrides[OWNER]={family:dict(source_record_sha256=source_hash,entries={root+'/'+suffix:value}) for family,(suffix,value) in fields.items()}
        expected=bytearray(man)
        expected[62:64]=b'\x6f\xff';expected[70]=255
        expected[73:80]=bytes.fromhex('01010002000300')
        expected[82:114]=b''.join(word.to_bytes(2,'little',signed=True) for word in range(1,17))
        expected[116:123]=bytes.fromhex('ff0080ff7fffff');expected[125:131]=bytes.fromhex('0080ff7fffff');expected[133:143]=bytes.fromhex('0080ff7fffff00000100');expected[145:153]=bytes.fromhex('00ff1f400080ff7f');expected[155]=255;expected[157]=0x2f;expected[159]=255;expected[161:163]=b'\x9f\xff'
        with patch('sdk.controller_selector_build.load_controller_system_flag_context',return_value=ctx):
            result,audit=compose(self.p,'scene://fixture',man,man)
        self.assertEqual(result,bytes(expected));self.assertEqual(len(audit),12)
        triplet=next(r for r in audit if r['field']=='script.party_selector')
        self.assertEqual(triplet['party_selector_id'],root+'/party-selector/0063')
        self.assertEqual(triplet['scope'],'controller-party-selector-only')
        from sdk.build import build_report,package_change_kinds
        report=build_report(dict(edits=[dict(triplet,scene='fixture')],validation={},overlays=[]))
        self.assertEqual(report['changes'][0]['after'],{'party_selector':7})
        self.assertEqual(report['changes'][0]['asset_id'],triplet['party_selector_id'])
        self.assertEqual(package_change_kinds([triplet]),['controller party selector'])

    def test_all_bit_opcodes_headers_masks_have_literal_one_byte_delivery(self):
        for opcode in range(0x2b,0x34):
            for extended in (False,True):
                for mask in range(8):
                    with self.subTest(opcode=opcode,extended=extended,mask=mask):
                        instruction=bytes([opcode|128,77]) if extended else bytes([opcode])
                        script=instruction+bytes([(mask<<5)|2])+b'\x26'+((-len(instruction)-2)&65535).to_bytes(2,'little')
                        src,man=source(script);ctx=ControllerSystemFlagAuthoringContext(src);value=15 if opcode<=0x2d else 31
                        self.p.overrides[OWNER]={'ControllerFlagBits':dict(source_record_sha256=sha256(src.verified_record(OWNER)[1]).hexdigest(),entries={ID:{'bit':value}})}
                        with patch('sdk.controller_selector_build.load_controller_system_flag_context',return_value=ctx):
                            result,audit=compose(self.p,'scene://fixture',man,man)
                        at=57+5+len(instruction);literal=bytearray(man);literal[at]=(mask<<5)|value
                        self.assertEqual(result,bytes(literal));self.assertEqual(len(audit),1);self.assertEqual(audit[0]['preserved_bits'],mask<<5);self.assertEqual(audit[0]['target_context'],77 if extended else None)
