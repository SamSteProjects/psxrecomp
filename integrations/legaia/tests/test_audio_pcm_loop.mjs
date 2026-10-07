import assert from 'node:assert/strict';
import {encodedPcmLoop,validatePcmLoop,pcmLoopFrame} from '../editor/audio-pcm-loop.js';
import {renderEnvelopePcm} from '../editor/audio-envelope-audition.js';
const marker=(block,flags)=>({block_index:block,frame_offset:block*28,flags,encoded_shift:0,effective_shift:0});
const wave=(markers,reason='encoded-end')=>({decoded_frames:84,decoded_blocks:3,consumed_bytes:48,termination:{reason,byte_offset:reason==='encoded-end'?32:48},markers});
const qualified=wave([marker(1,4),marker(2,3)]),loop=encodedPcmLoop(qualified,84);
assert.deepEqual(loop,{startFrame:28,endFrame:84});
assert.deepEqual([0,27,28,83,84,139,140,10000].map(n=>pcmLoopFrame(n,84,loop)),[0,27,28,83,28,83,28,32]);
assert.deepEqual(encodedPcmLoop(wave([marker(0,4),marker(1,4),marker(2,3)]),84),loop);
assert.deepEqual(encodedPcmLoop(wave([marker(2,7)]),84),{startFrame:56,endFrame:84});
assert.equal(encodedPcmLoop(wave([marker(1,4),marker(2,1)]),84),null);
assert.equal(encodedPcmLoop(wave([marker(2,3)]),84),null);
assert.equal(encodedPcmLoop(wave([marker(1,4)],'preview-budget'),84),null);
for(const mutate of [v=>v.decoded_frames++,v=>v.consumed_bytes++,v=>v.termination.byte_offset=16,v=>v.markers[0].flags=12,v=>v.markers[0].frame_offset++,v=>v.markers.reverse(),v=>v.markers[0].flags=1,v=>v.markers[0].effective_shift=9]){const bad=structuredClone(qualified);mutate(bad);assert.throws(()=>encodedPcmLoop(bad,84));}
for(const value of [{startFrame:1,endFrame:84},{startFrame:84,endFrame:84},{startFrame:28,endFrame:56},{startFrame:28,endFrame:84,extra:1},{startFrame:true,endFrame:84}])assert.throws(()=>validatePcmLoop(value,84));
const raw=new Uint8Array(168),view=new DataView(raw.buffer);for(let i=0;i<84;i++)view.setInt16(i*2,i<28?16000:i<56?-16000:8000,true);
const before=raw.slice(),render=(rate,keyOffFrame=180)=>renderEnvelopePcm(raw,rate,15,31,{frameCount:200,keyOffFrame},loop),samples=v=>Array.from({length:v.bytes.length/2},(_,i)=>new DataView(v.bytes.buffer).getInt16(i*2,true));
const native=samples(render(44100));assert.deepEqual(native.slice(0,3),[7000,14000,15999]);assert.equal(native[83],7999);assert.equal(native[84],-15999);assert.equal(native[139],7999);assert.equal(native[140],-15999);assert.equal(native[199],-15999);assert.deepEqual(raw,before);
const resampled=samples(render(22050));assert.equal(resampled[167],-3999);assert.equal(resampled[168],-15999); // linear interpolation wraps end -> loop start
const release=samples(renderEnvelopePcm(raw,44100,15,0,{frameCount:200,keyOffFrame:90},loop));assert.equal(release[90],-7999);assert.equal(release[91],0);assert(release.slice(91).every(n=>n===0));
assert(samples(renderEnvelopePcm(raw,44100,15,31,{frameCount:200,keyOffFrame:180})).slice(84).every(n=>n===0));
console.log('Encoded loop qualification, last-start ownership, intro, wrap interpolation, Release, one-pass fallback and immutable PCM passed.');
