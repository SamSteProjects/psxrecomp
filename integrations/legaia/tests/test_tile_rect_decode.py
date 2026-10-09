import unittest
from importer.script_inspection import inspect_record
from importer.branch_authoring import _branch


class TileRectDecode(unittest.TestCase):
    def test_byte_bounds_values_context_and_exact_continuation(self):
        for header in (b'\x4c',b'\xcc\x07'):
            for values in ((0,0,0,0,0),(0,1,254,255,255),(255,255,0,0,128)):
                record=header+b'\x83'+bytes(values)+b'\x21\x26\xfe\xff'
                report=inspect_record(record,0);self.assertFalse(report['stops'])
                row=report['instructions'][0];end=len(header)+6
                self.assertEqual(row['mnemonic'],'FIELD_TILE_RECT_REQUEST');self.assertEqual(row['length'],end)
                self.assertEqual(row['raw_hex'],record[:end].hex());self.assertEqual(row['target_context'],7 if len(header)==2 else None)
                self.assertEqual([row['operands'][k] for k in ('column_start','row_start','column_end','row_end','value')],list(values))
                self.assertEqual(row['operands']['tile_byte_writes'],{'offset_2':values[-1],'offset_3':0})
                self.assertEqual(row['operands']['tile_binding'],'runtime_lookup_unresolved')
                self.assertNotIn('address',row['operands']);self.assertIsNone(_branch(record,row))
                self.assertEqual(row['successors'],[{'pc':end,'condition':'encoded_continuation'}])

    def test_every_truncated_prefix_and_unknown_next_byte_stop(self):
        for header in (b'\x4c',b'\xcc\x07'):
            record=header+b'\x83\x00\x01\x02\x03\xff'
            for length in range(1,len(record)):
                report=inspect_record(record[:length],0);self.assertFalse(report['instructions']);self.assertTrue(report['stops']);self.assertFalse(report['dialogues'])
            report=inspect_record(record+b'\x4c\xee',0)
            self.assertEqual(len(report['instructions']),1);self.assertEqual(report['stops'][0]['pc'],len(record));self.assertFalse(report['dialogues'])
