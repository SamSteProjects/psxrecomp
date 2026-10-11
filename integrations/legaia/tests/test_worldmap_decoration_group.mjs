import fs from 'node:fs';import assert from 'node:assert/strict';
import {qualifyWorldDecorationSource,qualifyWorldDecorationGroupReview,transformWorldDecorationGroup} from '../editor/worldmap-decoration-state.js';
const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let refusals=0;
for(const row of rows){
 const held=JSON.stringify(row),source=await qualifyWorldDecorationSource(row.source,row.current,row.review.project_path);
 const {placement_ids:ids,delta}=row.review;
 await qualifyWorldDecorationGroupReview(row.review,source,ids,delta);
 for(const mutate of [v=>v.placement_ids.reverse(),v=>v.delta.x++,v=>v.source_key='foreign',v=>v.before_binding.operations.pop(),
   v=>v.binding.operations[0].requests[0].values.offset.x++,v=>v.audit.placements.pop(),v=>v.audit.placements[0].after.native_seed.source_position.y++,
   v=>v.audit.changed_bytes.pop(),v=>v.proposed_map_sha256='0'.repeat(64),v=>v.build_ready=true,v=>v.extra=true]){
  const bad=structuredClone(row.review);mutate(bad);await assert.rejects(qualifyWorldDecorationGroupReview(bad,source,ids,delta));refusals++;
 }
 for(const [badIds,badDelta] of [[[],delta],[[ids[0],ids[0]],delta],[ids,{...delta,x:true}],[ids,{...delta,y:65536}],[ids,{...delta,yaw_units:4096}],[ids,{x:0,y:0,z:0,yaw_units:0}],[ids,{...delta,x:65535}]]){
  await assert.rejects(transformWorldDecorationGroup(source,badIds,badDelta));refusals++;
 }
 assert.equal(JSON.stringify(row),held);
}
assert.equal(rows.length,3);console.log(`Three complete native group receipts and ${refusals} altered/domain refusals passed.`);
