import {readFileSync,writeFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {qualifyScriptedCreationSource} from '../editor/worldmap-scripted-creation-state.js';
import {qualifyProposedScriptedTransformScene} from '../editor/worldmap-scripted-placement-scene.js';
const rows=JSON.parse(readFileSync(process.argv[2],'utf8')),held=JSON.stringify(rows);let refusals=0;
for(const row of rows){
 const o=row.options,q=await qualifyScriptedCreationSource(row.source,row.retail,o.manWitness,o.mapWitness,o);
 const view=await qualifyProposedScriptedTransformScene(row.retail,row.proposed,row.review,q,o);
 const id=`scene://${row.name}/worldmap/authored-placements/${row.review.placement_id.split('/').pop()}`,entity=view.entities.find(e=>e.entity_id===id);
 assert(entity);assert.equal(entity.placement_scope,'authored_scripted_seed');assert.equal(entity.preview_layer,'Proposed authored seeds');
 assert.deepEqual(entity.source_position,row.review.audit.after.native_seed.source_position);
 assert.equal(view.entities.length,row.proposed.scene_graph.entities.length);
 for(const change of [v=>v.representation='current-scripted-placement-source',v=>v.scripted_proposal.review_key='0'.repeat(64),v=>v.scripted_proposal.values.offset.x++,v=>v.scene_graph.entities.pop(),v=>v.placement_source.binding.operations.at(-1).proposed_map_sha256='0'.repeat(64),v=>v.scene_graph.entities.find(e=>e.entity_id===id).source_position.y++,v=>v.scene_graph.entities.find(e=>e.entity_id===id).entity_id+='-forged',v=>v.gameplay_verified=true]){
  const altered=structuredClone(row.proposed);change(altered);await assert.rejects(()=>qualifyProposedScriptedTransformScene(row.retail,altered,row.review,q,o));refusals++;
 }
 console.log(row.name,id,'proposed transform scene qualifies');
}
assert.equal(JSON.stringify(rows),held);
const proof={cases:rows.length,refusals,inputs_unchanged:true,gameplay_verified:false};
if(process.argv[3])writeFileSync(process.argv[3],JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify(proof));
