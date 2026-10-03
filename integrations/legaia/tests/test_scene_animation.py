"""Coordinated tracks retain source mesh bindings and never mutate a project."""
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.core import ImportError as RetailImportError
from sdk.project import ProjectError, ProjectService, digest
from sdk.scene_animation import prepare_scene_animation, _json_size, MAX_METADATA_BYTES
from sdk.scene_preview import preview_project, source_key
from importer.animation import pose_vertices
from test_project_workflow import synthetic_scene


def geometry(offset=0):
    return dict(vertices=[[offset, 0, 0], [offset + 10, -20, 0], [offset + 10, 0, 5]],
        triangles=[[0, 1, 2]], triangle_colors=[[[128, 128, 128]] * 3],
        triangle_uvs=[[[1, 2], [3, 4], [5, 6]]], triangle_materials=[0],
        materials=[dict(textured=True, clut=0x123, tpage=0x41, semi_transparent=True,
                        blend={'qualified': 'unchanged'})],
        objects=[dict(object_index=0, vertex_start=0, vertex_count=3,
                      triangle_start=0, triangle_count=1, raw_object_word6=0x00808080)],
        coordinate_system='actor_local_y_down_source_units',
        textures=[{'material_index': 0, 'private-pixels': 'not copied'}])


def full_clip(preview, asset_id, frames=3):
    result = deepcopy(preview)
    result['vertices'][0][0] -= 50  # Full model vertices can be unposed.
    result['coordinate_system'] = 'retail_psx_actor_local_y_down'
    result['animation'] = dict(frame_count=frames, asset_semantic_id=asset_id,
        clip_id='placement', source_clip_id='animation://fixture/scene-anm/0001',
        source_record={'private': 'not copied'}, looping=None, timing={'fps': None})
    result['frames'] = []
    for index in range(frames):
        vertices = deepcopy(preview['vertices'])
        for v in vertices: v[0] += index * 7
        result['frames'].append(dict(frame_index=index, vertices=vertices,
            object_transforms=[dict(object_index=0, translation=[index * 7, 0, 0])],
            coordinate_system='retail_psx_actor_local_y_down'))
    return result


class SceneAnimationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.project = ProjectService(Path(self.directory.name))
        document = synthetic_scene()
        original = document['actors'][0]
        for n in (2, 3):
            actor = deepcopy(original)
            actor['semantic_id'] = original['semantic_id'].rsplit('/', 1)[0] + f'/{n:04d}'
            document['actors'].append(actor)
        self.project.import_metadata(document)
        path = Path(self.directory.name) / 'fixture.bin'; path.write_bytes(b'synthetic source')
        self.project.disc_path = str(path)
        self.actor_ids = [a['semantic_id'] for a in document['actors']]
        self.asset_id = document['assets']['models'][0]['semantic_id']

    def scene(self, representation='authored'):
        project = self.project
        key = source_key(project)
        geo = digest({'geometry': 1})
        pose_kind = 'imported_scene_animation_frame0'
        entities = [dict(entity_id=actor, asset_id=self.asset_id, geometry_key=geo,
            renderable=True, source_actor_id=actor, pose_kind=pose_kind,
            model_to_scene=[1, 0, 0, 100 + n, 0, -1, 0, 0, 0, 0, 1, 200, 0, 0, 0, 1])
            for n, actor in enumerate(self.actor_ids)]
        entities[1]['pose_kind'] = 'authored_initial_animation_frame0'
        entities[2]['pose_kind'] = 'single_object_static'
        return dict(schema='legaia.scene-preview.v1', scene_id=project.active_scene,
            source_key=source_key(preview_project(project, representation)), project_source_key=key,
            assets=[dict(asset_id=self.asset_id, geometry_key=geo, pose_kind=pose_kind, preview=geometry())],
            entities=entities)

    def prepare(self, scene, loader, representation='authored'):
        return prepare_scene_animation(self.project, scene, loader, representation, source_key(self.project))

    def test_shared_track_detached_baseline_and_exact_coverage(self):
        scene = self.scene(); baseline = deepcopy(scene)
        clip = full_clip(scene['assets'][0]['preview'], self.asset_id)
        pristine = deepcopy(clip)
        calls = []
        project_before = deepcopy(self.project._document()), deepcopy(self.project.undo_stack), deepcopy(self.project.assets.records)
        def loader(instance, asset):
            calls.append((deepcopy(instance), deepcopy(asset)))
            instance['model_to_scene'][3] = 999
            asset['source_record']['loader_private'] = True
            return clip
        report = self.prepare(scene, loader)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1]['semantic_id'], self.asset_id)
        self.assertIn('source_record', calls[0][1])
        self.assertEqual(set(report), {'schema_version', 'scene_id', 'project_source_key', 'scene_source_key',
            'representation', 'tracks', 'instances', 'unavailable_instances', 'metrics', 'limitations',
            'project_changed', 'gameplay_verified'})
        self.assertEqual(report['schema_version'], 'legaia.scene-animation.v1')
        self.assertFalse(report['project_changed']); self.assertFalse(report['gameplay_verified'])
        self.assertEqual(report['project_source_key'], source_key(self.project))
        self.assertEqual(report['scene_source_key'], scene['source_key'])
        self.assertEqual(len(report['tracks']), 1)
        track = report['tracks'][0]
        self.assertEqual(set(track), {'geometry_key', 'asset_id', 'clip_id', 'pose_kind', 'frame_count', 'vertex_count', 'frames'})
        self.assertEqual(track['clip_id'], 'animation://fixture/scene-anm/0001')
        self.assertEqual(track['pose_kind'], 'imported_scene_animation_frame0')
        self.assertEqual(track['frames'], [f['vertices'] for f in clip['frames']])

        self.assertEqual(track['frames'][0], scene['assets'][0]['preview']['vertices'])
        self.assertEqual([i['entity_id'] for i in report['instances']], self.actor_ids[:2])
        self.assertTrue(all(set(i) == {'entity_id', 'geometry_key', 'asset_id', 'source_actor_id'} for i in report['instances']))
        self.assertEqual(report['unavailable_instances'][0]['entity_id'], self.actor_ids[2])
        self.assertEqual(set(report['unavailable_instances'][0]), {'entity_id', 'geometry_key', 'asset_id', 'pose_kind', 'reason'})
        self.assertEqual(report['metrics'], dict(animated_instances=2, static_or_unavailable_instances=1,
            track_count=1, frame_vertex_count=9, max_frame_count=3))
        self.assertEqual(scene, baseline)
        self.assertEqual(clip, pristine)
        self.assertEqual((self.project._document(), self.project.undo_stack, self.project.assets.records), project_before)
        track['frames'][0][0][0] = 777
        self.assertEqual(clip, pristine); self.assertEqual(scene, baseline)

    def test_optional_normal_channels_match_source_and_actual_samples(self):
        scene = self.scene()
        baseline = scene['assets'][0]['preview']
        baseline.update(triangle_normals=[[[4096, 0, 0]]*3],
                        normal_preview=dict(status='source_unposed',coordinate_system='retail_tmd_object_local'))
        clip = full_clip(baseline, self.asset_id)
        clip.update(posed=False, vertices=deepcopy(baseline['vertices']))
        for index, frame in enumerate(clip['frames']):
            frame['posed'] = True
            frame['object_transforms'][0]['rotation_psx'] = [0, 0, index*1024]
            frame['vertices'] = pose_vertices(clip['vertices'], clip['objects'], frame['object_transforms'])
        report = self.prepare(scene, lambda *args: clip)
        normal = report['tracks'][0]['normal_pose']
        self.assertEqual(normal['source']['triangle_normals'], baseline['triangle_normals'])
        self.assertEqual(normal['frames'][1]['object_transforms'][0]['rotation_psx'], [0, 0, 1024])
        normal['source']['triangle_normals'][0][0][0] = 0
        self.assertEqual(clip['triangle_normals'][0][0][0], 4096)
        for mutate in [lambda c: c['frames'][1]['vertices'][0].__setitem__(0, 999),
                       lambda c: c['frames'][1]['object_transforms'][0]['rotation_psx'].__setitem__(0, 4096),
                       lambda c: c['triangle_normals'][0][0].__setitem__(0, 5000)]:
            changed = deepcopy(clip); mutate(changed)
            with self.assertRaises(ProjectError):
                self.prepare(scene, lambda *args: changed)
        unknown = deepcopy(clip); unknown['frames'][1]['coordinate_system'] = 'unknown'
        self.assertNotIn('normal_pose', self.prepare(scene, lambda *args: unknown)['tracks'][0])
        with patch('sdk.scene_animation.MAX_FRAME_NORMAL_CORNERS', 0):
            limited = self.prepare(scene, lambda *args: clip)['tracks'][0]
            self.assertNotIn('normal_pose', limited)
            self.assertEqual(limited['frames'], [f['vertices'] for f in clip['frames']])
        with patch('sdk.scene_animation._json_size', side_effect=lambda value:
                   MAX_METADATA_BYTES+1 if 'normal_pose' in value else _json_size(value)):
            limited = self.prepare(scene, lambda *args: clip)['tracks'][0]
            self.assertNotIn('normal_pose', limited)
            self.assertEqual(limited['frames'], [f['vertices'] for f in clip['frames']])
        malformed = deepcopy(scene); malformed['assets'][0]['preview']['normal_source'] = None
        with self.assertRaisesRegex(ProjectError, 'source evidence'):
            self.prepare(malformed, lambda *args: clip)

    def test_retail_authored_keys_remain_distinct_and_stale_checks_wrap_loader(self):
        self.project.overrides[self.actor_ids[0]] = {'Transform': {'position': {'x': 500}}}
        scene = self.scene('retail')
        self.assertNotEqual(scene['source_key'], scene['project_source_key'])
        report = self.prepare(scene, lambda *_: full_clip(scene['assets'][0]['preview'], self.asset_id), 'retail')
        self.assertEqual(report['representation'], 'retail')
        self.assertEqual(report['scene_source_key'], scene['source_key'])
        with self.assertRaisesRegex(ProjectError, 'stale'):
            self.prepare(scene, lambda *_: self.fail('stale scene loaded'))
        scene = self.scene()
        for field, invalid in (('source_key', '0' * 64), ('project_source_key', '0' * 64), ('scene_id', 'scene://other')):
            bad = deepcopy(scene); bad[field] = invalid
            with self.subTest(field=field), self.assertRaises(ProjectError):
                self.prepare(bad, lambda *_: self.fail('stale scene loaded'))
        def mutate_source(*_):
            self.project.overrides[self.actor_ids[0]]['Transform']['position']['x'] += 1
            return full_clip(scene['assets'][0]['preview'], self.asset_id)
        with self.assertRaisesRegex(ProjectError, 'changed'):
            self.prepare(scene, mutate_source)
        self.project.mode = 'live'
        with self.assertRaisesRegex(ProjectError, 'Edit mode'):
            self.prepare(self.scene(), lambda *_: self.fail('Live mode loaded'))

    def test_unavailable_decode_static_draft_and_environment_coverage(self):
        scene = self.scene()
        draft = 'authored-actor://fixture'
        self.project.actor_drafts[draft] = dict(scene_id=self.project.active_scene, donor_entity_id=self.actor_ids[0],
            position={'x': 704, 'z': 704}, name='Draft')
        scene = self.scene()  # Draft changes source identity.
        scene['entities'].append(dict(entity_id=draft, geometry_key=None, asset_id=None, kind='actor_draft',
            pose_kind='unavailable', renderable=False, reason='Draft source is unavailable'))
        scene['entities'].append(dict(entity_id='environment://fixture/ground', geometry_key=None,
            asset_id=None, kind='environment', renderable=False))
        def absent(*_): raise RetailImportError('Verified source clip cannot be decoded')
        report = self.prepare(scene, absent)
        self.assertEqual(report['tracks'], []); self.assertEqual(report['instances'], [])
        self.assertEqual([r['entity_id'] for r in report['unavailable_instances']], self.actor_ids + [draft])
        self.assertEqual(report['metrics'], dict(animated_instances=0, static_or_unavailable_instances=4,
            track_count=0, frame_vertex_count=0, max_frame_count=0))
        self.assertEqual(report['unavailable_instances'][0]['reason'], 'Verified source clip cannot be decoded')
        def malformed(*_): raise ProjectError('Contradictory source metadata')
        with self.assertRaisesRegex(ProjectError, 'Contradictory'): self.prepare(scene, malformed)
        with self.assertRaises(TypeError): self.prepare(scene, lambda *_: (_ for _ in ()).throw(TypeError('bug')))

    def test_complete_track_budgets_never_truncate_and_count_rejections(self):
        scene = self.scene()
        second_key = digest({'geometry': 2})
        scene['assets'].append(dict(asset_id=self.asset_id, geometry_key=second_key,
            pose_kind='reference_global_loop', preview=geometry(30)))
        scene['entities'][2].update(geometry_key=second_key, pose_kind='reference_global_loop')
        by_key = {asset['geometry_key']: asset['preview'] for asset in scene['assets']}
        with patch('sdk.scene_animation.MAX_FRAME_VERTICES', 10):
            report = self.prepare(scene, lambda instance, _: full_clip(by_key[instance['geometry_key']], self.asset_id))
        self.assertEqual(len(report['tracks']), 1)
        self.assertEqual(report['tracks'][0]['frame_count'], 3)
        self.assertEqual(report['metrics']['frame_vertex_count'], 9)
        self.assertIn('1 complete source track(s) omitted', report['limitations'][-1])
        self.assertTrue(all('budget' in r['reason'] for r in report['unavailable_instances']))
        one = self.scene()
        for patched, value, frames in (('MAX_FRAMES', 2, 3), ('MAX_VERTICES_PER_FRAME', 2, 3),
                                      ('MAX_METADATA_BYTES', 2500, 100)):
            with self.subTest(budget=patched), patch('sdk.scene_animation.' + patched, value):
                report = self.prepare(one, lambda *_: full_clip(one['assets'][0]['preview'], self.asset_id, frames))
                self.assertEqual(report['tracks'], [])
                self.assertEqual(report['metrics']['frame_vertex_count'], 0)
                self.assertIn('1 complete source track(s) omitted', report['limitations'][-1])

    def test_mesh_frame_count_order_coordinates_and_frame0_are_source_qualified(self):
        scene = self.scene(); good = full_clip(scene['assets'][0]['preview'], self.asset_id)
        invalid = []
        bad = deepcopy(good); bad['triangles'][0] = [2, 1, 0]; invalid.append(bad)
        bad = deepcopy(good); bad['objects'][0]['vertex_start'] = 1; invalid.append(bad)
        bad = deepcopy(good); bad['materials'][0]['tpage'] ^= 1; invalid.append(bad)
        bad = deepcopy(good); bad['triangle_uvs'][0][0][0] += 1; invalid.append(bad)
        bad = deepcopy(good); bad['triangle_colors'][0][0][0] += 1; invalid.append(bad)
        bad = deepcopy(good); bad['animation']['frame_count'] = 2; invalid.append(bad)
        bad = deepcopy(good); bad['animation']['frame_count'] = 3.0; invalid.append(bad)
        bad = deepcopy(good); bad['animation']['asset_semantic_id'] = 'asset://other'; invalid.append(bad)
        bad = deepcopy(good); bad['animation']['source_clip_id'] = '0x801e1234'; invalid.append(bad)
        bad = deepcopy(good); bad['animation']['source_clip_id'] = 0; invalid.append(bad)
        bad = deepcopy(good); bad.pop('frames'); invalid.append(bad)
        bad = deepcopy(good); bad['frames'][1]['frame_index'] = 0; invalid.append(bad)
        bad = deepcopy(good); bad['frames'][2]['vertices'].pop(); invalid.append(bad)
        bad = deepcopy(good); bad['frames'][0]['vertices'][0][0] += 1; invalid.append(bad)
        for value in (float('nan'), float('inf'), True, '0', 10 ** 400):
            bad = deepcopy(good); bad['frames'][1]['vertices'][0][1] = value; invalid.append(bad)
        for n, loaded in enumerate(invalid):
            with self.subTest(malformed=n), self.assertRaises(ProjectError):
                self.prepare(scene, lambda *_: loaded)
        # Only changed coordinate labels/derived texture details may differ.
        changed = deepcopy(good); changed['textures'] = [{'private': 'new association'}]
        changed['materials'][0]['blend'] = {'derived': 'fresh'}
        self.assertEqual(self.prepare(scene, lambda *_: changed)['metrics']['track_count'], 1)
        arrays = deepcopy(good); arrays['frames'] = [f['vertices'] for f in arrays['frames']]
        arrays['animation'].pop('source_clip_id'); arrays['animation']['clip_id'] = 'idle'
        with self.assertRaises(ProjectError):
            self.prepare(scene, lambda *_: arrays)
        arrays['animation']['semantic_id'] = 'animation://fixture/scene-anm/0001'
        self.assertEqual(self.prepare(scene, lambda *_: arrays)['tracks'][0]['clip_id'], 'animation://fixture/scene-anm/0001')

    def test_exact_entity_geometry_and_source_actor_binding_reject_fabrication(self):
        scene = self.scene(); invalid = []
        bad = deepcopy(scene); bad['entities'].append(deepcopy(bad['entities'][0])); invalid.append(bad)
        bad = deepcopy(scene); bad['assets'].append(deepcopy(bad['assets'][0])); invalid.append(bad)
        bad = deepcopy(scene); bad['entities'][0]['geometry_key'] = 'a' * 64; invalid.append(bad)
        bad = deepcopy(scene); bad['entities'][0]['asset_id'] = 'asset://other'; invalid.append(bad)
        bad = deepcopy(scene); bad['entities'][0]['source_actor_id'] = None; invalid.append(bad)
        bad = deepcopy(scene); bad['entities'][0]['source_actor_id'] = 'scene://other/actor'; invalid.append(bad)
        bad = deepcopy(scene); bad['entities'][0]['entity_id'] = 'scene://other/actor'; invalid.append(bad)
        bad = deepcopy(scene); bad['entities'][0]['pose_kind'] = 'reference_party_idle'; invalid.append(bad)
        bad = deepcopy(scene); bad['entities'][0]['geometry_key'] = None; invalid.append(bad)
        bad = deepcopy(scene); bad['entities'][0]['renderable'] = 1; invalid.append(bad)
        for n, value in enumerate(invalid):
            with self.subTest(binding=n), self.assertRaises(ProjectError):
                self.prepare(value, lambda *_: self.fail('invalid source binding loaded'))
        with patch('sdk.scene_animation.MAX_TRACKS', 0), self.assertRaises(ProjectError):
            self.prepare(scene, lambda *_: self.fail('oversized source loaded'))
        with patch('sdk.scene_animation.MAX_INSTANCES', 2), self.assertRaises(ProjectError):
            self.prepare(scene, lambda *_: self.fail('oversized source loaded'))


if __name__ == '__main__':
    unittest.main()
