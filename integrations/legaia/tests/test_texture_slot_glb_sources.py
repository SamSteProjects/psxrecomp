"""Embedded PNG lineage survives authored TIM conversion and native pack construction."""
from copy import deepcopy
from hashlib import sha256
import base64
import unittest
from importer.texture_png import _encode_png
from importer.texture_image_conversion import convert_png
from importer.model_pack_archive import _archive
from importer.model_pack_composition import compose_model_pack_archive
from importer.prot_layout import locate_physical_span
from importer.core import parse_scene_assets,decompress_lzs,ImportError
from importer.textures import _pack_members
from sdk import texture_slots,texture_slot_edit,texture_slot_sources
from sdk.project import ProjectService,ProjectError
from sdk.scene_preview import source_key
from sdk.export_snapshot import capture_export_inputs
from sdk.texture_allocation_build import prepare
import test_texture_slots_workflow as fixtures
import test_texture_glb as glb_fixtures
from test_model_primitive_workflow import http_server


def source_for(png,options,content=None):
    content=content or glb_fixtures.glb_png(png)
    selection=dict(content_base64=base64.b64encode(content).decode(),image_index=0,
        glb_sha256=sha256(content).hexdigest(),png_sha256=sha256(png).hexdigest())
    return dict(png=png,stp=None,options=options,glb_source=selection),content


