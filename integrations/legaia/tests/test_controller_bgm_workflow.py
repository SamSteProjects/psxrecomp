from copy import deepcopy
from contextlib import nullcontext
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.controller_bgm import snapshot,review,COMPONENT
from sdk.controller_system_flags import review as selector_review,snapshot as selector_snapshot
from sdk.controller_branches import review as branch_review,snapshot as branch_snapshot
from importer.controller_system_flags import ControllerSystemFlagAuthoringContext
from test_controller_branches import source,OWNER
from test_project_workflow import synthetic_scene

ID='script://fixture/controllers/man-p1/0000/bgm/004a'
VALUES=dict(encoded_id=65535)


class ControllerBgmWorkflow(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.p=ProjectService(Path(self.temp.name));self.p.import_metadata(synthetic_scene())
        src,_=source(b'\x61\x23\x4c\x83\x01\x02\x03\x04\x05\x4c\x90\x00'+bytes(6)+b'\x4c\x9e'+bytes(32)+b'\x4c\xd8\x00'+bytes(6)+b'\x4c\xe6'+bytes(6)+b'\x35\x34\x12\x80\x26\xb6\xff')
        self.context=ControllerSystemFlagAuthoringContext(src)
        for name,value in [('importer.pipeline._disc_context',nullcontext()),('sdk.resources._verify',None),('sdk.controller_system_flags.load_controller_system_flag_context',self.context)]:
            mock=patch(name,return_value=value);mock.start();self.addCleanup(mock.stop)

    def apply(self,value):
        r=review(self.p,OWNER,ID,value);self.p.command(dict(type='set_controller_bgm',entity_id=OWNER,operand_id=ID,value=value,review_key=r['review_key']));return r

    def selector(self,value):
        operand='script://fixture/controllers/man-p1/0000/system-flag/0005';r=selector_review(self.p,OWNER,operand,value)
        self.p.command(dict(type='set_controller_system_flag_selector',entity_id=OWNER,operand_id=operand,value=value,review_key=r['review_key']))

    def branch(self,value):
        operand='script://fixture/controllers/man-p1/0000/branch/004e';r=branch_review(self.p,OWNER,operand,value)
        self.p.command(dict(type='set_controller_branch',entity_id=OWNER,operand_id=operand,value=value,review_key=r['review_key']))

    def test_review_history_save_open_reset_and_authored_asset(self):
        before=deepcopy((self.p._document(),self.p.undo_stack,self.p.redo_stack));r=review(self.p,OWNER,ID,VALUES)
        self.assertEqual(before,(self.p._document(),self.p.undo_stack,self.p.redo_stack));self.assertEqual(r['changed_decoded_byte_offsets'],[132,133]);self.assertFalse(r['project_changed']);self.assertFalse(r['gameplay_verified'])
        self.apply(VALUES);saved=deepcopy(self.p.overrides);t=snapshot(self.p,OWNER)['targets'][0]
        self.assertEqual(t['values'],dict(encoded_id=4660));self.assertEqual(t['current_values'],VALUES);self.assertEqual(t['authored_values'],VALUES)
        self.assertIn(COMPONENT,self.p.authored_assets()[0]['authored']);self.p.undo();self.assertFalse(self.p.overrides);self.p.redo();self.assertEqual(self.p.overrides,saved)
        opened=ProjectService.open(self.p.save());self.assertEqual(opened._document(),self.p._document());self.assertEqual(opened.imports,self.p.imports)
        self.apply(None);self.assertFalse(self.p.overrides);self.p.undo();self.assertEqual(self.p.overrides,saved)
        self.apply(t['values']);self.assertFalse(self.p.overrides)

    def test_stale_review_bad_values_owner_hash_modes_and_mixed_components_refuse(self):
        stale=review(self.p,OWNER,ID,VALUES);self.selector({'index':4095});before=deepcopy((self.p._document(),self.p.undo_stack,self.p.redo_stack))
        with self.assertRaises(ProjectError):self.p.command(dict(type='set_controller_bgm',entity_id=OWNER,operand_id=ID,value=VALUES,review_key=stale['review_key']))
        for value in [dict(encoded_id=True),dict(encoded_id=-1),dict(encoded_id=65536),dict(encoded_id='1'),dict(encoded_id=1,extra=0),{}]:
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

    def test_build_collection_retains_bgm_components(self):
        from sdk.controller_selector_build import collect
        self.apply(VALUES)
        scene,components=collect(self.p,OWNER,self.p.overrides[OWNER])
        self.assertEqual(scene,'scene://fixture')
        self.assertEqual(components[COMPONENT]['entries'][ID],VALUES)

    def test_mixed_current_build_and_component_reset_preserve_other_edits(self):
        from sdk.controller_system_flags import prepare
        from sdk.controller_selector_build import compose
        from sdk.controller_component_reset import review as reset_review,apply as reset_apply
        self.selector({'index':4095});self.branch({'target_pc':7});self.apply(VALUES)
        expected=bytearray(self.context._man);expected[62:64]=bytes.fromhex('6fff');expected[132:134]=bytes([255,255]);expected[136:138]=(-72).to_bytes(2,'little',signed=True)
        self.assertEqual(prepare(self.p,OWNER)[6],bytes(expected))
        with patch('sdk.controller_selector_build.load_controller_system_flag_context',return_value=self.context):
            result,audit=compose(self.p,'scene://fixture',self.context._man,self.context._man)
        self.assertEqual(result,bytes(expected));self.assertEqual(len(audit),3)
        candidate=bytearray(self.context._man[:57]+bytes(4)+self.context._man[57:]);candidate[40:43]=(int.from_bytes(self.context._man[40:43],'little')+4).to_bytes(3,'little');candidate[46:49]=(12).to_bytes(3,'little')
        with patch('sdk.controller_selector_build.load_controller_system_flag_context',return_value=self.context):
            relocated,receipts=compose(self.p,'scene://fixture',self.context._man,bytes(candidate),appended=True)
        literal=bytearray(candidate);literal[66:68]=bytes.fromhex('6fff');literal[136:138]=bytes([255,255]);literal[140:142]=(-72).to_bytes(2,'little',signed=True)
        self.assertEqual(relocated,bytes(literal));bgm=next(row for row in receipts if row.get('bgm_id')==ID)
        self.assertEqual(bgm['source_decoded_byte_offset'],132);self.assertEqual(bgm['decoded_byte_offset'],136)
        saved=deepcopy(self.p.overrides);self.apply(None)
        expected[132:134]=bytes.fromhex('3412');self.assertEqual(prepare(self.p,OWNER)[6],bytes(expected))
        self.assertEqual(self.p.overrides[OWNER],{k:v for k,v in saved[OWNER].items() if k!=COMPONENT})
        self.p.undo();self.assertEqual(self.p.overrides,saved)

    def test_bgm_file_transfer_and_component_reset_are_atomic(self):
        import json
        from sdk.controller_operand_files import export_file,review as file_review
        from sdk.controller_component_reset import review as reset_review
        file=export_file(self.p,OWNER);file['components']={COMPONENT:{'entries':{ID:VALUES}}};content=json.dumps(file)
        before=deepcopy(self.p._document());r=file_review(self.p,OWNER,content);self.assertEqual(self.p._document(),before)
        self.p.command(dict(type='import_controller_operand_file',entity_id=OWNER,content=content,review_key=r['review_key']))
        self.assertEqual(export_file(self.p,OWNER),file);self.assertEqual(len(self.p.undo_stack),1)
        self.selector({'index':4095});saved=deepcopy(self.p.overrides);r=reset_review(self.p,OWNER,COMPONENT)
        self.assertEqual(r['removed_operand_ids'],[ID]);self.assertEqual(self.p.overrides,saved)
        self.p.command(dict(type='reset_controller_component',entity_id=OWNER,component=COMPONENT,review_key=r['review_key']))
        self.assertEqual(self.p.overrides[OWNER],{k:v for k,v in saved[OWNER].items() if k!=COMPONENT})
        self.p.undo();self.assertEqual(self.p.overrides,saved)
