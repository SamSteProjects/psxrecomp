import fs from 'node:fs';
import assert from 'node:assert/strict';
import {qualifyWorldDecorationSource,qualifyWorldDecorationCellReview} from '../editor/worldmap-decoration-state.js';
const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let refusals=0;
for(const row of rows){
  const held=JSON.stringify(row),source=await qualifyWorldDecorationSource(row.source,row.current,row.review.project_path);
  const review=await qualifyWorldDecorationCellReview(row.review,source,row.placement_id,row.target_cell);
  assert.equal(review.audit.before.placement_id,review.audit.after.placement_id);
  assert.equal(review.audit.before.record_index,review.audit.after.record_index);
  assert.equal(review.audit.after.target_cell,row.target_cell);
  assert(review.audit.rebased_donors.length);
  assert.equal(JSON.stringify(row),held);
  for(const mutate of [v=>v.placement_id='foreign',v=>v.target_cell++,v=>v.source_key='0'.repeat(64),
      v=>v.before_binding.operations.pop(),v=>v.binding.operations[0].requests[0].values.offset.x++,
      v=>v.audit.before.record_index++,v=>v.audit.after.native_seed.source_position.y++,
      v=>v.audit.rebased_donors.pop(),v=>v.audit.changed_bytes.pop(),v=>v.proposed_map_sha256='0'.repeat(64),
      v=>v.build_ready=true,v=>v.extra=true]){
    const bad=structuredClone(row.review);mutate(bad);
    await assert.rejects(qualifyWorldDecorationCellReview(bad,source,row.placement_id,row.target_cell));refusals++;
  }
}
assert.equal(rows.length,3);
console.log(`Three complete native cell Reviews and ${refusals} altered receipt refusals passed.`);
