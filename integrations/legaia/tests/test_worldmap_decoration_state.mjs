import fs from 'node:fs';import assert from 'node:assert/strict';
import {qualifyWorldDecorationSource,qualifyWorldDecorationReview,worldDecorationDraft,worldDecorationDonorValues} from '../editor/worldmap-decoration-state.js';
import {qualifyProposedWorldPlacements} from '../editor/worldmap-current-placements.js';
const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let refusals=0;
for(const row of rows){
 const held=JSON.stringify(row),source=await qualifyWorldDecorationSource(row.source,row.current,row.options.path),request=row.requests[0];
 const values=worldDecorationDonorValues(source,request.donor_cell);assert.deepEqual(values,request.values);
 assert.deepEqual(worldDecorationDraft(source,request.donor_cell,request.target_cell,values,()=>request.placement_id.split('/').pop()),request);
 const review=await qualifyWorldDecorationReview(row.review,source,row.requests),view=await qualifyProposedWorldPlacements(row.retail,row.current,row.proposed,review,row.options);
 assert.equal(view.entities.length,row.current.scene_graph.entities.length+1);
 assert.equal(view.entities.at(-1).entity_id,`scene://${row.current.scene}/worldmap/authored-placements/${request.placement_id.split('/').pop()}`);
 assert.deepEqual(view.entities.at(-1).source_position,review.audit.allocations[0].native_seed.source_position);
 assert.equal(JSON.stringify(row),held);
 for(const mutate of [v=>v.project_path='foreign',v=>v.donors.pop(),v=>v.target_cells.pop(),v=>v.free_record_indices.pop(),v=>v.current_map_sha256='0'.repeat(64),v=>v.current_placements[0].source_position.y++,v=>v.binding=null,v=>v.extra=true]){
  const bad=structuredClone(row.source);mutate(bad);await assert.rejects(qualifyWorldDecorationSource(bad,row.current,row.options.path));refusals++;
 }
 for(const mutate of [v=>v.review_key='foreign',v=>v.requests[0].target_cell++,v=>v.audit.allocations[0].native_seed.source_position.y++,v=>v.proposed_map_sha256='0'.repeat(64),v=>v.binding.operations.at(-1).proposed_map_sha256='0'.repeat(64),v=>v.binding.operations.shift(),v=>v.before_binding=null,v=>v.build_ready=true,v=>v.extra=true]){
  const bad=structuredClone(row.review);mutate(bad);await assert.rejects(qualifyWorldDecorationReview(bad,source,row.requests));refusals++;
 }
 for(const mutate of [v=>v.allocation_proposal.review_key='0'.repeat(64),v=>v.placement_authoring.current_map_sha256='0'.repeat(64),v=>v.placement_authoring.authored_records={},v=>v.placement_authoring.allocation_binding.operations.shift(),v=>v.scene_graph.entities.at(-1).source_to_world[13]++,v=>v.scene_graph.assets[0].preview.vertices[0][0]++]){
  const bad=structuredClone(row.proposed);mutate(bad);await assert.rejects(qualifyProposedWorldPlacements(row.retail,row.current,bad,review,row.options));refusals++;
 }
 assert.throws(()=>worldDecorationDraft(source,request.donor_cell,request.donor_cell,values));
}
assert.equal(rows.length,3);console.log(`Three native authored-donor Source/Review/Proposed workflows and ${refusals} altered native/proposal refusals passed.`);
