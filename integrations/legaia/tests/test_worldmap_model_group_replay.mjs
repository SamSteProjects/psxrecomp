import fs from 'node:fs';
import assert from 'node:assert/strict';
import {replayWorldVectors} from '../editor/worldmap-model-vector-replay.js';
const pairs=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),decode=s=>new Uint8Array(Buffer.from(s,'base64'));let refusals=0;
for(const row of pairs){const retail=decode(row.retail),base=decode(row.base),candidate=decode(row.candidate);assert.deepEqual(await replayWorldVectors(retail,base,row.binding),candidate);const group=b=>b.ledger.operations.find(o=>o.kind==='allocate_groups');
 for(const change of [b=>group(b).requests[0].group_id='foreign',b=>group(b).requests[0].donor_face_id='foreign',b=>group(b).requests[0].faces[0].face_id='foreign',b=>group(b).requests[0].faces[0].donor_face_id='foreign',b=>group(b).requests[0].faces[0].fields.vertices[0]=8192,b=>group(b).requests.push(structuredClone(group(b).requests[0])),b=>group(b).requests[0].extra=true,b=>group(b).extra=true,b=>group(b).input_sha256='0'.repeat(64),b=>group(b).proposed_sha256='0'.repeat(64),b=>b.ledger.schema_version='legaia.model-face-addition-ledger.v7',b=>b.asset_sha256='0'.repeat(64)]){const bad=structuredClone(row.binding);change(bad);await assert.rejects(replayWorldVectors(retail,base,bad));refusals++;}
}
assert.equal(pairs.length,27);console.log(`27 complete native group chains and ${refusals} altered group/donor/field/schema/hash refusals passed.`);
