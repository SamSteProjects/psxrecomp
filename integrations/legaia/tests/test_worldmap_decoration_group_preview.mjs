import fs from 'node:fs';import assert from 'node:assert/strict';
import {qualifyProposedWorldPlacementGroup} from '../editor/worldmap-current-placements.js';
const row=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const qualify=(proposed,review=row.review)=>qualifyProposedWorldPlacementGroup(row.retail,row.current,proposed,review,row.options);
const view=await qualify(row.proposed);assert.equal(view.entities.length,row.proposed.scene_graph.entities.length);let refusals=0;
for(const mutate of [v=>v.allocation_group_proposal.delta.x++,v=>v.placement_authoring.allocation_binding.operations[0].requests[0].target_cell++,
 v=>v.placement_authoring.authored_records={},v=>v.placement_authoring.exported_map_sha256='0'.repeat(64),
 v=>v.scene_graph.entities.find(e=>e.placement_scope==='authored_spawn_seed').source_position.x++,
 v=>v.scene_graph.assets.pop(),v=>v.model_authoring={},v=>v.texture_authoring={}]){
 const bad=structuredClone(row.proposed);mutate(bad);await assert.rejects(qualify(bad));refusals++;
}
for(const mutate of [v=>v.audit.placements.pop(),v=>v.audit.changed_bytes.pop(),v=>v.binding.operations[0].requests[0].values.offset.y++,v=>v.delta.y=true]){
 const bad=structuredClone(row.review);mutate(bad);await assert.rejects(qualify(row.proposed,bad));refusals++;
}
console.log(`Complete real group Proposed scene and ${refusals} altered scene/recipe/audit refusals passed.`);
