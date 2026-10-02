"""Transition dependency edges retain verified script identity, not runtime routes."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from sdk.project import ProjectService, ProjectError, digest
from sdk.asset_references import assemble, assemble_project
from sdk.transition_assets import build_transition_assets
from test_project_workflow import synthetic_scene
from test_importer_script_catalog import catalog as script_catalog


class TransitionAssetReferences(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = ProjectService(Path(temporary.name))
        self.project.import_metadata(synthetic_scene())
        self.scene = self.project.active_scene

    def catalog(self, name=b'town02', *, partition=1, extended=None):
        lead = b'\x3f' if extended is None else bytes([0xbf, extended])
        source = script_catalog(lead + b'\0\0' + bytes([len(name)]) + name + b'\x01\x82\x03')
        if partition == 2:
            # Requalify the decoded fixture as an independent P2 source owner.
            for script in source['assets']:
                script['semantic_id'] = script['script_id'] = script['semantic_id'].replace('/actors/man-p1/', '/scripts/man-p2/')
                script['owner_semantic_id'] = script['semantic_id'].replace('script://', 'scene://', 1)
                script['actor_semantic_id'] = None
                script['partition'] = script['source_record']['partition'] = 2
        transitions = build_transition_assets(source, self.project.imports)
        records = []
        for record in source['assets'] + transitions:
            if record['asset_kind'] not in ('script', 'transition'):
                continue
            record = deepcopy(record)
            record.update(id=record['semantic_id'], kind=record['asset_kind'], scene_id=self.scene, layer='derived')
            records.append(record)
        return dict(scene_id=self.scene, source_key='a'*64, records=records, limitations=['Source instructions only.'])

    def test_p1_p2_named_edges_preserve_legacy_and_exact_source_proof(self):
        for partition in (1, 2):
            with self.subTest(partition=partition):
                catalog = self.catalog(partition=partition, extended=7)
                record = next(row for row in catalog['records'] if row['kind'] == 'transition')
                before = deepcopy((catalog, self.project.imports, self.project.overrides, self.project.undo_stack))
                report = assemble(self.project, catalog, record['id'])
                incoming, outgoing = report['incoming'], report['outgoing']
                self.assertEqual([edge['kind'] for edge in incoming], ['script_transition_reference'])
                self.assertEqual([edge['kind'] for edge in outgoing], ['transition_destination_source'])
                proof = dict(transition_id=record['entry_layers']['transition_id'], source_record_sha256=record['source_record']['sha256'], destination_scene_id='scene://town02', extended_target=7, name_sha256=record['reference']['name_sha256'], status='encoded_named_reference', reachability='not_evaluated')
                for edge in incoming + outgoing:
                    self.assertEqual(edge['transition_reference_evidence'], proof)
                    self.assertEqual(edge['pc'], record['reference']['pc'])
                    self.assertEqual(edge['layer'], 'decoded')
                    self.assertEqual(edge['runtime_binding'], 'not_asserted')
                    self.assertEqual(edge['source_catalog_key'], catalog['source_key'])
                    self.assertEqual(edge['source_import_sha256'], digest(self.project.imports[self.scene]))
                    self.assertEqual(edge['id'], digest({key:value for key,value in edge.items() if key != 'id'}))
                legacy = assemble(self.project, catalog, record['script_id'])
                self.assertIn('encoded_scene_change', {edge['kind'] for edge in legacy['outgoing']})
                self.assertIn('script_transition_reference', {edge['kind'] for edge in legacy['outgoing']})
                destination = next(node for node in report['nodes'] if node['id'] == 'scene://town02')
                self.assertFalse(destination['available'])
                report['incoming'][0]['transition_reference_evidence']['source_record_sha256'] = 'b'*64
                self.assertEqual((catalog, self.project.imports, self.project.overrides, self.project.undo_stack), before)

    def test_unknown_name_has_only_source_edge_and_counts_once(self):
        catalog = self.catalog(name=b'Town02')
        record = next(row for row in catalog['records'] if row['kind'] == 'transition')
        report = assemble(self.project, catalog, record['id'])
        self.assertEqual(len(report['incoming']), 1)
        self.assertEqual(report['outgoing'], [])
        self.assertEqual(report['coverage']['unresolved_reference_count'], 1)
        proof = report['incoming'][0]['transition_reference_evidence']
        self.assertIsNone(proof['destination_scene_id'])
        self.assertEqual(proof['status'], 'unsupported_name_encoding')
        self.assertFalse(any('unresolved-target' in node['id'] or node['id'] == 'scene://Town02' for node in report['nodes']))

    def test_script_record_reference_and_duplicate_drift_reject(self):
        baseline = self.catalog()
        transition = next(row for row in baseline['records'] if row['kind'] == 'transition')
        mutations = [
            lambda rows: rows.remove(next(row for row in rows if row['id'] == transition['script_id'])),
            lambda rows: rows.append(deepcopy(next(row for row in rows if row['id'] == transition['script_id']))),
            lambda rows: rows.append(deepcopy(next(row for row in rows if row['kind'] == 'transition'))),
            lambda rows: next(row for row in rows if row['id'] == transition['script_id'])['source_record'].update(sha256='b'*64),
            lambda rows: next(row for row in rows if row['id'] == transition['script_id'])['source_record'].update(byte_length=128),
            lambda rows: next(row for row in rows if row['id'] == transition['script_id']).update(owner_semantic_id='scene://fixture/actors/man-p1/9999'),
            lambda rows: next(row for row in rows if row['id'] == transition['script_id']).update(status='partial'),
            lambda rows: next(row for row in rows if row['id'] == transition['script_id']).update(stop_count=1),
            lambda rows: next(row for row in rows if row['id'] == transition['script_id'])['stops'].append({'pc':5,'reason':'unknown'}),
            lambda rows: next(row for row in rows if row['id'] == transition['script_id'])['transitions'][0].update(target_scene_name='town01'),
            lambda rows: next(row for row in rows if row['id'] == transition['script_id'])['transitions'].clear(),
            lambda rows: next(row for row in rows if row['id'] == transition['script_id'])['transitions'].append(deepcopy(transition['reference'])),
            lambda rows: next(row for row in rows if row['kind'] == 'transition')['reference'].update(reachability='confirmed'),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                bad = deepcopy(baseline)
                mutation(bad['records'])
                with self.assertRaises(ProjectError):
                    assemble(self.project, bad, transition['id'])

    def test_project_memberships_and_external_destination_navigation(self):
        document = synthetic_scene()
        document['scene'] = dict(semantic_id='scene://town02', name='town02')
        document['actors'][0]['semantic_id'] = 'scene://town02/actors/man-p1/0001'
        self.project.import_metadata(document)
        self.project.active_scene = self.scene
        catalog = self.catalog(partition=2)
        transition = next(row for row in catalog['records'] if row['kind'] == 'transition')
        catalogs = {self.scene:catalog, 'scene://town02':dict(scene_id='scene://town02', source_key='b'*64, records=[], limitations=[])}
        before = deepcopy((self.project.imports, self.project.overrides, self.project.active_scene, self.project.undo_stack))
        report = assemble_project(self.project, catalogs, transition['id'])
        root = next(node for node in report['nodes'] if node['id'] == transition['id'])
        destination = next(node for node in report['nodes'] if node['id'] == 'scene://town02')
        self.assertEqual(root['scene_ids'], [self.scene])
        self.assertEqual(root['navigable_scene_ids'], [self.scene])
        self.assertEqual(destination['navigable_scene_ids'], ['scene://town02'])
        self.assertTrue(destination['available'])
        self.assertEqual(report['incoming'][0]['scene_id'], self.scene)
        self.assertEqual(report['outgoing'][0]['scene_id'], self.scene)
        self.assertEqual((self.project.imports, self.project.overrides, self.project.active_scene, self.project.undo_stack), before)


if __name__ == '__main__':
    unittest.main()
