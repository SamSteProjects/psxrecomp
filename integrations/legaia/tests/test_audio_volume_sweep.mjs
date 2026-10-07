import assert from 'node:assert/strict';
import {simulateVolumeRegister,renderSweepStereo} from '../editor/audio-volume-sweep.js';
import {renderStaticStereo} from '../editor/audio-static-stereo.js';
const values=(raw,initial,n=4)=>Array.from(simulateVolumeRegister(raw,initial,n).levels);
assert.deepEqual(values(0x8000,0),[14336,28672,32767,32767]);assert.deepEqual(values(0xa000,32767),[16383,0,0,0]);
assert.deepEqual(values(0xe000,32767),[16383,8191,4095,2047]);assert.deepEqual(values(0x9000,0),[-14336,-28672,-32767,-32767]);assert.deepEqual(values(0xb000,-32767),[-16383,0,0,0]);
assert.deepEqual(values(0x907f,123),[123,123,123,123]);assert.deepEqual(values(0xc000,24576),[28160,31744,32767,32767]);assert.deepEqual(values(8192,-123),[16384,16384,16384,16384]);
assert.deepEqual(values(0x8f80,0),values(0x8000,0)); // bits11..7 ignored by the recomp
const pcm=new Uint8Array(8),view=new DataView(pcm.buffer);[32767,-32768,-1,1].forEach((v,i)=>view.setInt16(i*2,v,true));const copy=pcm.slice();
assert.deepEqual(renderSweepStereo(pcm,[8192,24576],[0,0]).bytes,renderStaticStereo(pcm,8192,24576).bytes);
const mixed=renderSweepStereo(pcm,[0x8000,0x9000],[0,0]),words=Array.from({length:8},(_,i)=>new DataView(mixed.bytes.buffer).getInt16(i*2,true));assert.deepEqual(words,[14335,-14336,-28672,28672,-1,0,0,-1]);assert.deepEqual(pcm,copy);assert.equal(mixed.channels,2);assert.deepEqual(mixed.finalLevels,[32767,-32767]);
const padded=new Uint8Array(12);padded.set(pcm,2);assert.deepEqual(renderSweepStereo(padded.subarray(2,10),[8192,0],[0,0]).bytes,renderStaticStereo(pcm,8192,0).bytes);
for(const args of [[true,0,4],[-1,0,4],[65536,0,4],[32768,32768,4],[32768,0,0],[32768,0,220501],[32768,NaN,4]])assert.throws(()=>simulateVolumeRegister(...args));
for(const args of [[new Uint8Array(3),[0,0],[0,0]],[pcm,[0],[0,0]],[pcm,[0,0],[0,1.5]],[new Uint8Array(441002),[0,0],[0,0]]])assert.throws(()=>renderSweepStereo(...args));
console.log('Sweep modes, phases, freezes, signed initial levels, ignored bits, static equivalence, rounding, offset buffers and bounds passed.');
