"""NPC-owned text survives history and patches only allocated record spans."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from test_project_workflow import synthetic_scene
from test_importer_dialogue_authoring import fixture, ACTOR
from sdk.project import ProjectService
from sdk.npc_dialogue import source, review, patch_clones
from importer.man_actor_structure import append_actor_donor
from importer.core import ImportError
from importer.man_layout import read_man_layout
from hashlib import sha256

class NpcDialogueTests(TestCase):
    def test_history_persistence_review_freshness_and_donor_ownership(self):
        context,_=fixture()
        with TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.import_metadata(synthetic_scene())
            p.command(dict(type='create_actor_draft',donor_entity_id=ACTOR,position=dict(x=128,z=256),name='Resident'))
            identifier=next(iter(p.actor_drafts));original=deepcopy(p.actor_drafts)
            with patch.object(p,'_dialogue_context',return_value=context):
                before=len(p.undo_stack);report=source(p,identifier);run=report['options']['runs'][0]['semantic_id']
                request=dict(entity_id=identifier,runs={run:'Yo'});proposal=review(p,request)
                self.assertEqual(len(p.undo_stack),before);self.assertEqual(p.actor_drafts,original)
                with self.assertRaises(ValueError):p.command(dict(type='set_actor_draft_dialogue',**request,review_key='0'*64))
                p.command(dict(type='set_actor_draft_dialogue',**request,review_key=proposal['review_key']))
                self.assertEqual(source(p,identifier)['options']['runs'][0]['effective_text'],'Yo   ')
                authored=deepcopy(p.actor_drafts);self.assertEqual(len(p.undo_stack),before+1)
                p.undo();self.assertEqual(p.actor_drafts,original);p.redo();self.assertEqual(p.actor_drafts,authored)
                self.assertEqual(ProjectService.open(p.save()).actor_drafts,authored)
                for runs in ({run:'Too long'}, {run:'|'}, {run.replace('0001','0000'):'OK'}):
                    with self.assertRaises((ValueError,ImportError)):review(p,dict(entity_id=identifier,runs=runs))
                reset=review(p,dict(entity_id=identifier,runs={}))
                p.command(dict(type='set_actor_draft_dialogue',entity_id=identifier,runs={},review_key=reset['review_key']))
                self.assertEqual(p.actor_drafts,original);p.undo();self.assertEqual(p.actor_drafts,authored)
                bad=deepcopy(authored[identifier]);bad['dialogue']['donor_entity_id']='scene://fixture/actors/man-p1/0000'
                with self.assertRaises(ValueError):p._validate_actor_draft(identifier,bad)
                self.assertEqual(p.imports['scene://fixture'],synthetic_scene())

    def test_two_clones_independent_equal_span_and_original_bytes_preserved(self):
        context,man=fixture();run=context.options(ACTOR)['runs'][0]['semantic_id']
        with TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.import_metadata(synthetic_scene())
            for name in ['A','B']:p.command(dict(type='create_actor_draft',donor_entity_id=ACTOR,position=dict(x=128,z=256),name=name))
            ids=sorted(p.actor_drafts)
            for identifier,text in zip(ids,['First','Next']):p.actor_drafts[identifier]['dialogue']=dict(donor_entity_id=ACTOR,runs={run:text})
            candidate=man;allocation={'drafts':[]}
            for identifier in ids:
                candidate,row=append_actor_donor(candidate,sha256(candidate).hexdigest(),1)
                allocation['drafts'].append(dict(row,draft_id=identifier))
            result,audit=patch_clones(p,'scene://fixture',context,candidate,allocation)
            self.assertEqual(read_man_layout(result),read_man_layout(candidate));self.assertEqual(len(audit['changes']),2)
            touched=set()
            for row,text in zip(audit['changes'],['First','Next ']):
                start=row['decoded_byte_offset'];size=row['byte_length'];self.assertEqual(result[start:start+size],text.encode())
                touched.update(range(start,start+size))
            self.assertTrue(all(a==b for i,(a,b) in enumerate(zip(result,candidate)) if i not in touched))
            original=read_man_layout(result)['records'];span=next(r for r in original if r['partition']==1 and r['record_index']==1)
            old=context.verified_record(ACTOR)[1];self.assertEqual(result[span['byte_offset']:span['byte_offset']+span['byte_length']],old)
            tampered=bytearray(candidate);tampered[audit['changes'][0]['decoded_byte_offset']]=0
            with self.assertRaises(ValueError):patch_clones(p,'scene://fixture',context,bytes(tampered),allocation)
