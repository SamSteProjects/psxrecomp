import assert from 'node:assert/strict';
import {interpolateEffectiveAxis,decodeEffectiveInterpolation} from '../editor/animation-effective-interpolation.js';
import {interpolateRetainedFrameRange,validateRetainedAxes} from '../editor/animation-record-edit.js';
const expected={linear:[-12,-4,4,12,20],ease_in:[-12,-10,-4,6,20],ease_out:[-12,2,12,18,20],smoothstep:[-12,-7,4,15,20]};
for(const [curve,words] of Object.entries(expected)){
 assert.deepEqual(Array.from({length:5},(_,i)=>interpolateEffectiveAxis('translation',-12,20,i,4,curve)),words);
 const edits=[{frame_index:0,object_index:0,translation:{x:-12}},{frame_index:4,object_index:0,translation:{x:20}},{frame_index:2,object_index:1,rotation_psx:{z:32}}],held=structuredClone(edits),result=interpolateRetainedFrameRange({edits,frameCount:5,objectCount:2,objectIndex:0,start:0,end:4,curve});
 assert.deepEqual(result.edits.filter(r=>r.object_index===0).map(r=>r.translation.x),words);assert.deepEqual(result.edits.find(r=>r.object_index===1),held[2]);assert.deepEqual(edits,held);
}
assert.deepEqual(Array.from({length:5},(_,i)=>interpolateEffectiveAxis('rotation_psx',4080,48,i,4,'ease_in')),[4080,4080,0,16,48]);
assert.equal(interpolateEffectiveAxis('translation',-1,0,1,2,'smoothstep'),0);
for(const curve of [null,0,'unknown',{},[]])assert.throws(()=>interpolateEffectiveAxis('translation',0,1,1,2,curve));
console.log('Curve literal words, wrapped native rotations, negative half ties and immutable partial-axis drafts passed.');

const pose=x=>({translation:{x,y:0,z:0},rotation_psx:{x:0,y:0,z:0}});
for(const curve of ['ease_in','ease_out','smoothstep']){
 const request={scene_id:'scene://town01',record_id:'11111111-1111-4111-8111-111111111111',source_frame_indices:[0,1,0,1,0],edits:[{frame_index:0,object_index:0,translation:{x:-12}},{frame_index:4,object_index:0,translation:{x:20}}],object_index:0,start:0,end:4,expected_source_key:'a'.repeat(64),curve};
 const poses=expected[curve].map((x,i)=>({frame_index:i,before:pose(i===0?-12:i===4?20:5),after:pose(x)})),report={schema_version:'legaia.animation-record-interpolation.v3',scene_id:request.scene_id,record_id:request.record_id,project_source_key:request.expected_source_key,source_frame_indices:request.source_frame_indices,before_edits:request.edits,edits:poses.map(p=>({frame_index:p.frame_index,object_index:0,...p.after})),object_index:0,start:0,end:4,poses,before_record_sha256:'b'.repeat(64),after_record_sha256:'c'.repeat(64),project_changed:false,gameplay_verified:false,curve};
 assert.deepEqual(decodeEffectiveInterpolation(report,request,1,validateRetainedAxes),report);
 for(const mutate of [r=>r.curve='unknown',r=>delete r.curve,r=>r.schema_version='legaia.animation-record-interpolation.v1',r=>r.poses[1].after.translation.x++,r=>r.extra=1]){const bad=structuredClone(report);mutate(bad);assert.throws(()=>decodeEffectiveInterpolation(bad,request,1,validateRetainedAxes));}
 const full={...report,schema_version:'legaia.animation-record-interpolation.v4',all_objects:true,object_count:1,poses:poses.map(p=>({...p,object_index:0}))};assert.deepEqual(decodeEffectiveInterpolation(full,{...request,all_objects:true},1,validateRetainedAxes),full);assert.throws(()=>decodeEffectiveInterpolation(full,request,1,validateRetainedAxes));
}
console.log('Curved single/full-frame receipts bind exact curves, literal words, schemas and source requests.');
