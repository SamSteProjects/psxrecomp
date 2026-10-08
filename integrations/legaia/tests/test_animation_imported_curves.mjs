import assert from 'node:assert/strict';
import {interpolateAnimationRange} from '../editor/animation-range.js';
import {interpolateNativeFrameAxis} from '../editor/animation-sample-curves.js';
const pose=x=>({translation:{x,y:0,z:0},rotation_psx:{x:4080,y:0,z:0}}),args={first:pose(-12),last:{...pose(20),rotation_psx:{x:48,y:0,z:0}},start:0,end:4,object:0,frameCount:6,objectCount:2,edits:[{frame_index:5,object_index:0,translation:{y:17}},{frame_index:2,object_index:1,rotation_psx:{z:32}}]},held=structuredClone(args);
for(const [curve,words] of Object.entries({linear:[-12,-4,4,12,20],ease_in:[-12,-10,-4,6,20],ease_out:[-12,2,12,18,20],smoothstep:[-12,-7,4,15,20]})){const result=interpolateAnimationRange({...args,curve});assert.deepEqual(result.proposed.map(r=>r.translation.x),words);assert.deepEqual(result.edits.filter(r=>r.object_index===1||r.frame_index===5).sort((a,b)=>a.frame_index-b.frame_index),[held.edits[1],held.edits[0]]);assert.deepEqual(result.proposed[0].translation,args.first.translation);assert.deepEqual(result.proposed.at(-1).rotation_psx,args.last.rotation_psx);assert.deepEqual(args,held);}
const large=interpolateAnimationRange({...args,frameCount:4096,start:0,end:4095,edits:[],curve:'smoothstep'});assert.equal(large.edits.length,4096);assert.equal(large.proposed[0].translation.x,-12);assert.equal(large.proposed.at(-1).translation.x,20);
assert.equal(interpolateNativeFrameAxis('translation',-1,0,2048,4095,'smoothstep'),0);
for(const curve of [null,0,'unknown',{},[]])assert.throws(()=>interpolateAnimationRange({...args,curve}));
console.log('Imported curve literal samples, preserved ownership/inputs, native grid and full 4096-row budget passed.');
