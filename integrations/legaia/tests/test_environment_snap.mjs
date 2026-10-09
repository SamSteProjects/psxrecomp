import assert from 'node:assert/strict';
import {environmentLayoutOperation,decodeEnvironmentLayout} from '../editor/environment-layout.js';
const key='a'.repeat(64),scene='scene://fixture',ids=[1,2].map(i=>`environment://fixture/field-map/decorations/${String(i).padStart(5,'0')}`),operation={kind:'snap',axes:['x','z'],spacing:5};
const report={schema_version:'legaia.environment-layout-review.v1',project_source_key:key,scene_id:scene,source_sha256:'b'.repeat(64),review_key:'c'.repeat(64),entity_ids:ids,operation,targets:ids.map((entity_id,i)=>({entity_id,cell_index:i+1,retail:{x:0,z:0},current:i?{x:3,z:2}:{x:-3,z:-2},proposed:i?{x:5,z:0}:{x:-5,z:0}})),affected_count:2,project_change:true,value:{},scope:'static-decoration-instance-transform-only',gameplay_verified:false};
assert.deepEqual(decodeEnvironmentLayout(report,key,scene,ids,operation),report);const detached=environmentLayoutOperation(operation,ids);detached.axes.pop();assert.equal(operation.axes.length,2);
for(const op of [{kind:'snap',axes:['x','x'],spacing:5},{kind:'snap',axes:['z','x'],spacing:5},{kind:'snap',axes:['x'],spacing:0},{kind:'snap',axes:['x'],spacing:4097},{...operation,anchor:ids[0]}])assert.throws(()=>environmentLayoutOperation(op,ids));
const forged=structuredClone(report);forged.targets[0].proposed.x=-4;assert.throws(()=>decodeEnvironmentLayout(forged,key,scene,ids,operation));
console.log('Scenery grid snap: native integer spacing, signed odd-grid rounding, detached axes and forged proposal refusal passed.');
