import fs from 'node:fs';
import assert from 'node:assert/strict';
import {decodeAllocationOptions,decodeAllocationReview,decodeAllocationPcm} from '../editor/audio-allocation-contract.js';
if(!process.argv[2])throw Error('Provide a freshly qualified Current-size fixture.');
const f=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),o=decodeAllocationOptions(f.options,f.context,f.bank,f.sample),r=decodeAllocationReview(f.review,o,'apply-current-size',f.receipt,f.bank);
decodeAllocationReview(f.legacy_review,o,'apply',f.receipt,f.bank);
assert.equal(r.before_entry_size_bytes,r.after_entry_size_bytes);assert.equal(r.current_sample.size_bytes,r.proposed_sample.size_bytes);
const selection={row:r.proposed_sample,position:r.after_sample_entry_byte_offset,entryHash:r.after_entry_sha256,entryBytes:r.after_entry_size_bytes};
assert.equal((await decodeAllocationPcm(f.pcm,f.context,f.bank,f.sample,'proposed',r.proposed_sample_sha256,r.review_key,selection)).bytes.length,168);
let refusals=0;for(const [field,value] of [['schema_version','legaia.audio-allocation-review.v1'],['held_outside_sample_sha256','broken'],['after_entry_size_bytes',r.after_entry_size_bytes+16],['after_sample_entry_byte_offset',r.after_sample_entry_byte_offset+16],['operation','apply'],['proposed_sample',{...r.proposed_sample,size_bytes:r.proposed_sample.size_bytes+16,size_units:r.proposed_sample.size_units+2}]]){assert.throws(()=>decodeAllocationReview({...r,[field]:value},o,'apply-current-size',f.receipt,f.bank));refusals++;}
assert.throws(()=>decodeAllocationReview(r,o,'apply-current-size',f.wrong_receipt,f.bank));refusals++;
console.log(JSON.stringify({current_size_review_proposed_pcm:true,legacy_review_held:true,forged_refusals:refusals}));
