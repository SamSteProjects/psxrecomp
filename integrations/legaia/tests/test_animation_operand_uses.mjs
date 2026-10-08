import assert from 'node:assert/strict';
import fs from 'node:fs';
import {decodeAnimationOperandUses} from '../editor/script-animation-operands.js';
const {source,id,report,bounded_source,bounded_report}=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
assert.equal(decodeAnimationOperandUses(report,source,id).match_count,report.match_count);
let refused=0;
for(const mutate of [v=>v.state_key='0'.repeat(64),v=>v.gameplay_verified=true,v=>v.identity_resolution='model',v=>v.query_values.animation_operand=255,v=>v.rows[0].target.raw_instruction_hex='ff',v=>v.rows[0].retail_match=!v.rows[0].retail_match,v=>v.rows[0].entity_id='foreign',v=>v.rows.push(v.rows[0]),v=>v.match_count++,v=>v.truncated=true]){
 const bad=structuredClone(report);mutate(bad);assert.throws(()=>decodeAnimationOperandUses(bad,source,id));refused++;
}
const detached=decodeAnimationOperandUses(report,source,id);detached.rows[0].target.effective_values.animation_operand=123;assert.notDeepEqual(detached,report);
assert.equal(decodeAnimationOperandUses(bounded_report,bounded_source,id).rows.length,256);
console.log(`Native argument usage matches, detached results and ${refused} forged response refusals passed.`);
