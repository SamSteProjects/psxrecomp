"""Retail compressed NPC candidates exceeding fixed-span capacity reach normal Build."""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
import tomllib
import unittest
import zipfile
from importer.core import decompress_lzs,parse_man,parse_scene_assets,_pack_ranges
from importer.model_pack_archive import _archive
from importer.disc_relocation_package import decode_relocation_package
from sdk.build import build_project
from sdk.build_review import review
from sdk.draft_build import _prepare_draft_scene
import test_animation_glb_workflow as workflow


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class CompressedNpcGrowthBuild(unittest.TestCase):
    def test_oversized_donor_batch_review_and_exact_package_man(self):
        self._run()

    def test_oversized_donor_batch_with_allocated_animation(self):
        self._run(allocated=True)

    def test_oversized_donor_batch_with_allocated_animation_and_model_topology(self):
        self._run(allocated=True,topology=True)

    def _run(self,allocated=False,topology=False):
        with tempfile.TemporaryDirectory() as directory:
            project=workflow.AnimationGlbWorkflow().project(directory);scene=project.active_scene
            owner='scene://town01/actors/man-p1/0011'
            expected_bank=None
            if allocated:
                from sdk.animation_allocation import prepare_record_allocation
                from sdk.allocated_animation_assignment import review as assignment_review
                from sdk.animation_record_ledger import compose
                from sdk.scene_preview import source_key
                key=source_key(project);_,capture=prepare_record_allocation(project,owner,[0,1,0],[],key)
                project.command(dict(type='allocate_animation_record',entity_id=owner,source_frame_indices=[0,1,0],
                    edits=[],expected_source_key=key,review_key=capture['review_key']))
                record=capture['proposed_ledger']['records'][0]['record_id']
                options=project.animation_authoring_options(owner);value=project.animation_channel_values(owner,0,0)['retail']['translation']['x']^1
                project.command(dict(type='set_animation_channels',entity_id=owner,value=dict(
                    animation_id=options['binding']['semantic_id'],source_record_sha256=options['binding']['source_record']['record_sha256'],
                    edits=[dict(frame_index=0,object_index=0,translation={'x':value})])))
                request=dict(entity_id=owner,record_id=record,expected_source_key=source_key(project))
                assignment=assignment_review(project,**request)
                project.command(dict(type='set_actor_allocated_animation',**request,review_key=assignment['review_key']))
                expected_bank=compose(project,scene)[0]
            model_id=None
            if topology:
                from sdk.model_face_addition import source as face_source,review as face_review
                from sdk.scene_preview import source_key
                model_id=project._actor(owner)['model_reference']['asset_semantic_id']
                original=project._model_source(model_id,scene);key=source_key(project)
                info=face_source(project,model_id,key)
                face=info['topology']['faces'][0];donor=face['face_id']
                primitive=next(p for p in info['objects'][face['object_index']]['primitives'] if p['primitive_index']==face['current_primitive_index'])
                requests=[dict(face_id='face://authored/00000000-0000-4000-8000-000000000001',donor_face_id=donor,fields={'vertices':primitive['vertices']})]
                added=face_review(project,model_id,requests,sha256(original).hexdigest(),key)
                project.apply_model_face_additions(model_id,requests,sha256(original).hexdigest(),key,added['proposed_sha256'])
                expected_model=project.read_model_replacement(model_id,project.model_overrides[model_id])
                from importer.pipeline import _disc_context
                asset=next(a for a in project.imports[scene]['assets']['models'] if a['semantic_id']==model_id)
                record=asset['source_record']
                with _disc_context(project.disc_path) as (_,_,_,source_archive):
                    raw=source_archive.read_entry(source_archive.entry(record['prot_entry_index']))
                    descriptor=parse_scene_assets(raw,record['prot_entry_index']).descriptors[record['container_section']]
                    original_pack=decompress_lzs(raw[descriptor.data_offset:],descriptor.size)[0]
                slots=[i for i,(start,stop) in enumerate(_pack_ranges(original_pack)) if start==record['byte_offset'] and record['byte_length']<=stop-start]
                self.assertEqual(len(slots),1);model_slot=slots[0]
            for i in range(8):
                project.command(dict(type='create_actor_draft',donor_entity_id=owner,
                    position=dict(x=64+128*i,z=64),name=f'Deferred compressed NPC {i+1}'))
            before=deepcopy((project.overrides,project.actor_drafts,project.model_overrides,project.undo_stack))
            preparation=project
            if topology:
                from copy import copy
                preparation=copy(project);preparation.model_overrides={}
            _,prepared=_prepare_draft_scene(preparation,sorted(project.actor_drafts)[0],defer_rebuild=True,scene_id=scene,animation_growth_managed=True)
            candidate=prepared['_rebuild_request']['candidate']
            assessment=review(project);self.assertTrue(assessment['normal_build_ready'],assessment['blockers'])
            self.assertEqual(assessment['included_npc_draft_count'],8)
            self.assertFalse((Path(directory)/'Builds').exists())
            result=build_project(project);audit=json.loads(Path(result['audit']).read_text(encoding='utf-8'))
            metadata=audit['npc_candidates'][scene]
            self.assertEqual(metadata['schema_version'],'legaia.npc-compressed-growth-build.v1')
            self.assertTrue(metadata['native_growth']['original_consumed_span_exceeded'])
            self.assertFalse(metadata['gameplay_verified'])
            with zipfile.ZipFile(result['path']) as package:
                manifest=tomllib.loads(package.read('manifest.toml').decode());self.assertEqual(manifest['format_version'],7)
                self.assertNotIn('overlay',manifest)
                row=manifest['disc_relocation'][0]
                payload=decode_relocation_package(package.read(row['file']),row['sha256'])['replacement']
            request=prepared['_rebuild_request'];archive=_archive(payload)
            raw=archive.read_entry(archive.entry(request['entry_index']))
            table=parse_scene_assets(raw,request['entry_index'],request['table_offset'])
            descriptor=next(d for d in table.descriptors if d.type_byte==3 and d.size)
            emitted=decompress_lzs(raw[request['table_offset']+descriptor.data_offset:],descriptor.size)[0]
            self.assertEqual(emitted,candidate)
            self.assertEqual(len(parse_man(emitted,'town01').actors),len(project.imports[scene]['actors'])+8)
            self.assertTrue(audit['relocation']['composition']['final_compressed_man_verified'])
            if allocated:
                carrier=audit['animation_growth']['carriers'][0];raw=archive.read_entry(archive.entry(carrier['entry_index']))
                table=parse_scene_assets(raw,carrier['entry_index'],carrier['table_offset'])
                descriptor=table.descriptors[carrier['descriptor_index']]
                bank=decompress_lzs(raw[carrier['table_offset']+descriptor.data_offset:],descriptor.size)[0]
                self.assertEqual(bank,expected_bank)
                actors=parse_man(emitted,'town01').actors
                self.assertEqual(next(a for a in actors if a.record_index==11).animation_id,assignment['native_animation_id'])
                self.assertTrue(audit['validation']['allocated_initial_MAN_header_readback'])
            if topology:
                self.assertEqual(metadata['draft_audit']['managed_model_ids'],[model_id])
                self.assertEqual(audit['model_growth']['deferred_model_ids'],[model_id])
                asset=next(a for a in project.imports[scene]['assets']['models'] if a['semantic_id']==model_id)
                record=asset['source_record'];raw=archive.read_entry(archive.entry(record['prot_entry_index']))
                descriptor=parse_scene_assets(raw,record['prot_entry_index']).descriptors[record['container_section']]
                pack=decompress_lzs(raw[descriptor.data_offset:],descriptor.size)[0]
                start,_=_pack_ranges(pack)[model_slot]
                self.assertEqual(pack[start:start+len(expected_model)],expected_model)
                self.assertTrue(audit['relocation']['composition']['final_packs_verified'])
            self.assertEqual((project.overrides,project.actor_drafts,project.model_overrides,project.undo_stack),before)


if __name__=='__main__':unittest.main()
