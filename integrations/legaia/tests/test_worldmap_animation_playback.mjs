import fs from 'node:fs';
import assert from 'node:assert/strict';
import {createWorldAnimationSampler,sampledWorldFrame} from '../editor/worldmap-animation-playback.js';

const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
function equal(actual,expected){
  if(typeof expected==='number'){assert(Number.isFinite(actual));assert(Math.abs(actual-expected)<=1e-8);}
  else if(Array.isArray(expected)){assert(Array.isArray(actual));assert.equal(actual.length,expected.length);expected.forEach((v,i)=>equal(actual[i],v));}
  else if(expected&&typeof expected==='object'){assert.deepEqual(Object.keys(actual).sort(),Object.keys(expected).sort());for(const key of Object.keys(expected))equal(actual[key],expected[key]);}
  else assert.equal(actual,expected);
}
let frames=0;
for(const row of rows){
  const before=structuredClone(row),sampler=await createWorldAnimationSampler(row.preview,row.source);
  for(const native of row.frames){equal(sampler.sample(native.frame_index),native);frames++;}
  assert.deepEqual(row,before);
  // Returned geometry never aliases the retained raw model or subsequent samples.
  const first=sampler.sample(0);first.geometry.vertices[0][0]+=100;
  equal(sampler.sample(0),row.frames[0]);
  for(const frame of [-1,sampler.frameCount,.5,NaN,Infinity,true])assert.throws(()=>sampler.sample(frame));
  for(const mutate of [p=>p.record_sha256='0'.repeat(64),p=>p.bank_sha256='0'.repeat(64),p=>p.geometry.vertices[0][0]++]){
    const bad=structuredClone(row.preview);mutate(bad);await assert.rejects(createWorldAnimationSampler(bad,row.source));
  }
  await assert.rejects(createWorldAnimationSampler(row.preview,row.preview.geometry));
}
assert.equal(frames,125);
assert.equal(sampledWorldFrame(3,20,12,0),3);
assert.equal(sampledWorldFrame(3,20,12,82),3);
assert.equal(sampledWorldFrame(3,20,12,84),4);
assert.equal(sampledWorldFrame(3,20,60,1e6),19);
assert.equal(sampledWorldFrame(0,1,1,1000),0);
for(const args of [[-1,20,12,0],[20,20,12,0],[0,513,12,0],[0,20,0,0],[0,20,61,0],[0,20,12.5,0],[0,20,12,-1],[0,20,12,Infinity]])assert.throws(()=>sampledWorldFrame(...args));
console.log(`${frames} native frame/normal oracles, immutable sampler inputs and bounded one-pass display clock passed.`);
