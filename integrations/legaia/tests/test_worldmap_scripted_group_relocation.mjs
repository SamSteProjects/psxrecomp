import {readFileSync,writeFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {qualifyScriptedCreationSource} from '../editor/worldmap-scripted-creation-state.js';
import {qualifyScriptedGroupRelocationReview} from '../editor/worldmap-scripted-group-relocation-state.js';
import {qualifyProposedScriptedRelocationScene} from '../editor/worldmap-scripted-placement-scene.js';
const rows=JSON.parse(readFileSync(process.argv[2],'utf8')),held=JSON.stringify(rows);let refusals=0;
for(const row of rows){
 const o=row.options,q=await qualifyScriptedCreationSource(row.source,row.retail,o.manWitness,o.mapWitness,o),r=row.review;
 assert.deepEqual(await qualifyScriptedGroupRelocationReview(r,q,r.placement_ids,r.delta),r);
 const view=await qualifyProposedScriptedRelocationScene(row.retail,row.proposed,r,q,o);
 for(const a of r.audit.after){const e=view.entities.find(e=>e.authored_placement?.placement_id===a.placement_id);assert(e);assert.deepEqual(e.authored_placement,a);}
 for(const change of [v=>v.schema_version+='-forged',v=>v.placement_ids.pop(),v=>v.placement_ids.reverse(),v=>v.delta.col++,v=>v.current_map_sha256='0'.repeat(64),v=>v.proposed_map_sha256='0'.repeat(64),v=>v.audit.before.pop(),v=>v.audit.after.reverse(),v=>v.audit.after[0].script_id+='-forged',v=>v.audit.after[0].anchor_cell++,v=>v.audit.changed_bytes[0].after_byte^=1,v=>v.proposed_map_base64=v.proposed_map_base64.slice(4),v=>v.audit.scope='anything',v=>v.gameplay_verified=true,v=>v.extra=true,v=>v.binding.operations[0].requests[0].target_cell++]){
  const altered=structuredClone(r);change(altered);await assert.rejects(()=>qualifyScriptedGroupRelocationReview(altered,q,r.placement_ids,r.delta));refusals++;
 }
 for(const ids of [[],[r.placement_ids[0]],[...r.placement_ids,r.placement_ids[0]],['missing','missing2'],[...r.placement_ids].reverse()]){await assert.rejects(()=>qualifyScriptedGroupRelocationReview(r,q,ids,r.delta));refusals++;}
 for(const delta of [{col:true,row:0},{col:128,row:0},{col:0,row:0,extra:true},{col:-127,row:-127}]){await assert.rejects(()=>qualifyScriptedGroupRelocationReview(r,q,r.placement_ids,delta));refusals++;}
 for(const change of [v=>v.representation='current-scripted-placement-source',v=>v.scripted_proposal.review_key='0'.repeat(64),v=>v.scene_graph.entities.pop(),v=>v.placement_source.current_map_sha256='0'.repeat(64),v=>v.authored_entity_count++,v=>v.gameplay_verified=true]){
  const altered=structuredClone(row.proposed);change(altered);await assert.rejects(()=>qualifyProposedScriptedRelocationScene(row.retail,altered,r,q,o));refusals++;
 }
 console.log(row.name,'group relocation Review and complete proposed scene qualify');
}
assert.equal(JSON.stringify(rows),held);const proof={cases:rows.length,refusals,inputs_unchanged:true,gameplay_verified:false};
if(process.argv[3])writeFileSync(process.argv[3],JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify(proof));
