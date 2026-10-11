import {readFileSync,writeFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {qualifyScriptedCreationSource} from '../editor/worldmap-scripted-creation-state.js';
import {qualifyScriptedModelReview} from '../editor/worldmap-scripted-model-state.js';
import {qualifyProposedScriptedModelScene} from '../editor/worldmap-scripted-placement-scene.js';
const rows=JSON.parse(readFileSync(process.argv[2],'utf8')),held=JSON.stringify(rows);let refusals=0;
for(const row of rows){
 const o=row.options,q=await qualifyScriptedCreationSource(row.source,row.retail,o.manWitness,o.mapWitness,o),r=row.review;
 assert.deepEqual(await qualifyScriptedModelReview(r,q,r.placement_ids,r.model_pool_index,row.current),r);
 const view=await qualifyProposedScriptedModelScene(row.retail,row.proposed,r,q,o);
 for(const a of r.audit.after){const e=view.entities.find(e=>e.authored_placement?.placement_id===a.placement_id);assert(e);assert.equal(e.model_pool_index,r.model_pool_index);assert.deepEqual(e.source_position,a.native_seed.source_position);}
 for(const change of [v=>v.schema_version+='-forged',v=>v.model_pool_index++,v=>v.asset_id+='-forged',v=>v.model_source_record.extra=true,v=>v.binding.operations[0].proposed_map_sha256='0'.repeat(64),v=>v.current_map_sha256='0'.repeat(64),v=>v.proposed_map_sha256='0'.repeat(64),v=>v.audit.before.pop(),v=>v.audit.after[0].script_id+='-forged',v=>v.audit.authored_scripted_placements[0].native_seed.source_position.y++,v=>v.audit.changed_bytes[0].after_byte^=1,v=>v.proposed_map_base64=v.proposed_map_base64.slice(4),v=>v.audit.scope='anything',v=>v.gameplay_verified=true,v=>v.extra=true]){
  const altered=structuredClone(r);change(altered);await assert.rejects(()=>qualifyScriptedModelReview(altered,q,r.placement_ids,r.model_pool_index,row.current));refusals++;
 }
 for(const ids of [[],[...r.placement_ids,r.placement_ids[0]],['missing']]){await assert.rejects(()=>qualifyScriptedModelReview(r,q,ids,r.model_pool_index,row.current));refusals++;}
 for(const change of [v=>v.representation='current-scripted-placement-source',v=>v.scripted_proposal.review_key='0'.repeat(64),v=>v.scene_graph.entities.pop(),v=>v.placement_source.current_map_sha256='0'.repeat(64),v=>v.authored_entity_count++,v=>v.gameplay_verified=true]){
  const altered=structuredClone(row.proposed);change(altered);await assert.rejects(()=>qualifyProposedScriptedModelScene(row.retail,altered,r,q,o));refusals++;
 }
 console.log(row.name,'model Review and complete proposed scene qualify');
}
assert.equal(JSON.stringify(rows),held);const proof={cases:rows.length,refusals,inputs_unchanged:true,gameplay_verified:false};
if(process.argv[3])writeFileSync(process.argv[3],JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify(proof));
