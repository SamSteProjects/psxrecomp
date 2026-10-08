import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {decodeAnimationOperandSource,decodeAnimationOperandReview} from '../editor/script-animation-operands.js';
const path=process.argv[2];if(!path)throw new Error('Fresh source/Review contract fixture required.');
const fixtures=JSON.parse(readFileSync(path,'utf8'));
let refusals=0;
for(const fixture of fixtures){
 const {owner,id,values}=fixture,key=fixture.source.state_key;
 const source=decodeAnimationOperandSource(fixture.source,owner,key);
 const result=decodeAnimationOperandReview(fixture.review,source,id,values);
 assert.deepEqual(result.review.values,values);assert.equal(result.gameplay_verified,false);
 result.review.values[Object.keys(values)[0]]=0;assert.deepEqual(fixture.review.review.values,values);
 const sourceMutations=[v=>v.owner_id='scene://foreign/actors/man-p1/0001',v=>v.state_key='0'.repeat(64),v=>v.gameplay_verified=true,v=>v.targets.push(structuredClone(v.targets[0])),v=>v.targets[0].values[Object.keys(v.targets[0].values)[0]]=true,v=>v.targets[0].effective_values[Object.keys(v.targets[0].values)[0]]=-1,v=>v.targets[0].raw_instruction_hex='ff'+v.targets[0].raw_instruction_hex.slice(2),v=>v.targets[0].semantic_id+='0',v=>v.targets[0].decoded_byte_offset=0,v=>v.source.reference_commit='0'.repeat(40)];
 for(const mutate of sourceMutations){const v=structuredClone(fixture.source);mutate(v);assert.throws(()=>decodeAnimationOperandSource(v,owner,key));refusals++;}
 const reviewMutations=[v=>v.review.values[Object.keys(values)[0]]^=1,v=>v.review.review_key='bad',v=>v.state_key='0'.repeat(64),v=>v.target.pc++,v=>v.review.proposed_instruction_hex='ff'+v.review.proposed_instruction_hex.slice(2),v=>v.review.changed_byte_offsets=[],v=>v.review.no_op=true,v=>v.review.current_record_sha256='bad',v=>v.proposed_report.instructions[0].length++,v=>v.proposed_report.entry_pc++,v=>v.source.decoded_man_sha256='0'.repeat(64),v=>v.review.current_instruction_hex=v.review.proposed_instruction_hex];
 for(const mutate of reviewMutations){const v=structuredClone(fixture.review);mutate(v);assert.throws(()=>decodeAnimationOperandReview(v,source,id,values));refusals++;}
}
assert.equal(fixtures.length,2);console.log(`Animation operand contracts passed for P1/P2; ${refusals} forged source/Review refusals.`);
