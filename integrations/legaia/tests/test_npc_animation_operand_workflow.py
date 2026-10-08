"""Clone-owned animation Review/Apply, persistence and complete native package."""
from copy import deepcopy
from hashlib import sha256
import json, os, shutil, tempfile, unittest, zipfile
from pathlib import Path
from importer.pipeline import import_scene
from importer.animation_operand_authoring import load_animation_operand_authoring_context
from importer.man_actor_structure import append_actor_candidates
from importer.man_layout import read_man_layout
from sdk.project import ProjectService, ProjectError
from sdk.npc_animation_operands import source, review
from sdk.npc_current_script import inspect
from sdk.build import build_project
from sdk.build_history import verify_build
from test_model_primitive_workflow import http_server

OWNER='scene://map02/actors/man-p1/0003'


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'Private Retail disc required')
class NpcAnimationOperandWorkflow(unittest.TestCase):
    def project(self, root):
        p=ProjectService(Path(root))
        p.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'],'map02'),os.environ['LEGAIA_DISC_BIN'])
        p.command(dict(type='create_actor_draft',donor_entity_id=OWNER,name='Animation argument probe',position=dict(x=128,z=256)))
        identity=next(iter(p.actor_drafts))
        return p,identity,source(p,identity)['options']['targets'][0]

    def test_review_current_history_noop_clear_save_http_and_stale(self):
        with tempfile.TemporaryDirectory() as directory:
            p,identity,target=self.project(directory)
            before=deepcopy((p._document(),p.undo_stack,p.redo_stack,p.imports))
            request=dict(entity_id=identity,entries={target['semantic_id']:dict(animation_operand=255)})
            proposal=review(p,request)
            self.assertEqual(before,(p._document(),p.undo_stack,p.redo_stack,p.imports))
            current=proposal['current_inspection']['record']
            expected=bytearray.fromhex(current['raw_hex'])
            at=target['pc']+target['instruction_length']-1
            expected[at]=255
            self.assertEqual(proposal['proposed_inspection']['record']['raw_hex'],expected.hex())
            command=dict(type='set_actor_draft_animation_operands',**request,review_key=proposal['review_key'])
            p.command(command)
            self.assertEqual(inspect(p,identity)['inspection']['record']['raw_hex'],expected.hex())
            saved=deepcopy((p._document(),p.undo_stack))
            p.undo();self.assertEqual(p._document(),before[0]);p.redo()
            self.assertEqual(saved,(p._document(),p.undo_stack))
            self.assertEqual(ProjectService.open(p.save())._document(),saved[0])
            proposal=review(p,request)
            p.command(dict(command,review_key=proposal['review_key']))
            self.assertEqual(saved,(p._document(),p.undo_stack))
            p.command(dict(type='create_npc_preset',entity_id=identity,name='Must retain arguments'))
            self.assertEqual(next(iter(p.actor_templates.values()))['components']['NpcDraft']['animation_operands'],p.actor_drafts[identity]['animation_operands'])
            p.undo()
            with http_server(p) as (server,post):
                server.RequestHandlerClass.log_message=lambda *args:None
                self.assertEqual(post('/api/npc-animation-operands-source',dict(entity_id=identity))[0],200)
                self.assertEqual(post('/api/npc-animation-operands-source',dict(entity_id=identity,extra=1))[0],400)
                self.assertEqual(post('/api/npc-animation-operands-review',request)[0],200)
                self.assertEqual(post('/api/npc-animation-operands-review',dict(request,entries={target['semantic_id']:dict(animation_operand=True)}))[0],400)
            self.assertEqual(saved,(p._document(),p.undo_stack))
            clear=dict(entity_id=identity,entries={});proposal=review(p,clear)
            p.command(dict(type='set_actor_draft_animation_operands',**clear,review_key=proposal['review_key']))
            self.assertEqual(inspect(p,identity)['inspection']['record']['raw_hex'],current['raw_hex'])
            stale=review(p,request)
            p.command(dict(type='rename_actor_draft',entity_id=identity,name='Changed after Review'))
            changed=deepcopy((p._document(),p.undo_stack,p.redo_stack))
            with self.assertRaises(ProjectError):p.command(dict(command,review_key=stale['review_key']))
            self.assertEqual(changed,(p._document(),p.undo_stack,p.redo_stack))
            p.mode='live'
            with self.assertRaises(ProjectError):source(p,identity)
            with self.assertRaises(ProjectError):p.command(command)
            self.assertEqual(p.imports,before[3])

    def test_independent_clones_complete_normal_build_and_saved_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            p,identity,target=self.project(directory)
            p.command(dict(type='create_actor_draft',donor_entity_id=OWNER,name='Independent second clone',position=dict(x=256,z=256)))
            ids=list(p.actor_drafts)
            for name,value in zip(ids,(1,255)):
                request=dict(entity_id=name,entries={target['semantic_id']:dict(animation_operand=value)})
                proposal=review(p,request)
                p.command(dict(type='set_actor_draft_animation_operands',**request,review_key=proposal['review_key']))
            context=load_animation_operand_authoring_context(p.disc_path,'map02')
            requests=[dict(id=name,donor_record_index=3,position=p.actor_drafts[name]['position']) for name in sorted(ids)]
            candidate,allocation=append_actor_candidates(context._man,sha256(context._man).hexdigest(),requests)
            expected=bytearray(candidate)
            # A source-owner override must remain independent from both clones.
            from sdk.script_animation_operands import review as source_review
            source_values=dict(animation_operand=7)
            source_proposal,_=source_review(p,OWNER,target['semantic_id'],source_values)
            p.command(dict(type='apply_script_animation_operands',entity_id=OWNER,animation_operand_id=target['semantic_id'],values=source_values,review_key=source_proposal['review']['review_key']))
            original=next(r for r in read_man_layout(candidate)['records'] if r['partition']==1 and r['record_index']==3)
            expected[original['byte_offset']+target['pc']+target['instruction_length']-1]=7
            values={ids[0]:1,ids[1]:255}
            for row in allocation['drafts']:
                final=next(r for r in read_man_layout(candidate)['records'] if r['partition']==1 and r['record_index']==row['record_index'])
                expected[final['byte_offset']+target['pc']+target['instruction_length']-1]=values[row['draft_id']]
            p.save()
            before=deepcopy((p._document(),p.undo_stack,p.redo_stack,p.imports))
            output=build_project(p)
            from importer.pipeline import _disc_context, _bounded_scene_range
            from importer.model_pack_archive import _archive
            from importer.man_source import read_man_source
            from sdk.npc_build_script import emitted_prot
            audit=json.loads(Path(output['audit']).read_text(encoding='utf-8'))
            with zipfile.ZipFile(output['path']) as archive:
                with _disc_context(p.disc_path) as (_,_,mapping,source_archive):
                    source_prot=source_archive.image.read_user(source_archive.node.extent_lba,0,source_archive.node.size,source_archive.node.size)
                    prot,delivery=emitted_prot(source_prot,source_archive.node.extent_lba*2048,archive,audit)
                    made=_archive(prot)
                    actual=read_man_source(made,*_bounded_scene_range(made,mapping,'map02'),'map02').payload
                members=[row['file'] for row in audit['overlays']]
                if audit.get('relocation_payload'):members.append(audit['relocation_payload']['file'])
                for member in members:self.assertEqual(archive.read(member),(Path(output['package_directory'])/member).read_bytes())
            self.assertEqual(actual,bytes(expected))
            verify_build(p,Path(output['audit']).parent.name)
            self.assertEqual(before,(p._document(),p.undo_stack,p.redo_stack,p.imports))
            from sdk.npc_script_compare import compare
            comparison=compare(p,ids[0],Path(output['audit']).parent.name)
            self.assertEqual([r['category'] for r in comparison['authored_spans']],['own_animation_operand'])
            if os.environ.get('LEGAIA_NPC_ANIMATION_EVIDENCE'):
                path=Path(os.environ['LEGAIA_NPC_ANIMATION_EVIDENCE']);path.parent.mkdir(parents=True,exist_ok=True)
                retained=path.parent/'npc-fixtures'/Path(output['audit']).parent.name
                retained.parent.mkdir(parents=True,exist_ok=True)
                shutil.copytree(p.root,retained)
                reopened=ProjectService.open(retained)
                verify_build(reopened,Path(output['audit']).parent.name)
                path.write_text(json.dumps(dict(build_id=Path(output['audit']).parent.name,package_sha256=output['sha256'],
                    candidate_man_sha256=sha256(actual).hexdigest(),complete_literal_man_equal=True,directory_zip_equal=True,
                    delivery=delivery,retained_fixture=str(retained),saved_comparison=comparison,gameplay_verified=False,draft_audit=audit['npc_candidates'][p.active_scene]['draft_audit']),indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':unittest.main()
