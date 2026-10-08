import assert from 'node:assert/strict';
import fs from 'node:fs';
import {decodeNpcCurrentScript,npcCurrentMovementSelection} from '../editor/npc-current-script.js';
assert(process.argv[2],'Fresh Retail Current and movement qualification required');
const f=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),before=structuredClone(f),current=await decodeNpcCurrentScript(f.report,f.entity_id,f.state);
const selected=npcCurrentMovementSelection(current,f.movement,35,f.state);assert.equal(selected.entity_id,f.entity_id);assert.equal(selected.movement_id,'script://town01/actors/man-p1/0011/movement/0023');assert.deepEqual(selected.values,{x:64,z:16384,move_id:13});
selected.values.x=128;assert.deepEqual(f,before);
for(const pc of [null,19,999999])assert.throws(()=>npcCurrentMovementSelection(current,f.movement,pc,f.state));
for(const change of [s=>s.project.mode='live',s=>s.capabilities.actor_movement_authoring=false,s=>s.project_copy_source_key='f'.repeat(64),s=>s.actor_drafts[f.entity_id].donor_entity_id='scene://town01/actors/man-p1/0040']){const state=structuredClone(f.state);change(state);assert.throws(()=>npcCurrentMovementSelection(current,f.movement,35,state));}
for(const change of [s=>s.options.targets.find(n=>n.pc===35).source_record_sha256='b'.repeat(64),s=>s.options.targets.find(n=>n.pc===35).effective_values.x=128,s=>s.entity_id='authored-actor://other']){const source=structuredClone(f.movement);change(source);assert.throws(()=>npcCurrentMovementSelection(current,source,35,f.state));}
console.log('Current destination editing independently binds source owner, native record, effective coordinates, exact PC, Edit/capability and stale-context gates.');
