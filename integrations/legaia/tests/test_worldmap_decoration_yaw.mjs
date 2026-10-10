import assert from 'node:assert/strict';import fs from 'node:fs';
import {worldDecorationDraftTransform} from '../editor/worldmap-decoration-gizmo.js';
import {rotateSourceYaw} from '../editor/worldmap-placement-yaw.js';
import {qualifyCurrentWorldPlacements} from '../editor/worldmap-current-placements.js';
import {decodeWorldPlacementSeeds} from '../editor/worldmap-placement-replay.js';
const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8')).filter(r=>r.phase==='parent');let cases=0,refusals=0;
for(const row of rows){
 const view=await qualifyCurrentWorldPlacements(row.retail,row.current,row.options),meta=row.current.placement_authoring,raw=Uint8Array.from(Buffer.from(meta.current_map_base64,'base64'));
 for(const entity of view.entities.filter(e=>e.placement_scope==='authored_spawn_seed')){
  const at=entity.object_record_index*32,bytes=new DataView(raw.buffer),base={offset:{x:bytes.getInt16(at,true),y:bytes.getInt16(at+2,true),z:bytes.getInt16(at+4,true)},yaw_units:bytes.getUint16(at+10,true)&4095},draft={entityId:entity.entity_id,base,values:structuredClone(base)};
  assert.equal(worldDecorationDraftTransform(entity,draft),null);
  for(const angle of [0,1,1024,2048,4095])for(const translate of [false,true]){
   const values=structuredClone(base);values.yaw_units=angle;if(translate){values.offset.x+=64;values.offset.y-=16;values.offset.z+=128;}
   const changed=raw.slice(),v=new DataView(changed.buffer);v.setUint16(at+10,(v.getUint16(at+10,true)&0xf000)|angle,true);for(const [axis,byte] of [['x',0],['y',2],['z',4]])v.setInt16(at+byte,values.offset[axis],true);
   const decoded=await decodeWorldPlacementSeeds(changed,meta.floor_lut,row.current.scene),seed=decoded.placements.find(e=>e.entity_id===entity.native_entity_id),matrix=worldDecorationDraftTransform(entity,{...draft,values});
   if(angle===base.yaw_units){assert.equal(matrix,null);}else{const expected=[];for(let r=0;r<4;r++)for(let c=0;c<4;c++)expected.push(seed.source_to_world[c*4+r]*(r===1?-1:1));assert(matrix.every((n,i)=>Math.abs(n-expected[i])<=1e-12));}
   assert.equal(v.getUint16(at+10,true)&0xf000,bytes.getUint16(at+10,true)&0xf000);cases++;
  }
  for(const mutate of [e=>e.source_rotation_psx.x=1,e=>e.source_rotation_psx.z=1,e=>e.source_rotation_psx.y=undefined,e=>e.source_rotation_psx.y=(e.source_rotation_psx.y+1)&65535,e=>e.entity_id='foreign']){
   const bad=structuredClone(entity);mutate(bad);assert.throws(()=>worldDecorationDraftTransform(bad,{...draft,values:rotateSourceYaw(base,Math.PI/2,256)}));refusals++;
  }
 }
}
assert.equal(cases,60);assert.equal(refusals,30);console.log('60 actual native yaw/combined XYZ cases match reflected model matrices; 30 tilt/stale/foreign native-owner inputs refused.');
