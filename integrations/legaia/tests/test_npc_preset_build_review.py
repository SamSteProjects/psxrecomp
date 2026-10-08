from copy import deepcopy
from unittest.mock import patch
import unittest
from test_npc_presets import NpcPresetTests
from sdk.npc_presets import review as preset_review
from sdk.npc_preset_build_review import review
from sdk.project import ProjectError, ProjectService
from sdk.build import authored_state_key


class NpcPresetBuildReviewTests(unittest.TestCase):
    setUp = NpcPresetTests.setUp
    request = NpcPresetTests.request
    def reviewed_request(self):
        report = preset_review(self.p, self.request())
        return dict(**report['request'], review_key=report['review_key'])

    def test_complete_project_isolated_review_and_atomic_apply(self):
        p = self.p
        p.command(dict(type='set_transform', entity_id=self.donor, position=dict(y=512)))
        before = deepcopy((p._document(), p.undo_stack, p.redo_stack, p.imports, p.assets.records))
        def assess(view):
            self.assertEqual(view.overrides, p.overrides)
            self.assertEqual(view.actor_templates, p.actor_templates)
            self.assertEqual(len(view.actor_drafts), len(p.actor_drafts) + 1)
            for identifier, draft in p.actor_drafts.items():
                self.assertEqual(view.actor_drafts[identifier], draft)
            return dict(source_key=authored_state_key(view), included_npc_draft_count=2,
                        read_only=True, normal_build_ready=False, blockers=[dict(message='Existing unsupported height')])
        with patch('sdk.npc_preset_build_review.build_review', side_effect=assess):
            result = review(p, self.reviewed_request())
        self.assertFalse(result['output_written'])
        self.assertEqual(result['build_review']['blockers'][0]['message'], 'Existing unsupported height')
        self.assertEqual((p._document(), p.undo_stack, p.redo_stack, p.imports, p.assets.records), before)
        accepted = result['review']
        p.command(dict(type='instantiate_npc_preset', **accepted['request'], review_key=accepted['review_key']))
        self.assertEqual(p.actor_drafts[accepted['entity_id']], accepted['draft'])
        self.assertEqual(len(p.undo_stack), len(before[1]) + 1)
        self.assertEqual(ProjectService.open(p.save()).actor_drafts, p.actor_drafts)
        p.undo(); self.assertEqual(p._document(), before[0])
        p.redo(); self.assertEqual(p.actor_drafts[accepted['entity_id']], accepted['draft'])

    def test_stale_receipt_source_coverage_and_live_refuse(self):
        request = self.reviewed_request()
        before = deepcopy((self.p._document(), self.p.undo_stack, self.p.redo_stack))
        for change in ({'review_key': '0'*64}, {'expected_source_key': '0'*64}, {'extra': True}):
            with self.assertRaises(ProjectError): review(self.p, {**request, **change})
        with patch('sdk.npc_preset_build_review.build_review', return_value=dict(source_key='0'*64, included_npc_draft_count=1, read_only=True)):
            with self.assertRaises(ProjectError): review(self.p, request)
        self.assertEqual((self.p._document(), self.p.undo_stack, self.p.redo_stack), before)
        self.p.mode='live'
        with self.assertRaises(ProjectError): review(self.p, request)
