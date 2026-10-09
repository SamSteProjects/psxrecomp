"""Controller scenario sources must belong to fresh, independently reviewed bytes."""
from contextlib import nullcontext
from copy import deepcopy
from importlib import import_module
from pathlib import Path
import json, subprocess, tempfile, unittest, threading
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from unittest.mock import patch
from importer.controller_system_flags import ControllerSystemFlagAuthoringContext
from sdk.controller_flow_source import qualify, report_hash
from sdk.controller_snapshots import FAMILIES
from sdk.controller_system_flags import state_key
from sdk.project import ProjectService, ProjectError, digest
from test_controller_branches import source, OWNER
from test_project_workflow import synthetic_scene

FIELDS = {
    'ControllerSystemFlags': ('system-flag/0005', {'index':4095}),
    'ControllerBranches': ('branch/0067', {'target_pc':7}),
    'ControllerTileRects': ('tile-rect/0007', dict(column_start=1,row_start=2,column_end=3,row_end=4,value=255)),
    'ControllerFades': ('fade/000e', dict(selector=1,signed_words=[1,2,3])),
    'ControllerTableCopies': ('table-copy/0017', dict(signed_words=list(range(1,17)))),
    'ControllerWordTriplets': ('word-triplet/0039', dict(selector=255,signed_words=[-32768,32767,-1])),
    'ControllerThreeWords': ('three-word/0042', dict(signed_words=[-32768,32767,-1])),
    'ControllerFiveWords': ('five-word/004a', dict(signed_words=[-32768,32767,-1,0,1])),
    'ControllerGlobalBytes': ('global-byte/0056', dict(byte_values=[0,255,31,64],parameters_i16=[-32768,32767])),
    'ControllerSceneBytes': ('scene-byte/0060', {'value':255}),
    'ControllerPartySelectors': ('party-selector/0063', {'party_selector':7}),
    'ControllerFlagBits': ('flag-bit/0065', {'bit':31}),
}

