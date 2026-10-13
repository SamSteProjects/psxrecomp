import os
from copy import deepcopy
from hashlib import sha256
import unittest
from importer.core import ImportError
from importer.pipeline import _disc_context
from importer.player_art_animation import discover
from importer.player_art_authoring import owner, compose
from importer.player_battle import decode_part
from importer.me_archive import entries


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'), 'Private retail disc required')
class PlayerArtOwnershipTests(unittest.TestCase):
    def test_all_stream_owners_compose_exact_channels_and_refuse_tampering(self):
        disc = os.environ['LEGAIA_DISC_BIN']; catalog = discover(disc)
        with _disc_context(disc) as (_, _, _, archive): raw = archive.read_entry(archive.entry(894))
        total = refusals = 0
        for archive in catalog['archives']:
            start = archive['slot_index'] * 0x10800; original = raw[start:start+0x10800]
            records = entries(original); values = {}
            for stream in catalog['streams']:
                if stream['archive_asset_id'] != archive['semantic_id']: continue
                row = records[stream['stream_index']]; channels = decode_part(row['decoded'][2:11]); channels['translation'][0] ^= 1
                edits = [dict(frame_index=0, part_index=0, **channels)]
                binding = owner(original, catalog, archive['semantic_id'], stream['semantic_id'], edits)
                held = deepcopy(binding); values[stream['semantic_id']] = binding
                for change in [lambda v:v.update(current_body_sha256='0'*64), lambda v:v.update(decoded_sha256='0'*64), lambda v:v.update(extra=True), lambda v:v['source_record'].update(byte_offset=0), lambda v:v['edits'][0].update(frame_index=True)]:
                    bad = deepcopy(binding); change(bad)
                    with self.assertRaises(ImportError): compose(original,catalog,archive['semantic_id'],{stream['semantic_id']:bad})
                    refusals += 1
                for invalid in [[], edits*2, [dict(edits[0],part_index=stream['part_count'])], [dict(edits[0],translation=[2048,0,0])], [dict(edits[0],rotation_psx=[0,True,0])], [dict(frame_index=0,part_index=0,**decode_part(row['decoded'][2:11]))]]:
                    with self.assertRaises(ImportError): owner(original,catalog,archive['semantic_id'],stream['semantic_id'],invalid)
                    refusals += 1
                self.assertEqual(binding,held); total += 1
            candidate = compose(original,catalog,archive['semantic_id'],values)
            self.assertEqual(candidate,compose(original,catalog,archive['semantic_id'],dict(reversed(list(values.items())))))
            for old,new in zip(records,entries(candidate)):
                for field in ['entry_index','size_word','compressed','byte_offset','byte_length']: self.assertEqual(new[field],old[field])
                expected=bytearray(old['decoded']); expected[2]^=1; self.assertEqual(new['decoded'],bytes(expected))
                binding=next(v for v in values.values() if v['source_record']['byte_offset']==start+old['byte_offset'])
                at=old['byte_offset'];end=at+old['byte_length'];self.assertEqual(sha256(candidate[at:end]).hexdigest(),binding['current_body_sha256'])
            header=3+2*len(records);tail=records[-1]['byte_offset']+records[-1]['byte_length'];self.assertEqual(candidate[:header],original[:header]);self.assertEqual(candidate[tail:],original[tail:])
            foreign=next(v for v in catalog['streams'] if v['archive_asset_id']!=archive['semantic_id'])
            with self.assertRaises(ImportError): owner(original,catalog,archive['semantic_id'],foreign['semantic_id'],list(values.values())[0]['edits'])
            refusals += 1
        self.assertEqual(total,87);self.assertEqual(refusals,965)
        print('87 canonical art owners; eight complete composed slots; exact packed-channel changes and 965 owner/ledger/archive refusals',flush=True)


if __name__=='__main__':unittest.main()
