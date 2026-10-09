"""Exact controller operand changes preserve complete native MAN ownership."""
import unittest
from importer.core import ImportError, decompress_lzs
from importer.controller_global_bytes import ControllerGlobalByteAuthoringContext, validate_global_byte_values
from importer.controller_system_flags import ControllerRecordSource
from importer.serialization import compress_lzs
from importer.man_layout import read_man_layout
from importer.script_inspection import inspect_record
from test_controller_branches import source, OWNER

ID = 'script://fixture/controllers/man-p1/0000/global-byte/0005'
VALUES = dict(byte_values=[0, 255, 31, 64], parameters_i16=[-32768, 32767])

class ControllerGlobalBytes(unittest.TestCase):
    def test_all_subops_headers_carriers_literal_full_man_and_detachment(self):
        destinations = {3:'0x8007B618',4:'0x8007B614',5:'0x8007B60C',6:'0x8007B610'}
        for sub in range(3, 7):
            for header in (b'\x43', b'\xc3\xf8'):
                script = header+bytes([sub])+bytes(8)
                script += b'\x26'+((-len(script)-1)&65535).to_bytes(2,'little')
                src, man = source(script)
                for compression in ('none','lzs'):
                    ctx = ControllerGlobalByteAuthoringContext(src if compression=='none' else ControllerRecordSource('fixture',man,compress_lzs(man),{},compression='lzs'))
                    target = ctx.options(OWNER)['targets'][0]
                    self.assertEqual(target['values'],dict(byte_values=[0]*4,parameters_i16=[0]*2))
                    self.assertEqual(ctx.patch({ID:target['values']}),(man,[]))
                    for values in (VALUES,dict(byte_values=[255,0,64,31],parameters_i16=[32767,-32768])):
                        result,audit = ctx.patch({ID:values})
                        at=57+5+len(header)+1
                        expected=bytearray(man)
                        expected[at:at+8]=bytes(values['byte_values'])+b''.join(w.to_bytes(2,'little',signed=True) for w in values['parameters_i16'])
                        self.assertEqual(result,bytes(expected));self.assertEqual(ctx._man,man)
                        self.assertEqual(read_man_layout(result),read_man_layout(man))
                        self.assertEqual(decompress_lzs(compress_lzs(result),len(result))[0],result)
                        self.assertEqual(audit[0]['byte_length'],8);self.assertEqual(audit[0]['after_values'],values)
                        self.assertEqual(audit[0]['sub_op'],sub)
                    target['values']['byte_values'][0]=42
                    target['values']['parameters_i16'][0]=42
                    self.assertEqual(ctx.options(OWNER)['targets'][0]['values'],dict(byte_values=[0]*4,parameters_i16=[0]*2))
                    node=ctx.options(OWNER)['inspection']['instructions'][0]
                    self.assertEqual(node['operands']['native_destination'],destinations[sub])
                    self.assertEqual(node['operands']['runtime_effect'],'not_evaluated')

    def test_domains_and_source_owner_guards(self):
        script=b'\x43\x03'+bytes(8)+b'\x26\xf5\xff';src,man=source(script)
        ctx=ControllerGlobalByteAuthoringContext(src)
        for key,bad_values in [('byte_values',[True,-1,256,1.0,'1',None]),('parameters_i16',[True,-32769,32768,1.0,'1',None])]:
            for bad in bad_values:
                value=dict(byte_values=[0]*4,parameters_i16=[0]*2);value[key][0]=bad
                with self.assertRaises(ImportError):validate_global_byte_values(value)
        for value in ({},None,dict(VALUES,extra=0),dict(byte_values=[0]*3,parameters_i16=[0]*2),dict(byte_values=[0]*4,parameters_i16=[0]*3)):
            with self.assertRaises(ImportError):ctx.patch({ID:value})
        for identity in (ID.replace('fixture','foreign'),ID.replace('/global-byte/','/five-word/'),ID[:-4]+'0006',ID.replace('/controllers/','/actors/')):
            with self.assertRaises(ImportError):ctx.patch({identity:VALUES})
        with self.assertRaises(ImportError):ctx.patch({ID:VALUES},original=man+b'x')
        for size in range(2,10):
            partial,_=source(script[:size]);other=ControllerGlobalByteAuthoringContext(partial)
            self.assertFalse(other.options(OWNER)['supported'])
            with self.assertRaises(ImportError):other.patch({ID:VALUES})

    def test_opaque_unvisited_tail_preserved_and_reached_unknown_refused(self):
        base=b'\x43\x03'+bytes(8)+b'\x26\xf5\xff'
        src,man=source(base+b'\x43\x12\x1fOpaque\0')
        ctx=ControllerGlobalByteAuthoringContext(src);options=ctx.options(OWNER)
        self.assertTrue(options['supported']);self.assertEqual(options['inspection']['status'],'partial')
        result,_=ctx.patch({ID:VALUES});expected=bytearray(man);expected[64:72]=b'\x00\xff\x1f\x40\x00\x80\xff\x7f'
        self.assertEqual(result,bytes(expected))
        self.assertEqual(inspect_record(result[57:-18],5)['opaque_regions'],options['inspection']['opaque_regions'])
        partial,_=source(b'\x43\x03'+bytes(8)+b'\x43\x12')
        ctx=ControllerGlobalByteAuthoringContext(partial)
        self.assertFalse(ctx.options(OWNER)['supported'])
        with self.assertRaises(ImportError):ctx.patch({ID:VALUES})

    def test_multi_request_composition_remains_in_source_order(self):
        script=b'\x43\x03'+bytes(8)+b'\xc3\x07\x06'+bytes(8)
        script+=b'\x26'+((-len(script)-1)&65535).to_bytes(2,'little')
        src,man=source(script);ctx=ControllerGlobalByteAuthoringContext(src)
        targets=ctx.options(OWNER)['targets'];self.assertEqual(len(targets),2)
        result,audit=ctx.patch({targets[1]['semantic_id']:VALUES,targets[0]['semantic_id']:VALUES})
        expected=bytearray(man)
        literal=b'\x00\xff\x1f\x40\x00\x80\xff\x7f'
        expected[64:72]=literal;expected[75:83]=literal
        self.assertEqual(result,bytes(expected));self.assertEqual([a['decoded_byte_offset'] for a in audit],[64,75])
