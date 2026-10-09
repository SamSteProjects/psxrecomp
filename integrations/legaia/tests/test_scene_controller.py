import struct
import unittest
from unittest.mock import patch
from importer.core import ImportError
from importer.scene_controller import controller_record, load_controller_asset_catalog
from sdk.project import AssetDatabase
from sdk.inspector_schema import inspector_schema


def source():
    man = bytearray(49+24+18)
    struct.pack_into('<hhh',man,34,1,1,0)
    man[40:43]=(24).to_bytes(3,'little')
    man[43:46]=(0).to_bytes(3,'little');man[46:49]=(8).to_bytes(3,'little')
    man[49+8+5:49+8+9]=bytes([0x21,0x26,0xfe,0xff])
    return bytes(man)


class SceneController(unittest.TestCase):
    def test_catalog_keeps_source_identity_without_instruction_payload(self):
        report = dict(semantic_id='script://fixture/controllers/man-p1/0000',
            scene_id='scene://fixture', source_record={'sha256':'a'*64},
            entry_pc=5, record={'local_count':0,'raw_hex':'00'}, status='partial',
            instructions=[{'raw_hex':'ff'}], dialogues=[], flag_references=[], flag_reference_count=0, reference_commit='b'*40,
            limitations=['Runtime execution remains unverified.'])
        with patch('importer.scene_controller.inspect_scene_controller', return_value=report):
            catalog=load_controller_asset_catalog(None,'fixture')
        asset=catalog['assets'][0]
        self.assertEqual(asset['dependencies'],['scene://fixture'])
        self.assertEqual(asset['entry_pc'],5)
        self.assertTrue(asset['read_only'])
        self.assertNotIn('raw_hex',str(asset))
        database=AssetDatabase()
        registered=database.register_resources('scene://fixture','key',catalog['assets'],catalog['limitations'])
        self.assertEqual(registered['records'][0]['kind'],'controller')
        registered['records'][0]['source_record']['sha256']='changed'
        self.assertEqual(database.resource_catalogs['scene://fixture']['records'][0]['source_record']['sha256'],'a'*64)
        schema=inspector_schema()['components']['AssetController']
        self.assertEqual(schema['actions'][0]['id'],'inspect-asset-controller')
        self.assertFalse(schema['actions'][0].get('requires_edit',False))

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
