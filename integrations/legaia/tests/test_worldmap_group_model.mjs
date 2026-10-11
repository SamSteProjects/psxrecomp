import fs from 'node:fs';
import assert from 'node:assert/strict';
import {qualifyWorldDecorationSource, qualifyWorldDecorationModelReview, reassignWorldDecorationModel} from '../editor/worldmap-decoration-state.js';
const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let refusals=0;
for(const row of rows){
  const held=JSON.stringify(row),ids=row.review.placement_ids,model=row.review.model_pool_index;
  const source=await qualifyWorldDecorationSource(row.source,row.current,row.review.project_path);
  const review=await qualifyWorldDecorationModelReview(row.review,source,ids,model,row.current);
  const replay=await reassignWorldDecorationModel(source,ids,model);
  assert.deepEqual(Buffer.from(replay.bytes),Buffer.from(row.after.placement_authoring.current_map_base64,'base64'));
  assert(review.audit.after.every(a=>a.model_pool_index===model));
  for(let i=0;i<ids.length;i++){
    const before=review.audit.before[i],after=review.audit.after[i];
    assert.equal(after.placement_id,before.placement_id);
    assert.equal(after.target_cell,before.target_cell);assert.equal(after.record_index,before.record_index);
    assert.deepEqual(after.native_seed.source_position,before.native_seed.source_position);
    assert.deepEqual(after.native_seed.source_to_world,before.native_seed.source_to_world);
  }
  for(const mutate of [v=>v.placement_ids.reverse(),v=>v.placement_ids.push(v.placement_ids[0]),v=>v.placement_ids[0]='foreign',
    v=>v.model_pool_index++,v=>v.asset_id='foreign',v=>v.model_source_record={},v=>v.audit.after[0].native_seed.source_position.y++,
    v=>v.audit.before.reverse(),v=>v.audit.changed_bytes.pop(),v=>v.binding.operations[0].requests[0].values.offset.x++,
    v=>v.proposed_map_sha256='0'.repeat(64),v=>v.audit.scope='authored-decoration-model-only',v=>v.build_ready=true,
    v=>v.audit.retained_child_models.push({placement_id:'foreign',model_pool_index:1})]){
    const bad=structuredClone(review);mutate(bad);await assert.rejects(qualifyWorldDecorationModelReview(bad,source,ids,model,row.current));refusals++;
  }
  for(const bad of [[],ids.slice().reverse(),[ids[0],ids[0]],['foreign'],[true]]){
    await assert.rejects(reassignWorldDecorationModel(source,bad,model));refusals++;
  }
  assert.equal(JSON.stringify(row),held);
}
assert.equal(rows.length,3);console.log(`Three literal native group model replays and ${refusals} altered/domain refusals pass.`);
if(process.argv[3]){
  const chains=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
  for(const row of chains){
    const source={metadata:row.metadata,retailBytes:new Uint8Array(Buffer.from(row.retail,'base64')),bytes:new Uint8Array(Buffer.from(row.current,'base64')),authoredRecords:{}};
    const result=await qualifyWorldDecorationModelReview(row.review,source,row.review.placement_ids,row.review.model_pool_index,row.scene);
    assert.deepEqual(result.audit.retained_child_models,row.review.audit.retained_child_models);
    assert.equal(result.audit.retained_child_models.length,1);
  }
  assert.equal(chains.length,2);console.log('Both ledger versions preserve an unselected grandchild model in independent group replay.');
}
