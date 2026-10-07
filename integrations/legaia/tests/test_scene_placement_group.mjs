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

for(const turns of [-1,1,2]){
 const op={kind:'rotate',anchor_entity_id:ids[1],quarter_turns:turns},points=mixedLayoutPositions(report.targets,op),rotation={...report,schema_version:'legaia.scene-placement-layout-review.v1',delta:{x:0,z:0},operation:op,affected_count:1,targets:report.targets.map((row,i)=>({...row,proposed:points[i].position}))};
 const [x,z]=turns===1?[896,256]:turns===-1?[256,1024]:[960,960];assert.deepEqual(points[0].position,{x,z});assert.deepEqual(points[1].position,report.targets[1].current);
 assert.deepEqual(decodeScenePlacementLayout(rotation,key,scene,ids,op),rotation);
 assert.throws(()=>decodeScenePlacementLayout({...rotation,targets:rotation.targets.map(row=>({...row,proposed:{...row.current}}))},key,scene,ids,op));
}
for(const op of [{kind:'rotate',quarter_turns:0,anchor_entity_id:ids[1]},{kind:'rotate',quarter_turns:true,anchor_entity_id:ids[1]},{kind:'rotate',quarter_turns:1,anchor_entity_id:ids[0]+'other'},{kind:'rotate',quarter_turns:1,anchor_entity_id:ids[1],axis:'x'},{kind:'rotate',quarter_turns:1,anchor_entity_id:ids[1]}]){
 const targets=op.anchor_entity_id===ids[1]&&op.quarter_turns===1&&!op.axis?report.targets.map(row=>({...row,current:{x:1,z:1}})):report.targets;
 assert.throws(()=>mixedLayoutPositions(targets,op));
}
console.log('Mixed position rotation: exact signed permutations, fixed selected anchor, forged proposals and grid/operation guards passed.');

const gridTargets=report.targets.map((r,i)=>({...r,current:i?{x:128,z:256}:{x:192,z:192}}));
for(const percent of [1,50,100,200,1000]){
 const op={kind:'scale',anchor_entity_id:ids[1],percent},points=mixedLayoutPositions(gridTargets,op);
 assert.deepEqual(points[1].position,gridTargets[1].current);
 const expected={x:Math.floor((12800+64*percent+50)/100),z:Math.floor((25600-64*percent+50)/100)};assert.deepEqual(points[0].position,expected);
 const scaled={...report,schema_version:'legaia.scene-placement-layout-review.v1',delta:{x:0,z:0},operation:op,targets:gridTargets.map((r,i)=>({...r,proposed:points[i].position}))};scaled.affected_count=scaled.targets.filter(r=>r.current.x!==r.proposed.x||r.current.z!==r.proposed.z).length;scaled.project_change=scaled.affected_count>0;assert.deepEqual(decodeScenePlacementLayout(scaled,key,scene,ids,op),scaled);
 assert.throws(()=>decodeScenePlacementLayout({...scaled,targets:scaled.targets.map((r,i)=>i?r:{...r,proposed:{...r.proposed,x:r.proposed.x+64}})},key,scene,ids,op));
}
for(const percent of [true,0,1001,50.5,'50'])assert.throws(()=>mixedLayoutPositions(gridTargets,{kind:'scale',anchor_entity_id:ids[1],percent}));
const nativeTargets=gridTargets.map((r,i)=>i?r:{...r,current:{x:193,z:191}});assert.deepEqual(mixedLayoutPositions(nativeTargets,{kind:'scale',anchor_entity_id:ids[0],percent:100}).map(r=>r.position),nativeTargets.map(r=>r.current));
assert.deepEqual(mixedLayoutPositions(nativeTargets,{kind:'scale',anchor_entity_id:ids[0],percent:50})[1].position,{x:192,z:192});
assert.throws(()=>mixedLayoutPositions(nativeTargets.map((r,i)=>i?r:{...r,current:{x:193.5,z:191}}),{kind:'scale',anchor_entity_id:ids[1],percent:100}));
console.log('Mixed spacing scale: native actor/scenery precision, off-grid anchor, fixed anchor, exact DTO and integer guards passed.');

const signedTargets=nativeTargets.map((r,i)=>i?r:{...r,current:{x:-1,z:257}});
assert.deepEqual(mixedLayoutPositions(signedTargets,{kind:'scale',anchor_entity_id:ids[1],percent:50})[0].position,{x:64,z:257});
assert.deepEqual(mixedLayoutPositions(signedTargets,{kind:'scale',anchor_entity_id:ids[1],percent:200})[0].position,{x:-130,z:258});

