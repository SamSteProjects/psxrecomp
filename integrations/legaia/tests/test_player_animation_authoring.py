import json,os,struct,unittest
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch
from importer.core import ImportError,decompress_lzs
from importer.player_battle import _sources,actions,decode_part,assemble_tmd
from importer.player_animation_authoring import _encode,patch_player_action


class PlayerPartEncodingTests(unittest.TestCase):
    def test_all_full_precision_extremes_and_shared_nibbles(self):
        for translation in ([-2048,-1,2047],[0,1,-1],[2047,-2048,0]):
            for rotation in ([0,1,4095],[4095,2048,17],[256,255,4094]):
                encoded=_encode(translation,rotation)
                self.assertEqual(len(encoded),9)
                self.assertEqual(decode_part(encoded),dict(translation=translation,rotation_psx=rotation))


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc is private')
class PlayerAnimationAuthoringTests(unittest.TestCase):
    def test_every_nonempty_action_preserves_all_protected_native_bytes(self):
        _,sources=_sources(os.environ['LEGAIA_DISC_BIN']);proof=[];empty=0
        for slot,(_,_,_,raw) in enumerate(sources):
            clips,bank=actions(raw,slot,'0'*64);key=sha256(raw).hexdigest();desc,_,_,budget=struct.unpack_from('<4I',raw);_,_,tmd=assemble_tmd(raw,[0]*5)
            for clip in clips:
                if not clip['preview_supported']:
                    empty+=1
                    with self.assertRaises(ImportError):patch_player_action(raw,key,slot,clip['action_slot'],clip['source_record']['sha256'],[])
                    continue
                source=clip['source_record'];frame=clip['frame_count']-1;part=clip['part_count']-1;offset=source['byte_offset']+2+(frame*clip['part_count']+part)*9;before=decode_part(bank[offset:offset+9])
                no_op=[dict(frame_index=frame,part_index=part,translation=dict(zip('xyz',before['translation'])),rotation_psx=dict(zip('xyz',before['rotation_psx'])))];unchanged,no_report=patch_player_action(raw,key,slot,clip['action_slot'],source['sha256'],no_op);self.assertEqual(unchanged,raw);self.assertEqual(no_report['channels'],[])
                edits=[dict(frame_index=frame,part_index=part,translation=dict(x=-2048,y=2047,z=-1),rotation_psx=dict(x=4095,y=1,z=17))];held=deepcopy(edits);changed,report=patch_player_action(raw,key,slot,clip['action_slot'],source['sha256'],edits);reopened,used=decompress_lzs(changed[16:desc],budget)
                # Independent literal bit packing, preserving every other bank byte.
                expected=bytes((0,255,0x78,255,255,0xff,1,17,0));self.assertEqual(reopened[offset:offset+9],expected);self.assertEqual(reopened[:offset],bank[:offset]);self.assertEqual(reopened[offset+9:],bank[offset+9:]);self.assertEqual(changed[:16],raw[:16]);self.assertEqual(changed[desc:],raw[desc:]);self.assertEqual(changed[16+used:desc],raw[16+used:desc]);self.assertEqual(assemble_tmd(changed,[0]*5)[2],tmd);self.assertEqual(edits,held)
                self.assertEqual(report['proposed_file_sha256'],sha256(changed).hexdigest());self.assertEqual(report['proposed_bank_sha256'],sha256(reopened).hexdigest());self.assertEqual({r['byte_offset'] for r in report['changed_bytes']},{i for i,(a,b) in enumerate(zip(bank,reopened)) if a!=b});self.assertEqual({r['field'] for r in report['channels']},{field+'.'+axis for field in ('translation','rotation_psx') for axis in 'xyz' if before[field]['xyz'.index(axis)]!=edits[0][field][axis]})
                proof.append(dict(player_index=slot,action_slot=clip['action_slot'],frame_index=frame,part_index=part,source_file_sha256=key,proposed_file_sha256=report['proposed_file_sha256'],compression=report['compression']))
        self.assertEqual((len(proof),empty),(38,10))
        out=os.getenv('LEGAIA_PLAYER_ACTION_PROJECTION_PROOF')
        if out:Path(out).write_text(json.dumps(dict(actions=proof,empty_slots_refused=empty,protected_bytes_preserved=True,model_assemblies_unchanged=True,gameplay_verified=False),indent=2),encoding='utf-8')

    def test_foreign_sources_ambiguous_edits_precision_and_capacity_refuse(self):
        _,sources=_sources(os.environ['LEGAIA_DISC_BIN']);raw=sources[0][3];clips,_=actions(raw,0,'0'*64);key=sha256(raw).hexdigest();clip=clips[0];edit=dict(frame_index=0,part_index=0,translation=dict(x=1));args=[raw,key,0,0,clip['source_record']['sha256']]
        for changes in ([dict(edit,frame_index=True)],[dict(edit,part_index=999)],[dict(edit,translation=dict(x=True))],[dict(edit,translation=dict(x=2048))],[dict(edit,rotation_psx=dict(x=4096))],[dict(edit,rotation_psx=dict(x=.5))],[dict(edit,translation={})],[dict(edit,unknown=0)],[edit,edit]):
            with self.assertRaises(ImportError):patch_player_action(*args,changes)
        for index in (1,4):
            bad=list(args);bad[index]='0'*64
            with self.assertRaises(ImportError):patch_player_action(*bad,[edit])
        with patch('importer.player_animation_authoring.compress_lzs',return_value=bytes(len(raw))),patch('importer.player_animation_authoring.compress_lzs_optimal',return_value=bytes(len(raw))):
            with self.assertRaisesRegex(ImportError,'compressed allocation'):patch_player_action(*args,[edit])
