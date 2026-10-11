import fs from 'node:fs';import assert from 'node:assert/strict';
import {qualifyWorldScriptOperands,qualifyWorldScriptReview} from '../editor/world-script-animation-operands.js';
const [optionsPath,reviewPath]=process.argv.slice(2),source=JSON.parse(fs.readFileSync(optionsPath)),review=JSON.parse(fs.readFileSync(reviewPath));
const record={id:source.script_id,kind:'script',source_record:source.source_record,source_instance_ids:source.source_instance_ids,entry_pc:source.entry_pc};
const qualified=await qualifyWorldScriptOperands(source,record,source.source_key,source.project_path),target=qualified.targets.find(t=>t.pc===review.pc);
assert.equal(target.mnemonic,'EFFECT_COLOR_INTENSITY');assert.equal(review.proposed_values.intensity,-32768);
qualifyWorldScriptReview(review,qualified,target,review.proposed_values,review.shared);
let refusals=0;
for(const change of [v=>v.targets[0].retail_values.intensity=-32769,v=>v.targets[0].retail_values.red=true,v=>v.targets[0].retail_values.blue=256,v=>v.targets[0].pc++,v=>v.targets[0].target_context=7,v=>v.targets[0].authored_values={red:0,green:0,blue:0,intensity:32768},v=>v.current_record_base64=v.record_base64.slice(4),v=>v.targets.push(v.targets[0])]){
 const bad=structuredClone(source);change(bad);await assert.rejects(()=>qualifyWorldScriptOperands(bad,record,source.source_key,source.project_path));refusals++;
}
for(const change of [v=>v.proposed_values.intensity=32768,v=>v.proposed_values.red=-1,v=>v.changes[0].decoded_byte_offset++,v=>v.changes[0].after_byte^=1,v=>v.changes.push({decoded_byte_offset:0,before_byte:0,after_byte:1}),v=>v.no_op=true,v=>v.gameplay_verified=true,v=>v.compression.new_encoded_size=v.compression.original_encoded_size+1]){
 const bad=structuredClone(review);change(bad);assert.throws(()=>qualifyWorldScriptReview(bad,qualified,target,review.proposed_values,review.shared));refusals++;
}
console.log(`Actual effect-color bytes and signed Review qualified; ${refusals} altered source/Review refusals passed.`);
