import fs from 'node:fs';
import assert from 'node:assert/strict';
import {decodeReplacementOptions,decodeReplacementAuthoring} from '../editor/sequence-replacement-authoring.js';
const f=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),o=f.options,v=f.review,bytes=new Uint8Array(fs.readFileSync(process.argv[3])),context={assetId:o.asset_id,authoringKey:o.authoring_key,entryHash:o.source_record.entry_sha256,sceneId:'scene://town01'};
decodeReplacementOptions(o,context);const decode=r=>decodeReplacementAuthoring(r,o,bytes,v.midi_sha256,context.sceneId);decode(v);
for(const mutate of [r=>r.project_changed=true,r=>r.runtime_state='verified',r=>r.authoring_key='f'.repeat(64),r=>r.before_entry_sha256='f'.repeat(64),r=>r.proposed_binding.midi_sha256='f'.repeat(64),r=>r.after_entry_size++,r=>r.candidate_sequence_offset++,r=>r.supersedes_sequence_operands=!r.supersedes_sequence_operands,r=>r.sequence.events[1].delta_ticks++,r=>r.proposed_binding.format='unknown']){const bad=structuredClone(v);mutate(bad);assert.throws(()=>decode(bad));}
const reordered=structuredClone(v);reordered.proposed_binding.source_record=Object.fromEntries(Object.entries(reordered.proposed_binding.source_record).reverse());decode(reordered);
console.log('Replacement options/review, independent MIDI/native report, source/hash/extent/claim/refusal and canonical-key-order handling passed');

if(process.argv[4]){const saved=JSON.parse(fs.readFileSync(process.argv[4],'utf8'));decodeReplacementOptions(saved,{...context,authoringKey:saved.authoring_key});assert(saved.binding);console.log('Actual reopened binding/Current hashes and key order qualified');}
