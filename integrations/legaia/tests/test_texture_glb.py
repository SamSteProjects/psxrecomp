"""Embedded GLB PNG source ownership feeds the existing native texture workflow."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import base64,json,shutil,struct,subprocess,unittest
from importer.core import ImportError
from importer.texture_glb import inspect_glb_pngs,extract_glb_png
from sdk import texture_png
from sdk.project import ProjectService
import test_texture_png_workflow as fixtures
from test_model_primitive_workflow import http_server


def glb_png(png,change=None):
    doc=dict(asset=dict(version='2.0'),buffers=[dict(byteLength=len(png))],
             bufferViews=[dict(buffer=0,byteOffset=0,byteLength=len(png))],
             images=[dict(name='Source image',mimeType='image/png',bufferView=0),dict(uri='unfetched.jpg',mimeType='image/jpeg')])
    if change:change(doc)
    encoded=json.dumps(doc,separators=(',',':')).encode();encoded+=b' '*(-len(encoded)%4)
    binary=png+b'\0'*(-len(png)%4)
    return struct.pack('<3I',0x46546c67,2,28+len(encoded)+len(binary))+struct.pack('<2I',len(encoded),0x4e4f534a)+encoded+struct.pack('<2I',len(binary),0x004e4942)+binary


class TextureGlbTests(unittest.TestCase):
    def test_embedded_range_png_crc_and_exact_selection_guards(self):
        png=fixtures.png_rgba(2,1,bytes((255,0,0,255,0,255,0,255)))
        content=glb_png(png);catalog=inspect_glb_pngs(content);row=catalog['images'][0]
        self.assertEqual(catalog['excluded_image_indices'],[1])
        self.assertEqual((row['width'],row['height']),(2,1))
        extracted=extract_glb_png(content,0,catalog['glb_sha256'],row['png_sha256'])
        self.assertEqual(base64.b64decode(extracted['png_base64']),png)
        for index,glb_hash,png_hash in ((True,catalog['glb_sha256'],row['png_sha256']),
                                       (1,catalog['glb_sha256'],row['png_sha256']),
                                       (0,'0'*64,row['png_sha256']),(0,catalog['glb_sha256'],'0'*64)):
            with self.assertRaises(ImportError):extract_glb_png(content,index,glb_hash,png_hash)
        for mutate in (lambda d:d['images'][0].update(bufferView=True),
                       lambda d:d['bufferViews'][0].update(buffer=True),
                       lambda d:d['bufferViews'][0].update(byteLength=len(png)+1),
                       lambda d:d['bufferViews'][0].update(byteStride=4),
                       lambda d:d['images'][0].update(name='bad\nname')):
            with self.assertRaises(ImportError):inspect_glb_pngs(glb_png(png,mutate))
        damaged=bytearray(png);damaged[-1]^=1
        with self.assertRaises(ImportError):inspect_glb_pngs(glb_png(bytes(damaged)))

    def test_http_extraction_read_only_then_native_review_apply_history_and_browser_dto(self):
        helper=fixtures.TexturePngWorkflow();helper.setUp();self.addCleanup(helper.doCleanups)
        p=helper.project;png,stp,binding,_=helper.export();edited=helper.edited(png)
        content=glb_png(edited);before=helper.snapshot()
        files={str(file):sha256(file.read_bytes()).hexdigest() for file in p.root.rglob('*') if file.is_file()}
        with http_server(p) as (_,post):
            body=dict(content_base64=base64.b64encode(content).decode())
            status,catalog=post('/api/texture-glb-images',body);self.assertEqual(status,200,catalog)
            row=catalog['images'][0]
            asked=dict(body,image_index=0,glb_sha256=catalog['glb_sha256'],png_sha256=row['png_sha256'])
            status,extracted=post('/api/texture-glb-image',asked);self.assertEqual(status,200,extracted)
            status,_=post('/api/texture-glb-image',dict(asked,image_index=True));self.assertEqual(status,400)
            self.assertEqual(helper.snapshot(),before)
            self.assertEqual(files,{str(file):sha256(file.read_bytes()).hexdigest() for file in p.root.rglob('*') if file.is_file()})
            request=dict(asset_id=fixtures.ASSET,png_base64=extracted['png_base64'],stp_png_base64=base64.b64encode(stp).decode(),binding=binding,palette_mode='existing')
            status,review=post('/api/texture-png-preview',request);self.assertEqual(status,200,review)
            self.assertEqual(review['pending_changes']['pixel_indices_changed'],1)
            self.assertEqual(helper.snapshot(),before)
            status,result=post('/api/texture-png-import',dict(request,review_key=review['review_key']));self.assertEqual(status,200,result)
        p.undo();self.assertEqual(helper.snapshot()[0],before[0]);p.redo();p.save()
        reopened=ProjectService.open(p.root);self.assertEqual(reopened.texture_overrides,p.texture_overrides)
        script="""import {decodeTextureGlbImages,decodeTextureGlbImage} from './integrations/legaia/editor/texture-png.js';
import assert from 'node:assert/strict';let raw='';for await(const c of process.stdin)raw+=c;
const {catalog,extracted}=JSON.parse(raw);decodeTextureGlbImages(catalog,catalog.glb_sha256);await decodeTextureGlbImage(extracted,catalog,0);
for(const mutate of [c=>c.read_only=false,c=>c.images[0].image_index=true,c=>c.excluded_image_indices=[],c=>c.images[0].width=2097153]){const bad=structuredClone(catalog);mutate(bad);assert.throws(()=>decodeTextureGlbImages(bad,catalog.glb_sha256));}
const bad=structuredClone(extracted);bad.image.png_sha256='0'.repeat(64);await assert.rejects(()=>decodeTextureGlbImage(bad,catalog,0));"""
        result=subprocess.run([shutil.which('node'),'--input-type=module','-e',script],input=json.dumps(dict(catalog=catalog,extracted=extracted)),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3])
        self.assertEqual(result.returncode,0,result.stderr)
