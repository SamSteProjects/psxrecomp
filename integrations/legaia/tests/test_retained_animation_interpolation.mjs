import assert from 'node:assert/strict';
import {interpolateRetainedFrameRange} from '../editor/animation-record-edit.js';
const input={frameCount:5,objectCount:2,objectIndex:0,start:0,end:4,edits:[
  {frame_index:0,object_index:0,translation:{x:-2},rotation_psx:{y:4080}},
  {frame_index:2,object_index:0,translation:{x:99,z:7}},
  {frame_index:3,object_index:1,rotation_psx:{x:1024}},
  {frame_index:4,object_index:0,translation:{x:2},rotation_psx:{y:16}}]};
const before=structuredClone(input),result=interpolateRetainedFrameRange(input),rows=result.edits.filter(r=>r.object_index===0);
assert.deepEqual(rows.map(r=>r.translation.x),[-2,-1,0,1,2]);assert.deepEqual(rows.map(r=>r.rotation_psx.y),[4080,0,0,16,16]);assert.equal(rows[2].translation.z,7);assert.equal(result.axis_count,2);assert.equal(result.frame_count,5);assert.deepEqual(result.edits.find(r=>r.object_index===1),input.edits[2]);assert.deepEqual(input,before);
const half=interpolateRetainedFrameRange({...input,frameCount:3,end:2,edits:[{frame_index:0,object_index:0,translation:{x:-1},rotation_psx:{z:0}},{frame_index:2,object_index:0,translation:{x:0},rotation_psx:{z:2048}}]});assert.equal(half.edits[1].translation.x,0);assert.equal(half.edits[1].rotation_psx.z,1024);
const bounded=interpolateRetainedFrameRange({...input,start:1,end:3,edits:[...input.edits,{frame_index:1,object_index:0,translation:{y:10}},{frame_index:3,object_index:0,translation:{y:14}}]});assert.equal(bounded.edits.find(r=>r.frame_index===2&&r.object_index===0).translation.y,12);assert.deepEqual(bounded.edits.find(r=>r.frame_index===0),input.edits[0]);assert.deepEqual(bounded.edits.find(r=>r.frame_index===4),input.edits[3]);assert.equal(bounded.edits.find(r=>r.frame_index===2).translation.x,99);
for(const extra of [{end:0},{end:5},{start:true},{objectIndex:2},{objectCount:1024},{edits:input.edits.slice(1)},{edits:input.edits.map(r=>r.frame_index===4?{...r,translation:{z:2}}:r)},{edits:[...input.edits,input.edits[0]]}])assert.throws(()=>interpolateRetainedFrameRange({...input,...extra}));
result.edits[0].translation.x=42;assert.deepEqual(input,before);
console.log('Retained partial-axis interpolation, wrapping/grid ties, endpoint rejection, detached data and unrelated contribution preservation passed.');
