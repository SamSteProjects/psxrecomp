import assert from 'node:assert/strict';
import {decodeOperandReview} from '../editor/script-operand-files.js';
const owner='scene://town01/actors/man-p1/0003',scene='scene://town01',hash='a'.repeat(64),key='script://town01/actors/man-p1/0003/model-selector/000c';
const file={schema_version:'legaia.script-operand-file.v1',scene_id:scene,owner_id:owner,source_import_sha256:hash,components:{ScriptModelSelectors:{entries:{[key]:{model_selector_signed:239}}}}};
const value={schema_version:'legaia.script-operand-review.v1',owner_id:owner,scene_id:scene,source_import_sha256:hash,review_key:'b'.repeat(64),change_count:1,entries:[{component:'ScriptModelSelectors',operand_id:key,before:{model_selector_signed:240},after:{model_selector_signed:239},changed:true}]};
const decoded=decodeOperandReview(value,file,owner,scene);decoded.entries[0].after.model_selector_signed=0;assert.equal(value.entries[0].after.model_selector_signed,239);
for(const mutate of [v=>v.owner_id='other',v=>v.scene_id='other',v=>v.source_import_sha256='c'.repeat(64),v=>v.change_count=0,v=>v.entries.push(v.entries[0]),v=>v.entries[0].after.model_selector_signed=238,v=>v.entries[0].component='write_ram']){const bad=structuredClone(value);mutate(bad);assert.throws(()=>decodeOperandReview(bad,file,owner,scene));}
console.log('Operand file scene/source/owner, exact reviewed entries, duplicate/count and detached review guards passed.');
