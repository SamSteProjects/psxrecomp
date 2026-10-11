import {readFileSync,writeFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {qualifyScriptedCreationSource} from '../editor/worldmap-scripted-creation-state.js';
import {qualifyScriptedRemovalReview,scriptedRemovalIds} from '../editor/worldmap-scripted-removal-state.js';
import {qualifyProposedScriptedRemovalScene} from '../editor/worldmap-scripted-placement-scene.js';
const rows=JSON.parse(readFileSync(process.argv[2],'utf8')),held=JSON.stringify(rows);let refusals=0;
for(const row of rows){
 const o=row.options,q=await qualifyScriptedCreationSource(row.source,row.retail,o.manWitness,o.mapWitness,o),r=row.review;
 assert.deepEqual(await qualifyScriptedRemovalReview(r,q,r.placement_ids,r.cascade),r);
 const view=await qualifyProposedScriptedRemovalScene(row.retail,row.proposed,r,q,o);
 assert(view.entities.every(e=>!r.audit.removed_placement_ids.includes(e.authored_placement?.placement_id)));
 assert.deepEqual(scriptedRemovalIds(row.source.binding,r.placement_ids),r.audit.removed_placement_ids);
 for(const change of [v=>v.schema_version+='-forged',v=>v.placement_ids.pop(),v=>v.placement_ids.reverse(),v=>v.cascade=!v.cascade,v=>v.current_map_sha256='0'.repeat(64),v=>v.proposed_map_sha256='0'.repeat(64),v=>v.audit.removed_placements.pop(),v=>v.audit.removed_placement_ids.reverse(),v=>v.audit.removed_placements[0].script_id+='-forged',v=>v.audit.changed_bytes[0].after_byte^=1,v=>v.proposed_map_base64=v.proposed_map_base64.slice(4),v=>v.audit.scope='anything',v=>v.gameplay_verified=true,v=>v.extra=true]){
  const altered=structuredClone(r);change(altered);await assert.rejects(()=>qualifyScriptedRemovalReview(altered,q,r.placement_ids,r.cascade));refusals++;
 }
 for(const ids of [[],[...r.placement_ids,r.placement_ids[0]],['missing'],[...r.placement_ids].reverse()]){await assert.rejects(()=>qualifyScriptedRemovalReview(r,q,ids,r.cascade));refusals++;}
 for(const change of [v=>v.representation='current-scripted-placement-source',v=>v.scripted_proposal.review_key='0'.repeat(64),v=>v.scene_graph.entities.pop(),v=>v.placement_source.current_map_sha256='0'.repeat(64),v=>v.authored_entity_count++,v=>v.gameplay_verified=true]){
  const altered=structuredClone(row.proposed);change(altered);await assert.rejects(()=>qualifyProposedScriptedRemovalScene(row.retail,altered,r,q,o));refusals++;
 }
 console.log(row.name,'group removal Review and complete remaining scene qualify');
}
assert.equal(JSON.stringify(rows),held);const proof={cases:rows.length,refusals,inputs_unchanged:true,gameplay_verified:false};
if(process.argv[3])writeFileSync(process.argv[3],JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify(proof));
