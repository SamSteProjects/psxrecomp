from copy import deepcopy
from contextlib import nullcontext
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.controller_word_triplets import snapshot,review,COMPONENT
from sdk.controller_system_flags import review as selector_review,snapshot as selector_snapshot
from sdk.controller_branches import review as branch_review,snapshot as branch_snapshot
from importer.controller_system_flags import ControllerSystemFlagAuthoringContext
from test_controller_branches import source,OWNER
from test_project_workflow import synthetic_scene

ID='script://fixture/controllers/man-p1/0000/word-triplet/0039'
VALUES=dict(selector=255,signed_words=[-32768,32767,-1])


class ControllerWordTripletWorkflow(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.p=ProjectService(Path(self.temp.name));self.p.import_metadata(synthetic_scene())
        src,_=source(b'\x61\x23\x4c\x83\x01\x02\x03\x04\x05\x4c\x90\x00'+bytes(6)+b'\x4c\x9e'+bytes(32)+b'\x4c\xd8\x00'+bytes(6)+b'\x26\xc2\xff')
        self.context=ControllerSystemFlagAuthoringContext(src)
        for name,value in [('importer.pipeline._disc_context',nullcontext()),('sdk.resources._verify',None),('sdk.controller_system_flags.load_controller_system_flag_context',self.context)]:
            mock=patch(name,return_value=value);mock.start();self.addCleanup(mock.stop)

    def apply(self,value):
        r=review(self.p,OWNER,ID,value);self.p.command(dict(type='set_controller_word_triplet',entity_id=OWNER,operand_id=ID,value=value,review_key=r['review_key']));return r

    def selector(self,value):
        operand='script://fixture/controllers/man-p1/0000/system-flag/0005';r=selector_review(self.p,OWNER,operand,value)
        self.p.command(dict(type='set_controller_system_flag_selector',entity_id=OWNER,operand_id=operand,value=value,review_key=r['review_key']))

    def branch(self,value):
        operand='script://fixture/controllers/man-p1/0000/branch/0042';r=branch_review(self.p,OWNER,operand,value)
        self.p.command(dict(type='set_controller_branch',entity_id=OWNER,operand_id=operand,value=value,review_key=r['review_key']))

    def test_review_history_save_open_reset_and_authored_asset(self):
        before=deepcopy((self.p._document(),self.p.undo_stack,self.p.redo_stack));r=review(self.p,OWNER,ID,VALUES)
        self.assertEqual(before,(self.p._document(),self.p.undo_stack,self.p.redo_stack));self.assertEqual(r['changed_decoded_byte_offsets'],[116,118,119,120,121,122]);self.assertFalse(r['project_changed']);self.assertFalse(r['gameplay_verified'])
        self.apply(VALUES);saved=deepcopy(self.p.overrides);t=snapshot(self.p,OWNER)['targets'][0]
        self.assertEqual(t['values'],dict(selector=0,signed_words=[0]*3));self.assertEqual(t['current_values'],VALUES);self.assertEqual(t['authored_values'],VALUES)
        self.assertIn(COMPONENT,self.p.authored_assets()[0]['authored']);self.p.undo();self.assertFalse(self.p.overrides);self.p.redo();self.assertEqual(self.p.overrides,saved)
        opened=ProjectService.open(self.p.save());self.assertEqual(opened._document(),self.p._document());self.assertEqual(opened.imports,self.p.imports)
        self.apply(None);self.assertFalse(self.p.overrides);self.p.undo();self.assertEqual(self.p.overrides,saved)
        self.apply(t['values']);self.assertFalse(self.p.overrides)

    def test_six_controller_families_compose_and_reset_independently(self):
        from sdk.controller_tile_rects import review as tile_review
        tile_id='script://fixture/controllers/man-p1/0000/tile-rect/0007'
        tile_values=dict(column_start=1,row_start=2,column_end=3,row_end=4,value=255)
        r=tile_review(self.p,OWNER,tile_id,tile_values)
        self.p.command(dict(type='set_controller_tile_rect',entity_id=OWNER,operand_id=tile_id,value=tile_values,review_key=r['review_key']))
        from sdk.controller_fades import review as fade_review
        fade_id='script://fixture/controllers/man-p1/0000/fade/000e';fade_values=dict(selector=1,signed_words=[1,2,3]);r=fade_review(self.p,OWNER,fade_id,fade_values)
        self.p.command(dict(type='set_controller_fade',entity_id=OWNER,operand_id=fade_id,value=fade_values,review_key=r['review_key']))
        from sdk.controller_tables import review as table_review
        table_id='script://fixture/controllers/man-p1/0000/table-copy/0017';table_values=dict(signed_words=list(range(1,17)))
        r=table_review(self.p,OWNER,table_id,table_values)
        self.p.command(dict(type='set_controller_table_copy',entity_id=OWNER,operand_id=table_id,value=table_values,review_key=r['review_key']))
        self.selector({'index':4095});self.branch({'target_pc':7});self.apply(VALUES)
        from sdk.controller_system_flags import prepare
        import struct
        expected=bytearray(self.context._man)
        expected[62:64]=b'\x6f\xff'
        expected[66:71]=bytes([1,2,3,4,255])
        expected[73:80]=b'\x01'+struct.pack('<hhh',1,2,3)
        expected[82:114]=b''.join(word.to_bytes(2,'little',signed=True) for word in range(1,17))
        expected[116:123]=b'\xff'+struct.pack('<hhh',-32768,32767,-1)
        expected[124:126]=(-60).to_bytes(2,'little',signed=True)
        self.assertEqual(prepare(self.p,OWNER)[6],bytes(expected))
        saved=deepcopy(self.p.overrides);self.assertEqual(set(saved[OWNER]),{'ControllerSystemFlags','ControllerBranches','ControllerTileRects','ControllerFades','ControllerTableCopies',COMPONENT})
        self.assertEqual(selector_snapshot(self.p,OWNER)['targets'][0]['current_index'],4095)
        self.assertEqual(branch_snapshot(self.p,OWNER)['targets'][0]['current_target_pc'],7)
        self.selector({'index':4094});self.branch({'target_pc':57});self.assertEqual(self.p.overrides[OWNER][COMPONENT],saved[OWNER][COMPONENT])
        self.apply(None);self.assertNotIn(COMPONENT,self.p.overrides[OWNER]);self.p.undo();self.selector(None);self.assertIn(COMPONENT,self.p.overrides[OWNER]);self.branch(None);self.assertEqual(set(self.p.overrides[OWNER]),{'ControllerTileRects','ControllerFades','ControllerTableCopies',COMPONENT})
        self.assertEqual(snapshot(self.p,OWNER)['targets'][0]['current_values'],VALUES)
        self.assertEqual(ProjectService.open(self.p.save())._document(),self.p._document())

    def test_stale_review_bad_values_owner_hash_modes_and_mixed_components_refuse(self):
        stale=review(self.p,OWNER,ID,VALUES);self.selector({'index':4095});before=deepcopy((self.p._document(),self.p.undo_stack,self.p.redo_stack))
        with self.assertRaises(ProjectError):self.p.command(dict(type='set_controller_word_triplet',entity_id=OWNER,operand_id=ID,value=VALUES,review_key=stale['review_key']))
        for value in [dict(VALUES,selector=True),dict(VALUES,signed_words=[32768,0,0]),dict(VALUES,signed_words=[True,0,0]),dict(VALUES,selector=-1),dict(VALUES,selector=256),dict(VALUES,signed_words=[0,0]),{},dict(VALUES,capacity=256)]:
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

    def test_build_collection_retains_validated_triplet_components(self):
        from sdk.controller_selector_build import collect
        self.apply(VALUES)
        scene,components=collect(self.p,OWNER,self.p.overrides[OWNER])
        self.assertEqual(scene,'scene://fixture')
        self.assertEqual(components[COMPONENT]['entries'][ID],VALUES)
