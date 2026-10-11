import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {qualifyWorldViewReview} from '../editor/worldmap-views.js';
const cases=JSON.parse(readFileSync(process.argv[2],'utf8'));let refusals=0;
for(const row of cases){
 const {review,saved,current}=row,held=structuredClone(row);
 assert.deepEqual(await qualifyWorldViewReview(review,saved,current),saved.display);
 for(const mutate of [s=>s.binding.authored_owner.script_id='foreign',s=>s.binding.authored_owner.shared_script=false,s=>s.binding.authored_owner.placement_kind='decoration',s=>s.binding.authored_owner.native_entity_id='foreign',s=>s.binding.authored_owner.record_index++,s=>s.binding.authored_owner.target_cell++,s=>s.binding.authored_owner.model_pool_index++,s=>s.binding.authored_owner.extra=true,s=>s.binding.entity_sha256='0'.repeat(64),s=>s.binding.asset_source_sha256='0'.repeat(64),s=>s.display.layer='retail',s=>s.display.scope='foreign']){
  const bad=structuredClone(saved);mutate(bad);const {review_key,...entry}=bad;await assert.rejects(()=>qualifyWorldViewReview({...review,view:entry},bad,current));refusals++;
 }
 const gone=structuredClone(current);gone.scene_graph.entities=gone.scene_graph.entities.filter(e=>e.entity_id!==saved.display.selected_id);await assert.rejects(()=>qualifyWorldViewReview(review,saved,gone));refusals++;
 const proposed=structuredClone(current);proposed.representation='proposed-scripted-placement-source';await assert.rejects(()=>qualifyWorldViewReview(review,saved,proposed));refusals++;
 assert.deepEqual(row,held);
}
const proof={cases:cases.length,refusals,inputs_unchanged:true,gameplay_verified:false};if(process.argv[3])writeFileSync(process.argv[3],JSON.stringify(proof,null,2)+'\n');console.log(proof);
