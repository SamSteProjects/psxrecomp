import assert from 'node:assert/strict';
import {scenePlacementGroupDelta,decodeScenePlacementGroup,offsetScenePlacementGroup} from '../editor/scene-placement-group.js';
const key='a'.repeat(64),scene='scene://fixture';
const ids=['environment://fixture/field-map/decorations/00001','scene://fixture/actors/man-p1/0001'];
const delta={x:64,z:-128};
const report={schema_version:'legaia.scene-placement-group-review.v1',project_source_key:key,scene_id:scene,source_sha256:'b'.repeat(64),review_key:'c'.repeat(64),entity_ids:ids,delta,targets:[
  {entity_id:ids[0],kind:'decoration',cell_index:1,retail:{x:128,z:256},current:{x:192,z:320},proposed:{x:256,z:192}},
  {entity_id:ids[1],kind:'actor',retail:{x:512,z:512},current:{x:576,z:640},proposed:{x:640,z:512}},
],affected_count:2,project_change:true,scope:'imported-actor-and-static-decoration-xz-only',gameplay_verified:false};
assert.deepEqual(scenePlacementGroupDelta({z:-16320,x:16320}),{x:16320,z:-16320});
for(const value of [{x:1,z:0},{x:65,z:0},{x:16321,z:0},{x:-16321,z:0},{x:1.5,z:0},{x:true,z:0},{x:0},{x:0,z:0,extra:1},{x:NaN,z:0},{x:Infinity,z:0},null])assert.throws(()=>scenePlacementGroupDelta(value));
const decoded=decodeScenePlacementGroup(report,key,scene,ids,delta);assert.deepEqual(decoded,report);decoded.targets[0].current.x=0;assert.equal(report.targets[0].current.x,192);
for(const changes of [{schema_version:'wrong'},{project_source_key:'d'.repeat(64)},{scene_id:'scene://other'},{source_sha256:'bad'},{review_key:'bad'},{gameplay_verified:true},{scope:'runtime'},{project_change:1},{affected_count:1},{entity_ids:[...ids].reverse()},{delta:{x:65,z:-128}},{targets:report.targets.slice(0,1)}])assert.throws(()=>decodeScenePlacementGroup({...report,...changes},key,scene,ids,delta));
for(const change of [{cell_index:2},{cell_index:-1},{cell_index:16384},{entity_id:ids[1]},{kind:'actor'},{kind:'other'},{proposed:{x:257,z:192}},{current:{x:128,z:null}},{retail:{x:1.5,z:256}},{retail:{x:128,z:256,y:0}},{proposed:{x:Number.MAX_SAFE_INTEGER+1,z:192}}])assert.throws(()=>decodeScenePlacementGroup({...report,targets:[{...report.targets[0],...change},report.targets[1]]},key,scene,ids,delta));
for(const change of [{cell_index:1},{kind:'decoration'},{proposed:{x:640,z:513}}])assert.throws(()=>decodeScenePlacementGroup({...report,targets:[report.targets[0],{...report.targets[1],...change}]},key,scene,ids,delta));
for(const invalidIds of [[ids[0],ids[0]],[...ids].reverse(),[ids[0]],['environment://fixture/field-map/decorations/16384',ids[1]],['environment://other/field-map/decorations/00001',ids[1]],[ids[0],'scene://fixture/actors/man-p3/0001'],[ids[0],'scene://fixture/actors/draft/0001'],[ids[0],'scene://other/actors/man-p1/0001'],['environment://fixture/field-map/records/001',ids[1]],['scene://fixture/actors/man-p1/0001','scene://fixture/actors/man-p2/0002'],['environment://fixture/field-map/decorations/00001','environment://fixture/field-map/decorations/00002'],Array(129).fill(ids[0])])assert.throws(()=>decodeScenePlacementGroup(report,key,scene,invalidIds,delta));
assert.throws(()=>decodeScenePlacementGroup(report,'bad',scene,ids,delta));
assert.throws(()=>decodeScenePlacementGroup(report,key,'scene://fixture/other',ids,delta));
const zero={...report,delta:{x:0,z:0},affected_count:0,project_change:false,targets:report.targets.map(row=>({...row,proposed:{...row.current}}))};
assert.deepEqual(decodeScenePlacementGroup(zero,key,scene,ids,{x:0,z:0}),zero);
const overflow={...report,targets:[{...report.targets[0],current:{x:Number.MAX_SAFE_INTEGER,z:320},proposed:{x:Number.MAX_SAFE_INTEGER+64,z:192}},report.targets[1]]};
assert.throws(()=>decodeScenePlacementGroup(overflow,key,scene,ids,delta));
console.log('Mixed placement source identity, actor/decor selection, exact X/Z arithmetic, immutable decoding, no-op and offset bounds passed.');

