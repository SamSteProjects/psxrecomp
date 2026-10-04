"""Reviewed allocation, footprint choice, persistence and carrier collection."""
from copy import deepcopy
from hashlib import sha256
from types import SimpleNamespace
from unittest.mock import patch
import unittest
import struct

from importer.core import ImportError as NativeImportError
from importer.textures import TextureCatalog, parse_tim, _pack_members
from importer.texture_layout_allocation import resize_tim_image
from importer.model_pack_archive import _archive
from importer.model_pack_composition import compose_model_pack_archive
from sdk.project import ProjectService, ProjectError
from sdk.scene_preview import source_key
from sdk import texture_resize
from sdk.texture_allocation_build import prepare
import test_texture_png_workflow as png_fixture
ASSET=png_fixture.ASSET
from test_importer_textures import tim, block
from test_importer_texture_authoring import fixture
from test_model_pack_archive import archive_source
from test_model_primitive_workflow import http_server


class TextureResizeWorkflow(unittest.TestCase):
    def setUp(self):
        self.helper=png_fixture.TexturePngWorkflow();self.helper.setUp();self.addCleanup(self.helper.doCleanups)
        self.project=self.helper.project;self.source=self.helper.source;self.context=self.helper.context
        catalog=TextureCatalog('fixture','0'*64)
        catalog.textures=[(parse_tim(self.source),dict(semantic_id=ASSET)),
                          (parse_tim(tim(image=block(0,1,1,1,[0]))),dict(semantic_id=ASSET+'-neighbor'))]
        self.context._catalog=catalog

    def args(self,accept=False):
        return (self.project,ASSET,sha256(self.source).hexdigest(),source_key(self.project),4,2,7,accept)

    def test_review_overlap_choice_apply_history_reopen_and_following_payload_edit(self):
        before=self.helper.snapshot();report=texture_resize.review(*self.args())
        self.assertFalse(report['can_apply']);self.assertEqual(report['footprint']['potential_overlap_count'],1)
        self.assertEqual(self.helper.snapshot(),before);self.assertFalse((self.project.root/'Authored').exists())
        with self.assertRaises(ProjectError):texture_resize.apply(*self.args(),report['review_key'])
        accepted=texture_resize.review(*self.args(True));self.assertTrue(accepted['can_apply'])
        with self.assertRaises(ProjectError):texture_resize.apply(*self.args(True),report['review_key'])
        texture_resize.apply(*self.args(True),accepted['review_key']);binding=deepcopy(self.project.texture_overrides[ASSET])
        self.assertEqual(binding['format'],'tim-image-layout-v1')
        with self.assertRaises(NativeImportError):texture_resize.apply(*self.args(True),accepted['review_key'])
        self.project.undo();self.assertFalse(self.project.texture_overrides)
        self.project.redo();reopened=ProjectService.open(self.project.save());self.assertEqual(reopened.texture_overrides[ASSET],binding)
        current=reopened.read_texture_replacement(binding);changed=current[:-1]+bytes([current[-1]^1])
        self.project.set_texture_replacement(ASSET,changed);self.assertEqual(self.project.texture_overrides[ASSET]['image_layout'],binding['image_layout'])
        larger,_=resize_tim_image(changed,sha256(changed).hexdigest(),8,2,0)
        with self.assertRaises(NativeImportError):self.project.set_texture_replacement(ASSET,larger)
        pixel=self.project.texture_pixel_source(ASSET,0,0,1);self.assertIsNone(pixel['retail_entry'])
        self.project.set_texture_index_rectangle(ASSET,0,1,4,1,2,sha256(changed).hexdigest())
        self.assertEqual(self.project.texture_overrides[ASSET]['image_layout'],binding['image_layout'])
        from sdk.texture_png import export_texture
        _,_,_,png_report=export_texture(self.project,ASSET)
        self.assertEqual(png_report['retail_comparison']['added_pixels'],4)
        self.project.texture_json_source(ASSET,'effective')
        bad=deepcopy(binding);bad['image_layout']['height']+=1
        with self.assertRaises(ProjectError):reopened.read_texture_replacement(bad)

    def test_exact_http_and_stale_context_guards(self):
        body=dict(asset_id=ASSET,expected_sha256=sha256(self.source).hexdigest(),source_key=source_key(self.project),
                  width=4,height=2,fill_value=7,accept_potential_overlap=True)
        with http_server(self.project) as (_,post):
            for bad in (dict(body,width=True),dict(body,source_key='stale'),dict(body,unexpected=1),dict(body,accept_potential_overlap=1)):
                status,_=post('/api/texture-resize-preview',bad);self.assertEqual(status,400)
            status,review=post('/api/texture-resize-preview',body);self.assertEqual(status,200,review)
            status,result=post('/api/texture-resize',dict(body,review_key=review['review_key']));self.assertEqual(status,200,result)
            self.assertTrue(result['resize_report']['project_changed'])

    def test_layout_and_fixed_edits_collect_one_complete_pack(self):
        for compressed in (False,True):
            context,fake,catalog,_=fixture(compressed=compressed)
            raw=bytearray(fake.raw)
            if compressed:
                for descriptor in range(2,6):struct.pack_into('<I',raw,12+8*descriptor,len(raw))
            blob,_=archive_source(bytes(raw));archive=_archive(blob)
            # Fixture entry 5 is relocated into the synthetic archive's entry 1.
            for _,source in catalog.textures:source['prot_entry_index']=1;source['semantic_id']=source['semantic_id'].replace('/5/','/1/')
            context._items={s['semantic_id']:(t,deepcopy(s)) for t,s in catalog.textures}
            carrier=context._carrier(archive,catalog.textures[0][1]);ids=list(context._items)
            originals={i:context._original(i,carrier) for i in ids}
            resized,_=resize_tim_image(originals[ids[0]],sha256(originals[ids[0]]).hexdigest(),8,2,7)
            changed=originals[ids[1]][:-1]+bytes([originals[ids[1]][-1]^1])
            replacements={ids[0]:resized,ids[1]:changed}
            bindings={ids[0]:dict(format='tim-image-layout-v1'),ids[1]:dict(format='tim')}
            project=SimpleNamespace(validate_effective_texture=lambda *args,**kwargs:None)
            with patch.object(context,'build_patch',return_value=([],[],[])):
                overlays,audit,requests=prepare(project,bindings,replacements,context,archive)
            self.assertFalse(overlays);self.assertEqual((len(audit),len(requests)),(2,1))
            result,proof=compose_model_pack_archive(blob,sha256(blob).hexdigest(),requests)
            self.assertTrue(proof['final_texture_layouts_verified'])
            rebuilt=_archive(result);newcarrier=context._carrier(rebuilt,catalog.textures[0][1]);ranges=_pack_members(newcarrier['decoded'],not compressed)
            for slot,i in enumerate(ids):
                start,_=ranges[slot];self.assertEqual(newcarrier['decoded'][start:start+len(replacements[i])],replacements[i])
