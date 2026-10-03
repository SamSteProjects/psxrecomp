from contextlib import nullcontext
from hashlib import sha256
from types import SimpleNamespace
import struct
import unittest
from unittest.mock import patch

from importer.core import ImportError
from importer.model_normal_references import normal_users
from importer.model_primitives import inspect_model_primitives
from sdk.model_normal_users import inspect
from sdk.project import ProjectError
from test_model_primitives import synthetic


class ModelNormalUserTests(unittest.TestCase):
    def test_flat_gouraud_unlit_and_changed_corner_ownership(self):
        flat=synthetic(((0x12,),),count=1)
        users=normal_users(flat,0,0)
        self.assertEqual(len(users),1)
        self.assertEqual(users[0]['affected_corners'],[0,1,2,3])
        self.assertEqual(users[0]['sharing'],'flat_all_corners')
        source=synthetic(((0x14,),),count=1)
        before=normal_users(source,0,0)
        self.assertEqual([row['affected_corners'] for row in before],[[0]])
        primitive=inspect_model_primitives(source)['objects'][0]['primitives'][0]
        changed=bytearray(source);struct.pack_into('<H',changed,primitive['byte_offset']+22,0)
        self.assertEqual([row['affected_corners'] for row in normal_users(bytes(changed),0,0)],[[0],[2]])
        self.assertEqual(normal_users(synthetic(((0x20,),),count=1),0,0),[])
        for obj,index in [(True,0),(0,True),(1,0),(0,4)]:
            with self.assertRaises(ImportError):normal_users(source,obj,index)
        struct.pack_into('<H',changed,primitive['byte_offset']+22,1)
        with self.assertRaises(ImportError):normal_users(bytes(changed),0,0)

    def test_source_current_layers_and_mid_read_drift(self):
        source=synthetic(((0x14,),),count=1);current=bytearray(source)
        row=inspect_model_primitives(source)['objects'][0]['primitives'][0]
        struct.pack_into('<H',current,row['byte_offset']+22,0);current=bytes(current)
        asset='asset://fixture/models/0';key='a'*64
        project=SimpleNamespace(mode='edit',active_scene='scene://fixture',disc_path='private',
            imports={'scene://fixture':{'assets':{'models':[{'semantic_id':asset}]}}},
            model_overrides={asset:{}},_model_source=lambda *args:source,
            read_model_replacement=lambda *args:current)
        with patch('sdk.model_normal_users._disc_context',return_value=nullcontext()), \
                patch('sdk.model_normal_users.source_key',return_value=key):
            result=inspect(project,asset,0,0,sha256(current).hexdigest(),key)
            self.assertEqual(len(result['retail_users']),1)
            self.assertEqual(len(result['current_users']),2)
            self.assertTrue(result['read_only']);self.assertFalse(result['gameplay_verified'])
            with self.assertRaises(ProjectError):inspect(project,asset,0,0,'0'*64,key)
        with patch('sdk.model_normal_users._disc_context',return_value=nullcontext()), \
                patch('sdk.model_normal_users.source_key',side_effect=[key,'b'*64]):
            with self.assertRaisesRegex(ProjectError,'changed while'):inspect(project,asset,0,0,sha256(current).hexdigest(),key)
