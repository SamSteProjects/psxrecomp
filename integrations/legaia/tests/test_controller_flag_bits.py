import unittest
from copy import deepcopy
from importer.core import ImportError,decompress_lzs
from importer.flag_authoring import _target
from importer.controller_flag_bits import ControllerFlagBitAuthoringContext
from importer.controller_system_flags import ControllerRecordSource
from importer.serialization import compress_lzs
from importer.script_inspection import inspect_record
from test_controller_branches import source,OWNER

ID='script://fixture/controllers/man-p1/0000/flag-bit/0005'
def script(opcode,upper=0,extended=False,bit=2):
    header=bytes((opcode|128,7)) if extended else bytes((opcode,))
    return header+bytes((upper|bit,))+b'\x26'+((-len(header)-2)&65535).to_bytes(2,'little')

class ControllerFlagBits(unittest.TestCase):
    def test_banks_dispatch_high_bits_and_carriers(self):
        for opcode in range(0x2b,0x34):
            for extended in [False,True]:
                for upper in range(0,256,32):
                    src,man=source(script(opcode,upper,extended))
                    for compression in ['none','lzs']:
                        c=ControllerFlagBitAuthoringContext(src if compression=='none' else ControllerRecordSource('fixture',man,compress_lzs(man),{},compression='lzs'))
                        t=c.options(OWNER)['targets'][0];at=64 if extended else 63
                        self.assertEqual(t['bit_mask'],31);self.assertEqual(t['preserved_bits'],upper);self.assertEqual(c.patch({ID:{'bit':2}}),(man,[]))
                        actual,audit=c.patch({ID:{'bit':3}});literal=bytearray(man);literal[at]=upper|3
                        self.assertEqual(actual,bytes(literal));self.assertEqual(audit[0]['decoded_byte_offset'],at);self.assertEqual(audit[0]['preserved_bits'],upper);self.assertEqual(c._man,man)
                        self.assertEqual(decompress_lzs(compress_lzs(actual),len(actual))[0],actual)

    def test_side_effects_domains_owners_and_partial_paths_refuse(self):
        for opcode,before,after in [(0x2b,16,2),(0x2b,2,16),(0x31,8,2),(0x31,2,8),(0x32,10,2),(0x32,2,10)]:
            src,_=source(script(opcode,bit=before));c=ControllerFlagBitAuthoringContext(src)
            with self.assertRaises(ImportError):c.patch({ID:{'bit':after}})
        src,man=source(script(0x2e));c=ControllerFlagBitAuthoringContext(src)
        for values in [{},{'bit':True},{'bit':-1},{'bit':32},{'bit':'2'},{'bit':2,'extra':0}]:
            with self.assertRaises(ImportError):c.patch({ID:values})
        for identity in [ID.replace('fixture','foreign'),ID.replace('/controllers/','/actors/'),ID.replace('/0000/','/0001/'),ID[:-4]+'0006']:
            with self.assertRaises(ImportError):c.patch({identity:{'bit':3}})
        with self.assertRaises(ImportError):c.patch({ID:{'bit':3}},original=man+b'x')
        with self.assertRaises(ImportError):ControllerFlagBitAuthoringContext(object())
        src,_=source(b'\x2e\x02\xee');c=ControllerFlagBitAuthoringContext(src);self.assertFalse(c.options(OWNER)['supported'])
        with self.assertRaises(ImportError):c.patch({ID:{'bit':3}})

    def test_decoder_contract_is_checked_against_literal_bytes(self):
        raw=b'\x2e\xe2\x26\xfd\xff';report=inspect_record(raw,0)
        for field,value in [('length',3),('target_context',7),('successors',[]),('mnemonic','CFLAG_SET')]:
            altered=deepcopy(report);altered['instructions'][0][field]=value
            with self.assertRaises(ImportError):_target(raw,0,0,report=altered)
        altered=deepcopy(report);altered['instructions'][0]['operands']['bit']=3
        with self.assertRaises(ImportError):_target(raw,0,0,report=altered)

    def test_multi_site_edits_preserve_full_man_and_sort_audits(self):
        src,man=source(b'\x2e\xe2\xb3\x07\xc3\x26\xfa\xff');c=ControllerFlagBitAuthoringContext(src);targets=c.options(OWNER)['targets']
        edits={targets[1]['semantic_id']:{'bit':4},ID:{'bit':5}};result,audit=c.patch(edits);literal=bytearray(man);literal[63]=0xe5;literal[66]=0xc4
        self.assertEqual(result,bytes(literal));self.assertEqual(c.patch(dict(reversed(list(edits.items())))),(result,audit));self.assertEqual([row['decoded_byte_offset'] for row in audit],[63,66])

    def test_rebased_record_preimages_layout_and_detached_options(self):
        src,man=source(script(0x2e,0xe0));c=ControllerFlagBitAuthoringContext(src)
        candidate=bytearray(man[:57]+b'0123'+man[57:]);candidate[40:43]=(int.from_bytes(man[40:43],'little')+4).to_bytes(3,'little');candidate[46:49]=(12).to_bytes(3,'little')
        actual,audit=c.patch_appended(bytes(candidate),{ID:{'bit':3}});literal=bytearray(candidate);literal[67]=0xe3
        self.assertEqual(actual,bytes(literal));self.assertEqual(audit[0]['source_decoded_byte_offset'],63);self.assertEqual(audit[0]['decoded_byte_offset'],67)
        for at in [66,67]:
            forged=bytearray(candidate);forged[at]^=1
            with self.assertRaises(ImportError):c.patch_appended(bytes(forged),{ID:{'bit':3}})
        detached=c.options(OWNER);detached['targets'][0]['values']['bit']=15;detached['source']['limitations'].clear()
        self.assertEqual(c.options(OWNER)['targets'][0]['values'],{'bit':2});self.assertTrue(c.options(OWNER)['source']['limitations'])
