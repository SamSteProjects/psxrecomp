import fs from 'node:fs';
import assert from 'node:assert/strict';
import {qualifyWorldDecorationSource, qualifyWorldDecorationGroupReview, transformWorldDecorationGroup} from '../editor/worldmap-decoration-state.js';
import {worldDecorationGroupDisplay} from '../editor/worldmap-decoration-gizmo.js';
const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const displayed=report=>report.scene_graph.entities.map(e=>({...e,model_to_scene:Array.from({length:16},(_,i)=>e.source_to_world[(i%4)*4+Math.floor(i/4)]*(Math.floor(i/4)===1?-1:1))}));
let refusals=0;
for(const row of rows){
  const held=JSON.stringify(row),source=await qualifyWorldDecorationSource(row.source,row.current,row.review.project_path);
  const {placement_ids:ids,delta}=row.review;
  await qualifyWorldDecorationGroupReview(row.review,source,ids,delta);
  const entities=displayed(row.current),after=displayed(row.proposed),draft={ids,delta,source};
  const display=worldDecorationGroupDisplay(entities,draft);
  for(const id of ids){
    const e=entities.find(e=>e.authored_placement?.placement_id===id),expected=after.find(p=>p.entity_id===e.entity_id);
    const matrix=display.transforms.get(e.entity_id);assert(matrix);
    matrix.forEach((n,i)=>assert(Math.abs(n-expected.model_to_scene[i])<1e-12));
  }
  const pivot=after.find(e=>e.authored_placement?.placement_id===delta.orbit_pivot);
  assert.deepEqual(display.pivot,{x:pivot.model_to_scene[3],y:pivot.model_to_scene[7],z:pivot.model_to_scene[11]});
  const zero=worldDecorationGroupDisplay(entities,{...draft,delta:{...delta,x:0,y:0,z:0,yaw_units:0}});
  assert.equal(zero.positions.size,0);assert.equal(zero.transforms.size,0);assert(zero.pivot);
  for(const angle of [1,128,512,1024,2048,3072,-1024]){
    const next={...delta,yaw_units:angle},transformed=await transformWorldDecorationGroup(source,ids,next);
    const expected=source.bytes.slice(),words=new DataView(expected.buffer),anchor=source.metadata.authored_allocations.find(a=>a.placement_id===next.orbit_pivot).native_seed.source_position;
    for(const id of ids){
      const allocation=source.metadata.authored_allocations.find(a=>a.placement_id===id),p=allocation.native_seed.source_position,at=allocation.record_index*32,a=angle*Math.PI/2048;
      const x=Math.floor(anchor.x+Math.cos(a)*(p.x-anchor.x)+Math.sin(a)*(p.z-anchor.z)+.5)+next.x;
      const z=Math.floor(anchor.z-Math.sin(a)*(p.x-anchor.x)+Math.cos(a)*(p.z-anchor.z)+.5)-next.z;
      words.setInt16(at,x-(allocation.target_cell%128)*128-64,true);words.setInt16(at+2,words.getInt16(at+2,true)+next.y,true);
      words.setInt16(at+4,Math.floor(allocation.target_cell/128)*128+64-z,true);
      const yaw=words.getUint16(at+10,true);words.setUint16(at+10,(yaw&0xf000)|(((yaw&4095)+angle+4096)%4096),true);
    }
    assert.deepEqual(transformed.bytes,expected);
  }
  for(const mutate of [r=>r.schema_version='legaia.worldmap-decoration-group-review.v1',r=>r.delta.orbit_pivot=ids[1],r=>r.audit.placements[0].values.offset.x++,r=>r.binding.operations[0].requests[0].target_cell++,r=>r.proposed_map_sha256='0'.repeat(64),r=>r.audit.changed_bytes.pop(),r=>r.gameplay_verified=true]){
    const bad=structuredClone(row.review);mutate(bad);await assert.rejects(qualifyWorldDecorationGroupReview(bad,source,ids,delta));refusals++;
  }
  for(const bad of [{...delta,orbit_pivot:'foreign'},{...delta,yaw_units:0},{...delta,yaw_units:true},{...delta,x:65535},{...delta,extra:0}]){
    await assert.rejects(transformWorldDecorationGroup(source,ids,bad));refusals++;
  }
  const mismatched=structuredClone(source),record=row.review.audit.placements[0].before.record_index;
  mismatched.bytes[record*32]^=1;
  await assert.rejects(transformWorldDecorationGroup(mismatched,ids,delta));refusals++;
  assert.equal(JSON.stringify(row),held);
}
assert.equal(rows.length,3);
console.log(`Three complete orbit receipts, 21 literal signed/quantized rotations, six displayed native matrices and ${refusals} altered/domain refusals passed.`);
