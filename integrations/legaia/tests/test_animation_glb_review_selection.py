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
        with patch('sdk.animation_glb._snapshot', return_value=snapshot), patch('sdk.animation_glb._current'), patch('sdk.animation_sources.apply',side_effect=lambda p,c,content,**recipe:p.command(c)):
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
        with patch('sdk.animation_glb._snapshot', return_value=snapshot), patch('sdk.animation_glb._current'), patch('sdk.animation_sources.apply',side_effect=lambda p,c,content,**recipe:p.command(c)):
            report = preview_import(project, owner, content, binding)
            apply_import(project, owner, content, binding, report['review_key'])
        identity = dict(binding=binding, glb_sha256=sha256(content).hexdigest(),
                        candidate_sha256=report['candidate_sha256'], proposed_value=calls[0]['value'])
        self.assertEqual(report['review_key'], digest(identity))
        self.assertNotIn('file_animation_index', report)


    def test_equal_static_candidates_require_different_explicit_object_mapping_keys(self):
        project,owner,content,binding,snapshot,calls=self.fixture(duplicate=False)
        from importer.animation_glb import _read_glb
        doc,payload=_read_glb(content);doc['animations']=[]
        node=dict(name='External A',translation=[4,0,0]);doc['nodes']=[node,dict(node,name='External B')];doc['scenes'][0]['nodes']=[0,1]
        content=encode(doc,payload)
        with patch('sdk.animation_glb._snapshot',return_value=snapshot),patch('sdk.animation_glb._current'),patch('sdk.animation_sources.apply',side_effect=lambda p,c,content,**recipe:p.command(c)):
            first=preview_import(project,owner,content,dict(binding,external_object_nodes=[0]))
            second=preview_import(project,owner,content,dict(binding,external_object_nodes=[1]))
            self.assertEqual(first['candidate_sha256'],second['candidate_sha256']);self.assertNotEqual(first['review_key'],second['review_key'])
            with self.assertRaises(ProjectError):apply_import(project,owner,content,dict(binding,external_object_nodes=[1]),first['review_key'])
            self.assertEqual(calls,[])
            apply_import(project,owner,content,dict(binding,external_object_nodes=[1]),second['review_key']);self.assertEqual(len(calls),1)


    def test_equal_static_candidates_bind_external_sampling_choices(self):
        project,owner,content,binding,snapshot,calls=self.fixture(duplicate=False)
        from importer.animation_glb import _read_glb
        doc,payload=_read_glb(content);doc['animations']=[];doc['nodes'][0]['translation']=[4,0,0];content=encode(doc,payload)
        with patch('sdk.animation_glb._snapshot',return_value=snapshot),patch('sdk.animation_glb._current'),patch('sdk.animation_sources.apply',side_effect=lambda p,c,content,**recipe:p.command(c)):
            a=dict(binding,external_sampling=dict(start_seconds=0,rate=1));b=dict(binding,external_sampling=dict(start_seconds=1,rate=1))
            first=preview_import(project,owner,content,a);second=preview_import(project,owner,content,b)
            self.assertEqual(first['candidate_sha256'],second['candidate_sha256']);self.assertNotEqual(first['review_key'],second['review_key'])
            with self.assertRaises(ProjectError):apply_import(project,owner,content,b,first['review_key'])
            self.assertEqual(calls,[]);apply_import(project,owner,content,b,second['review_key']);self.assertEqual(len(calls),1)
