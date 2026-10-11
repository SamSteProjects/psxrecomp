import fs from 'node:fs';import assert from 'node:assert/strict';
import {qualifyWorldScriptOperands,qualifyWorldScriptReview} from '../editor/world-script-animation-operands.js';
const source=JSON.parse(fs.readFileSync(process.argv[2])),review=JSON.parse(fs.readFileSync(process.argv[3]));
const record={id:source.script_id,kind:'script',source_record:source.source_record,source_instance_ids:source.source_instance_ids,entry_pc:source.entry_pc};
const qualified=await qualifyWorldScriptOperands(source,record,source.source_key,source.project_path),target=qualified.targets.find(t=>t.pc===review.pc);
assert.equal(target.mnemonic,'SYSFLAG_TEST');assert.equal(review.proposed_values.index,4095);
qualifyWorldScriptReview(review,qualified,target,review.proposed_values,review.shared);
const retail=Buffer.from(source.record_base64,'base64');
for(const index of [0,255,256,4095]){
 const current=structuredClone(source),t=current.targets.find(t=>t.pc===review.pc),raw=Buffer.from(current.current_record_base64,'base64');
 raw[t.pc]=(retail[t.pc]&240)|(index>>8);raw[t.pc+1]=index&255;current.current_record_base64=raw.toString('base64');t.authored_values=t.current_values={index};
 await qualifyWorldScriptOperands(current,record,source.source_key,source.project_path);
 assert.equal(raw[t.pc]&240,retail[t.pc]&240);assert.deepEqual(raw.subarray(t.pc+2,t.pc+4),retail.subarray(t.pc+2,t.pc+4));
}
let refusals=0;
for(const value of [-1,4096,true]){
 const bad=structuredClone(source),t=bad.targets.find(t=>t.pc===review.pc);t.authored_values=t.current_values={index:value};
 await assert.rejects(()=>qualifyWorldScriptOperands(bad,record,source.source_key,source.project_path));refusals++;
}
for(const change of [v=>v.targets.find(t=>t.pc===review.pc).pc++,v=>v.targets.find(t=>t.pc===review.pc).target_context=7,v=>v.targets.push(v.targets[0]),v=>{const raw=Buffer.from(v.current_record_base64,'base64');raw[target.pc]^=16;v.current_record_base64=raw.toString('base64');},v=>{const raw=Buffer.from(v.current_record_base64,'base64');raw[target.pc+2]^=1;v.current_record_base64=raw.toString('base64');}]){
 const bad=structuredClone(source);change(bad);await assert.rejects(()=>qualifyWorldScriptOperands(bad,record,source.source_key,source.project_path));refusals++;
}
for(const change of [v=>v.proposed_values.index=4096,v=>v.proposed_values.index=-1,v=>v.changes[0].decoded_byte_offset++,v=>v.changes[0].after_byte^=16,v=>v.changes.push({decoded_byte_offset:source.source_record.byte_offset+target.pc+2,before_byte:retail[target.pc+2],after_byte:retail[target.pc+2]^1}),v=>v.no_op=true,v=>v.gameplay_verified=true,v=>v.compression.new_encoded_size=v.compression.original_encoded_size+1]){
 const bad=structuredClone(review);change(bad);assert.throws(()=>qualifyWorldScriptReview(bad,qualified,target,review.proposed_values,review.shared));refusals++;
}
console.log(`Actual system selector source/Review and four Current witnesses qualified; ${refusals} altered source/Review refusals passed.`);
