"""NPC arrivals preserve names, source donors, dispatch and all other bytes."""
from copy import deepcopy
from hashlib import sha256
import unittest
from importer.core import ImportError as NativeError
from importer.man_actor_structure import append_actor_donor
from importer.man_layout import read_man_layout
from importer.transition_authoring import TransitionAuthoringContext
from importer.wait_authoring import WaitAuthoringContext
from sdk.npc_transitions import patch_allocated_transitions
from sdk.npc_waits import patch_allocated_waits
from sdk.project import ProjectError
from test_importer_dialogue_authoring import fixture,ACTOR

class NpcTransitionTests(unittest.TestCase):
    def fixture(self,extended=False):
        source,candidate=fixture(b'\x4a\x0a\0'+(b'\xbf\x07' if extended else b'\x3f')+b'\0\0\x06town01\1\2\xe3opaque')
        context=TransitionAuthoringContext(source);allocations={'drafts':[]}
        for id in ('npc-a','npc-b'):
            candidate,row=append_actor_donor(candidate,sha256(candidate).hexdigest(),1);allocations['drafts'].append(dict(row,draft_id=id))
        target=context.options(ACTOR)['transitions'][0]
        return context,candidate,allocations,target

    def test_independent_arrival_fields_final_offsets_and_retained_waits(self):
        for extended in (False,True):
            for a,b in ((dict(entry_x_encoded=0,entry_z_encoded=255,direction_encoded=0),dict(entry_x_encoded=255,entry_z_encoded=0,direction_encoded=255)),(dict(direction_encoded=7),dict(entry_z_encoded=128))):
                context,candidate,allocations,target=self.fixture(extended);waits=WaitAuthoringContext(context._source);wait=waits.options(ACTOR)['targets'][0];candidate,wait_audit=patch_allocated_waits(waits,candidate,allocations,[dict(draft_id=id,donor_entity_id=ACTOR,entries={wait['semantic_id']:dict(duration_ticks=value)}) for id,value in [('npc-a',11),('npc-b',22)]])
                requests=[dict(draft_id=id,donor_entity_id=ACTOR,entries={target['semantic_id']:fields}) for id,fields in [('npc-a',a),('npc-b',b)]];result,audit=patch_allocated_transitions(context,candidate,allocations,requests);self.assertEqual(read_man_layout(result),read_man_layout(candidate));allowed=set()
                for row in audit['changes']:
                    at=row['decoded_byte_offset'];self.assertEqual(result[at],row['after_byte']);self.assertNotEqual(at,row['source_decoded_byte_offset']);self.assertEqual(row['target_context'],7 if extended else None);self.assertEqual(row['destination'],'town01');allowed.add(at)
                self.assertTrue(all(x==y for i,(x,y) in enumerate(zip(candidate,result)) if i not in allowed))
                for row in wait_audit['changes']:
                    at=row['decoded_byte_offset'];self.assertEqual(result[at:at+2],candidate[at:at+2])
                self.assertFalse(audit['gameplay_verified']);noop,receipt=patch_allocated_transitions(context,candidate,allocations,[dict(requests[0],entries={target['semantic_id']:dict(entry_x_encoded=1)})]);self.assertEqual(noop,candidate);self.assertEqual(receipt['changes'],[])

    def test_typed_fields_foreign_allocation_and_complete_noop_preimages(self):
        context,candidate,allocations,target=self.fixture(True);id=target['semantic_id'];request=dict(draft_id='npc-a',donor_entity_id=ACTOR,entries={id:dict(direction_encoded=7)})
        for fields in ({},dict(direction_encoded=True),dict(entry_x_encoded=-1),dict(entry_z_encoded=256),dict(direction_encoded=1.5),dict(destination='town02'),dict(direction_encoded=7,world_x=64)):
            with self.assertRaises((ProjectError,NativeError)):patch_allocated_transitions(context,candidate,allocations,[dict(request,entries={id:fields})])
        for altered in ([request,request],[dict(request,donor_entity_id=ACTOR[:-4]+'0000')],[dict(request,entries={id[:-4]+'ffff':dict(direction_encoded=0)})]):
            with self.assertRaises((ProjectError,NativeError)):patch_allocated_transitions(context,candidate,allocations,altered)
        layout=read_man_layout(candidate);record=next(r for r in layout['records'] if r['partition']==1 and r['record_index']==allocations['drafts'][0]['record_index']);start=record['byte_offset'];relative=target['decoded_byte_offset']-context._source.verified_record(ACTOR)[0]
        for at in range(target['pc'],relative+3):
            forged=bytearray(candidate);forged[start+at]^=1
            for fields in (dict(direction_encoded=7),dict(entry_x_encoded=1)):
                with self.assertRaises((ProjectError,NativeError)):patch_allocated_transitions(context,bytes(forged),allocations,[dict(request,entries={id:fields})])
        forged=deepcopy(allocations);forged['drafts'][0]['record_index']=1
        with self.assertRaises(ProjectError):patch_allocated_transitions(context,candidate,forged,[request])
        source,_=fixture(b'\x3f\0\0\x06town01\1\2\3');bad=bytearray(source._man);offset,_,_=source.verified_record(ACTOR);bad[offset+9]=ord('!')
        from importer.dialogue_authoring import DialogueAuthoringContext
        from test_importer_dialogue_authoring import literals
        self.assertFalse(TransitionAuthoringContext(DialogueAuthoringContext('fixture',bytes(bad),literals(bytes(bad)),{})).options(ACTOR)['supported'])

if __name__=='__main__':unittest.main()
