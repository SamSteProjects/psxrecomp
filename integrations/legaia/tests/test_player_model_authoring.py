import os,struct,unittest
from hashlib import sha256
from copy import deepcopy
from unittest.mock import patch
from importer.player_battle import _sources,assemble_tmd,table
from importer.player_model_authoring import export_player_model,import_player_model,project_tmd
from importer.animation_glb import _read_glb
from importer.model_glb import _write_glb
from importer.core import ImportError,decompress_lzs


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc is private')
class PlayerModelAuthoringTests(unittest.TestCase):
    def test_noop_and_mesh_edits_preserve_other_native_sections(self):
        _,sources=_sources(os.environ['LEGAIA_DISC_BIN']);modified=0
        for entry,_,_,raw in sources:
            ids=[0]*5;key=sha256(raw).hexdigest();glb,binding=export_player_model(raw,key,ids);held=deepcopy(binding);candidate,report=import_player_model(raw,binding,glb);self.assertEqual(candidate,raw);self.assertEqual(report['changes'],[])
            doc,binary=_read_glb(glb);doc['nodes'][0]['translation']=[1,0,0];doc['nodes'][-1]['translation']=[0,0,1];changed_glb=_write_glb(doc,binary);candidate,report=import_player_model(raw,binding,changed_glb);self.assertTrue(report['sections']);self.assertEqual(len(candidate),len(raw));before,assembly,tmd=assemble_tmd(raw,ids);after,_,current=assemble_tmd(candidate,ids)
            for obj in before['objects']:
                i=obj['object_index'];delta=[1,0,0] if i==0 else [0,0,1] if i==len(before['objects'])-1 else [0,0,0]
                for j in range(obj['vertex_start'],obj['vertex_start']+obj['vertex_count']):self.assertEqual(after['vertices'][j],[v+d for v,d in zip(before['vertices'][j],delta)])
            changed={s['record_index']:s for s in report['sections']}
            for r in table(raw):
                at=r['byte_offset'];end=at+r['byte_length']
                if r['record_index'] not in changed:self.assertEqual(candidate[at:end],raw[at:end]);continue
                size=struct.unpack_from('<I',raw,at)[0];old,_=decompress_lzs(raw[at+4:end],size);new,_=decompress_lzs(candidate[at+4:end],size);section=changed[r['record_index']];start=section['decoded_pool_offset'];stop=start+section['pool_byte_length'];self.assertEqual(new[:start],old[:start]);self.assertEqual(new[stop:],old[stop:]);self.assertEqual(candidate[at:at+4],raw[at:at+4]);modified+=1
            self.assertEqual(candidate[:0x8000],raw[:0x8000]);self.assertEqual(binding,held);self.assertEqual(sha256(current).hexdigest(),report['proposed_tmd_sha256'])
        self.assertGreaterEqual(modified,4)

    def test_foreign_binding_and_non_pool_edits_refuse(self):
        _,sources=_sources(os.environ['LEGAIA_DISC_BIN']);raw=sources[0][3];key=sha256(raw).hexdigest();glb,binding=export_player_model(raw,key,[0]*5)
        bad=deepcopy(binding);bad['source_sha256']='0'*64
        with self.assertRaises(ImportError):import_player_model(raw,bad,glb)
        bad=deepcopy(binding);bad['equipped'][0]=255
        with self.assertRaises(ImportError):import_player_model(raw,bad,glb)
        _,_,tmd=assemble_tmd(raw,[0]*5);candidate=bytearray(tmd);candidate[12]^=1
        with self.assertRaises(ImportError):project_tmd(raw,key,[0]*5,bytes(candidate))
        with self.assertRaises(ImportError):project_tmd(raw,'0'*64,[0]*5,tmd)
        doc,binary=_read_glb(glb);doc['nodes'][0]['translation']=[1,0,0];edited=_write_glb(doc,binary)
        with patch('importer.player_model_authoring.compress_lzs',return_value=bytes(len(raw))):
            with self.assertRaisesRegex(ImportError,'compressed allocation'):import_player_model(raw,binding,edited)
