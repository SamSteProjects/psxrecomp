"""Synthetic guarded observations retain distinct appearance/clip witnesses."""
from copy import deepcopy
import unittest

from integrations.legaia.observer.correlation import correlate
from integrations.legaia.observer.test_correlation import imported, status


def fixture():
    document = imported()
    target = document['actors'][0]['semantic_id']
    appearance = deepcopy(document['actors'][0])
    appearance['semantic_id'] = 'scene://town01/actors/man-p1/0002'
    appearance['source_record']['record_index'] = 2
    appearance['model_reference'].update(model_index=5, normalized_pool_index=5,
                                        asset_semantic_id='asset://model/5')
    appearance['placement_fields'].update(animation_id=8, local_count=9)
    witness = deepcopy(appearance)
    witness['semantic_id'] = 'scene://town01/actors/man-p1/0003'
    witness['source_record']['record_index'] = 3
    witness['placement_fields'].update(animation_id=9, local_count=12)
    document['actors'].extend((appearance, witness))
    document['assets']['models'].append({'semantic_id': 'asset://model/5',
                                        'source_record': {'object_count': 3}})
    return document, target, appearance['semantic_id'], witness['semantic_id']


class ActorAnimationCorrelationTests(unittest.TestCase):
    def test_effective_model_and_clip_witnesses_remain_distinct(self):
        document, target, appearance, witness = fixture()
        live = status()
        live['actor_bindings']['nodes'][0].update(model_index=5, normalized_pool_index=5,
                                                animation_id=9)
        model_donors, animation_donors = {target: appearance}, {target: witness}
        before = deepcopy((document, live, model_donors, animation_donors))
        result = correlate(document, live, model_donors, animation_donors)
        candidate = result['entities'][target]['candidates'][0]
        self.assertEqual(candidate['appearance_layers'], ['effective'])
        self.assertEqual(candidate['effective_donor_id'], appearance)
        self.assertEqual(candidate['effective_animation_donor_id'], witness)
        self.assertEqual(result['appearance_donors'], model_donors)
        self.assertEqual(result['animation_donors'], animation_donors)
        self.assertFalse(result['entities'][target]['binding_confirmed'])
        self.assertEqual(result['confirmed_match_count'], 0)
        self.assertTrue(candidate['placement_header_agrees_with_import'])
        self.assertEqual((document, live, model_donors, animation_donors), before)
        result['animation_donors'][target] = target
        self.assertEqual(animation_donors[target], witness)

    def test_imported_layer_remains_retail_and_old_api_defaults_to_appearance(self):
        document, target, appearance, witness = fixture()
        retail = correlate(document, status(), {target: appearance}, {target: witness})
        candidate = retail['entities'][target]['candidates'][0]
        self.assertEqual(candidate['appearance_layers'], ['imported'])
        self.assertIsNone(candidate['effective_donor_id'])
        self.assertIsNone(candidate['effective_animation_donor_id'])
        live = status()
        live['actor_bindings']['nodes'][0].update(model_index=5, normalized_pool_index=5,
                                                animation_id=8)
        old = correlate(document, live, {target: appearance})
        self.assertEqual(old, correlate(document, live, {target: appearance}, {}))
        self.assertEqual(old['animation_donors'], {})
        self.assertEqual(old['entities'][target]['candidates'][0]['appearance_layers'], ['effective'])
        self.assertEqual(old['entities'][target]['candidates'][0]['effective_animation_donor_id'], appearance)
        current = correlate(document, live, {target: appearance}, {target: witness})
        self.assertEqual(current['entities'][target]['candidates'], [])

    def test_assignment_without_appearance_uses_original_model_and_new_clip(self):
        document = imported()
        target = document['actors'][0]['semantic_id']
        witness = deepcopy(document['actors'][0])
        witness['semantic_id'] = 'scene://town01/actors/man-p1/0002'
        witness['placement_fields'].update(animation_id=8, local_count=9)
        document['actors'].append(witness)
        live = status()
        live['actor_bindings']['nodes'][0]['animation_id'] = 8
        result = correlate(document, live, animation_donors={target: witness['semantic_id']})
        candidate = result['entities'][target]['candidates'][0]
        self.assertEqual(candidate['appearance_layers'], ['effective'])
        self.assertEqual(candidate['effective_donor_id'], target)
        self.assertEqual(candidate['effective_animation_donor_id'], witness['semantic_id'])
        self.assertFalse(result['entities'][target]['binding_confirmed'])

    def test_invalid_mapping_and_incompatible_witness_fail_closed(self):
        document, target, appearance, witness = fixture()
        for donors in ([target, witness], {target: 'scene://other/actor'},
                       {'unknown': witness}, {target: 3}, {target: target}):
            with self.subTest(donors=donors):
                result = correlate(document, status(), {target: appearance}, donors)
                self.assertFalse(result['available'])
                self.assertEqual(result['candidate_count'], 0)
        for field, value in (('asset_semantic_id', 'asset://model/4'), ('model_index', 4),
                             ('model_pool', 'global_special'), ('normalized_pool_index', 4),
                             ('resolution_status', 'unresolved')):
            modified = deepcopy(document)
            modified['actors'][2]['model_reference'][field] = value
            with self.subTest(field=field):
                self.assertFalse(correlate(modified, status(), {target: appearance}, {target: witness})['available'])
        for value in (0, True, 256, None):
            modified = deepcopy(document)
            modified['actors'][2]['placement_fields']['animation_id'] = value
            with self.subTest(animation_id=value):
                self.assertFalse(correlate(modified, status(), {target: appearance}, {target: witness})['available'])
        modified = deepcopy(document)
        modified['assets']['models'].append(deepcopy(modified['assets']['models'][-1]))
        self.assertFalse(correlate(modified, status(), {target: appearance}, {target: witness})['available'])


if __name__ == '__main__':
    unittest.main()
