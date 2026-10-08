"""Retail-bound portable animation presets retain exact bytes and clone ownership."""
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest

from importer.core import ImportError as NativeError
from sdk.project import ProjectService, ProjectError
from sdk.project_copy import source_key
from sdk.npc_presets import review as instance_review, proposal_view
from sdk.npc_animation_operands import review as animation_review
from sdk.npc_current_script import inspect
from sdk.template_files import export_file, parse, review as transfer_review
import test_npc_animation_operand_workflow as workflow
TARGET = "script://map02/actors/man-p1/0003/animation-operands/000e"


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'Private Retail disc required')
class NpcAnimationPresetTests(unittest.TestCase):
    def captured(self, root):
        p, identity, target = workflow.NpcAnimationOperandWorkflow().project(root)
        retail = bytes.fromhex(inspect(p, identity)['inspection']['record']['raw_hex'])
        request = dict(entity_id=identity, entries={TARGET: dict(animation_operand=255)})
        review = animation_review(p, request)
        p.command(dict(type='set_actor_draft_animation_operands', **request, review_key=review['review_key']))
        p.command(dict(type='create_npc_preset', entity_id=identity, name='Animation argument preset'))
        return p, identity, next(iter(p.actor_templates)), retail

    def test_capture_transfer_instance_literal_current_history_and_independence(self):
        with tempfile.TemporaryDirectory() as raw:
            p, original, template_id, retail = self.captured(Path(raw)/'source')
            frozen = deepcopy(p.actor_templates[template_id])
            value = export_file(p, template_id)
            self.assertEqual(value['schema_version'], 'legaia.npc-preset-file.v13')
            self.assertEqual(parse(json.dumps(value)), value)
            clear = dict(entity_id=original, entries={})
            report = animation_review(p, clear)
            p.command(dict(type='set_actor_draft_animation_operands', **clear, review_key=report['review_key']))
            self.assertEqual(p.actor_templates[template_id], frozen)
            target = ProjectService(Path(raw)/'target')
            target.import_metadata(deepcopy(p.imports[p.active_scene]), p.disc_path)
            imports = deepcopy(target.imports)
            content = json.dumps(value)
            before = deepcopy((target._document(), target.undo_stack, target.redo_stack))
            transfer = transfer_review(target, content, 'Transferred animation arguments')
            self.assertEqual(before, (target._document(), target.undo_stack, target.redo_stack))
            target.command(dict(type='import_actor_template', content=content, name='Transferred animation arguments', review_key=transfer['review_key']))
            request = dict(template_id=transfer['template']['id'], name='Animation argument instance', position=dict(x=192,z=576), expected_source_key=source_key(target))
            before = deepcopy((target._document(), target.undo_stack, target.redo_stack))
            proposal = instance_review(target, request)
            view = proposal_view(target, proposal)
            expected = bytearray(retail)
            self.assertEqual(expected[16:17], bytes([0]))
            expected[16:17] = bytes([255])
            self.assertEqual(inspect(view, proposal['entity_id'])['inspection']['record']['raw_hex'], expected.hex())
            self.assertEqual(before, (target._document(), target.undo_stack, target.redo_stack))
            target.command(dict(type='instantiate_npc_preset', **request, review_key=proposal['review_key']))
            self.assertEqual(len(target.undo_stack), len(before[1])+1)
            self.assertEqual(inspect(target, proposal['entity_id'])['inspection']['record']['raw_hex'], expected.hex())
            saved = deepcopy(target._document())
            target.undo(); self.assertEqual(target._document(), before[0])
            target.redo(); self.assertEqual(target._document(), saved)
            self.assertEqual(ProjectService.open(target.save())._document(), saved)
            own = dict(entity_id=proposal['entity_id'], entries={TARGET: dict(animation_operand=3)})
            changed = animation_review(target, own)
            target.command(dict(type='set_actor_draft_animation_operands', **own, review_key=changed['review_key']))
            self.assertEqual(target.actor_templates[transfer['template']['id']]['components']['NpcDraft']['animation_operands'], frozen['components']['NpcDraft']['animation_operands'])
            self.assertEqual(target.imports, imports)
            evidence = os.environ.get('LEGAIA_NPC_ANIMATION_PRESET_EVIDENCE')
            if evidence:
                out = Path(evidence); out.mkdir(parents=True, exist_ok=True)
                (out/'fixture.json').write_text(json.dumps(dict(file=value, transfer=transfer, request=request, proposal=proposal, state=dict(scene=dict(id=target.active_scene),project=dict(mode='edit'),project_copy_source_key=proposal['project_source_key'],scene_preview_source_key=proposal['scene_preview_source_key'],actor_templates=[transfer['template']])), indent=2), encoding='utf-8')

    def test_forged_animations_downgrade_and_stale_review_refuse_without_mutation(self):
        with tempfile.TemporaryDirectory() as raw:
            p, original, template_id, _ = self.captured(raw)
            value = export_file(p, template_id)
            before = deepcopy((p._document(), p.undo_stack, p.redo_stack))
            for fields in ({'animation_operand': True}, {'animation_operand': -1}, {'animation_operand': 256}, {'model_id': 1, 'animation_frame': 0, 'tween_frames': 0}, {}):
                forged = deepcopy(value)
                forged['template']['components']['NpcDraft']['animation_operands']['entries'][TARGET] = fields
                with self.assertRaises((ProjectError, NativeError)):
                    transfer_review(p, json.dumps(forged), 'Forged')
            forged = deepcopy(value); forged['schema_version'] = 'legaia.npc-preset-file.v12'
            with self.assertRaises(ProjectError): parse(json.dumps(forged))
            forged = deepcopy(value)
            forged['template']['components']['NpcDraft']['animation_operands']['entries'] = {TARGET[:-4]+'ffff': {'animation_operand': 1}}
            with self.assertRaises((ProjectError, NativeError)): transfer_review(p, json.dumps(forged), 'Forged')
            self.assertEqual(before, (p._document(), p.undo_stack, p.redo_stack))
            request = dict(template_id=template_id,name='New instance',position=dict(x=192,z=576),expected_source_key=source_key(p))
            proposal = instance_review(p, request)
            p.command(dict(type='rename_actor_draft',entity_id=original,name='Changed'))
            before = deepcopy((p._document(),p.undo_stack,p.redo_stack))
            with self.assertRaises(ProjectError): p.command(dict(type='instantiate_npc_preset', **request, review_key=proposal['review_key']))
            self.assertEqual(before, (p._document(),p.undo_stack,p.redo_stack))


if __name__ == '__main__': unittest.main()
