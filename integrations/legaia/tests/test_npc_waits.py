"""Allocated NPC wait edits retain final ownership and all unrelated bytes."""
from copy import deepcopy
from hashlib import sha256
from unittest import TestCase
from importer.core import ImportError
from importer.man_actor_structure import append_actor_donor
from importer.man_layout import read_man_layout
from importer.wait_authoring import WaitAuthoringContext
from sdk.npc_waits import patch_allocated_waits
from sdk.project import ProjectError
from test_importer_dialogue_authoring import fixture, ACTOR
from test_wait_authoring import END


class NpcWaitTests(TestCase):
    def setup_candidate(self, header=b'\x4a'):
        source, man = fixture(header+b'\x01\x01'+END)
        context = WaitAuthoringContext(source)
        target = context.options(ACTOR)['targets'][0]['semantic_id']
        candidate, allocations = man, {'drafts': []}
        for identifier in ('npc-a', 'npc-b'):
            candidate, row = append_actor_donor(candidate, sha256(candidate).hexdigest(), 1)
            allocations['drafts'].append(dict(row, draft_id=identifier))
        return context, candidate, allocations, target

    def test_two_final_clone_offsets_and_independent_targets(self):
        for header in (b'\x4a', b'\xca\x07'):
            context, candidate, allocations, wait = self.setup_candidate(header)
            requests = [dict(draft_id=identifier, donor_entity_id=ACTOR,
                             entries={wait: {'duration_ticks': value}})
                        for identifier, value in [('npc-a', 0), ('npc-b', 32767)]]
            result, audit = patch_allocated_waits(context, candidate, allocations, requests)
            self.assertEqual(read_man_layout(candidate), read_man_layout(result))
            self.assertEqual(len(audit['changes']), 2)
            touched = set()
            records = {(r['partition'], r['record_index']): r for r in read_man_layout(result)['records']}
            for row, value in zip(audit['changes'], (0, 32767)):
                at = row['decoded_byte_offset'];touched.update(range(at, at+2))
                self.assertEqual(int.from_bytes(result[at:at+2], 'little'), value)
                self.assertEqual(at, records[(1,row['record_index'])]['byte_offset']+row['record_relative_byte_offset'])
            self.assertTrue(all(a == b for i,(a,b) in enumerate(zip(candidate,result)) if i not in touched))
            self.assertNotEqual(records[(1,allocations['drafts'][0]['record_index'])]['byte_offset'],allocations['drafts'][0]['byte_offset'])
            with self.assertRaises(ProjectError):patch_allocated_waits(context,result,allocations,requests)
            unchanged, no_op = patch_allocated_waits(context,candidate,allocations,[dict(requests[0],entries={wait:{'duration_ticks':257}})])
            self.assertEqual(unchanged,candidate);self.assertEqual(no_op['changes'],[])

    def test_ownership_preimages_values_aliases_and_unknown_paths_reject(self):
        context,candidate,allocations,wait=self.setup_candidate()
        request=dict(draft_id='npc-a',donor_entity_id=ACTOR,entries={wait:{'duration_ticks':512}})
        for mutation in [dict(draft_id='missing'),dict(donor_entity_id=ACTOR.replace('0001','0000')),dict(entries={wait:{'duration_ticks':True}}),dict(entries={wait:{'duration_ticks':32768}}),dict(entries={wait.replace('0001','9999'):{'duration_ticks':1}}),dict(payload=b'raw')]:
            with self.assertRaises((ProjectError,ImportError)):patch_allocated_waits(context,candidate,allocations,[dict(request,**mutation)])
        for change in [dict(record_index=1),dict(byte_length=1),dict(donor={'record_index':0}),dict(donor=None)]:
            bad=deepcopy(allocations);bad['drafts'][0].update(change)
            with self.assertRaises((ProjectError,ImportError)):patch_allocated_waits(context,candidate,bad,[request])
        with self.assertRaises(ProjectError):patch_allocated_waits(context,candidate,allocations,[request,request])
        bad=deepcopy(allocations);bad['drafts'].append(bad['drafts'][0])
        with self.assertRaises(ProjectError):patch_allocated_waits(context,candidate,bad,[request])
        layout=read_man_layout(candidate);alias=bytearray(candidate);count0=layout['partition_counts'][0]
        table=0x2b+3*(count0+allocations['drafts'][0]['record_index']);original_table=0x2b+3*(count0+1)
        alias[table:table+3]=alias[original_table:original_table+3]
        with self.assertRaises((ProjectError,ImportError)):patch_allocated_waits(context,bytes(alias),allocations,[request])
        raw=bytearray(candidate);record=next(r for r in layout['records'] if r['partition']==1 and r['record_index']==allocations['drafts'][0]['record_index']);raw[record['byte_offset']]=1
        with self.assertRaises((ProjectError,ImportError)):patch_allocated_waits(context,bytes(raw),allocations,[request])
        result,audit=patch_allocated_waits(context,candidate,allocations,[request]);raw=bytearray(candidate);raw[audit['changes'][0]['decoded_byte_offset']]=3
        with self.assertRaises(ProjectError):patch_allocated_waits(context,bytes(raw),allocations,[request])
        source,man=fixture(b'\x4a\1\1\xff');unsupported=WaitAuthoringContext(source)
        clone,row=append_actor_donor(man,sha256(man).hexdigest(),1)
        with self.assertRaises((ProjectError,ImportError)):patch_allocated_waits(unsupported,clone,{'drafts':[dict(row,draft_id='npc-a')]},[request])
