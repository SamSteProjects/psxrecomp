"""Mixed groups validate every owner before publishing one history entry."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from importer.core import ImportError
from sdk.project import ProjectService, ProjectError
from sdk.scene_placement_group import review, apply
from sdk.environment_group import review as decoration_review
from test_environment_group import SCENE, IDS, source_map
from test_project_workflow import synthetic_scene

ACTOR = 'scene://fixture/actors/man-p1/0001'
MIXED = [ACTOR, IDS[0]]


class ScenePlacementGroupTests(unittest.TestCase):
    def project(self, directory):
        p = ProjectService(Path(directory))
        document = synthetic_scene()
        document['actors'][0]['imported_transform']['position'].update(x=128, z=256)
        p.import_metadata(document)
        return p

    def apply_review(self, p, r):
        apply(p, dict(type='apply_scene_placement_group', entity_id=SCENE,
                      entity_ids=r['entity_ids'], delta=r['delta'], review_key=r['review_key']))

    def test_atomic_preservation_undo_redo_and_saved_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            p = self.project(directory)
            source = source_map()
            with patch.object(ProjectService, '_environment_source', return_value=source):
                p.command(dict(type='set_transform', entity_id=ACTOR, position=dict(x=192, y=77)))
                environment = dict(source_sha256=sha256(source).hexdigest(),
                    edits=[dict(record_index=4, offset=dict(x=40, y=50, z=60))],
                    instances=[dict(cell_index=129, offset=dict(x=70, y=80), rotation_psx=dict(y=777)),
                               dict(cell_index=387, offset=dict(z=120))])
                p.command(dict(type='set_environment_transforms', entity_id=SCENE, value=environment))
                p.command(dict(type='set_collision_walls', entity_id=SCENE,
                    value=dict(source_sha256=sha256(source).hexdigest(), edits=[dict(row=1, column=0, quadrant=0, blocked=True)])))
                p.save()
                before = deepcopy(p.overrides)
                depth = len(p.undo_stack)
                r = review(p, SCENE, MIXED[::-1], dict(x=64, z=-64))
                self.assertEqual(p.overrides, before)
                self.assertEqual(r['affected_count'], 2)
                actor = next(t for t in r['targets'] if t['kind'] == 'actor')
                self.assertEqual(actor['current'], dict(x=192, z=256))
                self.assertEqual(actor['proposed'], dict(x=256, z=192))
                self.assertNotIn('cell_index', actor)
                self.apply_review(p, r)
                self.assertEqual(len(p.undo_stack), depth + 1)
                self.assertEqual(p.undo_stack[-1]['target'], 'entity_overrides')
                self.assertEqual(p.overrides[ACTOR]['Transform']['position'], dict(x=256, y=77, z=192))
                self.assertEqual(p.overrides[SCENE]['Collision'], before[SCENE]['Collision'])
                self.assertEqual(p.overrides[SCENE]['Environment']['edits'], environment['edits'])
                entries = {e['cell_index']: e for e in p.overrides[SCENE]['Environment']['instances']}
                self.assertEqual(entries[129], dict(cell_index=129, offset=dict(x=134, y=80, z=124), rotation_psx=dict(y=777)))
                self.assertEqual(entries[387], environment['instances'][1])
                after = deepcopy(p.overrides)
                p.undo(); self.assertEqual(p.overrides, before)
                p.redo(); self.assertEqual(p.overrides, after)
                reopened = ProjectService.open(p.save())
                self.assertEqual(reopened.overrides, after)
                self.assertEqual(reopened.imports[SCENE]['actors'][0]['imported_transform']['position']['y'], None)

    def test_zero_delta_preserves_metadata_order_redo_and_dirty_state(self):
        with tempfile.TemporaryDirectory() as directory:
            p = self.project(directory); source = source_map()
            with patch.object(p, '_environment_source', return_value=source):
                p.command(dict(type='set_environment_transforms', entity_id=SCENE,
                    value=dict(source_sha256=sha256(source).hexdigest(),
                        instances=[dict(cell_index=258, offset=dict(z=90)), dict(cell_index=129, offset=dict(x=10))])))
                p.save()
                p.command(dict(type='set_transform', entity_id=ACTOR, position=dict(x=192)))
                p.undo()
                before = deepcopy(p.overrides); undo = deepcopy(p.undo_stack); redo = deepcopy(p.redo_stack)
                r = review(p, SCENE, MIXED, dict(x=0, z=0))
                self.assertFalse(r['project_change']); self.assertEqual(r['changes'], {})
                self.apply_review(p, r)
                self.assertEqual(p.overrides, before); self.assertEqual(p.undo_stack, undo)
                self.assertEqual(p.redo_stack, redo); self.assertFalse(p.dirty)

    def test_invalid_selection_ranges_and_actor_grid_publish_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            p = self.project(directory); source = source_map()
            with patch.object(p, '_environment_source', return_value=source):
                for ids in ([ACTOR], MIXED * 2, IDS, [ACTOR, ACTOR + '/invalid'],
                            [ACTOR, 'authored-actor://invalid'], [ACTOR, IDS[0].replace('00129', '129')],
                            MIXED + [f'invalid://{n}' for n in range(127)]):
                    with self.assertRaises(ProjectError): review(p, SCENE, ids, dict(x=64, z=0))
                for delta in (dict(x=1,z=0), dict(x=True,z=0), dict(x=64.0,z=0), dict(x=16384,z=0), dict(x=64), dict(x=64,z=0,y=0)):
                    with self.assertRaises(ProjectError): review(p, SCENE, MIXED, delta)
                for delta in (dict(x=-192,z=0), dict(x=16320,z=0)):
                    with self.assertRaises(ProjectError): review(p, SCENE, MIXED, delta)
                p.mode = 'live'
                with self.assertRaises(ProjectError): review(p, SCENE, MIXED, dict(x=64,z=0))
                p.mode = 'edit'
                self.assertEqual(p.overrides, {}); self.assertEqual(p.undo_stack, [])
                # Public scenery groups retain their two-decoration minimum.
                with self.assertRaises(ProjectError): decoration_review(p, SCENE, IDS[:1], dict(x=1,z=0))

    def test_capacity_and_stale_keys_are_all_or_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            p = self.project(directory); source = source_map()
            with patch.object(p, '_environment_source', return_value=source):
                r = review(p, SCENE, MIXED, dict(x=64,z=64)); p.name = 'Changed'
                with self.assertRaises(ProjectError): self.apply_review(p, r)
                r = review(p, SCENE, MIXED, dict(x=64,z=64))
                p.imports[SCENE]['actors'][0]['placement_fields']['animation_id'] = 3
                with self.assertRaises(ProjectError): self.apply_review(p, r)
                r = review(p, SCENE, MIXED, dict(x=64,z=64))
            changed = bytearray(source); changed[0x4000] = 1
            with patch.object(p, '_environment_source', return_value=bytes(changed)):
                with self.assertRaises(ProjectError): self.apply_review(p, r)
            full = bytearray(source)
            for record in range(5,512): full[record*32+31] = 1
            with patch.object(p, '_environment_source', return_value=bytes(full)):
                with self.assertRaisesRegex(ImportError, 'No unused'): review(p, SCENE, MIXED, dict(x=64,z=64))
            self.assertEqual(p.overrides, {}); self.assertEqual(p.undo_stack, [])

    def test_source_drift_during_review_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            p = self.project(directory)
            def drift(scene):
                p.name = 'Drift'; return source_map()
            with patch.object(p, '_environment_source', side_effect=drift):
                with self.assertRaisesRegex(ProjectError, 'changed while'): review(p, SCENE, MIXED, dict(x=64,z=0))
            self.assertEqual(p.overrides, {}); self.assertEqual(p.undo_stack, [])

    def test_unknown_height_components_and_descriptor_overflow(self):
        with tempfile.TemporaryDirectory() as directory:
            p = self.project(directory); source = source_map()
            appearance = dict(donor_entity_id=ACTOR)
            p.overrides[ACTOR] = dict(ActorAppearance=appearance)
            with patch.object(p, '_environment_source', return_value=source):
                r = review(p, SCENE, MIXED, dict(x=64,z=0))
                self.apply_review(p,r)
                self.assertEqual(p.overrides[ACTOR]['ActorAppearance'], appearance)
                self.assertEqual(p.overrides[ACTOR]['Transform']['position'], dict(x=192))
                self.assertIsNone(p.imports[SCENE]['actors'][0]['imported_transform']['position']['y'])
                p.undo()
            overflow = bytearray(source); struct.pack_into('<h', overflow, 4*32, 32767)
            with patch.object(p, '_environment_source', return_value=bytes(overflow)):
                before = deepcopy(p.overrides); redo = deepcopy(p.redo_stack)
                with self.assertRaisesRegex(ProjectError, 'signed MAP'): review(p, SCENE, MIXED, dict(x=64,z=0))
                self.assertEqual(p.overrides, before); self.assertEqual(p.redo_stack, redo)
                self.assertEqual(p.undo_stack, [])


if __name__ == '__main__':
    unittest.main()
