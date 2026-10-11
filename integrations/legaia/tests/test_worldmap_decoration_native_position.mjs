import assert from 'node:assert/strict';import fs from 'node:fs';
import {worldDecorationNativePosition,worldDecorationValuesAtPosition} from '../editor/worldmap-decoration-state.js';
const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let conversions=0,refusals=0;
for(const {report} of rows){
 const meta=report.placement_authoring,source={metadata:{authored_allocations:meta.authored_allocations,floor_lut:meta.floor_lut},bytes:Uint8Array.from(Buffer.from(meta.current_map_base64,'base64'))};
 const held=JSON.stringify(meta),original=source.bytes.slice();
 for(const row of meta.authored_allocations){
  const view=new DataView(source.bytes.buffer),offset={x:view.getInt16(row.record_index*32,true),y:view.getInt16(row.record_index*32+2,true),z:view.getInt16(row.record_index*32+4,true)},yaw=view.getUint16(row.record_index*32+10,true)&4095,base={offset,yaw_units:yaw};
  assert.deepEqual(worldDecorationNativePosition(source,row.placement_id,base),row.native_seed.source_position);
  for(const n of [-32768,-1,0,1,32767]){const values={offset:{x:n,y:n,z:n},yaw_units:yaw},position=worldDecorationNativePosition(source,row.placement_id,values);assert.deepEqual(worldDecorationValuesAtPosition(source,row.placement_id,position,yaw),values);const cell=row.target_cell,tier=source.bytes[0x4000+cell]&15;assert.deepEqual(position,{x:(cell%128)*128+n+64,y:-meta.floor_lut[tier]+n,z:Math.floor(cell/128)*128-n+64});conversions++;}
  const p=row.native_seed.source_position;
  for(const bad of [{...p,x:NaN},{...p,y:.5},{...p,z:Infinity},{...p,x:Number.MAX_SAFE_INTEGER},{x:p.x,y:p.y},{...p,extra:1}]){assert.throws(()=>worldDecorationValuesAtPosition(source,row.placement_id,bad,yaw));refusals++;}
  for(const mutate of [s=>s.metadata.authored_allocations.find(a=>a.placement_id===row.placement_id).native_seed.source_position.x++,s=>s.bytes[0x8000+row.target_cell*2]^=1,s=>s.metadata.floor_lut[0]=NaN]){const bad=structuredClone(source);mutate(bad);assert.throws(()=>worldDecorationNativePosition(bad,row.placement_id,base));refusals++;}
 }
 assert.equal(JSON.stringify(meta),held);assert.deepEqual(source.bytes,original);
 assert.throws(()=>worldDecorationValuesAtPosition(source,'foreign',{x:0,y:0,z:0},0));refusals++;
}
console.log(`${conversions} actual native coordinate round trips and ${refusals} invalid coordinate/source refusals pass.`);
