import fs from 'node:fs';
import assert from 'node:assert/strict';
import {decodeNpcArrivalPreview,npcArrivalPreviewCurrent,npcArrivalPreviewMarkers} from '../editor/npc-arrival-preview.js';
const fixture=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),{request,state}=fixture;
const report=decodeNpcArrivalPreview(fixture.report,request,state);
assert(npcArrivalPreviewCurrent(report,state));
assert.deepEqual(npcArrivalPreviewMarkers(report,12).map(p=>[p.layer,p.x,p.y,p.z,p.facing_angle_12bit]),[['Retail',4032,12,3904,0],['NPC Current',64,12,16384,3584]]);
for(const mutate of [v=>v.runtime_verified=true,v=>v.height_known=true,v=>v.destination_scene_id='scene://town01',v=>v.project_inputs_key='0'.repeat(64),v=>v.source.options.transitions[0].effective_values.direction_encoded=8,v=>v.source.options.transitions[0].raw_instruction_hex='00',v=>v.transition_activation='reachable']){
 const bad=structuredClone(fixture.report);mutate(bad);assert.throws(()=>decodeNpcArrivalPreview(bad,request,state));
}
for(const mutate of [s=>s.project.mode='live',s=>s.scene.id='scene://town01',s=>s.scene_preview_source_key='0'.repeat(64),s=>s.npc_arrival_preview_state_key='0'.repeat(64),s=>s.actor_drafts[request.entity_id].name='Changed']){
 const changed=structuredClone(state);mutate(changed);assert(!npcArrivalPreviewCurrent(report,changed));
}
assert.throws(()=>decodeNpcArrivalPreview(fixture.report,request,{...state,project:{mode:'live'}}));
assert.throws(()=>decodeNpcArrivalPreview(fixture.report,{...request,runtime_position:{}},state));
assert.throws(()=>npcArrivalPreviewMarkers(report,Infinity));
assert.throws(()=>npcArrivalPreviewMarkers(report,1e7+1));
assert.deepEqual(fixture.report,report);
console.log('Actual Retail/Current NPC destination markers, detached native source qualification, navigation freshness, Live and forged evidence refusal passed.');
