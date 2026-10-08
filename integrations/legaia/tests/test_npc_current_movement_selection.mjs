import assert from 'node:assert/strict';
import fs from 'node:fs';
import {decodeNpcCurrentScript,npcCurrentMovementSelection,npcCurrentSystemSelection} from '../editor/npc-current-script.js';
assert(process.argv[2],'Fresh Retail Current and movement qualification required');
const f=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),before=structuredClone(f),current=await decodeNpcCurrentScript(f.report,f.entity_id,f.state);
const selected=npcCurrentMovementSelection(current,f.movement,35,f.state);assert.equal(selected.entity_id,f.entity_id);assert.equal(selected.movement_id,'script://town01/actors/man-p1/0011/movement/0023');assert.deepEqual(selected.values,{x:64,z:16384,move_id:13});
selected.values.x=128;assert.deepEqual(f,before);
for(const pc of [null,19,999999])assert.throws(()=>npcCurrentMovementSelection(current,f.movement,pc,f.state));
for(const change of [s=>s.project.mode='live',s=>s.capabilities.actor_movement_authoring=false,s=>s.project_copy_source_key='f'.repeat(64),s=>s.actor_drafts[f.entity_id].donor_entity_id='scene://town01/actors/man-p1/0040']){const state=structuredClone(f.state);change(state);assert.throws(()=>npcCurrentMovementSelection(current,f.movement,35,state));}
for(const change of [s=>s.options.targets.find(n=>n.pc===35).source_record_sha256='b'.repeat(64),s=>s.options.targets.find(n=>n.pc===35).effective_values.x=128,s=>s.entity_id='authored-actor://other']){const source=structuredClone(f.movement);change(source);assert.throws(()=>npcCurrentMovementSelection(current,source,35,f.state));}
console.log('Current destination editing independently binds source owner, native record, effective coordinates, exact PC, Edit/capability and stale-context gates.');

const system=npcCurrentSystemSelection(current,f.system_flags,22,f.state);assert.equal(system.system_flag_id,'script://town01/actors/man-p1/0011/system-flag/0016');assert.deepEqual(system.values,{index:326});system.values.index=4095;assert.deepEqual(f,before);
for(const pc of [null,35,99999])assert.throws(()=>npcCurrentSystemSelection(current,f.system_flags,pc,f.state));
for(const change of [s=>s.project.mode='live',s=>s.capabilities.npc_system_selector_authoring=false,s=>s.project_copy_source_key='f'.repeat(64)]){const state=structuredClone(f.state);change(state);assert.throws(()=>npcCurrentSystemSelection(current,f.system_flags,22,state));}
for(const change of [s=>s.options.targets.find(n=>n.pc===22).source_record_sha256='b'.repeat(64),s=>s.options.targets.find(n=>n.pc===22).effective_values.index=2048,s=>s.entity_id='authored-actor://other']){const source=structuredClone(f.system_flags);change(source);assert.throws(()=>npcCurrentSystemSelection(current,source,22,f.state));}
console.log('Current system selector editing binds exact PC, source record, effective index, ownership and Edit/capability gates.');
