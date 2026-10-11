import fs from 'node:fs';import assert from 'node:assert/strict';
import {qualifyWorldScriptOperands,qualifyWorldScriptReview} from '../editor/world-script-animation-operands.js';
const source=JSON.parse(fs.readFileSync(process.argv[2])),review=JSON.parse(fs.readFileSync(process.argv[3]));
const record={id:source.script_id,kind:'script',source_record:source.source_record,source_instance_ids:source.source_instance_ids,entry_pc:source.entry_pc};
const qualified=await qualifyWorldScriptOperands(source,record,source.source_key,source.project_path),target=qualified.targets.find(t=>t.pc===review.pc);
assert.equal(target.mnemonic,'CFLAG_SET');qualifyWorldScriptReview(review,qualified,target,review.proposed_values,review.shared);
const relative=target.pc+(target.target_context===null?1:2),retail=Buffer.from(source.record_base64,'base64');
assert.equal(review.changes.length,1);assert.equal(review.changes[0].before_byte&224,review.changes[0].after_byte&224);
for(const bit of [0,3,7,9,31]){
 const current=structuredClone(source),t=current.targets.find(t=>t.pc===review.pc),raw=Buffer.from(current.current_record_base64,'base64');
 raw[relative]=(retail[relative]&224)|bit;current.current_record_base64=raw.toString('base64');t.authored_values=t.current_values={bit};
 await qualifyWorldScriptOperands(current,record,source.source_key,source.project_path);
}
let refusals=0;
for(const value of [8,-1,32,true]){
 const bad=structuredClone(source),t=bad.targets.find(t=>t.pc===review.pc);t.authored_values=t.current_values={bit:value};
 await assert.rejects(()=>qualifyWorldScriptOperands(bad,record,source.source_key,source.project_path));refusals++;
}
for(const change of [v=>v.targets.find(t=>t.pc===review.pc).pc++,v=>v.targets.find(t=>t.pc===review.pc).target_context=7,v=>v.targets.push(v.targets[0]),v=>{const raw=Buffer.from(v.current_record_base64,'base64');raw[relative]^=32;v.current_record_base64=raw.toString('base64');}]){
 const bad=structuredClone(source);change(bad);await assert.rejects(()=>qualifyWorldScriptOperands(bad,record,source.source_key,source.project_path));refusals++;
}
for(const change of [v=>v.proposed_values.bit=8,v=>v.proposed_values.bit=32,v=>v.changes[0].decoded_byte_offset++,v=>v.changes[0].after_byte^=32,v=>v.changes.push({decoded_byte_offset:0,before_byte:0,after_byte:1}),v=>v.no_op=true,v=>v.gameplay_verified=true,v=>v.compression.new_encoded_size=v.compression.original_encoded_size+1]){
 const bad=structuredClone(review);change(bad);assert.throws(()=>qualifyWorldScriptReview(bad,qualified,target,review.proposed_values,review.shared));refusals++;
}
console.log(`Actual masked flag source/Review and five Current witnesses qualified; ${refusals} altered source/Review refusals passed.`);
