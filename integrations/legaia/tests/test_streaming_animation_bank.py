"""Raw ANM allocation preserves opaque chunks and composes with MAN growth."""
from hashlib import sha256
import struct
import unittest
from importer.core import ImportError,parse_man
from importer.streaming_man import streaming_chunks
from importer.streaming_animation_bank import grow_streaming_animation_bank,rebuild_streaming_animation_bank_entry
from importer.prot_rebuild import rebuild_streaming_man_entry
from importer.model_pack_archive import _archive
from importer.man_actor_structure import append_actor_candidates
from test_animation_bank_growth import fixture as bank_fixture
from test_man_actor_structure import fixture as man_fixture
from test_model_pack_archive import archive_source


def chunk(kind,data):return struct.pack('<I',(kind<<24)|len(data))+data


class StreamingAnimationBank(unittest.TestCase):
    def test_raw_bank_growth_noop_and_exact_opaque_preservation(self):
        _,bank,expanded,_,_=bank_fixture();prefix=chunk(1,b'HEADraw!')
        suffix=chunk(3,man_fixture())+chunk(1,b'TAILraw!')+bytes(4)+b'opaque suffix'
        source=prefix+chunk(5,bank)+suffix;offset=len(prefix)
        result,audit=grow_streaming_animation_bank(source,sha256(source).hexdigest(),offset,sha256(bank).hexdigest(),expanded)
        growth=len(expanded)-len(bank)
        self.assertEqual(result[:offset],prefix);self.assertEqual(result[offset+4:offset+4+len(expanded)],expanded)
        self.assertEqual(result[offset+4+len(expanded):],suffix);self.assertEqual(audit['growth_bytes'],growth)
        self.assertTrue(audit['terminated_chain_verified']);self.assertEqual(audit['bank_audit']['allocated_record_count'],1)
        self.assertEqual(audit['relocated_chunks'][0]['after'],audit['relocated_chunks'][0]['before']+growth)
        same,noop=grow_streaming_animation_bank(source,sha256(source).hexdigest(),offset,sha256(bank).hexdigest(),bank)
        self.assertEqual(same,source);self.assertEqual(noop['growth_bytes'],0)
        for digest,locator,bank_hash,payload in [('0'*64,offset,sha256(bank).hexdigest(),expanded),
            (sha256(source).hexdigest(),True,sha256(bank).hexdigest(),expanded),
            (sha256(source).hexdigest(),0,sha256(bank).hexdigest(),expanded),
            (sha256(source).hexdigest(),offset,'0'*64,expanded),
            (sha256(source).hexdigest(),offset,sha256(bank).hexdigest(),expanded+b'x')]:
            with self.assertRaises(ImportError):grow_streaming_animation_bank(source,digest,locator,bank_hash,payload)
        broken=source[:offset+4+len(bank)]
        with self.assertRaisesRegex(ImportError,'terminated'):grow_streaming_animation_bank(broken,sha256(broken).hexdigest(),offset,sha256(bank).hexdigest(),expanded)
        damaged=bytearray(expanded);damaged[-1]^=1
        with self.assertRaises(ImportError):grow_streaming_animation_bank(source,sha256(source).hexdigest(),offset,sha256(bank).hexdigest(),bytes(damaged))
        overlap=struct.pack('<I',(1<<24)|3)+chunk(5,bank)+bytes(4)
        with self.assertRaisesRegex(ImportError,'overlapping opaque'):
            grow_streaming_animation_bank(overlap,sha256(overlap).hexdigest(),4,sha256(bank).hexdigest(),expanded)

    def test_archive_bank_and_man_growth_in_both_chunk_orders_with_explicit_remap(self):
        _,bank,expanded,_,_=bank_fixture();man=man_fixture()
        candidate,_=append_actor_candidates(man,sha256(man).hexdigest(),[dict(id='npc',donor_record_index=1,position=dict(x=832,z=896))])
        candidate+=bytes(-len(candidate)%4)
        for man_first in (False,True):
            pieces=[chunk(3,man),chunk(5,bank)] if man_first else [chunk(5,bank),chunk(3,man)]
            carrier=chunk(1,b'HEADraw!')+b''.join(pieces)+chunk(1,b'TAILraw!')+bytes(4)+b'opaque suffix'
            source,_=archive_source(carrier);rows=streaming_chunks(carrier)[0]
            anm_at=next(c['header_offset'] for c in rows if c['type_byte']==5);man_at=next(c['header_offset'] for c in rows if c['type_byte']==3)
            grown,audit=rebuild_streaming_animation_bank_entry(source,sha256(source).hexdigest(),1,anm_at,sha256(bank).hexdigest(),expanded)
            relocated=next((c for c in audit['carrier']['relocated_chunks'] if c['before']==man_at),None)
            proposed_man=relocated['after'] if relocated else man_at
            result,man_audit=rebuild_streaming_man_entry(grown,sha256(grown).hexdigest(),1,proposed_man,sha256(man).hexdigest(),candidate)
            other,first_man=rebuild_streaming_man_entry(source,sha256(source).hexdigest(),1,man_at,sha256(man).hexdigest(),candidate)
            relocated_anm=next((c for c in first_man['container']['relocated_chunks'] if c['before']==anm_at),None)
            proposed_anm=relocated_anm['after'] if relocated_anm else anm_at
            reverse,final_bank=rebuild_streaming_animation_bank_entry(other,sha256(other).hexdigest(),1,proposed_anm,sha256(bank).hexdigest(),expanded)
            self.assertEqual(result,reverse);self.assertEqual(result[-8*2048:],source[-8*2048:])
            archive=_archive(result);raw=archive.read_entry(archive.entry(1));chunks,terminated=streaming_chunks(raw)
            self.assertTrue(terminated);new_bank=next(c for c in chunks if c['type_byte']==5);new_man=next(c for c in chunks if c['type_byte']==3)
            self.assertEqual(raw[new_bank['header_offset']+4:new_bank['header_offset']+4+new_bank['size']],expanded)
            actual=raw[new_man['header_offset']+4:new_man['header_offset']+4+new_man['size']]
            self.assertEqual(actual,candidate);self.assertEqual(len(parse_man(actual).actors),2)
            self.assertTrue(final_bank['reopened_bank_verified']);self.assertTrue(man_audit['reopened_man_verified'])
            same,_=rebuild_streaming_animation_bank_entry(source,sha256(source).hexdigest(),1,anm_at,sha256(bank).hexdigest(),bank)
            self.assertEqual(same,source)
            if not man_first:
                with self.assertRaises(ImportError):rebuild_streaming_man_entry(grown,sha256(grown).hexdigest(),1,man_at,sha256(man).hexdigest(),candidate)


if __name__=='__main__':unittest.main()
