"""Fixed native operands preserve dispatch, source ownership and opaque neighbors."""
import json, os, unittest
from pathlib import Path
from hashlib import sha256
from importer.core import ImportError
from importer.animation_operand_authoring import AnimationOperandAuthoringContext, patch_animation_operands_target
from importer.man_actor_structure import append_actor_donor
from importer.man_layout import read_man_layout
from importer.animation_operand_authoring import load_animation_operand_authoring_context
from test_importer_dialogue_authoring import fixture, ACTOR
from test_effect_color_authoring import END

MODEL = dict(model_id=0xffffff, animation_frame=65535, tween_frames=0)
EFFECT = dict(animation_operand=255)


class AnimationOperands(unittest.TestCase):
    def test_normal_extended_literal_fields_and_preserved_context(self):
        for header in (b'\x4c', b'\xcc\x07'):
            source = header+b'\x81\x01\x02\x03\x04\x05\x06\x07'+END
            result, audit = patch_animation_operands_target(source, 0, 0, MODEL, base_offset=100)
            at = len(header)+1
            self.assertEqual(result, source[:at]+b'\xff\xff\xff\xff\xff\0\0'+END)
            self.assertEqual([row['byte_length'] for row in audit], [3, 2, 2])
            self.assertEqual(audit[0]['decoded_byte_offset'], 100+at)
            self.assertEqual(patch_animation_operands_target(result, 0, 0, MODEL), (result, []))
        for header in (b'\x34', b'\xb4\x02'):
            for selector in (0x30, 0x3f):
                source = header+bytes([selector, 1])+END
                result, audit = patch_animation_operands_target(source, 0, 0, EFFECT)
                self.assertEqual(result, header+bytes([selector, 255])+END)
                self.assertEqual(len(audit), 1)
        for bad in ({}, dict(MODEL, model_id=True), dict(MODEL, model_id=0x1000000),
                    dict(MODEL, animation_frame=-1), dict(MODEL, tween_frames=65536), dict(MODEL, extra=1)):
            with self.assertRaises(ImportError):
                patch_animation_operands_target(b'\x4c\x81'+bytes(7)+END, 0, 0, bad)
        for bad in (dict(animation_operand=True), dict(animation_operand=256), dict(animation_operand=-1)):
            with self.assertRaises(ImportError):
                patch_animation_operands_target(b'\x34\x30\1'+END, 0, 0, bad)

    def test_multiple_instructions_same_record_rebase_and_whole_preimage(self):
        source, man = fixture(b'\x4c\x81\1\2\3\4\5\6\7\xb4\x02\x3f\1'+END)
        context = AnimationOperandAuthoringContext(source)
        targets = context.options(ACTOR)['targets']
        self.assertEqual(len(targets), 2)
        request = {targets[0]['semantic_id']: MODEL, targets[1]['semantic_id']: EFFECT}
        result, audit = context.patch(request)
        expected = bytearray(man)
        first, second = [row['decoded_byte_offset'] for row in targets]
        expected[first:first+7] = b'\xff\xff\xff\xff\xff\0\0'
        expected[second] = 255
        self.assertEqual(result, bytes(expected))
        self.assertEqual(len(audit), 4)
        self.assertEqual(context._man, man)
        appended, _ = append_actor_donor(man, sha256(man).hexdigest(), 1)
        rebased, changes = context.patch_appended(appended, request)
        expected = bytearray(appended)
        expected[first+3:first+10] = b'\xff\xff\xff\xff\xff\0\0'
        expected[second+3] = 255
        self.assertEqual(rebased, bytes(expected))
        self.assertEqual([row['decoded_byte_offset'] for row in changes], [row['decoded_byte_offset']+3 for row in audit])
        noop = {row['semantic_id']: row['values'] for row in targets}
        self.assertEqual(context.patch_appended(appended, noop), (appended, []))
        # A no-op still checks the context and selector, not only changed fields.
        for at in (first+3-1, second+3-2, second+3-1, first+3):
            forged = bytearray(appended); forged[at] ^= 1
            with self.assertRaises(ImportError): context.patch_appended(bytes(forged), noop)
        with self.assertRaises(ImportError): context.patch(request, original=result)
        with self.assertRaises(ImportError): context.patch_appended(rebased, request)

    def test_alias_unknown_unreached_and_identity_refusal(self):
        source, _ = fixture(b'\x34\x30\1'+END, alias=True)
        with self.assertRaises(ImportError): AnimationOperandAuthoringContext(source).options(ACTOR)
        source, _ = fixture(b'\x34\x30\1\xff')
        self.assertFalse(AnimationOperandAuthoringContext(source).options(ACTOR)['supported'])
        for record, pc in ((b'\x34\x30', 0), (END+b'\x34\x30\1', len(END)),
                           (b'\x34\x20\1'+END, 0), (b'\x34\x30\1'+END, True)):
            with self.assertRaises(ImportError): patch_animation_operands_target(record, 0, pc, EFFECT)
        source, _ = fixture(b'\x34\x30\1'+END)
        context = AnimationOperandAuthoringContext(source)
        for key in (None, 'script://fixture/actors/man-p1/0001/animation-operands/00005',
                    'script://foreign/actors/man-p1/0001/animation-operands/0005'):
            with self.assertRaises(ImportError): context.patch({key: EFFECT})


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'Private Retail disc required')
class RetailAnimationOperands(unittest.TestCase):
    def test_qualified_retail_inventory_and_literal_complete_man(self):
        evidence=[]; changed=0
        for scene in ('town01', 'map02'):
            context=load_animation_operand_authoring_context(Path(os.environ['LEGAIA_DISC_BIN']), scene)
            man=context._man; targets=[]; refusals=[]
            for row in read_man_layout(man)['records']:
                if row['partition'] not in (1,2): continue
                family='actors/man-p1' if row['partition']==1 else 'scripts/man-p2'
                owner=f"scene://{scene}/{family}/{row['record_index']:04d}"
                try:
                    report=context.options(owner)
                    targets.extend(report['targets'])
                    if not report['supported']: refusals.append(dict(owner=owner,reason=report['reason']))
                except ImportError as error:
                    refusals.append(dict(owner=owner,reason=str(error)))
            request={}; expected=bytearray(man)
            for target in targets:
                # Literal LE oracle independent of the writer and value validator.
                if target['mnemonic']=='SET_MODEL_ANIMATION':
                    values=dict(MODEL); literal=b'\xff\xff\xff\xff\xff\0\0'
                else:
                    values=dict(EFFECT); literal=b'\xff'
                request[target['semantic_id']]=values
                at=target['decoded_byte_offset']; expected[at:at+len(literal)]=literal
            result,audit=context.patch(request)
            self.assertEqual(result,bytes(expected)); self.assertEqual(context._man,man)
            self.assertEqual(read_man_layout(result),read_man_layout(man))
            self.assertEqual(context.patch({t['semantic_id']:t['values'] for t in targets}),(man,[]))
            changed+=len(audit)
            evidence.append(dict(scene=scene,decoded_man_sha256=sha256(man).hexdigest(),
                                 changed_man_sha256=sha256(result).hexdigest(),targets=targets,
                                 refusals=refusals,changed_fields=len(audit),complete_literal_man_equal=True))
        self.assertGreater(changed,0,'No qualified Retail source found; do not weaken decoder/ownership gates')
        output=os.environ.get('LEGAIA_ANIMATION_OPERAND_EVIDENCE')
        if output:
            path=Path(output);path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps(dict(schema='legaia.animation-operand-native-evidence.v1',
                reference_commit='d6e64c68ede25813d35db20980da82a1a025549b',scenes=evidence),indent=2)+'\n',encoding='utf-8')


if __name__ == '__main__': unittest.main()
