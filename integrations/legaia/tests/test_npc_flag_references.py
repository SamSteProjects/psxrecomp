"""NPC clone operands stay separate from donor actor overrides and runtime flags."""
from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch
import test_flag_asset_integration as fixtures
from sdk.asset_references import assemble,assemble_project
from sdk.project import ProjectError
from sdk.resources import refresh_resource_catalog


class NpcFlagReferences(TestCase):
    def setUp(self):
        fixtures.FlagAssetIntegration.setUp(self)
        self.owner='authored-actor://npc-one';self.other='authored-actor://npc-two'
        for owner,bit in [(self.owner,4),(self.other,5)]:
            self.project.actor_drafts[owner]=dict(name=owner,scene_id=self.project.active_scene,
                donor_entity_id=fixtures.ACTOR,flags=dict(donor_entity_id=fixtures.ACTOR,entries={self.key:dict(bit=bit)}))
        self.stack.enter_context(patch.object(self.project,'model_references',return_value=[]))

    def test_forward_inverse_project_and_independent_donor_authorship(self):
        self.project.command(dict(type='set_flag_bit',entity_id=fixtures.ACTOR,flag_id=self.key,values=dict(bit=3)))
        catalog=refresh_resource_catalog(self.project);flag=next(row for row in catalog['records'] if row['kind']=='flag')
        before=deepcopy((self.project._document(),self.project.undo_stack,self.project.redo_stack,self.project.active_scene))
        forward=assemble(self.project,catalog,self.owner);rows=[e for e in forward['outgoing'] if e['kind']=='npc_script_flag_operand']
        self.assertEqual(len(rows),2);self.assertEqual([e['npc_flag_operand_evidence']['effective_index'] for e in rows],[4,2])
        self.assertEqual([e['npc_flag_operand_evidence']['authored_index'] for e in rows],[4,None])
        self.assertTrue(all(e['target_id']==flag['id'] and e['layer']=='authored' and e['runtime_binding']=='not_asserted' for e in rows))
        inverse=assemble(self.project,catalog,flag['id']);npc=[e for e in inverse['incoming'] if e['kind']=='npc_script_flag_operand']
        self.assertEqual({e['source_id'] for e in npc},{self.owner,self.other});self.assertEqual(len(npc),4)
        donor=next(e for e in inverse['incoming'] if e['kind']=='effective_script_flag_reference');self.assertEqual(donor['flag_binding_evidence']['effective_index'],3)
        combined=assemble_project(self.project,{self.project.active_scene:catalog},flag['id'])
        self.assertEqual([e for e in combined['incoming'] if e['kind']=='npc_script_flag_operand'],npc)
        self.assertEqual(before,(self.project._document(),self.project.undo_stack,self.project.redo_stack,self.project.active_scene))

    def test_duplicate_forged_source_and_unavailable_catalog_do_not_invent_usages(self):
        catalog=refresh_resource_catalog(self.project);flag=next(row for row in catalog['records'] if row['kind']=='flag')
        for alter in ['duplicate','pc','operand','source']:
            broken=deepcopy(catalog);row=next(row for row in broken['records'] if row['kind']=='flag')
            if alter=='duplicate':broken['records'].append(deepcopy(row))
            if alter=='pc':next(r for r in broken['records'] if r['kind']=='script' and r['id']==row['script_id'])['flag_references'][0]['pc']+=1
            if alter=='operand':row['references'][0]['flag_operand_id']+='bad'
            if alter=='source':row['source_record']['sha256']='b'*64
            with self.assertRaises(ProjectError):assemble(self.project,broken,self.owner)
        missing=deepcopy(catalog);missing['records']=[row for row in missing['records'] if row['kind']!='flag']
        result=assemble(self.project,missing,self.owner);self.assertFalse(any(e['kind']=='npc_script_flag_operand' for e in result['outgoing']));self.assertEqual(result['coverage']['unresolved_reference_count'],2)

    def test_read_only_inherited_usages_ignore_donor_current_bits(self):
        del self.project.actor_drafts[self.owner]['flags'];del self.project.actor_drafts[self.other]['flags']
        self.project.command(dict(type='set_flag_bit',entity_id=fixtures.ACTOR,flag_id=self.key,values=dict(bit=3)))
        result=assemble(self.project,refresh_resource_catalog(self.project),self.owner)
        rows=[e['npc_flag_operand_evidence'] for e in result['outgoing'] if e['kind']=='npc_script_flag_operand']
        self.assertEqual(len(rows),2);self.assertTrue(all(row['authored_index'] is None and row['effective_index']==2 for row in rows))
