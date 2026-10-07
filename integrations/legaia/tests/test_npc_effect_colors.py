"""NPC color spans follow final allocations and retain donor/dispatch bytes."""
from copy import deepcopy
from hashlib import sha256
import struct,unittest
from importer.core import ImportError
from importer.effect_color_authoring import EffectColorAuthoringContext
from importer.man_actor_structure import append_actor_donor
from importer.man_layout import read_man_layout
from sdk.npc_effect_colors import patch_allocated_effect_colors
from sdk.npc_script_compare import authored_spans
from sdk.project import ProjectError
from test_importer_dialogue_authoring import fixture,ACTOR
from test_effect_color_authoring import END

class NpcEffectColorTests(unittest.TestCase):
    def candidate(self,header):
        source,man=fixture(header+b'\x0f'+struct.pack('<BBBh',1,2,3,4)+END)
        context=EffectColorAuthoringContext(source);target=context.options(ACTOR)['targets'][0];candidate=man;allocations={'drafts':[]}
        for name in ['npc-a','npc-b']:
            candidate,row=append_actor_donor(candidate,sha256(candidate).hexdigest(),1);allocations['drafts'].append(dict(row,draft_id=name))
        return context,candidate,allocations,target

    def test_independent_clones_rebase_and_noop_dispatch(self):
        for header in (b'\x34',b'\xb4\x07'):
            c,base,allocations,target=self.candidate(header);values=[dict(red=255,green=0,blue=1,intensity=-32768),dict(red=0,green=128,blue=255,intensity=32767)]
            requests=[dict(draft_id=name,donor_entity_id=ACTOR,entries={target['semantic_id']:v}) for name,v in zip(['npc-a','npc-b'],values)]
            result,audit=patch_allocated_effect_colors(c,base,allocations,requests);self.assertEqual(read_man_layout(result),read_man_layout(base));self.assertEqual(len(audit['changes']),2);touched=set()
            for change,v in zip(audit['changes'],values):
                at=change['decoded_byte_offset'];touched.update(range(at,at+5));self.assertEqual(result[at:at+5],struct.pack('<BBBh',v['red'],v['green'],v['blue'],v['intensity']))
            self.assertTrue(all(a==b for i,(a,b) in enumerate(zip(base,result)) if i not in touched))
            self.assertNotEqual(audit['changes'][0]['decoded_byte_offset'],allocations['drafts'][0]['byte_offset']+target['pc']+len(header)+1)
            with self.assertRaises(ProjectError):patch_allocated_effect_colors(c,result,allocations,requests)
            noop=dict(requests[0],entries={target['semantic_id']:target['values']});same,proof=patch_allocated_effect_colors(c,base,allocations,[noop]);self.assertEqual(same,base);self.assertEqual(proof['changes'],[])
            bad=bytearray(base);bad[audit['changes'][0]['decoded_byte_offset']-1]^=0x10
            with self.assertRaises((ProjectError,ImportError)):patch_allocated_effect_colors(c,bytes(bad),allocations,[noop])

    def test_ownership_invalid_values_and_candidate_preimage(self):
        c,base,allocations,target=self.candidate(b'\x34');request=dict(draft_id='npc-a',donor_entity_id=ACTOR,entries={target['semantic_id']:dict(red=4,green=5,blue=6,intensity=-1)})
        for mutate in [dict(draft_id='missing'),dict(donor_entity_id=ACTOR.replace('0001','0000')),dict(entries={target['semantic_id']:dict(red=True,green=5,blue=6,intensity=1)}),dict(entries={target['semantic_id']:dict(red=1,green=2,blue=3,intensity=32768)}),dict(extra=0)]:
            with self.assertRaises((ProjectError,ImportError)):patch_allocated_effect_colors(c,base,allocations,[dict(request,**mutate)])
        for mutate in [dict(record_index=1),dict(byte_length=1),dict(donor={'record_index':0})]:
            bad=deepcopy(allocations);bad['drafts'][0].update(mutate)
            with self.assertRaises(ProjectError):patch_allocated_effect_colors(c,base,bad,[request])
        with self.assertRaises(ProjectError):patch_allocated_effect_colors(c,base,allocations,[request,request])
        result,audit=patch_allocated_effect_colors(c,base,allocations,[request]);bad=bytearray(base);bad[audit['changes'][0]['decoded_byte_offset']]=99
        with self.assertRaises(ProjectError):patch_allocated_effect_colors(c,bytes(bad),allocations,[request])

    def test_native_comparison_requires_source_qualified_color_span(self):
        c,base,allocations,target=self.candidate(b'\xb4\x07');v=dict(red=12,green=34,blue=56,intensity=-1234);result,audit=patch_allocated_effect_colors(c,base,allocations,[dict(draft_id='npc-a',donor_entity_id=ACTOR,entries={target['semantic_id']:v})]);offset,raw,entry=c._source.verified_record(ACTOR);final=next(r for r in read_man_layout(result)['records'] if r['partition']==1 and r['record_index']==allocations['drafts'][0]['record_index']);start=final['byte_offset'];made=result[start:start+final['byte_length']]
        record=lambda data,at,index:dict(raw_hex=data.hex(),script_offset=entry,byte_length=len(data),byte_offset=at,record_index=index)
        retail=record(raw,offset,1);generated=record(made,start,final['record_index']);draft=dict(donor_entity_id=ACTOR,effect_colors=dict(donor_entity_id=ACTOR,entries={target['semantic_id']:v}));metadata={'npc_effect_colors_changes':audit};spans=authored_spans(metadata,'npc-a',retail,generated,draft);self.assertEqual(len(spans),1);self.assertEqual(spans[0]['category'],'own_effect_color');self.assertEqual(spans[0]['byte_length'],5)
        for change in [dict(byte_length=4),dict(target_context=8),dict(after_hex='0000000000'),dict(pc=0),dict(effect_color_id=target['semantic_id'].replace('0001','0000'))]:
            bad=deepcopy(metadata);bad['npc_effect_colors_changes']['changes'][0].update(change)
            with self.assertRaises(ProjectError):authored_spans(bad,'npc-a',retail,generated,draft)

if __name__=='__main__':unittest.main()
