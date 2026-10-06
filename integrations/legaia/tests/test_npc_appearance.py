"""Native NPC appearance is independent of its script donor and text bytes."""
from copy import deepcopy
from hashlib import sha256
from unittest import TestCase
from importer.core import parse_man, ImportError
from importer.man_actor_structure import append_actor_donor
from sdk.npc_appearance import patch_allocated_appearance
from sdk.project import ProjectError
from test_importer_man_assignments import fixture

class NpcAppearanceTests(TestCase):
    def test_final_offsets_two_clones_and_only_initial_header_bytes_change(self):
        context,source=fixture();candidate=source;allocations={'drafts':[]}
        for identifier in ['npc-a','npc-b']:
            candidate,row=append_actor_donor(candidate,sha256(candidate).hexdigest(),1)
            allocations['drafts'].append(dict(row,draft_id=identifier))
        original=bytes(candidate)
        requests=[dict(draft_id='npc-a',appearance_donor_record_index=2)]
        result,audit=patch_allocated_appearance(context,candidate,allocations,requests)
        changed={i for i,(a,b) in enumerate(zip(original,result)) if a!=b}
        self.assertEqual(changed,{r['decoded_byte_offset'] for r in audit['changes']});self.assertEqual(len(changed),2)
        actors={a.record_index:a for a in parse_man(result).actors};target=actors[allocations['drafts'][0]['record_index']]
        self.assertEqual((target.model_index,target.animation_id),(5,2))
        other=actors[allocations['drafts'][1]['record_index']];self.assertEqual((other.model_index,other.animation_id),(4,1))
        offset=target.byte_offset+1+target.local_count*2
        self.assertEqual(original[:offset],result[:offset]);self.assertEqual(original[offset+2:],result[offset+2:])
        # The first allocation's recorded intermediate offset is deliberately stale.
        self.assertNotEqual(target.byte_offset,allocations['drafts'][0]['byte_offset'])
        self.assertEqual(candidate,original);self.assertFalse(audit['gameplay_verified'])
        with self.assertRaisesRegex(ProjectError,'preimage'):patch_allocated_appearance(context,result,allocations,requests)

    def test_wrong_record_donor_alias_shape_and_pair_reject(self):
        context,source=fixture();candidate,row=append_actor_donor(source,sha256(source).hexdigest(),1)
        allocations={'drafts':[dict(row,draft_id='npc')]};request=dict(draft_id='npc',appearance_donor_record_index=2)
        for requests in [[{**request,'payload':'native'}],[{**request,'appearance_donor_record_index':True}],[{**request,'appearance_donor_record_index':99}],[request,request]]:
            with self.assertRaises(ProjectError):patch_allocated_appearance(context,candidate,allocations,requests)
        for mutate in [lambda r:r.update(record_index=1),lambda r:r.update(byte_length=1),lambda r:r['donor'].update(record_index=99)]:
            bad=deepcopy(allocations);mutate(bad['drafts'][0])
            with self.assertRaises(ProjectError):patch_allocated_appearance(context,candidate,bad,[request])
        from importer.man_layout import read_man_layout
        layout=read_man_layout(candidate);alias=bytearray(candidate)
        count0=layout['partition_counts'][0];table=0x2b+3*(count0+row['record_index']);original_table=0x2b+3*(count0+1)
        alias[table:table+3]=alias[original_table:original_table+3]
        with self.assertRaises((ProjectError,ImportError)):patch_allocated_appearance(context,bytes(alias),allocations,[request])
        incompatible,raw=fixture(bones=(2,3));clone,new=append_actor_donor(raw,sha256(raw).hexdigest(),1)
        with self.assertRaises((ProjectError,ImportError)):patch_allocated_appearance(incompatible,clone,{'drafts':[dict(new,draft_id='npc')]},[request])
        unchanged,audit=patch_allocated_appearance(context,candidate,allocations,[{**request,'appearance_donor_record_index':1}])
        self.assertEqual(unchanged,candidate);self.assertEqual(audit['changes'],[])

    def test_reviewed_project_binding_retains_script_text_history_and_model_reference(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from sdk.project import ProjectService
        from sdk.npc_appearance import source,review
        from test_project_workflow import synthetic_scene
        with TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));document=synthetic_scene();donor=document['actors'][0]['semantic_id'];witness=deepcopy(document['actors'][0]);witness['semantic_id']='scene://fixture/actors/man-p1/0002';witness['model_reference']['asset_semantic_id']='asset://fixture/models/scene-tmd/0005';document['actors'].append(witness);p.import_metadata(document)
            p.command(dict(type='create_actor_draft',donor_entity_id=donor,position=dict(x=128,z=256),name='Resident'));identifier=next(iter(p.actor_drafts))
            run='script://fixture/actors/man-p1/0001/dialogue/0005/run/0006';p.actor_drafts[identifier]['dialogue']=dict(donor_entity_id=donor,runs={run:'Hello'})
            original=deepcopy(p.actor_drafts);options=dict(options=[dict(donor_entity_id=witness['semantic_id'])],supported=True)
            with patch.object(p,'appearance_options',return_value=options):
                request=dict(entity_id=identifier,donor_entity_id=witness['semantic_id']);before=len(p.undo_stack);report=review(p,request);self.assertEqual(p.actor_drafts,original)
                with self.assertRaises(ProjectError):p.command(dict(type='set_actor_draft_appearance',**request,review_key='0'*64))
                p.command(dict(type='set_actor_draft_appearance',**request,review_key=report['review_key']));after=deepcopy(p.actor_drafts);self.assertEqual(len(p.undo_stack),before+1)
                self.assertEqual(after[identifier]['dialogue'],original[identifier]['dialogue']);self.assertEqual(after[identifier]['donor_entity_id'],donor)
                self.assertEqual(p.model_references()[-1]['effective_donor_id'],witness['semantic_id']);self.assertEqual(p.model_references()[-1]['target_id'],witness['model_reference']['asset_semantic_id'])
                p.undo();self.assertEqual(p.actor_drafts,original);p.redo();self.assertEqual(p.actor_drafts,after);self.assertEqual(ProjectService.open(p.save()).actor_drafts,after)
                with self.assertRaises(ProjectError):p.command(dict(type='set_actor_draft_donor',entity_id=identifier,donor_entity_id=witness['semantic_id']))
                clear=dict(entity_id=identifier,donor_entity_id=None);reset=review(p,clear);p.command(dict(type='set_actor_draft_appearance',**clear,review_key=reset['review_key']));self.assertEqual(p.actor_drafts,original);p.undo();self.assertEqual(p.actor_drafts,after)
                self.assertEqual(source(p,identifier)['draft'],after[identifier])
                from sdk.template_files import export_file,review as transfer_review
                from sdk.npc_presets import review as instance_review
                from sdk.project_copy import source_key
                from contextlib import nullcontext
                import json
                disc=p.root/'fixture.bin';disc.write_bytes(b'synthetic');p.disc_path=str(disc)
                from test_importer_dialogue_authoring import fixture as text_fixture
                text_context,_=text_fixture()
                with patch.object(ProjectService,'_dialogue_context',return_value=text_context),patch.object(ProjectService,'appearance_options',return_value=options),patch('importer.pipeline._disc_context',side_effect=lambda _:nullcontext()),patch('importer.pipeline.import_scene',return_value=document):
                    p.command(dict(type='create_npc_preset',entity_id=identifier,name='Appearance speaker'))
                    template=next(iter(p.actor_templates.values()));frozen=deepcopy(template);file=export_file(p,template['id']);self.assertEqual(file['schema_version'],'legaia.npc-preset-file.v3')
                    target=ProjectService(p.root/'recipient');target.import_metadata(document);target.disc_path=str(disc);content=json.dumps(file);transfer=transfer_review(target,content,'Transferred appearance')
                    target.command(dict(type='import_actor_template',content=content,name='Transferred appearance',review_key=transfer['review_key']))
                    request=dict(template_id=transfer['template']['id'],name='New speaker',position=dict(x=256,z=320),expected_source_key=source_key(target));instance=instance_review(target,request)
                    target.command(dict(type='instantiate_npc_preset',**request,review_key=instance['review_key']))
                    self.assertEqual(target.actor_drafts[instance['entity_id']]['appearance'],after[identifier]['appearance']);self.assertEqual(target.actor_drafts[instance['entity_id']]['dialogue'],after[identifier]['dialogue'])
                    self.assertEqual(ProjectService.open(target.save()).actor_drafts,target.actor_drafts);self.assertEqual(p.actor_templates[template['id']],frozen)
