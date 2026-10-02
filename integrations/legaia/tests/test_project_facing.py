"""Facing source layers, atomic history, persistence and operand transfer boundaries."""
from contextlib import nullcontext
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from importer.core import ImportError
from importer.facing_authoring import FacingAuthoringContext
from sdk.project import ProjectService, ProjectError, digest
from sdk.script_operand_files import review, apply, export_file
from sdk.script_operand_bundle import review as bundle_review, apply as bundle_apply
from test_importer_dialogue_authoring import fixture, ACTOR
from test_project_workflow import synthetic_scene

END = b'\x3f\0\0\x06town01\1\2\3'

class ProjectFacingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = ProjectService(Path(temporary.name))
        self.project.import_metadata(synthetic_scene())
        self.source, _ = fixture(b'\x24\x38\x81\0\x4c\x51\x08\x09\xa3\x04' + END)
        self.context = FacingAuthoringContext(self.source)
        self.targets = self.context.options(ACTOR)['targets']
        self.key = self.targets[0]['semantic_id']
        self.command = dict(type='set_facing_target', entity_id=ACTOR, facing_id=self.key, values={'sector':5})

    def test_layers_history_noop_and_offline_clear_preserve_imports(self):
        p = self.project
        imported = deepcopy(p.imports)
        with patch.object(p, '_dialogue_context', return_value=self.source):
            p.command(self.command)
            result = p.facing_options(ACTOR)['targets'][0]
            self.assertEqual(result['values'], {'sector':1})
            self.assertEqual(result['authored_values'], {'sector':5})
            self.assertEqual(result['effective_values'], {'sector':5})
            self.assertEqual(len(p.undo_stack), 1)
            p.command(self.command)
            self.assertEqual(len(p.undo_stack), 1)
            result['effective_values']['sector'] = 7
            self.assertEqual(p.facing_options(ACTOR)['targets'][0]['effective_values'], {'sector':5})
        self.assertEqual(p.imports, imported)
        authored = deepcopy(p.overrides)
        self.assertIn('ScriptFacing', p.component_reviews(ACTOR)[0]['component'])
        self.assertEqual(p.authored_assets()[0]['changes'], ['Facing operands: 1 instructions'])
        p.undo(); self.assertEqual(p.overrides, {})
        p.redo(); self.assertEqual(p.overrides, authored)
        restored = ProjectService.open(p.save())
        self.assertEqual(restored.overrides, authored)
        restored.command(dict(type='clear_facing_target', entity_id=ACTOR, facing_id=self.key))
        self.assertEqual(restored.overrides, {})
        restored.undo(); self.assertEqual(restored.overrides, authored)

    def test_invalid_values_owner_unknown_pc_and_stale_source_are_atomic(self):
        p = self.project
        with patch.object(p, '_dialogue_context', return_value=self.source):
            for command in [dict(self.command, values=value) for value in ({}, {'sector':True}, {'sector':8}, {'sector':1.5}, {'sector':1,'x':64})] + [
                dict(self.command, source_offset=3),
                dict(self.command, facing_id=self.key.replace('/0001/', '/0000/')),
                dict(self.command, facing_id=self.key[:-4]+'ffff')]:
                before = deepcopy((p.overrides,p.undo_stack,p.redo_stack))
                with self.assertRaises((ProjectError,ImportError)):
                    p.command(command)
                self.assertEqual((p.overrides,p.undo_stack,p.redo_stack),before)
        with patch.object(p, '_dialogue_context', side_effect=ImportError('source changed')):
            with self.assertRaisesRegex(ImportError,'source changed'):
                p.command(self.command)
        self.assertEqual(p.overrides,{})

    def test_json_and_bundle_transfers_include_facing_and_source_guards(self):
        p = self.project
        p.disc_path = Path('source-disc.bin')
        file = dict(schema_version='legaia.script-operand-file.v1',scene_id=p.active_scene,
                    source_import_sha256=digest(p.imports[p.active_scene]),owner_id=ACTOR,
                    components={'ScriptFacing':{'entries':{self.key:{'sector':5}}}})
        content = json.dumps(file)
        with patch.object(p,'_dialogue_context',return_value=self.source), patch('importer.pipeline._disc_context',return_value=nullcontext()), patch('sdk.resources._verify'):
            report = review(p,ACTOR,content)
            self.assertEqual(p.overrides,{})
            self.assertEqual(report['change_count'],1)
            apply(p,dict(type='import_script_operands',entity_id=ACTOR,content=content,review_key=report['review_key']))
            self.assertEqual(export_file(p,ACTOR),file)
            self.assertEqual(len(p.undo_stack),1)
            p.undo()
            bundle=dict(schema_version='legaia.script-operand-bundle.v1',scene_id=p.active_scene,
                        source_import_sha256=file['source_import_sha256'],owners=[dict(owner_id=ACTOR,components=file['components'])])
            text=json.dumps(bundle);report=bundle_review(p,text)
            bundle_apply(p,dict(type='import_script_operand_bundle',content=text,review_key=report['review_key']))
            self.assertEqual(p.overrides[ACTOR],file['components'])
            self.assertEqual(len(p.undo_stack),1)
            stale=deepcopy(file);stale['source_import_sha256']='f'*64
            with self.assertRaisesRegex(ProjectError,'imported source'):
                review(p,ACTOR,json.dumps(stale))
            before=deepcopy(p.overrides)
            with self.assertRaisesRegex(ProjectError,'changed since review'):
                apply(p,dict(type='import_script_operands',entity_id=ACTOR,content=content,review_key='f'*64))
            self.assertEqual(p.overrides,before)

if __name__ == '__main__':unittest.main()
