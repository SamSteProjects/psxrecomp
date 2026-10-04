"""Retail expanded ANM banks survive normal Build and independent package readback."""
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
import tomllib
import unittest
from unittest.mock import patch
import zipfile
from types import SimpleNamespace

from importer.animation import animation_record_ranges
from importer.core import parse_scene_assets,decompress_lzs
from importer.disc_relocation_package import decode_relocation_package
from importer.model_pack_archive import _archive
from sdk.animation_allocation import prepare_record_allocation,prepare_record_activation
from sdk.animation_record_ledger import compose
from sdk.build import build_project,BuildError
from sdk.project import ProjectError
from sdk.scene_preview import source_key
import test_animation_glb_workflow as workflow


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class AnimationGrowthBuild(unittest.TestCase):
    def test_normal_package_delivers_active_captures_and_current_shared_channels(self):
        with tempfile.TemporaryDirectory() as directory:
            project=workflow.AnimationGlbWorkflow().project(directory);owner='scene://town01/actors/man-p1/0011'
            ids=[]
            for sequence in ([1,0,1],[0,1,2,2,1,0]):
                key=source_key(project);_,review=prepare_record_allocation(project,owner,sequence,[],key)
                project.command(dict(type='allocate_animation_record',entity_id=owner,source_frame_indices=sequence,
                    edits=[],expected_source_key=key,review_key=review['review_key']))
                ids.append(review['proposed_ledger']['records'][-1]['record_id'])
            key=source_key(project);_,review=prepare_record_activation(project,project.active_scene,ids[0],False,key)
            project.command(dict(type='set_animation_record_active',scene_id=project.active_scene,
                record_id=ids[0],active=False,expected_source_key=key,review_key=review['review_key']))
            options=project.animation_authoring_options(owner);retail=project.animation_channel_values(owner,0,0)['retail']['translation']['x']
            project.command(dict(type='set_animation_channels',entity_id=owner,value=dict(
                animation_id=options['binding']['semantic_id'],source_record_sha256=options['binding']['source_record']['record_sha256'],
                edits=[dict(frame_index=0,object_index=0,translation={'x':retail^1})])))
            expected,allocation=compose(project,project.active_scene)
            metadata=project.save().read_bytes();overrides=json.dumps(project.overrides,sort_keys=True)
            build=build_project(project)
            audit=json.loads(Path(build['audit']).read_text(encoding='utf-8'))
            self.assertTrue(audit['validation']['allocated_animation_bank_readback'])
            self.assertTrue(audit['validation']['lz_decode_round_trip'])
            self.assertEqual(audit['animation_growth']['carriers'][0]['active_records'][0]['record_id'],ids[1])
            self.assertFalse(audit['animation_growth']['carriers'][0]['runtime_assigned'])
            self.assertEqual(audit['overlays'],[],'shared bank edits must be composed once, not separately patched')
            with zipfile.ZipFile(build['path']) as package:
                manifest=tomllib.loads(package.read('manifest.toml').decode('utf-8'))
                self.assertEqual(manifest['format_version'],7)
                entry=manifest['disc_relocation'][0]
                decoded=decode_relocation_package(package.read(entry['file']),entry['sha256'])
            carrier_audit=audit['animation_growth']['carriers'][0]
            archive=_archive(decoded['replacement']);carrier=archive.read_entry(archive.entry(carrier_audit['entry_index']))
            offset=carrier_audit['table_offset'];descriptor=parse_scene_assets(carrier,0,offset).descriptors[carrier_audit['descriptor_index']]
            delivered,_=decompress_lzs(carrier[offset+descriptor.data_offset:],descriptor.size)
            self.assertEqual(delivered,expected)
            self.assertEqual(len(animation_record_ranges(delivered)),70)
            start,end=animation_record_ranges(delivered)[-1]
            self.assertEqual(sha256(delivered[start:end]).hexdigest(),project.overrides[project.active_scene]['AnimationRecords']['records'][1]['record_sha256'])
            self.assertEqual(metadata,(project.root/'project.legaia.json').read_bytes())
            self.assertEqual(overrides,json.dumps(project.overrides,sort_keys=True))
            unsupported=SimpleNamespace(source_bank=lambda:(b'',{'source_kind':'raw_streaming_anm'}))
            rejected=project.root/'RejectedStreamingBuild'
            with patch('sdk.animation_growth.verified_source',return_value=(b'',unsupported)):
                with self.assertRaisesRegex((ProjectError,BuildError),'raw chunk relocation'):
                    build_project(project,rejected)
            self.assertFalse(rejected.exists(),'unsupported carrier must not write a partial package')


if __name__=='__main__':unittest.main()
