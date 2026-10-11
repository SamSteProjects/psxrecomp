import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {qualifyScriptedCreationSource} from '../editor/worldmap-scripted-creation-state.js';
import {qualifyScriptedTransformReview} from '../editor/worldmap-scripted-transform-state.js';
const cases=JSON.parse(readFileSync(process.argv[2],'utf8'));let refusals=0;
for(const row of cases){
 const held=structuredClone(row),q=await qualifyScriptedCreationSource(row.source,row.retail,row.manWitness,row.mapWitness,row.options);
 assert.deepEqual(await qualifyScriptedTransformReview(row.review,q,row.placement_id,row.values),row.review);
 for(const mutate of [v=>v.placement_id='foreign',v=>v.source_key='0'.repeat(64),v=>v.current_man_sha256='0'.repeat(64),v=>v.values.offset.x++,v=>v.current_values.yaw_units++,v=>v.binding.operations[0].requests[0].record_index++,v=>v.binding.operations.at(-1).proposed_map_sha256='0'.repeat(64),v=>v.audit.after.script_id='foreign',v=>v.audit.after.native_seed.source_position.x++,v=>v.audit.changed_bytes.pop(),v=>v.proposed_map_sha256='0'.repeat(64),v=>v.project_changed=true,v=>v.gameplay_verified=true,v=>v.extra=true]){
  const bad=structuredClone(row.review);mutate(bad);await assert.rejects(()=>qualifyScriptedTransformReview(bad,q,row.placement_id,row.values));refusals++;
 }
 assert.deepEqual(row,held);console.log(row.scene,row.placement_id,'independent retained transform replay passes');
}
const proof={cases:cases.length,refusals,inputs_unchanged:true,gameplay_verified:false};if(process.argv[3])writeFileSync(process.argv[3],JSON.stringify(proof,null,2)+'\n');console.log(proof);
