"""Final-clone flag ownership, preserved upper bits and unsupported side effects."""
from copy import deepcopy
from hashlib import sha256
from unittest import TestCase
from importer.core import ImportError as NativeError
from importer.flag_authoring import FlagAuthoringContext
from importer.man_actor_structure import append_actor_donor
from importer.man_layout import read_man_layout
from sdk.npc_flags import patch_allocated_flags
from sdk.project import ProjectError
from test_importer_dialogue_authoring import fixture,ACTOR
from test_wait_authoring import END

class NpcFlagsTests(TestCase):
    def fixture(self,instruction):
        source,candidate=fixture(instruction+END);context=FlagAuthoringContext(source);allocations={'drafts':[]}
        for id in ('npc-a','npc-b'):
            candidate,row=append_actor_donor(candidate,sha256(candidate).hexdigest(),1);allocations['drafts'].append(dict(row,draft_id=id))
        return context,candidate,allocations

    def test_all_supported_banks_ops_and_extended_targets_change_only_owned_bits(self):
        for opcode in range(0x2b,0x34):
            for extended in (False,True):
                instruction=bytes([opcode|(0x80 if extended else 0)])+(b'\x07' if extended else b'')+b'\xe2'
                context,candidate,allocations=self.fixture(instruction);target=context.options(ACTOR)['targets'][0];request=lambda id,bit:dict(draft_id=id,donor_entity_id=ACTOR,entries={target['semantic_id']:dict(bit=bit)})
                result,audit=patch_allocated_flags(context,candidate,allocations,[request('npc-a',3),request('npc-b',4)])
                changed=[i for i,(a,b) in enumerate(zip(candidate,result)) if a!=b];self.assertEqual(changed,sorted(r['decoded_byte_offset'] for r in audit['changes']));self.assertEqual(len(changed),2);self.assertEqual(read_man_layout(result),read_man_layout(candidate))
                for row in audit['changes']:self.assertEqual(row['before_byte']&0xe0,row['after_byte']&0xe0)
                for bit in (2,3,4):
                    result,_=patch_allocated_flags(context,candidate,allocations,[request('npc-a',bit)]);self.assertEqual(len(result),len(candidate))

    def test_noop_preimages_unknown_owners_and_duplicate_allocations_reject(self):
        context,candidate,allocations=self.fixture(b'\xae\x07\xe2');target=context.options(ACTOR)['targets'][0];request=dict(draft_id='npc-a',donor_entity_id=ACTOR,entries={target['semantic_id']:dict(bit=2)})
        final=next(r for r in read_man_layout(candidate)['records'] if r['partition']==1 and r['record_index']==allocations['drafts'][0]['record_index']);source_at=context._source.verified_record(ACTOR)[0];at=final['byte_offset']+target['decoded_byte_offset']-source_at
        for offset in (at,at-1,at-2):
            forged=bytearray(candidate);forged[offset]^=0x20
            with self.assertRaises((ProjectError,NativeError)):patch_allocated_flags(context,bytes(forged),allocations,[request])
        for fields in (dict(bit=True),dict(bit=-1),dict(bit=32),dict(bit=1,flags=0)):
            bad=deepcopy(request);bad['entries'][target['semantic_id']]=fields
            with self.assertRaises((ProjectError,NativeError)):patch_allocated_flags(context,candidate,allocations,[bad])
        for bad in (dict(request,draft_id='missing'),dict(request,donor_entity_id=ACTOR.replace('0001','0002')),dict(request,entries={target['semantic_id'].replace('0001','0002'):dict(bit=3)})):
            with self.assertRaises((ProjectError,NativeError)):patch_allocated_flags(context,candidate,allocations,[bad])
        with self.assertRaises(ProjectError):patch_allocated_flags(context,candidate,allocations,[request,request])
        bad=deepcopy(allocations);bad['drafts'][0]['record_index']=1
        with self.assertRaises(ProjectError):patch_allocated_flags(context,candidate,bad,[request])
        bad=deepcopy(allocations);bad['drafts'][0]['byte_length']+=1
        with self.assertRaises(ProjectError):patch_allocated_flags(context,candidate,bad,[request])

    def test_unsupported_width_side_effects_and_stopped_paths_reject(self):
        for instruction in (b'\x2b\xf0',b'\x31\xe8',b'\x32\xea',b'\x2e\xe2\x7f'):
            context,candidate,allocations=self.fixture(instruction);owner=ACTOR;entry=context._source.verified_record(owner)[2];request=dict(draft_id='npc-a',donor_entity_id=owner,entries={f'script://{owner.removeprefix("scene://")}/flag-bit/{entry:04x}':dict(bit=3)})
            with self.assertRaises((ProjectError,NativeError)):patch_allocated_flags(context,candidate,allocations,[request])
        for instruction,bit in ((b'\x2b\xe2',16),(b'\x31\xe2',8),(b'\x32\xe2',10)):
            context,candidate,allocations=self.fixture(instruction);target=context.options(ACTOR)['targets'][0]
            with self.assertRaises(NativeError):patch_allocated_flags(context,candidate,allocations,[dict(draft_id='npc-a',donor_entity_id=ACTOR,entries={target['semantic_id']:dict(bit=bit)})])
