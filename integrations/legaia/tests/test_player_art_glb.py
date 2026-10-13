import base64,json,os,struct,unittest
from hashlib import sha256
from pathlib import Path
from importer.core import ImportError
from importer.player_art_glb import import_player_art_glb
from importer.animation_glb import _read_glb
from importer.model_glb import _write_glb
from importer.me_archive import entries

@unittest.skipUnless(os.getenv('PLAYER_ART_CURRENT_EXPORT_CASES'),'Private qualified Current export fixtures required')
class ArtGlbTests(unittest.TestCase):
    def test_roundtrip_changed_aliases_counts_and_neighbors(self):
        cases=json.loads(Path(os.environ['PLAYER_ART_CURRENT_EXPORT_CASES']).read_text(encoding='utf-8'))['cases'];clips=[c for c in cases if c['selection']['mode']=='clip'];self.assertEqual(len(clips),2)
        for c in clips:
            i=c['inspection'];base=i['base_playback'];stream=base['stream'];original=base64.b64decode(base['source_slot_base64']);current=base64.b64decode(i['current_slot_base64']);parts=base['base_inspection']['assembly']['animation_part_indices'];content=base64.b64decode(c['export']['glb_base64']);catalog=c['art_report']['catalog']
            args=(original,catalog,stream['archive_asset_id'],stream['semantic_id'],current,sha256(current).hexdigest(),parts)
            candidate,report=import_player_art_glb(*args,content,fps=23.5);self.assertEqual(candidate,current);self.assertEqual(report['edits'],[])
            doc,binary=_read_glb(content);binary=bytearray(binary)
            for channel in doc['animations'][0]['channels']:
                if channel['target']['path']=='translation' and parts[channel['target']['node']]==0:
                    accessor=doc['accessors'][doc['animations'][0]['samplers'][channel['sampler']]['output']];at=doc['bufferViews'][accessor['bufferView']]['byteOffset'];struct.pack_into('<f',binary,at,struct.unpack_from('<f',binary,at)[0]+1)
            changed=_write_glb(doc,bytes(binary));candidate,report=import_player_art_glb(*args,changed,fps=23.5);self.assertEqual(len(report['edits']),1);self.assertEqual(report['edits'][0]['frame_index'],0);self.assertEqual(report['edits'][0]['part_index'],0)
            row=entries(current)[stream['stream_index']];at=row['byte_offset'];end=at+row['byte_length'];self.assertEqual(candidate[:at],current[:at]);self.assertEqual(candidate[end:],current[end:]);decoded=entries(candidate)[stream['stream_index']]['decoded'];expected=bytearray(row['decoded']);expected[2]=(expected[2]+1)&255;self.assertEqual(decoded,bytes(expected))
            alias_part=next(part for part in set(parts) if parts.count(part)>1);doc,raw_binary=_read_glb(content);raw_binary=bytearray(raw_binary);one=next(channel for channel in doc['animations'][0]['channels'] if channel['target']['path']=='translation' and parts[channel['target']['node']]==alias_part);accessor=doc['accessors'][doc['animations'][0]['samplers'][one['sampler']]['output']];offset=doc['bufferViews'][accessor['bufferView']]['byteOffset'];struct.pack_into('<f',raw_binary,offset,struct.unpack_from('<f',raw_binary,offset)[0]+1)
            with self.assertRaisesRegex(ImportError,'aliases disagree'):import_player_art_glb(*args,_write_glb(doc,bytes(raw_binary)),fps=23.5)
            for kwargs in [dict(fps=True),dict(fps=0),dict(fps=float('nan')),dict(fps=121),dict(fps=23.5,object_node_indices=[0]*len(parts))]:
                with self.assertRaises(ImportError):import_player_art_glb(*args,changed,**kwargs)
            with self.assertRaises(ImportError):import_player_art_glb(*args[:-1],parts[:-2],changed,fps=23.5)

if __name__=='__main__':unittest.main()
