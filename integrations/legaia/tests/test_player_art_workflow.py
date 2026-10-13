import base64
from copy import deepcopy
import math
import os
from pathlib import Path
import tempfile
import unittest

from importer.animation_glb import _read_glb
from importer.model_glb import _write_glb
from importer.player_art_animation import load_stream
from sdk.project import ProjectService
from sdk.project_assets import source_key
from sdk import player_art_animation as arts
from sdk.player_battle import resources as model_resources, preview as model_preview
from sdk.player_model_authoring import current, export as model_export, review, apply
from test_model_primitive_workflow import http_server


def check_literal_pose(test, base, stream, decoded, frame, geometry, transforms):
    for obj, transform, part in zip(base['geometry']['objects'], transforms, base['assembly']['animation_part_indices']):
        raw = decoded[2 + (frame * stream['part_count'] + part) * 9:2 + (frame * stream['part_count'] + part + 1) * 9]
        channels = [raw[0] | (raw[2] & 15) << 8, raw[1] | (raw[2] >> 4) << 8,
                    raw[3] | (raw[5] & 15) << 8, raw[4] | (raw[5] >> 4) << 8,
                    raw[6] | (raw[8] & 15) << 8, raw[7] | (raw[8] >> 4) << 8]
        translation = [v - 4096 if v & 2048 else v for v in channels[:3]]
        test.assertEqual(transform['translation'], translation)
        test.assertEqual(transform['rotation_psx'], channels[3:])
        rx, ry, rz = [v * math.pi / 2048 for v in channels[3:]]
        sx, cx, sy, cy, sz, cz = math.sin(rx), math.cos(rx), math.sin(ry), math.cos(ry), math.sin(rz), math.cos(rz)
        matrix = [[cz * cy, cz * sy * sx - sz * cx, cz * sy * cx + sz * sx],
                  [sz * cy, sz * sy * sx + cz * cx, sz * sy * cx - cz * sx],
                  [-sy, cy * sx, cy * cx]]
        for index in range(obj['vertex_start'], obj['vertex_start'] + obj['vertex_count']):
            source = base['geometry']['vertices'][index]
            expected = [sum(matrix[axis][j] * source[j] for j in range(3)) + translation[axis] for axis in range(3)]
            for actual, wanted in zip(geometry['vertices'][index], expected):
                test.assertAlmostEqual(actual, wanted, delta=1e-7)


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'), 'Private retail source is required')
class PlayerArtWorkflowTests(unittest.TestCase):
    def test_all_stream_first_last_frames_on_retail_parts(self):
        with tempfile.TemporaryDirectory() as root:
            p = ProjectService(Path(root)); p.disc_path = os.environ['LEGAIA_DISC_BIN']; p.save()
            ctx = dict(expected_project_path=str(p.root), expected_source_key=source_key(p))
            models = model_resources(p, **ctx); report = arts.resources(p, **ctx)
            bases = {m['player_index']:model_preview(p, **ctx, asset_id=m['semantic_id'], catalog_source_key=models['catalog']['source_key'], equipped=[0]*5) for m in models['catalog']['models']}
            held = deepcopy((p._document(), p.undo_stack, p.redo_stack)); frames = 0
            for stream in report['catalog']['streams']:
                _, actual, _, decoded = load_stream(p.disc_path, stream['semantic_id'], report['catalog']['source_key'])
                self.assertEqual(stream, actual)
                base = bases[stream['player_index']]
                for frame in (0, stream['frame_count'] - 1):
                    geometry, transforms = arts.frame_geometry(base, stream, decoded, frame)
                    check_literal_pose(self, base, stream, decoded, frame, geometry, transforms)
                    self.assertEqual(geometry['textures'], base['geometry']['textures'])
                    self.assertNotIn('triangle_normals', geometry)
                    frames += 1
            self.assertEqual(frames, 174)
            self.assertEqual(held, (p._document(), p.undo_stack, p.redo_stack))

    def test_http_current_geometry_archive_and_source_guards(self):
        with tempfile.TemporaryDirectory() as root:
            p = ProjectService(Path(root)); p.disc_path = os.environ['LEGAIA_DISC_BIN']; p.save()
            models = model_resources(p, str(p.root), source_key(p))
            with http_server(p) as (_, post):
                for model in models['catalog']['models']:
                    ctx = dict(expected_project_path=str(p.root), expected_source_key=source_key(p), asset_id=model['semantic_id'], catalog_source_key=models['catalog']['source_key'], equipped=[0]*5)
                    exported = model_export(p, **ctx); doc, binary = _read_glb(base64.b64decode(exported['glb_base64'])); doc['nodes'][0]['translation'] = [10, 0, 0]
                    payload = base64.b64encode(_write_glb(doc, binary)).decode(); proposed = review(p, **ctx, binding=exported['binding'], glb_base64=payload); apply(p, **ctx, binding=exported['binding'], glb_base64=payload, review_key=proposed['review_key'])
                    ctx['expected_source_key'] = source_key(p)
                    saved = current(p, **ctx); report = arts.resources(p, ctx['expected_project_path'], ctx['expected_source_key'])
                    held = deepcopy((p._document(), p.undo_stack, p.redo_stack))
                    for role in ('main', 'base'):
                        stream = next(s for s in report['catalog']['streams'] if s['player_index'] == model['player_index'] and s['archive_role'] == role)
                        record = next(r for r in report['catalog']['records'] if stream['semantic_id'] in r['eligible_stream_ids'])
                        args = dict(ctx, art_source_key=report['catalog']['source_key'], stream_id=stream['semantic_id'], art_record_id=record['semantic_id'], layer='current', expected_current_sha256=saved['effective_file_sha256'])
                        status, value = post('/api/player-art-pose', dict(args, frame_index=stream['frame_count']-1)); self.assertEqual(status, 200, value)
                        playback = value['playback']; self.assertEqual(playback['base_inspection']['geometry']['vertices'], saved['geometry']['vertices'])
                        check_literal_pose(self, playback['base_inspection'], stream, base64.b64decode(playback['decoded_stream_base64']), value['frame_index'], value['geometry'], value['object_transforms'])
                        for key, bad in [('expected_current_sha256','stale'),('art_source_key','stale'),('stream_id','foreign'),('art_record_id','foreign'),('frame_index',True),('layer','foreign')]:
                            changed = dict(args,frame_index=0); changed[key] = bad
                            self.assertEqual(post('/api/player-art-pose',changed)[0],400)
                    self.assertEqual(held, (p._document(), p.undo_stack, p.redo_stack))
