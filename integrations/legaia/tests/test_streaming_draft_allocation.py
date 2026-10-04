"""Retail read-only raw archive composition; no physical Retail disc is exported."""
from copy import deepcopy
from hashlib import sha256
import os
from pathlib import Path
import tempfile
import unittest
from importer.model_pack_archive import _archive
from importer.streaming_man import streaming_chunks
from importer.core import parse_man
from sdk.animation_allocation import prepare_record_allocation
from sdk.allocated_animation_assignment import review as assignment_review
from sdk.animation_record_ledger import compose
from sdk.scene_preview import source_key
from sdk.draft_build import prepare_draft_archive
from sdk.streaming_build import prepare_streaming_scene
from sdk.project import ProjectError
import test_streaming_normal_build as workflow


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class StreamingDraftAllocation(unittest.TestCase):
    def test_managed_retained_assignment_npc_append_and_exact_final_raw_bank(self):
        with tempfile.TemporaryDirectory() as directory:
            project=workflow.StreamingNormalBuild().project(directory);scene=project.active_scene;owner='scene://dolk2/actors/man-p1/0001'
            key=source_key(project);_,allocation=prepare_record_allocation(project,owner,[0,0,0],[],key)
            project.command(dict(type='allocate_animation_record',entity_id=owner,source_frame_indices=[0,0,0],edits=[],expected_source_key=key,review_key=allocation['review_key']))
            record=allocation['proposed_ledger']['records'][0]['record_id']
            channel=project.animation_authoring_options(owner);value=project.animation_channel_values(owner,0,0)['retail']['translation']['x']^1
            project.command(dict(type='set_animation_channels',entity_id=owner,value=dict(animation_id=channel['binding']['semantic_id'],source_record_sha256=channel['binding']['source_record']['record_sha256'],edits=[dict(frame_index=0,object_index=0,translation={'x':value})])))
            request=dict(entity_id=owner,record_id=record,expected_source_key=source_key(project));assignment=assignment_review(project,**request)
            project.command(dict(type='set_actor_allocated_animation',**request,review_key=assignment['review_key']))
            project.command(dict(type='create_actor_draft',donor_entity_id=owner,position=dict(x=832,z=896),name='Deferred allocated donor'))
            draft=next(iter(project.actor_drafts));before=deepcopy((project.overrides,project.actor_drafts,project.undo_stack))
            with self.assertRaisesRegex(ProjectError,'managed bank delivery'):prepare_streaming_scene(project,scene)
            source,prepared=prepare_streaming_scene(project,scene,animation_growth_managed=True)
            self.assertIsNone(prepared['animation_changes']);self.assertIsNone(prepared['map_changes'])
            candidate=prepared['_rebuild_request']['candidate'];self.assertEqual(sha256(candidate).hexdigest(),prepared['final_man_sha256'])
            original_carrier,_,_=workflow.StreamingNormalBuild().source(project);original_actors=parse_man(original_carrier.payload,'dolk2').actors
            candidate_actors=parse_man(candidate,'dolk2').actors;self.assertEqual(len(candidate_actors),len(original_actors)+1)
            self.assertEqual(candidate_actors[0].animation_id,assignment['native_animation_id'])
            self.assertEqual(candidate_actors[-1].animation_id,original_actors[0].animation_id)
            expected,_=compose(project,scene);result,audit=prepare_draft_archive(project,draft)
            self.assertEqual((project.overrides,project.actor_drafts,project.undo_stack),before)
            carrier=audit['animation_growth']['carriers'][0];archive=_archive(result);raw=archive.read_entry(archive.entry(carrier['entry_index']))
            chunks,terminated=streaming_chunks(raw);self.assertTrue(terminated)
            anm=next(c for c in chunks if c['type_byte']==5);man=next(c for c in chunks if c['type_byte']==3)
            self.assertEqual(raw[anm['header_offset']+4:anm['header_offset']+4+anm['size']],expected)
            self.assertEqual(raw[man['header_offset']+4:man['header_offset']+4+man['size']],candidate)
            self.assertTrue(audit['animation_growth']['final_archive_banks'][0]['final_bank_verified'])
            self.assertEqual(audit['source_prot_sha256'],sha256(source).hexdigest())
            self.assertFalse((Path(directory)/'Builds').exists())


if __name__=='__main__':unittest.main()
