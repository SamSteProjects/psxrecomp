import fs from 'node:fs';import assert from 'node:assert/strict';
import {qualifyProposedWorldPlacementCell} from '../editor/worldmap-current-placements.js';
const row=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const held=JSON.stringify(row),view=await qualifyProposedWorldPlacementCell(row.retail,row.current,row.proposed,row.review,row.options);
assert.equal(view.entities.length,row.current.scene_graph.entities.length);
const id=`scene://${row.current.scene}/worldmap/authored-placements/${row.placement_id.split('/').pop()}`;
assert.equal(view.entities.find(e=>e.entity_id===id).source_cell,row.target_cell);
assert.equal(JSON.stringify(row),held);let refusals=0;
for(const mutate of [v=>v.allocation_cell_proposal.target_cell++,v=>v.placement_authoring.authored_records={},
    v=>v.placement_authoring.current_map_sha256='0'.repeat(64),v=>v.scene_graph.entities[1].source_to_world[13]++,
    v=>v.scene_graph.assets[0].preview.vertices[0][0]++,v=>v.allocation_cell_proposal.review_key='0'.repeat(64)]){
  const bad=structuredClone(row.proposed);mutate(bad);
  await assert.rejects(qualifyProposedWorldPlacementCell(row.retail,row.current,bad,row.review,row.options));refusals++;
}
const badReview=structuredClone(row.review),badScene=structuredClone(row.proposed);
badReview.binding.operations[0].requests[0].values.offset.x++;
badScene.placement_authoring.allocation_binding=structuredClone(badReview.binding);
await assert.rejects(qualifyProposedWorldPlacementCell(row.retail,row.current,badScene,badReview,row.options));refusals++;
console.log(`Complete coauthored cell preview and ${refusals} altered Proposed/recipe refusals passed.`);
