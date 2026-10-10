import fs from 'node:fs';import assert from 'node:assert/strict';
import {qualifyWorldTimRestore} from '../editor/worldmap-tim-replacement.js';
const out=process.argv[2],receipts=JSON.parse(fs.readFileSync(out+'/receipts.json')),expected=JSON.parse(fs.readFileSync(out+'/expected.json'));assert(receipts.length>=3);
for(const value of receipts){const request=structuredClone(value.request),record={source_record:{bpp:4,byte_length:expected[request.texture_id.split('/')[2]].byte_length}},options={record,request,path:value.project_path},held=structuredClone(value),result=qualifyWorldTimRestore(value,options);result.request.texture_id='foreign';assert.deepEqual(value,held);
 for(const mutate of [v=>v.project_path='foreign',v=>v.request.texture_id='foreign',v=>v.has_override=false,v=>v.content_changed=false,v=>v.candidate_tim_sha256='0'.repeat(64),v=>v.changed_palette_words=0,v=>v.changed_image_bytes=1,v=>v.changed_pixel_count=-1,v=>v.review_key='bad',v=>v.scope='all-textures',v=>v.project_changed=true,v=>v.extra=true]){const bad=structuredClone(value);mutate(bad);assert.throws(()=>qualifyWorldTimRestore(bad,options));}
}
console.log(`${receipts.length} native restoration receipts: detached metadata and twelve forged owner/source/count refusals each passed.`);
