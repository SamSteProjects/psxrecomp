import assert from 'node:assert/strict';
import {decodeAdsrWord,editAdsrWord,describeAdsrWord} from '../editor/audio-adsr.js';
// Independent native masks from the documented two-word register layout.
const masks={adsr1:{attack_mode:[15,1],attack_shift:[10,31],attack_step:[8,3],decay_shift:[4,15],sustain_level:[0,15]},adsr2:{sustain_mode:[15,1],sustain_direction:[14,1],sustain_shift:[8,31],sustain_step:[6,3],release_mode:[5,1],release_shift:[0,31]}};
for(const field of Object.keys(masks))for(const word of [0,1,0x2000,0x80ff,0x5fcf,65535]){
 const rows=decodeAdsrWord(field,word);assert.equal(rows.length,Object.keys(masks[field]).length);
 for(const [key,[shift,max]] of Object.entries(masks[field])){
  const row=rows.find(r=>r.key===key);assert.equal(row.value,(word>>>shift)&max);
  for(const value of [0,max]){const changed=editAdsrWord(field,word,key,value),mask=max<<shift;assert.equal(changed&mask,value<<shift);assert.equal(changed&~mask,word&~mask);if(field==='adsr2')assert.equal(changed&0x2000,word&0x2000);}
  for(const value of [-1,max+1,.5,NaN,true,'1'])assert.throws(()=>editAdsrWord(field,word,key,value));
 }
 let roundtrip=word;for(const row of rows)roundtrip=editAdsrWord(field,roundtrip,row.key,row.value);assert.equal(roundtrip,word);
 rows[0].value=99;assert.notEqual(decodeAdsrWord(field,word)[0].value,99);
}
assert(describeAdsrWord('adsr1',0x80ff).includes('Attack mode: Exponential'));assert(describeAdsrWord('adsr1',0x80ff).includes('Encoded sustain target: 32768'));assert(describeAdsrWord('adsr2',0x2000).includes('Held reserved bit 13: 1'));
for(const field of ['adsr3','__proto__',null])assert.throws(()=>decodeAdsrWord(field,0));
for(const word of [-1,65536,true,'1',NaN,.1])assert.throws(()=>decodeAdsrWord('adsr1',word));
assert.throws(()=>editAdsrWord('adsr2',0,'reserved',1));
console.log('ADSR register fields, independent masks, strict integer bounds, detached decoding and held reserved-bit roundtrips passed.');
