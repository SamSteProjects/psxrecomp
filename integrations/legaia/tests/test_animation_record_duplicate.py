"""Exact retained duplication uses native reconstruction and existing budgets."""
from copy import deepcopy
from hashlib import sha256
import unittest
from unittest.mock import patch

from importer.animation_allocation import append_animation_record_payloads
from sdk.animation_record_duplicate import prepare, apply
from sdk.animation_record_ledger import reconstruct
from sdk.project import ProjectError
import test_animation_record_ledger as fixtures


class RetainedDuplicate(unittest.TestCase):
    def setUp(self):
        self.project, self.source, self.ledger, self.native = fixtures.AnimationLedgerValidation().fixture()
        self.scene = 'scene://town01'
        self.record = self.ledger['records'][0]['record_id']
        self.project.active_scene = self.scene
        self.project.mode = 'edit'
        self.project.overrides = {self.scene: {'AnimationRecords': deepcopy(self.ledger)}}
        self.project.undo_stack = []
        self.project.redo_stack = ['old redo']
        self.key = 'a'*64
        self.guards = [patch('sdk.animation_record_duplicate.source_key', return_value=self.key),
                       patch('sdk.animation_record_duplicate.compose', side_effect=self.compose)]
        for guard in self.guards: guard.start(); self.addCleanup(guard.stop)

    def compose(self, project, scene, *, ledger):
        return append_animation_record_payloads(self.source, sha256(self.source).hexdigest(), reconstruct(self.source, ledger))

    def test_exact_copy_readonly_review_and_single_history_transaction(self):
        before = deepcopy(self.project.overrides)
        candidate, report = prepare(self.project, self.scene, self.record, self.key)
        self.assertEqual(self.project.overrides, before)
        self.assertEqual(self.project.undo_stack, [])
        copy = report['duplicate_entry']
        self.assertNotEqual(copy['record_id'], self.record)
        self.assertEqual(copy, dict(self.ledger['records'][0], record_id=copy['record_id']))
        self.assertFalse(report['assignments_changed'])
        self.assertEqual(prepare(self.project, self.scene, self.record, self.key)[0], candidate)
        apply(self.project, dict(type='duplicate_animation_record', scene_id=self.scene, record_id=self.record,
                                expected_source_key=self.key, review_key=report['review_key']))
        self.assertEqual(len(self.project.undo_stack), 1)
        self.assertEqual(self.project.redo_stack, [])
        self.assertEqual(self.project.overrides[self.scene]['AnimationRecords']['records'][0], self.ledger['records'][0])

    def test_retired_capture_duplicates_to_active_independent_identity(self):
        self.project.overrides[self.scene]['AnimationRecords']['removed_record_ids'] = [self.record]
        _, report = prepare(self.project, self.scene, self.record, self.key)
        self.assertFalse(report['source_active'])
        self.assertEqual(report['proposed_ledger']['removed_record_ids'], [self.record])
        self.assertNotIn(report['duplicate_entry']['record_id'], report['proposed_ledger']['removed_record_ids'])

    def test_stale_bad_review_and_native_hash_fail_without_mutation(self):
        before = deepcopy(self.project.overrides)
        for kwargs in [dict(scene_id='scene://other', record_id=self.record, expected_source_key=self.key),
                       dict(scene_id=self.scene, record_id='missing', expected_source_key=self.key),
                       dict(scene_id=self.scene, record_id=self.record, expected_source_key='b'*64)]:
            with self.assertRaises(ProjectError): prepare(self.project, **kwargs)
        with self.assertRaises(ProjectError):
            apply(self.project, dict(type='duplicate_animation_record', scene_id=self.scene, record_id=self.record,
                                    expected_source_key=self.key, review_key='b'*64))
        self.assertEqual(self.project.overrides, before)
        self.project.overrides[self.scene]['AnimationRecords']['records'][0]['record_sha256'] = 'c'*64
        with self.assertRaises(Exception): prepare(self.project, self.scene, self.record, self.key)
        self.assertEqual(self.project.undo_stack, [])

    def test_revision_and_cumulative_channel_budgets(self):
        ledger = self.project.overrides[self.scene]['AnimationRecords']
        ledger['revision'] = 64
        with self.assertRaises(ProjectError): prepare(self.project, self.scene, self.record, self.key)
        self.assertEqual(ledger['revision'], 64)
        ledger['revision'] = 1
        entry = ledger['records'][0]
        entry.update(object_count=64, source_frame_indices=[0]*64)
        with patch('sdk.animation_record_duplicate.compose', return_value=(self.source, None)):
            with self.assertRaisesRegex(ProjectError, 'cumulative'):
                prepare(self.project, self.scene, self.record, self.key)
        self.assertEqual(len(ledger['records']), 1)
        self.project.mode = 'live'
        with self.assertRaisesRegex(ProjectError, 'editable'):
            prepare(self.project, self.scene, self.record, self.key)
