import struct
import unittest
from importer.streaming_man import streaming_chunks
from importer.core import ImportError
from importer.streaming_man import replace_streaming_payload
from hashlib import sha256


class StreamingChunks(unittest.TestCase):
    def test_man_growth_preserves_following_chunk_and_opaque_tail(self):
        from importer.streaming_man import grow_streaming_man
        from test_importer_dialogue_authoring import fixture
        _, man = fixture()
        man += bytes(-len(man) % 4)
        prefix = struct.pack('<I', (2 << 24) | 4) + b'tmd!'
        suffix = struct.pack('<I', (5 << 24) | 4) + b'pose' + bytes(4) + b'opaque-tail'
        source = prefix + struct.pack('<I', (3 << 24) | len(man)) + man + suffix
        candidate = man + bytes(8)
        result, audit = grow_streaming_man(source, sha256(source).hexdigest(), len(prefix), sha256(man).hexdigest(), candidate)
        self.assertEqual(result[:len(prefix)], prefix)
        self.assertEqual(result[len(prefix) + 4:len(prefix) + 4 + len(candidate)], candidate)
        self.assertEqual(result[len(prefix) + 4 + len(candidate):], suffix)
        self.assertEqual(audit['growth_bytes'], 8)
        self.assertEqual(audit['relocated_chunks'][0]['after'] - audit['relocated_chunks'][0]['before'], 8)
        for bad in (man[:-4], man + b'x', b'bad!'):
            with self.assertRaises(ImportError):
                grow_streaming_man(source, sha256(source).hexdigest(), len(prefix), sha256(man).hexdigest(), bad)
        with self.assertRaisesRegex(ImportError, 'preimage'):
            grow_streaming_man(source, sha256(source).hexdigest(), len(prefix), '0'*64, candidate)
        with self.assertRaisesRegex(ImportError, 'structural MAN'):
            grow_streaming_man(source, sha256(source).hexdigest(), 0, sha256(man).hexdigest(), candidate)

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
