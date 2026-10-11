import {readFileSync,writeFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {qualifyScriptedCreationSource} from '../editor/worldmap-scripted-creation-state.js';
import {qualifyScriptedRelocationReview} from '../editor/worldmap-scripted-relocation-state.js';
import {qualifyProposedScriptedRelocationScene} from '../editor/worldmap-scripted-placement-scene.js';
const rows=JSON.parse(readFileSync(process.argv[2],'utf8')),held=JSON.stringify(rows);let sceneRefusals=0,reviewRefusals=0;
for(const row of rows){
 const o=row.options,q=await qualifyScriptedCreationSource(row.source,row.retail,o.manWitness,o.mapWitness,o),r=row.review;
 await qualifyScriptedRelocationReview(r,q,r.placement_id,r.target_cell);
 const view=await qualifyProposedScriptedRelocationScene(row.retail,row.proposed,r,q,o);
 const id=`scene://${row.name}/worldmap/authored-placements/${r.placement_id.split('/').pop()}`,entity=view.entities.find(e=>e.entity_id===id);
 assert(entity);assert.equal(entity.placement_scope,'authored_scripted_seed');assert.equal(entity.preview_layer,'Proposed authored seeds');
 assert.deepEqual(entity.source_position,r.audit.after.native_seed.source_position);assert.equal(entity.source_cell,r.target_cell);assert.equal(view.entities.length,row.proposed.scene_graph.entities.length);
 for(const change of [v=>v.target_cell++,v=>v.placement_id+='-forged',v=>v.binding.operations[0].requests[0].target_cell++,v=>v.current_map_sha256='0'.repeat(64),v=>v.proposed_map_sha256='0'.repeat(64),v=>v.audit.after.anchor_cell++,v=>v.audit.dependent_donor_placements.push('placement://forged'),v=>v.audit.changed_bytes[0].after_byte^=1,v=>v.audit.after.native_seed.source_position.y++,v=>v.proposed_map_base64=v.proposed_map_base64.slice(4),v=>v.gameplay_verified=true,v=>v.extra=true]){
  const altered=structuredClone(r);change(altered);await assert.rejects(()=>qualifyScriptedRelocationReview(altered,q,r.placement_id,r.target_cell));reviewRefusals++;
 }
 for(const target of [true,-1,16384,0.5]){await assert.rejects(()=>qualifyScriptedRelocationReview(r,q,r.placement_id,target));reviewRefusals++;}
 for(const change of [v=>v.representation='current-scripted-placement-source',v=>v.scripted_proposal.review_key='0'.repeat(64),v=>v.scripted_proposal.target_cell++,v=>v.scene_graph.entities.pop(),v=>v.placement_source.binding.operations.at(-1).proposed_map_sha256='0'.repeat(64),v=>v.scene_graph.entities.find(e=>e.entity_id===id).source_position.y++,v=>v.scene_graph.entities.find(e=>e.entity_id===id).entity_id+='-forged',v=>v.gameplay_verified=true]){
  const altered=structuredClone(row.proposed);change(altered);await assert.rejects(()=>qualifyProposedScriptedRelocationScene(row.retail,altered,r,q,o));sceneRefusals++;
 }
 console.log(row.name,id,'relocation Review and proposed scene qualify');
}
assert.equal(JSON.stringify(rows),held);
const proof={cases:rows.length,review_refusals:reviewRefusals,scene_refusals:sceneRefusals,inputs_unchanged:true,gameplay_verified:false};
if(process.argv[3])writeFileSync(process.argv[3],JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify(proof));
