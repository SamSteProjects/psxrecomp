// The fixture is produced from a freshly read private retail project.
import fs from 'node:fs';import assert from 'node:assert/strict';
import {decodeAllocationReceipt,decodeAllocationLibrary,decodeAllocationUploadReview} from '../editor/audio-allocation-input-contract.js';
import {decodeSampleReceipt} from '../editor/audio-sample-contract.js';
const file=process.argv[2];if(!file)throw Error('Provide a fresh allocation input fixture.');
const f=JSON.parse(fs.readFileSync(file,'utf8')),bytes=Uint8Array.from(Buffer.from(f.input_base64,'base64'));
const decode=v=>decodeAllocationUploadReview(v,f.context,f.bank,f.sample,bytes,f.input_sha256,f.retail);
assert.deepEqual(decode(f.review),f.review);assert.deepEqual(decodeAllocationReceipt(f.receipt,f.bank,f.sample),f.receipt);
assert.deepEqual(decodeAllocationLibrary(f.library,f.context.authoringKey,f.bank,f.sample),[f.receipt]);
assert.throws(()=>decodeSampleReceipt(f.receipt,f.bank,f.sample));
for(const change of [v=>v.authoring_key='f'.repeat(64),v=>v.binding.schema_version='legaia.audio-sample-source.v1',v=>v.binding.decoded_frames+=28,v=>v.binding.wav_sha256='f'.repeat(64),v=>v.native_content_changed=true,v=>v.native_audit.before_entry_sha256='f'.repeat(64),v=>v.native_audit.size_delta_bytes++,v=>v.native_audit.after_pieces.at(-1).size_bytes++,v=>v.native_audit.samples[1].after_sha256='f'.repeat(64),v=>v.native_audit.samples[1].after_bank_byte_offset++,v=>v.native_audit.sample.preserved_start_blocks=[],v=>v.native_audit.sample.remaining_bytes++,v=>v.native_audit.sample.termination.byte_offset++,v=>v.native_audit.sample.native_sample_rate=32000,v=>v.native_audit.sample.maximum_absolute_error=65536,v=>v.native_audit.sample.extra=true]){const bad=structuredClone(f.review);change(bad);assert.throws(()=>decode(bad));}
const bad=structuredClone(f.library);bad.imports.push(f.receipt);assert.throws(()=>decodeAllocationLibrary(bad,f.context.authoringKey,f.bank,f.sample));
assert.throws(()=>decodeAllocationLibrary(f.library,'f'.repeat(64),f.bank,f.sample));
console.log('Allocation input source, PCM, ordinal, marker, stale and forged contract checks passed.');
