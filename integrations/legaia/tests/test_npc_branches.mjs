import assert from 'node:assert/strict';
import {decodeNpcBranchesSource,decodeNpcBranchesReview,openNpcBranches} from '../editor/npc-branches.js';
const id='authored-actor://00000000-0000-4000-8000-000000000001',owner='scene://town01/actors/man-p1/0040',branches='script://town01/actors/man-p1/0040/branch/0065',key='a'.repeat(64),draft={scene_id:'scene://town01',donor_entity_id:owner,name:'Resident',position:{x:128,z:256},appearance:{script_donor_entity_id:owner,donor_entity_id:'scene://town01/actors/man-p1/0012'}},state={scene:{id:draft.scene_id},actor_drafts:{[id]:draft},project_copy_source_key:key};
const target={semantic_id:branches,owner_id:owner,pc:101,mnemonic:'JMP_REL',target_context:null,operand_pc:102,width:2,values:{target_pc:3},authored_values:null,effective_values:{target_pc:3},source_record_sha256:'b'.repeat(64)},source={schema_version:'legaia.npc-branches-source.v1',entity_id:id,scene_id:draft.scene_id,draft,project_source_key:key,options:{supported:true,targets:[target],destinations:[{pc:3,mnemonic:'NOP'},{pc:7,mnemonic:'NOP'}]},gameplay_verified:false,runtime_termination:'not_asserted',story_meaning:'not_asserted'};
assert.deepEqual(decodeNpcBranchesSource(source,id,state),source);
const request={entity_id:id,entries:{[branches]:{target_pc:7}}},review={schema_version:'legaia.npc-branches-review.v1',entity_id:id,project_source_key:key,request,current:draft,proposed:{...draft,branches:{donor_entity_id:owner,entries:request.entries}},review_key:'c'.repeat(64),gameplay_verified:false,runtime_termination:'not_asserted',story_meaning:'not_asserted'};
assert.deepEqual(decodeNpcBranchesReview(review,request,source,state),review);
for(const mutate of [v=>v.project_source_key='d'.repeat(64),v=>v.options.targets[0].owner_id='wrong',v=>v.options.targets[0].effective_values.target_pc=33,v=>v.options.targets[0].values.target_pc=32768,v=>v.draft.name='Wrong']){const v=structuredClone(source);mutate(v);assert.throws(()=>decodeNpcBranchesSource(v,id,state));}
for(const mutate of [v=>v.proposed.donor_entity_id='wrong',v=>v.proposed.appearance.donor_entity_id='wrong',v=>v.proposed.position.x++,v=>v.proposed.branches.entries[branches].target_pc=32]){const v=structuredClone(review);mutate(v);assert.throws(()=>decodeNpcBranchesReview(v,request,source,state));}
for(const ticks of [true,-1,32768,1.5,NaN,8])assert.throws(()=>decodeNpcBranchesReview(review,{entity_id:id,entries:{[branches]:{target_pc:ticks}}},source,state));
const detached=decodeNpcBranchesReview(review,request,source,state);detached.proposed.name='Detached';assert.equal(review.proposed.name,'Resident');
console.log('NPC branches owner/source/typed target/stale review and retained appearance/placement contracts pass.');



for(const mutate of [v=>v.options.destinations.push(v.options.destinations[0]),v=>v.options.destinations[0].pc=32768,v=>v.options.targets[0].width=1,v=>v.options.targets[0].operand_pc=101,v=>v.options.targets[0].target_context=256,v=>{v.options.targets[0].mnemonic='SYSFLAG_TEST';v.options.targets[0].target_context=7;}]){const v=structuredClone(source);mutate(v);assert.throws(()=>decodeNpcBranchesSource(v,id,state));}
console.log('NPC branch destinations are bounded, unique source boundaries; target word width and supported dispatch are held.');

assert.equal(typeof openNpcBranches,'function');
