"""Selection libraries are portable metadata with fresh source proof on recall."""
from copy import deepcopy
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

from sdk.project import ProjectService, ProjectError, digest
from sdk.scene_selection_sets import command, review, review_key, source_binding, validate
from sdk.build import authored_state_key
from test_environment_group import SCENE, IDS, source_map
from test_project_workflow import synthetic_scene

ACTOR = 'scene://fixture/actors/man-p1/0001'


class SceneSelectionSetTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(); self.addCleanup(self.directory.cleanup)
        self.p = ProjectService(Path(self.directory.name))
        self.p.import_metadata(synthetic_scene()); self.p.scene_selection_sets = {}
        self.source = source_map()
        self.mock = patch.object(self.p, '_environment_source', return_value=self.source).start()
        self.addCleanup(patch.stopall)

    def create(self, ids=None, name='Wall and actor'):
        ids = [ACTOR, IDS[0]] if ids is None else ids
        binding = source_binding(self.p, SCENE, ids)
        command(self.p, dict(type='create_scene_selection_set', scene_id=SCENE, name=name,
                             entity_ids=ids, **binding))
        return next(value for value in self.p.scene_selection_sets.values() if value['name'] == name.strip())

    def edit(self, kind, row, **fields):
        command(self.p, dict(type=kind, selection_set_id=row['id'], review_key=review_key(self.p, row), **fields))

    def npc(self):
        self.p.command(dict(type='create_actor_draft',donor_entity_id=ACTOR,name='Saved NPC',position=dict(x=256,z=512)))
        return next(iter(self.p.actor_drafts))

    def test_npc_mixed_library_persistence_build_identity_and_current_placement(self):
        p=self.p;npc=self.npc();baseline=deepcopy((p.imports,p.overrides,p.actor_drafts));key=authored_state_key(p)
        row=self.create([npc,ACTOR,IDS[0]],'NPC actor and wall');self.assertEqual(authored_state_key(p),key)
        self.assertEqual((p.imports,p.overrides,p.actor_drafts),baseline)
        p.undo();self.assertFalse(p.scene_selection_sets);p.redo()
        self.assertEqual(review(p,row['id'],review_key(p,row))['entity_ids'],sorted([npc,ACTOR,IDS[0]]))
        p.command(dict(type='set_actor_draft_position',entity_id=npc,position=dict(x=320,z=576)))
        p.command(dict(type='rename_actor_draft',entity_id=npc,name='Moved NPC'))
        self.assertEqual(review(p,row['id'],review_key(p,row))['entity_ids'],row['entity_ids'])
        reopened=ProjectService.open(p.save());self.assertEqual(reopened.scene_selection_sets,p.scene_selection_sets)
        self.assertEqual(reopened.actor_drafts,p.actor_drafts)
        self.edit('update_scene_selection_set',row,entity_ids=[npc]);row=p.scene_selection_sets[row['id']]
        self.assertIsNone(row['map_sha256']);self.mock.side_effect=AssertionError('NPC-only recall must not read MAP')
        self.assertEqual(review(p,row['id'],review_key(p,row))['entity_ids'],[npc])

    def test_deleted_npc_library_remains_portable_but_fresh_recall_rejects(self):
        p=self.p;npc=self.npc();row=self.create([npc],'NPC')
        p.command(dict(type='delete_actor_draft',entity_id=npc));before=deepcopy((p._document(),p.undo_stack))
        with self.assertRaisesRegex(ProjectError,'unavailable'):review(p,row['id'],review_key(p,row))
        self.assertEqual((p._document(),p.undo_stack),before)
        reopened=ProjectService.open(p.save());self.assertEqual(reopened.scene_selection_sets,p.scene_selection_sets)
        with self.assertRaisesRegex(ProjectError,'unavailable'):source_binding(p,SCENE,[npc])
        self.edit('rename_scene_selection_set',row,name='Missing NPC');row=p.scene_selection_sets[row['id']]
        self.edit('delete_scene_selection_set',row);self.assertFalse(p.scene_selection_sets)
        p.undo();p.undo();p.undo();self.assertIn(npc,p.actor_drafts)
        self.assertEqual(review(p,row['id'],review_key(p,p.scene_selection_sets[row['id']]))['entity_ids'],[npc])
        p.actor_drafts[npc]['scene_id']='scene://other'
        with self.assertRaises(ProjectError):source_binding(p,SCENE,[npc])

    def test_mixed_source_review_is_read_only_and_history_is_metadata_only(self):
        p = self.p; before = deepcopy(p.overrides); imports = deepcopy(p.imports)
        row = self.create([IDS[0], ACTOR], '  Wall and actor  ')
        self.assertEqual(row['entity_ids'], sorted([ACTOR, IDS[0]]))
        self.assertEqual(row['import_sha256'], digest(p.imports[SCENE]))
        self.assertEqual(len(row['map_sha256']), 64)
        entry = p.undo_stack[-1]
        self.assertEqual(entry['target'], 'scene_selection_sets')
        self.assertEqual(entry['entity_ids'], row['entity_ids']); self.assertIsNone(entry['before'])
        history = deepcopy(p.undo_stack)
        result = review(p, row['id'], review_key(p, row))
        self.assertTrue(result['read_only']); self.assertEqual(result['entity_ids'], row['entity_ids'])
        self.assertEqual(p.undo_stack, history); self.assertEqual(p.overrides, before); self.assertEqual(p.imports, imports)

    def test_portable_validation_never_reads_disc_and_actor_only_needs_no_map(self):
        mixed = self.create()
        self.mock.side_effect = AssertionError('Portable metadata must not read retail source')
        validate(self.p, mixed['id'], mixed)
        actor = self.create([ACTOR], 'Actor')
        self.assertIsNone(actor['map_sha256'])
        self.assertEqual(review(self.p, actor['id'], review_key(self.p.root, actor))['entity_ids'], [ACTOR])

    def test_integrated_save_open_undo_reimport_guard_and_build_identity(self):
        p = self.p; p.save(); inputs = authored_state_key(p)
        row = self.create(); self.assertTrue(p.dirty)
        self.assertEqual(authored_state_key(p), inputs)
        p.undo(); self.assertFalse(p.scene_selection_sets); self.assertFalse(p.dirty)
        p.redo(); self.assertEqual(p.scene_selection_sets[row['id']], row)
        changed = deepcopy(p.imports[SCENE]); changed['actors'][0]['imported_transform']['position']['x'] = 192
        with self.assertRaises(ProjectError): p.import_metadata(changed)
        self.edit('delete_scene_selection_set', row)
        with self.assertRaises(ProjectError): p.import_metadata(changed)
        p.undo(); path = p.save()
        with patch.object(ProjectService, '_environment_source', side_effect=AssertionError('Open must be portable')):
            reopened = ProjectService.open(path)
        self.assertEqual(reopened.scene_selection_sets, p.scene_selection_sets)
        self.assertFalse(reopened.undo_stack); self.assertFalse(reopened.dirty)
        raw = json.loads(path.read_text(encoding='utf-8'))
        raw['scene_selection_sets'][row['id']]['entity_ids'] = list(reversed(row['entity_ids']))
        path.write_text(json.dumps(raw), encoding='utf-8')
        with self.assertRaises(ProjectError): ProjectService.open(path)

    def test_crud_noop_retains_redo_and_rejects_stale_keys(self):
        p = self.p; row = self.create(); old = deepcopy(row)
        self.edit('rename_scene_selection_set', row, name='Other'); row = deepcopy(p.scene_selection_sets[row['id']])
        depth = len(p.undo_stack); p.redo_stack.append({'sentinel': True})
        self.edit('rename_scene_selection_set', row, name=' Other ')
        self.assertEqual(len(p.undo_stack), depth); self.assertEqual(p.redo_stack, [{'sentinel': True}])
        with self.assertRaises(ProjectError): self.edit('delete_scene_selection_set', old)
        self.edit('update_scene_selection_set', row, entity_ids=[ACTOR])
        row = deepcopy(p.scene_selection_sets[row['id']]); self.assertIsNone(row['map_sha256'])
        self.assertEqual(p.undo_stack[-1]['before']['entity_ids'], sorted([ACTOR, IDS[0]]))
        self.assertEqual(p.undo_stack[-1]['after']['entity_ids'], [ACTOR]); self.assertEqual(p.redo_stack, [])
        self.edit('delete_scene_selection_set', row); self.assertEqual(p.scene_selection_sets, {})
        self.assertEqual(p.overrides, {})

    def test_drift_and_source_membership_fail_before_any_publication(self):
        p = self.p; row = self.create(); baseline = deepcopy(p.scene_selection_sets); history = deepcopy(p.undo_stack)
        changed = bytearray(self.source); changed[4 * 32 + 1] ^= 1; self.mock.return_value = bytes(changed)
        with self.assertRaises(ProjectError): review(p, row['id'], review_key(p, row))
        with self.assertRaises(ProjectError): self.edit('update_scene_selection_set', row, entity_ids=[ACTOR])
        self.assertEqual(p.scene_selection_sets, baseline); self.assertEqual(p.undo_stack, history)
        self.mock.return_value = self.source
        with self.assertRaises(ProjectError): self.create([IDS[0].replace('00129', '00000')], 'Ground')
        p.imports[SCENE]['actors'][0]['imported_transform']['position']['x'] = 192
        with self.assertRaises(ProjectError): validate(p, row['id'], row)
        self.assertEqual(p.scene_selection_sets, baseline)

    def test_invalid_identity_selection_name_binding_and_library_bounds(self):
        p = self.p
        for ids in ([], [ACTOR, ACTOR], [ACTOR + '/extra'], ['authored-actor://invalid'],
                    [IDS[0].replace('00129', '129')], ['environment://other/field-map/decorations/00129'],
                    [IDS[0].replace('00129', '16384')], [f'invalid://{i}' for i in range(129)]):
            with self.assertRaises(ProjectError): self.create(ids)
        for name in ('', 'x' * 81, 'line\nbreak', 1):
            with self.assertRaises(ProjectError): self.create([ACTOR], name)
        row = self.create([ACTOR], 'Actor')
        with self.assertRaises(ProjectError): self.create([ACTOR], 'ACTOR')
        for field, value in (('id', 'scene-selection://INVALID'), ('name', ' untrimmed '),
                             ('map_sha256', 'a' * 64), ('import_sha256', 'stale'),
                             ('entity_ids', [ACTOR, ACTOR])):
            bad = deepcopy(row); bad[field] = value
            with self.assertRaises(ProjectError): validate(p, bad['id'], bad)
        binding = source_binding(p, SCENE, [ACTOR])
        with self.assertRaises(ProjectError): command(p, dict(type='create_scene_selection_set', scene_id=SCENE,
            name='Stale', entity_ids=[ACTOR], **{**binding, 'map_sha256': 'a' * 64}))
        for i in range(127): self.create([ACTOR], str(i))
        with self.assertRaises(ProjectError): self.create([ACTOR], 'Overflow')
        self.assertEqual(len(p.scene_selection_sets), 128)

    def test_inactive_and_live_recalls_rejected_but_metadata_management_is_portable(self):
        p = self.p; row = self.create()
        p.active_scene = None
        with self.assertRaises(ProjectError): review(p, row['id'], review_key(p, row))
        self.mock.side_effect = AssertionError('Rename must be portable')
        self.edit('rename_scene_selection_set', row, name='Other'); row = p.scene_selection_sets[row['id']]
        p.mode = 'live'
        with self.assertRaises(ProjectError): self.edit('delete_scene_selection_set', row)
        with self.assertRaises(ProjectError): review(p, row['id'], review_key(p, row))


if __name__ == '__main__':
    unittest.main()
