"""System annotations retain Retail groups and independently qualified spans."""
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from importer.system_flag_authoring import SystemFlagAuthoringContext
from importer.script_catalog import _catalog
from importer.pipeline import import_scene
from sdk.resources import refresh_resource_catalog,scene_flag_index,project_flag_index,scene_flag_state_key,project_flag_state_key
from sdk.asset_references import assemble
from sdk.flag_assets import validate_flag_asset
from sdk.project import ProjectService,ProjectError
from sdk.system_flags import review
import test_flag_asset_integration as base
from test_importer_dialogue_authoring import fixture,ACTOR


class SystemReferenceIntegration(unittest.TestCase):
    def setUp(self):
        base.FlagAssetIntegration.setUp(self)
        self.source,man=fixture(b'\x51\x46\x21')
        self.catalog=_catalog(man,'fixture',{'synthetic':True},set())
        self.context=SystemFlagAuthoringContext(self.source)
        self.key=self.context.options(ACTOR)['targets'][0]['semantic_id']
        self.stack.enter_context(patch('importer.script_catalog.load_script_asset_catalog',return_value=self.catalog))
        self.stack.enter_context(patch('importer.system_flag_authoring.load_system_flag_authoring_context',return_value=self.context))
        self.stack.enter_context(patch.object(self.project,'_dialogue_context',return_value=self.source))

    def edit(self):
        proposal=review(self.project,ACTOR,self.key,{'index':4095})
        self.project.command(dict(type='set_system_flag_selector',entity_id=ACTOR,operand_id=self.key,value={'index':4095},review_key=proposal['review_key']))

    def test_catalog_scene_project_and_graph_keep_retail_identity_and_exact_history(self):
        retail=refresh_resource_catalog(self.project)
        group=next(r for r in retail['records'] if r['kind']=='flag' and r['owner_id']==ACTOR)
        scene_key=scene_flag_state_key(self.project);project_key=project_flag_state_key(self.project)
        self.edit();before=deepcopy((self.project._document(),self.project.undo_stack,self.project.redo_stack))
        current=refresh_resource_catalog(self.project)
        authored=next(r for r in current['records'] if r['id']==group['id'])
        ref=authored['references'][0]
        self.assertEqual((authored['index'],ref['retail_index'],ref['authored_index'],ref['effective_index']),(326,326,4095,4095))
        self.assertEqual(ref['flag_operand_id'],self.key)
        self.assertEqual(ref['authored_qualification']['schema_version'],'legaia.system-flag-operand-qualification.v1')
        self.assertNotEqual(scene_flag_state_key(self.project),scene_key)
        self.assertNotEqual(project_flag_state_key(self.project),project_key)
        self.assertEqual(scene_flag_index(self.project)['authored_reference_count'],1)
        with patch('sdk.resources._verify'):self.assertEqual(project_flag_index(self.project)['authored_reference_count'],1)
        graph=assemble(self.project,current,group['id'])
        edge=next(e for e in graph['incoming'] if e['kind']=='effective_script_flag_reference')
        self.assertEqual(edge['flag_binding_evidence']['effective_index'],4095)
        self.assertEqual(edge['target_id'],group['id'])
        self.assertEqual(before,(self.project._document(),self.project.undo_stack,self.project.redo_stack))
        restored=ProjectService.open(self.project.save());self.assertEqual(restored.overrides,self.project.overrides)
        self.project.undo();self.assertEqual(refresh_resource_catalog(self.project),retail)
        self.project.redo();self.assertEqual(refresh_resource_catalog(self.project),current)

    def test_missing_forged_and_extended_qualifications_refuse(self):
        self.edit();catalog=refresh_resource_catalog(self.project)
        asset=next(r for r in catalog['records'] if r['kind']=='flag' and r['owner_id']==ACTOR)
        for field,val in [('maximum',31),('schema_version','legaia.flag-operand-qualification.v1'),('extended_target',1),('authored_index',4096),('source_record_sha256','a'*64)]:
            malformed=deepcopy(asset);malformed['references'][0]['authored_qualification'][field]=val
            with self.assertRaises(ProjectError):validate_flag_asset(malformed)
        malformed=deepcopy(asset);del malformed['references'][0]['authored_qualification']
        with self.assertRaises(ProjectError):validate_flag_asset(malformed)


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'Private Retail disc required')
class RetailSystemReferences(unittest.TestCase):
    def test_actual_town01_resource_and_graph_export_separate_layers(self):
        with tempfile.TemporaryDirectory() as path:
            p=ProjectService(Path(path));p.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'],'town01'),os.environ['LEGAIA_DISC_BIN'])
            owner='scene://town01/actors/man-p1/0011';operand='script://town01/actors/man-p1/0011/system-flag/0016'
            r=review(p,owner,operand,{'index':4095});p.command(dict(type='set_system_flag_selector',entity_id=owner,operand_id=operand,value={'index':4095},review_key=r['review_key']))
            before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
            catalog=refresh_resource_catalog(p)
            asset=next(a for a in catalog['records'] if a['kind']=='flag' and a['owner_id']==owner and a['bank']=='system' and a['index']==326)
            ref=next(r for r in asset['references'] if r['pc']==22)
            self.assertEqual((ref['retail_index'],ref['effective_index']),(326,4095))
            graph=assemble(p,catalog,asset['id'])
            self.assertEqual(len([e for e in graph['incoming'] if e['kind']=='effective_script_flag_reference']),1)
            self.assertEqual(before,(p._document(),p.undo_stack,p.redo_stack))
            p.command(dict(type='create_actor_draft',donor_entity_id=owner,position={'x':3008,'z':5440},name='Reference candidate'))
            before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
            graph=assemble(p,catalog,asset['id'])
            inherited=[e['npc_flag_operand_evidence'] for e in graph['incoming'] if e['kind']=='npc_script_flag_operand']
            self.assertTrue(inherited)
            self.assertTrue(all(e['authored_index'] is None and e['effective_index']==326 and e['operand_id'] is None for e in inherited))
            self.assertEqual(before,(p._document(),p.undo_stack,p.redo_stack))
            if os.environ.get('LEGAIA_SYSTEM_REFERENCE_EVIDENCE'):
                dest=Path(os.environ['LEGAIA_SYSTEM_REFERENCE_EVIDENCE']);dest.mkdir(parents=True,exist_ok=True)
                (dest/'retail.json').write_text(json.dumps(dict(asset=asset,graph=graph)),encoding='utf-8')


if __name__=='__main__':unittest.main()
