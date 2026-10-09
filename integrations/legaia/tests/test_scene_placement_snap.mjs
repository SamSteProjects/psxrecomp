import assert from 'node:assert/strict';
import {mixedLayoutPositions} from '../editor/scene-placement-group.js';
const targets=[{entity_id:'scene://fixture/actors/man-p1/0001',current:{x:192,z:320}},{entity_id:'environment://fixture/field-map/decorations/00001',current:{x:-128,z:130}}];
const held=structuredClone(targets);
assert.deepEqual(mixedLayoutPositions(targets,{kind:'snap',axes:['x','z'],spacing:256}).map(r=>r.position),[{x:256,z:256},{x:-256,z:256}]);
assert.deepEqual(mixedLayoutPositions(targets,{kind:'snap',axes:['x'],spacing:256}).map(r=>r.position),[{x:256,z:320},{x:-256,z:130}]);assert.deepEqual(targets,held);
for(const op of [{kind:'snap',axes:['x'],spacing:65},{kind:'snap',axes:['z','x'],spacing:256},{kind:'snap',axes:['x','x'],spacing:256},{kind:'snap',axes:['x'],spacing:256,anchor_entity_id:targets[0].entity_id},{kind:'snap',axes:['x'],spacing:0}])assert.throws(()=>mixedLayoutPositions(targets,op));
assert.throws(()=>mixedLayoutPositions([{...targets[0],current:{x:64,z:320}},targets[1]],{kind:'snap',axes:['x'],spacing:256}));
console.log('Mixed grid snap: signed half rounding, selected axes, immutable targets, strict fields and atomic actor boundary refusal passed.');
