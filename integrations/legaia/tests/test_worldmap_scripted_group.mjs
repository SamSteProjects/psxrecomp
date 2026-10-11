import {readFileSync,writeFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {qualifyScriptedCreationSource} from '../editor/worldmap-scripted-creation-state.js';
import {qualifyScriptedGroupReview} from '../editor/worldmap-scripted-group-state.js';
import {qualifyProposedScriptedGroupScene} from '../editor/worldmap-scripted-placement-scene.js';
const rows=JSON.parse(readFileSync(process.argv[2],'utf8')),held=JSON.stringify(rows);let reviewRefusals=0,sceneRefusals=0;
for(const row of rows){
 const o=row.options,q=await qualifyScriptedCreationSource(row.source,row.retail,o.manWitness,o.mapWitness,o),r=row.review;
 assert.deepEqual(await qualifyScriptedGroupReview(r,q,[...r.entries].reverse()),r);
 const view=await qualifyProposedScriptedGroupScene(row.retail,row.proposed,r,q,o);
 for(const a of r.audit.after){const entity=view.entities.find(e=>e.authored_placement?.placement_id===a.placement_id);assert(entity);assert.deepEqual(entity.source_position,a.native_seed.source_position);}
 for(const change of [v=>v.schema_version+='-forged',v=>v.entries[0].values.offset.x++,v=>v.current_values[1].values.yaw_units++,v=>v.entries.reverse(),v=>v.before_binding.operations[0].requests[0].target_cell++,v=>v.binding.operations[0].proposed_map_sha256='0'.repeat(64),v=>v.current_map_sha256='0'.repeat(64),v=>v.proposed_map_sha256='0'.repeat(64),v=>v.audit.before.pop(),v=>v.audit.after[1].script_id+='-forged',v=>v.audit.authored_scripted_placements[0].native_seed.source_position.y++,v=>v.audit.changed_bytes[0].after_byte^=1,v=>v.proposed_map_base64=v.proposed_map_base64.slice(4),v=>v.audit.scope='authored-scripted-transform-only',v=>v.gameplay_verified=true,v=>v.extra=true]){
  const altered=structuredClone(r);change(altered);await assert.rejects(()=>qualifyScriptedGroupReview(altered,q,r.entries));reviewRefusals++;
 }
 for(const bad of [[],r.entries.slice(0,1),[...r.entries,r.entries[0]],Array(33).fill(r.entries[0]),[{...r.entries[0],placement_id:'missing'},r.entries[1]],[{...r.entries[0],extra:true},r.entries[1]],[{...r.entries[0],values:{offset:{x:true,y:0,z:0},yaw_units:0}},r.entries[1]]]){
  await assert.rejects(()=>qualifyScriptedGroupReview(r,q,bad));reviewRefusals++;
 }
 for(const change of [v=>v.representation='current-scripted-placement-source',v=>v.scripted_proposal.review_key='0'.repeat(64),v=>v.scripted_proposal.entries.pop(),v=>v.scene_graph.entities.pop(),v=>v.placement_source.current_map_sha256='0'.repeat(64),v=>v.authored_entity_count++,v=>v.scene_graph.entities[0].entity_id+='-forged',v=>v.gameplay_verified=true]){
  const altered=structuredClone(row.proposed);change(altered);await assert.rejects(()=>qualifyProposedScriptedGroupScene(row.retail,altered,r,q,o));sceneRefusals++;
 }
 console.log(row.name,'group Review and complete proposed scene qualify');
}
assert.equal(JSON.stringify(rows),held);const proof={cases:rows.length,review_refusals:reviewRefusals,scene_refusals:sceneRefusals,inputs_unchanged:true,gameplay_verified:false};
if(process.argv[3])writeFileSync(process.argv[3],JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify(proof));
