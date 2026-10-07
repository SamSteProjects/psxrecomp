"""Wrapped native rotation staging, exact byte changes and retained history."""
from copy import deepcopy
import struct
from sdk.animation_record_offset import stage_rotation
from sdk.animation_record_edit import prepare
from sdk.animation_record_ledger import compose
from sdk.project import ProjectService
from importer.animation import animation_record_ranges
import test_animation_record_offset as offset_workflow
from test_model_primitive_workflow import http_server

class AnimationRecordRotationOffset(offset_workflow.AnimationRecordOffset):
    def setUp(self):
        super().setUp()
        self.args.update(edits=[dict(frame_index=0,object_index=0,translation=dict(x=17),rotation_psx=dict(x=4080,y=32))],delta=dict(x=32,y=-48,z=0))

    def test_effective_draft_offset_native_roundtrip_apply_history_and_reopen(self):
        held=deepcopy((self.project._document(),self.project.undo_stack,self.project.redo_stack))
        original=self.native(self.args['edits']);report=stage_rotation(self.project,**self.args)
        candidate=self.native(report['edits']);expected=bytearray(original);objects=struct.unpack_from('<H',original)[0]&255
        for frame in range(2):
            for axis,amount in [(0,2),(1,-3)]:
                at=8+frame*objects*8+5+axis;expected[at]=(expected[at]+amount)%256
        self.assertEqual(candidate,bytes(expected))
        self.assertEqual(report['changed_axes'][0],dict(frame_index=0,axis='x',before=4080,after=16))
        self.assertEqual(report['changed_axes'][1],dict(frame_index=0,axis='y',before=32,after=4080))
        self.assertEqual((self.project._document(),self.project.undo_stack,self.project.redo_stack),held)
        request={k:report[k] for k in ['scene_id','record_id','source_frame_indices','edits']};request['expected_source_key']=self.args['expected_source_key']
        _,review=prepare(self.project,**request);self.assertEqual(review['candidate_record_sha256'],report['after_record_sha256'])
        self.project.command(dict(type='edit_animation_record',**request,review_key=review['review_key']))
        bank,_=compose(self.project,self.project.active_scene);start,end=animation_record_ranges(bank)[-1];self.assertEqual(bank[start:end],candidate)
        self.project.save();opened=ProjectService.open(self.project.root);self.assertEqual(compose(opened,opened.active_scene)[0],bank)
        self.project.undo();self.assertEqual((self.project._document(),self.project.undo_stack),held[:2]);self.project.redo();self.assertEqual(compose(self.project,self.project.active_scene)[0],bank)

    def test_exact_http_bounds_overflow_stale_and_zero_offset(self):
        held=deepcopy((self.project._document(),self.project.undo_stack,self.project.redo_stack))
        with http_server(self.project) as (_,post):
            status,report=post('/api/animation-record-rotation-offset',self.args);self.assertEqual(status,200,report)
            for fields in [{'extra':True},{'object_index':True},{'start':-1},{'end':3},{'delta':{'x':4096}},{'delta':{'x':-4096}},{'delta':{'x':1}},{'delta':{'x':True}},{'delta':{'q':0}},{'delta':{}},{'expected_source_key':'0'*64}]:
                self.assertEqual(post('/api/animation-record-rotation-offset',{**self.args,**fields})[0],400,fields)
            status,zero=post('/api/animation-record-rotation-offset',{**self.args,'delta':dict(x=0,y=0,z=0)});self.assertEqual(status,200,zero);self.assertEqual(zero['edits'],self.args['edits']);self.assertEqual(zero['changed_axes'],[]);self.assertEqual(zero['before_record_sha256'],zero['after_record_sha256'])
        self.assertEqual((self.project._document(),self.project.undo_stack,self.project.redo_stack),held)
