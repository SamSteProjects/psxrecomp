import fs from 'node:fs';
import assert from 'node:assert/strict';
import {decodeFieldEquipmentTimelineChannel as decode,createFieldEquipmentTimeline,fieldEquipmentChannelTrack as track} from '../editor/field-equipment-timeline.js';

// Literal byte packing/decoding is independent of the timeline's decoder.
const pack=(translation,rotation,opaque)=>{const [x,y,z]=translation.map(v=>v&4095);return Uint8Array.from([x&255,y&255,(x>>>8)|((y>>>8)<<4),z&255,(z>>>8)|(opaque<<4),...rotation.map(v=>v/16)]);};
const literal=(bytes,frame,part)=>{const at=8+(frame*10+part)*8,b=bytes.subarray(at,at+8),sign=n=>(n&0x800)?n-0x1000:n;return {object_index:part,translation:[sign(b[0]|((b[2]&0xf)<<8)),sign(b[1]|((b[2]&0xf0)<<4)),sign(b[3]|((b[4]&0xf)<<8))],rotation_psx:[b[5]<<4,b[6]<<4,b[7]<<4],opaque_nibble:b[4]>>>4};};
const synthetic=new Uint8Array(176),v=new DataView(synthetic.buffer);v.setUint16(0,0x10a,true);v.setUint16(2,2,true);v.setUint16(4,0x080c,true);v.setUint16(6,2,true);
const edgeRows=[{t:[-2048,-1,2047],r:[0,16,4080],n:15},{t:[2047,-2048,0],r:[4080,2048,0],n:0},{t:[1,0,-1],r:[16,4064,32],n:7}];
let values=0,refusals=0;
for(let f=0;f<2;f++)for(let p=0;p<10;p++){const e=edgeRows[(f*10+p)%edgeRows.length];synthetic.set(pack(e.t,e.r,e.n),8+(f*10+p)*8);assert.deepEqual(decode(synthetic,f,p),{object_index:p,translation:e.t,rotation_psx:e.r,opaque_nibble:e.n});}
const surrounding=new Uint8Array(synthetic.length+7);surrounding.set(synthetic,3);assert.deepEqual(decode(surrounding.subarray(3,-4),1,9),literal(synthetic,1,9));
for(const [frame,part] of [[-1,0],[2,0],[.5,0],[0,-1],[0,10],[0,NaN],[NaN,0]]){assert.throws(()=>decode(synthetic,frame,part));refusals++;}
for(const change of [b=>b[0]=12,b=>b[1]=2,b=>b[4]=0,b=>b[6]=3,b=>b[2]=0,b=>b[b.length-1]=1]){const b=synthetic.slice();change(b);assert.throws(()=>decode(b,0,0));refusals++;}
assert.throws(()=>decode(synthetic.slice(0,-1),0,0));assert.throws(()=>decode(Array.from(synthetic),0,0));refusals+=2;

const cases=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
for(const {value,context} of cases){
 const model=await createFieldEquipmentTimeline(value,context),record=Uint8Array.from(Buffer.from(value.record_base64,'base64'));
 assert.equal(model.frameCount,value.frame_count);assert.equal(model.partCount,10);assert.equal(model.sourceOnly,true);assert.equal(model.modelLayer,context.modelLayer);
 for(let p=0;p<10;p++)for(const field of ['translation','rotation_psx'])for(const [a,axis] of [...'xyz'].entries()){
  const series=track(model,p,field,axis);assert.equal(series.samples.length,value.frame_count);assert.equal(track(model,p,field,axis),series);
  for(const row of series.samples){const expected=literal(record,row.frame,p);assert.equal(row.retail,expected[field][a]);assert.equal(row.opaque_nibble,expected.opaque_nibble);assert.equal(row.current,undefined);assert.equal(row.proposed,undefined);values++;}
  const first=series.samples[0].retail;assert.throws(()=>series.samples[0].retail++);assert.equal(series.samples[0].retail,first);
 }
 for(const args of [[-1,'translation','x'],[10,'translation','x'],[.5,'translation','x'],[0,'scale','x'],[0,'translation','w']]){assert.throws(()=>track(model,...args));refusals++;}
 const frozen=track(model,0,'translation','x');value.record_base64='';assert.equal(track(model,0,'translation','x'),frozen);
}
assert.throws(()=>track({frameCount:2,partCount:10},0,'translation','x'));refusals++;
const fresh=JSON.parse(fs.readFileSync(process.argv[2],'utf8'))[0];
for(const mutate of [v=>v.record_sha256='0'.repeat(64),v=>v.source_record.record_index++,v=>v.channel_count=12,v=>v.active_object_indices[0]=1,v=>v.preview.geometry.equipment_variant.source_descriptor_index=0,v=>v.preview.project_source_key='stale',v=>{const bytes=Buffer.from(v.record_base64,'base64');bytes[4]=0;v.record_base64=bytes.toString('base64');}]){const value=structuredClone(fresh.value);mutate(value);await assert.rejects(()=>createFieldEquipmentTimeline(value,fresh.context));refusals++;}
for(const patch of [{frameIndex:999},{clipId:'walk'},{equipmentByte:1},{modelLayer:'current'},{sourceKey:'stale'}]){await assert.rejects(()=>createFieldEquipmentTimeline(fresh.value,{...fresh.context,...patch}));refusals++;}
console.log(`${cases.length} field timeline clips / ${values} literal axis samples, edge codecs, cached tracks and ${refusals} malformed/source/index refusals passed`);
