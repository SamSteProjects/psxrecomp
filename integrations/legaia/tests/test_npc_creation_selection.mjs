import assert from 'node:assert/strict';
import {captureNpcCreation,createdNpcSelection} from '../editor/npc-creation-selection.js';
const scene='scene://fixture',donor=scene+'/actors/man-p1/0001',old='authored-actor://old',id='authored-actor://new';
const before={project:{mode:'edit',path:'fixture'},scene:{id:scene,entities:[{id:donor}]},actor_drafts:{[old]:{scene_id:scene,donor_entity_id:donor,name:'Old',position:{x:64,z:128}}}};
const command={type:'create_actor_draft',donor_entity_id:donor,name:'Created',position:{x:128,z:256}};
const capture=captureNpcCreation(before,command),state=structuredClone(before);
state.actor_drafts[id]={scene_id:scene,donor_entity_id:donor,name:'Created',position:{x:128,z:256}};
assert.equal(createdNpcSelection(state,capture),id);
command.position.x=999;before.actor_drafts[old].name='Changed after capture';assert.equal(capture.position.x,128);assert.equal(capture.existing[old].name,'Old');
for(const mutate of [s=>s.project.path='other',s=>s.project.mode='live',s=>s.scene.id='other',s=>delete s.actor_drafts[id],s=>s.actor_drafts.extra=structuredClone(s.actor_drafts[id]),s=>s.actor_drafts[id].donor_entity_id='other',s=>s.actor_drafts[id].position.x=64,s=>s.actor_drafts[id].name='other',s=>s.actor_drafts[old].name='other']){const changed=structuredClone(state);mutate(changed);assert.throws(()=>createdNpcSelection(changed,capture));}
assert.throws(()=>captureNpcCreation({...state,project:{...state.project,mode:'live'}},command));
assert.throws(()=>captureNpcCreation(state,{...command,donor_entity_id:'missing'}));
console.log('NPC creation selection is detached and binds unique returned identity, scope, donor, name, position and unchanged previous drafts.');
