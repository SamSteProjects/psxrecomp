"""Retail raw ANM allocation reaches normal format-7 Build with exact MAN bytes."""
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
import tomllib
import unittest
import zipfile
from importer.disc_relocation_package import decode_relocation_package
from importer.model_pack_archive import _archive
from importer.streaming_man import streaming_chunks
from importer.core import parse_man
from sdk.animation_allocation import prepare_record_allocation,record_library
from sdk.allocated_animation_assignment import review as assignment_review
from sdk.animation_record_ledger import compose
from sdk.scene_preview import source_key
from sdk.build import build_project
from sdk.build_review import review as build_review
import test_streaming_normal_build as workflow


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class StreamingAnimationGrowthBuild(unittest.TestCase):
    def test_raw_bank_frozen_capture_shared_axes_assigned_header_and_placement(self):
        with tempfile.TemporaryDirectory() as directory:
            project=workflow.StreamingNormalBuild().project(directory);scene=project.active_scene
            owner='scene://dolk2/actors/man-p1/0001';other='scene://dolk2/actors/man-p1/0011'
            key=source_key(project);_,allocation=prepare_record_allocation(project,owner,[0,0,0],[],key)
            self.assertTrue(allocation['capabilities']['build'])
            project.command(dict(type='allocate_animation_record',entity_id=owner,source_frame_indices=[0,0,0],edits=[],expected_source_key=key,review_key=allocation['review_key']))
            record=allocation['proposed_ledger']['records'][0]['record_id']
            options=project.animation_authoring_options(owner);value=project.animation_channel_values(owner,0,0)['retail']['translation']['x']^1
            project.command(dict(type='set_animation_channels',entity_id=owner,value=dict(animation_id=options['binding']['semantic_id'],source_record_sha256=options['binding']['source_record']['record_sha256'],edits=[dict(frame_index=0,object_index=0,translation={'x':value})])))
            request=dict(entity_id=owner,record_id=record,expected_source_key=source_key(project));assignment=assignment_review(project,**request)
            self.assertTrue(assignment['capabilities']['build_assignment'])
            project.command(dict(type='set_actor_allocated_animation',**request,review_key=assignment['review_key']))
            carrier,_,_=workflow.StreamingNormalBuild().source(project);baseline=carrier.payload
            position=parse_man(baseline,'dolk2').actors[10].world_x+64
            project.overrides[other]=dict(Transform=dict(position=dict(x=position)))
            expected,_=compose(project,scene);library=record_library(project,scene,source_key(project));self.assertTrue(library['build_available'])
            assessed=build_review(project);self.assertTrue(assessed['normal_build_ready'],assessed['blockers'])
            result=build_project(project);audit=json.loads(Path(result['audit']).read_text(encoding='utf-8'))
            self.assertTrue(audit['validation']['allocated_animation_bank_readback']);self.assertTrue(audit['validation']['allocated_initial_MAN_header_readback'])
            with zipfile.ZipFile(result['path']) as package:
                manifest=tomllib.loads(package.read('manifest.toml').decode());self.assertEqual(manifest['format_version'],7)
                self.assertNotIn('overlay',manifest);self.assertEqual(len(manifest['disc_relocation']),1)
                row=manifest['disc_relocation'][0];payload=decode_relocation_package(package.read(row['file']),row['sha256'])['replacement']
            resource=audit['animation_growth']['carriers'][0];self.assertEqual(resource['source_kind'],'raw_streaming_anm')
            archive=_archive(payload);raw=archive.read_entry(archive.entry(resource['entry_index']));chunks,terminated=streaming_chunks(raw);self.assertTrue(terminated)
            bank=next(c for c in chunks if c['type_byte']==5);self.assertEqual(raw[bank['header_offset']+4:bank['header_offset']+4+bank['size']],expected)
            man=next(c for c in chunks if c['type_byte']==3);emitted=raw[man['header_offset']+4:man['header_offset']+4+man['size']]
            actors=parse_man(emitted,'dolk2').actors;self.assertEqual(actors[10].world_x,position)
            self.assertEqual(actors[0].animation_id,assignment['native_animation_id'])
            self.assertEqual(sha256(emitted).hexdigest(),next(o['decoded_after_sha256'] for o in audit['overlays'] if o.get('source_kind')=='raw_streaming_man'))


if __name__=='__main__':unittest.main()
