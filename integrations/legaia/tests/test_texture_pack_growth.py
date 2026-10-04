"""Bounded texture growth, shared resource composition and normal package delivery."""
from contextlib import nullcontext
from hashlib import sha256
from pathlib import Path
from copy import deepcopy
import json
import random
import struct
import tempfile
import tomllib
import unittest
from unittest.mock import patch
import zipfile

from importer.core import ImportError,Mode2Image,ProtArchive,parse_scene_assets,decompress_lzs
from importer.texture_pack_growth import qualify_texture_pack
from importer.texture_authoring import TextureAuthoringContext
from importer.textures import TextureCatalog,parse_tim
from importer.model_pack_archive import _archive
from importer.model_pack_composition import compose_model_pack_archive
from importer.serialization import compress_lzs
from importer.relocated_disc import RelocatedLogicalDisc
from importer.disc_relocation_package import decode_relocation_package
from sdk.project import ProjectService
from sdk.build import build_project,_build_project
from tools.cd_sector import SYNC,encode_form1,relocate_mode2
from test_importer_textures import tim,block
from test_model_pack_archive import archive_source
from test_model_pack_growth import pack_source,ledger_for
from test_relocated_disc import LogicalSource
from test_project_workflow import synthetic_scene


def fixture():
    native=tim(16,image=block(0,0,64,16,bytes(2048)))
    pack=struct.pack('<II',1,2)+native+b'opaque texture tail'
    candidate=pack[:28]+random.Random(15).randbytes(2048)+pack[28+2048:]
    model,models=pack_source();stream=compress_lzs(pack);model_stream=compress_lzs(model)
    raw=bytearray(40);struct.pack_into('<I',raw,0,4)
    for i,(kind,size,payload) in enumerate(((1,len(pack),stream+b'OPAQUE!!'),(2,len(model),model_stream),(1,1,b'\xffZ'),(0,0,b'TAIL'))):
        struct.pack_into('<II',raw,8+i*8,(kind<<24)|size,len(raw));raw.extend(payload)
    source,_=archive_source(bytes(raw))
    request=dict(kind='texture-pack',entry_index=1,table_offset=0,descriptor_index=0,expected_pack_sha256=sha256(pack).hexdigest(),pack=candidate)
    return source,request,native,pack,model,models


