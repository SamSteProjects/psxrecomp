import fs from 'node:fs';import assert from 'node:assert/strict';
import {qualifyWorldTimSource} from '../editor/worldmap-tim-replacement.js';
const receipts=JSON.parse(fs.readFileSync(process.argv[2]));assert.equal(receipts.length,6);
for(const value of receipts){const request=structuredClone(value.request),record={source_record:{byte_length:value.byte_length}},options={record,path:value.project_path,request},held=structuredClone(value),result=await qualifyWorldTimSource(value,options);result.metadata.request.layer='foreign';result.bytes[0]^=1;assert.deepEqual(value,held);
 for(const mutate of [v=>v.project_path='foreign',v=>v.request.layer='foreign',v=>v.tim_sha256='0'.repeat(64),v=>v.byte_length++,v=>v.tim_base64='bad',v=>v.read_only=false,v=>v.project_changed=true,v=>v.gameplay_verified=true,v=>v.extra=0]){const bad=structuredClone(value);mutate(bad);await assert.rejects(()=>qualifyWorldTimSource(bad,options));}
}
console.log('Six native TIM source receipts: detached metadata/bytes, exact file hashes and nine forged-response refusals each passed.');
