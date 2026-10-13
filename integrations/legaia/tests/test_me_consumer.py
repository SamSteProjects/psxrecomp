import json
import os
from pathlib import Path
import unittest
from importer.pipeline import _disc_context
from importer.me_archive import entries, replace_entry, encode_channel_delta
from test_me_archive import literal_source
from me_consumer_oracle import Machine, qualified_code, consume, SPANS


class ConsumerMachineTests(unittest.TestCase):
    def test_load_branch_delay_and_signed_multiply(self):
        code={0x1000:0x8c820000,0x1004:0x00401821,0x1008:0x00402821,0x100c:0x03e00008,0x1010:0x24060007}
        m=Machine(code,[(0x3000,bytearray((42).to_bytes(4,'little')),False,'source')]);m.r[4]=0x3000;m.r[2]=9;m.r[31]=0x2000;m.run(0x1000,0x2000)
        self.assertEqual((m.r[3],m.r[5],m.r[6]),(9,42,7))
        code={0x1000:0x10000002,0x1004:0x24050001,0x1008:0x24050002,0x100c:0x03e00008,0x1010:0x24060003}
        m=Machine(code,[]);m.r[31]=0x2000;m.run(0x1000,0x2000);self.assertEqual((m.r[5],m.r[6]),(1,3))
        code={0x1000:0x00850018,0x1004:0x00001012,0x1008:0x00001810,0x100c:0x03e00008,0x1010:0}
        m=Machine(code,[]);m.r[4]=0xffffffff;m.r[5]=2;m.r[31]=0x2000;m.run(0x1000,0x2000);self.assertEqual((m.r[2],m.r[3]),(0xfffffffe,0xffffffff))

    def test_memory_instruction_and_step_guards(self):
        m=Machine({},[(0x3000,bytearray(4),False,'source')])
        for address,size,write in [(0x3000,4,1),(0x3001,4,None),(0x4000,1,None)]:
            with self.assertRaises(ValueError):m.memory(address,size,write)
        with self.assertRaises(ValueError):m.run(0x1000,0x2000)
        with self.assertRaises(ValueError):Machine({0x1000:0xffffffff},[]).run(0x1000,0x2000)
        with self.assertRaises(ValueError):Machine({0x1000:0x08000400,0x1004:0},[]).run(0x1000,0x2000,4)
        with self.assertRaises(ValueError):qualified_code(b'foreign executable')


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Private retail disc required')
class MeConsumerRetailTests(unittest.TestCase):
    def test_literal_oracle_and_all_original_candidate_archive_reads(self):
        with _disc_context(os.environ['LEGAIA_DISC_BIN']) as (image,disc,_,archive):
            executable=image.read_file(image.find('SCUS_942.54'));raw=archive.read_entry(archive.entry(894))
        from importer.player_art_consumer import qualify
        profile=qualify(executable);self.assertEqual(profile['allocation'],'not_supported');self.assertEqual(len(profile['functions']),2)
        for bad in [executable[:-1],b'foreign',bytes([executable[0]^1])+executable[1:]]:
            from importer.core import ImportError
            with self.assertRaises(ImportError):qualify(bad)
        code=qualified_code(executable);proof=[]
        from importer.me_archive import decode_channel_delta
        synthetic=literal_source()
        for seed in (0,0xa5):
            output,info=consume(code,synthetic,len(decode_channel_delta(synthetic)),scratch_seed=seed);self.assertEqual(output,decode_channel_delta(synthetic));self.assertEqual(info['output_written'],len(output))
        zero=bytes([1,1])+bytes(9)
        output,_=consume(code,encode_channel_delta(zero,0x4f),len(zero),scratch_seed=0x5a);self.assertEqual(output,zero)
        for player in range(4):
            for role in (1,2):
                slot_index=player*3+role;original=raw[slot_index*0x10800:(slot_index+1)*0x10800];candidate=original;records=entries(original)
                for row in records:
                    target=bytearray(row['decoded']);target[2]^=1;candidate=replace_entry(candidate,row['entry_index'],bytes(target))
                for row in records:
                    target=bytearray(row['decoded']);target[2]^=1
                    for label,slot,expected,seed in [('retail',original,row['decoded'],0xa5),('candidate',candidate,bytes(target),0x5a)]:
                        output,info=consume(code,slot,len(expected),row['entry_index'],scratch_seed=seed)
                        self.assertEqual(output,expected);self.assertEqual(info['returned'],len(expected));self.assertEqual(info['output_written'],len(expected));self.assertLess(info['scratch_highest'],1024)
                        header=3+2*len(records);start=row['byte_offset'];end=start+row['byte_length'];self.assertTrue(all(at<header or start<=at<end for at in info['source_reads']))
                        proof.append(dict(slot_index=slot_index,stream_index=row['entry_index'],layer=label,decoded_bytes=len(expected),**info))
                print(f'Qualified instruction oracle: player {player} archive {role} / {len(records)} original and candidate reads',flush=True)
        self.assertEqual(len(proof),174)
        output_dir=os.getenv('PLAYER_ART_CONSUMER_PROOF_DIR')
        if output_dir:
            out=Path(output_dir);out.mkdir(parents=True,exist_ok=True);(out/'consumer-proof.json').write_text(json.dumps(dict(disc_sha256=disc,profile=profile,function_spans=[dict(address=f'0x{a:08X}',byte_length=n,sha256=h) for a,n,h in SPANS],reads=proof,gameplay_verified=False),indent=2),encoding='utf-8')


if __name__=='__main__':unittest.main()
