from copy import deepcopy
from hashlib import sha256
from unittest.mock import patch
import unittest
from sdk.project import ProjectError
from sdk.controller_component_reset import review
from sdk.controller_system_flags import prepare
from importer.controller_system_flags import ControllerSystemFlagAuthoringContext
import test_controller_party_selector_workflow as fixtures
from test_controller_branches import source, OWNER


class ControllerComponentReset(unittest.TestCase):
    def setUp(self):
        fixture = fixtures.ControllerPartySelectorWorkflow()
        fixture.setUp(); self.addCleanup(fixture.doCleanups)
        self.p, self.context = fixture.p, fixture.context

    def command(self, result):
        self.p.command(dict(type='reset_controller_component', entity_id=OWNER,
                            component=result['component'], review_key=result['review_key']))

    def test_all_eleven_resets_retain_independent_literal_bytes_and_other_components(self):
        fields = {
            'ControllerSystemFlags': ('system-flag/0005', {'index':4095}, 62, bytes.fromhex('6fff')),
            'ControllerBranches': ('branch/0065', {'target_pc':7}, 159, bytes.fromhex('a1ff')),
            'ControllerTileRects': ('tile-rect/0007', dict(column_start=1,row_start=2,column_end=3,row_end=4,value=255),66,bytes([1,2,3,4,255])),
            'ControllerFades': ('fade/000e',dict(selector=1,signed_words=[1,2,3]),73,bytes.fromhex('01010002000300')),
            'ControllerTableCopies': ('table-copy/0017',dict(signed_words=list(range(1,17))),82,b''.join(w.to_bytes(2,'little',signed=True) for w in range(1,17))),
            'ControllerWordTriplets': ('word-triplet/0039',dict(selector=255,signed_words=[-32768,32767,-1]),116,bytes.fromhex('ff0080ff7fffff')),
            'ControllerThreeWords': ('three-word/0042',dict(signed_words=[-32768,32767,-1]),125,bytes.fromhex('0080ff7fffff')),
            'ControllerFiveWords': ('five-word/004a',dict(signed_words=[1,2,3,4,5]),133,bytes.fromhex('01000200030004000500')),
            'ControllerGlobalBytes': ('global-byte/0056',dict(byte_values=[0,255,31,64],parameters_i16=[-32768,32767]),145,bytes.fromhex('00ff1f400080ff7f')),
            'ControllerSceneBytes': ('scene-byte/0060',dict(value=255),155,bytes([255])),
            'ControllerPartySelectors': ('party-selector/0063',dict(party_selector=7),157,bytes([0x2f])),
        }
        source_hash = sha256(self.context._source.verified_record(OWNER)[1]).hexdigest()
        components = {family:dict(source_record_sha256=source_hash, entries={OWNER.replace('scene://','script://')+'/'+suffix:value})
                      for family,(suffix,value,_,_) in fields.items()}
        self.p.overrides[OWNER] = deepcopy(components)
        expected = bytearray(self.context._man)
        for _,_,at,raw in fields.values(): expected[at:at+len(raw)] = raw
        self.assertEqual(prepare(self.p,OWNER)[6],bytes(expected))
        imports = deepcopy(self.p.imports)
        for family,(_,_,at,raw) in fields.items():
            before = deepcopy((self.p._document(),self.p.undo_stack,self.p.redo_stack))
            result = review(self.p,OWNER,family)
            self.assertEqual(before,(self.p._document(),self.p.undo_stack,self.p.redo_stack))
            self.assertFalse(result['project_changed']); self.assertFalse(result['gameplay_verified'])
            self.command(result)
            candidate = bytearray(expected); candidate[at:at+len(raw)] = self.context._man[at:at+len(raw)]
            self.assertEqual(prepare(self.p,OWNER)[6],bytes(candidate))
            self.assertEqual(self.p.overrides[OWNER],{k:v for k,v in components.items() if k!=family})
            self.assertEqual(len(self.p.undo_stack),len(before[1])+1)
            self.p.undo(); self.assertEqual(self.p.overrides[OWNER],components)
            self.p.redo(); self.assertNotIn(family,self.p.overrides[OWNER]); self.p.undo()
        self.assertEqual(imports,self.p.imports)

    def test_multiple_entries_last_family_reset_persistence_and_detachment(self):
        src,man = source(b'\x61\x23\x4c\x08\x4c\x2a\xcc\xf8\x2b\x26\xf6\xff')
        ctx = ControllerSystemFlagAuthoringContext(src)
        with patch('sdk.controller_system_flags.load_controller_system_flag_context',return_value=ctx):
            from sdk.controller_party_selectors import review as operand_review
            for pc,value in [(7,1),(9,3),(11,7)]:
                identity=OWNER.replace('scene://','script://')+f'/party-selector/{pc:04x}'
                r=operand_review(self.p,OWNER,identity,{'party_selector':value})
                self.p.command(dict(type='set_controller_party_selector',entity_id=OWNER,operand_id=identity,value={'party_selector':value},review_key=r['review_key']))
            authored=deepcopy(self.p.overrides); result=review(self.p,OWNER,'ControllerPartySelectors')
            self.assertEqual(result['removed_operand_count'],3); self.assertEqual(result['changed_decoded_byte_offsets'],[65,67,70])
            detached=review(self.p,OWNER,'ControllerPartySelectors'); detached['authored']['entries'].clear()
            self.assertEqual(self.p.overrides,authored)
            self.command(result); self.assertFalse(self.p.overrides); self.assertEqual(prepare(self.p,OWNER)[6],man)
            from sdk.project import ProjectService
            self.assertEqual(ProjectService.open(self.p.save())._document(),self.p._document())
            self.p.undo(); self.assertEqual(self.p.overrides,authored); self.p.redo(); self.assertFalse(self.p.overrides)

    def test_stale_source_missing_family_modes_and_exact_command_refuse_without_mutation(self):
        from sdk.controller_party_selectors import review as operand_review
        identity=OWNER.replace('scene://','script://')+'/party-selector/0063'
        r=operand_review(self.p,OWNER,identity,{'party_selector':7})
        self.p.command(dict(type='set_controller_party_selector',entity_id=OWNER,operand_id=identity,value={'party_selector':7},review_key=r['review_key']))
        result=review(self.p,OWNER,'ControllerPartySelectors')
        from sdk.controller_system_flags import review as flag_review
        flag_id=OWNER.replace('scene://','script://')+'/system-flag/0005'
        r=flag_review(self.p,OWNER,flag_id,{'index':3})
        self.p.command(dict(type='set_controller_system_flag_selector',entity_id=OWNER,operand_id=flag_id,value={'index':3},review_key=r['review_key']))
        before=deepcopy((self.p._document(),self.p.undo_stack,self.p.redo_stack))
        with self.assertRaises(ProjectError): self.command(result)
        for family in ('Transform','ControllerFades',None,True):
            with self.assertRaises(ProjectError): review(self.p,OWNER,family)
        with self.assertRaises(ProjectError): review(self.p,OWNER.replace('fixture','foreign'),'ControllerPartySelectors')
        command=dict(type='reset_controller_component',entity_id=OWNER,component='ControllerPartySelectors',review_key=review(self.p,OWNER,'ControllerPartySelectors')['review_key'],extra=True)
        with self.assertRaises(ProjectError): self.p.command(command)
        self.assertEqual(before,(self.p._document(),self.p.undo_stack,self.p.redo_stack))
        self.p.mode='live'
        with self.assertRaises(ProjectError): review(self.p,OWNER,'ControllerPartySelectors')
        self.p.mode='edit'; self.p.overrides[OWNER]['ControllerPartySelectors']['source_record_sha256']='f'*64
        with self.assertRaises(ProjectError): review(self.p,OWNER,'ControllerPartySelectors')

    def test_retail_equal_authored_entries_reset_history_without_native_byte_changes(self):
        source_hash=sha256(self.context._source.verified_record(OWNER)[1]).hexdigest()
        identity=OWNER.replace('scene://','script://')+'/party-selector/0063'
        self.p.overrides[OWNER]={'ControllerPartySelectors':dict(source_record_sha256=source_hash,entries={identity:{'party_selector':2}})}
        result=review(self.p,OWNER,'ControllerPartySelectors')
        self.assertFalse(result['native_bytes_changed']); self.assertEqual(result['changed_decoded_byte_offsets'],[])
        self.assertEqual(result['current_record_sha256'],result['proposed_record_sha256'])
        self.command(result); self.assertFalse(self.p.overrides); self.assertEqual(len(self.p.undo_stack),1)
        self.p.undo(); self.assertIn('ControllerPartySelectors',self.p.overrides[OWNER])
