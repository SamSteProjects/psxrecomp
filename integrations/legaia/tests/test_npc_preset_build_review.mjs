import assert from 'node:assert/strict';
import {decodeNpcPresetBuildReview} from '../editor/npc-preset-build-review.js';
const key='a'.repeat(64),accepted={review_key:'b'.repeat(64),draft:{name:'Resident',position:{x:128,z:256},waits:{fixture:true}}};
const build={schema_version:'legaia.build-review.v2',source_key:key,read_only:true,status:'blocked',normal_build_ready:false,blockers:[{kind:'serialization',owner_id:null,message:'Existing unsupported height'}],excluded_npc_draft_count:0,included_npc_draft_count:2,assessment:null,assessment_scope:'all_supported_authored_content_including_source_qualified_npc_drafts',npc_build_scope:'qualified_man_source_candidates',npc_gameplay_verified:false,limitations:['Gameplay unverified']};
const value={schema_version:'legaia.npc-preset-build-review.v1',review:accepted,prospective_build_source_key:key,build_review:build,existing_npc_draft_count:1,proposed_npc_draft_count:2,read_only:true,project_changed:false,output_written:false,gameplay_verified:false,assessment_scope:'complete_supported_project_with_one_preset_instance'};
assert.deepEqual(decodeNpcPresetBuildReview(value,accepted,1),value);
const detached=decodeNpcPresetBuildReview(value,accepted,1);detached.review.draft.name='Changed';assert.equal(accepted.draft.name,'Resident');
for(const change of [v=>v.review.draft.waits.fixture=false,v=>v.review.review_key='c'.repeat(64),v=>v.proposed_npc_draft_count=1,v=>v.build_review.included_npc_draft_count=1,v=>v.build_review.source_key='d'.repeat(64),v=>v.output_written=true,v=>v.gameplay_verified=true,v=>v.read_only=false]){const bad=structuredClone(value);change(bad);assert.throws(()=>decodeNpcPresetBuildReview(bad,accepted,1));}
assert.throws(()=>decodeNpcPresetBuildReview(value,accepted,0));
console.log('Preset Build review binds the entire accepted preset, full project NPC coverage and no-output/no-gameplay scope.');
