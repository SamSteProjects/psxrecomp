import assert from 'node:assert/strict';
import fs from 'node:fs';
import {decodeSceneController} from '../editor/scene-controller.js';
const r=JSON.parse(fs.readFileSync(process.env.LEGAIA_CONTROLLER_EVIDENCE)),scene=r.scene_id,key=r.source_key;
const report=decodeSceneController(r,scene,key);assert.equal(report.entry_pc,17);assert.deepEqual(report.instructions.map(n=>n.mnemonic),['NOP','JMP_REL']);report.record.local_count=0;assert.notEqual(r.record.local_count,0);
let refusals=0;
for(const change of [v=>v.scene_id='scene://foreign',v=>v.source_key='0'.repeat(64),v=>v.semantic_id='script://actor',v=>v.read_only=false,v=>v.representation='live',v=>v.runtime_execution='confirmed',v=>v.source_record.record_index=1,v=>v.source_record.byte_offset=v.source_record.containing_decoded_size,v=>v.record.script_offset=0,v=>v.entry_pc=1,v=>v.record.local_count=256,v=>v.record.raw_hex='00',v=>v.instructions=Array(4097).fill({}),v=>v.dialogues=null]){const forged=structuredClone(r);change(forged);assert.throws(()=>decodeSceneController(forged,scene,key));refusals++;}
console.log(`Controller source contract passed; ${refusals} forged records refused.`);
