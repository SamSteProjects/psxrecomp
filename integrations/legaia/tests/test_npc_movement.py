"""NPC movement operands preserve final ownership and all other candidate bytes."""
from copy import deepcopy
from hashlib import sha256
from unittest import TestCase
from importer.core import ImportError
from importer.man_actor_structure import append_actor_donor
from importer.man_layout import read_man_layout
from importer.movement_authoring import MovementAuthoringContext
from importer.wait_authoring import WaitAuthoringContext
from sdk.npc_movement import patch_allocated_movement
from sdk.npc_waits import patch_allocated_waits
from sdk.project import ProjectError
from test_importer_dialogue_authoring import fixture, ACTOR
from test_wait_authoring import END


class NpcMovementTests(TestCase):
    def candidate(self,instruction):
        source,man=fixture(instruction+b'\x4a\x0a\0'+END)
        context=MovementAuthoringContext(source);target=context.options(ACTOR)['targets'][0]
        candidate,allocations=man,{'drafts':[]}
        for name in ('npc-a','npc-b'):
            candidate,row=append_actor_donor(candidate,sha256(candidate).hexdigest(),1)
            allocations['drafts'].append(dict(row,draft_id=name))
        return context,source,candidate,allocations,target

    def test_instruction_families_contexts_two_clones_final_offsets_and_wait_composition(self):
        for instruction,values in [(b'\x23\0\x80',{'x':128,'z':16384}), (b'\xa3\x07\0\x80',{'x':128}),
                                   (b'\x4c\x51\0\x80\xab\x09',{'x':128,'z':192,'move_id':10}),
                                   (b'\xcc\x07\x51\0\x80\xab\x09',{'move_id':10}),
                                   (b'\x22\x09',{'move_id':10}), (b'\xa2\x07\x09',{'move_id':10})]:
            context,source,candidate,allocations,target=self.candidate(instruction)
            waits=WaitAuthoringContext(source);wait=waits.options(ACTOR)['targets'][0]
            candidate,wait_audit=patch_allocated_waits(waits,candidate,allocations,[dict(draft_id='npc-a',donor_entity_id=ACTOR,entries={wait['semantic_id']:{'duration_ticks':11}})])
            requests=[dict(draft_id=name,donor_entity_id=ACTOR,entries={target['semantic_id']:values}) for name in ('npc-a','npc-b')]
            result,audit=patch_allocated_movement(context,candidate,allocations,requests)
            self.assertEqual(read_man_layout(result),read_man_layout(candidate));self.assertEqual(len(audit['changes']),len(values)*2)
            touched={r['decoded_byte_offset'] for r in audit['changes']};self.assertEqual(touched,{i for i,(a,b) in enumerate(zip(result,candidate)) if a!=b})
            self.assertTrue(all(a==b for i,(a,b) in enumerate(zip(result,candidate)) if i not in touched))
            at=wait_audit['changes'][0]['decoded_byte_offset'];self.assertEqual(result[at:at+2],b'\x0b\0')
            records={(r['partition'],r['record_index']):r for r in read_man_layout(result)['records']}
            self.assertNotEqual(records[(1,allocations['drafts'][0]['record_index'])]['byte_offset'],allocations['drafts'][0]['byte_offset'])
            for row in audit['changes']:self.assertEqual(row['decoded_byte_offset'],records[(1,row['record_index'])]['byte_offset']+row['record_relative_byte_offset'])
            with self.assertRaises((ProjectError,ImportError)):patch_allocated_movement(context,result,allocations,requests)
            unchanged,no_op=patch_allocated_movement(context,candidate,allocations,[dict(requests[0],entries={target['semantic_id']:target['values']})])
            self.assertEqual(unchanged,candidate);self.assertEqual(no_op['changes'],[])

    def test_fields_ownership_aliases_stopped_paths_and_preimages_reject(self):
        context,_,candidate,allocations,target=self.candidate(b'\x23\0\x80')
        request=dict(draft_id='npc-a',donor_entity_id=ACTOR,entries={target['semantic_id']:{'x':128}})
        for values in ({'x':True},{'x':32},{'x':-64},{'x':16448},{'y':0},{'move_id':1}):
            with self.assertRaises((ProjectError,ImportError)):patch_allocated_movement(context,candidate,allocations,[dict(request,entries={target['semantic_id']:values})])
        with self.assertRaises(ProjectError):patch_allocated_movement(context,candidate,allocations,[request,request])
        with self.assertRaises((ProjectError,ImportError)):patch_allocated_movement(context,candidate,allocations,[dict(request,donor_entity_id=ACTOR.replace('0001','0000'))])
        for change in [dict(record_index=1),dict(byte_length=1),dict(donor={'record_index':0})]:
            bad=deepcopy(allocations);bad['drafts'][0].update(change)
            with self.assertRaises((ProjectError,ImportError)):patch_allocated_movement(context,candidate,bad,[request])
        layout=read_man_layout(candidate);alias=bytearray(candidate);count=layout['partition_counts'][0];at=0x2b+3*(count+allocations['drafts'][0]['record_index']);original=0x2b+3*(count+1);alias[at:at+3]=alias[original:original+3]
        with self.assertRaises((ProjectError,ImportError)):patch_allocated_movement(context,bytes(alias),allocations,[request])
        source,man=fixture(b'\x23\0\x80\xff');unsupported=MovementAuthoringContext(source);clone,row=append_actor_donor(man,sha256(man).hexdigest(),1)
        with self.assertRaises((ProjectError,ImportError)):patch_allocated_movement(unsupported,clone,{'drafts':[dict(row,draft_id='npc-a')]},[request])
