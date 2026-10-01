"""Signed source selectors preserve dispatch/record boundaries and audit spans."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from importer.core import ImportError
from importer.model_selector_authoring import ModelSelectorAuthoringContext, patch_model_selector_target
from importer.man_actor_structure import append_actor_donor
from importer.script_inspection import inspect_record
from importer.dialogue_authoring import DialogueAuthoringContext
from sdk.project import ProjectService
from sdk.build import _merge_model_selector_patch, build_report, package_change_kinds, BuildError
from test_importer_dialogue_authoring import fixture, ACTOR, literals
from test_project_workflow import synthetic_scene

END=b'\x3f\0\0\x06town01\1\2\3opaque'
class ModelSelectorTests(unittest.TestCase):
    def test_appended_extended_actor_context_must_match_source(self):
        source,man=fixture(b'\xcc\x07\x50\xef\0'+END)
        context=ModelSelectorAuthoringContext(source)
        target=context.options(ACTOR)['targets'][0]
        edits={target['semantic_id']:{'model_selector_signed':240}}
        appended,_=append_actor_donor(man,sha256(man).hexdigest(),1)
        valid,audit=context.patch_appended(appended,edits)
        self.assertEqual(audit[0]['appended_target_context'],7)
        changed_context=bytearray(appended)
        changed_context[audit[0]['decoded_byte_offset']-2]=8
        with self.assertRaisesRegex(ImportError,'instruction or preimage'):
            context.patch_appended(bytes(changed_context),edits)
        self.assertEqual(valid[audit[0]['decoded_byte_offset']-2],7)

    def test_partition_two_owner_signed_patch_and_persistence(self):
        _,original=fixture();region=0x2b+12;section=int.from_bytes(original[0x28:0x2b],'little')
        p2=bytes(4)+b'\x4c\x50\xef\0'+END
        man=bytearray(original[:region+section]+p2+original[region+section:])
        man[0x34:0x37]=section.to_bytes(3,'little');man[0x28:0x2b]=(section+len(p2)).to_bytes(3,'little');man=bytes(man)
        context=ModelSelectorAuthoringContext(DialogueAuthoringContext('fixture',man,literals(man),{}))
        owner='scene://fixture/scripts/man-p2/0000';target=context.options(owner)['targets'][0]
        self.assertEqual(target['pc'],4)
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.import_metadata(synthetic_scene())
            with patch.object(p,'_model_selector_context',return_value=context):
                p.command(dict(type='set_model_selector_target',entity_id=owner,model_selector_id=target['semantic_id'],values={'model_selector_signed':-1}))
                changed,_=context.patch(p.overrides[owner]['ScriptModelSelectors']['entries'])
                at=target['decoded_byte_offset'];self.assertEqual(changed[at:at+2],b'\xff\xff')
                self.assertEqual(changed[:at],man[:at]);self.assertEqual(changed[at+2:],man[at+2:])
                self.assertEqual(ProjectService.open(p.save()).overrides,p.overrides)

    def test_signed_ordinary_extended_and_appended_exact_span(self):
        for header in (b'\x4c\x50',b'\xcc\x07\x50'):
            record=header+b'\xef\0'+END
            for value in (-32768,-1,0,239,240,32767):
                result,audit=patch_model_selector_target(record,0,0,{'model_selector_signed':value})
                node=inspect_record(result,0)['instructions'][0]
                self.assertEqual(node['operands']['model_selector_signed'],value)
                self.assertEqual(node['operands']['high_pool_flag'],value>=240)
                self.assertEqual(result[:len(header)],header);self.assertEqual(result[len(header)+2:],END)
                self.assertTrue(all(i in (len(header),len(header)+1) for i,(a,b) in enumerate(zip(record,result)) if a!=b))
            for value in (True,-32769,32768,1.5):
                with self.assertRaises(ImportError):patch_model_selector_target(record,0,0,{'model_selector_signed':value})
        source,man=fixture(b'\x4c\x50\xef\0'+END);context=ModelSelectorAuthoringContext(source)
        target=context.options(ACTOR)['targets'][0];edits={target['semantic_id']:{'model_selector_signed':-1}}
        changed,audit=context.patch(edits);at=target['decoded_byte_offset']
        self.assertEqual(changed[at:at+2],b'\xff\xff')
        appended,_=append_actor_donor(man,sha256(man).hexdigest(),1)
        rebased,changes=context.patch_appended(appended,edits)
        self.assertEqual(changes[0]['decoded_byte_offset'],at+3);self.assertEqual(rebased[at+3:at+5],b'\xff\xff')
        with self.assertRaises(ImportError):context.patch_appended(rebased,edits)
        stopped,_=fixture(b'\x4c\x50\0\0\xff')
        self.assertFalse(ModelSelectorAuthoringContext(stopped).options(ACTOR)['supported'])

    def test_project_commands_history_save_clear(self):
        source,_=fixture(b'\x4c\x50\xef\0'+END);context=ModelSelectorAuthoringContext(source)
        key=context.options(ACTOR)['targets'][0]['semantic_id']
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.import_metadata(synthetic_scene())
            with patch.object(p,'_model_selector_context',return_value=context):
                p.command(dict(type='set_model_selector_target',entity_id=ACTOR,model_selector_id=key,values={'model_selector_signed':240}))
                options=p.model_selector_options(ACTOR)['targets'][0]
                self.assertEqual(options['values']['model_selector_signed'],239)
                self.assertEqual(options['effective_values']['model_selector_signed'],240)
                p.undo();self.assertNotIn(ACTOR,p.overrides);p.redo()
                restored=ProjectService.open(p.save());self.assertEqual(restored.overrides,p.overrides)
                p.command(dict(type='clear_model_selector_target',entity_id=ACTOR,model_selector_id=key))
                self.assertNotIn(ACTOR,p.overrides);p.undo();self.assertIn('ScriptModelSelectors',p.overrides[ACTOR])

    def test_build_merge_signed_audit_and_unaudited_bytes(self):
        source,man=fixture(b'\x4c\x50\xef\0'+END);context=ModelSelectorAuthoringContext(source)
        target=context.options(ACTOR)['targets'][0];key=target['semantic_id'];values={'model_selector_signed':-1}
        changed,audit=context.patch({key:values});expected={key:dict(target,requested_values=values)}
        self.assertEqual(_merge_model_selector_patch(man,man,changed,audit,expected,[]),changed)
        for mutation in ('extra','hash','overlap','value','pc'):
            candidate=changed;changes=deepcopy(audit);prior=[]
            if mutation=='extra':candidate=bytes([changed[0]^1])+changed[1:]
            if mutation=='hash':changes[0]['source_record_sha256']='stale'
            if mutation=='overlap':prior=[{'decoded_byte_offset':target['decoded_byte_offset']+1}]
            if mutation=='value':changes[0]['after_selector']=0
            if mutation=='pc':changes[0]['pc']+=1
            with self.assertRaises(BuildError):_merge_model_selector_patch(man,man,candidate,changes,expected,prior)
        row=dict(audit[0],scene='fixture',semantic_id=ACTOR,scope='script-model-selector-only')
        result=build_report(dict(edits=[row],validation={},overlays=[]))['changes'][0]
        self.assertEqual(result['asset_id'],key);self.assertEqual((result['before'],result['after']),(239,-1))
        self.assertEqual(package_change_kinds([row]),['script model selectors'])

if __name__=='__main__':unittest.main()
