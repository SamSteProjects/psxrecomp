import struct
import unittest
from importer.streaming_man import streaming_chunks
from importer.core import ImportError
from importer.streaming_man import replace_streaming_payload
from hashlib import sha256


class StreamingChunks(unittest.TestCase):
    def test_replacement_preserves_neighbors_and_rejects_growth_or_wrong_source(self):
        source=struct.pack('<I',(3<<24)|8)+b'abcdefgh'+struct.pack('<I',(5<<24)|4)+b'pose'+bytes(4)+b'padding'
        digest=sha256(source).hexdigest();payload_hash=sha256(b'abcdefgh').hexdigest()
        result,audit=replace_streaming_payload(source,digest,0,payload_hash,b'ABCDEFGH')
        self.assertEqual(result[:4],source[:4]);self.assertEqual(result[12:],source[12:])
        self.assertEqual(result[4:12],b'ABCDEFGH')
        self.assertEqual(audit['payload_offset'],4)
        with self.assertRaisesRegex(ImportError,'unchanged'):
            replace_streaming_payload(source,digest,0,payload_hash,b'longer-payload')
        with self.assertRaisesRegex(ImportError,'preimage'):
            replace_streaming_payload(source,digest,0,'0'*64,b'ABCDEFGH')
        with self.assertRaisesRegex(ImportError,'source hash'):
            replace_streaming_payload(source,'0'*64,0,payload_hash,b'ABCDEFGH')

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
