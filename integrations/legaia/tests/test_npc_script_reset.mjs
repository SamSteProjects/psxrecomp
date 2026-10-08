import assert from 'node:assert/strict';import fs from 'node:fs';
import {decodeNpcScriptResetSource,decodeNpcScriptResetReview} from '../editor/npc-script-reset.js';
const id='authored-actor://fixture',key='a'.repeat(64),families=['dialogue','waits','movement','facing','flags','system_flags','branches','model_selectors','effect_colors','transitions'];
const draft={scene_id:'scene://fixture',donor_entity_id:'scene://fixture/actors/man-p1/0001',name:'NPC',position:{x:128,z:256},waits:{entries:{one:{duration_ticks:12}}},facing:{entries:{two:{sector:4}}}};
const state={scene:{id:draft.scene_id},project_copy_source_key:key,actor_drafts:{[id]:draft}},scope={scope:'project_metadata',native_byte_preview:false,runtime_binding:'not_asserted',gameplay_verified:false};
const source={schema_version:'legaia.npc-script-reset-source.v1',entity_id:id,scene_id:draft.scene_id,project_source_key:key,draft,families:families.map(f=>({id:f,owned_count:['waits','facing'].includes(f)?1:0})),...scope};
const request={entity_id:id,families:['waits','facing']},proposed=structuredClone(draft);delete proposed.waits;delete proposed.facing;
const review={schema_version:'legaia.npc-script-reset-review.v1',entity_id:id,project_source_key:key,request,current:draft,proposed,removed:source.families.filter(r=>request.families.includes(r.id)),review_key:key,...scope};
decodeNpcScriptResetSource(source,id,state);const result=decodeNpcScriptResetReview(review,request,source,state);result.proposed.name='Detached';assert.equal(review.proposed.name,'NPC');
for(const mutate of [v=>v.proposed.position.x=192,v=>v.proposed.donor_entity_id='scene://other',v=>v.proposed.facing=draft.facing,v=>v.removed[0].owned_count=99,v=>v.runtime_binding='confirmed',v=>v.native_byte_preview=true,v=>v.project_source_key='b'.repeat(64),v=>v.extra='invented']){const bad=structuredClone(review);mutate(bad);assert.throws(()=>decodeNpcScriptResetReview(bad,request,source,state));}
assert.throws(()=>decodeNpcScriptResetReview(review,{entity_id:id,families:['facing','waits']},source,state));
if(process.argv[2]){const v=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));decodeNpcScriptResetSource(v.source,v.request.entity_id,v.state);decodeNpcScriptResetReview(v.review,v.request,v.source,v.state);}
console.log('NPC reset client: exact selected-family removal, preserved identity/placement, source freshness, detached results and native/live claim rejection passed.');
