import assert from 'node:assert/strict';
import {sceneGroundPositionCommand} from '../editor/scene-ground-position.js';
const position={x:128,z:256};const actor=sceneGroundPositionCommand('actor','scene://fixture/actors/0001',position),npc=sceneGroundPositionCommand('npc','authored-actor://fixture',position);assert.equal(actor.type,'set_transform');assert.equal(npc.type,'set_actor_draft_position');assert.deepEqual(actor.position,position);actor.position.x=999;assert.equal(position.x,128);assert.deepEqual(Object.keys(npc.position),['x','z']);
for(const bad of [{x:65,z:256},{x:0,z:256},{x:16448,z:256},{x:128,z:256,y:0},{x:NaN,z:256},null])assert.throws(()=>sceneGroundPositionCommand('actor','id',bad));assert.throws(()=>sceneGroundPositionCommand('scenery','id',position));
console.log('Actor/NPC picked positions use detached X/Z-only existing Project commands and reject unsupported axes/grid.');