class TexturePackGrowth(unittest.TestCase):
    def test_composition_preserves_opaque_tail_model_growth_and_both_headers(self):
        source,request,native,pack,model,models=fixture()
        _,ledger=ledger_for(models[2],32,varied=True)
        model_request=dict(entry_index=1,descriptor_index=1,expected_pack_sha256=sha256(model).hexdigest(),replacements=[dict(slot_index=2,ledger=ledger)])
        for header in (0,2048):
            raw=_archive(source).read_entry(_archive(source).entry(1));original,_=archive_source(raw,header)
            result,audit=compose_model_pack_archive(original,sha256(original).hexdigest(),[model_request,request],header_offset=header)
            archive=_archive(result);carrier=archive.read_entry(archive.entry(1));table=parse_scene_assets(carrier,1)
            decoded,used=decompress_lzs(carrier[table.descriptors[0].data_offset:],len(pack))
            self.assertEqual(decoded,request['pack']);self.assertTrue(audit['final_texture_packs_verified'])
            old_table=parse_scene_assets(raw,1);_,old_used=decompress_lzs(raw[40:],len(pack))
            old_gap=raw[40+old_used:old_table.descriptors[1].data_offset]
            padding=audit['resources'][0]['carrier']['growth_bytes']+old_used-used
            self.assertEqual(carrier[40+used+padding:table.descriptors[1].data_offset],old_gap)
            self.assertEqual(result[-8*2048:],original[-8*2048:])
        snapshot=deepcopy(request)
        for bad in (request['pack']+b'X',request['pack'][:-1]+b'X',b'X'+request['pack'][1:]):
            with self.assertRaises(ImportError):qualify_texture_pack(pack,bad)
        for bad in (dict(request,expected_pack_sha256='0'*64),dict(request,descriptor_index=True),dict(request,descriptor_index=1)):
            with self.assertRaises(ImportError):compose_model_pack_archive(source,sha256(source).hexdigest(),[bad])
        self.assertEqual(request,snapshot)

    def test_normal_build_delivers_exact_texture_after_growth_with_read_only_review(self):
        source,request,native,pack,_,_=fixture()
        directory=self.enterContext(tempfile.TemporaryDirectory())
        root=Path(directory);base=LogicalSource();view=RelocatedLogicalDisc(base,source,sha256(base.read_file(base.find('PROT.DAT'))).hexdigest())
        sectors=[]
        for lba in range(view.size//2352):
            frame=bytearray(2352);frame[:12]=SYNC;frame[15]=2;frame[17]=1;frame[18]=8;frame[20:24]=frame[16:20];frame[24:2072]=view.user_sector(lba)
            sectors.append(encode_form1(relocate_mode2(bytes(frame),lba)))
        disc=root/'source.bin';disc.write_bytes(b''.join(sectors));image=Mode2Image(disc);self.addCleanup(image.close)
        disc_hash=sha256(disc.read_bytes()).hexdigest();archive=ProtArchive(image,image.find('PROT.DAT'))
        identifier='texture://fixture/1/0/0';catalog=TextureCatalog('fixture',disc_hash)
        catalog.textures.append((parse_tim(native),dict(semantic_id=identifier,prot_entry_index=1,descriptor_index=0,compressed_stream_offset=40,pack_slot=0,byte_offset=8,byte_length=len(native),byte_coordinate_space='decoded_lzs_descriptor')))
        context=TextureAuthoringContext(str(disc),'fixture',catalog)
        p=ProjectService(root/'project');doc=synthetic_scene();doc['source']['disc_identity']='sha256:'+disc_hash;p.import_metadata(doc,str(disc));p.save()
        scope=lambda _:nullcontext((image,disc_hash,None,archive))
        with patch('importer.texture_authoring._disc_context',side_effect=scope),patch.object(ProjectService,'_texture_context',return_value=context),patch('sdk.build._disc_context',side_effect=scope),patch('sdk.build.import_scene',return_value=doc),patch('importer.texture_authoring.load_texture_authoring_context',return_value=context):
            edited=request['pack'][8:8+len(native)];p.set_texture_replacement(identifier,edited);p.save();before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
            with self.assertRaisesRegex(ImportError,'relocation is unsupported'):context.patch({identifier:edited})
            review=_build_project(p,None,review_only=True);self.assertFalse(review['output_written']);self.assertFalse((p.root/'Builds').exists())
            result=build_project(p)
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
        with zipfile.ZipFile(result['path']) as package:
            manifest=tomllib.loads(package.read('manifest.toml').decode());self.assertEqual(manifest['format_version'],7)
            self.assertEqual(result['report']['resource_relocation']['texture_pack_count'],1)
            self.assertGreater(result['report']['resource_relocation']['archive_growth_bytes'],0)
            row=manifest['disc_relocation'][0];decoded=decode_relocation_package(package.read(row['file']),row['sha256'])
        reopened=_archive(decoded['replacement']);raw=reopened.read_entry(reopened.entry(1));descriptor=parse_scene_assets(raw,1).descriptors[0]
        actual,_=decompress_lzs(raw[descriptor.data_offset:],descriptor.size);self.assertEqual(actual,request['pack'])
        audit=json.loads(Path(result['audit']).read_text(encoding='utf-8'));self.assertTrue(audit['relocation']['composition']['final_texture_packs_verified'])
        self.assertTrue(next(row for row in audit['edits'] if row.get('semantic_id')==identifier)['carrier_relocation_required'])
