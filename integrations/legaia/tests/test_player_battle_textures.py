import os,struct,unittest
from importer.player_battle import discover,preview,_sources
from importer.core import decompress_lzs


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc is private')
class PlayerBattleTextureTests(unittest.TestCase):
    def test_static_crops_against_ordered_original_upload_words(self):
        disc=os.environ['LEGAIA_DISC_BIN'];catalog=discover(disc);_,sources=_sources(disc);self.assertEqual(sum(len(m['textures']) for m in catalog['models']),153);pixels=matches=0
        rects=[(0,128,32,128),(0,0,64,128),(64,0,32,128),(64,128,32,128),(96,128,32,128)]
        for m in catalog['models']:
            raw=sources[m['player_index']][3]
            for ids in [[0]*5,[next(r['item_id'] for r in m['descriptors'] if r['section_index']==i) for i in range(5)]]:
                _,_,g,a=preview(disc,m['semantic_id'],catalog['source_key'],ids);desc,ca,cb,budget=struct.unpack_from('<4I',raw);bank,_=decompress_lzs(raw[16:desc],budget);blocks=[(bank,ca,(32,128,32,128)),(bank,cb,(96,0,32,128))]
                for r in a['sections']:
                    at=r['byte_offset'];d,_=decompress_lzs(raw[at+4:at+r['byte_length']],struct.unpack_from('<I',raw,at)[0])
                    if struct.unpack_from('<H',d,18)[0]:blocks.append((d,struct.unpack_from('<I',d,12)[0],rects[r['section_index']]))
                image={};palette={}
                for d,at,(x,y,w,h) in blocks:
                    cx,cn=struct.unpack_from('<2H',d,at)
                    for i in range(cn):v=struct.unpack_from('<H',d,at+4+i*2)[0];palette[cx+i]=v|0x8000 if v else 0
                    start=at+4+cn*2
                    for i in range(w*h):image[(320+x+i%w,256+y+i//w)]=struct.unpack_from('<H',d,start+i*2)[0]
                for t in g['textures']:
                    if t['status']!='address_match':self.assertNotIn('rgba',t);continue
                    mat=g['materials'][t['material_index']];page=mat['tpage'];clut=mat['clut'];self.assertEqual((clut>>6)&511,480);self.assertEqual((page>>7)&3,0);u0,v0=t['uv_origin'];matches+=1
                    for i in range(t['width']*t['height']):
                        u=u0+i%t['width'];v=v0+i//t['width'];word=image[((page&15)*64+u//4,((page>>4)&1)*256+v)];index=(word>>((u%4)*4))&15;colour=palette[(clut&63)*16+index];expand=lambda n:(n<<3)|(n>>2);rgba=bytes([expand(colour&31),expand((colour>>5)&31),expand((colour>>10)&31),255 if colour else 0]);self.assertEqual(t['rgba'][i*4:i*4+4],rgba);self.assertEqual(t['stp'][i],colour>>15);pixels+=1
        self.assertGreater(matches,50);self.assertGreater(pixels,300000);print(f'Independent native texture proof: {matches} crops, {pixels} RGBA/STP pixels')
