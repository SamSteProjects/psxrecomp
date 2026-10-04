"""Reviewed persistent TIM additions and mixed native pack delivery."""
from contextlib import nullcontext
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from importer.model_pack_archive import _archive
from importer.model_pack_composition import compose_model_pack_archive
from importer.texture_layout_allocation import resize_tim_image
from importer.textures import _pack_members
from sdk.project import ProjectService, ProjectError
from sdk.scene_preview import source_key
from sdk.build import authored_state_key
from sdk import texture_slots
from sdk.texture_allocation_build import prepare
from test_importer_texture_authoring import fixture
from test_importer_textures import tim, block
from test_model_pack_archive import archive_source
from test_project_workflow import synthetic_scene


class TextureSlotsWorkflow(unittest.TestCase):
    def setup_project(self, compressed=False):
        temp = tempfile.TemporaryDirectory(prefix='texture-slots-')
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        context, fake, catalog, _ = fixture(compressed=compressed)
        raw = bytearray(fake.raw)
        if compressed:
            for descriptor in range(2, 6):
                struct.pack_into('<I', raw, 12 + 8 * descriptor, len(raw))
        blob, _ = archive_source(bytes(raw))
        archive = _archive(blob)
        for _, locator in catalog.textures:
            locator['prot_entry_index'] = 1
            locator['semantic_id'] = locator['semantic_id'].replace('/5/', '/1/')
        context._items = {s['semantic_id']: (t, deepcopy(s)) for t, s in catalog.textures}
        p = ProjectService(root / 'project')
        disc = root / 'fixture.bin'
        disc.write_bytes(b'fixture')
        p.import_metadata(synthetic_scene(), str(disc))
        p.save()
        for mock in (patch.object(ProjectService, '_texture_context', return_value=context),
                     patch.object(context, '_archive', side_effect=lambda: nullcontext(archive))):
            mock.start()
            self.addCleanup(mock.stop)
        return p, context, archive, blob, list(context._items)

    def test_readonly_review_overlap_choice_apply_history_offline_open_and_tamper(self):
        p, context, archive, blob, ids = self.setup_project()
        content = tim(16, image=block(0, 0, 2, 1, bytes([1, 128, 255, 255])))
        before = deepcopy((p._document(), p.undo_stack, p.redo_stack))
        original_key = source_key(p)
        build_key = authored_state_key(p)
        args = (p, ids[0], content, original_key, 'New wall texture')
        report = texture_slots.review(*args)
        self.assertFalse(report['can_apply'])
        self.assertGreater(report['footprint']['potential_overlap_count'], 0)
        self.assertEqual((p._document(), p.undo_stack, p.redo_stack), before)
        self.assertFalse((p.root / 'Authored').exists())
        with self.assertRaises(ProjectError):
            texture_slots.apply(*args, False, report['review_key'])
        accepted = texture_slots.review(*args, True)
        with self.assertRaises(ProjectError):
            texture_slots.apply(*args, True, report['review_key'])
        result = texture_slots.apply(*args, True, accepted['review_key'])
        identifier = result['asset_id']
        binding = deepcopy(p.texture_additions[identifier])
        self.assertEqual(binding['slot_index'], 2)
        self.assertNotEqual(source_key(p), original_key)
        self.assertNotEqual(authored_state_key(p), build_key)
        self.assertEqual(len(p.undo_stack), 1)
        with self.assertRaises(ProjectError):
            texture_slots.apply(*args, True, accepted['review_key'])
        p.undo()
        self.assertFalse(p.texture_additions)
        p.redo()
        reopened = ProjectService.open(p.save())
        self.assertEqual(reopened.texture_additions, p.texture_additions)
        self.assertEqual(texture_slots.read(reopened, identifier, binding), content)
        self.assertFalse(reopened.dirty)
        self.assertFalse(p.texture_overrides)
        broken=deepcopy(reopened.texture_additions)
        reopened.texture_additions[identifier]['slot_index']+=1
        with self.assertRaises(ProjectError):
            reopened.save()
        reopened.texture_additions=broken
        from sdk.export_snapshot import capture_export_inputs
        _, files = capture_export_inputs(reopened)
        self.assertEqual(files['Authored/Textures/' + binding['asset_sha256'] + '.tim'], content)
        path = p.root / 'Authored' / 'Textures' / (binding['asset_sha256'] + '.tim')
        path.write_bytes(content[:-1] + bytes([content[-1] ^ 1]))
        with self.assertRaises(ProjectError):
            p.save()
        with self.assertRaises(ProjectError):
            ProjectService.open(p.root)

    def test_following_resize_reports_authored_slot_upload(self):
        p, context, archive, blob, ids = self.setup_project()
        content=tim(16,image=block(2,1,2,1,b'\x00\x80'*2))
        args=(p,ids[0],content,source_key(p),'Adjacent new texture',True)
        report=texture_slots.review(*args)
        result=texture_slots.apply(*args,report['review_key'])
        from sdk.texture_resize import review as resize_review
        original=context.original_tim(ids[0])
        report=resize_review(p,ids[0],sha256(original).hexdigest(),source_key(p),16,2,0,False)
        self.assertFalse(report['can_apply'])
        self.assertTrue(any(row['asset_id']==result['asset_id'] for row in report['footprint']['rows']))

    def test_http_exact_fields_pixels_stale_review_and_one_apply(self):
        import base64
        from test_model_primitive_workflow import http_server
        from importer.texture_png import decode_png
        p,context,archive,blob,ids=self.setup_project()
        content=tim(16,image=block(640,32,2,1,b'\x00\x80'*2))
        body=dict(anchor_asset_id=ids[0],source_key=source_key(p),label='HTTP texture',
                  accept_potential_overlap=True,content_base64=base64.b64encode(content).decode('ascii'))
        before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        with http_server(p) as (_,post):
            for bad in (dict(body,extra=1),dict(body,content_base64='!'),dict(body,source_key='stale'),dict(body,accept_potential_overlap=1)):
                status,_=post('/api/texture-slot-review',bad);self.assertEqual(status,400)
            status,report=post('/api/texture-slot-review',body);self.assertEqual(status,200,report)
            pixels=dict(body,review_key=report['review_key'],palette_index=0)
            status,result=post('/api/texture-slot-pixels',pixels);self.assertEqual(status,200,result)
            self.assertEqual(result['report'],report)
            image=decode_png(base64.b64decode(result['proposed_png_base64']));self.assertEqual((image['width'],image['height']),(2,1))
            for bad in (dict(pixels,palette_index=True),dict(pixels,review_key='0'*64),dict(pixels,palette_index=1)):
                status,_=post('/api/texture-slot-pixels',bad);self.assertEqual(status,400)
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
            status,result=post('/api/texture-slot-apply',dict(body,review_key=report['review_key']));self.assertEqual(status,200,result)
            self.assertTrue(result['texture_slot_report']['project_changed'])
            self.assertIn(result['texture_slot_report']['asset_id'],result['texture_additions'])
            self.assertTrue(result['project']['dirty'])
            self.assertEqual(len(p.undo_stack),1)
            status,_=post('/api/texture-slot-apply',dict(body,review_key=report['review_key']));self.assertEqual(status,400)

    def test_two_additions_resize_and_payload_edit_share_one_pack_reopen(self):
        for compressed in (False, True):
            p, context, archive, blob, ids = self.setup_project(compressed)
            contents = [tim(16, image=block(640, 32, 2, 1, b'\x00\x80' * 2)),
                        tim(16, image=block(768, 32, 2, 1, b'\xff\xff' * 2))]
            for content in contents:
                args = (p, ids[0], content, source_key(p), 'Texture ' + str(len(p.texture_additions)), True)
                report = texture_slots.review(*args)
                texture_slots.apply(*args, report['review_key'])
            p.undo()
            self.assertEqual(len(p.texture_additions), 1)
            p.redo()
            self.assertEqual(sorted(b['slot_index'] for b in p.texture_additions.values()), [2, 3])
            old = context.original_tim(ids[0])
            resized, _ = resize_tim_image(old, sha256(old).hexdigest(), 8, 2, 7)
            p.set_texture_replacement(ids[0], resized, image_allocation=True)
            other = context.original_tim(ids[1])
            p.set_texture_replacement(ids[1], other[:-1] + bytes([other[-1] ^ 1]))
            p = ProjectService.open(p.save())
            replacements = {i: p.read_texture_replacement(b) for i, b in p.texture_overrides.items()}
            overlays, audit, requests = prepare(p, p.texture_overrides, replacements, context, archive)
            self.assertFalse(overlays)
            self.assertEqual((len(audit), len(requests)), (4, 1))
            result, proof = compose_model_pack_archive(blob, sha256(blob).hexdigest(), requests)
            self.assertTrue(proof['final_texture_additions_verified'])
            pack = context._carrier(_archive(result), context._item(ids[0])[1])['decoded']
            ranges = _pack_members(pack, not compressed)
            self.assertEqual(len(ranges), 4)
            for slot, content in enumerate([replacements[ids[0]], replacements[ids[1]]] + contents):
                start, _ = ranges[slot]
                self.assertEqual(pack[start:start + len(content)], content)
            binding = next(iter(p.texture_additions.values()))
            binding['source_pack_sha256'] = 'f' * 64
            with self.assertRaises(ProjectError):
                prepare(p, p.texture_overrides, replacements, context, archive)


if __name__ == '__main__':
    unittest.main()
