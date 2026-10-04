"""Persistent clip snapshots, identity retention and explicit delivery boundary."""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from uuid import uuid4

from importer.animation import animation_record_ranges
from importer.core import ImportError as RetailImportError
from importer.animation_allocation import allocate_animation_record
from sdk.animation_record_ledger import SCHEMA, compose, reconstruct, validate
from sdk.build import BuildError, build_project
from sdk.build_review import review as build_review
from sdk.project import ProjectError, ProjectService
from sdk.scene_preview import source_key
from test_animation_allocation import bank
from test_animation_glb import record
import test_animation_glb_workflow as workflow
from test_model_primitive_workflow import http_server


class AnimationLedgerValidation(unittest.TestCase):
    def fixture(self):
        owner = 'scene://town01/actors/man-p1/0011'
        asset = 'asset://town01/models/scene-tmd/0001'
        donor = record([[([0,0,0],[0,0,0])], [([1,2,3],[4,5,6])]])
        source = bank([donor])
        allocated, _ = allocate_animation_record(donor,sha256(donor).hexdigest(),[1,0,1],[])
        entry = dict(record_id=str(uuid4()),entity_id=owner,channel_owner_entity_id=owner,
            model_source_entity_id=owner,donor_animation_id='animation://town01/scene-anm/0000',
            donor_asset_id=asset,donor_record_sha256=sha256(donor).hexdigest(),
            effective_donor_record_sha256=sha256(donor).hexdigest(),donor_frame_count=2,object_count=1,
            donor_edits=[],source_frame_indices=[1,0,1],edits=[],record_sha256=sha256(allocated).hexdigest())
        ledger = dict(schema_version=SCHEMA,source_scene_id='scene://town01',source_bank_sha256=sha256(source).hexdigest(),
                      revision=1,records=[entry],removed_record_ids=[])
        project = SimpleNamespace(imports={'scene://town01':dict(scene=dict(name='town01'),actors=[dict(
            semantic_id=owner,placement_fields=dict(animation_id=1),model_reference=dict(asset_semantic_id=asset))])})
        return project,source,ledger,allocated

    def test_structural_bounds_and_tombstone_identity_reservations(self):
        project,source,ledger,allocated = self.fixture()
        accepted = validate(project,'scene://town01',ledger)
        self.assertEqual(reconstruct(source,accepted)[0]['record'],allocated)
        accepted['records'][0]['edits'].append({})
        self.assertEqual(ledger['records'][0]['edits'],[])
        for change in (lambda v:v.update(revision=True), lambda v:v.update(revision=65),
                       lambda v:v['records'].append(deepcopy(v['records'][0])),
                       lambda v:v['records'][0].update(entity_id=[]),
                       lambda v:v['records'][0].update(source_frame_indices=[True]),
                       lambda v:v['records'][0].update(edits=[dict(frame_index=0,object_index=0,rotation_psx={'x':1})]),
                       lambda v:v.update(removed_record_ids=[str(uuid4())])):
            bad = deepcopy(ledger); change(bad)
            with self.assertRaises(ProjectError): validate(project,'scene://town01',bad)
        retired = deepcopy(ledger)
        retired['removed_record_ids'] = [ledger['records'][0]['record_id']]
        validate(project,'scene://town01',retired)
        self.assertEqual(reconstruct(source,retired),[])
        retired['records'].append(deepcopy(retired['records'][0]))
        with self.assertRaisesRegex(ProjectError,'Duplicate'): validate(project,'scene://town01',retired)
        oversized = deepcopy(ledger)
        oversized['records'][0].update(object_count=64,source_frame_indices=[0]*65)
        with self.assertRaisesRegex(ProjectError,'cumulative'): validate(project,'scene://town01',oversized)

    def test_wire_replay_rejects_valid_looking_changed_hashes_and_donor_capture(self):
        project,source,ledger,_ = self.fixture()
        for key in ('source_bank_sha256','donor_record_sha256','effective_donor_record_sha256','record_sha256'):
            bad = deepcopy(ledger)
            target = bad if key == 'source_bank_sha256' else bad['records'][0]
            target[key] = 'f'*64
            validate(project,'scene://town01',bad)  # Offline metadata validation has no disc proof.
            with self.assertRaises((ProjectError,RetailImportError)): reconstruct(source,bad)
        bad = deepcopy(ledger)
        bad['records'][0]['donor_edits'] = [dict(frame_index=0,object_index=0,translation={'x':1})]
        with self.assertRaisesRegex(ProjectError,'captured donor hash'): reconstruct(source,bad)


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class AnimationLedgerWorkflow(unittest.TestCase):
    def allocation(self,post,project,frames):
        body = dict(entity_id='scene://town01/actors/man-p1/0011',source_frame_indices=frames,
                    edits=[],expected_source_key=source_key(project))
        status,report = post('/api/animation-record-allocation-preview',body)
        self.assertEqual(status,200,report)
        return body,report

    def clips(self,project):
        candidate,audit = compose(project,'scene://town01')
        ranges = animation_record_ranges(candidate)
        clips = {row['record_id']:candidate[ranges[row['record_index']][0]:ranges[row['record_index']][1]]
                 for row in audit['allocated_records']}
        return candidate,clips

    def test_review_apply_history_frozen_donor_save_offline_open_and_build_blocker(self):
        with tempfile.TemporaryDirectory() as directory:
            project = workflow.AnimationGlbWorkflow().project(directory)
            owner = 'scene://town01/actors/man-p1/0011'
            options = project.animation_authoring_options(owner)
            retail = project.animation_channel_values(owner,0,0)['retail']['translation']['x']
            def channels(value):
                return dict(animation_id=options['binding']['semantic_id'],
                    source_record_sha256=options['binding']['source_record']['record_sha256'],
                    edits=[dict(frame_index=0,object_index=0,translation={'x':value})])
            project.command(dict(type='set_animation_channels',entity_id=owner,value=channels(retail^1)))
            with http_server(project) as (_,post):
                body,report = self.allocation(post,project,[1,0,1])
                before = deepcopy(project.overrides); count = len(project.undo_stack)
                status,_ = post('/api/animation-record-allocation',dict(body,review_key='0'*64))
                self.assertEqual(status,400)
                self.assertEqual(project.overrides,before)
                status,state = post('/api/animation-record-allocation',dict(body,review_key=report['review_key']))
                self.assertEqual(status,200,state)
                self.assertEqual(len(project.undo_stack),count+1)
                ledger = deepcopy(project.overrides['scene://town01']['AnimationRecords'])
                identity = ledger['records'][0]['record_id']
                candidate,clips = self.clips(project)
                self.assertEqual(sha256(candidate).hexdigest(),report['candidate_bank_sha256'])
                snapshot = clips[identity]
                self.assertEqual(ledger['records'][0]['record_sha256'],sha256(snapshot).hexdigest())
                self.assertTrue(any('AnimationRecords' in row['authored'] for row in project.authored_assets()))
                self.assertTrue(any(row['component'] == 'AnimationRecords' for row in project.component_reviews('scene://town01')))
                project.undo(); self.assertEqual(project.overrides,before)
                project.redo(); self.assertEqual(project.overrides['scene://town01']['AnimationRecords'],ledger)
                status,_ = post('/api/animation-record-allocation',dict(body,review_key=report['review_key']))
                self.assertEqual(status,400,'old source key is stale after Apply')
            project.command(dict(type='set_animation_channels',entity_id=owner,value=channels(retail^3)))
            self.assertEqual(self.clips(project)[1][identity],snapshot)
            project.command(dict(type='clear_animation_channels',entity_id=owner))
            self.assertEqual(self.clips(project)[1][identity],snapshot)
            path = project.save()
            reopened = ProjectService.open(path)
            self.assertEqual(reopened.overrides['scene://town01']['AnimationRecords'],ledger)
            self.assertEqual(self.clips(reopened)[1][identity],snapshot)
            saved = path.read_bytes()
            raw = json.loads(saved)
            raw['retail_source']['disc_path'] = str(Path(directory)/'missing-disc.bin')
            path.write_text(json.dumps(raw),encoding='utf-8')
            offline = ProjectService.open(path)
            self.assertEqual(offline.overrides['scene://town01']['AnimationRecords'],ledger)
            path.write_bytes(saved)
            files = {str(p.relative_to(project.root)):p.read_bytes() for p in project.root.rglob('*') if p.is_file()}
            assessment = build_review(reopened)
            self.assertFalse(assessment['normal_build_ready'])
            self.assertIn('bank descriptor/carrier relocation',assessment['blockers'][0]['message'])
            with self.assertRaisesRegex(BuildError,'bank descriptor/carrier relocation'): build_project(reopened)
            self.assertEqual(files,{str(p.relative_to(project.root)):p.read_bytes() for p in project.root.rglob('*') if p.is_file()})
            malformed = json.loads(saved)
            malformed['authored']['scene://town01']['AnimationRecords']['records'].append(deepcopy(ledger['records'][0]))
            path.write_text(json.dumps(malformed),encoding='utf-8')
            with self.assertRaisesRegex(ProjectError,'Duplicate'): ProjectService.open(path)
            path.write_bytes(saved)

    def test_multiple_clips_retirement_restore_keep_identities_and_rebase_only_native_ordinals(self):
        with tempfile.TemporaryDirectory() as directory:
            project = workflow.AnimationGlbWorkflow().project(directory)
            with http_server(project) as (_,post):
                identities = []
                for frames in ([0,1],[1,0,1]):
                    body,report = self.allocation(post,project,frames)
                    status,state = post('/api/animation-record-allocation',dict(body,review_key=report['review_key']))
                    self.assertEqual(status,200,state)
                    identities.append(report['allocation']['allocated_records'][0]['record_id'])
                original,clips = self.clips(project)
                self.assertEqual(len(animation_record_ranges(original)),71)
                first,second = identities
                body = dict(scene_id='scene://town01',record_id=first,active=False,expected_source_key=source_key(project))
                count = len(project.undo_stack)
                status,report = post('/api/animation-record-activation-preview',body)
                self.assertEqual(status,200,report)
                self.assertEqual(len(project.undo_stack),count)
                status,_ = post('/api/animation-record-activation',dict(body,review_key='0'*64))
                self.assertEqual(status,400)
                status,state = post('/api/animation-record-activation',dict(body,review_key=report['review_key']))
                self.assertEqual(status,200,state)
                self.assertEqual(len(project.undo_stack),count+1)
                candidate,retained = self.clips(project)
                self.assertEqual(len(animation_record_ranges(candidate)),70)
                self.assertEqual(retained,{second:clips[second]})
                ledger = project.overrides['scene://town01']['AnimationRecords']
                self.assertEqual([row['record_id'] for row in ledger['records']],identities)
                self.assertEqual(ledger['removed_record_ids'],[first])
                project.undo(); self.assertEqual(self.clips(project)[0],original)
                project.redo(); self.assertEqual(self.clips(project)[1],retained)
                project.save(); reopened = ProjectService.open(project.root)
                self.assertEqual(self.clips(reopened)[1],retained)
                body = dict(body,active=True,expected_source_key=source_key(project))
                status,report = post('/api/animation-record-activation-preview',body)
                self.assertEqual(status,200,report)
                status,state = post('/api/animation-record-activation',dict(body,review_key=report['review_key']))
                self.assertEqual(status,200,state)
                self.assertEqual(self.clips(project)[0],original)
                self.assertEqual(project.overrides['scene://town01']['AnimationRecords']['removed_record_ids'],[])
                status,_ = post('/api/animation-record-activation-preview',dict(body,active=1,expected_source_key=source_key(project)))
                self.assertEqual(status,400)


if __name__ == '__main__': unittest.main()
