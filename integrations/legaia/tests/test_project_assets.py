"""Project-wide memberships, detached verification and bounded metadata index."""
from contextlib import nullcontext
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from importer.core import ImportError as RetailImportError, validate_metadata_only
from sdk.project import ProjectService, ProjectError, digest
from sdk.project_assets import source_key, assemble, inspect
from test_project_workflow import synthetic_scene


class ProjectAssetsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.project = ProjectService(Path(self.tmp.name))
        self.disc = Path(self.tmp.name) / 'private-disc.bin'; self.disc.write_bytes(b'fixture')
        self.project.disc_path = str(self.disc)
        self.model = 'asset://legaia/shared-model/0000'
        self.animation = 'animation://legaia/shared/0000'
        for name in ('fixture', 'other'):
            document = synthetic_scene()
            scene = 'scene://' + name
            document['scene'] = dict(semantic_id=scene, name=name)
            document['actors'][0]['semantic_id'] = scene + '/actors/man-p1/0001'
            document['actors'][0]['model_reference']['asset_semantic_id'] = self.model
            document['assets']['models'][0]['semantic_id'] = self.model
            document['assets']['models'][0]['source_record']['scene_binding'] = name
            self.project.import_metadata(document)
        self.project.active_scene = 'scene://fixture'
        self.project.selected = 'scene://fixture/actors/man-p1/0001'
        self.catalogs = {}
        for index, scene in enumerate(sorted(self.project.imports)):
            actor = self.project.imports[scene]['actors'][0]['semantic_id']
            self.catalogs[scene] = dict(scene_id=scene, source_key=str(index + 1) * 64, limitations=[], records=[
                dict(semantic_id=self.animation, asset_kind='animation', name='Shared animation',
                     bindings=[dict(actor_semantic_id=actor, model_asset_semantic_id=self.model)], source_record={'fixture': index}),
                dict(id='texture://' + scene[8:] + '/0', kind='texture')])

    def test_authored_npc_membership_is_detached_and_distinct_from_retail(self):
        identifier='authored-actor://12345678-1234-1234-1234-123456789abc'
        scene='scene://other';donor=self.project.imports[scene]['actors'][0]['semantic_id']
        draft=dict(scene_id=scene,donor_entity_id=donor,name='Project\nNPC',position=dict(x=128,z=256))
        self.project.actor_drafts[identifier]=deepcopy(draft)
        before=deepcopy(self.project._document());history=deepcopy((self.project.undo_stack,self.project.redo_stack));report=assemble(self.project,self.catalogs)
        asset=next(row for row in report['assets'] if row['id']==identifier)
        self.assertEqual(asset['scene_ids'],[scene]);variant=asset['variants'][0]
        self.assertEqual(variant['source_import_sha256'],digest(self.project.imports[scene]))
        self.assertIsNone(variant['source_catalog_key'])
        record=variant['record'];self.assertEqual(record['layer'],'authored');self.assertTrue(record['draft'])
        self.assertEqual(record['authored'],draft);self.assertEqual(record['donor_entity_id'],donor)
        self.assertNotIn('source_record',record)
        ref=record['model_reference'];self.assertEqual(ref['source_id'],identifier);self.assertEqual(ref['target_id'],self.model)
        self.assertEqual(ref['effective_donor_id'],donor);self.assertFalse(ref['imported']);self.assertEqual(ref['runtime_binding'],'not_asserted')
        authored=next(row for row in self.project.authored_assets() if row['id']==identifier)
        self.assertEqual(authored['model_reference'],ref)
        self.assertEqual(report['coverage']['asset_count'],9);self.assertEqual(report['coverage']['membership_count'],11)
        self.assertEqual(self.project._document(),before);self.assertEqual((self.project.undo_stack,self.project.redo_stack),history)
        record['authored']['position']['x']=512;self.assertEqual(self.project.actor_drafts[identifier],draft)
        catalogs=deepcopy(self.catalogs);catalogs[scene]['records'].append(deepcopy(record))
        with self.assertRaisesRegex(ProjectError,'validated authored'):assemble(self.project,catalogs)
        self.project.actor_drafts[identifier]['scene_id']='scene://absent'
        with self.assertRaises(ProjectError):assemble(self.project,self.catalogs)

    def test_draft_model_reference_uses_retail_donor_and_keeps_unknown_explicit(self):
        p=self.project;scene=p.active_scene;donor=p.imports[scene]['actors'][0]
        identifier='authored-actor://12345678-1234-1234-1234-123456789abc'
        p.actor_drafts[identifier]=dict(scene_id=scene,donor_entity_id=donor['semantic_id'],name='NPC',position=dict(x=128,z=256))
        other=deepcopy(donor);other['semantic_id']=scene+'/actors/man-p1/0002'
        other['model_reference']['asset_semantic_id']='asset://legaia/other-model/0000'
        p.imports[scene]['actors'].append(other)
        sources={actor['semantic_id']:actor for document in p.imports.values() for actor in document['actors']}
        with patch.object(p,'appearance_source_actor',side_effect=lambda actor:other if actor==donor['semantic_id'] else sources[actor]):
            authored=next(row for row in p.authored_assets() if row['id']==identifier)
        self.assertEqual(authored['model_reference']['target_id'],self.model)
        donor['model_reference']['asset_semantic_id']=None
        self.assertIsNone(next(row for row in p.authored_assets() if row['id']==identifier)['model_reference'])
        result=assemble(p,self.catalogs)
        self.assertIsNone(next(row for row in result['assets'] if row['id']==identifier)['variants'][0]['record']['model_reference'])

    def test_navigation_independent_key_stales_for_source_and_authored_inputs(self):
        project = self.project; key = source_key(project)
        project.active_scene = 'scene://other'; project.selected = self.model
        project.undo_stack.append({'navigation': True}); project.redo_stack.append({'irrelevant': True})
        project.assets.resource_catalogs['irrelevant'] = {'cached': True}
        self.assertEqual(source_key(project), key)
        for field, replacement in [('overrides', {'actor': {'Transform': {'position': {'x': 64}}}}),
                                   ('actor_drafts', {'new': {'scene_id': 'scene://fixture'}}),
                                   ('model_overrides', {self.model: {'replacement': 'local.tmd'}}),
                                   ('texture_overrides', {'texture': {'replacement': 'local.tim'}})]:
            previous = deepcopy(getattr(project, field)); setattr(project, field, replacement)
            self.assertNotEqual(source_key(project), key); setattr(project, field, previous)
        project.imports['scene://fixture']['assets']['models'][0]['source_record']['changed'] = True
        self.assertNotEqual(source_key(project), key)
        del project.imports['scene://fixture']['assets']['models'][0]['source_record']['changed']
        self.disc.write_bytes(b'longer source fixture')
        self.assertNotEqual(source_key(project), key)

    def test_deterministic_project_memberships_keep_distinct_shared_variants(self):
        before = deepcopy(self.project.imports)
        report = assemble(self.project, self.catalogs)
        self.assertEqual(set(report), {'schema_version', 'source_key', 'project_path', 'metadata_only', 'read_only',
                                       'scenes', 'assets', 'coverage', 'limitations'})
        validate_metadata_only(report)
        self.assertEqual(report['coverage'], dict(imported_scene_count=2, available_scene_count=2,
            partial_scene_count=0, unavailable_scene_count=0, asset_count=8, membership_count=10))
        for identifier in (self.model, self.animation):
            asset = next(row for row in report['assets'] if row['id'] == identifier)
            self.assertEqual(asset['scene_ids'], sorted(self.project.imports))
            self.assertEqual(len(asset['variants']), 2)
            self.assertNotEqual(asset['variants'][0]['record'], asset['variants'][1]['record'])
            for variant in asset['variants']:
                self.assertEqual(variant['source_import_sha256'], digest(self.project.imports[variant['scene_id']]))
                self.assertEqual(variant['source_catalog_key'], None if identifier == self.model else self.catalogs[variant['scene_id']]['source_key'])
                record = variant['record']
                self.assertEqual(record['id'], identifier); self.assertEqual(record['semantic_id'], identifier)
                self.assertEqual(record['kind'], asset['kind']); self.assertEqual(record['asset_kind'], asset['kind'])
        self.assertEqual([row['record_count'] for row in report['scenes']], [5, 5])
        reordered = {scene: {**catalog, 'records': list(reversed(catalog['records']))}
                     for scene, catalog in reversed(list(self.catalogs.items()))}
        self.assertEqual(assemble(self.project, reordered), report)
        report['assets'][0]['variants'][0]['record']['name'] = 'changed'
        self.assertEqual(self.project.imports, before)

    def test_missing_and_partial_catalogs_keep_imported_records_and_explicit_coverage(self):
        catalogs = deepcopy(self.catalogs)
        catalogs['scene://fixture']['limitations'] = ['Only bounded supported records are decoded.']
        del catalogs['scene://other']
        report = assemble(self.project, catalogs, {'scene://other': {'status': 'unavailable', 'reason': 'Unsupported source table'}})
        self.assertEqual([row['status'] for row in report['scenes']], ['partial', 'unavailable'])
        self.assertEqual([row['record_count'] for row in report['scenes']], [5, 3])
        self.assertIn('Unsupported source table', report['scenes'][1]['limitations'][0])
        self.assertEqual(report['coverage']['partial_scene_count'], 1)
        self.assertEqual(report['coverage']['unavailable_scene_count'], 1)
        shared = next(row for row in report['assets'] if row['id'] == self.model)
        self.assertEqual(shared['scene_ids'], ['scene://fixture', 'scene://other'])
        self.assertEqual(assemble(self.project, {})['coverage']['unavailable_scene_count'], 2)
        explicit = assemble(self.project, catalogs, {'scene://fixture': {'status': 'available'}})
        self.assertEqual(explicit['scenes'][0]['status'], 'available')

    def test_duplicate_enrichment_requires_complete_consistent_baseline_source(self):
        catalogs = deepcopy(self.catalogs)
        scene = 'scene://fixture'
        record = deepcopy(self.project.imports[scene]['assets']['models'][0])
        record.update(asset_kind='model', kind='model', name='Verified enriched model', available=True)
        catalogs[scene]['records'].extend([record, deepcopy(record)])
        report = assemble(self.project, catalogs)
        variant = next(row for row in report['assets'] if row['id'] == self.model)['variants'][0]
        self.assertTrue(variant['record']['available']); self.assertEqual(variant['source_catalog_key'], catalogs[scene]['source_key'])
        bad = deepcopy(catalogs); bad[scene]['records'][-1]['source_record']['fixture'] = False
        with self.assertRaisesRegex(ProjectError, 'same-scene duplicate'): assemble(self.project, bad)
        bad = deepcopy(catalogs); bad[scene]['records'][-1]['kind'] = bad[scene]['records'][-1]['asset_kind'] = 'texture'
        with self.assertRaisesRegex(ProjectError, 'duplicate'): assemble(self.project, bad)
        bad = deepcopy(catalogs); del bad[scene]['records'][-1]['source_record']
        with self.assertRaisesRegex(ProjectError, 'duplicate'): assemble(self.project, bad)
        bad = deepcopy(self.catalogs); bad['scene://other']['records'][0]['asset_kind'] = 'texture'
        with self.assertRaisesRegex(ProjectError, 'conflicting kinds'): assemble(self.project, bad)

    def test_retail_tmd_model_family_normalizes_without_losing_source_structure(self):
        for document in self.project.imports.values():
            document['assets']['models'][0]['asset_kind'] = 'tmd_model'
        report = assemble(self.project, self.catalogs)
        asset = next(row for row in report['assets'] if row['id'] == self.model)
        self.assertEqual(asset['kind'], 'model')
        for variant in asset['variants']:
            self.assertEqual(variant['record']['kind'], 'model')
            self.assertEqual(variant['record']['asset_kind'], 'model')
            self.assertEqual(variant['record']['source_asset_kind'], 'tmd_model')
            self.assertEqual(variant['record']['source_record'],
                             self.project.imports[variant['scene_id']]['assets']['models'][0]['source_record'])
        self.assertTrue(all(document['assets']['models'][0]['asset_kind'] == 'tmd_model'
                            for document in self.project.imports.values()))
        # Encoded families are normalized only from qualified imported models.
        bad = deepcopy(self.catalogs); bad['scene://fixture']['records'][0]['asset_kind'] = 'tmd_model'
        with self.assertRaises(ProjectError): assemble(self.project, bad)

    def test_malformed_catalogs_metadata_and_budget_failures_are_explicit(self):
        for field, value in [('scene_id', 'scene://wrong'), ('source_key', 'bad'), ('source_key', 'F' * 64), ('records', {})]:
            catalogs = deepcopy(self.catalogs); catalogs['scene://fixture'][field] = value
            with self.assertRaises(ProjectError): assemble(self.project, catalogs)
        for record in [dict(id='bad', kind='texture'), dict(id='texture://id', semantic_id='texture://else', kind='texture'),
                       dict(id='texture://id', kind='unknown'), dict(id='texture://id', kind='texture', payload=b'private')]:
            catalogs = deepcopy(self.catalogs); catalogs['scene://fixture']['records'].append(record)
            with self.assertRaises(ProjectError): assemble(self.project, catalogs)
        with self.assertRaises(ProjectError): assemble(self.project, self.catalogs, {'scene://other': {'source_import_sha256': 'a' * 64}})
        with self.assertRaises(ProjectError): assemble(self.project, {}, {'scene://other': {'status': 'available'}})
        with patch('sdk.project_assets.MAX_ASSETS', 6), self.assertRaisesRegex(ProjectError, 'unique asset budget'):
            assemble(self.project, self.catalogs)
        with patch('sdk.project_assets.MAX_MEMBERSHIPS', 9), self.assertRaisesRegex(ProjectError, 'membership budget'):
            assemble(self.project, self.catalogs)
        with patch('sdk.project_assets.MAX_METADATA_BYTES', 10), self.assertRaisesRegex(ProjectError, '32 MiB'):
            assemble(self.project, self.catalogs)
        with patch('sdk.project_assets.MAX_SCENES', 1), self.assertRaisesRegex(ProjectError, '64 imported scenes'):
            assemble(self.project, self.catalogs)

    def mocks(self, verify=None, refresh=None):
        return [patch('importer.pipeline._disc_context', return_value=nullcontext()),
                patch('sdk.resources._verify', side_effect=verify or (lambda view, document: None)),
                patch('sdk.resources.refresh_resource_catalog', side_effect=refresh or (lambda view: deepcopy(self.catalogs[view.active_scene])))]

    def test_detached_discovery_verifies_every_scene_before_decode_and_preserves_state(self):
        self.project.assets.resource_catalogs = {'sentinel': {'keep': []}}
        self.project.assets.material_reference_catalogs = {'sentinel': {'keep': []}}
        before = deepcopy(vars(self.project)); events = []
        def verify(view, document):
            events.append(('verify', document['scene']['semantic_id']))
            self.assertIsNot(view, self.project)
        def refresh(view):
            events.append(('decode', view.active_scene))
            self.assertIsNot(view.assets, self.project.assets)
            self.assertEqual(view.assets.records, {}); self.assertNotIn('sentinel', view.assets.resource_catalogs)
            view.selected = 'scratch'; view.undo_stack.append({'scratch': True}); view.scene_views['scratch'] = []
            view.assets.resource_catalogs[view.active_scene] = {'scratch': True}
            return deepcopy(self.catalogs[view.active_scene])
        mocks = self.mocks(verify, refresh)
        with mocks[0], mocks[1], mocks[2]: report = inspect(self.project)
        self.assertEqual(events[:2], [('verify', 'scene://fixture'), ('verify', 'scene://other')])
        self.assertEqual(report['source_key'], source_key(self.project))
        for name in before:
            if name != 'assets': self.assertEqual(getattr(self.project, name), before[name], name)
        for name in ('records', 'resource_catalogs', 'material_reference_catalogs'):
            self.assertEqual(getattr(self.project.assets, name), getattr(before['assets'], name))
        # Discovery does not need an active scene and its index key is stable.
        self.project.active_scene = None; self.project.selected = None
        mocks = self.mocks()
        with mocks[0], mocks[1], mocks[2]: self.assertEqual(inspect(self.project), report)

    def test_expected_availability_failures_and_stale_or_unexpected_errors(self):
        def unavailable(view):
            if view.active_scene == 'scene://other': raise RetailImportError('Unsupported source table')
            return deepcopy(self.catalogs[view.active_scene])
        mocks = self.mocks(refresh=unavailable)
        with mocks[0], mocks[1], mocks[2]:
            self.assertEqual(inspect(self.project)['scenes'][1]['status'], 'unavailable')
        def cannot_verify(view, document):
            if document['scene']['name'] == 'other': raise RetailImportError('Unsupported verification source')
        mocks = self.mocks(verify=cannot_verify)
        with mocks[0], mocks[1], mocks[2] as decode:
            report = inspect(self.project)
            self.assertEqual(decode.call_count, 1); self.assertEqual(report['scenes'][1]['status'], 'unavailable')
        def stale(view, document): raise ProjectError('Stale imported evidence')
        mocks = self.mocks(verify=stale)
        with mocks[0], mocks[1], mocks[2] as decode, self.assertRaisesRegex(ProjectError, 'Stale'):
            inspect(self.project)
        self.assertEqual(decode.call_count, 0)
        def drift(view):
            self.project.texture_overrides['texture://new'] = {'replacement': 'changed.tim'}
            return deepcopy(self.catalogs[view.active_scene])
        mocks = self.mocks(refresh=drift)
        with mocks[0], mocks[1], mocks[2], self.assertRaisesRegex(ProjectError, 'source changed'):
            inspect(self.project)
        for error in (ProjectError('Invalid authored data'), ValueError('Broken decoder')):
            def fail(view): raise error
            mocks = self.mocks(refresh=fail)
            with mocks[0], mocks[1], mocks[2], self.assertRaises(type(error)): inspect(self.project)


if __name__ == '__main__': unittest.main()
