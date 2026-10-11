import {readFileSync,writeFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {qualifyScriptedCreationSource} from '../editor/worldmap-scripted-creation-state.js';
import {qualifyScriptedRemovalReview,scriptedRemovalIds} from '../editor/worldmap-scripted-removal-state.js';
import {qualifyProposedScriptedRemovalScene} from '../editor/worldmap-scripted-placement-scene.js';
const rows=JSON.parse(readFileSync(process.argv[2],'utf8')),held=JSON.stringify(rows);let sceneRefusals=0,reviewRefusals=0;
for(const row of rows){
 const o=row.options,q=await qualifyScriptedCreationSource(row.source,row.retail,o.manWitness,o.mapWitness,o),r=row.review;
 assert.deepEqual(scriptedRemovalIds(q.source.binding,r.placement_id),r.audit.removed_placement_ids);
 await qualifyScriptedRemovalReview(r,q,r.placement_id,r.cascade);const view=await qualifyProposedScriptedRemovalScene(row.retail,row.proposed,r,q,o);
 const removed=r.audit.removed_placement_ids.map(id=>`scene://${row.name}/worldmap/authored-placements/${id.split('/').pop()}`);
 assert(!view.entities.some(e=>removed.includes(e.entity_id)));assert.equal(view.entities.length,row.proposed.scene_graph.entities.length);
 for(const change of [v=>v.cascade=!v.cascade,v=>v.placement_id+='-forged',v=>v.before_binding.operations[0].requests[0].target_cell++,v=>v.current_map_sha256='0'.repeat(64),v=>v.proposed_map_sha256='0'.repeat(64),v=>v.audit.removed_placement_ids.pop(),v=>v.audit.removed_placements[0].native_seed.source_position.y++,v=>v.audit.changed_bytes[0].after_byte^=1,v=>v.audit.authored_scripted_placements.push(v.audit.removed_placements[0]),v=>v.proposed_map_base64=v.proposed_map_base64.slice(4),v=>v.gameplay_verified=true,v=>v.extra=true]){
  const altered=structuredClone(r);change(altered);await assert.rejects(()=>qualifyScriptedRemovalReview(altered,q,r.placement_id,r.cascade));reviewRefusals++;
 }
 for(const cascade of [null,0,1,'yes']){await assert.rejects(()=>qualifyScriptedRemovalReview(r,q,r.placement_id,cascade));reviewRefusals++;}
 if(r.audit.removed_placement_ids.length>1){await assert.rejects(()=>qualifyScriptedRemovalReview(r,q,r.placement_id,false));reviewRefusals++;}
 for(const change of [v=>v.representation='current-scripted-placement-source',v=>v.scripted_proposal.review_key='0'.repeat(64),v=>v.scripted_proposal.cascade=!v.scripted_proposal.cascade,v=>v.scene_graph.entities.pop(),v=>v.placement_source.current_map_sha256='0'.repeat(64),v=>v.authored_entity_count++,v=>v.scene_graph.entities[0].entity_id+='-forged',v=>v.gameplay_verified=true]){
  const altered=structuredClone(row.proposed);change(altered);await assert.rejects(()=>qualifyProposedScriptedRemovalScene(row.retail,altered,r,q,o));sceneRefusals++;
 }
 console.log(row.name,r.cascade,'removal Review and proposed scene qualify');
}
assert.equal(JSON.stringify(rows),held);const proof={cases:rows.length,review_refusals:reviewRefusals,scene_refusals:sceneRefusals,inputs_unchanged:true,gameplay_verified:false};
if(process.argv[3])writeFileSync(process.argv[3],JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify(proof));
