import assert from 'node:assert/strict';
import fs from 'node:fs';
import {encodeNpcArrivalReference,npcArrivalReference} from '../editor/npc-transitions.js';
if(!process.argv[2])throw new Error('Provide the native arrival encoder reference fixture.');
const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
assert.equal(rows.length,256);
for(const {arrival,effective,encoded,reference} of rows){
  assert.deepEqual(encodeNpcArrivalReference(arrival,effective),encoded);
  assert.deepEqual(npcArrivalReference(encoded),reference);
}
const effective={entry_x_encoded:1,entry_z_encoded:2,direction_encoded:227};
assert.deepEqual(encodeNpcArrivalReference({x:64,z:16384,facing_sector:7},effective),{entry_x_encoded:0,entry_z_encoded:255,direction_encoded:231});
assert.deepEqual(effective,{entry_x_encoded:1,entry_z_encoded:2,direction_encoded:227});
for(const arrival of [{},{x:0},{x:32},{x:65},{x:16385},{x:64.5},{x:true},{x:NaN},{z:Infinity},{facing_sector:8},{facing_sector:true},{y:64},{destination:'town01'},[]])assert.throws(()=>encodeNpcArrivalReference(arrival,effective));
assert.throws(()=>encodeNpcArrivalReference({x:64},{...effective,direction_encoded:256}));
console.log('All 256 native encoder/reference cases, exact grid bounds, direction upper bits, independent values and invalid-field refusal passed.');
