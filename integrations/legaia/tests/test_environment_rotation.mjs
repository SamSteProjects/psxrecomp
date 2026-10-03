import assert from 'node:assert/strict';
import {environmentYawMatrix,yawFromDrag,environmentRotationCommand} from '../editor/environment-rotation.js';
import {SceneRenderer} from '../editor/scene-renderer.js';

const scene='scene://fixture',hash='a'.repeat(64),id='environment://fixture/field-map/decorations/00001';
const item=()=>({entity_id:id,effective_transform:{position:{x:128,y:-32,z:256},rotation_psx:{x:0,y:100,z:0}},
  source_record:{semantic_id:id,object_record_index:194,record_offset:{x:16,y:-8,z:32},
    imported_transform:{rotation_psx:{x:256,y:100,z:768}},
    source_record:{grid_byte_offset:0x8002,map_sha256:hash}}});
const authoring=()=>({source_sha256:hash,
  edits:[{record_index:194,offset:{x:64,z:24},rotation_psx:{x:512,y:200,z:768}},
         {record_index:195,rotation_psx:{z:128}}],
  instances:[{cell_index:1,offset:{z:17},rotation_psx:{x:128,y:300}},
             {cell_index:2,rotation_psx:{y:700}}]});
const command=(value,yaw,shared=false)=>environmentRotationCommand(scene,item(),value,yaw,shared);

// A quarter-turn maps local +X to -Z before the single display Y flip.
{
  const entity=item(),before=JSON.stringify(entity),m=environmentYawMatrix(entity,1024);
  const expected=[0,0,1,128,0,-1,0,32,-1,0,0,256,0,0,0,1];
  m.forEach((v,i)=>assert.ok(Math.abs(v-expected[i])<1e-12));
  assert.equal(JSON.stringify(entity),before);
  const renderer=Object.create(SceneRenderer.prototype),instance={entity_id:id,geometry_key:'model',
    model_to_scene:[1,0,0,128,0,-1,0,32,0,0,1,256,0,0,0,1]},stored=JSON.stringify(instance);
  renderer.instances=[instance];renderer.meshes=new Map([['model',{min:[0,0,0],max:[2,3,5]}]]);
  const transforms=new Map([[id,m]]),points=renderer.bounds(new Map(),id,new Set(),transforms);
  for(const [axis,low,high] of [['x',128,133],['y',29,32],['z',254,256]]){
    assert.ok(Math.abs(Math.min(...points.map(p=>p[axis]))-low)<1e-12);
    assert.ok(Math.abs(Math.max(...points.map(p=>p[axis]))-high)<1e-12);
  }
  assert.deepEqual(renderer.bounds(new Map(),id,new Set([id]),transforms),[]);
  assert.equal(JSON.stringify(instance),stored,'Preview framing never mutates scene instances.');
  assert.deepEqual(renderer.matrix(instance,new Map()),instance.model_to_scene,'Default renderer path remains unchanged.');
  assert.throws(()=>renderer.bounds(new Map(),id,new Set(),new Map([[id,[1,NaN]]])));
}
// Circular dragging crosses both wrap boundaries and snaps in PSX angle units.
{
  const pivot={x:128,z:256},start={x:128,z:266};
  assert.equal(yawFromDrag(start,{x:138,z:256},pivot,0,1),1024);
  assert.equal(yawFromDrag(start,{x:118,z:256},pivot,100,1),3172);
  assert.equal(yawFromDrag(start,{x:128,z:266},pivot,4095,256),0);
  const angle=300*Math.PI*2/4096;
  assert.equal(yawFromDrag(start,{x:128+Math.sin(angle)*10,z:256+Math.cos(angle)*10},pivot,0,256),256);
  for(const args of [[pivot,start,pivot,0,1],[start,pivot,pivot,0,1],
    [start,{x:NaN,z:256},pivot,0,1],[start,start,pivot,0,3],[start,start,pivot,0,0],
    [start,start,pivot,.5,1]])assert.throws(()=>yawFromDrag(...args));
}
// Instance edits retain every other axis, offset, record, and sibling instance.
{
  const authored=authoring(),before=JSON.stringify(authored),source=item(),sourceBefore=JSON.stringify(source);
  const result=environmentRotationCommand(scene,source,authored,1024);
  const expected=structuredClone(authored);expected.instances[0].rotation_psx.y=1024;
  assert.deepEqual(result,{type:'set_environment_transforms',entity_id:scene,value:expected});
  assert.equal(JSON.stringify(authored),before);assert.equal(JSON.stringify(source),sourceBefore);
}
// Returning to the inherited shared yaw removes only the local yaw override.
{
  const authored=authoring(),result=command(authored,200),expected=structuredClone(authored);
  delete expected.instances[0].rotation_psx.y;
  assert.deepEqual(result.value,expected);
  const only={source_sha256:hash,edits:[],instances:[{cell_index:1,rotation_psx:{y:900}}]};
  assert.deepEqual(command(only,100),{type:'clear_environment_transforms',entity_id:scene});
  assert.deepEqual(command(null,100),{type:'clear_environment_transforms',entity_id:scene});
}
// Shared authoring targets the record while preserving per-instance yaw overrides.
{
  const authored=authoring(),result=command(authored,1024,true),expected=structuredClone(authored);
  expected.edits[0].rotation_psx.y=1024;
  assert.deepEqual(result,{type:'set_environment_transforms',entity_id:scene,value:expected});
  const reset=command(authored,100,true),cleanup=structuredClone(authored);
  delete cleanup.edits[0].rotation_psx.y;
  assert.deepEqual(reset.value,cleanup);
}
// Foreign source owners, malformed yaw and non-decoration individual edits reject.
{
  for(const yaw of [-1,4096,.5,Infinity,NaN]){
    assert.throws(()=>command(authoring(),yaw));assert.throws(()=>environmentYawMatrix(item(),yaw));
  }
  const cell=item();cell.entity_id='environment://fixture/field-map/cells/00001';cell.source_record.semantic_id=cell.entity_id;
  assert.throws(()=>environmentRotationCommand(scene,cell,authoring(),1024));
  assert.equal(environmentRotationCommand(scene,cell,authoring(),1024,true).value.edits[0].rotation_psx.y,1024);
  const foreign=item();foreign.entity_id=id.replace('fixture','foreign');
  assert.throws(()=>environmentRotationCommand(scene,foreign,authoring(),1024));
  const stale=authoring();stale.source_sha256='b'.repeat(64);
  assert.throws(()=>command(stale,1024));
}
console.log('Scenery yaw matrix, circular drag, instance/shared inheritance and read-only command construction passed.');
