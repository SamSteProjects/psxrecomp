import assert from 'node:assert/strict';
import {environmentRotationGroupOperation,decodeEnvironmentRotationGroup} from '../editor/environment-rotation-group.js';
const key='a'.repeat(64),scene='scene://fixture',ids=[129,258].map(c=>`environment://fixture/field-map/decorations/${String(c).padStart(5,'0')}`);
const operation={anchor_id:ids[0],quarter_turns:1};
const rows=[{entity_id:ids[0],cell_index:129,retail:{x:202,z:162,yaw:200},current:{x:262,z:132,yaw:777},proposed:{x:262,z:132,yaw:1801}},
  {entity_id:ids[1],cell_index:258,retail:{x:330,z:290,yaw:200},current:{x:360,z:260,yaw:4000},proposed:{x:390,z:34,yaw:928}}];
const report={schema_version:'legaia.environment-rotation-group-review.v1',project_source_key:key,scene_id:scene,source_sha256:'b'.repeat(64),review_key:'c'.repeat(64),entity_ids:ids,operation,targets:rows,affected_count:2,project_change:true,value:{},scope:'static-decoration-instance-layout-and-yaw-only',gameplay_verified:false};
assert.deepEqual(environmentRotationGroupOperation(operation,ids),operation);
for(const bad of [null,{}, {...operation,quarter_turns:true},{...operation,quarter_turns:-1},{...operation,quarter_turns:4},{...operation,quarter_turns:1.1},{...operation,anchor_id:'foreign'},{...operation,extra:true}])assert.throws(()=>environmentRotationGroupOperation(bad,ids));
for(const bad of [ids.slice(0,1),ids.toReversed(),[ids[0],ids[0]],[ids[0],'environment://fixture/field-map/decorations/16384']])assert.throws(()=>environmentRotationGroupOperation(operation,bad));
const decoded=decodeEnvironmentRotationGroup(report,key,scene,ids,operation);decoded.targets[0].current.yaw=0;assert.equal(report.targets[0].current.yaw,777);
for(const delta of [{project_source_key:'d'.repeat(64)},{scene_id:'scene://other'},{entity_ids:ids.toReversed()},{scope:'shared'},{gameplay_verified:true},{affected_count:1},{review_key:'bad'}])assert.throws(()=>decodeEnvironmentRotationGroup({...report,...delta},key,scene,ids,operation));
for(const delta of [{cell_index:128},{current:{x:262,z:132,yaw:4096}},{retail:{x:202,z:162,yaw:-1}},{proposed:{x:262,z:133,yaw:1801}},{proposed:{x:262,z:132,yaw:1802}},{current:{x:NaN,z:132,yaw:777}}])assert.throws(()=>decodeEnvironmentRotationGroup({...report,targets:[{...rows[0],...delta},rows[1]]},key,scene,ids,operation));
for(let q=0;q<4;q++){
  const op={anchor_id:ids[0],quarter_turns:q},coords=[[360,260],[390,34],[164,4],[134,230]][q];
  const targets=rows.map((row,index)=>({...row,proposed:{x:index?coords[0]:262,z:index?coords[1]:132,yaw:(row.current.yaw+q*1024)%4096}}));
  const candidate={...report,operation:op,targets,affected_count:q?2:0,project_change:q!==0};
  assert.deepEqual(decodeEnvironmentRotationGroup(candidate,key,scene,ids,op),candidate);
  if(q===0)assert.throws(()=>decodeEnvironmentRotationGroup({...candidate,project_change:true},key,scene,ids,op));
}
console.log('Scenery group rotation: pivot direction, all quarter turns, yaw wrap, stale identity, exact selection, malformed reports and no-op guards passed.');
