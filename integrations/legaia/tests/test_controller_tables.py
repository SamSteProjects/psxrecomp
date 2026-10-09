import unittest
from hashlib import sha256
from importer.core import ImportError, decompress_lzs
from importer.controller_tables import ControllerTableCopyAuthoringContext, validate_table_copy_values
from importer.controller_system_flags import ControllerRecordSource
from importer.man_layout import read_man_layout
from importer.serialization import compress_lzs, serialize_man_decoded
from test_controller_branches import source, OWNER

ID='script://fixture/controllers/man-p1/0000/table-copy/0005'
VALUES={'signed_words':[-32768,32767,-1,0]*4}
encode=lambda words:b''.join(n.to_bytes(2,'little',signed=True) for n in words)


class ControllerTables(unittest.TestCase):
    def test_complete_literal_man_extrema_multiple_targets_and_compression(self):
        for header in (b'\x4c',b'\xcc\x07'):
            script=header+b'\x9e'+encode(list(range(16)))
            second=5+len(script);script+=header+b'\x9e'+encode(list(range(-16,0)))
            script+=b'\x26'+((-len(script)-1)&65535).to_bytes(2,'little')
            src,man=source(script)
            for compression in ('none','lzs'):
                ctx=ControllerTableCopyAuthoringContext(src if compression=='none' else
                    ControllerRecordSource('fixture',man,compress_lzs(man),{},compression='lzs'))
                options=ctx.options(OWNER);self.assertEqual(len(options['targets']),2)
                self.assertEqual(ctx.patch({t['semantic_id']:t['values'] for t in options['targets']}),(man,[]))
                edits={ID:VALUES,ID[:-4]+f'{second:04x}':{'signed_words':[0]*16}}
                changed,audit=ctx.patch(edits);expected=bytearray(man)
                for pc,values in [(5,VALUES),(second,{'signed_words':[0]*16})]:
                    at=57+pc+len(header)+1;expected[at:at+32]=encode(values['signed_words'])
                self.assertEqual(changed,bytes(expected));self.assertEqual(ctx._man,man)
                self.assertEqual(read_man_layout(changed),read_man_layout(man))
                self.assertEqual([r['byte_length'] for r in audit],[32,32])
                self.assertEqual(audit[0]['source_record_sha256'],sha256(man[57:-18]).hexdigest())
                self.assertEqual(audit[0]['source_decoded_man_sha256'],sha256(man).hexdigest())
                self.assertEqual(audit[0]['before_values'],options['targets'][0]['values'])
                self.assertEqual(audit[0]['after_values'],VALUES)
                encoded,_=serialize_man_decoded(compress_lzs(man),len(man),changed,'fixture')
                self.assertEqual(decompress_lzs(encoded,len(man))[0],changed)
                options['targets'][0]['values']['signed_words'][0]=999
                self.assertEqual(ctx.options(OWNER)['targets'][0]['values']['signed_words'][0],0)

    def test_invalid_domains_owners_pcs_and_original_source_refuse(self):
        src,man=source(b'\x4c\x9e'+bytes(32)+b'\x26\xdd\xff');ctx=ControllerTableCopyAuthoringContext(src)
        for invalid in (True,-32769,32768,1.0,'1',None):
            with self.assertRaises(ImportError):validate_table_copy_values({'signed_words':[invalid]+[0]*15})
        for values in ({},{'signed_words':[0]*15},{'signed_words':[0]*17},{'signed_words':tuple([0]*16)},dict(VALUES,selector=1)):
            with self.assertRaises(ImportError):ctx.patch({ID:values})
        for owner in (OWNER.replace('fixture','foreign'),OWNER.replace('/controllers/','/actors/'),OWNER.replace('/0000','/0001')):
            with self.assertRaises(ImportError):ctx.options(owner)
            with self.assertRaises(ImportError):ctx.patch({owner.replace('scene://','script://')+'/table-copy/0005':VALUES})
        for pc in ('0006','0007','0027','ffff'):
            with self.assertRaises(ImportError):ctx.patch({ID[:-4]+pc:VALUES})
        with self.assertRaises(ImportError):ctx.patch({ID:VALUES},original=man+b'x')
        with self.assertRaises(ImportError):ControllerTableCopyAuthoringContext(object())

    def test_partial_truncated_paths_and_other_menu_forms_refuse(self):
        for script in (b'\x4c\x9e'+bytes(32)+b'\x4c\x93',b'\x4c\x9e'+bytes(31)):
            src,_=source(script);ctx=ControllerTableCopyAuthoringContext(src)
            self.assertFalse(ctx.options(OWNER)['supported'])
            with self.assertRaises(ImportError):ctx.patch({ID:VALUES})
        for script in (b'\x4c\x90\x00'+bytes(6)+b'\x26\xf6\xff',b'\x4c\x9f\x26\xfd\xff'):
            src,_=source(script);ctx=ControllerTableCopyAuthoringContext(src)
            self.assertFalse(ctx.options(OWNER)['inspection']['stops'])
            self.assertFalse(ctx.options(OWNER)['supported'])
            with self.assertRaises(ImportError):ctx.patch({ID:VALUES})