class ControllerFlowSource(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.p=ProjectService(Path(self.temp.name));self.p.import_metadata(synthetic_scene())
        src,_=source(b'\x61\x23\x4c\x83\x01\x02\x03\x04\x05\x4c\x90\x00'+bytes(6)+b'\x4c\x9e'+bytes(32)+b'\x4c\xd8\x00'+bytes(6)+b'\x4c\xe6'+bytes(6)+b'\x43\x11'+bytes(10)+b'\x43\x03'+bytes(8)+b'\x4c\xdf\x01\x4c\x2a\x2e\xe2\x26\x9d\xff')
        self.context=ControllerSystemFlagAuthoringContext(src)
        for name,value in [('importer.pipeline._disc_context',nullcontext()),('sdk.resources._verify',None),('sdk.controller_system_flags.load_controller_system_flag_context',self.context)]:
            mock=patch(name,return_value=value);mock.start();self.addCleanup(mock.stop)

    def binding(self,component,value='fixture'):
        suffix,fields=FIELDS[component]
        return OWNER.replace('scene://','script://',1)+'/'+suffix, deepcopy(fields) if value=='fixture' else value

    def state(self):
        return deepcopy((self.p._document(),self.p.imports,self.p.undo_stack,self.p.redo_stack))

    def test_all_twelve_current_proposed_reset_sources_and_js_hashes(self):
        before=self.state();hashes=[]
        self.assertEqual(set(FIELDS),dict(FAMILIES).keys())
        for component,name in FAMILIES:
            with self.subTest(component=component):
                module=import_module('sdk.'+name);current=module.snapshot(self.p,OWNER)
                result=qualify(self.p,OWNER,component,'current',state_key(self.p))
                self.assertEqual(result['report'],current['current_report'])
                self.assertEqual(result['effective_record_sha256'],current['current_record_sha256'])
                self.assertIsNone(result['operand_id']);self.assertIsNone(result['value'])
                operand,value=self.binding(component)
                for proposal in (value,None):
                    review=module.review(self.p,OWNER,operand,proposal)
                    proof=qualify(self.p,OWNER,component,'proposed',state_key(self.p),operand_id=operand,value=proposal,review_key=review['review_key'])
                    self.assertEqual(proof['report'],review['proposed_report'])
                    self.assertEqual(proof['effective_record_sha256'],review['proposed_record_sha256'])
                    self.assertEqual(proof['source_key'],digest({k:v for k,v in proof.items() if k not in ('source_key','report')}))
                    self.assertFalse(proof['project_changed']);self.assertFalse(proof['gameplay_verified'])
                    self.assertEqual(proof['runtime_execution'],'not_asserted')
                    hashes.append(dict(report=proof['report'],expected=proof['report_sha256'],raw=proof,snapshot=current,review=review,kind='proposed',context=dict(projectPath=str(self.p.root),sceneId=self.p.active_scene,mode='edit',scriptKey=state_key(self.p)),projectSourceKey='a'*64))
                hashes.append(dict(report=deepcopy(result['report']),expected=result['report_sha256'],raw=deepcopy(result),snapshot=current,kind='current',context=dict(projectPath=str(self.p.root),sceneId=self.p.active_scene,mode='edit',scriptKey=state_key(self.p)),projectSourceKey='a'*64))
                result['report'].clear()
                self.assertEqual(module.snapshot(self.p,OWNER)['current_report'],current['current_report'])
        self.assertEqual(before,self.state())
        path=Path(self.temp.name)/'hashes.json';path.write_text(json.dumps(hashes,ensure_ascii=False),encoding='utf-8')
        subprocess.run(['C:/Program Files/nodejs/node.exe',str(Path(__file__).with_suffix('.mjs')),str(path)],check=True)

    def test_foreign_stale_unreviewed_and_current_proposal_refuse(self):
        component='ControllerFlagBits';operand,value=self.binding(component)
        from sdk.controller_flag_bits import review
        r=review(self.p,OWNER,operand,value);key=state_key(self.p);before=self.state()
        for owner,family,layer,source_key,kwargs in [
            (OWNER,'ControllerUnknown','current',key,{}),
            (OWNER,component,'retail',key,{}),
            (OWNER.replace('fixture','foreign'),component,'current',key,{}),
            (OWNER,component,'current','f'*64,{}),
            (OWNER,component,'current',key,dict(operand_id=operand,value=value,review_key=r['review_key'])),
            (OWNER,component,'proposed',key,dict(operand_id=operand,value=value,review_key='f'*64)),
            (OWNER,component,'proposed',key,dict(operand_id=operand,value={'bit':30},review_key=r['review_key'])),
            (OWNER,component,'proposed',key,dict(operand_id=operand.replace('fixture','foreign'),value=value,review_key=r['review_key'])),
            (OWNER,component,'proposed',key,dict(operand_id=operand,value=value,review_key=None)),
        ]:
            with self.subTest(owner=owner,family=family,layer=layer,kwargs=kwargs),self.assertRaises(ProjectError):
                qualify(self.p,owner,family,layer,source_key,**kwargs)
        self.assertEqual(before,self.state())
        self.p.mode='live'
        with self.assertRaises(ProjectError):qualify(self.p,OWNER,component,'current',state_key(self.p))

    def test_source_changes_during_read_refuse(self):
        from sdk import controller_flag_bits
        original=controller_flag_bits.snapshot
        def changing(*args):
            result=original(*args);self.p.mode='live';return result
        with patch.object(controller_flag_bits,'snapshot',side_effect=changing),self.assertRaises(ProjectError):
            qualify(self.p,OWNER,'ControllerFlagBits','current',state_key(self.p))

    def test_saved_authored_current_and_reviewed_reset_remain_separate(self):
        from sdk.controller_flag_bits import review
        operand,value=self.binding('ControllerFlagBits');key=state_key(self.p)
        original=qualify(self.p,OWNER,'ControllerFlagBits','current',key)
        r=review(self.p,OWNER,operand,value)
        self.p.command(dict(type='set_controller_flag_bit',entity_id=OWNER,operand_id=operand,value=value,review_key=r['review_key']))
        before=self.state();current=qualify(self.p,OWNER,'ControllerFlagBits','current',state_key(self.p))
        reset=review(self.p,OWNER,operand,None)
        proposed=qualify(self.p,OWNER,'ControllerFlagBits','proposed',state_key(self.p),operand_id=operand,value=None,review_key=reset['review_key'])
        self.assertNotEqual(current['effective_record_sha256'],original['effective_record_sha256'])
        self.assertEqual(proposed['effective_record_sha256'],original['effective_record_sha256'])
        self.assertEqual(before,self.state())
        with self.assertRaises(ProjectError):qualify(self.p,OWNER,'ControllerFlagBits','current',key)
        opened=ProjectService.open(self.p.save())
        self.assertEqual(qualify(opened,OWNER,'ControllerFlagBits','current',state_key(opened)),current)

    def test_http_exact_current_and_proposed_fields(self):
        from sdk.server import EditorServer,EditorHandler
        from sdk.controller_flag_bits import review
        class Quiet(EditorHandler):
            def log_message(self,*args):pass
        server=EditorServer(('127.0.0.1',0),self.p,runtime_port=65533)
        server.RequestHandlerClass=Quiet
        worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
        def post(body):
            request=Request(f'http://127.0.0.1:{server.server_port}/api/controller-flow-source',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
            try:
                with urlopen(request,timeout=10) as response:return response.status,json.load(response)
            except HTTPError as error:
                with error:return error.code,json.load(error)
        try:
            with urlopen(f'http://127.0.0.1:{server.server_port}/controller-flow-source.js',timeout=10) as response:
                self.assertEqual(response.status,200);self.assertIn(b'export function controllerScenarioBindings',response.read())
            before=self.state();body=dict(entity=OWNER,component='ControllerFlagBits',layer='current',expected_source_key=state_key(self.p))
            status,result=post(body);self.assertEqual(status,200)
            self.assertEqual(result,qualify(self.p,OWNER,'ControllerFlagBits','current',state_key(self.p)))
            operand,value=self.binding('ControllerFlagBits');r=review(self.p,OWNER,operand,value)
            proposed=dict(body,layer='proposed',operand_id=operand,value=value,review_key=r['review_key'])
            status,result=post(proposed);self.assertEqual(status,200);self.assertEqual(result['report'],r['proposed_report'])
            for invalid in [dict(body,value=None),dict(body,extra=1),{k:v for k,v in body.items() if k!='component'},dict(proposed,review_key='f'*64),{k:v for k,v in proposed.items() if k!='value'},dict(body,component=['ControllerFlagBits'])]:
                with self.subTest(invalid=invalid):self.assertEqual(post(invalid)[0],400)
            self.assertEqual(before,self.state())
        finally:
            server.shutdown();server.server_close();worker.join(10)
