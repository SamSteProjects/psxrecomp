"""Effective inherited endpoints stage exact complete native poses."""
from copy import deepcopy
import struct
from sdk.animation_record_interpolation import stage,interpolate_axis
from sdk.animation_record_edit import prepare
from sdk.animation_record_ledger import compose
from sdk.project import ProjectService
from importer.animation import animation_record_ranges
import test_animation_record_offset as workflow
from test_model_primitive_workflow import http_server

class EffectiveInterpolation(workflow.AnimationRecordOffset):
    def setUp(self):
        super().setUp();self.args.pop('delta');self.args.update(end=2,edits=[dict(frame_index=0,object_index=0,translation=dict(x=-17),rotation_psx=dict(y=4080))])
    def test_effective_draft_offset_native_roundtrip_apply_history_and_reopen(self):
        held=deepcopy((self.project._document(),self.project.undo_stack,self.project.redo_stack));original=self.native(self.args['edits']);report=stage(self.project,**self.args);candidate=self.native(report['edits']);objects=struct.unpack_from('<H',original)[0]&255;expected=bytearray(original)
        def channels(frame):
            data=original[8+frame*objects*8:16+frame*objects*8]
            signed=lambda v:v-4096 if v&2048 else v
            return [signed(data[0]|(data[2]&15)<<8),signed(data[1]|(data[2]>>4)<<8),signed(data[3]|(data[4]&15)<<8),*data[5:]]
        first,last=channels(0),channels(2)
        for frame in range(3):
            values=[]
            for axis in range(6):
                delta=last[axis]-first[axis]
                if axis>=3:
                    delta%=256
                    if delta>128:delta-=256
                values.append((2*(first[axis]*2+delta*frame)+2)//4)
            at=8+frame*objects*8;x,y,z=[v&4095 for v in values[:3]]
            expected[at:at+4]=bytes([x&255,y&255,(x>>8)|((y>>8)<<4),z&255]);expected[at+4]=(expected[at+4]&240)|(z>>8);expected[at+5:at+8]=bytes(v%256 for v in values[3:])
        self.assertEqual(candidate,bytes(expected));self.assertEqual((self.project._document(),self.project.undo_stack,self.project.redo_stack),held)
        request={k:report[k] for k in ['scene_id','record_id','source_frame_indices','edits']};request['expected_source_key']=self.args['expected_source_key'];_,review=prepare(self.project,**request)
        self.project.command(dict(type='edit_animation_record',**request,review_key=review['review_key']));bank,_=compose(self.project,self.project.active_scene);a,b=animation_record_ranges(bank)[-1];self.assertEqual(bank[a:b],candidate);self.project.save();self.assertEqual(compose(ProjectService.open(self.project.root),self.project.active_scene)[0],bank);self.project.undo();self.assertEqual((self.project._document(),self.project.undo_stack),held[:2]);self.project.redo();self.assertEqual(compose(self.project,self.project.active_scene)[0],bank)
    def test_exact_http_bounds_overflow_stale_and_zero_offset(self):
        held=deepcopy((self.project._document(),self.project.undo_stack,self.project.redo_stack))
        with http_server(self.project) as (_,post):
            status,report=post('/api/animation-record-interpolation',self.args);self.assertEqual(status,200,report);self.assertEqual(len(report['poses']),3)
            for change in [{'extra':1},{'object_index':True},{'start':-1},{'end':3},{'end':0},{'start':2},{'expected_source_key':'0'*64}]:self.assertEqual(post('/api/animation-record-interpolation',{**self.args,**change})[0],400,change)
        self.assertEqual((self.project._document(),self.project.undo_stack,self.project.redo_stack),held)
        self.assertEqual(interpolate_axis('translation',-1,0,1,2),0);self.assertEqual(interpolate_axis('rotation_psx',4080,16,1,2),0);self.assertEqual(interpolate_axis('rotation_psx',0,2048,1,2),1024)
