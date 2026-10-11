import fs from 'node:fs';import assert from 'node:assert/strict';
import {qualifyWorldScriptOperands,qualifyWorldScriptReview} from '../editor/world-script-animation-operands.js';
const source=JSON.parse(fs.readFileSync(process.argv[2])),review=JSON.parse(fs.readFileSync(process.argv[3]));
const record={id:source.script_id,kind:'script',source_record:source.source_record,source_instance_ids:source.source_instance_ids,entry_pc:source.entry_pc};
const qualified=await qualifyWorldScriptOperands(source,record,source.source_key,source.project_path),target=qualified.targets.find(t=>t.pc===review.pc);
assert.equal(target.mnemonic,'SET_ACTOR_MODEL');assert.equal(review.proposed_values.model_selector_signed,240);
qualifyWorldScriptReview(review,qualified,target,review.proposed_values,review.shared);
for(const value of [-32768,-1,239,240,32767]){
 const current=structuredClone(source),t=current.targets.find(t=>t.pc===review.pc),raw=Buffer.from(current.current_record_base64,'base64'),at=t.pc+(t.target_context===null?1:2)+1;
 raw.writeInt16LE(value,at);current.current_record_base64=raw.toString('base64');t.authored_values=t.current_values={model_selector_signed:value};
 await qualifyWorldScriptOperands(current,record,source.source_key,source.project_path);
}
let refusals=0;
for(const change of [v=>v.targets[0].retail_values.model_selector_signed=-32769,v=>v.targets[0].retail_values.model_selector_signed=true,v=>v.targets[0].retail_values.model_selector_signed=32768,v=>v.targets[0].pc++,v=>v.targets[0].target_context=7,v=>v.targets[0].authored_values={model_selector_signed:32768},v=>v.current_record_base64=v.record_base64.slice(4),v=>v.targets.push(v.targets[0])]){
 const bad=structuredClone(source);change(bad);await assert.rejects(()=>qualifyWorldScriptOperands(bad,record,source.source_key,source.project_path));refusals++;
}
for(const change of [v=>v.proposed_values.model_selector_signed=32768,v=>v.proposed_values.model_selector_signed=-32769,v=>v.changes[0].decoded_byte_offset++,v=>v.changes[0].after_byte^=1,v=>v.changes.push({decoded_byte_offset:0,before_byte:0,after_byte:1}),v=>v.no_op=true,v=>v.gameplay_verified=true,v=>v.compression.new_encoded_size=v.compression.original_encoded_size+1]){
 const bad=structuredClone(review);change(bad);assert.throws(()=>qualifyWorldScriptReview(bad,qualified,target,review.proposed_values,review.shared));refusals++;
}
console.log(`Actual model-selector source/Review and five signed Current witnesses qualified; ${refusals} altered source/Review refusals passed.`);
