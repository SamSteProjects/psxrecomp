import fs from 'node:fs';
import assert from 'node:assert/strict';
import {replayWorldVectors} from '../editor/worldmap-model-vector-replay.js';
const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),bytes=s=>new Uint8Array(Buffer.from(s,'base64'));let refusals=0;
for(const row of rows){
 const base=bytes(row.base);assert.deepEqual(await replayWorldVectors(base,base,row.binding),bytes(row.candidate));
 const operations=ledger=>ledger.batches??ledger.operations;
 for(const mutate of [b=>operations(b.ledger)[0].additions[0].donor_face_id='foreign',b=>operations(b.ledger)[0].additions[0].face_id='face://authored/invalid',b=>operations(b.ledger)[0].additions[0].fields.vertices[0]=8192,b=>operations(b.ledger)[0].additions.push(structuredClone(operations(b.ledger)[0].additions[0])),b=>operations(b.ledger)[0].extra=true,b=>operations(b.ledger)[0].proposed_sha256='0'.repeat(64),b=>b.ledger.source_sha256='0'.repeat(64),b=>b.asset_sha256='0'.repeat(64)]){
  const bad=structuredClone(row.binding);mutate(bad);await assert.rejects(replayWorldVectors(base,base,bad));refusals++;
 }
}
assert(rows.length);console.log(`${rows.length} complete native face/vector/content pairs and ${refusals} forged identity/reference/schema/hash refusals passed.`);
