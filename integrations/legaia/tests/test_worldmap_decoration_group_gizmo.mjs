import assert from 'node:assert/strict';
import fs from 'node:fs';
import {worldDecorationGroupDisplay} from '../editor/worldmap-decoration-gizmo.js';
import {qualifyWorldDecorationSource} from '../editor/worldmap-decoration-state.js';
const displayed=report=>report.scene_graph.entities.map(e=>({...e,model_to_scene:Array.from({length:16},(_,i)=>e.source_to_world[(i%4)*4+Math.floor(i/4)]*(Math.floor(i/4)===1?-1:1))}));
const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let comparisons=0,refusals=0;
for(const row of rows){
  const source=await qualifyWorldDecorationSource(row.source,row.current,row.review.project_path),entities=displayed(row.current),after=displayed(row.proposed);
  const draft={ids:row.review.placement_ids,delta:row.review.delta,source},held=JSON.stringify([source,entities,draft]);
  const display=worldDecorationGroupDisplay(entities,draft);
  for(const id of draft.ids){
    const entity=entities.find(e=>e.authored_placement?.placement_id===id),proposed=after.find(e=>e.entity_id===entity.entity_id);
    assert.deepEqual(display.positions.get(entity.entity_id),{x:proposed.model_to_scene[3],y:proposed.model_to_scene[7],z:proposed.model_to_scene[11]});
    const matrix=display.transforms.get(entity.entity_id);assert(matrix);matrix.forEach((v,i)=>assert(Math.abs(v-proposed.model_to_scene[i])<1e-12));comparisons++;
  }
  const zero=worldDecorationGroupDisplay(entities,{...draft,delta:{x:0,y:0,z:0,yaw_units:0}});assert.equal(zero.positions.size,0);assert.equal(zero.transforms.size,0);
  for(const mutate of [d=>d.ids=[],d=>d.ids.push(d.ids[0]),d=>d.ids[0]='foreign',d=>d.delta.x=65535,d=>d.delta.y=NaN,d=>d.delta.z=.5,d=>d.delta.yaw_units=4096,d=>d.delta.extra=0,d=>d.source.metadata.binding.operations[0].requests[0].values.offset.x=32768]){
    const bad=structuredClone(draft);mutate(bad);assert.throws(()=>worldDecorationGroupDisplay(entities,bad));refusals++;
  }
  assert.throws(()=>worldDecorationGroupDisplay([...entities,entities.find(e=>e.authored_placement?.placement_id===draft.ids[0])],draft));refusals++;
  const foreign=structuredClone(entities);foreign.find(e=>e.authored_placement?.placement_id===draft.ids[0]).entity_id='scene://foreign/worldmap/authored-placements/'+draft.ids[0].split('/').pop();assert.throws(()=>worldDecorationGroupDisplay(foreign,draft));refusals++;
  const late=structuredClone(draft);late.source.metadata.binding.operations.flatMap(op=>op.requests).find(r=>r.placement_id===draft.ids.at(-1)).values.offset.z=32767;assert.throws(()=>worldDecorationGroupDisplay(entities,late));refusals++;
  assert.equal(JSON.stringify([source,entities,draft]),held);
}
assert.equal(rows.length,3);console.log(`${comparisons} actual group display/native Proposed matrix comparisons and ${refusals} owner/range refusals passed.`);
