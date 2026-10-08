import assert from 'node:assert/strict';
import {captureNpcPresetCreation,createdNpcPresetSelection} from '../editor/npc-creation-selection.js';
const key='a'.repeat(64),scene='scene://town01',donor=scene+'/actors/man-p1/0002',id='authored-actor://12345678-1234-5234-8234-123456789abc';
const state={project:{mode:'edit',path:'fixture'},scene:{id:scene,entities:[{id:donor}]},project_copy_source_key:key,scene_preview_source_key:key,actor_drafts:{existing:{scene_id:scene,donor_entity_id:donor,name:'Existing',position:{x:64,z:128}}}};
const draft={scene_id:scene,donor_entity_id:donor,name:'Resident',position:{x:128,z:256},facing:{entries:{pc:{sector:3,source_sha256:key}}}};
const report={schema_version:'legaia.npc-preset-review.v1',project_source_key:key,scene_preview_source_key:key,scene_id:scene,entity_id:id,draft,gameplay_verified:false};
const capture=captureNpcPresetCreation(state,report),after={...structuredClone(state),actor_drafts:{...structuredClone(state.actor_drafts),[id]:structuredClone(draft)}};
report.draft.name='Mutated';assert.equal(capture.draft.name,'Resident');assert.equal(createdNpcPresetSelection(after,capture),id);
for(const change of [v=>v.actor_drafts[id].facing.entries.pc.sector=4,v=>v.actor_drafts[id].position.x=192,v=>v.actor_drafts.existing.name='Changed',v=>{v.actor_drafts['authored-actor://22345678-1234-5234-8234-123456789abc']=v.actor_drafts[id];delete v.actor_drafts[id];},v=>v.project.path='other',v=>v.project.mode='live']){const bad=structuredClone(after);change(bad);assert.throws(()=>createdNpcPresetSelection(bad,capture));}
for(const change of [v=>v.project_copy_source_key='b'.repeat(64),v=>v.scene_preview_source_key='b'.repeat(64),v=>v.actor_drafts[id]=draft,v=>v.project.mode='live']){const bad=structuredClone(state);change(bad);assert.throws(()=>captureNpcPresetCreation(bad,{...report,draft:capture.draft}));}
console.log('Preset creation selection binds planned identity and all reviewed components, retains prior drafts and refuses stale Project/scene/Live state.');
