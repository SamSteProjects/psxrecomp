"""Review must authorize the chosen clip even when native outcomes coincide."""
from copy import deepcopy
from hashlib import sha256
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from importer.animation_authoring import patch_animation_channels
from sdk.animation_glb import preview_import, apply_import
from sdk.project import ProjectError, digest
from test_animation_glb import document, encode, record, changed_key


class ClipReviewIdentity(unittest.TestCase):
    def fixture(self, duplicate=True):
        frames = [[([0, 0, 0], [0, 0, 0])]] * 2
        native = record(frames); doc, payload = document(frames)
        payload = changed_key(doc, payload, 'translation', 0, [4, 0, 0])
        if duplicate: doc['animations'].append(deepcopy(doc['animations'][0]))
        content = encode(doc, payload); owner = 'scene://town01/actors/man-p1/0011'
        binding = dict(schema_version='legaia.animation-glb-binding.v1', entity_id=owner,
                       animation_id='animation://town01/scene-anm/0012', clip_fps=15.0,
                       source_record_sha256=sha256(native).hexdigest(),
                       effective_record_sha256=sha256(native).hexdigest(), project_source_key='a'*64)
        def bank(owners):
            edits = owners.get(owner, {}).get('edits', [])
            return patch_animation_channels(native, sha256(native).hexdigest(), edits)
        snapshot = dict(binding=binding, retail=native, effective=native, owners={},
                        start=0, channel_owner=owner, catalog=SimpleNamespace(authored_bank=bank))
        calls = []; project = SimpleNamespace(command=calls.append)
        return project, owner, content, binding, snapshot, calls

    def test_equal_native_candidates_require_different_clip_review_keys(self):
        project, owner, content, binding, snapshot, calls = self.fixture()
        with patch('sdk.animation_glb._snapshot', return_value=snapshot), patch('sdk.animation_glb._current'):
            first = preview_import(project, owner, content, binding, animation_index=0)
            second = preview_import(project, owner, content, binding, animation_index=1)
            self.assertEqual(first['candidate_sha256'], second['candidate_sha256'])
            self.assertEqual(first['changes'], second['changes'])
            self.assertNotEqual(first['review_key'], second['review_key'])
            with self.assertRaisesRegex(ProjectError, 'changed after review'):
                apply_import(project, owner, content, binding, first['review_key'], animation_index=1)
            self.assertEqual(calls, [])
            apply_import(project, owner, content, binding, second['review_key'], animation_index=1)
            self.assertEqual(len(calls), 1)

    def test_implicit_single_clip_retains_legacy_review_digest(self):
        project, owner, content, binding, snapshot, calls = self.fixture(duplicate=False)
        with patch('sdk.animation_glb._snapshot', return_value=snapshot), patch('sdk.animation_glb._current'):
            report = preview_import(project, owner, content, binding)
            apply_import(project, owner, content, binding, report['review_key'])
        identity = dict(binding=binding, glb_sha256=sha256(content).hexdigest(),
                        candidate_sha256=report['candidate_sha256'], proposed_value=calls[0]['value'])
        self.assertEqual(report['review_key'], digest(identity))
        self.assertNotIn('file_animation_index', report)
