import assert from 'node:assert/strict';
import {decodeDraftRepeatGroup} from '../editor/draft-repeat.js';
const ids=['authored-actor://11111111-1111-4111-8111-111111111111','authored-actor://22222222-2222-4222-8222-222222222222'];
const sources=Object.fromEntries(ids.map((id,i)=>[id,{scene_id:'scene',name:'Member '+i,donor_entity_id:'donor'+i,position:{x:i*256,z:128}}]));
const request={entity_ids:ids,count:1,step:{x:64,z:128}},state={scene:{id:'scene'},project_copy_source_key:'source',actor_drafts:sources};
const report={schema_version:'legaia.draft-repeat-group.v1',scene_id:'scene',project_source_key:'source',source_drafts:structuredClone(sources),request:structuredClone(request),review_key:'a'.repeat(64),limitations:['Gameplay unverified.'],copies:ids.map((id,i)=>({entity_id:`authored-actor://${i+3}${'3'.repeat(7)}-3333-4333-8333-333333333333`,source_entity_id:id,copy_index:1,draft:{...structuredClone(sources[id]),name:`Member ${i} copy 001`,position:{x:i*256+64,z:256}}}))};
const accepted=decodeDraftRepeatGroup(report,request,state);accepted.copies[0].draft.name='Detached';assert.equal(report.copies[0].draft.name,'Member 0 copy 001');
for(const change of [r=>r.project_source_key='stale',r=>r.copies[0].draft.position.x+=64,r=>r.copies[1].draft.donor_entity_id='donor0',r=>r.copies[1].source_entity_id=ids[0],r=>r.copies[1].entity_id=r.copies[0].entity_id,r=>r.source_drafts[ids[0]].name='Changed',r=>r.copies.pop()]){const bad=structuredClone(report);change(bad);assert.throws(()=>decodeDraftRepeatGroup(bad,request,state));}
console.log('NPC arrangement member-specific donors, relative positions, identity, stale source and detached report checks pass.');

const reordered=structuredClone(report);reordered.request={step:request.step,count:request.count,entity_ids:ids};assert.doesNotThrow(()=>decodeDraftRepeatGroup(reordered,request,state));