const nativeRotationTargets=report.targets.map((row,i)=>({...row,current:i?{x:128,z:256}:{x:202,z:162}}));
for(const turns of [-1,1,2]){const op={kind:'rotate',anchor_entity_id:ids[0],quarter_turns:turns},points=mixedLayoutPositions(nativeRotationTargets,op);assert.deepEqual(points[0].position,nativeRotationTargets[0].current);const expected=turns===1?{x:128,z:64}:turns===-1?{x:320,z:256}:{x:256,z:64};assert.deepEqual(points[1].position,expected);const review={...report,schema_version:'legaia.scene-placement-layout-review.v1',delta:{x:0,z:0},operation:op,affected_count:1,targets:nativeRotationTargets.map((r,i)=>({...r,proposed:points[i].position}))};assert.deepEqual(decodeScenePlacementLayout(review,key,scene,ids,op),review);assert.throws(()=>decodeScenePlacementLayout({...review,targets:review.targets.map((r,i)=>i?{...r,proposed:{...r.proposed,x:r.proposed.x+1}}:r)},key,scene,ids,op));}
const halfTargets=nativeRotationTargets.map((r,i)=>i?r:{...r,current:{x:80,z:144}});assert.deepEqual(mixedLayoutPositions(halfTargets,{kind:'rotate',anchor_entity_id:ids[0],quarter_turns:2})[1].position,{x:64,z:64});
assert.throws(()=>mixedLayoutPositions(nativeRotationTargets.map((r,i)=>i?r:{...r,current:{x:202.5,z:162}}),{kind:'rotate',anchor_entity_id:ids[0],quarter_turns:1}));assert.throws(()=>mixedLayoutPositions(nativeRotationTargets.map((r,i)=>({...r,current:{x:i?Number.MAX_SAFE_INTEGER:-Number.MAX_SAFE_INTEGER,z:162}})),{kind:'rotate',anchor_entity_id:ids[0],quarter_turns:1}));
console.log('Mixed native rotation: off-grid scenery anchors, exact quarter turns, final actor quantization, fixed anchor, half rounding and forged/safe-arithmetic guards passed.');

for(const axis of ['x','z']){const op={kind:'mirror',axis,anchor_entity_id:ids[0]},points=mixedLayoutPositions(nativeRotationTargets,op);assert.deepEqual(points[0].position,nativeRotationTargets[0].current);assert.deepEqual(points[1].position,axis==='x'?{x:256,z:256}:{x:128,z:64});const r={...report,schema_version:'legaia.scene-placement-layout-review.v1',delta:{x:0,z:0},operation:op,affected_count:1,targets:nativeRotationTargets.map((r,i)=>({...r,proposed:points[i].position}))};assert.deepEqual(decodeScenePlacementLayout(r,key,scene,ids,op),r);assert.throws(()=>decodeScenePlacementLayout({...r,targets:r.targets.map((t,i)=>i?{...t,proposed:{...t.proposed,[axis]:t.proposed[axis]+64}}:t)},key,scene,ids,op));}
assert.deepEqual(mixedLayoutPositions(halfTargets,{kind:'mirror',axis:'x',anchor_entity_id:ids[0]})[1].position,{x:64,z:256});for(const op of [{kind:'mirror',axis:'y',anchor_entity_id:ids[0]},{kind:'mirror',axis:'x'},{kind:'mirror',axis:'x',anchor_entity_id:'unknown'},{kind:'mirror',axis:'x',anchor_entity_id:ids[0],percent:100}])assert.throws(()=>mixedLayoutPositions(nativeRotationTargets,op));assert.throws(()=>mixedLayoutPositions(nativeRotationTargets.map(r=>({...r,current:{x:Number.MAX_SAFE_INTEGER,z:162}})),{kind:'mirror',axis:'x',anchor_entity_id:ids[0]}));
console.log('Mixed placement mirror: both axes, off-grid fixed anchor, retained other axis, native actor half rounding and forged/source/arithmetic guards passed.');

import {rotatePlacementPosition} from '../editor/placement-angle.js';

assert.deepEqual(rotatePlacementPosition({x:640,z:512},{x:512,z:512},1,45),{x:603,z:603});
assert.deepEqual(rotatePlacementPosition({x:640,z:512},{x:512,z:512},64,45),{x:576,z:576});
for(const angle of [true,45.5,'45',-360,360,NaN])assert.throws(()=>mixedLayoutPositions(report.targets,{kind:'rotate_angle',anchor_entity_id:ids[1],angle_degrees:angle}));
for(const angle of [-359,-90,-45,0,45,90,180,359]){const op={kind:'rotate_angle',anchor_entity_id:ids[1],angle_degrees:angle},points=mixedLayoutPositions(report.targets,op),r={...report,schema_version:'legaia.scene-placement-layout-review.v1',delta:{x:0,z:0},operation:op,affected_count:angle?1:0,project_change:!!angle,targets:report.targets.map((row,i)=>({...row,proposed:points[i].position}))};assert.deepEqual(decodeScenePlacementLayout(r,key,scene,ids,op),r);}
console.log('Whole-degree mixed position rotation: deterministic native rounding, exact operation fields, bounds and reviewed decoder passed.');
