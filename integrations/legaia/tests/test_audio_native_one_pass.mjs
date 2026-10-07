import assert from 'node:assert/strict';
import fs from 'node:fs';
import {decodeNativeOnePass,nativeOnePassQualified,decodeNativeSample,renderNativeOnePassEnvelope} from '../editor/audio-native-loop.js';
import {renderGaussianEnvelope} from '../editor/audio-native-gaussian.js';
const block=(header,flags,data=0)=>Uint8Array.from([header,flags,...Array(14).fill(data)]),raw=Uint8Array.from([...block(0,0,0x11),...block(0x10,1),...block(0,7,0x77)]),before=raw.slice();
const read=bytes=>Int16Array.from({length:bytes.length/2},(_,i)=>new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength).getInt16(i*2,true));
const decoded=decodeNativeOnePass(raw);assert.equal(decoded.sourceFrames,56);assert.equal(decoded.consumedBytes,32);assert.equal(read(decoded.bytes)[0],4096);assert.equal(read(decoded.bytes)[28],3840);assert.deepEqual(raw,before);
assert.deepEqual(decodeNativeOnePass(raw.slice(0,32)).bytes,decoded.bytes);assert.deepEqual(decodeNativeOnePass(Uint8Array.from([...raw.slice(0,32),255])).bytes,decoded.bytes);
for(const bad of [block(0,3),block(0,7),block(0x0d,1),block(0x50,1),block(0,8),block(0,0),new Uint8Array(65537)])assert.throws(()=>decodeNativeOnePass(bad));
for(const rate of [11025,22050,32000,44100,48000]){
 const output=renderNativeOnePassEnvelope(raw,rate,15,31,{frameCount:500,keyOffFrame:400});assert.equal(output.endFrame,Math.ceil(56*44100/rate));assert(read(output.bytes).slice(output.endFrame).every(v=>v===0));
 const gaussian=renderGaussianEnvelope(raw,rate,15,31,{frameCount:500,keyOffFrame:400},'one-pass');assert(gaussian.nativeOnePass);assert(read(gaussian.bytes).slice(gaussian.endFrame).every(v=>v===0));
}
assert.throws(()=>renderGaussianEnvelope(raw,44100,15,31,{},'unknown'));
const file=process.argv[2];if(!file)throw Error('Supply fresh nonrepeat native oracle fixtures.');const f=JSON.parse(fs.readFileSync(file,'utf8'));
for(const row of f.onePassOracleCases){
 const dto=f.adpcm[row.layer],raw=Uint8Array.from(Buffer.from(dto.adpcm_base64,'base64')),source=f.pcm[row.layer],pcm=Uint8Array.from(Buffer.from(source.pcm_base64,'base64'));
 assert(nativeOnePassQualified(source.waveform));assert.deepEqual(decodeNativeOnePass(raw).bytes,pcm);
 const verified=await decodeNativeSample(dto,f.config.context,f.bank,f.bank.samples[f.sampleIndex],row.layer,source.sample_sha256,f.config.currentEntryHash,source.waveform,pcm,'one-pass');assert.deepEqual(verified,raw);
 await assert.rejects(()=>decodeNativeSample(dto,f.config.context,f.bank,f.bank.samples[f.sampleIndex],row.layer,source.sample_sha256,f.config.currentEntryHash,source.waveform,pcm));
 const actual=renderGaussianEnvelope(raw,row.rate,15,31,{frameCount:row.frames,keyOffFrame:22050},'one-pass'),words=read(actual.bytes),expected=read(fs.readFileSync(row.pcm_file));
 for(let i=0;i<words.length;i++)assert.equal(words[i],Math.floor(expected[i]*actual.model.levels[i]/32768),`${row.layer} ${row.rate} ${i}`);
 assert(words.slice(actual.endFrame).every(v=>v===0));
}
console.log('Native nonrepeat first pass, opaque-tail exclusion, all-rate END mute, exact Current PCM/native DTO guards and complete compiled Gaussian/end-stop oracle outputs passed.');
