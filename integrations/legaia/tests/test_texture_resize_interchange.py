"""Current allocation interchange, distinct Retail baseline and freshness."""
import base64
from copy import deepcopy
from hashlib import sha256
import json
import unittest

from importer.core import ImportError as NativeImportError
from importer.texture_comparison import compare_payloads
from importer.texture_layout_allocation import resize_tim_image
from importer.texture_authoring import patch_tim_pixel_index
from sdk.project import ProjectError
from sdk import texture_png, texture_resize
import test_texture_resize_workflow as resize_fixture
from test_importer_textures import tim, block


class TextureResizeInterchange(unittest.TestCase):
    def setUp(self):
        self.fixture=resize_fixture.TextureResizeWorkflow();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.p=self.fixture.project;self.asset=resize_fixture.ASSET
        args=self.fixture.args(True);report=texture_resize.review(*args);texture_resize.apply(*args,report['review_key'])

    def test_png_current_roundtrip_pixels_review_apply_and_stale_binding(self):
        png,stp,binding,export=texture_png.export_texture(self.p,self.asset)
        self.assertEqual(export['pending_changes']['total_change_count'],0)
        self.assertEqual(export['retail_comparison']['added_pixels'],4)
        self.assertEqual(export['retail_comparison']['removed_pixels'],0)
        before=self.fixture.helper.snapshot();edited=self.fixture.helper.edited(png)
        report=texture_png.preview_import(self.p,self.asset,edited,binding,'existing',stp)
        pixels=texture_png.pixels_import(self.p,self.asset,edited,binding,'existing',stp)
        self.assertEqual(pixels['report'],report);self.assertEqual(report['pending_changes']['pixel_indices_changed'],1)
        self.assertEqual(self.fixture.helper.snapshot(),before)
        texture_png.apply_import(self.p,self.asset,edited,binding,'existing',stp,report['review_key'])
        self.assertEqual(self.p.texture_overrides[self.asset]['format'],'tim-image-layout-v1')
        with self.assertRaisesRegex(ProjectError,'differs|stale'):texture_png.preview_import(self.p,self.asset,edited,binding,'existing',stp)

    def test_json_v2_roundtrip_combined_edits_file_preview_and_stale_hashes(self):
        response=self.p.texture_json_source(self.asset,'effective');content=base64.b64decode(response['json_base64']);document=json.loads(content)
        self.assertEqual(document['schema_version'],'legaia.indexed-texture.v2')
        self.assertEqual(document['retail_source_sha256'],sha256(self.fixture.source).hexdigest())
        before=self.fixture.helper.snapshot();preview=self.p.preview_texture_file(self.asset,content,'json')
        self.assertEqual(preview['current_changes']['total_change_count'],0);self.assertEqual(preview['retail_comparison']['added_pixels'],4)
        self.assertEqual(self.fixture.helper.snapshot(),before)
        document['palette_words'][1]^=1;document['pixel_indices'][1][0]=2
        edited=json.dumps(document).encode();preview=self.p.preview_texture_file(self.asset,edited,'json')
        self.assertEqual(preview['current_changes']['palette_words_changed'],1);self.assertEqual(preview['current_changes']['pixel_indices_changed'],1)
        for field in ('retail_source_sha256','source_sha256'):
            bad=deepcopy(document);bad[field]='0'*64
            with self.assertRaises(NativeImportError):self.p.preview_texture_file(self.asset,json.dumps(bad).encode(),'json')
        self.p.set_texture_json(self.asset,edited);binding=self.p.texture_overrides[self.asset];current=self.p.read_texture_replacement(binding)
        with self.assertRaises(NativeImportError):self.p.set_texture_json(self.asset,edited)
        native=patch_tim_pixel_index(current,sha256(current).hexdigest(),1,1,2)
        tim_review=self.p.preview_texture_file(self.asset,native,'tim')
        self.assertEqual(tim_review['current_changes']['pixel_indices_changed'],1)
        self.p.undo();self.p.redo();self.assertEqual(self.p.read_texture_replacement(binding),current)

    def test_all_modes_added_removed_counts_and_zero_baseline_are_distinct(self):
        for bpp,width,grow in ((4,12,16),(8,6,8),(16,3,4),(24,2,4)):
            source=tim(bpp,image=block(0,0,3,2,bytes(range(12))))
            candidate,_=resize_tim_image(source,sha256(source).hexdigest(),grow,1,0)
            changes,comparison=compare_payloads(source,candidate)
            self.assertEqual(changes['total_change_count'],0)
            self.assertEqual(comparison['baseline_sha256'],sha256(candidate).hexdigest())
            self.assertNotEqual(comparison['source_sha256'],comparison['baseline_sha256'])
            self.assertEqual(comparison['added_pixels'],grow-width);self.assertEqual(comparison['removed_pixels'],width)
