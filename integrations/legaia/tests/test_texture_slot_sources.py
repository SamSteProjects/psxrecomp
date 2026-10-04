from copy import deepcopy
from hashlib import sha256
import base64
import unittest

from importer.texture_png import _encode_png
from importer.texture_image_conversion import convert_png
from sdk import texture_slots,texture_slot_sources,texture_slot_edit
from sdk.project import ProjectService,ProjectError
from sdk.scene_preview import source_key
from sdk.export_snapshot import capture_export_inputs
import test_texture_slots_workflow as fixtures
from test_model_primitive_workflow import http_server


class SlotSources(unittest.TestCase):
    def setup_project(self):
        helper=fixtures.TextureSlotsWorkflow();self.addCleanup(helper.doCleanups)
        p,*_=helper.setup_project()
        options=dict(bpp=16,image_x=640,image_y=32,clut_x=0,clut_y=0,stp_mode='opaque')
        png=_encode_png(4,1,bytes([255,0,0,255]*4))
        stp=_encode_png(4,1,bytes([0,0,0,255]*4))
        native,_=convert_png(png,options,stp)
        args=(p,'texture://fixture/1/raw/0',native,source_key(p),'Retained',True)
        r=texture_slots.review(*args);identifier=texture_slots.apply(*args,r['review_key'])['asset_id']
        return p,identifier,png,stp,options,native

    def test_exact_reproduction_history_snapshot_offline_open_and_receipt_withdrawal(self):
        p,i,png,stp,options,native=self.setup_project();before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        args=(p,i,sha256(native).hexdigest(),source_key(p),png,options,stp)
        r=texture_slot_sources.review(*args);self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
        texture_slot_sources.apply(*args,r['review_key']);self.assertEqual(len(p.undo_stack),2)
        binding=deepcopy(p.texture_additions[i]);self.assertEqual(texture_slots.read(p,i,binding),native)
        p.undo();self.assertNotIn('image_source',p.texture_additions[i]);p.redo()
        reopened=ProjectService.open(p.save());self.assertEqual(reopened.texture_additions[i],binding)
        _,files=capture_export_inputs(reopened)
        for content in (png,stp):self.assertEqual(files['Authored/TextureSources/'+sha256(content).hexdigest()+'.png'],content)
        args=(p,i,native,sha256(native).hexdigest(),source_key(p),'Renamed',True)
        r=texture_slot_edit.review(*args);texture_slot_edit.apply(*args,r['review_key'])
        self.assertIn('image_source',p.texture_additions[i])
        changed=native[:-1]+bytes([native[-1]^1]);args=(p,i,changed,sha256(native).hexdigest(),source_key(p),'Renamed',True)
        r=texture_slot_edit.review(*args);texture_slot_edit.apply(*args,r['review_key'])
        self.assertNotIn('image_source',p.texture_additions[i]);p.undo();self.assertIn('image_source',p.texture_additions[i])
        source_path=p.root/'Authored'/'TextureSources'/(sha256(png).hexdigest()+'.png');source_path.write_bytes(png[:-1]+bytes([png[-1]^1]))
        with self.assertRaises(ProjectError):p.save()
        with self.assertRaises(ProjectError):ProjectService.open(reopened.root)

    def test_http_exact_context_wrong_recipe_review_apply_download_and_noop(self):
        p,i,png,stp,options,native=self.setup_project()
        body=dict(asset_id=i,expected_sha256=sha256(native).hexdigest(),source_key=source_key(p),png_base64=base64.b64encode(png).decode(),stp_png_base64=base64.b64encode(stp).decode(),options=options)
        with http_server(p) as (_,post):
            for bad in (dict(body,extra=1),dict(body,expected_sha256='f'*64),dict(body,source_key='stale'),dict(body,options=dict(options,image_x=768))):
                status,_=post('/api/texture-slot-source-review',bad);self.assertEqual(status,400)
            before=deepcopy((p._document(),p.undo_stack,p.redo_stack));status,r=post('/api/texture-slot-source-review',body);self.assertEqual(status,200,r)
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
            status,result=post('/api/texture-slot-source-apply',dict(body,review_key=r['review_key']));self.assertEqual(status,200,result)
            self.assertFalse(result['texture_source_report']['native_bytes_changed'])
            download=dict(asset_id=i,expected_sha256=body['expected_sha256'],source_key=source_key(p))
            status,result=post('/api/texture-slot-source-download',download);self.assertEqual(status,200,result)
            self.assertEqual(base64.b64decode(result['png_base64']),png);self.assertEqual(base64.b64decode(result['stp_png_base64']),stp)
            body['source_key']=source_key(p);status,r=post('/api/texture-slot-source-review',body);self.assertEqual(status,200,r);self.assertFalse(r['can_apply'])
            status,_=post('/api/texture-slot-source-apply',dict(body,review_key=r['review_key']));self.assertEqual(status,400)


if __name__=='__main__':unittest.main()
