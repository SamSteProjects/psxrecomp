import assert from 'node:assert/strict';
import {selectVertexRectangle as select} from '../editor/model-vertex-marquee.js';
const points=[{index:4,x:10,y:10,depth:3},{index:2,x:20,y:20,depth:8},{index:2,x:20,y:20,depth:8},{index:1,x:40,y:40,depth:3},{index:5,x:-1,y:10,depth:1},null,{index:9,x:NaN,y:1,depth:1}],before=structuredClone(points),existing=[0,2];
assert.deepEqual(select(points,[25,25],[5,5],100,100),[2,4]);
assert.deepEqual(select(points,[5,5],[25,25],100,100,existing,true),[0,2,4]);
assert.deepEqual(select(points,[-10,0],[15,15],100,100),[4]);
assert.deepEqual(select(points,[70,70],[90,90],100,100),[]);
assert.deepEqual(select(points,[70,70],[90,90],100,100,existing,true),existing);
assert.deepEqual(points,before);assert.deepEqual(existing,[0,2]);
const many=Array.from({length:4097},(_,index)=>({index,x:10,y:10,depth:1}));
assert.throws(()=>select(many,[0,0],[20,20],100,100));assert.equal(select(many.slice(0,4096),[0,0],[20,20],100,100).length,4096);
assert.throws(()=>select(many.slice(1),[0,0],[20,20],100,100,[0],true));
for(const args of [[points,[0,NaN],[20,20],100,100],[points,[0,0],[20,20],0,100],[points,[0,0],[20,20],100,100,[1,1]],[points,[0,0],[20,20],100,100,[true]],[points,[0,0],[20,20],100,100,[],1]])assert.throws(()=>select(...args));
// Marker drawing is capped separately; rectangle selection still covers later rows.
assert.deepEqual(select([{index:3000,x:12,y:12,depth:4}],[0,0],[20,20],100,100),[3000]);
console.log('Vertex marquee: inclusive/reversed/clipped bounds, hidden/deep rows, add/replace, uniqueness, immutable inputs, drawing-cap independence and bounded overflow passed');
