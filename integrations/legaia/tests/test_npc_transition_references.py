"""Recorded clone arrival dependencies keep source and authored ownership distinct."""
from copy import deepcopy
import json, os
from pathlib import Path
import tempfile, unittest
from unittest.mock import patch
from sdk.asset_references import assemble, assemble_project, source_key
from sdk.resources import refresh_resource_catalog
from sdk.project import ProjectService, ProjectError
from sdk.npc_transitions import review
from importer.transition_authoring import TransitionAuthoringContext
import test_npc_transition_workflow as workflow


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'Private Retail disc required')
class NpcTransitionReferenceTests(unittest.TestCase):
    def test_retail_forward_inverse_project_independence_history_and_native_refusal(self):
        with tempfile.TemporaryDirectory() as raw:
            p,first=workflow.NpcTransitionWorkflow().project(raw);clones=[first]
            for name in ('Partial arrival','Inherited arrival'):
                p.command(dict(type='create_actor_draft',donor_entity_id=workflow.OWNER,name=name,position=dict(x=192,z=576)))
                clones.append(list(p.actor_drafts)[-1])
            for identity,values in zip(clones,[dict(entry_x_encoded=0,entry_z_encoded=255,direction_encoded=7),dict(direction_encoded=255)]):
                request=dict(entity_id=identity,entries={workflow.TARGET:values});r=review(p,request)
                p.command(dict(type='set_actor_draft_transitions',**request,review_key=r['review_key']))
            p.command(dict(type='set_transition_entry',entity_id=workflow.OWNER,transition_id=workflow.TARGET,values=dict(direction_encoded=3)))
            catalog=refresh_resource_catalog(p)
            asset=next(r for r in catalog['records'] if r['kind']=='transition' and r['owner_id']==workflow.OWNER and r['reference']['pc']==53)
            before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
            graph=assemble(p,catalog,asset['id']);edges=[e for e in graph['incoming'] if e['kind']=='npc_script_transition_arrival']
            self.assertEqual(len(edges),3)
            bindings={e['source_id']:e['npc_transition_arrival_evidence'] for e in edges}
            for identity,expected in zip(clones,[dict(entry_x_encoded=0,entry_z_encoded=255,direction_encoded=7),dict(entry_x_encoded=31,entry_z_encoded=30,direction_encoded=255),dict(entry_x_encoded=31,entry_z_encoded=30,direction_encoded=0)]):
                binding=bindings[identity];self.assertEqual(binding['effective_values'],expected)
                self.assertEqual(binding['retail_values'],dict(entry_x_encoded=31,entry_z_encoded=30,direction_encoded=0))
                self.assertEqual(binding['destination_scene_id'],'scene://map02')
                self.assertEqual(binding['native_instruction']['relative_operand_offset'],62)
                self.assertIn(next(e for e in edges if e['source_id']==identity),assemble(p,catalog,identity)['outgoing'])
            self.assertIsNone(bindings[clones[2]]['authored_values'])
            combined=assemble_project(p,{p.active_scene:catalog},asset['id'])
            self.assertEqual([e for e in combined['incoming'] if e['kind']=='npc_script_transition_arrival'],edges)
            self.assertEqual(before,(p._document(),p.undo_stack,p.redo_stack))
            restored=ProjectService.open(p.save())
            self.assertEqual(assemble(restored,refresh_resource_catalog(restored),asset['id']),graph)
            context=p._transition_context(workflow.OWNER);options=context.options(workflow.OWNER)
            bad=deepcopy(options);bad['transitions'][0]['decoded_byte_offset']+=1
            with patch.object(TransitionAuthoringContext,'options',return_value=bad):
                with self.assertRaises(ProjectError):assemble(p,catalog,clones[0])
            request=dict(entity_id=clones[0],entries={});r=review(p,request)
            p.command(dict(type='set_actor_draft_transitions',**request,review_key=r['review_key']))
            cleared=assemble(p,catalog,clones[0]);self.assertIsNone(next(e for e in cleared['outgoing'] if e['kind']=='npc_script_transition_arrival')['npc_transition_arrival_evidence']['authored_values'])
            p.undo();self.assertEqual(assemble(p,catalog,asset['id']),graph)
            p.redo();self.assertEqual(assemble(p,catalog,clones[0]),cleared);p.undo()
            evidence=os.environ.get('LEGAIA_NPC_ARRIVAL_REFERENCE_EVIDENCE')
            if evidence:
                root=Path(evidence);root.mkdir(parents=True,exist_ok=True)
                reports=[dict(id=asset['id'],report=graph)]+[dict(id=identity,report=assemble(p,catalog,identity)) for identity in clones]
                (root/'retail.json').write_text(json.dumps(dict(source_key=source_key(p),reports=reports,project=combined,project_id=asset['id'])),encoding='utf-8')


if __name__=='__main__':unittest.main()
