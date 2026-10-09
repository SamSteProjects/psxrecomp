from copy import deepcopy
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import patch
import tempfile,unittest,json,subprocess
from sdk.project import ProjectService,ProjectError
from sdk.controller_flag_bits import snapshot,review,COMPONENT
from sdk.controller_system_flags import prepare,state_key
from sdk.controller_snapshots import snapshot as workspace
from importer.controller_system_flags import ControllerSystemFlagAuthoringContext
from test_controller_branches import source,OWNER
from test_project_workflow import synthetic_scene

ID='script://fixture/controllers/man-p1/0000/flag-bit/0005'
class ControllerFlagBitWorkflow(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.p=ProjectService(Path(self.temp.name));self.p.import_metadata(synthetic_scene())
        src,self.man=source(b'\x2e\xe2\x61\x23\x4c\x2a\x26\xf9\xff');self.context=ControllerSystemFlagAuthoringContext(src)
        for name,value in [('importer.pipeline._disc_context',nullcontext()),('sdk.resources._verify',None),('sdk.controller_system_flags.load_controller_system_flag_context',self.context)]:
            mock=patch(name,return_value=value);mock.start();self.addCleanup(mock.stop)
    def apply(self,value):
        r=review(self.p,OWNER,ID,value);self.p.command(dict(type='set_controller_flag_bit',entity_id=OWNER,operand_id=ID,value=value,review_key=r['review_key']));return r
    def test_review_history_save_reset_and_literal_composition(self):
        before=deepcopy((self.p._document(),self.p.imports,self.p.undo_stack));r=review(self.p,OWNER,ID,{'bit':31});self.assertEqual(before,(self.p._document(),self.p.imports,self.p.undo_stack));self.assertEqual(r['changed_decoded_byte_offsets'],[63])
        self.apply({'bit':31});literal=bytearray(self.man);literal[63]=0xff;self.assertEqual(prepare(self.p,OWNER)[6],bytes(literal));s=snapshot(self.p,OWNER);self.assertEqual(s['targets'][0]['current_values'],{'bit':31});self.assertEqual(s['targets'][0]['preserved_bits'],224)
        saved=deepcopy(self.p.overrides);self.p.undo();self.assertFalse(self.p.overrides);self.p.redo();self.assertEqual(saved,self.p.overrides);self.assertEqual(ProjectService.open(self.p.save())._document(),self.p._document());self.apply(None);self.assertFalse(self.p.overrides);self.p.undo();self.assertEqual(saved,self.p.overrides)
    def test_invalid_fields_stale_values_and_modes_are_atomic(self):
        stale=review(self.p,OWNER,ID,{'bit':3});self.apply({'bit':4});before=deepcopy((self.p._document(),self.p.undo_stack))
        with self.assertRaises(ProjectError):self.p.command(dict(type='set_controller_flag_bit',entity_id=OWNER,operand_id=ID,value={'bit':3},review_key=stale['review_key']))
        for value in [{'bit':True},{'bit':-1},{'bit':32},{'bit':'3'},{'bit':3,'extra':0},{}]:
            with self.assertRaises(ProjectError):review(self.p,OWNER,ID,value)
        for owner,operand in [(OWNER.replace('fixture','foreign'),ID),(OWNER,ID.replace('/0000/','/0001/'))]:
            with self.assertRaises(ProjectError):review(self.p,owner,operand,{'bit':3})
        self.assertEqual(before,(self.p._document(),self.p.undo_stack));self.p.mode='live'
        with self.assertRaises(ProjectError):review(self.p,OWNER,ID,{'bit':3})
    def test_shared_workspace_and_frontend_decoder(self):
        self.apply({'bit':31});batch=workspace(self.p,OWNER,state_key(self.p));self.assertEqual(len(batch['families']),12)
        path=Path(self.temp.name)/'flag.json';path.write_text(json.dumps(dict(raw=batch['families'][COMPONENT],owner=OWNER,context=dict(projectPath=str(self.p.root),sceneId=self.p.active_scene,mode='edit',scriptKey=state_key(self.p)))),encoding='utf-8')
        subprocess.run(['C:/Program Files/nodejs/node.exe',str(Path(__file__).with_suffix('.mjs')),str(path)],check=True)
    def test_build_refuses_pending_family_instead_of_omitting_bytes(self):
        from sdk.controller_selector_build import compose
        from sdk.build import BuildError
        self.apply({'bit':31})
        with self.assertRaisesRegex(BuildError,'no package can omit'):compose(self.p,self.p.active_scene,self.man,self.man)
