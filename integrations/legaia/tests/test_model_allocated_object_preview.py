"""Existing pose channels remain evidenced; allocated objects stay explicitly unposed."""
from copy import deepcopy
from hashlib import sha256
import unittest
from importer.assets import decode_tmd
from importer.animation import pose_vertices
from importer.core import ImportError
from importer.model_authoring import preview_model_shape
from importer.model_face_ledger import create_face_ledger,replay_face_ledger,append_object_ledger,append_vector_ledger,append_content_ledger
from importer.model_object_ledger import source_objects
from importer.model_primitives import patch_model_primitives
from test_model_primitives import synthetic
from test_model_object_ledger import clone_request


class ObjectPreviewTests(unittest.TestCase):
    def fixture(self):
        source=synthetic(((0x20,),(0x20,)),count=1);ledger=create_face_ledger(source)
        current,ledger,_=append_vector_ledger(source,ledger,[dict(object_index=0,kind='vertices',vectors=[[1,2,3]])])
        _,audit=replay_face_ledger(source,ledger)
        request=clone_request(audit,next(iter(source_objects(source).values())),100)
        candidate,ledger,_=append_object_ledger(source,ledger,[request])
        return source,candidate,dict(format='tmd-face-addition-v1',asset_sha256=sha256(candidate).hexdigest(),byte_length=len(candidate),ledger=ledger)

    def test_unposed_complete_geometry_and_existing_pose_prefix(self):
        source,candidate,binding=self.fixture();preview=decode_tmd(source);native=decode_tmd(candidate)
        full=preview_model_shape(preview,candidate,binding)
        self.assertEqual(full['vertices'],native['vertices']);self.assertEqual(full['objects'],native['objects'])
        self.assertEqual(full['unposed_object_indices'],[0,1,2])
        # Retain only an evidenced source prefix, as party/equipment viewers do.
        preview['objects']=preview['objects'][:1];preview['vertices']=preview['vertices'][:5]
        transform=dict(object_index=0,translation=[10,20,30],rotation_psx=[0,0,0])
        preview.update(posed=True,pose={'object_transforms':[transform]})
        preview['frames']=[dict(object_transforms=[transform],vertices=preview['vertices'])]
        result=preview_model_shape(preview,candidate,binding)
        self.assertEqual(result['vertices'][:6],[[v[0]+10,v[1]+20,v[2]+30] for v in native['vertices'][:6]])
        self.assertEqual(result['vertices'][6:],native['vertices'][6:])
        self.assertEqual(result['unposed_object_indices'],[1,2])
        self.assertEqual(result['frames'][0]['vertices'],result['vertices'])
        self.assertEqual(result['pose']['object_transforms'],[transform])

    def test_current_continuation_keeps_clones_unposed_and_rejects_forged_channels(self):
        source,candidate,binding=self.fixture();preview=decode_tmd(source)
        transforms=[dict(object_index=i,translation=[10,0,0],rotation_psx=[0,0,0]) for i in range(2)]
        preview.update(posed=True,pose={'object_transforms':transforms})
        current=preview_model_shape(preview,candidate,binding)
        changed,_=patch_model_primitives(candidate,sha256(candidate).hexdigest(),[dict(object_index=2,primitive_index=0,vertices=[2,1,0])])
        changed,ledger,_=append_content_ledger(source,binding['ledger'],changed)
        updated=dict(binding,ledger=ledger,asset_sha256=sha256(changed).hexdigest(),byte_length=len(changed))
        result=preview_model_shape(current,changed,updated)
        self.assertEqual(result['unposed_object_indices'],[2]);self.assertEqual(result['pose']['object_transforms'],transforms)
        bad=deepcopy(current);bad['pose']['object_transforms'].append(dict(object_index=2,translation=[999,0,0],rotation_psx=[0,0,0]))
        with self.assertRaises(ImportError):preview_model_shape(bad,changed,updated)
        bad=deepcopy(updated);bad['ledger']['operations'][0]['requests'][0]['vectors'][0][0]+=1
        with self.assertRaises(ImportError):preview_model_shape(current,changed,bad)
        with self.assertRaises(ImportError):preview_model_shape(preview,changed,binding)


if __name__=='__main__':unittest.main()
