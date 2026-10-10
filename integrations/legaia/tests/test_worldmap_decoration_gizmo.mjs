import assert from 'node:assert/strict';
import {worldDecorationDraftPosition} from '../editor/worldmap-decoration-gizmo.js';
import {translateOffset} from '../editor/worldmap-placement-gizmo.js';
const id='scene://map01/worldmap/authored-placements/00000000-0000-4000-8000-000000000001';
const entity={entity_id:id,placement_scope:'authored_spawn_seed',model_to_scene:[1,0,0,500,0,-1,0,80,0,0,1,900,0,0,0,1]};
const base={offset:{x:7,y:-32,z:64},yaw_units:2112},draft={entityId:id,base,values:structuredClone(base)},held=structuredClone([entity,draft]);
assert.equal(worldDecorationDraftPosition(entity,draft),null);
for(const axis of ['x','y','z']){
 const values=translateOffset(base,axis,{x:32,y:0},{x:128,y:0},128,16),position=worldDecorationDraftPosition(entity,{...draft,values});
 const delta=values.offset[axis]-base.offset[axis];const expected={x:500,y:80,z:900};expected[axis]+=axis==='x'?delta:-delta;assert.deepEqual(position,expected);
}
assert.deepEqual(worldDecorationDraftPosition(entity,{...draft,values:{offset:{x:32767,y:-32768,z:32767},yaw_units:2112}}),{x:33260,y:32816,z:-31803});
for(const change of [d=>d.entityId='foreign',d=>d.values.offset.x=32768,d=>d.values.offset.y=NaN,d=>d.values.yaw_units=0,d=>d.base.offset.z=1.2]){const bad=structuredClone(draft);change(bad);assert.throws(()=>worldDecorationDraftPosition(entity,bad));}
assert.throws(()=>worldDecorationDraftPosition({...entity,placement_scope:'source_spawn_seed'},draft));assert.deepEqual([entity,draft],held);
console.log('Decoration XYZ preview uses native direction, signed limits and immutable owner; invalid/foreign/yaw-changing drafts refuse.');

if(process.argv[2]){
 const fs=await import('node:fs'),{qualifyCurrentWorldPlacements}=await import('../editor/worldmap-current-placements.js'),{decodeWorldPlacementSeeds}=await import('../editor/worldmap-placement-replay.js');
 const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8')).filter(r=>r.phase==='parent');let cases=0;
 for(const row of rows){
  const view=await qualifyCurrentWorldPlacements(row.retail,row.current,row.options),meta=row.current.placement_authoring,raw=Uint8Array.from(Buffer.from(meta.current_map_base64,'base64'));
  for(const entity of view.entities.filter(e=>e.placement_scope==='authored_spawn_seed')){
   const at=entity.object_record_index*32,v=new DataView(raw.buffer),base={offset:{x:v.getInt16(at,true),y:v.getInt16(at+2,true),z:v.getInt16(at+4,true)},yaw_units:v.getUint16(at+10,true)&4095};
   for(const [axis,byte] of [['x',0],['y',2],['z',4]]){
    const values=structuredClone(base);values.offset[axis]+=64;const changed=raw.slice();new DataView(changed.buffer).setInt16(at+byte,values.offset[axis],true);
    const decoded=await decodeWorldPlacementSeeds(changed,meta.floor_lut,row.current.scene),seed=decoded.placements.find(e=>e.entity_id===entity.native_entity_id),display=worldDecorationDraftPosition(entity,{entityId:entity.entity_id,base,values});
    assert.deepEqual(display,{x:seed.source_position.x,y:-seed.source_position.y,z:seed.source_position.z});cases++;
   }
  }
 }
 assert.equal(cases,18);console.log('18 actual coauthored native XYZ word changes match the decoration display preview in all three kingdoms.');
}
