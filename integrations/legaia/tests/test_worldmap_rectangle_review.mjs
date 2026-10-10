import fs from 'node:fs';import assert from 'node:assert/strict';
import {qualifyWorldRectangleReview} from '../editor/worldmap-tim-palette.js';
const receipts=JSON.parse(fs.readFileSync(process.argv[2]));assert(receipts.length>=3);
for(const value of receipts){const request=structuredClone(value.request),held=structuredClone(value),result=qualifyWorldRectangleReview(value,request,value.project_path);result.request.x++;assert.deepEqual(value,held);
 for(const mutate of [v=>v.project_path='foreign',v=>v.request.x++,v=>v.bpp=3,v=>v.changed_pixel_count=-1,v=>v.changed_pixel_count=v.request.width*v.request.height+1,v=>v.changed=!v.changed,v=>v.candidate_tim_sha256=v.request.effective_sha256,v=>v.review_key='bad',v=>v.project_changed=true,v=>v.scope='palette-write',v=>v.extra=true]){const bad=structuredClone(value);mutate(bad);assert.throws(()=>qualifyWorldRectangleReview(bad,request,value.project_path));}
}
console.log(`${receipts.length} native rectangle receipts: detached Review and eleven forged-response refusals each passed.`);
