"""Native PLAYER GLB no-op, twelve-bit edit and attachment ownership checks."""
import os,struct,unittest,json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from importer.core import ImportError
from importer.player_battle import _sources,actions,assemble,action_frames_source,decode_part
from importer.player_animation_glb import import_player_action_glb
from importer.animation_glb import _quantize_rotation,_orientation_error
from importer.export import encode_model_glb
from test_importer_export import parse_glb
from test_animation_glb import encode,quaternion

@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc is private')
class PlayerAnimationGLBTests(unittest.TestCase):
    def test_complete_existing_actions_and_full_precision_changes(self):
        digest,sources=_sources(os.environ['LEGAIA_DISC_BIN']);proof=[];total=0
        for slot,(_,_,_,raw) in enumerate(sources):
            clips,bank=actions(raw,slot,digest);base,assembly=assemble(raw,[0]*5)
            for clip in clips:
                if not clip['preview_supported']:continue
                g=deepcopy(base);g['frames']=action_frames_source(raw,slot,digest,assembly,clip);content,_=encode_model_glb(g,clip_fps=17.5)
                args=(raw,sha256(raw).hexdigest(),slot,clip['action_slot'],clip['source_record']['sha256'],[0]*5)
                candidate,report=import_player_action_glb(*args,content,fps=17.5);self.assertEqual(candidate,raw);self.assertEqual(report['edits'],[]);total+=clip['frame_count']
                if clip['action_slot']==0:
                    doc,payload=parse_glb(content);payload=bytearray(payload)
                    def offset(sampler):
                        a=doc['accessors'][sampler['output']];v=doc['bufferViews'][a['bufferView']];return v['byteOffset']+a.get('byteOffset',0)
                    samplers=doc['animations'][0]['samplers'];at=offset(samplers[0]);old=struct.unpack_from('<f',payload,at)[0];struct.pack_into('<f',payload,at,old+1)
                    desired=quaternion([17/16,33/16,49/16]);struct.pack_into('<4f',payload,offset(samplers[1]),*desired)
                    candidate,changed=import_player_action_glb(*args,encode(doc,bytes(payload)),fps=17.5);_,after=actions(candidate,slot,digest);at=clip['source_record']['byte_offset']+2;part=decode_part(after[at:at+9]);before=decode_part(bank[at:at+9]);self.assertEqual(part['translation'][0],before['translation'][0]+1);self.assertTrue(any(v%16 for v in part['rotation_psx']));self.assertLess(changed['maximum_angular_error_degrees'],.15);self.assertEqual(after[:at],bank[:at]);self.assertEqual(after[at+9:],bank[at+9:]);desc=struct.unpack_from('<I',raw)[0];self.assertEqual(candidate[:16],raw[:16]);self.assertEqual(candidate[desc:],raw[desc:])
                    # Change only an attachment track, whose body alias is unchanged.
                    original_doc,original_payload=parse_glb(content);bad=bytearray(original_payload);index=len(assembly['animation_part_indices'])-1;s=original_doc['animations'][0]['samplers'][index*2];a=original_doc['accessors'][s['output']];v=original_doc['bufferViews'][a['bufferView']];at=v['byteOffset'];old=struct.unpack_from('<f',bad,at)[0];struct.pack_into('<f',bad,at,old+1)
                    with self.assertRaisesRegex(ImportError,'attachment and body'):import_player_action_glb(*args,encode(original_doc,bytes(bad)),fps=17.5)
                    for fps in (True,0,121,float('nan'),'30'):
                        with self.assertRaises(ImportError):import_player_action_glb(*args,content,fps=fps)
                proof.append(dict(player_index=slot,action_slot=clip['action_slot'],frames=clip['frame_count'],parts=clip['part_count'],attachment_alias_checks=report['attachment_alias_checks'],source_exact=True))
        self.assertEqual(len(proof),38)
        output=os.getenv('LEGAIA_PLAYER_GLB_IMPORT_PROOF')
        if output:Path(output).write_text(json.dumps(dict(actions=proof,frames=total,full_precision_edits=4,attachment_conflict_refusals=4,gameplay_verified=False),indent=2),encoding='utf-8')


class PlayerRotationPrecisionTests(unittest.TestCase):
    def test_source_biased_full_precision_and_gimbal_neighborhood(self):
        for target in ([17,33,49],[4095,1,2049],[512,1024,1537],[1537,3072,512],[999,1023,3333],[999,1025,3333]):
            q=quaternion([v/16 for v in target])
            exact,error=_quantize_rotation(q,target,rotation_step=1,maximum_degrees=.15)
            self.assertEqual(exact,target)
            sampled,error=_quantize_rotation(q,[0,0,0],rotation_step=1,maximum_degrees=.15)
            self.assertTrue(all(0<=v<=4095 for v in sampled));self.assertLess(error,.15)
            self.assertLess(_orientation_error(q,quaternion([v/16 for v in sampled])),.15*3.141592653589793/180)
