import assert from 'node:assert/strict';
import {decodeNpcFlagsSource,decodeNpcFlagsReview} from '../editor/npc-flags.js';
const id='authored-actor://00000000-0000-4000-8000-000000000001',owner='scene://town01/actors/man-p1/0040',flags='script://town01/actors/man-p1/0040/flag-bit/0065',key='a'.repeat(64),draft={scene_id:'scene://town01',donor_entity_id:owner,name:'Resident',position:{x:128,z:256},appearance:{script_donor_entity_id:owner,donor_entity_id:'scene://town01/actors/man-p1/0012'}},state={scene:{id:draft.scene_id},actor_drafts:{[id]:draft},project_copy_source_key:key};
const target={semantic_id:flags,owner_id:owner,pc:101,mnemonic:'GFLAG_SET',target_context:null,before_raw:227,preservation_mask:224,maximum:31,values:{bit:3},authored_values:null,effective_values:{bit:3},source_record_sha256:'b'.repeat(64)},source={schema_version:'legaia.npc-flags-source.v1',entity_id:id,scene_id:draft.scene_id,draft,project_source_key:key,options:{supported:true,targets:[target]},gameplay_verified:false,runtime_variable_identity:'not_asserted',story_meaning:'not_asserted'};
assert.deepEqual(decodeNpcFlagsSource(source,id,state),source);
const request={entity_id:id,entries:{[flags]:{bit:7}}},review={schema_version:'legaia.npc-flags-review.v1',entity_id:id,project_source_key:key,request,current:draft,proposed:{...draft,flags:{donor_entity_id:owner,entries:request.entries}},review_key:'c'.repeat(64),gameplay_verified:false,runtime_variable_identity:'not_asserted',story_meaning:'not_asserted'};
assert.deepEqual(decodeNpcFlagsReview(review,request,source,state),review);
for(const mutate of [v=>v.project_source_key='d'.repeat(64),v=>v.options.targets[0].owner_id='wrong',v=>v.options.targets[0].effective_values.bit=33,v=>v.options.targets[0].values.bit=32768,v=>v.draft.name='Wrong']){const v=structuredClone(source);mutate(v);assert.throws(()=>decodeNpcFlagsSource(v,id,state));}
for(const mutate of [v=>v.proposed.donor_entity_id='wrong',v=>v.proposed.appearance.donor_entity_id='wrong',v=>v.proposed.position.x++,v=>v.proposed.flags.entries[flags].bit=32]){const v=structuredClone(review);mutate(v);assert.throws(()=>decodeNpcFlagsReview(v,request,source,state));}
for(const ticks of [true,-1,32,1.5,NaN])assert.throws(()=>decodeNpcFlagsReview(review,{entity_id:id,entries:{[flags]:{bit:ticks}}},source,state));
const detached=decodeNpcFlagsReview(review,request,source,state);detached.proposed.name='Detached';assert.equal(review.proposed.name,'Resident');
console.log('NPC flags owner/source/typed target/stale review and retained appearance/placement contracts pass.');


for(const mutate of [v=>v.options.targets[0].preservation_mask=31,v=>v.options.targets[0].maximum=15,v=>v.options.targets[0].before_raw=224,v=>v.options.targets[0].target_context=256,v=>v.options.targets[0].mnemonic='GFLAG_BRANCH',v=>v.story_meaning='known']){const v=structuredClone(source);mutate(v);assert.throws(()=>decodeNpcFlagsSource(v,id,state));}
for(const [mnemonic,maximum,bit] of [['LFLAG_SET',15,16],['CFLAG_SET',31,8],['CFLAG_CLEAR',31,10]]){const local=structuredClone(source);Object.assign(local.options.targets[0],{mnemonic,maximum});assert.deepEqual(decodeNpcFlagsSource(local,id,state),local);assert.throws(()=>decodeNpcFlagsReview(review,{entity_id:id,entries:{[flags]:{bit}}},local,state));}
console.log('NPC flag widths, special side effects, dispatch and upper masks pass.');
