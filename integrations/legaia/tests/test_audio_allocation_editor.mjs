// Run against independent, freshly qualified Retail/Current backend DTOs.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import {decodeAllocationOptions,decodeAllocationReview,decodeAllocationPcm} from '../editor/audio-allocation-contract.js';
if(!process.argv[2])throw Error('Provide a freshly qualified native allocation fixture.');
const f=JSON.parse(fs.readFileSync(process.argv[2],'utf8')), {context:c,bank:b,sample:s}=f;
const o=decodeAllocationOptions(f.options,c,b,s),r=decodeAllocationReview(f.review,o,'apply',o.retained_inputs[0],b);
const selection={row:r.proposed_sample,position:r.after_sample_entry_byte_offset,entryHash:r.after_entry_sha256,entryBytes:r.after_entry_size_bytes};
assert.equal((await decodeAllocationPcm(f.pcm,c,b,s,'proposed',r.proposed_sample_sha256,r.review_key,selection)).bytes.length,168);
let refusals=0;
for(const [field,value] of [['current_sample_entry_byte_offset',0],['current_entry_size_bytes',1],['current_sample_sha256','0'.repeat(64)],['authoring_key','0'.repeat(64)]]){assert.throws(()=>decodeAllocationOptions({...f.options,[field]:value},c,b,s));refusals++;}
for(const [field,value] of [['after_sample_entry_byte_offset',0],['after_entry_size_bytes',1],['proposed_sample_sha256','0'.repeat(64)],['native_content_changed',false]]){assert.throws(()=>decodeAllocationReview({...f.review,[field]:value},o,'apply',o.retained_inputs[0],b));refusals++;}
for(const [field,value] of [['sample_entry_byte_offset',0],['entry_sha256','0'.repeat(64)],['layer','current'],['pcm_sha256','0'.repeat(64)]]){await assert.rejects(()=>decodeAllocationPcm({...f.pcm,[field]:value},c,b,s,'proposed',r.proposed_sample_sha256,r.review_key,selection));refusals++;}
console.log(JSON.stringify({retail_current_review_proposed_pcm:true,forged_field_refusals:refusals}));
