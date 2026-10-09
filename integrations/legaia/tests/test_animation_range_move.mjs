import assert from 'node:assert/strict';
import {moveAnimationRange,duplicateAnimationRange} from '../editor/animation-range.js';
const edits=[{frame_index:0,object_index:0,translation:{x:10,y:20}},{frame_index:1,object_index:0,translation:{x:30},rotation_psx:{z:4080}},{frame_index:2,object_index:0,translation:{y:40}},{frame_index:1,object_index:1,translation:{x:50}}],args={start:0,end:1,frameCount:5,objectCount:2,object:0,axes:'translation.x',offset:1,edits},held=structuredClone(args),result=moveAnimationRange(args);
assert.equal(result.movedAxes,2);assert.deepEqual(result.proposed,[{frame_index:1,object_index:0,translation:{x:10}},{frame_index:2,object_index:0,translation:{x:30}}]);assert.deepEqual(result.edits,[{frame_index:0,object_index:0,translation:{y:20}},{frame_index:1,object_index:0,rotation_psx:{z:4080},translation:{x:10}},edits[3],{frame_index:2,object_index:0,translation:{y:40,x:30}}]);assert.deepEqual(args,held);result.edits[0].translation.y=99;assert.deepEqual(args,held);
const reverse=moveAnimationRange({...args,start:1,end:1,axes:'rotation_psx',offset:-1});assert.deepEqual(reverse.proposed,[{frame_index:0,object_index:0,rotation_psx:{z:4080}}]);assert.equal(reverse.edits.find(r=>r.frame_index===1&&r.object_index===0).translation.x,30);
for(const update of [{offset:0},{offset:.5},{offset:-1},{offset:5},{start:0,end:0,offset:1},{start:2,end:3,axes:'rotation_psx'},{offset:4},{edits:[...edits,{frame_index:2,object_index:0,translation:{x:30}}]}])assert.throws(()=>moveAnimationRange({...args,...update}));
assert.equal(moveAnimationRange({...args,start:1,end:1,object:null,axes:'all',offset:2}).movedAxes,3);
console.log('Simultaneous overlapping shifts, sparse axes, exact values, disjoint destinations, collisions, bounds and detached contributions passed.');

assert.throws(()=>moveAnimationRange({...args,start:1,end:1,offset:1,edits:edits.map(r=>r.frame_index===2?{...r,translation:{x:30,y:40}}:r)}),/already has/);
const full=Array.from({length:4096},(_,i)=>({frame_index:Math.floor(i/64),object_index:i%64,translation:{x:1,y:2}}));assert.throws(()=>moveAnimationRange({start:0,end:0,frameCount:65,objectCount:64,object:0,axes:'translation.x',offset:64,edits:full}),/4096/);

const duplicate=duplicateAnimationRange({...args,offset:3});
assert.equal(duplicate.duplicatedAxes,2);
assert.deepEqual(duplicate.proposed,[{frame_index:3,object_index:0,translation:{x:10}},{frame_index:4,object_index:0,translation:{x:30}}]);
assert.deepEqual(duplicate.edits.slice(0,4),[edits[0],edits[1],edits[3],edits[2]]);
assert.deepEqual(args,held);duplicate.edits[0].translation.x=99;assert.deepEqual(args,held);
assert.throws(()=>duplicateAnimationRange(args),/already has/); // Moving this overlap succeeds; duplication retains and protects the source.
const merge=duplicateAnimationRange({...args,start:0,end:0,axes:'translation.x',offset:2});
assert.deepEqual(merge.edits.find(r=>r.frame_index===2&&r.object_index===0).translation,{y:40,x:10});
assert.equal(merge.edits[0].translation.x,10);
assert.equal(duplicateAnimationRange({...args,start:1,end:1,object:null,axes:'all',offset:2}).duplicatedAxes,3);
assert.throws(()=>duplicateAnimationRange({...args,start:1,end:1,offset:1,edits:edits.map(r=>r.frame_index===2?{...r,translation:{x:30,y:40}}:r)}),/already has/);
for(const offset of [0,.5,-1,5,4])assert.throws(()=>duplicateAnimationRange({...args,offset}));
assert.throws(()=>duplicateAnimationRange({start:0,end:0,frameCount:65,objectCount:64,object:0,axes:'translation.x',offset:64,edits:full}),/4096/);
console.log('Duplication retains detached source contributions, merges disjoint axes and refuses occupied source/destination overlaps and budget overflow.');
