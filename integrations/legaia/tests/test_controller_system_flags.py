import struct
import unittest
from importer.core import ImportError, decompress_lzs
from importer.controller_system_flags import ControllerRecordSource, ControllerSystemFlagAuthoringContext
from importer.system_flag_authoring import SystemFlagAuthoringContext
from importer.serialization import compress_lzs, serialize_man_decoded
from importer.man_layout import read_man_layout

OWNER='scene://fixture/controllers/man-p1/0000'
ID='script://fixture/controllers/man-p1/0000/system-flag/0005'


def fixture(test=False):
    record=bytes(5)+(b'\x71\x23\x02\0\x26\xfb\xff' if test else b'\x51\x23\x26\xfd\xff')
    man=bytearray(49+8+len(record)+18)
    struct.pack_into('<hhh',man,34,1,1,0)
    man[40:43]=(8+len(record)).to_bytes(3,'little')
    man[46:49]=(8).to_bytes(3,'little')
    man[57:57+len(record)]=record
    return bytes(man)


def context(man):
    return ControllerSystemFlagAuthoringContext(ControllerRecordSource('fixture',man,man,{},compression='none'))


class ControllerSelectors(unittest.TestCase):
    def test_exact_controller_identity_and_equal_span_serialization(self):
        for test in (False,True):
            original=fixture(test);ctx=context(original);options=ctx.options(OWNER)
            self.assertEqual([t['semantic_id'] for t in options['targets']],[ID])
            changed,audit=ctx.patch({ID:{'index':4095}},original=original)
            expected=bytearray(original);expected[62:64]=bytes.fromhex('7fff' if test else '5fff')
            self.assertEqual(changed,bytes(expected));self.assertEqual(len(audit),1)
            self.assertEqual(audit[0]['owner_id'],OWNER)
            self.assertEqual(read_man_layout(original),read_man_layout(changed))
            self.assertEqual(ctx._source.verified_record(OWNER)[1],original[57:-18])
            stream=compress_lzs(original)
            encoded,_=serialize_man_decoded(stream,len(original),changed,'fixture')
            self.assertEqual(decompress_lzs(encoded,len(original))[0],changed)

    def test_foreign_owner_and_baseline_refuse(self):
        original=fixture();ctx=context(original)
        for owner in ('scene://fixture/actors/man-p1/0000','scene://fixture/scripts/man-p2/0000','scene://other/controllers/man-p1/0000','scene://fixture/controllers/man-p1/0001'):
            with self.assertRaises(ImportError):ctx.options(owner)
            with self.assertRaises(ImportError):ctx.patch({owner.replace('scene://','script://')+'/system-flag/0005':{'index':1}})
        with self.assertRaises(ImportError):ctx.patch({ID:{'index':1}},original=original+b'0')
        with self.assertRaises(ImportError):SystemFlagAuthoringContext(ctx._source).patch({ID:{'index':1}})
        with self.assertRaises(ImportError):ControllerSystemFlagAuthoringContext(object())

    def test_noop_and_appended_preimage_are_qualified(self):
        original=fixture();ctx=context(original)
        self.assertEqual(ctx.patch({ID:{'index':291}}),(original,[]))
        changed,audit=ctx.patch_appended(original,{ID:{'index':292}})
        self.assertEqual(changed[62:64],bytes.fromhex('5124'));self.assertEqual(len(audit),1)
        forged=bytearray(original);forged[63]=0x24
        for index in (291,292):
            with self.assertRaises(ImportError):ctx.patch_appended(bytes(forged),{ID:{'index':index}})

    def test_source_parity_alias_and_prefix_refuse(self):
        original=fixture()
        with self.assertRaises(ImportError):ControllerRecordSource('fixture',original,original+b'0',{},compression='none')
        for change in ('alias','prefix','outside'):
            man=bytearray(original)
            if change=='alias':man[46:49]=bytes(3)
            elif change=='prefix':man[57]=255
            else:man[46:49]=(1000).to_bytes(3,'little')
            with self.assertRaises(ImportError):context(bytes(man))

    def test_unknown_path_and_invalid_selector_refuse(self):
        man=bytearray(fixture());man[64]=0x2a
        ctx=context(bytes(man));self.assertFalse(ctx.options(OWNER)['supported'])
        with self.assertRaises(ImportError):ctx.patch({ID:{'index':1}})
        ctx=context(fixture())
        for value in ({'index':True},{'index':4096},{'bit':1},{'index':-1}):
            with self.assertRaises(ImportError):ctx.patch({ID:value})
