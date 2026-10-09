"""Controller-only native ownership and independent target-word readback."""
import struct
import unittest
from hashlib import sha256
from importer.core import ImportError,decompress_lzs
from importer.controller_system_flags import ControllerRecordSource,ControllerSystemFlagAuthoringContext
from importer.controller_branches import ControllerBranchAuthoringContext
from importer.branch_authoring import BranchAuthoringContext
from importer.man_layout import read_man_layout
from importer.serialization import compress_lzs,serialize_man_decoded
from test_branch_authoring import family_script

OWNER='scene://fixture/controllers/man-p1/0000'
ID='script://fixture/controllers/man-p1/0000/branch/0005'


def source(script):
    record=bytes(5)+script
    man=bytearray(49+8+len(record)+18)
    struct.pack_into('<hhh',man,34,1,1,0)
    man[40:43]=(8+len(record)).to_bytes(3,'little');man[46:49]=(8).to_bytes(3,'little')
    man[57:57+len(record)]=record
    man=bytes(man)
    return ControllerRecordSource('fixture',man,man,{},compression='none'),man


class ControllerBranches(unittest.TestCase):
    def test_existing_branch_families_keep_full_man_and_literal_target_word(self):
        for family in ['JMP_REL','COND_JMP','BBOX_TEST','FLAG_WORD_BRANCH','SYSFLAG_TEST']:
            for extended in [False,True]:
                script,operand,target,closing=family_script(family,extended)
                src,man=source(script);ctx=ControllerBranchAuthoringContext(src)
                options=ctx.options(OWNER)
                if family=='SYSFLAG_TEST' and extended:
                    self.assertFalse(options['supported']);continue
                row=next(t for t in options['targets'] if t['pc']==5)
                changed,audit=ctx.patch({ID:{'target_pc':closing}})
                expected=bytearray(man);expected[57+operand:59+operand]=((closing-operand)&65535).to_bytes(2,'little')
                self.assertEqual(changed,bytes(expected));self.assertEqual(read_man_layout(man),read_man_layout(changed))
                self.assertEqual(audit[0]['owner_id'],OWNER);self.assertEqual(audit[0]['source_record_sha256'],sha256(man[57:-18]).hexdigest())
                self.assertFalse(ctx.inspect_owner(OWNER,changed)['stops']);self.assertEqual(ctx._man,man)
                self.assertEqual(ctx.patch({ID:row['values']}),(man,[]))
                encoded,_=serialize_man_decoded(compress_lzs(man),len(man),changed,'fixture')
                self.assertEqual(decompress_lzs(encoded,len(man))[0],changed)

    def test_ownership_source_parity_and_invalid_targets_refuse(self):
        src,man=source(b'\x26\x02\0\x21\x26\xfb\xff');ctx=ControllerBranchAuthoringContext(src)
        for owner in ['scene://fixture/actors/man-p1/0000','scene://fixture/scripts/man-p2/0000','scene://other/controllers/man-p1/0000','scene://fixture/controllers/man-p1/0001']:
            with self.assertRaises(ImportError):ctx.options(owner)
            with self.assertRaises(ImportError):ctx.patch({owner.replace('scene://','script://')+'/branch/0005':{'target_pc':5}})
        with self.assertRaises(ImportError):BranchAuthoringContext(src).options(OWNER)
        with self.assertRaises(ImportError):BranchAuthoringContext(src).patch({ID:{'target_pc':5}})
        with self.assertRaises(ImportError):ControllerBranchAuthoringContext(object())
        for value in [True,6,7,32768,-1]:
            with self.assertRaises(ImportError):ctx.patch({ID:{'target_pc':value}})
        with self.assertRaises(ImportError):ctx.patch({ID:{'target_pc':5}},original=man+b'0')
        with self.assertRaises(ImportError):ControllerRecordSource('fixture',man,man+b'0',{},compression='none')

    def test_selector_composition_keeps_test_operation_and_branch_preimages(self):
        script,operand,target,closing=family_script('SYSFLAG_TEST');src,man=source(script)
        selector='script://fixture/controllers/man-p1/0000/system-flag/0005';edits={selector:{'index':4095}}
        selected,_=ControllerSystemFlagAuthoringContext(src).patch(edits)
        ctx=ControllerBranchAuthoringContext(src,system_selectors=edits)
        changed,audit=ctx.patch_composed(selected,{ID:{'target_pc':closing}})
        expected=bytearray(man);expected[62:64]=b'\x7f\xff';expected[57+operand:59+operand]=((closing-operand)&65535).to_bytes(2,'little')
        self.assertEqual(changed,bytes(expected));self.assertEqual(changed[62]&0xf0,0x70)
        self.assertEqual(audit[0]['effective_record_sha256'],sha256(selected[57:-18]).hexdigest())
        self.assertEqual(ctx.patch({ID:{'target_pc':closing}})[0][62:64],man[62:64])
        with self.assertRaises(ImportError):ControllerBranchAuthoringContext(src).patch_composed(selected,{ID:{'target_pc':closing}})
        forged=bytearray(selected);forged[57+operand]^=1
        with self.assertRaises(ImportError):ctx.patch_composed(bytes(forged),{ID:{'target_pc':closing}})

    def test_rebased_appended_spans_unknown_paths_and_detached_reports(self):
        src,man=source(b'\x26\x02\0\x21\x26\xfb\xff');ctx=ControllerBranchAuthoringContext(src)
        candidate=bytearray(man[:57]+b'0123'+man[57:]);candidate[40:43]=(int.from_bytes(man[40:43],'little')+4).to_bytes(3,'little');candidate[46:49]=(12).to_bytes(3,'little')
        changed,audit=ctx.patch_appended(bytes(candidate),{ID:{'target_pc':9}})
        expected=bytearray(candidate);expected[67:69]=b'\x03\0'
        self.assertEqual(changed,bytes(expected));self.assertEqual(audit[0]['source_decoded_byte_offset'],63);self.assertEqual(audit[0]['decoded_byte_offset'],67)
        self.assertEqual(audit[0]['appended_man_sha256'],sha256(candidate).hexdigest())
        options=ctx.options(OWNER);options['targets'].clear();self.assertTrue(ctx.options(OWNER)['targets'])
        src,_=source(b'\x2a');bad=ControllerBranchAuthoringContext(src);self.assertFalse(bad.options(OWNER)['supported'])
        with self.assertRaises(ImportError):bad.patch({ID:{'target_pc':5}})
