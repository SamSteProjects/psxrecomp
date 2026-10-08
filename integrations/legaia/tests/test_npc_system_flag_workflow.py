"""Reviewed NPC selectors, persistence and per-clone branch composition."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from hashlib import sha256
from importer.branch_authoring import BranchAuthoringContext
from importer.man_actor_structure import append_actor_donor
from importer.man_layout import read_man_layout
from sdk.project import ProjectService, ProjectError
from sdk.npc_system_flags import review, source
from sdk.npc_branches import review as branch_review, patch_project
import test_npc_system_flags as native_fixture
from test_importer_dialogue_authoring import ACTOR
from test_project_workflow import synthetic_scene
from test_model_primitive_workflow import http_server


class NpcSystemFlagWorkflow(TestCase):
    def test_per_clone_branch_baselines_retain_candidate_wide_target_budget(self):
        from types import SimpleNamespace
        context,candidate,allocations=native_fixture.NpcSystemFlagsTests().fixture(b'\x26\x02\0'*513)
        branches=BranchAuthoringContext(context._source)
        targets=branches.options(ACTOR)['targets'];self.assertEqual(len(targets),513)
        drafts={row['draft_id']:dict(scene_id='scene://fixture',donor_entity_id=ACTOR,
                    branches=dict(donor_entity_id=ACTOR,entries={t['semantic_id']:{'target_pc':5} for t in targets})) for row in allocations['drafts']}
        project=SimpleNamespace(actor_drafts=drafts,_validate_branches=lambda *_:None)
        with self.assertRaisesRegex(ProjectError,'1024-target budget'):
            patch_project(project,'scene://fixture',branches,candidate,allocations)

    def test_review_history_persistence_repetition_presets_clear_and_http(self):
        context, _, _ = native_fixture.NpcSystemFlagsTests().fixture(b'\x71\x46\x02\0')
        target = context.options(ACTOR)['targets'][0]
        with TemporaryDirectory() as directory:
            p = ProjectService(Path(directory)); p.import_metadata(synthetic_scene())
            p.command(dict(type='create_actor_draft', donor_entity_id=ACTOR, name='System probe', position=dict(x=128,z=256)))
            identifier = next(iter(p.actor_drafts)); before = deepcopy(p.actor_drafts); imports = deepcopy(p.imports)
            with patch.object(ProjectService,'_dialogue_context',return_value=context._source):
                request=dict(entity_id=identifier,entries={target['semantic_id']:{'index':4095}})
                report=review(p,request);self.assertEqual(p.actor_drafts,before)
                with self.assertRaises(ProjectError):
                    p.command(dict(type='set_actor_draft_system_flags',**request,review_key='0'*64))
                p.command(dict(type='set_actor_draft_system_flags',**request,review_key=report['review_key']))
                after=deepcopy(p.actor_drafts)
                self.assertEqual(source(p,identifier)['options']['targets'][0]['effective_values'],{'index':4095})
                p.undo();self.assertEqual(p.actor_drafts,before);p.redo()
                self.assertEqual(ProjectService.open(p.save()).actor_drafts,after)
                from sdk.draft_repeat import preview
                self.assertEqual(preview(p,dict(entity_id=identifier,count=1,step=dict(x=64,z=0),name='System copy'))['copies'][0]['draft']['system_flags'],after[identifier]['system_flags'])
                p.command(dict(type='create_npc_preset',entity_id=identifier,name='System preset'))
                self.assertEqual(next(iter(p.actor_templates.values()))['components']['NpcDraft']['system_flags'],after[identifier]['system_flags'])
                from sdk.template_files import export_file, parse
                import json
                from contextlib import nullcontext
                p.disc_path='synthetic-fixture.bin'
                with patch('importer.pipeline._disc_context',side_effect=lambda _:nullcontext()),patch('importer.pipeline.import_scene',side_effect=lambda *_:deepcopy(p.imports[p.active_scene])):
                    exported=export_file(p,next(iter(p.actor_templates)))
                p.disc_path=None
                self.assertEqual(exported['schema_version'],'legaia.npc-preset-file.v11')
                self.assertEqual(parse(json.dumps(exported)),exported)
                import os
                if os.environ.get('LEGAIA_SYSTEM_PACKAGE_EVIDENCE'):
                    (Path(os.environ['LEGAIA_SYSTEM_PACKAGE_EVIDENCE'])/'preset-fixture.json').write_text(json.dumps(exported),encoding='utf-8')
                with http_server(p) as (server,post):
                    server.RequestHandlerClass.log_message=lambda *args:None
                    self.assertEqual(post('/api/npc-system-flags-source',dict(entity_id=identifier))[0],200)
                    self.assertEqual(post('/api/npc-system-flags-source',dict(entity_id=identifier,extra=1))[0],400)
                    self.assertEqual(post('/api/npc-system-flags-review',dict(entity_id=identifier,entries={target['semantic_id']:{'index':True}}))[0],400)
                clear=dict(entity_id=identifier,entries={});report=review(p,clear)
                p.command(dict(type='set_actor_draft_system_flags',**clear,review_key=report['review_key']))
                self.assertEqual(p.actor_drafts,before);self.assertEqual(p.imports,imports)
                p.mode='live'
                with self.assertRaises(ProjectError):source(p,identifier)

    def test_two_same_donor_clones_compose_separate_selector_and_branch_baselines(self):
        context, _, _ = native_fixture.NpcSystemFlagsTests().fixture(b'\x71\x46\x02\0')
        target=context.options(ACTOR)['targets'][0];branch_context=BranchAuthoringContext(context._source)
        original=context._man;candidate=original;allocations={'drafts':[]}
        with TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.import_metadata(synthetic_scene())
            with patch.object(ProjectService,'_dialogue_context',return_value=context._source),patch.object(ProjectService,'_branch_context',return_value=branch_context):
                for value in (0,4095):
                    p.command(dict(type='create_actor_draft',donor_entity_id=ACTOR,name=f'System {value}',position=dict(x=128,z=256)))
                    identifier=list(p.actor_drafts)[-1]
                    request=dict(entity_id=identifier,entries={target['semantic_id']:{'index':value}});r=review(p,request)
                    p.command(dict(type='set_actor_draft_system_flags',**request,review_key=r['review_key']))
                    branch_id=target['semantic_id'].replace('/system-flag/','/branch/')
                    request=dict(entity_id=identifier,entries={branch_id:{'target_pc':target['pc']}})
                    r=branch_review(p,request);p.command(dict(type='set_actor_draft_branches',**request,review_key=r['review_key']))
                    candidate,row=append_actor_donor(candidate,sha256(candidate).hexdigest(),1)
                    allocations['drafts'].append(dict(row,draft_id=identifier))
                from sdk.npc_system_flags import patch_project as patch_selectors
                candidate,_=patch_selectors(p,p.active_scene,context,candidate,allocations)
                expected=bytearray(candidate)
                for allocation in allocations['drafts']:
                    row=next(r for r in read_man_layout(candidate)['records'] if r['partition']==1 and r['record_index']==allocation['record_index'])
                    at=row['byte_offset']+target['pc']+2;expected[at:at+2]=b'\xfe\xff'
                result,audit=patch_project(p,p.active_scene,branch_context,candidate,allocations)
                self.assertEqual(result,bytes(expected));self.assertEqual(len(audit['changes']),2)
                self.assertEqual(audit['candidate_man_sha256'],sha256(candidate).hexdigest())
                from sdk.npc_script_compare import authored_spans
                from sdk.npc_system_flags import patch_project as patch_selectors
                # Reconstruct the selector receipts from the untouched clones.
                plain=original
                for _ in allocations['drafts']:
                    plain,_=append_actor_donor(plain,sha256(plain).hexdigest(),1)
                _,selector_audit=patch_selectors(p,p.active_scene,context,plain,allocations)
                source_at,raw,entry=context._source.verified_record(ACTOR)
                retail=dict(raw_hex=raw.hex(),script_offset=entry,byte_offset=source_at)
                for allocation in allocations['drafts']:
                    row=next(r for r in read_man_layout(result)['records'] if r['partition']==1 and r['record_index']==allocation['record_index'])
                    clone=result[row['byte_offset']:row['byte_offset']+row['byte_length']]
                    generated=dict(raw_hex=clone.hex(),script_offset=entry,**row)
                    spans=authored_spans(dict(npc_system_flags_changes=selector_audit,npc_branches_changes=audit),allocation['draft_id'],retail,generated,p.actor_drafts[allocation['draft_id']])
                    self.assertEqual([s['category'] for s in spans],['own_system_flag','own_branch'])