assert.deepEqual(offsetScenePlacementGroup(report,'x',-128),{entity_ids:ids,delta:{x:-64,z:-128}});
assert.deepEqual(offsetScenePlacementGroup(report,'z',192),{entity_ids:ids,delta:{x:64,z:64}});
assert.deepEqual(report.delta,delta);
const dragged=offsetScenePlacementGroup(report,'x',64);dragged.entity_ids.pop();assert.equal(report.entity_ids.length,2);
for(const [axis,amount] of [['y',64],['x',1],['z',-65],['x',1.5],['z',true],['x',Infinity],['x',16320],['z',-16320]])assert.throws(()=>offsetScenePlacementGroup(report,axis,amount));
assert.throws(()=>offsetScenePlacementGroup({...report,targets:[{...report.targets[0],kind:'actor'},report.targets[1]]},'x',64));
const safeEdge={...report,delta:{x:0,z:0},affected_count:0,project_change:false,targets:report.targets.map((row,index)=>({...row,current:{x:index?Number.MAX_SAFE_INTEGER:192,z:320},proposed:{x:index?Number.MAX_SAFE_INTEGER:192,z:320}}))};
assert.throws(()=>offsetScenePlacementGroup(safeEdge,'x',64));
console.log('Mixed placement drag composition, 64-unit increments, immutable selections, bounds and decoded proposal guards passed.');

import {mixedLayoutPositions,decodeScenePlacementLayout} from '../editor/scene-placement-group.js';
const operation={kind:'align',axis:'x',anchor_entity_id:ids[1]},layout={...report,schema_version:'legaia.scene-placement-layout-review.v1',delta:{x:0,z:0},operation,affected_count:1,targets:report.targets.map(row=>({...row,proposed:{...row.current,x:576}}))};
assert.deepEqual(decodeScenePlacementLayout(layout,key,scene,ids,operation),layout);
for(const change of [{affected_count:2},{operation:{...operation,axis:'z'}},{targets:layout.targets.map(row=>({...row,proposed:{...row.proposed,z:0}}))}])assert.throws(()=>decodeScenePlacementLayout({...layout,...change},key,scene,ids,operation));
const three=[...report.targets,{entity_id:'environment://fixture/field-map/decorations/00002',current:{x:1024,z:320}}];assert.deepEqual(mixedLayoutPositions(three,{kind:'distribute',axis:'x'}).map(row=>row.position.x),[192,640,1024]);
assert.throws(()=>mixedLayoutPositions(three,{kind:'align',axis:'x',anchor_entity_id:'other'}));assert.throws(()=>mixedLayoutPositions(three,{kind:'distribute',axis:'y'}));
assert.throws(()=>mixedLayoutPositions(three.map(row=>({...row,current:{...row.current,x:1}})),{kind:'distribute',axis:'x'}));
console.log('Mixed layout: exact anchor/grid distribution, complete proposal qualification and forged operation/count/axis guards passed.');

const resetOp={kind:'reset'},reset={...report,schema_version:'legaia.scene-placement-layout-review.v1',delta:{x:0,z:0},operation:resetOp,reset_actor_axes:{[ids[1]]:['x']},targets:report.targets.map(row=>({...row,proposed:{...row.retail}}))};
assert.deepEqual(decodeScenePlacementLayout(reset,key,scene,ids,resetOp,{[ids[1]]:['x']}),reset);
for(const axes of [null,{}, {[ids[1]]:[]},{[ids[1]]:['z']}])assert.throws(()=>decodeScenePlacementLayout(reset,key,scene,ids,resetOp,axes));
const metadataReset={...reset,affected_count:0,targets:reset.targets.map(row=>({...row,current:{...row.retail}}))};assert.deepEqual(decodeScenePlacementLayout(metadataReset,key,scene,ids,resetOp,{[ids[1]]:['x']}),metadataReset);
assert.throws(()=>decodeScenePlacementLayout({...metadataReset,project_change:false},key,scene,ids,resetOp,{[ids[1]]:['x']}));
console.log('Mixed Retail reset: exact source positions, Current authored-axis witnesses, metadata-only reset and forged/no-op guards passed.');
