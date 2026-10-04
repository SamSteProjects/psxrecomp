"""Construction checks for resized TIMs, pack rebasing and physical delivery."""
from copy import deepcopy
from hashlib import sha256
import struct
import unittest

from importer.core import ImportError,parse_scene_assets,decompress_lzs
from importer.texture_layout_allocation import resize_tim_image,validate_tim_allocation
from importer.texture_pack_allocation import allocate_texture_pack
from importer.texture_pack_growth import rebuild_texture_pack_entry,rebuild_raw_texture_pack_entry
from importer.textures import parse_tim,_pack_members
from importer.model_pack_archive import _archive
from importer.model_pack_composition import compose_model_pack_archive
from test_importer_textures import tim,block
from test_importer_texture_authoring import fixture as texture_fixture
from test_texture_pack_growth import fixture as growth_fixture
from test_model_pack_archive import archive_source


class TextureLayoutAllocation(unittest.TestCase):
    def test_encoded_overlap_fill_crop_and_typed_layout_guards(self):
        for bpp,width,larger,smaller,fill in ((4,12,16,8,4),(8,6,8,4,18),(16,3,4,2,0x8000),(24,2,4,2,0x443322)):
            source=tim(bpp,image=block(0,0,3,2,bytes(range(12))));original=parse_tim(source)
            candidate,audit=resize_tim_image(source,sha256(source).hexdigest(),larger,3,fill);decoded=parse_tim(candidate)
            self.assertEqual((decoded.width,decoded.image.height),(larger,3));self.assertEqual(decoded.bpp,bpp)
            stride=decoded.image.width_words*2
            pattern=bytes([fill|(fill<<4)]) if bpp==4 else fill.to_bytes(bpp//8,'little')
            for row in range(3):
                expected=(original.image.data[row*6:row*6+6]+pattern*((stride-6)//len(pattern))) if row<2 else pattern*(stride//len(pattern))
                self.assertEqual(decoded.image.data[row*stride:(row+1)*stride],expected)
            self.assertEqual(decoded.clut,original.clut);self.assertTrue(audit['layout_changed'])
            cropped,_=resize_tim_image(source,sha256(source).hexdigest(),smaller,1,fill)
            self.assertEqual(parse_tim(cropped).image.data,original.image.data[:parse_tim(cropped).image.width_words*2])
            noop,_=resize_tim_image(source,sha256(source).hexdigest(),width,2,fill);self.assertEqual(noop,source)
            for values in ((True,3,fill),(larger,True,fill),(larger,3,True),(larger,3,1<<bpp),(0,3,fill),(larger,513,fill)):
                with self.assertRaises(ImportError):resize_tim_image(source,sha256(source).hexdigest(),*values)
            with self.assertRaises(ImportError):resize_tim_image(source,'0'*64,larger,3,fill)
            moved=bytearray(candidate);offset=8+(12+len(decoded.clut.data) if decoded.clut else 0);struct.pack_into('<H',moved,offset+4,1)
            with self.assertRaises(ImportError):validate_tim_allocation(source,bytes(moved))

    def test_nearest_copies_encoded_pixels_in_all_modes(self):
        for bpp,width in ((4,12),(8,6),(16,3),(24,2)):
            source=tim(bpp,image=block(0,0,3,2,bytes([0,128,255,255,0,0,1,128,254,127,255,128])))
            old=parse_tim(source)
            for w,h in ((width*2,4),(width,2),(width,1)):
                candidate,_=resize_tim_image(source,sha256(source).hexdigest(),w,h,0,'nearest')
                decoded=parse_tim(candidate)
                def pixel(image,x,y):
                    start=y*image.image.width_words*2
                    if bpp==4:return (image.image.data[start+x//2]>>(4*(x%2)))&15
                    count=bpp//8;start+=x*count
                    return image.image.data[start:start+count]
                for y in range(h):
                    for x in range(w):
                        self.assertEqual(pixel(decoded,x,y),pixel(old,(2*x+1)*width//(2*w),(2*y+1)*2//(2*h)))
                self.assertEqual(decoded.clut,old.clut)
                if (w,h)==(width,2):self.assertEqual(candidate,source)
            for mode,fill in ((None,0),(True,0),('linear',0),('nearest',1),('nearest',False)):
                with self.assertRaises(ImportError):resize_tim_image(source,sha256(source).hexdigest(),width,2,fill,mode)

    def test_pack_offsets_rebase_with_exact_unedited_members_and_alignment_tails(self):
        for standalone in (False,True):
            _,archive,_,pack=texture_fixture(compressed=not standalone)
            ranges=_pack_members(pack,standalone);start,end=ranges[0];old=parse_tim(pack[start:end]);source=pack[start:start+old.byte_length]
            resized,_=resize_tim_image(source,sha256(source).hexdigest(),8,3,7)
            edits=[dict(slot_index=0,source_tim_sha256=sha256(source).hexdigest(),tim=resized)];snapshot=deepcopy(edits)
            candidate,audit=allocate_texture_pack(pack,sha256(pack).hexdigest(),edits,standalone=standalone)
            new=_pack_members(candidate,standalone);self.assertEqual(candidate[new[0][0]:new[0][0]+len(resized)],resized)
            self.assertEqual(candidate[new[1][0]:new[1][1]],pack[ranges[1][0]:ranges[1][1]])
            self.assertEqual(new[1][0]-ranges[1][0],audit['growth_bytes']);self.assertEqual(edits,snapshot)
            odd,_=resize_tim_image(source,sha256(source).hexdigest(),4,2,7)
            odd_pack,odd_audit=allocate_texture_pack(pack,sha256(pack).hexdigest(),[dict(edits[0],tim=odd)],standalone=standalone)
            self.assertEqual(odd_audit['members'][0]['alignment_padding_bytes'],2)
            self.assertEqual(_pack_members(odd_pack,standalone)[1][0]%4,0)
            for bad in (edits*2,[dict(edits[0],slot_index=True)],[dict(edits[0],source_tim_sha256='0'*64)],[dict(edits[0],tim=resized+b'X')]):
                with self.assertRaises(ImportError):allocate_texture_pack(pack,sha256(pack).hexdigest(),bad,standalone=standalone)

    def test_raw_and_compressed_physical_allocation_readback_for_both_headers(self):
        for header in (0,2048):
            source,_,native,pack,_,_=growth_fixture();archive=_archive(source);carrier=archive.read_entry(archive.entry(1));source,_=archive_source(carrier,header)
            resized,_=resize_tim_image(native,sha256(native).hexdigest(),128,32,0x8000)
            edits=[dict(slot_index=0,source_tim_sha256=sha256(native).hexdigest(),tim=resized)]
            proposed,_=allocate_texture_pack(pack,sha256(pack).hexdigest(),edits)
            with self.assertRaises(ImportError):rebuild_texture_pack_entry(source,sha256(source).hexdigest(),1,0,0,sha256(pack).hexdigest(),proposed,header_offset=header)
            result,audit=rebuild_texture_pack_entry(source,sha256(source).hexdigest(),1,0,0,sha256(pack).hexdigest(),proposed,header_offset=header,layout_edits=edits)
            request=dict(kind='texture-layout-pack',entry_index=1,table_offset=0,descriptor_index=0,expected_pack_sha256=sha256(pack).hexdigest(),pack=proposed,layout_edits=edits)
            composed,composition=compose_model_pack_archive(source,sha256(source).hexdigest(),[request],header_offset=header)
            self.assertEqual(composed,result);self.assertTrue(composition['final_texture_layouts_verified'])
            reopened=_archive(result);raw=reopened.read_entry(reopened.entry(1));table=parse_scene_assets(raw,1);row=table.descriptors[0]
            self.assertEqual(row.size,len(proposed));decoded,_=decompress_lzs(raw[row.data_offset:],row.size);self.assertEqual(decoded,proposed)
            self.assertEqual(result[-8*2048:],source[-8*2048:]);self.assertTrue(audit['reopened_pack_verified'])
            _,fake,_,_=texture_fixture();raw_source,_=archive_source(fake.raw,header);old_raw=_archive(raw_source).read_entry(_archive(raw_source).entry(1));ranges=_pack_members(old_raw,True);start,end=ranges[0];old_tim=parse_tim(old_raw[start:end]);original=old_raw[start:start+old_tim.byte_length]
            expanded,_=resize_tim_image(original,sha256(original).hexdigest(),256,128,3)
            raw_edits=[dict(slot_index=0,source_tim_sha256=sha256(original).hexdigest(),tim=expanded)]
            raw_result,raw_audit=rebuild_raw_texture_pack_entry(raw_source,sha256(raw_source).hexdigest(),1,sha256(old_raw).hexdigest(),raw_edits,header_offset=header)
            request=dict(kind='texture-layout-raw',entry_index=1,expected_pack_sha256=sha256(old_raw).hexdigest(),edits=raw_edits)
            composed,composition=compose_model_pack_archive(raw_source,sha256(raw_source).hexdigest(),[request],header_offset=header)
            self.assertEqual(composed,raw_result);self.assertTrue(composition['final_texture_layouts_verified'])
            reopened=_archive(raw_result);emitted=reopened.read_entry(reopened.entry(1));new=_pack_members(emitted,True)
            self.assertEqual(emitted[new[0][0]:new[0][0]+len(expanded)],expanded)
            self.assertEqual(raw_result[-8*2048:],raw_source[-8*2048:]);self.assertTrue(raw_audit['physical_neighbors_preserved'])
