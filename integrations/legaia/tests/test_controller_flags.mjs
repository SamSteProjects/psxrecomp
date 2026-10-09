import assert from 'node:assert/strict';
import fs from 'node:fs';
import {decodeControllerFlags} from '../editor/controller-flags.js';
import {decodeSceneController} from '../editor/scene-controller.js';
const report=JSON.parse(fs.readFileSync(process.env.LEGAIA_CONTROLLER_FLAG_EVIDENCE));
const rows=decodeControllerFlags(report);
assert.equal(rows.length,122);
assert.equal(rows.filter(row=>row.bank==='context').length,1);
assert(rows.every(row=>row.runtime_value===null));
rows[0].index++;assert.notEqual(rows[0].index,report.flag_references[0].index);
let refusals=0;
for(const mutate of [v=>v.flag_reference_count++,v=>{v.flag_references.pop();v.flag_reference_count--;},v=>v.flag_references[0].pc++,v=>v.flag_references[0].byte_offset++,v=>v.flag_references[0].index++,v=>v.flag_references[0].runtime_value=1,v=>v.flag_references[0].scope='live',v=>v.flag_references[0].extended_target=1,v=>v.flag_references[0].operation='unknown',v=>v.flag_references[0].extra=true,v=>v.flag_references[1]=structuredClone(v.flag_references[0]),v=>v.flag_references[0].status='confirmed',v=>v.flag_references[0].bank='global']){const bad=structuredClone(report);mutate(bad);assert.throws(()=>decodeControllerFlags(bad));assert.throws(()=>decodeSceneController(bad,bad.scene_id,bad.source_key));refusals++;}
console.log(`122 Town01 controller flag operands qualified; ${refusals} forged inventories refused.`);
