"""Reviewed source operands persist and enter actual private native packages."""
from copy import deepcopy
from hashlib import sha256
import json, os, shutil, tempfile, unittest, zipfile
from pathlib import Path
from unittest.mock import patch
from importer.animation_operand_authoring import AnimationOperandAuthoringContext, load_animation_operand_authoring_context
from importer.core import ImportError, decompress_lzs
from importer.pipeline import import_scene
from sdk.project import ProjectService, ProjectError
from sdk.script_animation_operands import COMPONENT, compose, options, review
from sdk.build import build_project, build_report, package_change_kinds
from sdk.build_history import verify_build
from test_project_workflow import synthetic_scene
from test_importer_dialogue_authoring import fixture, ACTOR
from test_effect_color_authoring import END
from test_model_primitive_workflow import http_server


class AnimationOperandWorkflow(unittest.TestCase):
    def test_review_apply_history_persistence_http_stale_live_and_reset(self):
        source,man=fixture(b'\x4c\x81\1\2\3\4\5\6\7\x34\x3f\1'+END)
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.import_metadata(synthetic_scene())
            with patch.object(p,'_dialogue_context',return_value=source):
                targets=options(p,ACTOR)['targets'];target=targets[0];key=target['semantic_id']
                values=dict(target['values'],animation_frame=65535,tween_frames=0)
                before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
                proposal,component=review(p,ACTOR,key,values)
                self.assertEqual(before,(p._document(),p.undo_stack,p.redo_stack))
                at=target['decoded_byte_offset'];expected=bytearray(man);expected[at+3:at+7]=b'\xff\xff\0\0'
                self.assertEqual(proposal['review']['proposed_record_sha256'],sha256(bytes(expected)[source.verified_record(ACTOR)[0]:source.verified_record(ACTOR)[0]+len(source.verified_record(ACTOR)[1])]).hexdigest())
                command=dict(type='apply_script_animation_operands',entity_id=ACTOR,animation_operand_id=key,values=values,review_key=proposal['review']['review_key'])
                with self.assertRaises(ProjectError):p.command(dict(command,review_key='0'*64))
                with http_server(p) as (server,post):
                    server.RequestHandlerClass.log_message=lambda *args:None
                    self.assertEqual(post('/api/script-animation-operands',dict(entity_id=ACTOR))[0],200)
                    self.assertEqual(post('/api/script-animation-operand-review',dict(entity_id=ACTOR,animation_operand_id=key,values=values))[0],200)
                    self.assertEqual(post('/api/script-animation-operands',dict(entity_id=ACTOR,extra=1))[0],400)
                    self.assertEqual(post('/api/script-animation-operand-review',dict(entity_id=ACTOR,animation_operand_id=key,values=dict(values,animation_frame=True)))[0],400)
                p.command(command);self.assertEqual(p.overrides[ACTOR][COMPONENT],component)
                from sdk.script_operand_files import export_file
                from sdk.script_operand_bundle import export_file as export_bundle
                with self.assertRaisesRegex(ProjectError,'user-owned disc'):export_file(p,ACTOR)
                with self.assertRaisesRegex(ProjectError,'user-owned disc'):export_bundle(p)
                after=deepcopy((p._document(),p.undo_stack));self.assertEqual(len(p.undo_stack),len(before[1])+1)
                fresh,_=review(p,ACTOR,key,values);self.assertTrue(fresh['review']['no_op'])
                p.command(dict(command,review_key=fresh['review']['review_key']));self.assertEqual(after,(p._document(),p.undo_stack))
                p.undo();self.assertEqual(p._document(),before[0]);p.redo();self.assertEqual(after,(p._document(),p.undo_stack))
                self.assertEqual(ProjectService.open(p.save())._document(),after[0])
                clear,_=review(p,ACTOR,key,None);p.command(dict(command,values=None,review_key=clear['review']['review_key']))
                self.assertNotIn(ACTOR,p.overrides)
                stale,_=review(p,ACTOR,key,values);p.name+=' changed'
                with self.assertRaises(ProjectError):p.command(dict(command,review_key=stale['review']['review_key']))
                p.mode='live'
                with self.assertRaises(ProjectError):review(p,ACTOR,key,values)
                with self.assertRaises(ProjectError):p.command(command)
                self.assertEqual(p.imports["scene://fixture"],synthetic_scene())

    def test_native_composition_locks_full_instruction_and_report_identity(self):
        source,man=fixture(b'\x34\x3f\1'+END);context=AnimationOperandAuthoringContext(source)
        target=context.options(ACTOR)['targets'][0];key=target['semantic_id'];at=target['decoded_byte_offset']
        working=bytes([man[0]^1])+man[1:]
        result,audit=compose(context,man,working,{key:dict(animation_operand=255)},[dict(decoded_byte_offset=0,byte_length=1)])
        expected=bytearray(working);expected[at]=255;self.assertEqual(result,bytes(expected))
        row=dict(audit[0],scene='fixture');report=build_report(dict(edits=[row],validation={},overlays=[]))
        self.assertEqual(report['changes'][0]['asset_id'],key)
        self.assertEqual(report['changes'][0]['field'],'script.animation.animation_operand')
        self.assertEqual(package_change_kinds([row]),['script animation operands'])
        for previous,candidate in (([dict(decoded_byte_offset=at-1,byte_length=1)],man),([],man[:at-1]+b'\x30'+man[at:])):
            with self.assertRaises(ProjectError):compose(context,man,candidate,{key:target['values']},previous)


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'Private Retail disc required')
class RetailAnimationOperandWorkflow(unittest.TestCase):
    def test_existing_operand_survives_npc_table_growth_without_editing_clone(self):
        from importer.man_actor_structure import append_actor_candidates
        from sdk.draft_build import _prepare_draft_scene
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'],'map02'),os.environ['LEGAIA_DISC_BIN'])
            owner='scene://map02/actors/man-p1/0003';context=load_animation_operand_authoring_context(p.disc_path,'map02')
            target=context.options(owner)['targets'][0];key=target['semantic_id'];values=dict(animation_operand=255)
            proposal,_=review(p,owner,key,values)
            p.command(dict(type='apply_script_animation_operands',entity_id=owner,animation_operand_id=key,values=values,review_key=proposal['review']['review_key']))
            p.command(dict(type='create_actor_draft',donor_entity_id='scene://map02/actors/man-p1/0002',name='Independent clone',position=dict(x=128,z=256)))
            identity=next(iter(p.actor_drafts));draft=p.actor_drafts[identity]
            expanded,_=append_actor_candidates(context._man,sha256(context._man).hexdigest(),[
                dict(id=identity,donor_record_index=2,position=draft['position'])])
            expected=bytearray(expanded);at=target['decoded_byte_offset']+3;expected[at]=255
            before=deepcopy((p._document(),p.undo_stack,p.redo_stack,p.imports))
            _,prepared=_prepare_draft_scene(p,identity,defer_rebuild=True)
            self.assertEqual(prepared['_rebuild_request']['candidate'],bytes(expected))
            self.assertEqual(prepared['animation_operand_changes'][0]['decoded_byte_offset'],at)
            self.assertEqual(before,(p._document(),p.undo_stack,p.redo_stack,p.imports))

    def test_source_owner_project_and_complete_saved_native_man(self):
        receipts=[]
        for scene,owner in (('town01','scene://town01/scripts/man-p2/0005'),('map02','scene://map02/actors/man-p1/0003')):
            with self.subTest(scene=scene),tempfile.TemporaryDirectory() as directory:
                p=ProjectService(Path(directory));p.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'],scene),os.environ['LEGAIA_DISC_BIN'])
                source=load_animation_operand_authoring_context(p.disc_path,scene)
                target=source.options(owner)['targets'][0];key=target['semantic_id'];at=target['decoded_byte_offset']
                values=deepcopy(target['values']);expected=bytearray(source._man)
                if target['mnemonic']=='SET_MODEL_ANIMATION':
                    values['animation_frame']^=1;values['tween_frames']^=1
                    expected[at+3:at+5]=values['animation_frame'].to_bytes(2,'little')
                    expected[at+5:at+7]=values['tween_frames'].to_bytes(2,'little')
                else:
                    values['animation_operand']^=1;expected[at]=values['animation_operand']
                imports=deepcopy(p.imports)
                before=deepcopy((p._document(),p.undo_stack,p.redo_stack));proposal,_=review(p,owner,key,values)
                self.assertEqual(before,(p._document(),p.undo_stack,p.redo_stack))
                p.command(dict(type='apply_script_animation_operands',entity_id=owner,animation_operand_id=key,values=values,review_key=proposal['review']['review_key']))
                saved=deepcopy(p._document());p.undo();self.assertEqual(p._document(),before[0]);p.redo()
                self.assertEqual(ProjectService.open(p.save())._document(),saved)
                output=build_project(p)
                with zipfile.ZipFile(output['path']) as archive:
                    payload=archive.read(f'assets/{scene}-man.lzs')
                    actual=decompress_lzs(payload,len(expected))[0]
                    self.assertEqual(actual,bytes(expected))
                    self.assertEqual(payload,(Path(output['package_directory'])/f'assets/{scene}-man.lzs').read_bytes())
                result=verify_build(p,Path(output['audit']).parent.name)
                self.assertEqual(result['report']['changes'],output['report']['changes'])
                self.assertTrue(all(row['asset_id']==key for row in output['report']['changes']))
                self.assertEqual(p.imports,imports)
                retained=None
                destination=os.environ.get('LEGAIA_ANIMATION_WORKFLOW_EVIDENCE')
                if destination:
                    retained=Path(destination).resolve().parent/'fixtures'/(Path(output['audit']).parent.name+'-'+Path(directory).name)
                    retained.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copytree(p.root,retained)
                    reopened=ProjectService.open(retained)
                    verified=verify_build(reopened,Path(output['audit']).parent.name)
                    self.assertEqual(verified['report']['changes'],output['report']['changes'])
                receipts.append(dict(scene=scene,owner=owner,target=key,build_id=Path(output['audit']).parent.name,
                    package_sha256=output['sha256'],source_man_sha256=sha256(source._man).hexdigest(),
                    candidate_man_sha256=sha256(actual).hexdigest(),complete_literal_man_equal=True,
                    directory_zip_equal=True,retained_fixture=str(retained) if retained else None,report=output['report']))
        destination=os.environ.get('LEGAIA_ANIMATION_WORKFLOW_EVIDENCE')
        if destination:
            path=Path(destination);path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps(receipts,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':unittest.main()
