"""Stable slot TIM interchange, mode/CLUT growth, history and carrier delivery."""
from copy import deepcopy
from hashlib import sha256
import base64
import unittest
from importer.texture_slot_allocation import append_texture_pack
from importer.textures import _pack_members,parse_tim
from importer.model_pack_archive import _archive
from importer.prot_layout import locate_physical_span
from importer.core import parse_scene_assets,decompress_lzs
from importer.model_pack_composition import compose_model_pack_archive
from sdk import texture_slots,texture_slot_edit
from sdk.project import ProjectService,ProjectError
from sdk.scene_preview import source_key
from sdk.texture_allocation_build import prepare
from test_importer_textures import tim,block
import test_texture_slots_workflow as slots_workflow
from test_model_primitive_workflow import http_server


class TextureSlotEdit(unittest.TestCase):
    def setup_project(self,compressed=False):
        helper=slots_workflow.TextureSlotsWorkflow();self.addCleanup(helper.doCleanups)
        p,context,archive,blob,ids=helper.setup_project(compressed)
        added=tim(16,image=block(640,32,2,1,b'\x00\x80'*2))
        for label in ('Editable','Neighbor'):
            args=(p,ids[0],added,source_key(p),label,True)
            report=texture_slots.review(*args);texture_slots.apply(*args,report['review_key'])
        identifier=next(iter(p.texture_additions))
        return p,context,archive,blob,ids,identifier,added

    def test_mode_palette_growth_keeps_identity_neighbor_and_reopens_both_carriers(self):
        for compressed in (False,True):
            p,context,archive,blob,ids,identifier,original=self.setup_project(compressed)
            current=deepcopy(p.texture_additions[identifier]);neighbor={i:deepcopy(b) for i,b in p.texture_additions.items() if i!=identifier}
            candidate=tim(8,image=block(768,48,4,3,bytes(range(24))),palette=block(0,500,256,2,[0,0x801f]*256))
            args=(p,identifier,candidate,sha256(original).hexdigest(),source_key(p),'Edited with two palettes',True)
            snapshot=deepcopy((p._document(),p.undo_stack,p.redo_stack))
            report=texture_slot_edit.review(*args)
            self.assertTrue(report['content_changed']);self.assertTrue(report['layout_changed'])
            self.assertEqual(report['palette_count'],2);self.assertEqual(report['slot_index'],2)
            pixels=texture_slot_edit.pixels(*args,report['review_key'],1)
            self.assertIsNotNone(pixels['current_png_base64']);self.assertEqual(pixels['current_palette_index'],0)
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),snapshot)
            texture_slot_edit.apply(*args,report['review_key'])
            binding=deepcopy(p.texture_additions[identifier]);self.assertEqual(binding['slot_index'],current['slot_index'])
            self.assertEqual({i:b for i,b in p.texture_additions.items() if i!=identifier},neighbor)
            self.assertEqual(len(p.undo_stack),3)
            with self.assertRaises(ProjectError):texture_slot_edit.apply(*args,report['review_key'])
            p.undo();self.assertEqual(p.texture_additions[identifier],current);p.redo()
            reopened=ProjectService.open(p.save());self.assertEqual(texture_slots.read(reopened,identifier,binding),candidate)
            overlays,audit,requests=prepare(reopened,{}, {},context,archive)
            self.assertFalse(overlays);self.assertEqual(len(requests),1)
            result,_=compose_model_pack_archive(blob,sha256(blob).hexdigest(),requests)
            reopened_archive=_archive(result);entry=reopened_archive.entry(1)
            span=locate_physical_span(reopened_archive,entry.start_lba*2048)
            raw=result[span['byte_offset']:span['byte_offset']+span['byte_length']]
            if compressed:
                descriptor=parse_scene_assets(raw,1).descriptors[0]
                pack=decompress_lzs(raw[descriptor.data_offset:],descriptor.size)[0]
            else:pack=raw
            members=_pack_members(pack,not compressed)
            self.assertEqual(len(members),4)
            self.assertEqual(pack[members[2][0]:members[2][0]+len(candidate)],candidate)
            self.assertEqual(pack[members[3][0]:members[3][0]+len(original)],original)

    def test_http_source_review_pixels_apply_noop_and_exact_context(self):
        p,context,archive,blob,ids,identifier,original=self.setup_project()
        candidate=original[:-1]+bytes([original[-1]^1])
        body=dict(asset_id=identifier,expected_sha256=sha256(original).hexdigest(),source_key=source_key(p),label='Edited',accept_potential_overlap=True,content_base64=base64.b64encode(candidate).decode('ascii'))
        with http_server(p) as (_,post):
            status,source=post('/api/texture-slot-edit-source',dict(asset_id=identifier,source_key=body['source_key']));self.assertEqual(status,200,source)
            self.assertEqual(base64.b64decode(source['content_base64']),original)
            before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
            for bad in (dict(body,extra=1),dict(body,expected_sha256='f'*64),dict(body,source_key='stale'),dict(body,accept_potential_overlap=1)):
                status,_=post('/api/texture-slot-edit-review',bad);self.assertEqual(status,400)
            status,report=post('/api/texture-slot-edit-review',body);self.assertEqual(status,200,report)
            status,pixels=post('/api/texture-slot-edit-pixels',dict(body,review_key=report['review_key'],palette_index=0));self.assertEqual(status,200,pixels)
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
            status,result=post('/api/texture-slot-edit-apply',dict(body,review_key=report['review_key']));self.assertEqual(status,200,result)
            self.assertEqual(result['texture_slot_report']['asset_id'],identifier)
            self.assertEqual(result['texture_additions'][identifier]['asset_sha256'],sha256(candidate).hexdigest())
            args=(p,identifier,candidate,sha256(candidate).hexdigest(),source_key(p),'Edited',True)
            noop=texture_slot_edit.review(*args);self.assertFalse(noop['changed']);self.assertFalse(noop['can_apply'])
            before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
            with self.assertRaises(ProjectError):texture_slot_edit.apply(*args,noop['review_key'])
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)


if __name__=='__main__':unittest.main()
