from pathlib import Path
from copy import deepcopy
from hashlib import sha256
import os,struct,unittest
from importer.battle_character_catalog import decode_catalog,discover,preview,FIRST_ATLAS,ATLAS_STRIDE,CLUT_ROWS
from importer.core import ImportError,validate_metadata_only
from test_importer_assets import model

def fixture():
    data=bytearray(FIRST_ATLAS+7*ATLAS_STRIDE);cursor=0;body=model()
    for i in range(5):struct.pack_into('<I',data,cursor,(9<<24)|len(body));data[cursor+4:cursor+4+len(body)]=body;cursor+=4+len(body)
    for i,row in enumerate(CLUT_ROWS):
        at=FIRST_ATLAS+i*ATLAS_STRIDE
        struct.pack_into('<III4H',data,at,16,8,524,0,row,256,1)
        struct.pack_into('<I4H',data,at+532,32780,0,0,64,256)
    return bytes(data)

class BattleCharacterCatalogTests(unittest.TestCase):
    def test_source_metadata_and_partial_final_atlas(self):
        raw=fixture();catalog=decode_catalog(raw,'0'*64);validate_metadata_only(catalog)
        self.assertEqual((len(catalog['models']),len(catalog['textures'])),(5,7));self.assertTrue(all(t['preview_supported'] for t in catalog['textures']))
        for asset in catalog['models']+catalog['textures']:
            s=asset['source_record'];self.assertEqual(s['sha256'],sha256(raw[s['byte_offset']:s['byte_offset']+s['byte_length']]).hexdigest());self.assertEqual(s['containing_sha256'],sha256(raw).hexdigest())
        partial=decode_catalog(raw[:-10000],'0'*64);self.assertFalse(partial['textures'][-1]['preview_supported']);self.assertEqual(partial['textures'][-1]['status'],'partial');self.assertEqual(sum(t['preview_supported'] for t in partial['textures']),6)
        self.assertNotEqual(partial['source_key'],catalog['source_key']);self.assertFalse(catalog['gameplay_verified']);self.assertFalse(catalog['project_changed'])
    def test_bad_layouts_refuse(self):
        raw=fixture()
        for offset,value in [(3,2),(0,255),(FIRST_ATLAS,0),(FIRST_ATLAS+14,0),(FIRST_ATLAS+532+11,0)]:
            bad=bytearray(raw);bad[offset]=value
            with self.subTest(offset=offset),self.assertRaises(ImportError):decode_catalog(bytes(bad),'0'*64)
        for value in [b'',raw[:12]]:
            with self.assertRaises(ImportError):decode_catalog(value,'0'*64)
        with self.assertRaises(ImportError):decode_catalog(raw,'foreign')
    @unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc is private')
    def test_retail_pack_and_existing_decoders(self):
        disc=Path(os.environ['LEGAIA_DISC_BIN']);catalog=discover(disc);self.assertEqual([m['source_record']['object_count'] for m in catalog['models']],[15,16,15,20,15]);self.assertEqual([m['source_record']['byte_offset'] for m in catalog['models']],[4,0x82f4,0x1065c,0x1672c,0x1d0cc]);self.assertEqual(sum(t['preview_supported'] for t in catalog['textures']),6);held=deepcopy(catalog)
        for asset in catalog['models']+catalog['textures']:
            if asset['preview_supported']:
                actual,record,value=preview(disc,asset['semantic_id'],catalog['source_key']);self.assertEqual(actual,catalog);self.assertEqual(record,asset)
                if asset['asset_kind']=='tmd_model':self.assertEqual(len(value['objects']),asset['source_record']['object_count'])
                else:self.assertEqual((value['width'],value['height']),(256,256))
        for identifier,key in [(catalog['textures'][-1]['semantic_id'],catalog['source_key']),('asset://foreign',catalog['source_key']),(catalog['models'][0]['semantic_id'],'0'*64)]:
            with self.assertRaises(ImportError):preview(disc,identifier,key)
        self.assertEqual(catalog,held)

    @unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc is private')
    def test_static_texture_crops_against_native_words(self):
        from importer.pipeline import _disc_context
        disc=Path(os.environ['LEGAIA_DISC_BIN']);catalog=discover(disc)
        with _disc_context(disc) as (_,_,_,archive):raw=archive.read_entry(archive.entry(1204))
        matched=[];pixels=0
        for model_record in catalog['models']:
            _,_,model_preview=preview(disc,model_record['semantic_id'],catalog['source_key']);count=0
            for texture in model_preview['textures']:
                if texture['status']!='address_match':
                    self.assertNotIn('rgba',texture);self.assertNotIn('stp',texture);continue
                count+=1;material=model_preview['materials'][texture['material_index']];page=material['tpage'];clut=material['clut'];u0,v0=texture['uv_origin']
                # Independently address original TIM image and palette words.
                for n in range(texture['width']*texture['height']):
                    u=u0+n%texture['width'];v=v0+n//texture['width'];x=(page&15)*64+u//4;y=((page>>4)&1)*256+v
                    image=[t for t in catalog['textures'] if t['preview_supported'] and t['image']['x']<=x<t['image']['x']+64 and t['image']['y']<=y<t['image']['y']+256];self.assertEqual(len(image),1);im=image[0];start=im['source_record']['byte_offset']+544
                    word=struct.unpack_from('<H',raw,start+2*((y-im['image']['y'])*64+x-im['image']['x']))[0];index=(word>>((u%4)*4))&15
                    palette=[t for t in catalog['textures'] if t['preview_supported'] and t['clut']['y']==clut>>6];self.assertEqual(len(palette),1);pal=palette[0];colour=struct.unpack_from('<H',raw,pal['source_record']['byte_offset']+20+2*((clut&63)*16+index))[0]
                    expand=lambda v:(v<<3)|(v>>2)
                    expected=bytes([expand(colour&31),expand((colour>>5)&31),expand((colour>>10)&31),255 if colour else 0]);self.assertEqual(texture['rgba'][4*n:4*n+4],expected);self.assertEqual(texture['stp'][n],colour>>15);pixels+=1
            matched.append(count)
        self.assertEqual(matched,[8,10,9,0,0]);self.assertEqual(pixels,194857)

    @unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc is private')
    def test_project_http_resources_and_private_previews(self):
        import tempfile
        from sdk.project import ProjectService
        from sdk.project_assets import source_key
        from test_model_primitive_workflow import http_server
        with tempfile.TemporaryDirectory() as root:
            project=ProjectService(Path(root));project.disc_path=os.environ['LEGAIA_DISC_BIN'];held=deepcopy((project._document(),project.undo_stack));key=source_key(project);body=dict(expected_project_path=str(project.root),expected_source_key=key)
            with http_server(project) as (_,post):
                status,response=post('/api/battle-character-resources',body);self.assertEqual(status,200);catalog=response['catalog'];self.assertTrue(response['read_only'])
                for asset in [catalog['models'][0],catalog['textures'][0]]:
                    request=dict(body,asset_id=asset['semantic_id'],catalog_source_key=catalog['source_key'],palette_index=0)
                    status,value=post('/api/battle-character-preview',request);self.assertEqual(status,200);self.assertEqual(value['record'],asset);self.assertFalse(value['gameplay_verified'])
                for request in [{},dict(body,extra=True),dict(body,expected_source_key='0'*64),dict(body,expected_project_path='foreign')]:self.assertEqual(post('/api/battle-character-resources',request)[0],400)
                for asset_id,palette in [(catalog['textures'][-1]['semantic_id'],0),(catalog['textures'][0]['semantic_id'],True),('foreign',0)]:self.assertEqual(post('/api/battle-character-preview',dict(body,asset_id=asset_id,catalog_source_key=catalog['source_key'],palette_index=palette))[0],400)
            self.assertEqual((project._document(),project.undo_stack),held)
