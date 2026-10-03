from contextlib import nullcontext
from hashlib import sha256
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from importer.core import ImportError
from importer.model_face_removal import remove_faces
from sdk.model_reference_faces import mapping
from sdk import model_normal_users, model_vertex_users
from test_model_primitives import synthetic

class ReferenceFaceMappingTests(unittest.TestCase):
    def test_dropped_groups_and_cumulative_dense_indices(self):
        source=synthetic(((0x12,0x14),(0x14,)),count=2)
        current,removed=remove_faces(source,source,[],[dict(object_index=0,primitive_index=0),dict(object_index=0,primitive_index=1)])
        binding=dict(format='tmd-face-removal-v1',removed_faces=removed)
        self.assertEqual(mapping(source,current,binding,0),[dict(retail_index=i,current_index=None if i<2 else i-2) for i in range(4)])
        current,removed=remove_faces(source,current,removed,[dict(object_index=0,primitive_index=1)])
        binding['removed_faces']=removed
        self.assertEqual(mapping(source,current,binding,0),[dict(retail_index=i,current_index=0 if i==2 else None) for i in range(4)])
        bad=bytearray(current);bad[-1]^=1
        with self.assertRaises(ImportError):mapping(source,bytes(bad),binding,0)
        self.assertEqual(mapping(source,source,None,1),[dict(retail_index=i,current_index=i) for i in range(2)])

    def test_both_reference_layers_expose_removed_and_retained_faces(self):
        source=synthetic(((0x14,),),count=3)
        current,removed=remove_faces(source,source,[],[dict(object_index=0,primitive_index=0)])
        asset='asset://fixture/models/0';key='a'*64
        project=SimpleNamespace(mode='edit',active_scene='scene://fixture',disc_path='private',
            imports={'scene://fixture':{'assets':{'models':[{'semantic_id':asset}]}}},
            model_overrides={asset:dict(format='tmd-face-removal-v1',removed_faces=removed)},
            _model_source=lambda *args:source,read_model_replacement=lambda *args:current)
        for noun,module in [('normal',model_normal_users),('vertex',model_vertex_users)]:
            with self.subTest(noun=noun),patch(f'sdk.model_{noun}_users._disc_context',return_value=nullcontext()),patch(f'sdk.model_{noun}_users.source_key',return_value=key):
                report=module.inspect(project,asset,0,0,sha256(current).hexdigest(),key)
                self.assertEqual(report['face_mapping'],[dict(retail_index=0,current_index=None),dict(retail_index=1,current_index=0),dict(retail_index=2,current_index=1)])
                self.assertEqual({row['primitive_index'] for row in report['retail_users']},{0,1,2})
                self.assertEqual({row['primitive_index'] for row in report['current_users']},{0,1})
                self.assertTrue(report['read_only'])
