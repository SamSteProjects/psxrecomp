import assert from 'node:assert/strict';
import fs from 'node:fs';
import {webcrypto} from 'node:crypto';
import {decodeReplacementReview} from '../editor/audio-sequence-replacement.js';
const f=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),bytes=new Uint8Array(fs.readFileSync(process.argv[3])),v=f.replacement;
const decode=r=>decodeReplacementReview(r,f.options,bytes,v.midi_sha256,'scene://town01');
const result=decode(v);result.sequence.events[0].values[0]++;assert.notDeepEqual(result,v);
for(const mutate of [r=>r.writable=true,r=>r.project_changed=true,r=>r.input_retained=true,r=>r.runtime_state='verified',r=>r.authoring_key='f'.repeat(64),r=>r.audit.bank_samples_preserved=false,r=>r.audit.carrier_suffix_preserved=false,r=>r.audit.opaque_tail_size++,r=>r.audit.added_alignment_bytes=4,r=>r.audit.after_ticks++,r=>r.sequence.events[1].delta_ticks++,r=>r.audit.after_entry_size++,r=>r.audit.unchanged=true]){const bad=structuredClone(v);mutate(bad);assert.throws(()=>decode(bad));}
console.log('Native replacement DTO, independent MIDI/event agreement, detached results, ownership/tail/extent/runtime/writable refusal passed');
