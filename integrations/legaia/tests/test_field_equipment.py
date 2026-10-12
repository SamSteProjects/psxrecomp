import os,struct,tempfile,unittest,base64,json
from copy import deepcopy
from pathlib import Path
from importer.pipeline import import_scene
from importer.assets import load_model_source,decode_tmd
from importer.field_equipment import project_field_equipment,load_field_equipment_preview
from importer.animation import load_animation_preview
from importer.core import ImportError
from sdk.project import ProjectService
from sdk.project_assets import source_key
from sdk.field_equipment import preview as sdk_preview
from importer.textures import TextureCatalog,load_asset_texture_catalog
from test_model_primitive_workflow import http_server


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc is private')
class FieldEquipmentTests(unittest.TestCase):
    def test_selected_material_pixels_from_original_upload_words(self):
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.import_metadata(import_scene(p.disc_path,'town01'));pixels=matches=0;cases=[]
            for slot in range(3):
                asset=p.assets.records[f'asset://legaia/models/global-special/{0xf0+slot:04x}'];catalog=load_asset_texture_catalog(p.disc_path,asset,TextureCatalog('unused',asset['source_record']['disc']['sha256']))
                # Rasterize immutable original words independently of association.
                words={}
                for block,_ in catalog.boot_uploads:
                    for y in range(block.height):
                        for x in range(block.width_words):
                            if block.x+x<1024 and block.y+y<512:words[block.x+x,block.y+y]=struct.unpack_from('<H',block.data,(y*block.width_words+x)*2)[0]
                for tim,_ in catalog.textures:
                    for block,flat in ((tim.image,False),(tim.clut,True)):
                        w,h=(block.width_words*block.height,1) if flat else (block.width_words,block.height)
                        for y in range(h):
                            for x in range(w):words[block.x+x,block.y+y]=struct.unpack_from('<H',block.data,(y*w+x)*2)[0]
                for byte in (0,1):
                    for clip in (None,'idle','walk'):
                        context=dict(projectPath=str(p.root),sourceKey=source_key(p),assetId=asset['semantic_id'],equipmentByte=byte,clipId=clip,frameIndex=0 if clip else None);value=sdk_preview(p,expected_project_path=context['projectPath'],expected_source_key=context['sourceKey'],asset_id=context['assetId'],equipment_byte=byte,clip_id=clip,frame_index=context['frameIndex']);cases.append(dict(context=context,value=value))
                        for t in value['geometry']['textures']:
                            if t['status']!='address_match':continue
                            m=value['geometry']['materials'][t['material_index']];page,clut=m['tpage'],m['clut'];bpp=(4,8,16)[(page>>7)&3];px,py=(page&15)*64,((page>>4)&1)*256;cx,cy=(clut&63)*16,(clut>>6)&511;rgba=base64.b64decode(t['rgba_base64']);stp=base64.b64decode(t['stp_base64']);count=0
                            for v in range(t['uv_origin'][1],t['uv_origin'][1]+t['height']):
                                for u in range(t['uv_origin'][0],t['uv_origin'][0]+t['width']):
                                    word=words[px+u*bpp//16,py+v]
                                    if bpp<16:word=words[cx+((word>>((u%(16//bpp))*bpp))&((1<<bpp)-1)),cy]
                                    channels=[(word>>shift)&31 for shift in (0,5,10)];expected=bytes([*(n*8+n//4 for n in channels),0 if word==0 else 255]);self.assertEqual(rgba[count*4:count*4+4],expected);self.assertEqual(stp[count],word>>15);count+=1
                            pixels+=count;matches+=1
            self.assertGreater(matches,0)
            output=os.getenv('LEGAIA_FIELD_TEXTURE_CASES')
            if output:Path(output).write_text(json.dumps(cases),encoding='utf-8');Path(output).with_name('texture-proof.json').write_text(json.dumps(dict(matches=matches,pixels=pixels,original_word_readback=True,gameplay_verified=False),indent=2),encoding='utf-8')
    def test_all_party_template_copies_and_native_poses(self):
        disc=os.environ['LEGAIA_DISC_BIN'];document=import_scene(disc,'town01')
        for slot,target in enumerate((0,3,5)):
            asset=next(m for m in document['assets']['models'] if m['semantic_id']==f'asset://legaia/models/global-special/{0xf0+slot:04x}');raw=load_model_source(disc,asset)
            for value in (0,1,255):
                projected,proof=project_field_equipment(raw,slot,value);source=12+(11 if value==0 else 10)*28;destination=12+target*28;self.assertEqual(projected[destination:destination+28],raw[source:source+28]);self.assertEqual(projected[:destination],raw[:destination]);self.assertEqual(projected[destination+28:],raw[destination+28:]);self.assertEqual(struct.unpack_from('<I',projected,8)[0],12)
                g=load_field_equipment_preview(disc,asset,value);self.assertEqual(len(g['objects']),10);expected=decode_tmd(projected);self.assertEqual(g['vertices'],expected['vertices'][:len(g['vertices'])]);self.assertEqual(g['triangles'],expected['triangles'][:len(g['triangles'])]);self.assertEqual(g['equipment_variant'],proof)
                posed=load_animation_preview(disc,asset,'idle',equipment_byte=value);self.assertEqual(posed['geometry']['vertices'],g['vertices']);self.assertEqual(len(posed['frames'][0]['object_transforms']),10);self.assertEqual(len(posed['geometry']['objects']),10)
            self.assertEqual(project_field_equipment(raw,slot,1)[0],project_field_equipment(raw,slot,255)[0])
            for value in (True,-1,256,.5):
                with self.assertRaises(ImportError):project_field_equipment(raw,slot,value)

    def test_exact_http_fields_and_source_only_state(self):
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.import_metadata(import_scene(p.disc_path,'town01'));before=deepcopy((p._document(),p.undo_stack));args=dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id='asset://legaia/models/global-special/00f0',equipment_byte=0,clip_id='idle',frame_index=0)
            with http_server(p) as (_,post):
                status,body=post('/api/field-equipment-preview',args);self.assertEqual(status,200,body);self.assertEqual(body['layer'],'retail_selected_variant');self.assertTrue(body['geometry']['posed']);self.assertEqual(body['geometry']['equipment_variant']['runtime_equipment'],'not_observed')
                for change in (dict(equipment_byte=True),dict(equipment_byte=256),dict(frame_index=True),dict(frame_index=999),dict(asset_id='asset://legaia/models/global-special/00f3'),dict(expected_source_key='0'*64),dict(extra=True)):
                    self.assertEqual(post('/api/field-equipment-preview',dict(args,**change))[0],400)
            self.assertEqual((p._document(),p.undo_stack),before)
