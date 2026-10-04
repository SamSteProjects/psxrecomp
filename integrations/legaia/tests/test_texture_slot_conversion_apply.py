"""Converted TIM plus retained sources form one reviewed history operation."""
from copy import deepcopy
from hashlib import sha256
import base64
import unittest

from importer.texture_png import _encode_png
from importer.texture_image_conversion import convert_png
from importer.model_pack_archive import _archive
from importer.model_pack_composition import compose_model_pack_archive
from importer.prot_layout import locate_physical_span
from importer.core import parse_scene_assets,decompress_lzs
from importer.textures import _pack_members
from sdk import texture_slots,texture_slot_edit
from sdk.project import ProjectService,ProjectError
from sdk.scene_preview import source_key
from sdk.export_snapshot import capture_export_inputs
from sdk.texture_allocation_build import prepare
import test_texture_slots_workflow as fixtures
from test_model_primitive_workflow import http_server


class ConversionApply(unittest.TestCase):
    def test_combined_append_edit_history_snapshot_and_native_carriers(self):
        for compressed in (False,True):
            helper=fixtures.TextureSlotsWorkflow();self.addCleanup(helper.doCleanups)
            p,context,archive,blob,ids=helper.setup_project(compressed)
            png=_encode_png(8,2,bytes([255,0,0,255]*16))
            options=dict(bpp=16,image_x=640,image_y=32,clut_x=0,clut_y=0,stp_mode='opaque')
            plane=_encode_png(8,2,bytes([0,0,0,255]*16))
            source=dict(png=png,stp=plane,options=options);native,_=convert_png(png,options,plane)
            args=(p,ids[0],native,source_key(p),'Combined',True)
            before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
            report=texture_slots.review(*args,conversion_source=source)
            texture_slots.pixels(*args,report['review_key'],0,conversion_source=source)
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
            self.assertFalse((p.root/'Authored').exists())
            alternate=dict(source,stp=None)
            with self.assertRaises(ProjectError):texture_slots.apply(*args,report['review_key'],conversion_source=alternate)
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
            applied=texture_slots.apply(*args,report['review_key'],conversion_source=source);i=applied['asset_id']
            self.assertEqual(len(p.undo_stack),1);self.assertIn('image_source',p.texture_additions[i])
            old=deepcopy(p.texture_additions[i]);p.undo();self.assertFalse(p.texture_additions);p.redo()
            changed_options=dict(options,bpp=8,image_x=704,image_y=48,clut_y=500)
            changed_source=dict(source,options=changed_options);changed,_=convert_png(png,changed_options)
            args=(p,i,changed,sha256(native).hexdigest(),source_key(p),'Combined edit',True)
            report=texture_slot_edit.review(*args,conversion_source=changed_source)
            texture_slot_edit.apply(*args,report['review_key'],conversion_source=changed_source)
            self.assertEqual(len(p.undo_stack),2);self.assertEqual(p.texture_additions[i]['slot_index'],2)
            self.assertEqual(p.texture_additions[i]['image_source']['options'],changed_options)
            p.undo();self.assertEqual(p.texture_additions[i],old);p.redo()
            reopened=ProjectService.open(p.save());self.assertEqual(texture_slots.read(reopened,i,reopened.texture_additions[i]),changed)
            _,files=capture_export_inputs(reopened);self.assertEqual(files['Authored/TextureSources/'+sha256(png).hexdigest()+'.png'],png);self.assertEqual(files['Authored/TextureSources/'+sha256(plane).hexdigest()+'.png'],plane)
            _,_,requests=prepare(reopened,{}, {},context,archive)
            result,_=compose_model_pack_archive(blob,sha256(blob).hexdigest(),requests)
            ar=_archive(result);entry=ar.entry(1);span=locate_physical_span(ar,entry.start_lba*2048)
            raw=result[span['byte_offset']:span['byte_offset']+span['byte_length']]
            if compressed:
                descriptor=parse_scene_assets(raw,1).descriptors[0];pack=decompress_lzs(raw[descriptor.data_offset:],descriptor.size)[0]
            else:pack=raw
            start,_=_pack_members(pack,not compressed)[2];self.assertEqual(pack[start:start+len(changed)],changed)

    def test_http_recipe_mismatch_null_and_combined_apply(self):
        helper=fixtures.TextureSlotsWorkflow();self.addCleanup(helper.doCleanups)
        p,context,archive,blob,ids=helper.setup_project()
        png=_encode_png(4,1,bytes([255,0,0,255]*4));options=dict(bpp=16,image_x=640,image_y=32,clut_x=0,clut_y=0,stp_mode='opaque')
        native,_=convert_png(png,options)
        source=dict(png_base64=base64.b64encode(png).decode(),stp_png_base64=None,options=options)
        body=dict(anchor_asset_id=ids[0],source_key=source_key(p),content_base64=base64.b64encode(native).decode(),label='Combined HTTP',accept_potential_overlap=True,conversion_source=source)
        before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        with http_server(p) as (_,post):
            for bad in (None,{},dict(source,extra=1),dict(source,png_base64='?'),dict(source,options=dict(options,image_x=768))):
                status,_=post('/api/texture-slot-review',dict(body,conversion_source=bad));self.assertEqual(status,400)
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
            status,report=post('/api/texture-slot-review',body);self.assertEqual(status,200,report);self.assertIn('image_source',report)
            path=p.root/'Authored'/'TextureSources'/(sha256(png).hexdigest()+'.png');path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'changed')
            status,_=post('/api/texture-slot-apply',dict(body,review_key=report['review_key']));self.assertEqual(status,400)
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
            path.write_bytes(png)
            status,result=post('/api/texture-slot-apply',dict(body,review_key=report['review_key']));self.assertEqual(status,200,result)
            self.assertEqual(len(p.undo_stack),1);self.assertIn('image_source',result['texture_additions'][result['texture_slot_report']['asset_id']])


if __name__=='__main__':unittest.main()
