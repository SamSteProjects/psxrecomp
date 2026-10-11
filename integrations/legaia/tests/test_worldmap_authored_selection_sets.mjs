import fs from 'node:fs';import assert from 'node:assert/strict';
import {qualifyAuthoredWorldSelectionReview} from '../editor/worldmap-authored-selection-state.js';
const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let refusals=0;
for(const row of rows){
 const held=JSON.stringify(row),source={metadata:row.source};
 assert.deepEqual(await qualifyAuthoredWorldSelectionReview(row.review,row.saved,source),row.saved.placement_ids);
 for(const mutate of [v=>v.read_only=false,v=>v.source_key='foreign',v=>v.selection.placement_ids.reverse(),v=>v.selection.bindings[v.selection.placement_ids[0]].record_index++,v=>v.review_key='0'.repeat(64),v=>v.extra=true]){
  const bad=structuredClone(row.review);mutate(bad);await assert.rejects(qualifyAuthoredWorldSelectionReview(bad,row.saved,source));refusals++;
 }
 const missing=structuredClone(source);missing.metadata.authored_allocations.shift();await assert.rejects(qualifyAuthoredWorldSelectionReview(row.review,row.saved,missing));refusals++;
 const forged=structuredClone(row.saved);forged.name+=' altered';const receipt=structuredClone(row.review);receipt.selection.name=forged.name;await assert.rejects(qualifyAuthoredWorldSelectionReview(receipt,forged,source));refusals++;
 assert.equal(JSON.stringify(row),held);
}
assert.equal(rows.length,6);console.log(`Six actual authored group receipts and ${refusals} altered/digest/ownership refusals passed.`);
