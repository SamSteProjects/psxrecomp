"""Final NPC branch ownership retains source boundaries and unrelated operands."""
from copy import deepcopy
from hashlib import sha256
from unittest import TestCase
from importer.branch_authoring import BranchAuthoringContext
from importer.core import ImportError as NativeError
from importer.man_actor_structure import append_actor_donor
from importer.man_layout import read_man_layout
from sdk.npc_branches import patch_allocated_branches
from sdk.project import ProjectError
from test_importer_dialogue_authoring import fixture,ACTOR
from test_branch_authoring import family_script

class NpcBranchesTests(TestCase):
    def fixture(self,script):
        source,candidate=fixture(script);context=BranchAuthoringContext(source);allocations={'drafts':[]}
        for id in ('npc-a','npc-b'):
            candidate,row=append_actor_donor(candidate,sha256(candidate).hexdigest(),1);allocations['drafts'].append(dict(row,draft_id=id))
        return context,candidate,allocations

    def test_family_words_final_offsets_two_independent_clones_and_exact_byte_budget(self):
        for family in ('JMP_REL','COND_JMP','BBOX_TEST','FLAG_WORD_BRANCH','SYSFLAG_TEST'):
            for extended in (False,True):
                if family=='SYSFLAG_TEST' and extended:continue
                script,operand,target,closing=family_script(family,extended);context,candidate,allocations=self.fixture(script);branch=context.options(ACTOR)['targets'][0];id=branch['semantic_id']
                requests=[dict(draft_id=name,donor_entity_id=ACTOR,entries={id:dict(target_pc=value)}) for name,value in [('npc-a',5),('npc-b',closing)]]
                result,audit=patch_allocated_branches(context,candidate,allocations,requests);self.assertEqual(read_man_layout(result),read_man_layout(candidate));self.assertEqual(len(audit['changes']),2)
                allowed=set()
                for row,value in zip(audit['changes'],[5,closing]):
                    at=row['decoded_byte_offset'];self.assertEqual((operand+int.from_bytes(result[at:at+2],'little'))&65535,value);self.assertEqual(row['after_target_pc'],value);allowed.update(range(at,at+2));self.assertNotEqual(at,row['source_decoded_byte_offset'])
                    for byte in row['changed_bytes']:self.assertEqual(result[byte['decoded_byte_offset']],byte['after_byte'])
                self.assertTrue(all(a==b for i,(a,b) in enumerate(zip(candidate,result)) if i not in allowed));self.assertFalse(audit['gameplay_verified'])
                with self.assertRaises((ProjectError,NativeError)):patch_allocated_branches(context,result,allocations,requests)
                noop,_=patch_allocated_branches(context,candidate,allocations,[dict(draft_id='npc-a',donor_entity_id=ACTOR,entries={id:dict(target_pc=target)})]);self.assertEqual(noop,candidate)

    def test_invalid_types_foreign_owners_preimages_and_opaque_boundaries_reject(self):
        script,operand,target,closing=family_script('COND_JMP',True);context,candidate,allocations=self.fixture(script);branch=context.options(ACTOR)['targets'][0];id=branch['semantic_id'];request=dict(draft_id='npc-a',donor_entity_id=ACTOR,entries={id:dict(target_pc=5)})
        for value in (True,-1,32768,6):
            with self.assertRaises((ProjectError,NativeError)):patch_allocated_branches(context,candidate,allocations,[dict(request,entries={id:dict(target_pc=value)})])
        for bad in (dict(request,draft_id='missing'),dict(request,donor_entity_id='wrong'),dict(request,entries={id.replace('0001','0002'):dict(target_pc=5)})):
            with self.assertRaises((ProjectError,NativeError)):patch_allocated_branches(context,candidate,allocations,[bad])
        with self.assertRaises(ProjectError):patch_allocated_branches(context,candidate,allocations,[request,request])
        final=next(r for r in read_man_layout(candidate)['records'] if r['partition']==1 and r['record_index']==allocations['drafts'][0]['record_index']);start=final['byte_offset']
        for relative in (5,6,7,operand):
            changed=bytearray(candidate);changed[start+relative]^=32
            with self.assertRaises((ProjectError,NativeError)):patch_allocated_branches(context,bytes(changed),allocations,[request])
        bad=deepcopy(allocations);bad['drafts'][0]['record_index']=1
        with self.assertRaises(ProjectError):patch_allocated_branches(context,candidate,bad,[request])
