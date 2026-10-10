import fs from 'node:fs';import assert from 'node:assert/strict';
import {qualifyWorldDecorationSource,qualifyWorldDecorationTransformReview} from '../editor/worldmap-decoration-state.js';
import {qualifyProposedWorldPlacementEdit} from '../editor/worldmap-current-placements.js';
const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let refusals=0;
for(const row of rows){
 const held=JSON.stringify(row),source=await qualifyWorldDecorationSource(row.source,row.current,row.options.path);
 const review=await qualifyWorldDecorationTransformReview(row.review,source,row.placement_id,row.values);
 const view=await qualifyProposedWorldPlacementEdit(row.retail,row.current,row.proposed,review,row.options);
 assert.equal(view.entities.length,row.current.scene_graph.entities.length);
 const edited=view.entities.find(e=>e.authored_placement?.placement_id===row.placement_id);assert.deepEqual(edited.source_position,review.audit.after.native_seed.source_position);
 for(const entity of row.current.scene_graph.entities)if(entity.entity_id!==edited.entity_id)assert.deepEqual(view.entities.find(e=>e.entity_id===entity.entity_id).source_position,entity.source_position);
 assert.equal(JSON.stringify(row),held);
 for(const mutate of [v=>v.placement_id='foreign',v=>v.values.offset.x++,v=>v.current_values.offset.y++,v=>v.before_binding.operations.pop(),v=>v.binding.operations[0].requests[0].target_cell++,v=>v.binding.operations.at(-1).requests[0].values.offset.z++,v=>v.audit.changed_bytes.pop(),v=>v.audit.after.native_seed.source_position.y++,v=>v.proposed_map_sha256='0'.repeat(64),v=>v.build_ready=true,v=>v.extra=true]){
  const bad=structuredClone(row.review);mutate(bad);await assert.rejects(qualifyWorldDecorationTransformReview(bad,source,row.placement_id,row.values));refusals++;
 }
 for(const mutate of [v=>v.allocation_edit_proposal.placement_id='foreign',v=>v.allocation_edit_proposal.values.yaw_units++,v=>v.placement_authoring.current_map_sha256='0'.repeat(64),v=>v.placement_authoring.allocation_binding.operations.at(-1).requests[0].target_cell++,v=>v.scene_graph.entities.find(e=>e.placement_scope==='authored_spawn_seed').source_to_world[13]++]){
  const bad=structuredClone(row.proposed);mutate(bad);await assert.rejects(qualifyProposedWorldPlacementEdit(row.retail,row.current,bad,review,row.options));refusals++;
 }
}
assert.equal(rows.length,3);console.log(`Three retained native transform workflows and ${refusals} altered Review/Proposed refusals passed.`);
