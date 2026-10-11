import fs from 'node:fs';import assert from 'node:assert/strict';
import {qualifyWorldDecorationSource,qualifyWorldDecorationModelReview} from '../editor/worldmap-decoration-state.js';
import {replayWorldPlacementAllocations,composeWorldPlacementTransforms,equalWorldPlacementBytes} from '../editor/worldmap-placement-replay.js';
const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let refusals=0;
for(const row of rows){
 const held=JSON.stringify(row),source=await qualifyWorldDecorationSource(row.source,row.current,row.review.project_path);
 const review=await qualifyWorldDecorationModelReview(row.review,source,row.placement_id,row.model_pool_index,row.current);
 const replayed=await replayWorldPlacementAllocations(source.retailBytes,source.metadata.floor_lut,source.metadata.scene,review.binding,source.metadata.source_record);
 const bytes=await composeWorldPlacementTransforms(source.retailBytes,replayed.bytes,source.metadata.floor_lut,source.metadata.scene,source.authoredRecords);
 assert(equalWorldPlacementBytes(bytes,Uint8Array.from(atob(row.after.placement_authoring.current_map_base64),c=>c.charCodeAt(0))));
 assert.equal(review.audit.before.placement_id,review.audit.after.placement_id);assert.equal(review.audit.before.target_cell,review.audit.after.target_cell);
 assert.equal(review.audit.after.model_pool_index,row.model_pool_index);assert(review.audit.retained_child_models.length);
 const downgraded=structuredClone(review.binding);downgraded.schema_version='legaia.worldmap-placement-allocation-ledger.v1';
 await assert.rejects(replayWorldPlacementAllocations(source.retailBytes,source.metadata.floor_lut,source.metadata.scene,downgraded,source.metadata.source_record));refusals++;
 for(const mutate of [v=>v.placement_id='foreign',v=>v.model_pool_index++,v=>v.asset_id='foreign',v=>v.model_source_record={},
     v=>v.before_binding.operations.pop(),v=>v.binding.operations[0].requests[0].values.offset.x++,
     v=>v.audit.retained_child_models.pop(),v=>v.audit.after.native_seed.source_position.y++,v=>v.audit.changed_bytes.pop(),
     v=>v.proposed_map_sha256='0'.repeat(64),v=>v.build_ready=true,v=>v.extra=true]){
  const bad=structuredClone(review);mutate(bad);await assert.rejects(qualifyWorldDecorationModelReview(bad,source,row.placement_id,row.model_pool_index,row.current));refusals++;
 }
 assert.equal(JSON.stringify(row),held);
}
assert.equal(rows.length,3);console.log(`Three complete native model assignments and ${refusals} altered receipt/version refusals passed.`);
