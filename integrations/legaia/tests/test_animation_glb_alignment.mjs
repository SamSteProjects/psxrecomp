import assert from 'node:assert/strict';
import {validatePoseAlignment,validatePoseAlignmentReview} from '../editor/animation-glb-alignment.js';
const value={mode:'native_reference_local',source_frame_index:1,reference_seconds:.25};
assert.deepEqual(validatePoseAlignment(value,2),value);
for(const bad of [null,{}, {...value,extra:true},{...value,mode:'guess'},{...value,source_frame_index:true},{...value,source_frame_index:2},{...value,reference_seconds:Infinity},{...value,reference_seconds:-1}])assert.throws(()=>validatePoseAlignment(bad,2));
const binding={external_pose_alignment:value,external_object_nodes:[0]};validatePoseAlignmentReview({external_pose_alignment:value},binding,2);validatePoseAlignmentReview({}, {},2);
for(const analysis of [{},{external_pose_alignment:null},{external_pose_alignment:{...value,source_frame_index:0}},{external_pose_alignment:{...value,reference_seconds:0}}])assert.throws(()=>validatePoseAlignmentReview(analysis,binding,2));
assert.throws(()=>validatePoseAlignmentReview({external_pose_alignment:value},{},2));assert.throws(()=>validatePoseAlignmentReview({external_pose_alignment:value},{external_pose_alignment:value},2));
console.log('Reference pose alignment decoders passed');
