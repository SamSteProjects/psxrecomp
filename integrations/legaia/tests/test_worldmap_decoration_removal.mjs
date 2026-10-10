import fs from 'node:fs';import assert from 'node:assert/strict';
import {qualifyWorldDecorationSource,qualifyWorldDecorationRemovalReview} from '../editor/worldmap-decoration-state.js';
import {qualifyProposedWorldPlacementRemoval} from '../editor/worldmap-current-placements.js';
const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let refusals=0;
for(const row of rows){
 const held=JSON.stringify(row),source=await qualifyWorldDecorationSource(row.source,row.current,row.options.path);
 const review=await qualifyWorldDecorationRemovalReview(row.review,source,row.placement_id);
 const view=await qualifyProposedWorldPlacementRemoval(row.retail,row.current,row.proposed,review,row.options);
 assert.equal(view.entities.length,row.current.scene_graph.entities.length-1);assert(!view.entities.some(e=>e.authored_placement?.placement_id===row.placement_id));
 for(const entity of view.entities)assert.deepEqual(entity.source_position,row.current.scene_graph.entities.find(e=>e.entity_id===entity.entity_id).source_position);
 if(row.phase==='last')assert.equal(review.binding,null);else assert(review.audit.rebased_donors.length);
 assert.equal(JSON.stringify(row),held);
 for(const mutate of [v=>v.placement_id='foreign',v=>v.before_binding.operations.pop(),v=>v.binding=null,v=>v.audit.removed.target_cell++,v=>v.audit.rebased_donors.push({placement_id:'foreign'}),v=>v.audit.remaining_allocations.push(v.audit.removed),v=>v.audit.changed_bytes.pop(),v=>v.proposed_map_sha256='0'.repeat(64),v=>v.build_ready=true,v=>v.extra=true]){
  const bad=structuredClone(row.review);mutate(bad);if(JSON.stringify(bad)===JSON.stringify(row.review))continue;await assert.rejects(qualifyWorldDecorationRemovalReview(bad,source,row.placement_id));refusals++;
 }
 for(const mutate of [v=>v.allocation_remove_proposal.placement_id='foreign',v=>v.placement_authoring.current_map_sha256='0'.repeat(64),v=>v.placement_authoring.authored_records={},v=>v.scene_graph.entities[1].source_to_world[13]++,v=>v.scene_graph.assets[0].preview.vertices[0][0]++]){
  const bad=structuredClone(row.proposed);mutate(bad);await assert.rejects(qualifyProposedWorldPlacementRemoval(row.retail,row.current,bad,review,row.options));refusals++;
 }
 const badReview=structuredClone(review),badScene=structuredClone(row.proposed);
 const other=row.current.placement_authoring.authored_allocations.find(a=>a.placement_id!==row.placement_id)?.placement_id??'foreign';
 badReview.placement_id=other;badScene.allocation_remove_proposal.placement_id=other;
 await assert.rejects(qualifyProposedWorldPlacementRemoval(row.retail,row.current,badScene,badReview,row.options));refusals++;
}
assert.equal(rows.length,6);console.log(`Six retained removal/last-owner workflows and ${refusals} altered Review/Proposed refusals passed.`);
