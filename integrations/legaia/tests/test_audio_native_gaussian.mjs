import assert from 'node:assert/strict';
import fs from 'node:fs';
import {GAUSSIAN_TABLE,gaussianSample,previewPitch,renderGaussianEnvelope} from '../editor/audio-native-gaussian.js';
import {renderNativeEnvelope} from '../editor/audio-native-loop.js';
import {mountEnvelopeAudition} from '../editor/audio-envelope-audition.js';
const signed=v=>(v<<16)>>16;
const read=bytes=>Int16Array.from({length:bytes.length/2},(_,i)=>new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength).getInt16(i*2,true));
assert.equal(GAUSSIAN_TABLE.length,512);assert(Object.isFrozen(GAUSSIAN_TABLE));
assert.deepEqual(previewPitch(44100),{pitchRegister:4096,effectiveSourceRate:44100});
for(const invalid of [true,44101,0,'44100'])assert.throws(()=>previewPitch(invalid));
for(const args of [[new Int16Array(0),0,0],[new Int16Array(1),-1,0],[new Int16Array(1),0,-1],[new Int16Array(1),0,0.5],[new Uint8Array(3),0,0]])assert.throws(()=>gaussianSample(...args));
const zeros=new Int16Array(4);assert.equal(gaussianSample(zeros,0,0),0);
const file=process.argv[2];if(!file)throw Error('Supply fresh source/native Gaussian oracle fixtures.');const fixture=JSON.parse(fs.readFileSync(file,'utf8'));
const oracle=read(fs.readFileSync(fixture.taps_file));let at=0;
for(let pattern=0;pattern<4;pattern++){
 const samples=Int16Array.from({length:31},(_,i)=>pattern===0?32767:pattern===1?-32768:pattern===2?(i%2?32767:-32768):signed(i*7919-50000));
 for(const index of [0,1,2,3,27])for(let phase=0;phase<4096;phase++)assert.equal(gaussianSample(samples,index+3,phase),oracle[at++],`pattern ${pattern} index ${index} phase ${phase}`);
}
assert.equal(at,81920);
for(const row of fixture.gaussianOracleCases){
 const raw=Uint8Array.from(Buffer.from(fixture.adpcm[row.layer].adpcm_base64,'base64')),before=raw.slice(),expected=read(fs.readFileSync(row.pcm_file));
 const result=renderGaussianEnvelope(raw,row.rate,15,31,{frameCount:row.frames,keyOffFrame:22050}),out=read(result.bytes);
 assert.equal(result.pitchRegister,row.pitch);assert.equal(result.interpolation,'native-gaussian');
 for(let i=0;i<out.length;i++)assert.equal(out[i],Math.floor(expected[i]*result.model.levels[i]/32768),`${row.layer} ${row.rate} frame ${i}`);
 assert.deepEqual(raw,before);
 if(row.rate===44100)assert.notDeepEqual(result.bytes,renderNativeEnvelope(raw,row.rate,15,31,{frameCount:row.frames,keyOffFrame:22050}).bytes);
}
const raw=Uint8Array.from(Buffer.from(fixture.adpcm.current.adpcm_base64,'base64'));
assert.equal(renderGaussianEnvelope(raw,48000,15,31,{frameCount:220500,keyOffFrame:200000}).bytes.length,441000);
assert.throws(()=>renderGaussianEnvelope(raw,44101,15,31));
assert.throws(()=>renderGaussianEnvelope(new Uint8Array(65537),44100,15,31));
class Element{constructor(tag){this.tag=tag;this.children=[];this.style={};this.attrs={};this.value='';this.textContent='';}append(...nodes){this.children.push(...nodes);}replaceChildren(...nodes){this.children=[...nodes];}setAttribute(key,value){this.attrs[key]=value;}}
globalThis.document={createElement:tag=>new Element(tag)};
const nodes=root=>[root,...root.children.flatMap(nodes)],control=(root,label)=>nodes(root).find(n=>n.attrs['aria-label']===label),button=(root,label)=>nodes(root).find(n=>n.tag==='button'&&n.textContent===label);
let fresh=true,stops=0,played=null;const errors=[],request=async(path,init)=>{const body=JSON.parse(init.body),value=path==='/api/audio-sample-authoring'?fixture.options:path==='/api/audio-sample-adpcm'?fixture.adpcm[body.layer]:fixture.pcm[body.layer];return {ok:true,text:async()=>JSON.stringify(value)};};
const audioContext=()=>({destination:{},resume:async()=>{},close:async()=>{},createGain:()=>({gain:{value:0},connect(){},disconnect(){}}),createBuffer(channels,frames,rate){played=new Float32Array(frames);return {getChannelData:()=>played};},createBufferSource:()=>({connect(){},disconnect(){},start(){},stop(){stops++;}})});
const host=new Element('section'),mounted=mountEnvelopeAudition(host,{bank:fixture.bank,request,audioContext,fresh:()=>fresh,onError:e=>errors.push(e.message)});mounted.update(fixture.config);
const interpolation=control(host,'Envelope native interpolation'),mode=control(host,'Envelope sample playback'),rate=control(host,'Envelope sample rate'),load=button(host,'Load envelope sample'),play=button(host,'Play envelope audition');
assert(interpolation.disabled&&interpolation.children[1].disabled);await load.onclick();rate.value='44100';mode.value='native-loop';mode.onchange();assert(interpolation.children[1].disabled);
interpolation.value='gaussian';interpolation.onchange();assert.equal(interpolation.value,'linear');await load.onclick();assert(!interpolation.children[1].disabled);
interpolation.value='gaussian';interpolation.onchange();await play.onclick();assert(played);
const row=fixture.config.layers[0],expected=read(renderGaussianEnvelope(Uint8Array.from(Buffer.from(fixture.adpcm.retail.adpcm_base64,'base64')),44100,row.adsr1,row.adsr2,{keyOffFrame:22050}).bytes);
for(let i=0;i<expected.length;i++)assert.equal(played[i],expected[i]/32768);
interpolation.value='linear';interpolation.onchange();assert.equal(stops,1);assert(button(host,'Stop envelope audition').disabled);
mode.value='encoded-loop';mode.onchange();assert(interpolation.disabled);mounted.clear();mounted.update(fixture.config);assert.equal(interpolation.value,'linear');assert(interpolation.children[1].disabled);
fresh=false;interpolation.value='gaussian';interpolation.onchange();assert(host.hidden&&play.disabled);assert.deepEqual(errors,[]);
console.log('81920 native C tap results and 1102500 native ADPCM/Gaussian counter samples match; all explicit rates, boundaries/history, signed shaping, bounded output and immutable inputs passed.');
