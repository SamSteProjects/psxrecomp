import assert from 'node:assert/strict';
import {validatePoseBlend,validatePoseBlendReview} from '../editor/animation-glb-blend.js';
const value={translation_weight:.25,rotation_weight:.5};assert.deepEqual(validatePoseBlend(value),value);
for(const bad of [null,{}, {...value,extra:true},{...value,rotation_weight:true},{...value,translation_weight:'0.25'},{...value,translation_weight:-.1},{...value,rotation_weight:1.1},{...value,rotation_weight:NaN}])assert.throws(()=>validatePoseBlend(bad));
validatePoseBlendReview({external_pose_blend:value},{external_pose_blend:value});validatePoseBlendReview({},{});
for(const bad of [{},{external_pose_blend:null},{external_pose_blend:{...value,rotation_weight:0}},{external_pose_blend:{...value,translation_weight:1}}])assert.throws(()=>validatePoseBlendReview(bad,{external_pose_blend:value}));
assert.throws(()=>validatePoseBlendReview({external_pose_blend:value},{}));const copy=validatePoseBlend(value);copy.translation_weight=0;assert.equal(value.translation_weight,.25);
console.log('Native/external pose influence decoders passed');
