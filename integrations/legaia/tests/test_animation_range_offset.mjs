import assert from 'node:assert/strict';
import {offsetAnimationRange} from '../editor/animation-range.js';
const edits=[{frame_index:0,object_index:0,translation:{x:-2048,y:10},rotation_psx:{x:4080,z:0}},{frame_index:1,object_index:0,translation:{x:2040}},{frame_index:1,object_index:1,translation:{x:50}}],args={start:0,end:1,frameCount:4,objectCount:2,object:0,kind:'translation',delta:{x:7,y:0,z:9},edits},held=structuredClone(args),r=offsetAnimationRange(args);
assert.equal(r.changedAxes,2);assert.deepEqual(r.proposed,[{frame_index:0,object_index:0,translation:{x:-2041}},{frame_index:1,object_index:0,translation:{x:2047}}]);assert.deepEqual(r.edits[0],{...edits[0],translation:{x:-2041,y:10}});assert.deepEqual(r.edits[2],edits[2]);assert.deepEqual(args,held);r.edits[0].translation.y=99;assert.deepEqual(args,held);
const rotation=offsetAnimationRange({...args,kind:'rotation_psx',delta:{x:32,y:0,z:-16}});assert.equal(rotation.changedAxes,2);assert.deepEqual(rotation.proposed,[{frame_index:0,object_index:0,rotation_psx:{x:16,z:4080}}]);assert.deepEqual(rotation.edits[0].translation,edits[0].translation);
assert.equal(offsetAnimationRange({...args,object:null}).changedAxes,3);
for(const update of [{delta:{x:8,y:0,z:0}},{delta:{x:-1,y:0,z:0}},{delta:{x:0,y:0,z:0}},{delta:{x:0,y:0,z:8},start:1},{delta:{x:.5,y:0,z:0}},{delta:{x:4096,y:0,z:0}},{delta:{x:1,y:0}},{delta:{x:1,y:0,z:0,w:0}},{kind:'rotation_psx',delta:{x:1,y:0,z:0}},{kind:'rotation_psx',delta:{x:4096,y:0,z:0}},{object:2},{start:2,end:1},{edits:[...edits,edits[0]]}])assert.throws(()=>offsetAnimationRange({...args,...update}));
assert.deepEqual(args,held);
console.log('Exact sparse offsets, native translation boundaries, signed rotation wrap, complete refusal and detached outside contributions passed.');
