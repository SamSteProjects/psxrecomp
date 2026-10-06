"""Independent NPC selector words preserve imported and composed bytes."""
from copy import deepcopy
from hashlib import sha256
import unittest
from importer.core import ImportError as NativeError
from importer.man_actor_structure import append_actor_donor
from importer.man_layout import read_man_layout
from importer.model_selector_authoring import ModelSelectorAuthoringContext
from importer.wait_authoring import WaitAuthoringContext
from sdk.npc_model_selectors import patch_allocated_model_selectors
from sdk.npc_waits import patch_allocated_waits
from sdk.project import ProjectError
from test_importer_dialogue_authoring import fixture,ACTOR
from test_model_selector_authoring import END

class NpcModelSelectorTests(unittest.TestCase):
    def fixture(self,extended=False):
        source,candidate=fixture((b'\xcc\x07\x50' if extended else b'\x4c\x50')+b'\xef\0\x4a\x0a\0'+END)
        context=ModelSelectorAuthoringContext(source);allocations={'drafts':[]}
        for id in ('npc-a','npc-b'):
            candidate,row=append_actor_donor(candidate,sha256(candidate).hexdigest(),1);allocations['drafts'].append(dict(row,draft_id=id))
        target=context.options(ACTOR)['targets'][0]
        return context,candidate,allocations,target

    def test_signed_words_final_offsets_two_clones_and_retained_wait(self):
        for extended in (False,True):
            for a,b in ((-32768,32767),(-1,240),(0,239)):
                context,candidate,allocations,target=self.fixture(extended)
                waits=WaitAuthoringContext(context._source);wait=waits.options(ACTOR)['targets'][0]
                candidate,wait_audit=patch_allocated_waits(waits,candidate,allocations,[dict(draft_id=id,donor_entity_id=ACTOR,entries={wait['semantic_id']:dict(duration_ticks=value)}) for id,value in [('npc-a',11),('npc-b',22)]])
                requests=[dict(draft_id=id,donor_entity_id=ACTOR,entries={target['semantic_id']:dict(model_selector_signed=value)}) for id,value in [('npc-a',a),('npc-b',b)]]
                result,audit=patch_allocated_model_selectors(context,candidate,allocations,requests);self.assertEqual(read_man_layout(result),read_man_layout(candidate));allowed=set()
                for row,value in zip(audit['changes'],[a,b]):
                    at=row['decoded_byte_offset'];self.assertEqual(int.from_bytes(result[at:at+2],'little',signed=True),value);self.assertNotEqual(at,row['source_decoded_byte_offset']);self.assertEqual(row['target_context'],7 if extended else None);allowed.update(range(at,at+2))
                self.assertTrue(all(x==y for i,(x,y) in enumerate(zip(candidate,result)) if i not in allowed))
                for row in wait_audit['changes']:
                    at=row['decoded_byte_offset'];self.assertEqual(result[at:at+2],candidate[at:at+2])
                self.assertFalse(audit['gameplay_verified'])
                noop,_=patch_allocated_model_selectors(context,candidate,allocations,[dict(requests[0],entries={target['semantic_id']:dict(model_selector_signed=239)})]);self.assertEqual(noop,candidate)

    def test_typed_source_ownership_allocation_and_noop_preimages(self):
        context,candidate,allocations,target=self.fixture(True);id=target['semantic_id'];request=dict(draft_id='npc-a',donor_entity_id=ACTOR,entries={id:dict(model_selector_signed=240)})
        for fields in (dict(model_selector_signed=True),dict(model_selector_signed=-32769),dict(model_selector_signed=32768),dict(model_selector_signed=1.5),dict(model_selector_signed=0,asset_id='invented')):
            with self.assertRaises((ProjectError,NativeError)):patch_allocated_model_selectors(context,candidate,allocations,[dict(request,entries={id:fields})])
        for altered in ([request,request],[dict(request,donor_entity_id=ACTOR[:-4]+'0000')],[dict(request,entries={id[:-4]+'ffff':dict(model_selector_signed=0)})]):
            with self.assertRaises((ProjectError,NativeError)):patch_allocated_model_selectors(context,candidate,allocations,altered)
        layout=read_man_layout(candidate);record=next(r for r in layout['records'] if r['partition']==1 and r['record_index']==allocations['drafts'][0]['record_index']);start=record['byte_offset'];relative=target['decoded_byte_offset']-context._source.verified_record(ACTOR)[0]
        for at in range(target['pc'],relative+2):
            forged=bytearray(candidate);forged[start+at]^=1
            for value in (239,240):
                with self.assertRaises((ProjectError,NativeError)):patch_allocated_model_selectors(context,bytes(forged),allocations,[dict(request,entries={id:dict(model_selector_signed=value)})])
        forged=deepcopy(allocations);forged['drafts'][0]['record_index']=1
        with self.assertRaises(ProjectError):patch_allocated_model_selectors(context,candidate,forged,[request])
        source,_=fixture(b'\x4c\x50\xef\0\xff');self.assertFalse(ModelSelectorAuthoringContext(source).options(ACTOR)['supported'])

if __name__=='__main__':unittest.main()
