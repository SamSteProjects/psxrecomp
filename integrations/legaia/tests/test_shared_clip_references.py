"""Pinned shared model/clip metadata is evidence, never an actor playback claim."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from importer.pipeline import REFERENCE_COMMIT,REFERENCE_REPOSITORY
from unittest.mock import patch
from sdk.asset_references import assemble,assemble_project
from sdk.project import ProjectError,ProjectService,digest
from test_project_workflow import synthetic_scene


def shared_clip(slot=0,clip='idle'):
    index=slot*7+(clip=='idle') if slot<3 else slot+18
    model=f'asset://legaia/models/global-special/{0xf0+slot:04x}'
    identity=f'animation://legaia/field-locomotion/{index:04d}'
    channels=10 if slot<3 else 3 if slot==3 else 2
    source=dict(disc=dict(sha256='a'*64,serial='SCUS-94254'),iso_file='PROT.DAT',prot_entry_index=874,
                container_section=1,compressed_stream_offset=120000,compressed_bytes_consumed=70000,
                record_index=index,byte_offset=96+index*512,byte_length=16+6*channels*8,
                byte_coordinate_space='decoded_lzs_section',containing_size=65536)
    return dict(id=identity,semantic_id=identity,kind='animation',asset_kind='animation',scope='global-field',
                association_kind='reference_pinned_global_model_clip',reference_commit=REFERENCE_COMMIT,
                preview=dict(asset_id=model,clip_id=clip),asset_semantic_ids=[model],bindings=[],
                runtime_state='not_observed',record_index=index,frame_count=6,bone_count=channels,
                channel_count=channels,source_record=source)


def shared_model(slot=0):
    source=dict(disc=dict(sha256='a'*64,serial='SCUS-94254'),iso_file='PROT.DAT',
                prot_entry_index=874,container_section=0,pack_slot=slot)
    return dict(semantic_id=f'asset://legaia/models/global-special/{0xf0+slot:04x}',asset_kind='tmd_model',
                claims=[dict(property='source_record',value=deepcopy(source),source=deepcopy(source),confidence='confirmed',evidence=[dict(kind='parser_span',source=REFERENCE_REPOSITORY,
                             commit=REFERENCE_COMMIT,locator='crates/asset/src/character_pack.rs::parse',
                             observation='bounded TMD record in the structurally ordered model pool')])],
                source_record=source)


class SharedClipReferences(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.project=ProjectService(Path(temporary.name))
        document=synthetic_scene();document['assets']['models']+=[shared_model(slot) for slot in range(5)]
        self.project.import_metadata(document)
        self.record=shared_clip();self.clip=self.record['id'];self.model=self.record['preview']['asset_id']
        self.catalog=dict(source_key='b'*64,scene_id=self.project.active_scene,records=[self.record],limitations=[])

    def test_active_shared_edge_carries_exact_detached_source_evidence(self):
        before=deepcopy((self.project.imports,self.project.overrides,self.project.actor_drafts,self.project.undo_stack,self.catalog))
        report=assemble(self.project,self.catalog,self.clip)
        self.assertEqual(report['incoming'],[]);self.assertEqual(len(report['outgoing']),1)
        edge=report['outgoing'][0]
        self.assertEqual(edge['kind'],'reference_pinned_model_clip')
        self.assertEqual(edge['source_id'],self.clip);self.assertEqual(edge['target_id'],self.model)
        self.assertEqual(edge['layer'],'decoded');self.assertEqual(edge['runtime_binding'],'not_asserted')
        self.assertEqual(edge['source_catalog_key'],'b'*64)
        self.assertEqual(edge['source_import_sha256'],digest(self.project.imports[self.project.active_scene]))
        self.assertEqual(edge['reference_clip_evidence'],dict(reference_commit=REFERENCE_COMMIT,model_id=self.model,
            clip_id='idle',record_index=1,frame_count=6,channel_count=10,source_record=self.record['source_record']))
        self.assertEqual(edge['id'],digest({key:value for key,value in edge.items() if key!='id'}))
        self.assertEqual(len([edge for edge in assemble(self.project,self.catalog,self.model)['incoming'] if edge['kind']=='reference_pinned_model_clip']),1)
        edge['reference_clip_evidence']['source_record']['disc']['sha256']='changed'
        self.assertEqual(before,(self.project.imports,self.project.overrides,self.project.actor_drafts,self.project.undo_stack,self.catalog))

    def test_all_eight_pinned_pairs_have_their_own_model_and_record(self):
        records=[shared_clip(slot,clip) for slot in range(5) for clip in (('idle','walk') if slot<3 else ('loop',))]
        self.catalog['records']=records
        self.assertEqual(sorted(row['record_index'] for row in records),[0,1,7,8,14,15,21,22])
        for record in records:
            with self.subTest(model=record['preview']['asset_id'],clip=record['preview']['clip_id']):
                edge=assemble(self.project,self.catalog,record['id'])['outgoing'][0]
                self.assertEqual(edge['target_id'],record['preview']['asset_id'])
                self.assertEqual(edge['reference_clip_evidence']['clip_id'],record['preview']['clip_id'])
                self.assertEqual(edge['reference_clip_evidence']['record_index'],record['record_index'])

    def test_project_shared_identity_has_distinct_scene_qualified_links(self):
        document=deepcopy(self.project.imports[self.project.active_scene]);document['scene']=dict(semantic_id='scene://other',name='other')
        document['actors'][0]['semantic_id']='scene://other/actors/man-p1/0001';self.project.import_metadata(document)
        self.project.active_scene='scene://fixture'
        catalogs={scene:dict(deepcopy(self.catalog),scene_id=scene,source_key=str(index+1)*64) for index,scene in enumerate(sorted(self.project.imports))}
        before=deepcopy((self.project.imports,self.project.active_scene,self.project.selected,self.project.undo_stack,catalogs))
        report=assemble_project(self.project,catalogs,self.clip)
        self.assertEqual(report['incoming'],[]);self.assertEqual(len(report['outgoing']),2)
        self.assertEqual({edge['scene_id'] for edge in report['outgoing']},set(self.project.imports))
        self.assertEqual(len({edge['id'] for edge in report['outgoing']}),2)
        self.assertEqual(next(node for node in report['nodes'] if node['id']==self.clip)['scene_ids'],sorted(self.project.imports))
        for edge in report['outgoing']:
            self.assertEqual(edge['source_catalog_key'],catalogs[edge['scene_id']]['source_key'])
            self.assertEqual(edge['source_import_sha256'],digest(self.project.imports[edge['scene_id']]))
            self.assertEqual(edge['reference_clip_evidence']['source_record'],self.record['source_record'])
        report['outgoing'][0]['reference_clip_evidence']['source_record']['disc']['serial']='changed'
        self.assertEqual(before,(self.project.imports,self.project.active_scene,self.project.selected,self.project.undo_stack,catalogs))

    def test_missing_model_is_unresolved_without_inventing_a_node(self):
        self.project.imports[self.project.active_scene]['assets']['models']=[item for item in self.project.imports[self.project.active_scene]['assets']['models'] if item['semantic_id']!=self.model]
        report=assemble(self.project,self.catalog,self.clip)
        self.assertEqual(report['outgoing'],[]);self.assertEqual(report['coverage']['unresolved_reference_count'],1)
        self.assertNotIn(self.model,{node['id'] for node in report['nodes']})
        project_report=assemble_project(self.project,{self.project.active_scene:self.catalog},self.clip)
        self.assertEqual(project_report['outgoing'],[]);self.assertEqual(project_report['coverage']['unresolved_reference_count'],1)

    def test_shared_model_usage_and_donors_do_not_invent_actor_clip_bindings(self):
        actor=self.project.imports[self.project.active_scene]['actors'][0]
        actor['model_reference']['asset_semantic_id']=self.model
        second=deepcopy(actor);second['semantic_id']=actor['semantic_id'][:-1]+'2'
        self.project.imports[self.project.active_scene]['actors'].append(second)
        self.project.overrides[second['semantic_id']]={'ActorAppearance':dict(donor_entity_id=actor['semantic_id'])}
        self.project.actor_drafts['draft://fixture/shared']=dict(scene_id=self.project.active_scene,name='Shared draft',donor_entity_id=actor['semantic_id'])
        refs=[dict(source_id=identity,target_id=self.model,scene_id=self.project.active_scene,imported=identity==actor['semantic_id'],
                   effective=True,effective_donor_id=actor['semantic_id'],kind='draft_initial_model_assignment' if identity.startswith('draft://') else 'initial_model_assignment')
              for identity in (actor['semantic_id'],second['semantic_id'],'draft://fixture/shared')]
        # A global model donor is not an editable scene-local appearance donor;
        # exercise the graph's explicit effective model references independently.
        with patch.object(self.project,'model_references',return_value=refs):
            self.assertEqual(assemble(self.project,self.catalog,self.clip)['incoming'],[])
            for identity in (actor['semantic_id'],second['semantic_id'],'draft://fixture/shared'):
                report=assemble(self.project,self.catalog,identity)
                self.assertFalse(any('animation_binding' in edge['kind'] for edge in report['outgoing']))

    def test_unflagged_animation_is_excluded_and_existing_bindings_still_work(self):
        self.record.pop('association_kind')
        self.assertEqual(assemble(self.project,self.catalog,self.clip)['outgoing'],[])
        actor=self.project.imports[self.project.active_scene]['actors'][0]['semantic_id']
        self.record['bindings']=[dict(actor_semantic_id=actor,model_asset_semantic_id=self.model,initial_animation_id=2)]
        report=assemble(self.project,self.catalog,self.clip)
        self.assertEqual({edge['kind'] for edge in report['incoming']},{'initial_animation_binding'})
        self.assertEqual({edge['kind'] for edge in report['outgoing']},{'recorded_model_clip_binding'})

    def test_declared_association_rejects_malformed_pin_scope_model_and_clip(self):
        changes=[dict(reference_commit='0'*40),dict(scope='scene'),dict(kind='texture'),dict(asset_kind='texture'),
                 dict(runtime_state='playing'),dict(bindings=[{}]),dict(actor_semantic_ids=['scene://fixture/actor']),
                 dict(preview=dict(asset_id=self.model,clip_id='run')),dict(preview=dict(asset_id=self.model,clip_id='idle',actor_id='actor')),
                 dict(preview=dict(asset_id='asset://missing',clip_id='idle')),dict(asset_semantic_ids=[]),
                 dict(asset_semantic_ids=[self.model,self.model]),dict(id='animation://legaia/field-locomotion/0000'),
                 dict(semantic_id='animation://legaia/field-locomotion/0000'),dict(record_index=0),dict(record_index=True)]
        for change in changes:
            with self.subTest(change=change):
                record=dict(deepcopy(self.record),**change)
                with self.assertRaisesRegex(ProjectError,'reference-pinned'):assemble(self.project,dict(self.catalog,records=[record]),self.clip)

    def test_declared_association_rejects_counts_and_decoded_record_length(self):
        changes=[dict(frame_count=0),dict(frame_count=513),dict(frame_count=True),dict(channel_count=3),
                 dict(channel_count=True),dict(bone_count=9),dict(bone_count=True)]
        for change in changes:
            with self.subTest(change=change):
                record=dict(deepcopy(self.record),**change)
                with self.assertRaisesRegex(ProjectError,'decoded counts'):assemble(self.project,dict(self.catalog,records=[record]),self.clip)
        record=deepcopy(self.record);record['source_record']['byte_length']+=8
        with self.assertRaisesRegex(ProjectError,'source bounds'):assemble(self.project,dict(self.catalog,records=[record]),self.clip)

    def test_declared_association_rejects_malformed_source_locators_and_payload(self):
        changes=[dict(iso_file='OTHER.DAT'),dict(prot_entry_index=875),dict(prot_entry_index=True),dict(container_section=0),
                 dict(container_section=True),dict(record_index=0),dict(record_index=True),dict(byte_coordinate_space='prot_entry'),
                 dict(byte_offset=95),dict(byte_offset=True),dict(byte_length=True),dict(containing_size=100),
                 dict(containing_size=4*1024*1024+1),dict(compressed_stream_offset=-1),dict(compressed_stream_offset=True),
                 dict(compressed_stream_offset=0xffffffff),dict(compressed_bytes_consumed=0),dict(compressed_bytes_consumed=True),
                 dict(compressed_bytes_consumed=0x100000000),dict(payload=b'private')]
        for change in changes:
            with self.subTest(change=change):
                record=deepcopy(self.record);record['source_record'].update(change)
                with self.assertRaisesRegex(ProjectError,'reference-pinned'):assemble(self.project,dict(self.catalog,records=[record]),self.clip)
        for disc in [dict(sha256='A'*64,serial='SCUS-94254'),dict(sha256='a'*63,serial='SCUS-94254'),
                     dict(sha256='a'*64,serial='OTHER'),dict(sha256='a'*64,serial='SCUS-94254',payload='private')]:
            record=deepcopy(self.record);record['source_record']['disc']=disc
            with self.subTest(disc=disc),self.assertRaisesRegex(ProjectError,'disc identity'):
                assemble(self.project,dict(self.catalog,records=[record]),self.clip)
        record=deepcopy(self.record);record['source_record'].pop('compressed_bytes_consumed')
        with self.assertRaisesRegex(ProjectError,'source metadata'):assemble(self.project,dict(self.catalog,records=[record]),self.clip)

    def test_declared_association_requires_existing_model_provenance_to_agree(self):
        model=next(item for item in self.project.imports[self.project.active_scene]['assets']['models'] if item['semantic_id']==self.model)
        for key,value in [('prot_entry_index',875),('container_section',1),('container_section',False),('pack_slot',1),('iso_file','OTHER.DAT'),('disc',dict(sha256='b'*64,serial='SCUS-94254'))]:
            previous=deepcopy(model['source_record']);model['source_record'][key]=value
            with self.subTest(key=key),self.assertRaisesRegex(ProjectError,'imported model provenance'):
                assemble(self.project,self.catalog,self.clip)
            model['source_record']=previous
        model['reference_commit']='0'*40
        with self.assertRaisesRegex(ProjectError,'imported model provenance'):assemble(self.project,self.catalog,self.clip)
        model.pop('reference_commit')
        model['claims'][0]['evidence'][0]['commit']='0'*40
        with self.assertRaisesRegex(ProjectError,'imported model reference pin'):assemble(self.project,self.catalog,self.clip)


if __name__=='__main__':unittest.main()
