from copy import deepcopy
import json
import unittest
import test_controller_party_selector_workflow as fixtures
from test_controller_branches import OWNER
from sdk.controller_operand_files import export_file, review, parse
from sdk.controller_system_flags import prepare
from sdk.project import ProjectError, ProjectService


class ControllerOperandFiles(unittest.TestCase):
    def setUp(self):
        fixture=fixtures.ControllerPartySelectorWorkflow();fixture.setUp();self.addCleanup(fixture.doCleanups)
        self.p=fixture.p;self.context=fixture.context

    def apply(self, content, result):
        self.p.command(dict(type='import_controller_operand_file',entity_id=OWNER,content=content,review_key=result['review_key']))

    def test_all_eleven_transfer_literal_man_atomic_history_export_and_persistence(self):
        fields={
            'ControllerSystemFlags':('system-flag/0005',{'index':4095},62,bytes.fromhex('6fff')),
            'ControllerBranches':('branch/0065',{'target_pc':7},159,bytes.fromhex('a1ff')),
            'ControllerTileRects':('tile-rect/0007',dict(column_start=1,row_start=2,column_end=3,row_end=4,value=255),66,bytes([1,2,3,4,255])),
            'ControllerFades':('fade/000e',dict(selector=1,signed_words=[1,2,3]),73,bytes.fromhex('01010002000300')),
            'ControllerTableCopies':('table-copy/0017',dict(signed_words=list(range(1,17))),82,b''.join(w.to_bytes(2,'little',signed=True) for w in range(1,17))),
            'ControllerWordTriplets':('word-triplet/0039',dict(selector=255,signed_words=[-32768,32767,-1]),116,bytes.fromhex('ff0080ff7fffff')),
            'ControllerThreeWords':('three-word/0042',dict(signed_words=[-32768,32767,-1]),125,bytes.fromhex('0080ff7fffff')),
            'ControllerFiveWords':('five-word/004a',dict(signed_words=[1,2,3,4,5]),133,bytes.fromhex('01000200030004000500')),
            'ControllerGlobalBytes':('global-byte/0056',dict(byte_values=[0,255,31,64],parameters_i16=[-32768,32767]),145,bytes.fromhex('00ff1f400080ff7f')),
            'ControllerSceneBytes':('scene-byte/0060',dict(value=255),155,bytes([255])),
            'ControllerPartySelectors':('party-selector/0063',dict(party_selector=7),157,bytes([0x2f])),
        }
        file=export_file(self.p,OWNER);self.assertFalse(file['components']);expected=bytearray(self.context._man)
        for family,(suffix,values,at,raw) in fields.items():
            file['components'][family]={'entries':{OWNER.replace('scene://','script://')+'/'+suffix:values}};expected[at:at+len(raw)]=raw
        content=json.dumps(file);before=deepcopy((self.p._document(),self.p.undo_stack,self.p.redo_stack,self.p.imports))
        result=review(self.p,OWNER,content);self.assertEqual(before,(self.p._document(),self.p.undo_stack,self.p.redo_stack,self.p.imports));self.assertEqual(result['change_count'],11)
        self.apply(content,result);self.assertEqual(len(self.p.undo_stack),1);self.assertEqual(prepare(self.p,OWNER)[6],bytes(expected))
        saved=deepcopy(self.p._document());self.assertEqual(ProjectService.open(self.p.save())._document(),saved)
        self.assertEqual(parse(json.dumps(export_file(self.p,OWNER))),file)
        result['after'].clear();self.assertEqual(len(self.p.overrides[OWNER]),11)
        self.p.undo();self.assertEqual(self.p._document(),before[0]);self.p.redo();self.assertEqual(self.p._document(),saved)
        result=review(self.p,OWNER,content);self.assertTrue(result['no_op']);self.assertEqual(result['change_count'],0);self.apply(content,result);self.assertEqual(len(self.p.undo_stack),1)

    def test_sparse_null_retail_equal_stale_invalid_and_failed_transfer_are_atomic(self):
        file=export_file(self.p,OWNER);party=OWNER.replace('scene://','script://')+'/party-selector/0063';flag=OWNER.replace('scene://','script://')+'/system-flag/0005'
        file['components']={'ControllerPartySelectors':{'entries':{party:{'party_selector':7}}},'ControllerSystemFlags':{'entries':{flag:{'index':3}}}}
        content=json.dumps(file);self.apply(content,review(self.p,OWNER,content));original=deepcopy(self.p.overrides)
        file['components']={'ControllerPartySelectors':{'entries':{party:None}}};content=json.dumps(file);result=review(self.p,OWNER,content);self.apply(content,result)
        self.assertEqual(set(self.p.overrides[OWNER]),{'ControllerSystemFlags'});self.p.undo();self.assertEqual(self.p.overrides,original)
        file['components']['ControllerPartySelectors']['entries'][party]={'party_selector':2};content=json.dumps(file);self.apply(content,review(self.p,OWNER,content));self.assertNotIn('ControllerPartySelectors',self.p.overrides[OWNER]);self.p.undo()
        before=deepcopy((self.p._document(),self.p.undo_stack,self.p.redo_stack))
        for values in ({'party_selector':True},{'party_selector':2.0},{'party_selector':8}):
            file['components']['ControllerPartySelectors']['entries'][party]=values
            with self.assertRaises(ProjectError):review(self.p,OWNER,json.dumps(file))
        file['components']['ControllerPartySelectors']['entries']={party.replace('0063','ffff'):None}
        with self.assertRaises(ProjectError):review(self.p,OWNER,json.dumps(file))
        self.assertEqual(before,(self.p._document(),self.p.undo_stack,self.p.redo_stack))
        file=export_file(self.p,OWNER);content=json.dumps(file);stale=review(self.p,OWNER,content);self.p.undo()
        with self.assertRaises(ProjectError):self.apply(content,stale)
        self.p.mode='live'
        with self.assertRaises(ProjectError):review(self.p,OWNER,content)

    def test_exact_source_parser_bounds_and_duplicate_keys(self):
        file=export_file(self.p,OWNER)
        for changed in [dict(file,extra=True),dict(file,source_import_sha256='f'*64),dict(file,source_record_sha256='f'*64),dict(file,scene_id='scene://foreign'),dict(file,owner_id='scene://foreign/controllers/man-p1/0000'),dict(file,components={'Transform':{'entries':{}}})]:
            with self.assertRaises(ProjectError):review(self.p,OWNER,json.dumps(changed))
        for content in ['{"a":1,"a":2}',json.dumps(file)+' '*65536,'{"x":NaN}',json.dumps(dict(file,components={'ControllerPartySelectors':{'entries':{str(i):None for i in range(257)}}}))]:
            with self.assertRaises(ProjectError):parse(content)
