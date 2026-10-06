"""Allocated NPC facing composes with movement/waits and preserves all other bytes."""
from copy import deepcopy
from unittest import TestCase
from importer.core import ImportError
from importer.facing_authoring import FacingAuthoringContext
from importer.man_layout import read_man_layout
from importer.movement_authoring import MovementAuthoringContext
from importer.wait_authoring import WaitAuthoringContext
from sdk.npc_facing import patch_allocated_facing
from sdk.npc_movement import patch_allocated_movement
from sdk.npc_waits import patch_allocated_waits
from sdk.project import ProjectError
from test_importer_dialogue_authoring import fixture,ACTOR
from test_wait_authoring import END
from importer.man_actor_structure import append_actor_donor
from hashlib import sha256

class NpcFacingTests(TestCase):
    def fixture(self,instruction):
        source,candidate=fixture(instruction+b'\x4a\x0a\0'+END);allocations={'drafts':[]}
        for name in ('npc-a','npc-b'):
            candidate,row=append_actor_donor(candidate,sha256(candidate).hexdigest(),1);allocations['drafts'].append(dict(row,draft_id=name))
        context=FacingAuthoringContext(source);target=context.options(ACTOR)['targets'][0]
        return context,candidate,allocations,target

    def test_families_contexts_all_sectors_final_records_and_composed_movement_waits(self):
        for instruction in (b'\x38\xa3\x80',b'\xb8\xf8\xa3\x80',b'\x4c\x51\0\x80\xb3\x09',b'\xcc\xf8\x51\0\x80\xb3\x09'):
            for sector in range(8):
                context,candidate,allocations,target=self.fixture(instruction)
                waits=WaitAuthoringContext(context._source);wait=waits.options(ACTOR)['targets'][0];candidate,_=patch_allocated_waits(waits,candidate,allocations,[dict(draft_id='npc-a',donor_entity_id=ACTOR,entries={wait['semantic_id']:dict(duration_ticks=11)})])
                if target['mnemonic']=='NPC_RUN':
                    movement=MovementAuthoringContext(context._source);move=movement.options(ACTOR)['targets'][0];candidate,_=patch_allocated_movement(movement,candidate,allocations,[dict(draft_id='npc-a',donor_entity_id=ACTOR,entries={move['semantic_id']:dict(x=128,z=192,move_id=10)})])
                requests=[dict(draft_id=name,donor_entity_id=ACTOR,entries={target['semantic_id']:dict(sector=value)}) for name,value in [('npc-a',sector),('npc-b',7)]]
                result,audit=patch_allocated_facing(context,candidate,allocations,requests);touched={r['decoded_byte_offset'] for r in audit['changes']};self.assertEqual(touched,{i for i,(a,b) in enumerate(zip(candidate,result)) if a!=b});self.assertEqual(read_man_layout(result),read_man_layout(candidate));self.assertTrue(all(a==b for i,(a,b) in enumerate(zip(candidate,result)) if i not in touched))
                for row in audit['changes']:
                    self.assertEqual(row['before_byte']&240,row['after_byte']&240);self.assertEqual(row['after_byte']&15,sector if row['draft_id']=='npc-a' else 7);self.assertNotEqual(row['source_decoded_byte_offset'],row['decoded_byte_offset'])
                self.assertFalse(audit['gameplay_verified']);self.assertFalse(audit['npc_placement_changed'])
                self.assertEqual(audit['runtime_dispatch'],'not_asserted')
                with self.assertRaises((ProjectError,ImportError)):patch_allocated_facing(context,result,allocations,requests)

    def test_noop_stale_owners_headers_flags_modes_aliases_and_parked_targets_reject(self):
        context,candidate,allocations,target=self.fixture(b'\xcc\xf8\x51\0\x80\xb3\x09');request=dict(draft_id='npc-a',donor_entity_id=ACTOR,entries={target['semantic_id']:dict(sector=3)})
        result,audit=patch_allocated_facing(context,candidate,allocations,[request]);self.assertEqual(result,candidate);self.assertFalse(audit['changes'])
        record=next(r for r in read_man_layout(candidate)['records'] if r['partition']==1 and r['record_index']==allocations['drafts'][0]['record_index']);source_offset,_,_=context._source.verified_record(ACTOR);at=record['byte_offset']+target['decoded_byte_offset']-source_offset
        for offset,mask in ((at,1),(at,16),(record['byte_offset']+target['pc'],1),(record['byte_offset']+target['pc']+1,1)):
            stale=bytearray(candidate);stale[offset]^=mask
            with self.assertRaises((ProjectError,ImportError)):patch_allocated_facing(context,bytes(stale),allocations,[request])
        for values in (dict(sector=True),dict(sector=8),dict(sector=-1),dict(sector=1,flags=0),dict(x=128)):
            with self.assertRaises((ProjectError,ImportError)):patch_allocated_facing(context,candidate,allocations,[dict(request,entries={target['semantic_id']:values})])
        with self.assertRaises(ProjectError):patch_allocated_facing(context,candidate,allocations,[request,request])
        with self.assertRaises((ProjectError,ImportError)):patch_allocated_facing(context,candidate,allocations,[dict(request,donor_entity_id=ACTOR.replace('0001','0000'))])
        for changes in ({'record_index':1},{'record_index':allocations['drafts'][1]['record_index']},{'byte_length':1},{'donor':{'record_index':0}}):
            bad=deepcopy(allocations);bad['drafts'][0].update(changes)
            # A different valid appended index is rejected when both owners name it.
            requests=[request,dict(request,draft_id='npc-b')]
            with self.assertRaises((ProjectError,ImportError)):patch_allocated_facing(context,candidate,bad,requests)
        movement=MovementAuthoringContext(context._source);move=movement.options(ACTOR)['targets'][0];parked,_=patch_allocated_movement(movement,candidate,allocations,[dict(draft_id='npc-a',donor_entity_id=ACTOR,entries={move['semantic_id']:dict(x=16384,z=16384)})])
        with self.assertRaises((ProjectError,ImportError)):patch_allocated_facing(context,parked,allocations,[request])
        cam,raw,rows,face=self.fixture(b'\x38\xa3\x80');record=next(r for r in read_man_layout(raw)['records'] if r['partition']==1 and r['record_index']==rows['drafts'][0]['record_index']);mode=record['byte_offset']+face['decoded_byte_offset']-cam._source.verified_record(ACTOR)[0]+1;changed=bytearray(raw);changed[mode]=0
        with self.assertRaises(ProjectError):patch_allocated_facing(cam,bytes(changed),rows,[dict(draft_id='npc-a',donor_entity_id=ACTOR,entries={face['semantic_id']:dict(sector=0)})])

    def test_unsupported_source_modes_slots_stopped_paths_and_record_aliases_reject(self):
        for script in (b'\x38\xa3\x01',b'\x38\xa8\0',b'\x4c\x51\xff\xff\xb3\x09',b'\x38\xa3\0\x7f'):
            source,candidate=fixture(script+END);candidate,row=append_actor_donor(candidate,sha256(candidate).hexdigest(),1);context=FacingAuthoringContext(source);entry=source.verified_record(ACTOR)[2];request=dict(draft_id='npc-a',donor_entity_id=ACTOR,entries={f'script://{ACTOR.removeprefix("scene://")}/facing/{entry:04x}':dict(sector=0)})
            before=candidate
            with self.assertRaises((ProjectError,ImportError)):patch_allocated_facing(context,candidate,{'drafts':[dict(row,draft_id='npc-a')]},[request])
            self.assertEqual(candidate,before)
        context,candidate,allocations,target=self.fixture(b'\x38\xa3\0');alias=bytearray(candidate)
        # P0 has one record, so P1 index N occupies table slot 1+N.
        first=0x2b+3*(1+allocations['drafts'][0]['record_index']);second=0x2b+3*(1+allocations['drafts'][1]['record_index']);alias[second:second+3]=alias[first:first+3]
        request=dict(draft_id='npc-a',donor_entity_id=ACTOR,entries={target['semantic_id']:dict(sector=0)})
        with self.assertRaises((ProjectError,ImportError)):patch_allocated_facing(context,bytes(alias),allocations,[request])
