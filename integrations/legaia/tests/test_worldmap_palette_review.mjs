import fs from 'node:fs';import assert from 'node:assert/strict';
import {qualifyWorldPaletteReview} from '../editor/worldmap-tim-palette.js';
const receipts=JSON.parse(fs.readFileSync(process.argv[2]));assert(receipts.length>=3);
for(const value of receipts){const held=structuredClone(value),request=structuredClone(value.request),result=qualifyWorldPaletteReview(value,request,value.project_path);result.request.word^=1;assert.deepEqual(value,held);
 for(const mutate of [v=>v.project_path='foreign',v=>v.request.word^=1,v=>v.current_word=-1,v=>v.retail_word=65536,v=>v.changed=!v.changed,v=>v.candidate_tim_sha256=v.request.effective_sha256,v=>v.review_key='bad',v=>v.project_changed=true,v=>v.scope='layout-change',v=>v.extra=true]){const bad=structuredClone(value);mutate(bad);assert.throws(()=>qualifyWorldPaletteReview(bad,request,value.project_path));}
}
console.log(`${receipts.length} native palette receipts: detached Review values and ten forged-response refusals each passed.`);
