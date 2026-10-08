import assert from 'node:assert/strict';
import {captureNpcDuplication,duplicatedNpcSelection} from '../editor/npc-creation-selection.js';
const scene='scene://town01',donor=scene+'/actors/man-p1/0002',originalId='authored-actor://12345678-1234-4234-8234-123456789abc',newId='authored-actor://22345678-1234-4234-8234-123456789abc';
const original={scene_id:scene,donor_entity_id:donor,name:'Resident',position:{x:128,z:256},dialogue:{runs:{line:'Hello'}},facing:{entries:{pc:{sector:3}}}};
const before={project:{mode:'edit',path:'fixture'},scene:{id:scene,entities:[{id:donor}]},actor_drafts:{[originalId]:original}},capture=captureNpcDuplication(before,originalId,'Resident copy');
const after={...structuredClone(before),actor_drafts:{...structuredClone(before.actor_drafts),[newId]:{...structuredClone(original),name:'Resident copy'}}};
assert.equal(duplicatedNpcSelection(after,capture),newId);original.dialogue.runs.line='Changed';assert.equal(capture.draft.dialogue.runs.line,'Hello');
for(const change of [v=>v.actor_drafts[newId].facing.entries.pc.sector=4,v=>delete v.actor_drafts[newId].dialogue,v=>v.actor_drafts[newId].position.x=192,v=>v.actor_drafts[originalId].name='Changed',v=>v.actor_drafts.extra=v.actor_drafts[newId],v=>v.project.path='other',v=>v.project.mode='live']){const bad=structuredClone(after);change(bad);assert.throws(()=>duplicatedNpcSelection(bad,capture));}
assert.throws(()=>captureNpcDuplication(before,'missing','Copy'));assert.throws(()=>captureNpcDuplication(before,originalId,''));assert.throws(()=>captureNpcDuplication({...before,project:{...before.project,mode:'live'}},originalId,'Copy'));
console.log('NPC duplication binds unique UUID, complete detached component copy, name/placement/scope and preserved original drafts.');
