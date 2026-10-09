import assert from 'node:assert/strict';
import fs from 'node:fs';
import {decodeControllerFlagBitSnapshot} from '../editor/controller-flag-bits.js';
const fixture=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),{raw,owner,context}=fixture,before=structuredClone(raw);
const value=decodeControllerFlagBitSnapshot(raw,owner,context);assert.equal(value.targets[0].current_values.bit,31);value.targets[0].values.bit=10;assert.deepEqual(raw,before);
for(const mutate of [r=>r.owner_id='foreign',r=>r.state_key='f'.repeat(64),r=>r.targets[0].semantic_id='foreign',r=>r.targets[0].current_values.bit=30,r=>r.targets[0].preserved_bits=0,r=>r.current_report.instructions[0].raw_hex='2fff',r=>r.targets[0].decoded_byte_offset++]){const r=structuredClone(raw);mutate(r);assert.throws(()=>decodeControllerFlagBitSnapshot(r,owner,context));}
console.log('Controller flag-bit snapshot byte qualification, authored layers, detachment and malformed-source refusal passed.');
