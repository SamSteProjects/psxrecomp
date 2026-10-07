"""Copy complete effective poses without moving opaque native channel bits."""
from copy import deepcopy
import struct
from sdk.animation_record_pose_copy import stage
from sdk.animation_record_edit import prepare
from sdk.animation_record_ledger import compose
from sdk.project import ProjectService
from importer.animation import animation_record_ranges
import test_animation_record_offset as workflow
from test_model_primitive_workflow import http_server


class EffectivePoseCopy(workflow.AnimationRecordOffset):
    def setUp(self):
        super().setUp();self.args.pop('delta');self.args.update(source_frame_index=1,end=2,edits=[dict(frame_index=0,object_index=0,translation=dict(x=-17)),dict(frame_index=1,object_index=0,rotation_psx=dict(y=4080)),dict(frame_index=2,object_index=1,translation=dict(z=37))])

    def test_effective_draft_offset_native_roundtrip_apply_history_and_reopen(self):
        held=deepcopy((self.project._document(),self.project.undo_stack,self.project.redo_stack));original=self.native(self.args['edits']);report=stage(self.project,**self.args);candidate=self.native(report['edits']);objects=struct.unpack_from('<H',original)[0]&255;expected=bytearray(original)
        source=original[8+objects*8:16+objects*8]
        for frame in range(3):
            at=8+frame*objects*8;expected[at:at+4]=source[:4];expected[at+4]=(expected[at+4]&240)|(source[4]&15);expected[at+5:at+8]=source[5:8]
        self.assertEqual(candidate,bytes(expected));self.assertEqual((self.project._document(),self.project.undo_stack,self.project.redo_stack),held)
        self.assertEqual(report['source_pose']['rotation_psx']['y'],4080)
        self.assertTrue(all(p['after']==report['source_pose'] for p in report['poses']))
        request={k:report[k] for k in ['scene_id','record_id','source_frame_indices','edits']};request['expected_source_key']=self.args['expected_source_key'];_,review=prepare(self.project,**request)
        self.project.command(dict(type='edit_animation_record',**request,review_key=review['review_key']));bank,_=compose(self.project,self.project.active_scene);a,b=animation_record_ranges(bank)[-1];self.assertEqual(bank[a:b],candidate)
        self.assertEqual(len(self.project.undo_stack),len(held[1])+1);self.project.save();self.assertEqual(compose(ProjectService.open(self.project.root),self.project.active_scene)[0],bank)
        self.project.undo();self.assertEqual((self.project._document(),self.project.undo_stack),held[:2]);self.project.redo();self.assertEqual(compose(self.project,self.project.active_scene)[0],bank)

    def test_exact_http_bounds_overflow_stale_and_zero_offset(self):
        held=deepcopy((self.project._document(),self.project.undo_stack,self.project.redo_stack))
        with http_server(self.project) as (_,post):
            status,report=post('/api/animation-record-pose-copy',self.args);self.assertEqual(status,200,report)
            for change in [{'extra':1},{'object_index':True},{'source_frame_index':True},{'source_frame_index':-1},{'source_frame_index':3},{'start':-1},{'end':3},{'start':2,'end':1},{'expected_source_key':'0'*64}]:self.assertEqual(post('/api/animation-record-pose-copy',{**self.args,**change})[0],400,change)
        single=stage(self.project,**{**self.args,'start':1,'end':1});self.assertEqual(self.native(single['edits']),self.native(self.args['edits']))
        partial=stage(self.project,**{**self.args,'start':0,'end':0});original=self.native(self.args['edits']);candidate=self.native(partial['edits']);objects=struct.unpack_from('<H',original)[0]&255
        self.assertEqual(candidate[16:8+objects*8],original[16:8+objects*8]);self.assertEqual(candidate[8+objects*8:],original[8+objects*8:])
        self.assertEqual((self.project._document(),self.project.undo_stack,self.project.redo_stack),held)
