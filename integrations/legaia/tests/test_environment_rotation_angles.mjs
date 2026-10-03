import assert from 'node:assert/strict';
import {SOURCE_YAW_Q30,Q30_SINE_QUARTER,sourceYawSinCos,roundSourceQ30,rotateSourceXZ} from '../editor/environment-rotation-math.js';
import {environmentRotationGroupOperation,decodeEnvironmentRotationGroup} from '../editor/environment-rotation-group.js';
const parity=[];
const rounded=value=>value<0?-Math.floor(-value+.5):Math.floor(value+.5);
assert.equal(Q30_SINE_QUARTER.length,1025);
for(let angle=0;angle<4096;angle++){
  const theta=angle*Math.PI/2048,sin=rounded(Math.sin(theta)*Number(SOURCE_YAW_Q30)),cos=rounded(Math.cos(theta)*Number(SOURCE_YAW_Q30));
  const actual=sourceYawSinCos(angle);assert.ok(actual.sin===sin&&actual.cos===cos);
  const point=rotateSourceXZ(-137,281,angle),away=n=>n<0n?-((-n+SOURCE_YAW_Q30/2n)/SOURCE_YAW_Q30):(n+SOURCE_YAW_Q30/2n)/SOURCE_YAW_Q30;
  assert.deepEqual(point,{x:away(-137n*BigInt(cos)+281n*BigInt(sin)),z:away(281n*BigInt(cos)+137n*BigInt(sin))});
  parity.push([Number(point.x),Number(point.z)]);
}
for(const [numerator,expected] of [[SOURCE_YAW_Q30/2n,1n],[-SOURCE_YAW_Q30/2n,-1n],[SOURCE_YAW_Q30*3n/2n,2n],[-SOURCE_YAW_Q30*3n/2n,-2n],[SOURCE_YAW_Q30/2n-1n,0n],[-SOURCE_YAW_Q30/2n+1n,0n]])assert.equal(roundSourceQ30(numerator),expected);
const ids=[129,258].map(c=>`environment://fixture/field-map/decorations/${String(c).padStart(5,'0')}`),operation={anchor_id:ids[0],yaw_units:512};
assert.deepEqual(environmentRotationGroupOperation(operation,ids),operation);
for(const value of [true,false,-1,4096,512.5,'512'])assert.throws(()=>environmentRotationGroupOperation({...operation,yaw_units:value},ids));
for(const delta of [{quarter_turns:1},{extra:true}])assert.throws(()=>environmentRotationGroupOperation({...operation,...delta},ids));
const key='a'.repeat(64),scene='scene://fixture',rows=[{entity_id:ids[0],cell_index:129,retail:{x:202,z:162,yaw:200},current:{x:202,z:162,yaw:200},proposed:{x:202,z:162,yaw:712}},{entity_id:ids[1],cell_index:258,retail:{x:330,z:290,yaw:200},current:{x:330,z:290,yaw:200},proposed:{x:383,z:162,yaw:712}}];
const report={schema_version:'legaia.environment-rotation-group-review.v1',project_source_key:key,scene_id:scene,source_sha256:'b'.repeat(64),review_key:'c'.repeat(64),entity_ids:ids,operation,targets:rows,affected_count:2,project_change:true,value:{},scope:'static-decoration-instance-layout-and-yaw-only',gameplay_verified:false};
assert.deepEqual(decodeEnvironmentRotationGroup(report,key,scene,ids,operation),report);
assert.throws(()=>decodeEnvironmentRotationGroup({...report,targets:[rows[0],{...rows[1],proposed:{...rows[1].proposed,x:384}}]},key,scene,ids,operation));
assert.throws(()=>decodeEnvironmentRotationGroup(report,'d'.repeat(64),scene,ids,operation));
if(process.argv.includes('--parity-json'))console.log(JSON.stringify(parity));
else console.log('All4096 source angles, Q30 signed rounding, independent trig, custom report arithmetic and stale/invalid operation guards passed.');
