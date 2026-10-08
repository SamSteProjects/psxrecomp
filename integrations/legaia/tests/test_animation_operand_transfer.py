"""Portable source-owned arguments remain atomic, source-bound and metadata-only."""
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
import json, os, tempfile, unittest
from sdk.project import ProjectService,ProjectError,digest
from sdk.script_operand_files import review,export_file,parse
from sdk.script_operand_bundle import review as bundle_review,export_file as export_bundle,parse as parse_bundle
from sdk.script_operand_bundle import _composition
from importer.animation_operand_authoring import AnimationOperandAuthoringContext,load_animation_operand_authoring_context
from importer.effect_color_authoring import EffectColorAuthoringContext
from importer.core import ImportError
from importer.pipeline import import_scene
from test_project_workflow import synthetic_scene
from test_importer_dialogue_authoring import fixture,ACTOR
from test_effect_color_authoring import END


class AnimationTransfer(unittest.TestCase):
    def test_whole_instruction_overlap_including_noop_and_same_byte(self):
        from types import SimpleNamespace
        animation=SimpleNamespace(_requests=lambda entries:[(None,None,0,None,None,0,{'length':3},None,None)])
        project=SimpleNamespace(overrides={
            'a':{'ScriptFlags':{'entries':{'flag':{'bit':1}}}},
            'z':{'ScriptAnimationOperands':{'entries':{'animation':{'animation_operand':1}}}},
        },_dialogue_document=lambda owner:{'scene':{'name':'fixture'}},
            _flag_context=lambda owner:SimpleNamespace(patch=lambda entries:(b'\1\2\3',[{'decoded_byte_offset':2,'byte_length':1}])))
        for audits in ([],[{'decoded_byte_offset':2,'byte_length':1}]):
            animation.patch=lambda entries:(b'\1\2\3',audits)
            with patch('sdk.script_animation_operands.context',return_value=animation):
                with self.assertRaisesRegex(ProjectError,'overlaps another'):_composition(project,'scene://fixture')

    def test_synthetic_model_effect_and_color_spans_roundtrip_atomically(self):
        source,_=fixture(b'\x4c\x81\1\2\3\4\5\6\7\xb4\x07\x3f\1\x34\x0f\1\2\3\4\0'+END)
        animation=AnimationOperandAuthoringContext(source);targets=animation.options(ACTOR)['targets']
        color=EffectColorAuthoringContext(source).options(ACTOR)['targets'][0]
        components=dict(ScriptAnimationOperands=dict(entries={targets[0]['semantic_id']:dict(model_id=16777215,animation_frame=65535,tween_frames=0),targets[1]['semantic_id']:dict(animation_operand=255)}),ScriptEffectColors=dict(entries={color['semantic_id']:dict(red=255,green=128,blue=0,intensity=-32768)}))
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.import_metadata(synthetic_scene());p.disc_path='fixture.bin'
            file=dict(schema_version='legaia.script-operand-file.v2',scene_id=p.active_scene,source_import_sha256=digest(p.imports[p.active_scene]),owner_id=ACTOR,components=components)
            bundle=dict(schema_version='legaia.script-operand-bundle.v2',scene_id=p.active_scene,source_import_sha256=file['source_import_sha256'],owners=[dict(owner_id=ACTOR,components=components)])
            with patch('importer.pipeline._disc_context'),patch('sdk.resources._verify'),patch.object(ProjectService,'_dialogue_context',return_value=source):
                before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
                report=bundle_review(p,json.dumps(bundle));self.assertEqual(before,(p._document(),p.undo_stack,p.redo_stack))
                p.command(dict(type='import_script_operand_bundle',content=json.dumps(bundle),review_key=report['review_key']))
                self.assertEqual(p.overrides[ACTOR],components);self.assertEqual(len(p.undo_stack),1)
                self.assertEqual(export_file(p,ACTOR),file);self.assertEqual(export_bundle(p),bundle)
                self.assertEqual(ProjectService.open(p.save()).overrides,p.overrides)
                p.undo();self.assertEqual(p.overrides,{})
                p.redo();same=bundle_review(p,json.dumps(bundle));p.command(dict(type='import_script_operand_bundle',content=json.dumps(bundle),review_key=same['review_key']));self.assertEqual(len(p.undo_stack),1)
                bad=deepcopy(file);bad['components']['ScriptAnimationOperands']['entries'][targets[1]['semantic_id']]=dict(model_id=0,animation_frame=0,tween_frames=0)
                snapshot=deepcopy((p._document(),p.undo_stack,p.redo_stack))
                with self.assertRaises((ProjectError,ImportError)):review(p,ACTOR,json.dumps(bad))
                self.assertEqual(snapshot,(p._document(),p.undo_stack,p.redo_stack))
                with self.assertRaises(ProjectError):p.command(dict(type='import_script_operand_bundle',content=json.dumps(bundle),review_key=report['review_key']))
            for schema in ('legaia.script-operand-file.v1','unknown'):
                with self.assertRaises(ProjectError):parse(json.dumps(dict(file,schema_version=schema)))
            with self.assertRaises(ProjectError):parse_bundle(json.dumps(dict(bundle,schema_version='legaia.script-operand-bundle.v1')))


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'Private Retail disc required')
class RetailAnimationTransfer(unittest.TestCase):
    def test_p1_p2_file_bundle_imports_history_and_preserved_unrelated_state(self):
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'],'map02'),os.environ['LEGAIA_DISC_BIN'])
            context=load_animation_operand_authoring_context(p.disc_path,'map02');owners=[]
            for owner in ['scene://map02/actors/man-p1/0003','scene://map02/scripts/man-p2/0012']:
                target=context.options(owner)['targets'][0];values=deepcopy(target['values'])
                for key in values:values[key]^=1
                owners.append(dict(owner_id=owner,components={'ScriptAnimationOperands':{'entries':{target['semantic_id']:values}}}))
            bundle=dict(schema_version='legaia.script-operand-bundle.v2',scene_id=p.active_scene,source_import_sha256=digest(p.imports[p.active_scene]),owners=owners)
            file=dict(schema_version='legaia.script-operand-file.v2',scene_id=p.active_scene,source_import_sha256=bundle['source_import_sha256'],**owners[0])
            before=deepcopy((p._document(),p.undo_stack,p.redo_stack,p.imports))
            report=review(p,owners[0]['owner_id'],json.dumps(file));self.assertEqual(before,(p._document(),p.undo_stack,p.redo_stack,p.imports))
            p.command(dict(type='import_script_operands',entity_id=owners[0]['owner_id'],content=json.dumps(file),review_key=report['review_key']))
            self.assertEqual(export_file(p,owners[0]['owner_id']),file)
            p.undo();self.assertEqual(p._document(),before[0])
            proposal=bundle_review(p,json.dumps(bundle));self.assertEqual(proposal['change_count'],2)
            p.command(dict(type='import_script_operand_bundle',content=json.dumps(bundle),review_key=proposal['review_key']))
            self.assertEqual(len(p.undo_stack),1);self.assertEqual(export_bundle(p),bundle)
            saved=deepcopy(p._document());p.undo();self.assertEqual(p._document(),before[0]);p.redo()
            self.assertEqual(ProjectService.open(p.save())._document(),saved);self.assertEqual(p.imports,before[3])
            if os.environ.get('LEGAIA_ANIMATION_TRANSFER_EVIDENCE'):
                out=Path(os.environ['LEGAIA_ANIMATION_TRANSFER_EVIDENCE']);out.parent.mkdir(parents=True,exist_ok=True)
                out.write_text(json.dumps(dict(file=file,file_review=report,bundle=bundle,bundle_review=proposal),indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':unittest.main()
