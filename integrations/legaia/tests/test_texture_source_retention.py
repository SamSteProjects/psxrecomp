"""One legacy receipt upgrade, exact input recovery, and stale review rejection."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import base64
import json
import shutil
import subprocess
import unittest

from sdk.project import ProjectService
from sdk.scene_preview import source_key
from test_model_primitive_workflow import http_server
from test_texture_glb import glb_png
from importer.texture_glb import inspect_glb_pngs
import test_texture_png_workflow as fixtures


class TextureSourceRetention(unittest.TestCase):
    def test_legacy_receipt_review_apply_and_history(self):
        helper=fixtures.TexturePngWorkflow();helper.setUp();self.addCleanup(helper.doCleanups)
        p=helper.project;png,_,_,_=helper.export();content=glb_png(png)
        catalog=inspect_glb_pngs(content);image=catalog['images'][0]
        receipt=dict(glb_sha256=catalog['glb_sha256'],png_sha256=image['png_sha256'],image_index=0,name=image['name'])
        p.set_texture_replacement(fixtures.ASSET,helper.source,glb_source=receipt);p.save()
        native=p.read_texture_replacement(p.texture_overrides[fixtures.ASSET]);before=helper.snapshot()
        files=lambda:{str(f.relative_to(p.root)):sha256(f.read_bytes()).hexdigest() for f in p.root.rglob('*') if f.is_file()}
        originals=files();old=deepcopy(p.texture_overrides)
        request=dict(asset_id=fixtures.ASSET,expected_sha256=sha256(native).hexdigest(),source_key=source_key(p),content_base64=base64.b64encode(content).decode())
        with http_server(p) as (_,post):
            status,review=post('/api/texture-glb-retain-review',request);self.assertEqual(status,200,review)
            self.assertFalse(review['native_bytes_changed']);self.assertEqual(helper.snapshot(),before);self.assertEqual(files(),originals)
            for changed in (dict(source_key='stale'),dict(expected_sha256='0'*64),dict(content_base64=base64.b64encode(content[:-1]+b'X').decode())):
                status,_=post('/api/texture-glb-retain-review',dict(request,**changed));self.assertEqual(status,400)
            status,_=post('/api/texture-glb-retain',dict(request,review_key='0'*64));self.assertEqual(status,400)
            self.assertEqual(helper.snapshot(),before);self.assertEqual(files(),originals)
            status,result=post('/api/texture-glb-retain',dict(request,review_key=review['review_key']));self.assertEqual(status,200,result)
            self.assertTrue(result['retention_report']['project_changed'])
            status,_=post('/api/texture-glb-retain',dict(request,review_key=review['review_key']));self.assertEqual(status,400)
        self.assertEqual(len(p.undo_stack),len(before[2])+1)
        self.assertEqual(p.read_texture_replacement(p.texture_overrides[fixtures.ASSET]),native)
        self.assertEqual(p.read_texture_glb_source(p.texture_overrides[fixtures.ASSET]),content)
        p.undo();self.assertEqual(p.texture_overrides,old);p.redo();p.save()
        reopened=ProjectService.open(p.root)
        self.assertEqual(reopened.read_texture_glb_source(reopened.texture_overrides[fixtures.ASSET]),content)
        self.assertEqual(reopened.read_texture_replacement(reopened.texture_overrides[fixtures.ASSET]),native)
        from sdk.export_snapshot import capture_export_inputs
        _,inputs=capture_export_inputs(p)
        self.assertEqual(inputs['Authored/TextureSources/'+receipt['glb_sha256']+'.glb'],content)
        script="""import assert from 'node:assert/strict';import {qualifyRetention} from './integrations/legaia/editor/texture-source-retention.js';let raw='';for await(const c of process.stdin)raw+=c;const {review,request,receipt,size}=JSON.parse(raw);qualifyRetention(review,request,receipt,size);for(const change of [{native_bytes_changed:true},{project_changed:true},{review_key:'bad'},{effective_sha256:'bad'},{source:{...review.source,image_index:1}}])assert.throws(()=>qualifyRetention({...review,...change},request,receipt,size));"""
        check=subprocess.run([shutil.which('node'),'--input-type=module','-e',script],input=json.dumps(dict(review=review,request=request,receipt=receipt,size=len(content))),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3])
        self.assertEqual(check.returncode,0,check.stderr)
