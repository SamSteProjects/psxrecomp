from copy import deepcopy
from unittest import TestCase
from importer.core import ImportError
from importer.texture_material_binding import texture_material_pages
from importer.textures import TextureCatalog,parse_tim,associate_material
from test_importer_textures import tim,block
import test_texture_png_workflow as png_fixture
ASSET=png_fixture.ASSET
from test_model_primitive_workflow import http_server
from sdk.scene_preview import source_key

class TextureMaterialBinding(TestCase):
    def test_page_regions_cover_each_depth_and_static_native_addresses(self):
        for bpp in (4,8,16):
            width=256*bpp//16+3;data=tim(bpp,image=block(64,255,width,2,bytes(width*4)))
            result=texture_material_pages(data,0);pages=result['pages'];self.assertEqual(len(pages),4)
            self.assertEqual(sum(p['image_rectangle']['width_words']*p['image_rectangle']['height'] for p in pages),width*2)
            catalog=TextureCatalog('fixture','0'*64,[(parse_tim(data),dict(semantic_id='texture://fixture/0'))])
            for row in pages:
                v=row['values'];clut=v.get('clut_column',0)*16 | v.get('clut_row',0)<<6
                tpage=v['page_column']|v['page_row']<<4|(4,8,16).index(bpp)<<7
                association=associate_material(catalog,dict(textured=True,clut=clut,tpage=tpage),tuple(row['uv_rectangle']))
                self.assertEqual(association['status'],'address_match')
            if bpp==16:self.assertNotIn('clut_column',pages[0]['values'])
    def test_flattened_palette_alignment_and_unsupported_inputs(self):
        content=tim(4,palette=block(16,480,16,2,[0]*32))
        result=texture_material_pages(content,1);self.assertEqual(result['palette_origin'],dict(x=32,y=480));self.assertEqual(result['palette_count'],2)
        for data,palette in ((content,True),(content,2),(tim(16),1),(tim(24,image=block(0,0,3,1,bytes(6))),0),(tim(4,palette=block(1,100,16,1,[0]*16)),0),(content+b'X',0)):
            with self.assertRaises(ImportError):texture_material_pages(data,palette)
    def test_current_source_http_readonly_and_stale_withdrawal(self):
        helper=png_fixture.TexturePngWorkflow();helper.setUp();self.addCleanup(helper.doCleanups);p=helper.project;before=helper.snapshot()
        body=dict(asset_id=ASSET,source_key=source_key(p),palette_index=0)
        with http_server(p) as (_,post):
            status,result=post('/api/material-texture-source',body);self.assertEqual(status,200,result)
            self.assertFalse(result['project_changed']);self.assertEqual(result['pages'][0]['uv_rectangle'],[0,0,3,0]);self.assertEqual(helper.snapshot(),before)
            for bad in (dict(body,palette_index=True),dict(body,source_key='stale'),dict(body,unexpected=1)):
                status,_=post('/api/material-texture-source',bad);self.assertEqual(status,400)
            p.set_texture_replacement(ASSET,helper.source[:-1]+bytes([helper.source[-1]^1]))
            status,_=post('/api/material-texture-source',body);self.assertEqual(status,400)
            fresh=dict(body,source_key=source_key(p));status,changed=post('/api/material-texture-source',fresh);self.assertEqual(status,200,changed);self.assertNotEqual(changed['effective_sha256'],changed['source_sha256'])
