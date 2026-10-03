"""Retail branch review, ordinary history and independent package readback."""
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest
import zipfile

from importer.core import decompress_lzs, ImportError as RetailImportError
from importer.pipeline import import_scene, _disc_context, _bounded_scene_range
from importer.man_source import read_man_source
from sdk.build import build_project, package_change_kinds
from sdk.build_review import review as build_review
from sdk.project import ProjectService, ProjectError
from sdk.script_branches import snapshot, review, state_key


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
class ScriptBranchWorkflow(unittest.TestCase):
    def project(self, directory, scene):
        project = ProjectService(Path(directory))
        project.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'], scene), os.environ['LEGAIA_DISC_BIN'])
        return project

    def apply(self, project, owner, identifier, value):
        inspected, _ = review(project, owner, identifier, value)
        project.command(dict(type='set_branch', entity=owner, branch_id=identifier, value=value,
                             review_key=inspected['review']['review_key']))
        return inspected

    def readback(self, project, scene):
        with _disc_context(project.disc_path) as (_, _, mapping, archive):
            carrier = read_man_source(archive, *_bounded_scene_range(archive, mapping, scene), scene)
        assessment = build_review(project)
        self.assertTrue(assessment['normal_build_ready'], assessment['blockers'])
        result = build_project(project)
        self.assertEqual(assessment['assessment']['report'], result['report'])
        with zipfile.ZipFile(result['path']) as package:
            suffix = 'bin' if carrier.kind == 'raw_streaming_man' else 'lzs'
            payload = package.read(f'assets/{scene}-man.{suffix}')
        decoded = payload if suffix == 'bin' else decompress_lzs(payload, len(carrier.payload))[0]
        return carrier.payload, decoded, result, json.loads(Path(result['audit']).read_text(encoding='utf-8'))

    def test_composed_dialogue_flag_review_history_and_compressed_build(self):
        from sdk.script_branches import _compose
        from importer.branch_authoring import BranchAuthoringContext
        with tempfile.TemporaryDirectory() as directory, _disc_context(os.environ['LEGAIA_DISC_BIN']):
            p = self.project(directory, 'town01')
            imported = deepcopy(p.imports)
            owner = 'scene://town01/actors/man-p1/0002'
            identifier = 'script://town01/actors/man-p1/0002/branch/001f'
            first = snapshot(p, owner)
            self.assertEqual(first['targets'][0]['target_pc'], 15)
            self.assertIn({'pc': 15, 'mnemonic': 'MES_SEGMENT'}, first['destinations'])
            stale, _ = review(p, owner, identifier, {'target_pc': 11})
            flag = p.flag_options(owner)['targets'][0]
            p.command(dict(type='set_flag_bit', entity_id=owner, flag_id=flag['semantic_id'], values={'bit': 3}))
            with self.assertRaises(ProjectError):
                p.command(dict(type='set_branch', entity=owner, branch_id=identifier, value={'target_pc': 11}, review_key=stale['review']['review_key']))
            run = p.dialogue_options(owner)['runs'][0]
            p.command(dict(type='set_dialogue_text', entity_id=owner, run_id=run['semantic_id'], text='SDK'))
            inspected = self.apply(p, owner, identifier, {'target_pc': 11})
            self.assertEqual(inspected['review']['audit'][0]['changed_byte_offsets'], [4791])
            self.assertEqual(next(row['operands']['bit'] for row in inspected['review']['proposed_report']['instructions'] if row['mnemonic'] == 'CFLAG_SET'), 3)
            self.assertTrue(inspected['review']['proposed_report']['dialogues'][0]['text'].startswith('SDK'))
            current = deepcopy(p.overrides)
            p.undo(); self.assertNotIn('ScriptBranches', p.overrides[owner])
            p.redo(); self.assertEqual(p.overrides, current)
            p.save(); q = ProjectService.open(p.root); self.assertEqual(q.overrides, current)
            self.assertEqual(q.imports, imported)
            original, decoded, result, audit = self.readback(q, 'town01')
            source = q._dialogue_context(owner); context = BranchAuthoringContext(source)
            expected, _ = context.patch_composed(_compose(source, owner, q.overrides[owner]), q.overrides[owner]['ScriptBranches']['entries'])
            self.assertEqual(decoded, expected)
            spans = {offset for row in audit['edits'] for offset in range(row['decoded_byte_offset'], row['decoded_byte_offset'] + row.get('byte_length', 1))}
            self.assertTrue(all(a == b or offset in spans for offset, (a, b) in enumerate(zip(original, decoded))))
            branch = next(row for row in result['report']['changes'] if row['scope'] == 'script-branch-target-only')
            self.assertEqual((branch['asset_id'], branch['owner_id'], branch['before'], branch['after']), (identifier, owner, 15, 11))
            self.assertIn('script branch destinations', package_change_kinds(audit['edits']))
            no_op, _ = review(q, owner, identifier, {'target_pc': 11})
            self.assertTrue(no_op['review']['no_op'])
            self.apply(q, owner, identifier, None)
            self.assertNotIn('ScriptBranches', q.overrides[owner])
            self.assertEqual(snapshot(q, owner)['targets'][0]['current_target_pc'], 15)

    def test_retail_partition_two_field68_history_and_exact_package_word(self):
        with tempfile.TemporaryDirectory() as directory:
            p = self.project(directory, 'town01')
            imported = deepcopy(p.imports)
            owner = 'scene://town01/scripts/man-p2/0015'
            identifier = 'script://town01/scripts/man-p2/0015/branch/0017'
            row = next(r for r in snapshot(p, owner)['targets'] if r['semantic_id'] == identifier)
            self.assertEqual((row['mnemonic'], row['target_pc'], row['target_context']),
                             ('FIELD_68_BRANCH', 50, 0))
            reviewed = self.apply(p, owner, identifier, {'target_pc': 12})
            self.assertEqual(reviewed['review']['audit'][0]['changed_byte_offsets'], [40645, 40646])
            authored = deepcopy(p.overrides)
            p.undo(); self.assertNotIn('ScriptBranches', p.overrides.get(owner, {}))
            p.redo(); self.assertEqual(p.overrides, authored)
            p.save(); q = ProjectService.open(p.root)
            self.assertEqual(q.overrides, authored)
            self.assertEqual(q.imports, imported)
            original, decoded, result, _ = self.readback(q, 'town01')
            # Independent native arithmetic: word base PC26, target PC12,
            # signed delta -14. The extended selector and every other byte stay retail.
            self.assertEqual(original[40645:40647], bytes.fromhex('1800'))
            expected = bytearray(original); expected[40645:40647] = bytes.fromhex('f2ff')
            self.assertEqual(decoded, expected)
            self.assertEqual(len(result['report']['changes']), 1)
            self.assertEqual(result['report']['changes'][0]['scope'], 'script-branch-target-only')

    def test_raw_streaming_build_exact_words_and_operand_file_bundle(self):
        from sdk.script_operand_files import export_file, review as file_review
        from sdk.script_operand_bundle import export_file as bundle_export, review as bundle_review
        with tempfile.TemporaryDirectory() as directory, _disc_context(os.environ['LEGAIA_DISC_BIN']):
            p = self.project(directory, 'dolk2')
            owner = 'scene://dolk2/actors/man-p1/0002'
            identifier = 'script://dolk2/actors/man-p1/0002/branch/001c'
            self.apply(p, owner, identifier, {'target_pc': 9})
            original, decoded, result, audit = self.readback(p, 'dolk2')
            self.assertEqual(len(decoded), 44036)
            self.assertEqual([i for i, (a, b) in enumerate(zip(original, decoded)) if a != b], [7481, 7482])
            self.assertEqual(decoded[7481:7483], b'\xec\xff')
            self.assertTrue(audit['validation']['raw_MAN_structural_round_trip'])
            content = json.dumps(export_file(p, owner))
            p.undo()
            report = file_review(p, owner, content)
            p.command(dict(type='import_script_operands', entity_id=owner, content=content, review_key=report['review_key']))
            self.assertEqual(p.overrides[owner]['ScriptBranches']['entries'][identifier], {'target_pc': 9})
            bundle = json.dumps(bundle_export(p)); p.undo()
            report = bundle_review(p, bundle)
            p.command(dict(type='import_script_operand_bundle', content=bundle, review_key=report['review_key']))
            self.assertEqual(p.overrides[owner]['ScriptBranches']['entries'][identifier], {'target_pc': 9})
            p.undo(); self.assertNotIn(owner, p.overrides)

    def test_rejected_destinations_and_stale_review_do_not_mutate_history(self):
        with tempfile.TemporaryDirectory() as directory, _disc_context(os.environ['LEGAIA_DISC_BIN']):
            p = self.project(directory, 'town01')
            owner = 'scene://town01/actors/man-p1/0002'
            identifier = 'script://town01/actors/man-p1/0002/branch/001f'
            baseline = deepcopy((p.overrides, p.undo_stack, p.redo_stack))
            for value in ({'target_pc': 16}, {'target_pc': 35}, {'target_pc': 32768}, {'target_pc': True}, {'target_pc': -1}, {'target_pc': 11, 'mask': 255}):
                with self.subTest(value=value), self.assertRaises((ProjectError, RetailImportError)):
                    review(p, owner, identifier, value)
                self.assertEqual((p.overrides, p.undo_stack, p.redo_stack), baseline)
            inspected, _ = review(p, owner, identifier, {'target_pc': 11})
            p.name += ' changed'
            self.assertNotEqual(state_key(p), inspected['state_key'])
            with self.assertRaises(ProjectError):
                p.command(dict(type='set_branch', entity=owner, branch_id=identifier, value={'target_pc': 11}, review_key=inspected['review']['review_key']))
            self.assertEqual((p.overrides, p.undo_stack, p.redo_stack), baseline)


if __name__ == '__main__':
    unittest.main()
