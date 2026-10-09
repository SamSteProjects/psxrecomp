from copy import deepcopy
from contextlib import nullcontext
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.controller_global_bytes import snapshot,review,COMPONENT
from sdk.controller_system_flags import review as selector_review,snapshot as selector_snapshot
from sdk.controller_branches import review as branch_review,snapshot as branch_snapshot
from importer.controller_system_flags import ControllerSystemFlagAuthoringContext
from test_controller_branches import source,OWNER
from test_project_workflow import synthetic_scene

ID='script://fixture/controllers/man-p1/0000/global-byte/0056'
VALUES=dict(byte_values=[0,255,31,64],parameters_i16=[-32768,32767])


class ControllerGlobalByteWorkflow(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.p=ProjectService(Path(self.temp.name));self.p.import_metadata(synthetic_scene())
        src,_=source(b'\x61\x23\x4c\x83\x01\x02\x03\x04\x05\x4c\x90\x00'+bytes(6)+b'\x4c\x9e'+bytes(32)+b'\x4c\xd8\x00'+bytes(6)+b'\x4c\xe6'+bytes(6)+b'\x43\x11'+bytes(10)+b'\x43\x03'+bytes(8)+b'\x4c\xdf\x01\x26\xa1\xff')
        self.context=ControllerSystemFlagAuthoringContext(src)
        for name,value in [('importer.pipeline._disc_context',nullcontext()),('sdk.resources._verify',None),('sdk.controller_system_flags.load_controller_system_flag_context',self.context)]:
            mock=patch(name,return_value=value);mock.start();self.addCleanup(mock.stop)

    def apply(self,value):
        r=review(self.p,OWNER,ID,value);self.p.command(dict(type='set_controller_global_byte',entity_id=OWNER,operand_id=ID,value=value,review_key=r['review_key']));return r

    def selector(self,value):
        operand='script://fixture/controllers/man-p1/0000/system-flag/0005';r=selector_review(self.p,OWNER,operand,value)
        self.p.command(dict(type='set_controller_system_flag_selector',entity_id=OWNER,operand_id=operand,value=value,review_key=r['review_key']))

    def branch(self,value):
        operand='script://fixture/controllers/man-p1/0000/branch/0063';r=branch_review(self.p,OWNER,operand,value)
        self.p.command(dict(type='set_controller_branch',entity_id=OWNER,operand_id=operand,value=value,review_key=r['review_key']))

    def test_review_history_save_open_reset_and_authored_asset(self):
        before=deepcopy((self.p._document(),self.p.undo_stack,self.p.redo_stack));r=review(self.p,OWNER,ID,VALUES)
        self.assertEqual(before,(self.p._document(),self.p.undo_stack,self.p.redo_stack));self.assertEqual(r['changed_decoded_byte_offsets'],[146,147,148,150,151,152]);self.assertFalse(r['project_changed']);self.assertFalse(r['gameplay_verified'])
        self.apply(VALUES);saved=deepcopy(self.p.overrides);t=snapshot(self.p,OWNER)['targets'][0]
        self.assertEqual(t['values'],dict(byte_values=[0]*4,parameters_i16=[0]*2));self.assertEqual(t['current_values'],VALUES);self.assertEqual(t['authored_values'],VALUES)
        self.assertIn(COMPONENT,self.p.authored_assets()[0]['authored']);self.p.undo();self.assertFalse(self.p.overrides);self.p.redo();self.assertEqual(self.p.overrides,saved)
        opened=ProjectService.open(self.p.save());self.assertEqual(opened._document(),self.p._document());self.assertEqual(opened.imports,self.p.imports)
        self.apply(None);self.assertFalse(self.p.overrides);self.p.undo();self.assertEqual(self.p.overrides,saved)
        self.apply(t['values']);self.assertFalse(self.p.overrides)

    def test_stale_review_bad_values_owner_hash_modes_and_mixed_components_refuse(self):
        stale=review(self.p,OWNER,ID,VALUES);self.selector({'index':4095});before=deepcopy((self.p._document(),self.p.undo_stack,self.p.redo_stack))
        with self.assertRaises(ProjectError):self.p.command(dict(type='set_controller_global_byte',entity_id=OWNER,operand_id=ID,value=VALUES,review_key=stale['review_key']))
        for value in [dict(byte_values=[True,0,0,0],parameters_i16=[0,0]),dict(byte_values=[256,0,0,0],parameters_i16=[0,0]),dict(byte_values=[0]*4,parameters_i16=[32768,0]),dict(byte_values=[0]*3,parameters_i16=[0,0]),dict(byte_values=[0]*4,parameters_i16=[0]),dict(VALUES,extra=0),{}]:
            with self.assertRaises(ProjectError):review(self.p,OWNER,ID,value)
        for owner,operand in [(OWNER.replace('/controllers/','/actors/'),ID),(OWNER.replace('fixture','other'),ID),(OWNER,ID[:-4]+'000f')]:
            with self.assertRaises(ProjectError):review(self.p,owner,operand,VALUES)
        self.assertEqual(before,(self.p._document(),self.p.undo_stack,self.p.redo_stack));self.apply(VALUES)
        self.p.overrides[OWNER][COMPONENT]['source_record_sha256']='f'*64
        with self.assertRaises(ProjectError):snapshot(self.p,OWNER)
        with self.assertRaises(ProjectError):ProjectService.open(self.p.save())
        self.p.overrides[OWNER][COMPONENT]['source_record_sha256']=self.p.overrides[OWNER]['ControllerSystemFlags']['source_record_sha256'];self.p.mode='live'
        with self.assertRaises(ProjectError):review(self.p,OWNER,ID,None)
        self.p.mode='edit';self.p.overrides[OWNER]['Transform']={'position':{'x':1}}
        with self.assertRaises(ProjectError):ProjectService.open(self.p.save())

    def test_build_collection_retains_global_byte_components(self):
        from sdk.controller_selector_build import collect
        self.apply(VALUES)
        scene,components=collect(self.p,OWNER,self.p.overrides[OWNER])
        self.assertEqual(scene,'scene://fixture')
        self.assertEqual(components[COMPONENT]['entries'][ID],VALUES)

    def test_ten_families_compose_complete_MAN_and_reset_independently(self):
        families=[
            ('sdk.controller_tile_rects','tile-rect/0007','set_controller_tile_rect',dict(column_start=1,row_start=2,column_end=3,row_end=4,value=255),66,bytes([1,2,3,4,255])),
            ('sdk.controller_fades','fade/000e','set_controller_fade',dict(selector=1,signed_words=[1,2,3]),73,bytes.fromhex('01010002000300')),
            ('sdk.controller_tables','table-copy/0017','set_controller_table_copy',dict(signed_words=list(range(1,17))),82,b''.join(w.to_bytes(2,'little',signed=True) for w in range(1,17))),
            ('sdk.controller_word_triplets','word-triplet/0039','set_controller_word_triplet',dict(selector=255,signed_words=[-32768,32767,-1]),116,bytes.fromhex('ff0080ff7fffff')),
            ('sdk.controller_three_words','three-word/0042','set_controller_three_word',dict(signed_words=[-32768,32767,-1]),125,bytes.fromhex('0080ff7fffff')),
            ('sdk.controller_scene_bytes','scene-byte/0060','set_controller_scene_byte',dict(value=255),155,bytes([255])),
            ('sdk.controller_five_words','five-word/004a','set_controller_five_word',dict(signed_words=[1,2,3,4,5]),133,bytes.fromhex('01000200030004000500')),
        ]
        import importlib
        expected=bytearray(self.context._man)
        for module,suffix,command,value,at,raw in families:
            operand='script://fixture/controllers/man-p1/0000/'+suffix
            r=importlib.import_module(module).review(self.p,OWNER,operand,value)
            self.p.command(dict(type=command,entity_id=OWNER,operand_id=operand,value=value,review_key=r['review_key']))
            expected[at:at+len(raw)]=raw
        self.selector({'index':4095});self.branch({'target_pc':7});self.apply(VALUES)
        expected[62:64]=bytes.fromhex('6fff');expected[145:153]=bytes.fromhex('00ff1f400080ff7f');expected[157:159]=(-93).to_bytes(2,'little',signed=True)
        from sdk.controller_system_flags import prepare
        self.assertEqual(prepare(self.p,OWNER)[6],bytes(expected))
        saved=deepcopy(self.p.overrides);self.assertEqual(len(saved[OWNER]),10)
        self.apply(None);self.assertNotIn(COMPONENT,self.p.overrides[OWNER]);self.assertEqual({k:v for k,v in saved[OWNER].items() if k!=COMPONENT},self.p.overrides[OWNER])
        expected[145:153]=bytes(8);self.assertEqual(prepare(self.p,OWNER)[6],bytes(expected))
        self.p.undo();self.assertEqual(self.p.overrides,saved)
        self.assertEqual(ProjectService.open(self.p.save())._document(),self.p._document())
