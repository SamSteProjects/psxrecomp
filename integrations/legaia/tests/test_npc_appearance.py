"""Native NPC appearance is independent of its script donor and text bytes."""
from copy import deepcopy
from hashlib import sha256
from unittest import TestCase
from importer.core import parse_man, ImportError
from importer.man_actor_structure import append_actor_donor
from sdk.npc_appearance import patch_allocated_appearance
from sdk.project import ProjectError
from test_importer_man_assignments import fixture

class NpcAppearanceTests(TestCase):
    def test_final_offsets_two_clones_and_only_initial_header_bytes_change(self):
        context,source=fixture();candidate=source;allocations={'drafts':[]}
        for identifier in ['npc-a','npc-b']:
            candidate,row=append_actor_donor(candidate,sha256(candidate).hexdigest(),1)
            allocations['drafts'].append(dict(row,draft_id=identifier))
        original=bytes(candidate)
        requests=[dict(draft_id='npc-a',appearance_donor_record_index=2)]
        result,audit=patch_allocated_appearance(context,candidate,allocations,requests)
        changed={i for i,(a,b) in enumerate(zip(original,result)) if a!=b}
        self.assertEqual(changed,{r['decoded_byte_offset'] for r in audit['changes']});self.assertEqual(len(changed),2)
        actors={a.record_index:a for a in parse_man(result).actors};target=actors[allocations['drafts'][0]['record_index']]
        self.assertEqual((target.model_index,target.animation_id),(5,2))
        other=actors[allocations['drafts'][1]['record_index']];self.assertEqual((other.model_index,other.animation_id),(4,1))
        offset=target.byte_offset+1+target.local_count*2
        self.assertEqual(original[:offset],result[:offset]);self.assertEqual(original[offset+2:],result[offset+2:])
        # The first allocation's recorded intermediate offset is deliberately stale.
        self.assertNotEqual(target.byte_offset,allocations['drafts'][0]['byte_offset'])
        self.assertEqual(candidate,original);self.assertFalse(audit['gameplay_verified'])
        with self.assertRaisesRegex(ProjectError,'preimage'):patch_allocated_appearance(context,result,allocations,requests)

    def test_wrong_record_donor_alias_shape_and_pair_reject(self):
        context,source=fixture();candidate,row=append_actor_donor(source,sha256(source).hexdigest(),1)
        allocations={'drafts':[dict(row,draft_id='npc')]};request=dict(draft_id='npc',appearance_donor_record_index=2)
        for requests in [[{**request,'payload':'native'}],[{**request,'appearance_donor_record_index':True}],[{**request,'appearance_donor_record_index':99}],[request,request]]:
            with self.assertRaises(ProjectError):patch_allocated_appearance(context,candidate,allocations,requests)
        for mutate in [lambda r:r.update(record_index=1),lambda r:r.update(byte_length=1),lambda r:r['donor'].update(record_index=99)]:
            bad=deepcopy(allocations);mutate(bad['drafts'][0])
            with self.assertRaises(ProjectError):patch_allocated_appearance(context,candidate,bad,[request])
        from importer.man_layout import read_man_layout
        layout=read_man_layout(candidate);alias=bytearray(candidate)
        count0=layout['partition_counts'][0];table=0x2b+3*(count0+row['record_index']);original_table=0x2b+3*(count0+1)
        alias[table:table+3]=alias[original_table:original_table+3]
        with self.assertRaises((ProjectError,ImportError)):patch_allocated_appearance(context,bytes(alias),allocations,[request])
        incompatible,raw=fixture(bones=(2,3));clone,new=append_actor_donor(raw,sha256(raw).hexdigest(),1)
        with self.assertRaises((ProjectError,ImportError)):patch_allocated_appearance(incompatible,clone,{'drafts':[dict(new,draft_id='npc')]},[request])
        unchanged,audit=patch_allocated_appearance(context,candidate,allocations,[{**request,'appearance_donor_record_index':1}])
        self.assertEqual(unchanged,candidate);self.assertEqual(audit['changes'],[])
