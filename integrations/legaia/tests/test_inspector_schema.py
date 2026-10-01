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
if __name__=='__main__':unittest.main()
