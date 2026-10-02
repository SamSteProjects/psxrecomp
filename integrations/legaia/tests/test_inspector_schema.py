import unittest
from sdk.inspector_schema import inspector_schema
class InspectorSchema(unittest.TestCase):
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
        self.assertEqual(set(schema['asset_inspectors']),{'actor','scene','template','worldmap','model','texture','animation','script','dialogue','flag','collision','trigger','region'})
        for kind,identifier in schema['asset_inspectors'].items():
            definition=schema['components'][identifier]
            self.assertEqual(definition['layout'],'read-only-properties')
            self.assertTrue(all('authoring' not in prop for prop in definition['properties']))
            self.assertEqual(len(definition['actions']),2 if kind=='worldmap' else 1)
            self.assertNotIn('command',definition['actions'][0])
        schema['components']['AssetModel']['actions'][0]['label']='changed'
        self.assertEqual(inspector_schema()['components']['AssetModel']['actions'][0]['label'],'Inspect model')

if __name__=='__main__':unittest.main()
