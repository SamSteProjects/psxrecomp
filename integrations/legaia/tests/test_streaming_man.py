import struct
import unittest
from importer.streaming_man import streaming_chunks
from importer.core import ImportError


class StreamingChunks(unittest.TestCase):
    def test_word_truncated_advance_and_incomplete_tail(self):
        data=struct.pack('<I',(3<<24)|5)+b'abcd'+bytes(4)
        chunks,terminated=streaming_chunks(data)
        self.assertTrue(terminated)
        self.assertEqual(chunks,[{'header_offset':0,'type_byte':3,'size':5}])
        chunks,terminated=streaming_chunks(struct.pack('<I',(3<<24)|8)+b'abcd')
        self.assertFalse(terminated);self.assertEqual(chunks,[])
        chunks,terminated=streaming_chunks(struct.pack('<I',(0xff<<24)|4)+b'abcd')
        self.assertFalse(terminated);self.assertEqual(chunks,[])
        with self.assertRaises(ImportError):streaming_chunks(b'',True)


if __name__=='__main__':unittest.main()
