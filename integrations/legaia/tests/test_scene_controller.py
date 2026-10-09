import struct
import unittest
from importer.core import ImportError
from importer.scene_controller import controller_record


def source():
    man = bytearray(49+24+18)
    struct.pack_into('<hhh',man,34,1,1,0)
    man[40:43]=(24).to_bytes(3,'little')
    man[43:46]=(0).to_bytes(3,'little');man[46:49]=(8).to_bytes(3,'little')
    man[49+8+5:49+8+9]=bytes([0x21,0x26,0xfe,0xff])
    return bytes(man)


class SceneController(unittest.TestCase):
    def test_controller_span_excludes_other_records_and_sections(self):
        man=source();offset,record,entry=controller_record(man,'fixture')
        self.assertEqual((offset,len(record),entry),(57,16,5))
        self.assertEqual(record,man[57:73])

    def test_aliased_outside_and_truncated_prefix_refuse(self):
        for offset in [0,24,100]:
            man=bytearray(source());man[46:49]=offset.to_bytes(3,'little')
            with self.assertRaises(ImportError):controller_record(bytes(man),'fixture')
        man=bytearray(source());man[57]=6
        with self.assertRaisesRegex(ImportError,'prefix or script entry'):controller_record(bytes(man),'fixture')

    def test_missing_controller_refuses(self):
        man=bytearray(source());struct.pack_into('<h',man,36,0)
        with self.assertRaises(ImportError):controller_record(bytes(man),'fixture')
