import assert from 'node:assert/strict';import fs from 'node:fs';
import {qualifyWorldDecorationSource,worldDecorationGroupCloneDraft} from '../editor/worldmap-decoration-state.js';
import {allocateWorldPlacements} from '../editor/worldmap-placement-replay.js';
const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let refusals=0,clones=0;
for(const {source:raw,current} of rows){
 const source=await qualifyWorldDecorationSource(raw,current,raw.project_path),held=JSON.stringify(raw),bytes=source.bytes.slice(),ids=raw.authored_allocations.map(r=>r.placement_id).sort(),delta={x:16,y:-4,z:32,yaw_units:1024};let requests,anchor;
 const fresh=()=>{let i=0;return ()=>`ffffffff-ffff-4fff-8fff-${String(++i).padStart(12,'0')}`;};
 for(const cell of raw.target_cells){try{requests=worldDecorationGroupCloneDraft(source,ids,cell,delta,fresh());anchor=cell;if(requests.some(r=>(source.bytes[0x4000+r.target_cell]&15)!==(source.bytes[0x4000+r.donor_cell]&15)))break;}catch{}}
 assert(requests);assert(requests.some(r=>(source.bytes[0x4000+r.target_cell]&15)!==(source.bytes[0x4000+r.donor_cell]&15)));const allocated=await allocateWorldPlacements(source.bytes,raw.floor_lut,raw.scene,requests),first=raw.authored_allocations.find(a=>a.placement_id===ids[0]),dx=anchor%128-first.target_cell%128,dz=Math.floor(anchor/128)-Math.floor(first.target_cell/128);
 for(const [index,request] of requests.entries()){
  const donor=raw.authored_allocations.find(a=>a.placement_id===ids[index]),copy=allocated.audit.allocations.find(a=>a.placement_id===request.placement_id),p=donor.native_seed.source_position;
  assert.deepEqual(copy.native_seed.source_position,{x:p.x+dx*128+delta.x,y:p.y+delta.y,z:p.z+dz*128-delta.z});assert.equal(copy.model_pool_index,donor.model_pool_index);assert.equal(copy.native_seed.source_rotation_psx.y,(donor.native_seed.source_rotation_psx.y+delta.yaw_units)%4096);clones++;
 }
 for(const args of [[[],anchor,delta],[ids,first.target_cell,delta],[[ids[0],ids[0]],anchor,delta],[['foreign'],anchor,delta],[ids,16384,delta],[ids,anchor,{...delta,y:.5}],[ids,anchor,{...delta,z:65536}],[ids,anchor,{...delta,y:65535}],[ids,anchor,{...delta,x:-65535}],[ids,anchor,{...delta,z:65535}]]){assert.throws(()=>worldDecorationGroupCloneDraft(source,...args,fresh()));refusals++;}
 for(const factory of [()=>ids[0].split('/').pop(),()=> 'ffffffff-ffff-4fff-8fff-000000000001',()=> 'bad']){assert.throws(()=>worldDecorationGroupCloneDraft(source,ids,anchor,delta,factory));refusals++;}
 for(const mutate of [s=>s.inventory.free_record_indices=[],s=>s.inventory.current_placements=Array(511),s=>s.metadata.authored_allocations[0].native_seed.source_position.x++]){const bad=structuredClone(source);mutate(bad);assert.throws(()=>worldDecorationGroupCloneDraft(bad,ids,anchor,delta,fresh()));refusals++;}
 assert.equal(JSON.stringify(raw),held);assert.deepEqual(source.bytes,bytes);
}
console.log(`${clones} actual native group copies preserve models, yaw and relative world positions; ${refusals} bounded/domain/UUID/source refusals pass.`);
