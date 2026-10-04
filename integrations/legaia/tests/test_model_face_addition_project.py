from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from importer.assets import decode_tmd
from importer.core import ImportError
from importer.model_authoring import preview_model_shape, model_shape_overlays
from importer.model_face_removal import remove_faces
from sdk.project import ProjectService, ProjectError
from sdk.model_face_addition import source, review
from test_model_primitives import synthetic


class ModelFaceAdditionProjectTests(unittest.TestCase):
    def project(self, kind=None):
        temp = tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        project = ProjectService(Path(temp.name));project.active_scene = 'scene://fixture'
        asset = 'asset://fixture/model/0';original = synthetic(((0x22,),), count=2)
        project._model_source = lambda *args:original
        current = original
        if kind:
            binding = dict(format=kind, source_scene_id=project.active_scene, source_sha256=sha256(original).hexdigest())
            if kind == 'tmd-face-removal-v1':
                current, removed = remove_faces(original, original, [], [dict(object_index=0, primitive_index=0)])
                binding['removed_faces'] = removed
            else:
                edited = bytearray(original);at = 12+struct.unpack_from('<I', original, 12)[0]
                struct.pack_into('<h', edited, at, 7);current = bytes(edited)
            binding.update(asset_sha256=sha256(current).hexdigest(), byte_length=len(current))
            project.model_overrides[asset] = binding
            path = project.root/'Authored'/'Models'/(binding['asset_sha256']+'.tmd')
            path.parent.mkdir(parents=True);path.write_bytes(current)
        return project, asset, original, current

    def context(self):
        self.enterContext(patch('sdk.scene_preview.source_key', return_value='a'*64))
        self.enterContext(patch('sdk.model_face_addition.source_key', return_value='a'*64))

    def request(self, donor, index=1):
        return dict(face_id=f'face://authored/00000000-0000-4000-8000-{index:012x}',
                    donor_face_id=donor, fields={'vertices':[3, 2, 1, 0]})

    def test_review_apply_history_and_repeated_authored_donors(self):
        self.context();p,asset,original,current = self.project()
        info = source(p, asset, 'a'*64);requests = [self.request(info['topology']['faces'][0]['face_id'])]
        report = review(p, asset, requests, sha256(current).hexdigest(), 'a'*64)
        self.assertFalse(report['project_changed']);self.assertEqual(p.undo_stack, [])
        self.assertEqual(p.model_overrides, {});self.assertFalse((p.root/'Authored').exists())
        with self.assertRaises(ProjectError):p.apply_model_face_additions(asset, requests, sha256(current).hexdigest(), 'a'*64, '0'*64)
        self.assertFalse((p.root/'Authored').exists())
        p.apply_model_face_additions(asset, requests, sha256(current).hexdigest(), 'a'*64, report['proposed_sha256'])
        first = p.read_model_replacement(asset, p.model_overrides[asset])
        self.assertEqual(len(first)-len(current), 24)
        second = [self.request(requests[0]['face_id'], 2)]
        report2 = review(p, asset, second, sha256(first).hexdigest(), 'a'*64)
        p.apply_model_face_additions(asset, second, sha256(first).hexdigest(), 'a'*64, report2['proposed_sha256'])
        final = p.read_model_replacement(asset, p.model_overrides[asset])
        self.assertEqual(len(final)-len(original), 48)
        self.assertEqual(len(p.model_overrides[asset]['ledger']['batches']), 2)
        saved_state = deepcopy((p.model_overrides, p.undo_stack, p.redo_stack))
        with self.assertRaises(ProjectError):p.set_model_replacement(asset, original)
        self.assertEqual((p.model_overrides, p.undo_stack, p.redo_stack), saved_state)
        with self.assertRaisesRegex(ImportError, 'relocated model-pack path'):
            model_shape_overlays(None, {}, {}, removal_bindings=p.model_overrides)
        p.undo();self.assertEqual(p.read_model_replacement(asset, p.model_overrides[asset]), first)
        p.undo();self.assertNotIn(asset, p.model_overrides)
        p.redo();p.redo();self.assertEqual(p.read_model_replacement(asset, p.model_overrides[asset]), final)

    def test_existing_shape_and_removed_face_base_are_retained_and_previewed(self):
        self.context()
        for kind in ('tmd-shape', 'tmd-face-removal-v1'):
            with self.subTest(kind=kind):
                p,asset,original,current = self.project(kind);before = deepcopy(p.model_overrides[asset])
                info = source(p,asset,'a'*64);requests = [self.request(info['topology']['faces'][0]['face_id'])]
                report = review(p,asset,requests,sha256(current).hexdigest(),'a'*64)
                p.apply_model_face_additions(asset,requests,sha256(current).hexdigest(),'a'*64,report['proposed_sha256'])
                binding = p.model_overrides[asset];self.assertEqual(binding['base_binding'], before)
                candidate = p.read_model_replacement(asset, binding)
                self.assertEqual(decode_tmd(candidate)['vertices'], decode_tmd(current)['vertices'])
                preview = preview_model_shape(decode_tmd(original), candidate, binding)
                self.assertEqual(preview['triangles'], decode_tmd(candidate)['triangles'])
                self.assertEqual(preview['objects'], decode_tmd(candidate)['objects'])
                p.undo();self.assertEqual(p.model_overrides[asset],before)
                self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),current)
                p.redo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),candidate)

    def test_binding_base_and_ledger_tampering_reject(self):
        self.context();p,asset,original,current = self.project('tmd-shape')
        donor = source(p,asset,'a'*64)['topology']['faces'][0]['face_id'];requests=[self.request(donor)]
        report=review(p,asset,requests,sha256(current).hexdigest(),'a'*64)
        p.apply_model_face_additions(asset,requests,sha256(current).hexdigest(),'a'*64,report['proposed_sha256'])
        binding=deepcopy(p.model_overrides[asset])
        for change in (lambda b:b.update(source_sha256='0'*64), lambda b:b.update(extra=True),
                       lambda b:b['base_binding'].update(format='tmd-face-addition-v1'),
                       lambda b:b['base_binding'].update(source_scene_id='scene://other'),
                       lambda b:b['ledger']['batches'][0].update(proposed_sha256='0'*64)):
            bad=deepcopy(binding);change(bad)
            with self.assertRaises((ProjectError,ImportError)):p.read_model_replacement(asset,bad)
        base_file=p.root/'Authored'/'Models'/(binding['base_binding']['asset_sha256']+'.tmd')
        base_file.write_bytes(bytes(len(current)))
        with self.assertRaises(ProjectError):p.read_model_replacement(asset,binding)

    def test_stale_or_wrong_mode_cannot_review_or_apply(self):
        self.context();p,asset,_,current = self.project()
        donor=source(p,asset,'a'*64)['topology']['faces'][0]['face_id'];requests=[self.request(donor)]
        for key,digest in (('stale',sha256(current).hexdigest()),('a'*64,'0'*64)):
            with self.assertRaises(ProjectError):review(p,asset,requests,digest,key)
        p.mode='live'
        with self.assertRaises(ProjectError):source(p,asset,'a'*64)
        self.assertEqual(p.model_overrides,{});self.assertEqual(p.undo_stack,[])
        self.assertFalse((p.root/'Authored').exists())


if __name__ == '__main__':
    unittest.main()
