import assert from 'node:assert/strict';
import fs from 'node:fs';
import {decodeOperandReview,operandFileSchema} from '../editor/script-operand-files.js';
import {decodeOperandBundleReview} from '../editor/script-operand-bundle.js';
const evidence=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const {file,file_review,bundle,bundle_review}=evidence;
assert.equal(operandFileSchema(file.components),'legaia.script-operand-file.v2');
assert.equal(operandFileSchema({ScriptFlags:{entries:{}}}),'legaia.script-operand-file.v1');
assert.equal(decodeOperandReview(file_review,file,file.owner_id,file.scene_id).change_count,1);
assert.equal(decodeOperandBundleReview(bundle_review,bundle,bundle.scene_id).change_count,2);
for(const schema_version of ['legaia.script-operand-file.v1','unknown'])assert.throws(()=>decodeOperandReview(file_review,{...file,schema_version},file.owner_id,file.scene_id));
for(const schema_version of ['legaia.script-operand-bundle.v1','unknown'])assert.throws(()=>decodeOperandBundleReview(bundle_review,{...bundle,schema_version},bundle.scene_id));
for(const mutate of [v=>v.entries[0].after.animation_operand=256,v=>v.owner_id='other',v=>v.source_import_sha256='0'.repeat(64),v=>v.entries[0].component='Unknown']){
  const bad=structuredClone(file_review);mutate(bad);assert.throws(()=>decodeOperandReview(bad,file,file.owner_id,file.scene_id));
}
const detached=decodeOperandBundleReview(bundle_review,bundle,bundle.scene_id);
detached.owners[0].entries[0].after.animation_operand=0;
assert.notDeepEqual(detached,bundle_review);
const mixed=structuredClone(file),mixedReview=structuredClone(file_review);
mixed.components.ScriptBranches={entries:{branch:{destination_pc:16}}};
mixed.components.ScriptWaits={entries:{wait:{duration_ticks:2}}};
mixedReview.entries.push({component:'ScriptWaits',operand_id:'wait',before:null,after:{duration_ticks:2},changed:true},{component:'ScriptBranches',operand_id:'branch',before:null,after:{destination_pc:16},changed:true});
mixedReview.change_count=3;
assert.equal(decodeOperandReview(mixedReview,mixed,mixed.owner_id,mixed.scene_id).change_count,3);
console.log('Actual Retail P1/P2 v2 transfer contracts, schema selection, forged review refusal and detached state passed.');