class SlotGlbSources(unittest.TestCase):
    def test_append_edit_history_reopen_snapshot_and_raw_compressed_build(self):
        for compressed in (False,True):
            helper=fixtures.TextureSlotsWorkflow();self.addCleanup(helper.doCleanups)
            p,context,archive,blob,ids=helper.setup_project(compressed)
            png=_encode_png(8,2,bytes([255,0,0,255]*16))
            options=dict(bpp=16,image_x=640,image_y=32,clut_x=0,clut_y=0,stp_mode='opaque')
            inputs,glb=source_for(png,options);native,_=convert_png(png,options)
            args=(p,ids[0],native,source_key(p),'GLB source',True)
            before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
            plain=texture_slots.review(*args,conversion_source={k:v for k,v in inputs.items() if k!='glb_source'})
            reviewed=texture_slots.review(*args,conversion_source=inputs)
            self.assertNotEqual(plain['review_key'],reviewed['review_key'])
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
            with self.assertRaises(ProjectError):texture_slots.apply(*args,plain['review_key'],conversion_source=inputs)
            i=texture_slots.apply(*args,reviewed['review_key'],conversion_source=inputs)['asset_id']
            self.assertEqual(len(p.undo_stack),1);old=deepcopy(p.texture_additions[i])
            p.undo();self.assertFalse(p.texture_additions);p.redo()
            changed_options=dict(options,bpp=4,clut_y=500);changed,_=convert_png(png,changed_options)
            changed_inputs=dict(inputs,options=changed_options)
            args=(p,i,changed,sha256(native).hexdigest(),source_key(p),'GLB edit',True)
            r=texture_slot_edit.review(*args,conversion_source=changed_inputs)
            texture_slot_edit.apply(*args,r['review_key'],conversion_source=changed_inputs)
            self.assertEqual(len(p.undo_stack),2);p.undo();self.assertEqual(p.texture_additions[i],old);p.redo()
            reopened=ProjectService.open(p.save());binding=reopened.texture_additions[i]
            self.assertEqual(texture_slots.read(reopened,i,binding),changed)
            self.assertEqual(texture_slot_sources.read_glb_source(reopened,binding,png),glb)
            _,files=capture_export_inputs(reopened)
            self.assertEqual(files['Authored/TextureSources/'+sha256(glb).hexdigest()+'.glb'],glb)
            self.assertEqual(files['Authored/TextureSources/'+sha256(png).hexdigest()+'.png'],png)
            _,_,requests=prepare(reopened,{}, {},context,archive)
            result,_=compose_model_pack_archive(blob,sha256(blob).hexdigest(),requests)
            ar=_archive(result);span=locate_physical_span(ar,ar.entry(1).start_lba*2048)
            raw=result[span['byte_offset']:span['byte_offset']+span['byte_length']]
            if compressed:
                d=parse_scene_assets(raw,1).descriptors[0];pack=decompress_lzs(raw[d.data_offset:],d.size)[0]
            else:pack=raw
            at,_=_pack_members(pack,not compressed)[2];self.assertEqual(pack[at:at+len(changed)],changed)
            path=p.root/'Authored'/'TextureSources'/(sha256(glb).hexdigest()+'.glb')
            path.write_bytes(glb[:-1]+bytes([glb[-1]^1]))
            for action in (p.save,lambda:ProjectService.open(p.root),lambda:capture_export_inputs(p)):
                with self.assertRaises((ProjectError,ImportError)):action()

    def test_http_conversion_selection_preflight_retention_and_exact_download(self):
        helper=fixtures.TextureSlotsWorkflow();self.addCleanup(helper.doCleanups)
        p,context,archive,blob,ids=helper.setup_project()
        png=_encode_png(4,1,bytes([255,0,0,255]*4));options=dict(bpp=16,image_x=640,image_y=32,clut_x=0,clut_y=0,stp_mode='opaque')
        inputs,glb=source_for(png,options);native,_=convert_png(png,options)
        conversion=dict(asset_id=ids[0],source_key=source_key(p),png_base64=base64.b64encode(png).decode(),stp_png_base64=None,options=options,glb_source=inputs['glb_source'])
        transport={k:v for k,v in conversion.items() if k not in ('asset_id','source_key')}
        body=dict(anchor_asset_id=ids[0],source_key=source_key(p),content_base64=base64.b64encode(native).decode(),label='GLB HTTP',accept_potential_overlap=True,conversion_source=transport)
        with http_server(p) as (_,post):
            for selection in (None,{},dict(inputs['glb_source'],image_index=True),dict(inputs['glb_source'],glb_sha256='f'*64),dict(inputs['glb_source'],png_sha256='f'*64)):
                status,_=post('/api/texture-image-convert',dict(conversion,glb_source=selection));self.assertEqual(status,400)
            status,r=post('/api/texture-image-convert',conversion);self.assertEqual(status,200,r)
            self.assertEqual(base64.b64decode(r['content_base64']),native)
            status,r=post('/api/texture-slot-review',body);self.assertEqual(status,200,r)
            path=p.root/'Authored'/'TextureSources'/(sha256(glb).hexdigest()+'.glb');path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'changed')
            before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
            status,_=post('/api/texture-slot-apply',dict(body,review_key=r['review_key']));self.assertEqual(status,400)
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
            self.assertFalse((path.parent/(sha256(png).hexdigest()+'.png')).exists())
            path.write_bytes(glb)
            status,result=post('/api/texture-slot-apply',dict(body,review_key=r['review_key']));self.assertEqual(status,200,result)
            i=result['texture_slot_report']['asset_id'];download=dict(asset_id=i,expected_sha256=sha256(native).hexdigest(),source_key=source_key(p))
            status,r=post('/api/texture-slot-source-download',download);self.assertEqual(status,200,r)
            self.assertEqual(base64.b64decode(r['glb_base64']),glb)
            retention=dict(download,**transport)
            status,r=post('/api/texture-slot-source-review',retention);self.assertEqual(status,200,r);self.assertFalse(r['can_apply'])
            # Same embedded PNG in another GLB gives a different metadata review.
            other=glb_fixtures.glb_png(png,lambda d:d['images'][0].update(name='Other source'))
            selected,_=source_for(png,options,other);retention['glb_source']=selected['glb_source']
            status,r=post('/api/texture-slot-source-review',retention);self.assertEqual(status,200,r);self.assertTrue(r['can_apply'])
            status,result=post('/api/texture-slot-source-apply',dict(retention,review_key=r['review_key']));self.assertEqual(status,200,result)
            self.assertEqual(len(p.undo_stack),2);self.assertEqual(p.texture_additions[i]['asset_sha256'],sha256(native).hexdigest())
            p.undo();self.assertEqual(texture_slot_sources.read_glb_source(p,p.texture_additions[i]),glb);p.redo()


if __name__=='__main__':unittest.main()
