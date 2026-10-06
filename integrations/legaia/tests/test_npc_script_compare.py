from hashlib import sha256
import unittest
from sdk.npc_script_compare import compare_records
from sdk.project import ProjectError
class ScriptComparisonTests(unittest.TestCase):
    def record(self,data,entry=2):return dict(raw_hex=data.hex(),byte_length=len(data),sha256=sha256(data).hexdigest(),script_offset=entry)
    def test_exact_relative_bytes_headers_opaque_tail_and_lengths(self):
        a=self.record(b'abcdef');b=self.record(b'aXcYef!');r=compare_records(a,b)
        self.assertEqual(r['changed_byte_count'],3);self.assertEqual(r['unchanged_common_byte_count'],4);self.assertFalse(r['script_tail_bytes_equal']);self.assertEqual(r['changes'],[dict(relative_offset=1,retail_byte=98,generated_byte=88,scope='record_header'),dict(relative_offset=3,retail_byte=100,generated_byte=89,scope='script_or_remaining_record_bytes'),dict(relative_offset=6,retail_byte=None,generated_byte=33,scope='script_or_remaining_record_bytes')])
        self.assertEqual(compare_records(a,a)['changes'],[]);self.assertTrue(compare_records(a,a)['record_bytes_equal'])
        self.assertTrue(compare_records(a,self.record(b'aXcdef'))['script_tail_bytes_equal'])
        for change in [dict(sha256='0'*64),dict(raw_hex='bad'),dict(byte_length=5),dict(script_offset=True),dict(script_offset=8)]:
            with self.assertRaises(ProjectError):compare_records(a,{**b,**change})
if __name__=='__main__':unittest.main()
