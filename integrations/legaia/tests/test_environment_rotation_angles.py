"""Custom source-angle placement rounding, compatibility and fail-closed authoring."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import math, struct, tempfile, unittest
from unittest.mock import patch

from importer.core import ImportError
from importer.environment_authoring import patch_environment_overrides
from sdk.project import ProjectService, ProjectError
from sdk.environment_rotation_group import review, apply
from sdk.environment_rotation_math import Q30, SINE_QUARTER_Q30, sin_cos_q30, round_q30, rotate_displacement
from test_environment_group import SCENE, IDS, source_map
from test_project_workflow import synthetic_scene


class EnvironmentRotationAngleTests(unittest.TestCase):
    def test_all_angles_independent_sine_and_coordinate_arithmetic(self):
        self.assertEqual(len(SINE_QUARTER_Q30),1025)
        away=lambda n: (abs(n)+Q30//2)//Q30*(1 if n>=0 else -1)
        for numerator,expected in [(Q30//2,1),(-Q30//2,-1),(Q30*3//2,2),(-Q30*3//2,-2),(Q30//2-1,0),(-Q30//2+1,0)]:
            self.assertEqual(round_q30(numerator),expected)
        for angle in range(4096):
            theta=angle*math.tau/4096
            sin=int(math.floor(math.sin(theta)*Q30+.5)) if math.sin(theta)>=0 else -int(math.floor(-math.sin(theta)*Q30+.5))
            cos=int(math.floor(math.cos(theta)*Q30+.5)) if math.cos(theta)>=0 else -int(math.floor(-math.cos(theta)*Q30+.5))
            self.assertEqual(sin_cos_q30(angle),(sin,cos))
            self.assertEqual(rotate_displacement(-137,281,angle),(away(-137*cos+281*sin),away(281*cos+137*sin)))
        for args in [(True,0,0),(0,False,0),(1,2,True),(1,2,4096)]:
            with self.assertRaises(ProjectError):rotate_displacement(*args)

    def test_all_angles_match_frontend_bigint_results(self):
        import json, shutil, subprocess
        node=shutil.which('node')
        if not node:self.skipTest('Node unavailable for frontend parity')
        script=Path(__file__).with_suffix('.mjs')
        results=json.loads(subprocess.check_output([node,str(script),'--parity-json'],text=True,timeout=15))
        self.assertEqual(results,[list(rotate_displacement(-137,281,a)) for a in range(4096)])

    def project(self, root):
        p=ProjectService(Path(root));p.import_metadata(synthetic_scene());return p

    def command(self,r):
        return dict(type='apply_environment_rotation_group',entity_id=SCENE,entity_ids=r['entity_ids'],operation=r['operation'],review_key=r['review_key'])

    def test_cardinal_angles_match_legacy_complete_proposals(self):
        with tempfile.TemporaryDirectory() as root:
            p=self.project(root)
            with patch.object(p,'_environment_source',return_value=source_map()):
                for q in range(4):
                    a=review(p,SCENE,IDS,dict(anchor_id=IDS[0],yaw_units=q*1024))
                    b=review(p,SCENE,IDS,dict(anchor_id=IDS[0],quarter_turns=q))
                    for key in ('targets','value','affected_count','project_change','source_sha256','scope'):
                        self.assertEqual(a[key],b[key])

    def test_45_degree_known_integer_positions_and_exact_bytes_history(self):
        with tempfile.TemporaryDirectory() as root:
            p=self.project(root);source=source_map();source_hash=sha256(source).hexdigest()
            with patch.object(ProjectService,'_environment_source',return_value=source):
                p.save();before=deepcopy(p.overrides)
                r=review(p,SCENE,IDS,dict(anchor_id=IDS[0],yaw_units=512))
                self.assertEqual([x['proposed'] for x in r['targets']],[dict(x=202,z=162,yaw=712),dict(x=383,z=162,yaw=712)])
                self.assertEqual(p.overrides,before);self.assertFalse(p.dirty)
                apply(p,self.command(r));self.assertEqual(len(p.undo_stack),1)
                candidate,_=patch_environment_overrides(source,p.overrides[SCENE]['Environment'])
                for cell,expected in [(129,(10,20,30)),(258,(63,20,158))]:
                    word=struct.unpack_from('<H',candidate,0x8000+cell*2)[0];offset=(word&511)*32
                    self.assertEqual(word&~511,0x2000)
                    self.assertEqual(struct.unpack_from('<3h',candidate,offset),expected)
                    self.assertEqual(struct.unpack_from('<3H',candidate,offset+8),(100,712,300))
                    self.assertEqual(candidate[offset+14:offset+32],source[142:160])
                after=deepcopy(p.overrides);p.undo();self.assertEqual(p.overrides,before);p.redo();self.assertEqual(p.overrides,after)
                self.assertEqual(ProjectService.open(p.save()).overrides,after)
                self.assertEqual(sha256(source).hexdigest(),source_hash)

    def test_custom_zero_is_metadata_noop_and_invalid_operations_reject(self):
        with tempfile.TemporaryDirectory() as root:
            p=self.project(root);source=source_map()
            with patch.object(p,'_environment_source',return_value=source):
                b=dict(source_sha256=sha256(source).hexdigest(),instances=[dict(cell_index=258,rotation_psx=dict(y=200)),dict(cell_index=129,offset=dict(x=10))])
                p.command(dict(type='set_environment_transforms',entity_id=SCENE,value=b));p.save();depth=len(p.undo_stack)
                r=review(p,SCENE,IDS,dict(anchor_id=IDS[0],yaw_units=0));self.assertEqual(r['value'],b);self.assertFalse(r['project_change'])
                apply(p,self.command(r));self.assertEqual(len(p.undo_stack),depth);self.assertFalse(p.dirty)
                for yaw in (True,False,0.0,512.5,-1,4096,None,'512'):
                    with self.assertRaises(ProjectError):review(p,SCENE,IDS,dict(anchor_id=IDS[0],yaw_units=yaw))
                for op in (dict(anchor_id=IDS[0],yaw_units=512,quarter_turns=1),dict(anchor_id=IDS[0],yaw_units=512,extra=True)):
                    with self.assertRaises(ProjectError):review(p,SCENE,IDS,op)

    def test_stale_capacity_and_signed_range_rejections_are_atomic(self):
        with tempfile.TemporaryDirectory() as root:
            p=self.project(root);source=source_map()
            with patch.object(p,'_environment_source',return_value=source):
                r=review(p,SCENE,IDS,dict(anchor_id=IDS[0],yaw_units=512));p.name='Drift'
                with self.assertRaises(ProjectError):apply(p,self.command(r))
            full=bytearray(source)
            for record in range(5,512):full[record*32+31]=1
            with patch.object(p,'_environment_source',return_value=bytes(full)):
                with self.assertRaises(ImportError):review(p,SCENE,IDS,dict(anchor_id=IDS[0],yaw_units=512))
            with patch.object(p,'_environment_source',return_value=source):
                p.command(dict(type='set_environment_transforms',entity_id=SCENE,value=dict(source_sha256=sha256(source).hexdigest(),instances=[dict(cell_index=258,offset=dict(x=32767,z=-32768))])))
                before=deepcopy(p.overrides);depth=len(p.undo_stack)
                with self.assertRaisesRegex(ProjectError,'signed'):review(p,SCENE,IDS,dict(anchor_id=IDS[0],yaw_units=512))
                self.assertEqual(p.overrides,before);self.assertEqual(len(p.undo_stack),depth)

    def test_custom_angle_http_review_apply_readonly_and_stale_guard(self):
        import json,threading
        from urllib.request import Request,urlopen
        from urllib.error import HTTPError
        from sdk.server import EditorServer
        with tempfile.TemporaryDirectory() as root:
            p=self.project(root);saved=p.save();bytes_before=saved.read_bytes();before=deepcopy(p._document())
            with patch.object(ProjectService,'_environment_source',return_value=source_map()):
                server=EditorServer(('127.0.0.1',0),p);thread=threading.Thread(target=server.serve_forever);thread.start()
                try:
                    def post(route,body):
                        request=Request(f'http://127.0.0.1:{server.server_port}{route}',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
                        try:
                            with urlopen(request,timeout=10) as r:return r.status,json.load(r)
                        except HTTPError as e:
                            with e:return e.code,json.load(e)
                    body=dict(entity_id=SCENE,entity_ids=IDS,operation=dict(anchor_id=IDS[0],yaw_units=512))
                    code,r=post('/api/environment-rotation-group-review',body);self.assertEqual(code,200,r)
                    self.assertEqual(p._document(),before);self.assertEqual(p.undo_stack,[]);self.assertEqual(saved.read_bytes(),bytes_before)
                    self.assertEqual(post('/api/command',self.command(r))[0],200);after=deepcopy(p._document())
                    self.assertEqual(post('/api/command',self.command(r))[0],400);self.assertEqual(p._document(),after)
                    self.assertEqual(saved.read_bytes(),bytes_before);self.assertEqual(len(p.undo_stack),1)
                finally:server.shutdown();server.server_close();thread.join(timeout=5)
                self.assertFalse(thread.is_alive())


if __name__=='__main__':unittest.main()
