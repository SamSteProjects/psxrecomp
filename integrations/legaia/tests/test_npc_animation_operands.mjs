import assert from 'node:assert/strict';
import fs from 'node:fs';
import {decodeNpcAnimationOperandSource,decodeNpcAnimationOperandReview,npcAnimationOperandRequest,npcCurrentAnimationSelection} from '../editor/npc-animation-operands.js';
import {decodeNpcCurrentScript} from '../editor/npc-current-script.js';
const path=process.env.LEGAIA_NPC_ANIMATION_EDITOR_CONTRACT;
if(!path){console.log('Private NPC animation editor contract not supplied; skipped.');process.exit(0);}
const fixture=JSON.parse(fs.readFileSync(path,'utf8')), {entity_id:id,target_id:target,values,state,source,review,current}=fixture;
assert.deepEqual(decodeNpcAnimationOperandSource(source,id,state),source);
assert.deepEqual(await decodeNpcCurrentScript(current,id,state),current);
const accepted=await decodeNpcAnimationOperandReview(review,source,target,values,state);
assert.equal(accepted.review.review_key,review.review_key);
assert.deepEqual(npcAnimationOperandRequest(source,target,values),review.request);
assert.equal(npcCurrentAnimationSelection(current,source,source.options.targets[0].pc,state).animation_operand_id,target);
const reset=npcAnimationOperandRequest(source,target,null);assert.equal(reset.entries[target],undefined);
for(const change of [v=>v.draft.name='Changed',v=>v.project_source_key='0'.repeat(64),v=>v.options.targets[0].owner_id='foreign',v=>v.options.targets[0].values.animation_operand=true,v=>v.options.targets[0].raw_instruction_hex='003001',v=>v.options.targets[0].source_record_sha256='invalid',v=>v.options.targets.push(v.options.targets[0])]){const value=structuredClone(source);change(value);assert.throws(()=>decodeNpcAnimationOperandSource(value,id,state));}
for(const change of [v=>v.proposed.position.x++,v=>v.request.entries[target].animation_operand++,v=>v.review_key='invalid',v=>v.current_inspection.record.sha256='0'.repeat(64),v=>v.proposed_inspection.record.raw_hex='00'+v.proposed_inspection.record.raw_hex.slice(2),v=>v.proposed_inspection.record.byte_offset++,v=>v.proposed_inspection.actor_semantic_id='foreign',v=>v.proposed_inspection.instructions[0].successors=[999]]){const value=structuredClone(review);change(value);await assert.rejects(()=>decodeNpcAnimationOperandReview(value,source,target,values,state));}
await assert.rejects(()=>decodeNpcAnimationOperandReview(review,source,target,{animation_operand:256},state));
assert.throws(()=>npcCurrentAnimationSelection(current,source,source.options.targets[0].pc,{...state,project:{...state.project,mode:'live'}}));
const forged=structuredClone(current);forged.inspection.instructions.find(n=>n.pc===source.options.targets[0].pc).raw_hex='343000';assert.throws(()=>npcCurrentAnimationSelection(forged,source,source.options.targets[0].pc,state));
console.log('Actual Retail NPC source/Review/Current navigation, request isolation, reset and 18 forged/stale/native-bound refusals passed.');
