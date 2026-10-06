"""Read-only SDK allocation review against actual project/HTTP source evidence."""
import os
import tempfile
import unittest

from importer.animation import animation_record_ranges, decode_animation_record
from sdk.animation_allocation import prepare_record_allocation
from sdk.project import digest
from sdk.scene_preview import source_key
import test_animation_glb_workflow as workflow
from test_model_primitive_workflow import http_server


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
class AnimationAllocationWorkflow(unittest.TestCase):
    def snapshot(self, project):
        return digest(dict(overrides=project.overrides, undo=project.undo_stack,
                           redo=project.redo_stack, imports=project.imports)), {
            str(path.relative_to(project.root)): path.read_bytes()
            for path in project.root.rglob('*') if path.is_file()}

    def test_http_review_identity_effective_donor_and_zero_project_mutations(self):
        with tempfile.TemporaryDirectory() as directory:
            project = workflow.AnimationGlbWorkflow().project(directory)
            owner = 'scene://town01/actors/man-p1/0011'
            options = project.animation_authoring_options(owner)
            retail = project.animation_channel_values(owner,0,0)['retail']
            shared_x = retail['translation']['x'] ^ 1
            contribution = dict(animation_id=options['binding']['semantic_id'],
                source_record_sha256=options['binding']['source_record']['record_sha256'],
                edits=[dict(frame_index=0,object_index=0,translation={'x':shared_x})])
            project.command(dict(type='set_animation_channels',entity_id=owner,value=contribution))
            body = dict(entity_id=owner, expected_source_key=source_key(project),
                source_frame_indices=[1,0,1],
                edits=[dict(frame_index=2,object_index=0,translation={'z':123})])
            before = self.snapshot(project)
            with http_server(project) as (_,post):
                status, report = post('/api/animation-record-allocation-preview',body)
                self.assertEqual(status,200,report)
                status, same = post('/api/animation-record-allocation-preview',body)
                self.assertEqual(status,200,same)
                self.assertEqual(same,report)
                self.assertEqual(report['donor_animation_id'],contribution['animation_id'])
                self.assertEqual(report['channel_owner_entity_id'],owner)
                self.assertNotEqual(report['effective_bank_sha256'],report['retail_bank_sha256'])
                self.assertEqual(report['capabilities'],dict(review=True,apply=True,build=True,actor_assignment=False))
                self.assertFalse(report['project_changed'])
                candidate, direct = prepare_record_allocation(project,owner,body['source_frame_indices'],
                    body['edits'],body['expected_source_key'])
                self.assertEqual(direct,report)
                a,b = animation_record_ranges(candidate)[-1]
                decoded = decode_animation_record(candidate[a:b])
                self.assertEqual(decoded['frames'][1]['object_transforms'][0]['translation'][0],shared_x)
                self.assertEqual(decoded['frames'][2]['object_transforms'][0]['translation'][2],123)
                other_body = dict(body,source_frame_indices=[0,1],edits=[])
                status, other = post('/api/animation-record-allocation-preview',other_body)
                self.assertEqual(status,200,other)
                self.assertNotEqual(other['review_key'],report['review_key'])
                self.assertNotEqual(other['animation_id'],report['animation_id'])
                for bad in (dict(body,expected_source_key='0'*64), dict(body,entity_id='missing'),
                            dict(body,source_frame_indices=[True]), dict(body,edits=[{}]), dict(body,extra=1)):
                    status, _ = post('/api/animation-record-allocation-preview',bad)
                    self.assertEqual(status,400)
                self.assertEqual(self.snapshot(project),before)

    def test_assigned_clip_and_appearance_resolve_distinct_donor_witnesses(self):
        from sdk.actor_animation import review
        with tempfile.TemporaryDirectory() as directory:
            project = workflow.AnimationGlbWorkflow().project(directory, 'town0b')
            subject = 'scene://town0b/actors/man-p1/0019'
            owner = 'scene://town0b/actors/man-p1/0049'
            clip = 'animation://town0b/scene-anm/0012'
            assignment = review(project,subject,clip)
            project.command(dict(type='set_actor_animation',
                **{k:assignment[k] for k in ('entity_id','animation_asset_id','source_key','review_key')}))
            before = self.snapshot(project)
            with http_server(project) as (_,post):
                body = dict(entity_id=subject,expected_source_key=source_key(project),
                            source_frame_indices=[0,1,0],edits=[])
                status, report = post('/api/animation-record-allocation-preview',body)
                self.assertEqual(status,200,report)
                self.assertEqual(report['donor_animation_id'],clip)
                self.assertEqual(report['channel_owner_entity_id'],owner)
                self.assertEqual(report['model_source_entity_id'],subject)
                self.assertEqual(self.snapshot(project),before)
                project.command(dict(type='set_actor_appearance',entity_id=subject,donor_entity_id=owner))
                after = self.snapshot(project)
                status, _ = post('/api/animation-record-allocation-preview',body)
                self.assertEqual(status,400)
                body['expected_source_key'] = source_key(project)
                status, report = post('/api/animation-record-allocation-preview',body)
                self.assertEqual(status,200,report)
                self.assertEqual(report['channel_owner_entity_id'],owner)
                self.assertEqual(report['model_source_entity_id'],owner)
                self.assertEqual(self.snapshot(project),after)
                project.mode = 'live'
                status, _ = post('/api/animation-record-allocation-preview',body)
                self.assertEqual(status,400)
                project.mode = 'edit'
                self.assertEqual(self.snapshot(project),after)


if __name__ == '__main__':
    unittest.main()
