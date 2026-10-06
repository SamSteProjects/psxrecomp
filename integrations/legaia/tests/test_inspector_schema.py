import unittest
from sdk.inspector_schema import inspector_schema
class InspectorSchema(unittest.TestCase):
    def test_npc_draft_asset_schema_is_authored_metadata_with_qualified_navigation(self):
        schema=inspector_schema();self.assertEqual(schema['authored_asset_inspectors'],{'npc_draft':'AssetNpcDraft'})
        component=schema['components']['AssetNpcDraft'];self.assertEqual(component['layout'],'read-only-properties')
        self.assertTrue(all('authoring' not in prop for prop in component['properties']))
        positions=[p for p in component['properties'] if p['id'] in ('x','z')]
        self.assertTrue(all(p['path'][:3]==['authoredRecord','authored','position'] for p in positions))
        self.assertTrue(all(p['state']=='authored-through-command' for p in positions))
        self.assertEqual([action['id'] for action in component['actions']],['select-asset-actor','edit-npc-appearance','edit-npc-dialogue','inspect-npc-build-script','inspect-npc-donor-script','inspect-npc-donor-model'])
        self.assertEqual(next(a for a in component['actions'] if a['id']=='inspect-npc-donor-model')['when'],['authoredRecord','model_reference','target_id'])
        self.assertEqual(next(a for a in component['actions'] if a['id']=='inspect-npc-donor-model')['capability'],'model_preview')
        component['properties'][0]['path'].clear();self.assertEqual(inspector_schema()['components']['AssetNpcDraft']['properties'][0]['path'],['id'])

    def test_npc_draft_identity_authored_position_and_preview_remain_separate(self):
        schema=inspector_schema();components=schema['components']
        for name in ('NpcDraftIdentity','NpcDraftTransform','NpcDraftPreview'):
            self.assertEqual(components[name]['layout'],'read-only-properties')
            self.assertTrue(all('authoring' not in p for p in components[name]['properties']))
        authored=components['NpcDraftTransform']['properties']
        self.assertEqual([p['path'] for p in authored],[['draft','position','x'],['draft','position','z']])
        self.assertTrue(all(p['state']=='authored-through-command' for p in authored))
        preview={p['id']:p for p in components['NpcDraftPreview']['properties']}
        self.assertEqual(preview['position_y']['state'],'unresolved')
        self.assertEqual(preview['surface_y']['state'],'derived')
        self.assertEqual(preview['surface_y']['path'],['preview','preview_position','y'])
        self.assertTrue(all('fallback_paths' not in p for p in preview.values()))
        self.assertEqual(components['NpcDraftIdentity']['details'][0]['path'],['donor','components','RetailMetadata'])
        authored[0]['path'].clear();self.assertEqual(inspector_schema()['components']['NpcDraftTransform']['properties'][0]['path'],['draft','position','x'])

    def test_environment_snapshots_keep_retail_preview_and_source_paths_separate(self):
        schema=inspector_schema();components=schema['components']
        identifiers=('EnvironmentPlacement','EnvironmentRetailTransform','EnvironmentPreviewTransform','EnvironmentMetadata')
        for identifier in identifiers:
            definition=components[identifier]
            self.assertEqual(definition['layout'],'read-only-properties')
            self.assertTrue(all('authoring' not in prop for prop in definition['properties']))
            self.assertNotIn('actions',definition)
        retail=components['EnvironmentRetailTransform']['properties']
        current=components['EnvironmentPreviewTransform']['properties']
        self.assertEqual(len(retail),6);self.assertEqual(len(current),6)
        for prop in retail:
            self.assertEqual(prop['path'][:2],['source_record','imported_transform'])
            self.assertEqual(prop['state'],'read-only-retail')
        for prop in current:
            self.assertEqual(prop['path'][:1],['effective_transform'])
            self.assertEqual(prop['state'],'effective')
            self.assertNotIn('fallback_paths',prop)
        self.assertEqual(components['EnvironmentMetadata']['details'],[
            {'label':'Placement source record','path':['source_record']},
            {'label':'Decoder evidence','path':['evidence']}])
        current[0]['path'].clear()
        self.assertEqual(inspector_schema()['components']['EnvironmentPreviewTransform']['properties'][0]['path'],['effective_transform','position','x'])

    def test_authoring_build_unknown_and_detached_contracts(self):
        schema=inspector_schema();props={p['id']:p for p in schema['components']['Transform']['properties']}
        self.assertEqual(props['x']['authoring']['minimum'],-32767)
        self.assertEqual(props['x']['build'],{'supported':True,'minimum':64,'maximum':16384,'step':64,'note':'Build requires a representable64-unit retail placement'})
        self.assertEqual(props['y']['retail_status'],'unresolved');self.assertFalse(props['y']['build']['supported'])
        self.assertFalse(schema['live_writes']);self.assertEqual(schema['unknown_component_policy'],'read-only-details')
        props['x']['authoring']['set_command']='bad';self.assertEqual(inspector_schema()['components']['Transform']['properties'][0]['authoring']['set_command'],'set_transform')
        self.assertTrue(all('authoring' not in p for p in schema['components']['ModelRenderer']['properties']))
    def test_appearance_live_and_provenance_never_imply_direct_writes(self):
        schema=inspector_schema()['components']
        donor=next(p for p in schema['ActorAppearance']['properties'] if p['id']=='donor_entity_id')
        self.assertEqual(donor['state'],'authored-through-donor-review');self.assertNotIn('authoring',donor)
        self.assertEqual(donor['layers'],['authored'])
        self.assertTrue(next(a for a in schema['ActorAppearance']['actions'] if a['id']=='clear-appearance')['requires_edit'])
        self.assertEqual(schema['Dialogue']['actions'][0]['capability'],'actor_script_preview')
        self.assertTrue(all('authoring' not in p for p in schema['RuntimeCorrelation']['properties']))
        self.assertEqual(schema['RetailMetadata']['details'][0]['path'],[])

    def test_animation_and_preset_actions_preserve_capability_and_edit_guards(self):
        from copy import deepcopy
        from unittest.mock import patch
        from pathlib import Path
        import tempfile
        from sdk.project import ProjectService
        from sdk.server import EditorServer
        from integrations.legaia.tests.test_project_workflow import synthetic_scene
        schema=inspector_schema()['components']
        actions={row['id']:row for row in schema['Animation']['actions']}
        self.assertTrue(actions['author-animation-channels']['requires_edit'])
        self.assertEqual(actions['author-animation-channels']['capability'],'actor_animation_authoring')
        self.assertEqual(actions['preview-scene-animation']['when'],['preview_support','supported'])
        self.assertEqual(schema['ModelRenderer']['actions'][1]['when'],['reference_animation','supported'])
        self.assertEqual(schema['ActorPresets']['actions'][0]['capability'],'authored_transform_templates')
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.import_metadata(synthetic_scene());p.disc_path='missing-fixture.bin'
            before=deepcopy(p.imports)
            with patch('importer.animation.animation_capabilities',return_value={'supported':True,'clips':[{'id':'reference-source'}]}):
                with EditorServer(('127.0.0.1',0),p) as server:state=server.state()
            self.assertTrue(state['capabilities']['actor_animation_authoring'])
            self.assertEqual(state['scene']['entities'][0]['components']['ModelRenderer']['reference_animation'],{'supported':True,'first_clip_id':'reference-source'})
            self.assertNotIn('reference_animation',p.state()['scene']['entities'][0]['components']['ModelRenderer'])
            self.assertNotIn('ActorPresets',state['scene']['entities'][0]['components'])
            self.assertEqual(p.imports,before)

    def test_asset_inspectors_are_detached_read_only_tool_groups(self):
        schema=inspector_schema()
        self.assertEqual(set(schema['asset_inspectors']),{'actor','scene','template','worldmap','model','texture','animation','script','dialogue','flag','transition','collision','trigger','region'})
        for kind,identifier in schema['asset_inspectors'].items():
            definition=schema['components'][identifier]
            self.assertEqual(definition['layout'],'read-only-properties')
            self.assertTrue(all('authoring' not in prop for prop in definition['properties']))
            self.assertEqual(len(definition['actions']),4 if kind == 'trigger' else 2 if kind in ('worldmap','region') else 1)
            self.assertNotIn('command',definition['actions'][0])
        self.assertEqual(schema['components']['AssetRegion']['actions'][1]['capability'],'field_region_authoring')
        schema['components']['AssetModel']['actions'][0]['label']='changed'
        self.assertEqual(inspector_schema()['components']['AssetModel']['actions'][0]['label'],'Inspect model')

    def test_authored_script_components_are_detached_and_omit_empty_overrides(self):
        import tempfile
        from pathlib import Path
        from copy import deepcopy
        from sdk.project import ProjectService
        from integrations.legaia.tests.test_project_workflow import synthetic_scene
        families=('ScriptMovement','ScriptFlags','ScriptWaits','ScriptModelSelectors')
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.import_metadata(synthetic_scene())
            identifier=p.imports[p.active_scene]['actors'][0]['semantic_id'];before=deepcopy(p.imports)
            self.assertTrue(all(name not in p.state()['scene']['entities'][0]['components'] for name in families))
            for name in families:
                p.overrides.setdefault(identifier,{})[name]={'entries':{'16':{'fixture':'authored'}}}
            state=p.state();components=state['scene']['entities'][0]['components']
            for name in families:
                self.assertEqual(components[name]['authored_instruction_count'],1)
                components[name]['entries']['16']['fixture']='changed'
                self.assertEqual(p.overrides[identifier][name]['entries']['16']['fixture'],'authored')
                definition=state['inspector_schema']['components'][name]
                self.assertEqual(definition['layout'],'read-only-properties')
                self.assertTrue(all('authoring' not in prop for prop in definition['properties']))
                self.assertEqual(definition['actions'][0]['id'],'inspect-script')
                reset=definition['actions'][1]
                self.assertEqual(reset['id'],'reset-script-component')
                self.assertEqual(reset['capability'],'project_navigation')
                self.assertTrue(reset['requires_edit'])
            self.assertEqual(p.imports,before)

    def test_allocated_assignment_is_readonly_metadata_with_reviewed_actions(self):
        definition=inspector_schema()['components']['ActorAllocatedAnimation']
        self.assertEqual(definition['layout'],'read-only-properties')
        self.assertEqual({p['id'] for p in definition['properties']},{'record_id','record_sha256','model_asset_id','initial_selection','gameplay_verified'})
        self.assertTrue(all('authoring' not in p for p in definition['properties']))
        actions=definition['actions']
        self.assertTrue(actions[0]['requires_edit'])
        self.assertEqual(actions[0]['capability'],'actor_animation_assignment')
        self.assertEqual(actions[1]['when'],['authored','record_id'])
        self.assertNotIn('requires_edit',actions[1])
        definition['properties'][0]['label']='changed'
        self.assertEqual(inspector_schema()['components']['ActorAllocatedAnimation']['properties'][0]['label'],'Retained clip')

    def test_facing_and_branch_reset_actions_require_authored_entries(self):
        import tempfile
        from pathlib import Path
        from sdk.project import ProjectService
        from integrations.legaia.tests.test_project_workflow import synthetic_scene
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.import_metadata(synthetic_scene())
            owner=p.imports[p.active_scene]['actors'][0]['semantic_id']
            for name in ('ScriptFacing','ScriptBranches'):
                self.assertEqual(p.state()['scene']['entities'][0]['components'][name]['authored_instruction_count'],0)
                p.overrides.setdefault(owner,{})[name]={'entries':{'fixture':{'value':1}}}
                state=p.state();component=state['scene']['entities'][0]['components'][name]
                self.assertEqual(component['authored_instruction_count'],1)
                component['entries'].clear()
                self.assertEqual(len(p.overrides[owner][name]['entries']),1)
                action=state['inspector_schema']['components'][name]['actions'][1]
                self.assertEqual(action['id'],'reset-script-component')
                self.assertEqual(action['when'],['authored_instruction_count'])
                self.assertTrue(action['requires_edit'])

    def test_dialogue_and_transition_components_keep_distinct_entry_shapes(self):
        import tempfile
        from pathlib import Path
        from sdk.project import ProjectService
        from integrations.legaia.tests.test_project_workflow import synthetic_scene
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.import_metadata(synthetic_scene())
            owner=p.imports[p.active_scene]['actors'][0]['semantic_id']
            components=p.state()['scene']['entities'][0]['components']
            self.assertEqual(components['Dialogue']['authored_run_count'],0)
            self.assertNotIn('Transitions',components)
            p.overrides[owner]={'Dialogue':{'runs':{'text-run':'Edited text'}},'Transitions':{'entries':{'entry':{'entry_bytes':[1,2,3]}}}}
            state=p.state();components=state['scene']['entities'][0]['components']
            self.assertEqual(components['Dialogue']['authored_run_count'],1)
            self.assertEqual(components['Transitions']['authored_instruction_count'],1)
            components['Dialogue']['authored']['runs'].clear();components['Transitions']['entries'].clear()
            self.assertEqual(p.overrides[owner]['Dialogue']['runs'],{'text-run':'Edited text'})
            self.assertEqual(len(p.overrides[owner]['Transitions']['entries']),1)
            reset=next(a for a in state['inspector_schema']['components']['Dialogue']['actions'] if a['id']=='reset-script-component')
            self.assertTrue(reset['requires_edit']);self.assertEqual(reset['when'],['authored_run_count'])

    def test_property_states_cover_registry_without_granting_capabilities(self):
        schema=inspector_schema();states=schema['property_states']
        self.assertFalse(schema['live_writes']);self.assertNotIn('live-writable',states)
        for component in schema['components'].values():
            for prop in component['properties']:
                if 'state' in prop:self.assertIn(prop['state'],states)
            for layer in component.get('layers',[]):
                if isinstance(layer,dict):self.assertIn(layer['state'],states)
            for state in component.get('layer_states',{}).values():self.assertIn(state,states)
        for definition in states.values():
            self.assertEqual(set(definition),{'label','note'});self.assertTrue(definition['label']);self.assertTrue(definition['note'])
        self.assertEqual(schema['components']['Transform']['layer_states']['authored'],'authored-through-command')
        states['derived']['label']='Changed';self.assertEqual(inspector_schema()['property_states']['derived']['label'],'Derived')

if __name__=='__main__':unittest.main()
