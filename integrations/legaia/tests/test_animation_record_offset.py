"""Native translation staging preserves donor mappings, other channels and history."""
from copy import deepcopy
import os
import tempfile
import unittest

from importer.animation import animation_record_ranges, decode_animation_record
from importer.animation_allocation import allocate_animation_record
from importer.animation_authoring import patch_animation_channels
from sdk.animation_allocation import prepare_record_allocation
from sdk.animation_record_edit import prepare
from sdk.animation_record_ledger import compose, verified_source
from sdk.animation_record_offset import stage
from sdk.project import ProjectError, ProjectService
from sdk.scene_preview import source_key
import test_animation_glb_workflow as workflow
from test_model_primitive_workflow import http_server


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'), 'Retail disc required')
class AnimationRecordOffset(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = workflow.AnimationGlbWorkflow().project(self.tmp.name)
        self.owner = 'scene://town01/actors/man-p1/0011'
        key = source_key(self.project)
        _, report = prepare_record_allocation(self.project, self.owner, [1, 0, 1], [], key)
        self.project.command(dict(type='allocate_animation_record', entity_id=self.owner,
            source_frame_indices=[1, 0, 1], edits=[], expected_source_key=key, review_key=report['review_key']))
        self.entry = self.project.overrides[self.project.active_scene]['AnimationRecords']['records'][0]
        self.args = dict(scene_id=self.project.active_scene, record_id=self.entry['record_id'],
            source_frame_indices=[1, 0, 1], edits=[dict(frame_index=0, object_index=0,
                translation=dict(x=17), rotation_psx=dict(y=32))], object_index=0,
            start=0, end=1, delta=dict(x=5), expected_source_key=source_key(self.project))

    def native(self, edits):
        source, _ = verified_source(self.project, self.project.active_scene)
        index = int(self.entry['donor_animation_id'].split('/')[-1])
        start, end = animation_record_ranges(source)[index]
        captured, _ = patch_animation_channels(source[start:end], self.entry['donor_record_sha256'], self.entry['donor_edits'])
        return allocate_animation_record(captured, self.entry['effective_donor_record_sha256'], [1, 0, 1], edits)[0]

    def test_effective_draft_offset_native_roundtrip_apply_history_and_reopen(self):
        before = deepcopy((self.project._document(), self.project.undo_stack, self.project.redo_stack))
        original = self.native(self.args['edits'])
        report = stage(self.project, **self.args)
        candidate = self.native(report['edits'])
        original_frames = decode_animation_record(original)['frames']
        frames = decode_animation_record(candidate)['frames']
        self.assertEqual(report['changed_axes'][0], dict(frame_index=0, axis='x', before=17, after=22))
        for index, frame in enumerate(frames):
            for obj, transform in enumerate(frame['object_transforms']):
                expected = deepcopy(original_frames[index]['object_transforms'][obj])
                if index <= 1 and obj == 0:
                    expected['translation'][0] += 5
                self.assertEqual(transform, expected)
        self.assertEqual(candidate[:8], original[:8])
        self.assertEqual(candidate[-8:], original[-8:])
        self.assertEqual((self.project._document(), self.project.undo_stack, self.project.redo_stack), before)
        request = {k: report[k] for k in ('scene_id', 'record_id', 'source_frame_indices', 'edits')}
        request['expected_source_key'] = self.args['expected_source_key']
        _, review = prepare(self.project, **request)
        self.assertEqual(review['candidate_record_sha256'], report['after_record_sha256'])
        self.project.command(dict(type='edit_animation_record', **request, review_key=review['review_key']))
        bank, _ = compose(self.project, self.project.active_scene)
        start, end = animation_record_ranges(bank)[-1]
        self.assertEqual(bank[start:end], candidate)
        self.project.save()
        reopened = ProjectService.open(self.project.root)
        self.assertEqual(compose(reopened, reopened.active_scene)[0], bank)
        self.project.undo()
        self.assertEqual((self.project._document(), self.project.undo_stack), before[:2])
        self.project.redo()
        self.assertEqual(compose(self.project, self.project.active_scene)[0], bank)

    def test_exact_http_bounds_overflow_stale_and_zero_offset(self):
        before = deepcopy((self.project._document(), self.project.undo_stack, self.project.redo_stack))
        with http_server(self.project) as (_, post):
            status, report = post('/api/animation-record-offset', self.args)
            self.assertEqual(status, 200, report)
            for fields in ({'extra': True}, {'object_index': True}, {'start': -1}, {'end': 3},
                           {'delta': {'x': 4096}}, {'delta': {'x': True}}, {'delta': {}},
                           {'expected_source_key': '0' * 64},
                           {'edits': [dict(frame_index=0, object_index=0, translation=dict(x=2047))], 'delta': {'x': 1}}):
                self.assertEqual(post('/api/animation-record-offset', {**self.args, **fields})[0], 400, fields)
            status, zero = post('/api/animation-record-offset', {**self.args, 'delta': {'x': 0, 'y': 0}})
            self.assertEqual(status, 200, zero)
            self.assertEqual(zero['edits'], self.args['edits'])
            self.assertEqual(zero['changed_axes'], [])
            self.assertEqual(zero['before_record_sha256'], zero['after_record_sha256'])
        self.assertEqual((self.project._document(), self.project.undo_stack, self.project.redo_stack), before)
