from hashlib import sha256
from pathlib import Path
from copy import deepcopy
import struct,tempfile,unittest
from unittest.mock import patch
from importer.core import ImportError
from importer.model_face_removal import remove_faces,restore_faces,qualify_face_removal
from importer.model_materials import patch_model_materials,inspect_model_materials
from importer.assets import decode_tmd
from sdk.project import ProjectService,ProjectError
from sdk.model_face_removal import review
from test_model_primitives import synthetic

class FaceRestorationTests(unittest.TestCase):
    def test_partial_and_dropped_group_restoration_preserve_owned_fields(self):
        original=synthetic(((0x22,0x14),(0x22,)),count=2)
        removed=[dict(object_index=0,primitive_index=0),dict(object_index=0,primitive_index=1),dict(object_index=1,primitive_index=0)]
        current,removed=remove_faces(original,original,[],removed)
        current=patch_model_materials(current,sha256(current).hexdigest(),[dict(kind='primitive',object_index=0,primitive_index=0,values={'page_column':3}),dict(kind='group',object_index=0,group_index=0,values={'semi_transparent':False})])[0]
        vertex=12+struct.unpack_from('<I',current,12)[0];edited=bytearray(current);struct.pack_into('<h',edited,vertex,7);current=bytes(edited)
        candidate,left=restore_faces(original,current,removed,[dict(object_index=0,primitive_index=0)])
        self.assertEqual(left,[dict(object_index=0,primitive_index=1),dict(object_index=1,primitive_index=0)])
        self.assertEqual(len(decode_tmd(candidate)['triangles']),len(decode_tmd(current)['triangles'])+2)
        groups=inspect_model_materials(candidate)['objects'][0]['groups'];self.assertTrue(groups[0]['semi_transparent']);self.assertFalse(groups[1]['semi_transparent'])
        result,remaining=restore_faces(original,candidate,left,left);self.assertEqual(remaining,[])
        expected=bytearray(original);struct.pack_into('<h',expected,vertex,7)
        group=inspect_model_materials(original)['objects'][0]['groups'][1];expected[group['byte_offset']+7]&=~2
        at=group['primitives'][0]['byte_offset'];struct.pack_into('<H',expected,at+6,(struct.unpack_from('<H',original,at+6)[0]&~15)|3)
        self.assertEqual(result,bytes(expected));qualify_face_removal(original,sha256(original).hexdigest(),result,[])
        for invalid in [[dict(object_index=0,primitive_index=2)],left+left,[dict(object_index=True,primitive_index=0)]]:
            with self.assertRaises(ImportError):restore_faces(original,candidate,left,invalid)

    def project(self,typed=False):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);p=ProjectService(Path(temp.name));p.active_scene='scene://fixture';asset='asset://fixture/model/0'
        original=synthetic(((0x22,),),count=2);current,removed=remove_faces(original,original,[],[dict(object_index=0,primitive_index=0)])
        if typed:
            data=bytearray(current);at=12+struct.unpack_from('<I',current,12)[0];struct.pack_into('<h',data,at,7);current=bytes(data)
        p._model_source=lambda *args:original
        binding=dict(format='tmd-face-removal-v1',source_scene_id=p.active_scene,source_sha256=sha256(original).hexdigest(),asset_sha256=sha256(current).hexdigest(),byte_length=len(current),removed_faces=removed)
        p.model_overrides[asset]=binding;path=p.root/'Authored'/'Models'/(binding['asset_sha256']+'.tmd');path.parent.mkdir(parents=True);path.write_bytes(current)
        return p,asset,original,current,removed

    def test_all_restored_clear_or_typed_binding_and_exact_history(self):
        key='a'*64
        for typed in [False,True]:
            with self.subTest(typed=typed):
                p,asset,original,current,removed=self.project(typed)
                with patch('sdk.scene_preview.source_key',return_value=key),patch('sdk.model_face_removal.source_key',return_value=key):
                    report=review(p,asset,removed,sha256(current).hexdigest(),key,restore=True)
                    with self.assertRaises(ProjectError):p.apply_model_face_removal(asset,removed,sha256(current).hexdigest(),key,'0'*64,restore=True)
                    p.apply_model_face_removal(asset,removed,sha256(current).hexdigest(),key,report['proposed_sha256'],restore=True)
                    if typed:self.assertEqual(p.model_overrides[asset]['format'],'tmd-shape')
                    else:self.assertNotIn(asset,p.model_overrides)
                    self.assertEqual(len(p.undo_stack),1);p.undo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),current)
                    p.redo();self.assertEqual(asset in p.model_overrides,typed)
