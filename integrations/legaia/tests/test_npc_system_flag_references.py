"""Clone selector references retain Retail identities and independent ownership."""
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from importer.pipeline import import_scene
from sdk.asset_references import assemble, assemble_project, source_key
from sdk.project import ProjectService, ProjectError
from sdk.resources import refresh_resource_catalog
from sdk.npc_system_flags import review as npc_review
from sdk.system_flags import review
import test_system_flag_references as base
from test_importer_dialogue_authoring import ACTOR


class NpcSystemReferences(unittest.TestCase):
    def setUp(self):
        base.SystemReferenceIntegration.setUp(self)
        self.owners=['authored-actor://one','authored-actor://two','authored-actor://inherited']
        for owner,value in zip(self.owners,[0,2048,None]):
            draft=dict(name=owner,scene_id=self.project.active_scene,donor_entity_id=ACTOR)
            if value is not None:
                draft['system_flags']=dict(donor_entity_id=ACTOR,entries={self.key:dict(index=value)})
            self.project.actor_drafts[owner]=draft
        self.stack.enter_context(patch.object(self.project,'model_references',return_value=[]))

    def test_forward_inverse_project_separate_clone_and_donor_values(self):
        base.SystemReferenceIntegration.edit(self)
        catalog=refresh_resource_catalog(self.project)
        group=next(r for r in catalog['records'] if r['kind']=='flag' and r['owner_id']==ACTOR)
        before=deepcopy((self.project._document(),self.project.undo_stack,self.project.redo_stack))
        graph=assemble(self.project,catalog,group['id'])
        edges=[e for e in graph['incoming'] if e['kind']=='npc_script_flag_operand']
        values={e['source_id']:e['npc_flag_operand_evidence'] for e in edges}
        self.assertEqual(len(edges),3)
        for owner,value in zip(self.owners,[0,2048,None]):
            binding=values[owner]
            self.assertEqual(binding['retail_index'],326)
            self.assertEqual(binding['authored_index'],value)
            self.assertEqual(binding['effective_index'],326 if value is None else value)
            self.assertEqual(binding['operand_id'],None if value is None else self.key)
            self.assertEqual('native_operand_qualification' in binding,value is not None)
            if value is not None:
                self.assertEqual(binding['native_operand_qualification']['maximum'],4095)
                self.assertEqual(binding['native_operand_qualification']['authored_index'],value)
            forward=assemble(self.project,catalog,owner)
            self.assertIn(next(e for e in edges if e['source_id']==owner),forward['outgoing'])
        donor=next(e for e in graph['incoming'] if e['kind']=='effective_script_flag_reference')
        self.assertEqual(donor['flag_binding_evidence']['effective_index'],4095)
        combined=assemble_project(self.project,{self.project.active_scene:catalog},group['id'])
        self.assertEqual([e for e in combined['incoming'] if e['kind']=='npc_script_flag_operand'],edges)
        self.assertEqual(before,(self.project._document(),self.project.undo_stack,self.project.redo_stack))

    def test_owned_selector_does_not_require_a_donor_override(self):
        catalog=refresh_resource_catalog(self.project)
        group=next(r for r in catalog['records'] if r['kind']=='flag' and r['owner_id']==ACTOR)
        self.assertIsNone(group['references'][0]['flag_operand_id'])
        graph=assemble(self.project,catalog,self.owners[1])
        binding=next(e['npc_flag_operand_evidence'] for e in graph['outgoing'] if e['kind']=='npc_script_flag_operand')
        self.assertEqual((binding['operand_id'],binding['authored_index'],binding['effective_index']),(self.key,2048,2048))

    def test_missing_catalog_and_forged_qualification_do_not_invent_usages(self):
        catalog=refresh_resource_catalog(self.project)
        missing=deepcopy(catalog);missing['records']=[r for r in missing['records'] if r['kind']!='flag']
        graph=assemble(self.project,missing,self.owners[0])
        self.assertEqual(graph['coverage']['unresolved_reference_count'],2)
        self.assertFalse(any(e['kind']=='npc_script_flag_operand' for e in graph['outgoing']))
        for field,value in [('maximum',31),('source_record_sha256','b'*64),('target_context',1)]:
            options=self.context.options(ACTOR);options['targets'][0][field]=value
            with patch('importer.system_flag_authoring.SystemFlagAuthoringContext.options',return_value=options):
                with self.assertRaises(ProjectError):assemble(self.project,catalog,self.owners[0])
        self.project.actor_drafts[self.owners[0]]['system_flags']['entries'][self.key]['index']=True
        with self.assertRaises(ProjectError):assemble(self.project,catalog,self.owners[0])


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'Private Retail disc required')
class RetailNpcSystemReferences(unittest.TestCase):
    def test_town01_clones_history_and_actual_client_reports(self):
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory))
            p.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'],'town01'),os.environ['LEGAIA_DISC_BIN'])
            owner='scene://town01/actors/man-p1/0011';operand='script://town01/actors/man-p1/0011/system-flag/0016'
            r=review(p,owner,operand,{'index':4095})
            p.command(dict(type='set_system_flag_selector',entity_id=owner,operand_id=operand,value={'index':4095},review_key=r['review_key']))
            clones=[]
            for index in [0,2048,None]:
                previous=set(p.actor_drafts)
                p.command(dict(type='create_actor_draft',donor_entity_id=owner,position={'x':3008,'z':5440},name=f'Selector {index}'))
                identifier=(set(p.actor_drafts)-previous).pop();clones.append(identifier)
                if index is not None:
                    request=dict(entity_id=identifier,entries={operand:dict(index=index)})
                    r=npc_review(p,request)
                    p.command(dict(type='set_actor_draft_system_flags',**request,review_key=r['review_key']))
            catalog=refresh_resource_catalog(p)
            group=next(a for a in catalog['records'] if a['kind']=='flag' and a['owner_id']==owner and a['bank']=='system' and a['index']==326)
            before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
            graph=assemble(p,catalog,group['id'])
            for clone,index in zip(clones,[0,2048,None]):
                rows=[e for e in graph['incoming'] if e['kind']=='npc_script_flag_operand' and e['source_id']==clone]
                own=next(e['npc_flag_operand_evidence'] for e in rows if e['pc']==22)
                other=next(e['npc_flag_operand_evidence'] for e in rows if e['pc']==67)
                self.assertEqual((own['retail_index'],own['authored_index'],own['effective_index']),(326,index,326 if index is None else index))
                self.assertEqual((other['operand_id'],other['authored_index'],other['effective_index']),(None,None,326))
            self.assertEqual(before,(p._document(),p.undo_stack,p.redo_stack))
            saved=p.save();restored=ProjectService.open(saved)
            self.assertEqual(restored.actor_drafts,p.actor_drafts)
            self.assertEqual(assemble(restored,refresh_resource_catalog(restored),group['id']),graph)
            request=dict(entity_id=clones[1],entries={});r=npc_review(p,request)
            original_key=source_key(p)
            p.command(dict(type='set_actor_draft_system_flags',**request,review_key=r['review_key']))
            self.assertNotEqual(source_key(p),original_key)
            cleared=assemble(p,catalog,clones[1]);row=next(e for e in cleared['outgoing'] if e['kind']=='npc_script_flag_operand' and e['pc']==22)
            self.assertIsNone(row['npc_flag_operand_evidence']['authored_index'])
            p.undo();self.assertEqual(assemble(p,catalog,group['id']),graph)
            p.redo();self.assertEqual(assemble(p,catalog,clones[1]),cleared)
            p.undo()
            if os.environ.get('LEGAIA_NPC_SYSTEM_REFERENCE_EVIDENCE'):
                root=Path(os.environ['LEGAIA_NPC_SYSTEM_REFERENCE_EVIDENCE']);root.mkdir(parents=True,exist_ok=True)
                reports=[dict(id=group['id'],report=graph)]+[dict(id=c,report=assemble(p,catalog,c)) for c in clones]
                (root/'retail.json').write_text(json.dumps(dict(source_key=source_key(p),reports=reports)),encoding='utf-8')


if __name__=='__main__':unittest.main()
