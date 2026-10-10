from pathlib import Path
from copy import deepcopy
from hashlib import sha256
import base64,struct,tempfile,unittest
from unittest.mock import patch
from importer.textures import parse_tim,TextureCatalog
from sdk.project import ProjectService,ProjectError
from sdk.worldmap_texture import inspect
H='a'*64

def fixture(indexed=True,clut=True):
    raw=struct.pack('<II',16,8 if indexed and clut else 0 if indexed else 2)
    if indexed and clut:
        colors=[0,0x801f,0x03e0,0x7c00]+[0]*12+[0x7fff]*16
        raw+=struct.pack('<IHHHH',12+len(colors)*2,0,0,32,1)+struct.pack('<32H',*colors)
    raw+=struct.pack('<IHHHHH',14,0,0,1,1,0x3210)
    tim=parse_tim(raw);catalog=TextureCatalog('map01',H);catalog.textures.append((tim,dict(semantic_id='texture://map01/kingdom/0000',pack_slot=0,prot_entry_index=86,descriptor_index=0,byte_offset=4,byte_length=len(raw),decoded_member_sha256=sha256(raw).hexdigest())))
    return tim,catalog.metadata()['textures'][0],dict(disc_sha256=H,bundle_sha256=H,texture_pack_sha256=H)

class WorldTextureTests(unittest.TestCase):
 def setUp(self):
    self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.p=ProjectService(Path(self.temp.name));self.p.disc_path='private';self.key=patch('sdk.worldmap_texture.state_key',return_value=H);self.key.start();self.addCleanup(self.key.stop)
 def test_explicit_native_palette_alpha_stp_and_unchanged_empty_project(self):
    f=fixture();held=deepcopy((self.p._document(),self.p.imports,self.p.selected,self.p.undo_stack,self.p.redo_stack))
    with patch('sdk.worldmap_texture.load_worldmap_texture',return_value=f):
        a=inspect(self.p,f[1]['semantic_id'],H,f[1]['decoded_member_sha256'],0);b=inspect(self.p,f[1]['semantic_id'],H,f[1]['decoded_member_sha256'],1)
        self.assertEqual(base64.b64decode(a['rgba_base64']),bytes([0,0,0,0,255,0,0,255,0,255,0,255,0,0,255,255]));self.assertEqual(base64.b64decode(a['stp_base64']),bytes([0,1,0,0]));self.assertEqual(base64.b64decode(b['rgba_base64']),bytes([255,255,255,255])*4);self.assertEqual(a['palette_count'],2)
        for palette in (-1,True,2,32768):
            with self.assertRaises(ProjectError):inspect(self.p,f[1]['semantic_id'],H,f[1]['decoded_member_sha256'],palette)
        with self.assertRaises(ProjectError):inspect(self.p,f[1]['semantic_id'],H,'0'*64,0)
    self.assertEqual((self.p._document(),self.p.imports,self.p.selected,self.p.undo_stack,self.p.redo_stack),held)
 def test_no_local_clut_explicitly_unsupported_and_direct_color_has_no_palette(self):
    for indexed,clut,status,count in [(True,False,'unsupported',0),(False,False,'available',1)]:
        f=fixture(indexed,clut)
        with patch('sdk.worldmap_texture.load_worldmap_texture',return_value=f):
            r=inspect(self.p,f[1]['semantic_id'],H,f[1]['decoded_member_sha256'],0);self.assertEqual((r['status'],r['palette_count']),(status,count))
            if not count:self.assertEqual(r['rgba_base64'],'');self.assertIn('CLUT',r['reason'])
            with self.assertRaises(ProjectError):inspect(self.p,f[1]['semantic_id'],H,f[1]['decoded_member_sha256'],1)
 def test_stale_live_and_noncanonical_ids_refuse_before_source(self):
    with patch('sdk.worldmap_texture.load_worldmap_texture',side_effect=AssertionError('must not load')):
        for id,key in [('texture://map01/kingdom/00000',H),('texture://town01/0000',H),('texture://map01/kingdom/0000','0'*64)]:
            with self.assertRaises(ProjectError):inspect(self.p,id,key,H,0)
        self.p.mode='live'
        with self.assertRaises(ProjectError):inspect(self.p,'texture://map01/kingdom/0000',H,H,0)
if __name__=='__main__':unittest.main()
