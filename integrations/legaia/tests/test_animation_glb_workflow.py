"""Private-disc workflow checks: source binding, shared ownership and normal Build."""
import base64
from copy import deepcopy
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile

from importer.core import decompress_lzs
from importer.pipeline import _disc_context, import_scene
from importer.scene_animation import load_scene_actor_animation_catalog
from sdk.animation_glb import apply_import, export_clip, preview_import
from sdk.build import build_project
from sdk.project import ProjectError, ProjectService, digest
from test_importer_export import parse_glb
from test_model_primitive_workflow import http_server


def shifted(raw, *, node=0, frame=0, axis=0, amount=1):
    doc, _ = parse_glb(raw)
    channel = next(item for item in doc['animations'][0]['channels']
                   if item['target'] == {'node': node, 'path': 'translation'})
    sampler = doc['animations'][0]['samplers'][channel['sampler']]
    accessor = doc['accessors'][sampler['output']]
    view = doc['bufferViews'][accessor['bufferView']]
    json_length = struct.unpack_from('<I', raw, 12)[0]
    offset = 28 + json_length + view.get('byteOffset', 0) + accessor.get('byteOffset', 0) + frame * 12 + axis * 4
    result = bytearray(raw)
    value = struct.unpack_from('<f', result, offset)[0]
    struct.pack_into('<f', result, offset, value + amount)
    return bytes(result)


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
class AnimationGlbWorkflow(unittest.TestCase):
    def test_current_mesh_export_keeps_native_channel_roundtrip(self):
        from hashlib import sha256
        from importer.assets import decode_tmd
        with tempfile.TemporaryDirectory() as directory:
            project=self.project(directory);owner='scene://town01/actors/man-p1/0011'
            asset=project.animation_authoring_options(owner)['binding']['asset_semantic_id']
            source=project._model_source(asset,project.active_scene)
            project.translate_model_object(asset,0,[2,0,0],sha256(source).hexdigest())
            current=decode_tmd(project.read_model_replacement(asset,project.model_overrides[asset]))
            before=deepcopy((project._document(),project.imports,project.undo_stack,project.redo_stack))
            with http_server(project) as (_,post):
                exported=self.export(post,owner);raw=base64.b64decode(exported['glb_base64']);doc,payload=parse_glb(raw)
                primitive=doc['meshes'][0]['primitives'][0];accessor=doc['accessors'][primitive['attributes']['POSITION']];view=doc['bufferViews'][accessor['bufferView']]
                vertex=current['vertices'][current['triangles'][0][0]]
                self.assertEqual(list(struct.unpack_from('<3f',payload,view.get('byteOffset',0)+accessor.get('byteOffset',0))),[vertex[0],-vertex[1],vertex[2]])
                status,review=post('/api/animation-glb-preview',dict(entity_id=owner,glb_base64=exported['glb_base64'],binding=exported['binding']))
                self.assertEqual(status,200,review);self.assertEqual(review['changed_axes'],0)
            self.assertEqual((project._document(),project.imports,project.undo_stack,project.redo_stack),before)

    def project(self, directory, scene='town01'):
        project = ProjectService(Path(directory))
        project.disc_path = os.environ['LEGAIA_DISC_BIN']
        with _disc_context(project.disc_path):
            project.import_metadata(import_scene(project.disc_path, scene))
        return project

    def export(self, post, owner):
        status, result = post('/api/animation-glb-export', dict(entity_id=owner, clip_fps=15))
        self.assertEqual(status, 200, result)
        self.assertEqual(Path(result['path']).read_bytes(), base64.b64decode(result['glb_base64']))
        self.assertEqual(json.loads(Path(result['binding_path']).read_text(encoding='utf-8')), result['binding'])
        return result

    def test_cubic_http_review_pose_history_reopen_and_exact_build_bank(self):
        from test_animation_glb import encode
        from test_animation_glb_cubic import cubic_channel
        with tempfile.TemporaryDirectory() as directory:
            project = self.project(directory)
            owner = 'scene://town01/actors/man-p1/0011'
            with http_server(project) as (_, post):
                exported = self.export(post, owner)
                doc, payload = parse_glb(base64.b64decode(exported['glb_base64']))
                payload = payload[:doc['buffers'][0]['byteLength']]
                # Every existing TR track uses in/value/out records. Existing
                # frame times coincide with keys, so exactly one edit is expected.
                for channel in doc['animations'][0]['channels']:
                    sampler = doc['animations'][0]['samplers'][channel['sampler']]
                    accessor = doc['accessors'][sampler['output']]
                    view = doc['bufferViews'][accessor['bufferView']]
                    width = 3 if channel['target']['path'] == 'translation' else 4
                    start = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
                    rows = [list(row) for row in struct.iter_unpack(f'<{width}f',
                            payload[start:start+accessor['count']*width*4])]
                    if channel['target'] == {'node': 0, 'path': 'translation'}:
                        rows[1][0] += 1
                    doc, payload = cubic_channel(doc, payload, channel['target']['path'],
                        [([0]*width, row, [0]*width) for row in rows], channel['target']['node'])
                raw = encode(doc, payload)
                body = dict(entity_id=owner, binding=exported['binding'],
                            glb_base64=base64.b64encode(raw).decode())
                before = digest(dict(overrides=project.overrides, undo=project.undo_stack))
                status, review = post('/api/animation-glb-preview', body)
                self.assertEqual(status, 200, review)
                self.assertEqual(review['changed_axes'], 1)
                self.assertEqual(review['changes'][0]['frame_index'], 1)
                self.assertEqual(review['changes'][0]['field'], 'translation.x')
                status, pose = post('/api/animation-glb-pose-preview', body)
                self.assertEqual(status, 200, pose)
                self.assertEqual(pose['report']['candidate_sha256'], review['candidate_sha256'])
                self.assertEqual(digest(dict(overrides=project.overrides, undo=project.undo_stack)), before)
                # Uploaded GLB bytes remain part of review identity even when
                # changed metadata leaves the sampled candidate unchanged.
                changed_doc = deepcopy(doc)
                changed_doc['asset']['generator'] = 'changed-after-review'
                status, _ = post('/api/animation-glb-import', dict(body,
                    glb_base64=base64.b64encode(encode(changed_doc,payload)).decode(),
                    review_key=review['review_key']))
                self.assertEqual(status, 400)
                self.assertEqual(digest(dict(overrides=project.overrides, undo=project.undo_stack)), before)
                status, applied = post('/api/animation-glb-import', dict(body, review_key=review['review_key']))
                self.assertEqual(status, 200, applied)
                self.assertEqual(len(project.undo_stack), 1)
                contribution = deepcopy(project.overrides[owner]['AnimationChannels'])
                project.undo(); self.assertFalse(project.overrides)
                project.redo(); self.assertEqual(project.overrides[owner]['AnimationChannels'], contribution)
                project.save()
                reopened = ProjectService.open(project.root / 'project.legaia.json')
                self.assertEqual(reopened.overrides[owner]['AnimationChannels'], contribution)
                with _disc_context(project.disc_path):
                    catalog = load_scene_actor_animation_catalog(project.disc_path, 'town01')
                    expected, _ = catalog.authored_bank({owner: contribution})
                before_build = digest(dict(overrides=reopened.overrides, undo=reopened.undo_stack))
                built = build_project(reopened)
                with zipfile.ZipFile(built['path']) as archive:
                    actual = decompress_lzs(archive.read('assets/town01-animation.lzs'), len(expected))[0]
                self.assertEqual(actual, expected)
                self.assertEqual(digest(dict(overrides=reopened.overrides, undo=reopened.undo_stack)), before_build)

    def test_http_review_pose_history_save_and_normal_build(self):
        for scene, index, extension in [('town01', 11, 'lzs'), ('dolk2', 1, 'bin')]:
            with self.subTest(scene=scene), tempfile.TemporaryDirectory() as directory:
                project = self.project(directory, scene)
                owner = f'scene://{scene}/actors/man-p1/{index:04d}'
                imported = digest(project.imports)
                with http_server(project) as (_, post):
                    export = self.export(post, owner)
                    # Browser JSON.stringify normalizes integral floats to ints.
                    export['binding']['clip_fps'] = int(export['binding']['clip_fps'])
                    raw = shifted(base64.b64decode(export['glb_base64']))
                    body = dict(entity_id=owner, binding=export['binding'], glb_base64=base64.b64encode(raw).decode())
                    status, review = post('/api/animation-glb-preview', body)
                    self.assertEqual(status, 200, review)
                    self.assertEqual(review['changed_axes'], 1)
                    self.assertEqual(review['changes'][0]['field'], 'translation.x')
                    self.assertFalse(project.overrides)
                    status, pose = post('/api/animation-glb-pose-preview', body)
                    self.assertEqual(status, 200, pose)
                    self.assertEqual(pose['report']['review_key'], review['review_key'])
                    self.assertEqual(pose['animation']['representation'], 'file_preview')
                    before = len(project.undo_stack)
                    status, error = post('/api/animation-glb-import', dict(body, review_key='0' * 64))
                    self.assertEqual(status, 400)
                    self.assertEqual(len(project.undo_stack), before)
                    status, applied = post('/api/animation-glb-import', dict(body, review_key=review['review_key']))
                    self.assertEqual(status, 200, applied)
                    self.assertEqual(len(project.undo_stack), before + 1)
                    contribution = deepcopy(project.overrides[owner]['AnimationChannels'])
                    project.undo(); self.assertFalse(project.overrides)
                    project.redo(); self.assertEqual(project.overrides[owner]['AnimationChannels'], contribution)
                    project.save(); reopened = ProjectService.open(project.root / 'project.legaia.json')
                    self.assertEqual(reopened.overrides[owner]['AnimationChannels'], contribution)
                    status, _ = post('/api/animation-glb-preview', body)
                    self.assertEqual(status, 400, 'old export must be stale after Apply')
                    with _disc_context(project.disc_path):
                        catalog = load_scene_actor_animation_catalog(project.disc_path, scene)
                        expected, _ = catalog.authored_bank({owner: contribution})
                    output = build_project(reopened)
                    with zipfile.ZipFile(output['path']) as archive:
                        payload = archive.read(f'assets/{scene}-animation.{extension}')
                        actual = decompress_lzs(payload, len(expected))[0] if extension == 'lzs' else payload
                    self.assertEqual(actual, expected)
                    self.assertEqual(digest(project.imports), imported)

    def test_shared_axes_are_preserved_without_adopting_other_owners(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.project(directory)
            owner = 'scene://town01/actors/man-p1/0011'
            options = project.animation_authoring_options(owner)
            other = next(item for item in options['shared_actor_ids'] if item != owner)
            source = project.animation_channel_values(owner, 0, 0)['retail']
            def contribution(axis):
                return dict(animation_id=options['binding']['semantic_id'],
                    source_record_sha256=options['binding']['source_record']['record_sha256'],
                    edits=[dict(frame_index=0, object_index=0, translation={axis: source['translation'][axis] ^ 1})])
            project.command(dict(type='set_animation_channels', entity_id=owner, value=contribution('z')))
            project.command(dict(type='set_animation_channels', entity_id=other, value=contribution('y')))
            other_before = deepcopy(project.overrides[other])
            with http_server(project) as (_, post):
                exported = self.export(post, owner)
                binding = exported['binding']
                original = base64.b64decode(exported['glb_base64'])
                noop = preview_import(project, owner, original, binding)
                self.assertEqual(noop['changed_axes'], 0)
                self.assertEqual(noop['ownership']['actor_axis_count_after'], 1)
                with self.assertRaisesRegex(ProjectError, 'no source-quantized'):
                    apply_import(project, owner, original, binding, noop['review_key'])
                candidate = shifted(original)
                review = preview_import(project, owner, candidate, binding)
                self.assertEqual(review['ownership']['actor_axis_count_before'], 1)
                self.assertEqual(review['ownership']['actor_axis_count_after'], 2)
                apply_import(project, owner, candidate, binding, review['review_key'])
                axes = project.overrides[owner]['AnimationChannels']['edits'][0]['translation']
                self.assertEqual(set(axes), {'x', 'z'})
                self.assertEqual(project.overrides[other], other_before)
                exported = self.export(post, owner)
                # GLB Y is reflected. Reverting another owner's axis must reject,
                # including the case where removing our own contribution is insufficient.
                value = source['translation']['y'] ^ 1
                conflicting = shifted(base64.b64decode(exported['glb_base64']), axis=1,
                                      amount=value - source['translation']['y'])
                unchanged = digest(dict(overrides=project.overrides, undo=project.undo_stack))
                with self.assertRaisesRegex((ProjectError, ValueError), 'another actor|Another actor|Conflicting'):
                    preview_import(project, owner, conflicting, exported['binding'])
                self.assertEqual(digest(dict(overrides=project.overrides, undo=project.undo_stack)), unchanged)

    def test_equal_ownership_changes_and_unsupported_contexts_invalidate_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.project(directory)
            owner = 'scene://town01/actors/man-p1/0011'
            options = project.animation_authoring_options(owner)
            other = next(item for item in options['shared_actor_ids'] if item != owner)
            source = project.animation_channel_values(owner, 0, 0)
            value = dict(animation_id=options['binding']['semantic_id'],
                         source_record_sha256=source['source_record_sha256'],
                         edits=[dict(frame_index=0, object_index=0, translation={'x': source['retail']['translation']['x'] ^ 1})])
            project.command(dict(type='set_animation_channels', entity_id=owner, value=value))
            with http_server(project) as (_, post):
                exported = self.export(post, owner)
                raw = base64.b64decode(exported['glb_base64'])
                project.command(dict(type='set_animation_channels', entity_id=other, value=value))
                self.assertEqual(project.animation_record_source(owner, 'effective')[0],
                                 project.animation_record_source(other, 'effective')[0])
                with self.assertRaisesRegex(ProjectError, 'binding differs'):
                    preview_import(project, owner, raw, exported['binding'])
                project.mode = 'live'
                with self.assertRaisesRegex(ProjectError, 'Edit mode'):
                    export_clip(project, owner, 15)
                project.mode = 'edit'
                for fps in (True, 0, 121, float('nan')):
                    with self.subTest(fps=fps), self.assertRaises(ProjectError):
                        export_clip(project, owner, fps)


if __name__ == '__main__':
    unittest.main()
