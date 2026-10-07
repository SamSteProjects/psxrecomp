import {exact,equal,hash,integer,decodeSampleReceipt} from './audio-sample-contract.js';
import {inspectInputWav} from './audio-sample-recovery.js';
export const ALLOCATION_SCHEMA='legaia.audio-sample-allocation-source.v1';
export function decodeAllocationReceipt(v,bank,sample,retained=true){
 decodeSampleReceipt(v,bank,sample,retained,true);
 if(v.schema_version!==ALLOCATION_SCHEMA)throw Error('Choose a retained allocation input.');
 return structuredClone(v);
}
export function decodeAllocationLibrary(v,key,bank,sample){
 if(!exact(v,['schema_version','authoring_key','imports','historical_inputs','project_changed','runtime_state'])||v.schema_version!=='legaia.audio-sample-sources.v1'||v.authoring_key!==key||!hash(key)||v.historical_inputs!==true||v.project_changed!==false||v.runtime_state!=='not_observed'||!Array.isArray(v.imports)||v.imports.length>32)throw Error('Allocation input library differs from Current.');
 const selected=v.imports.filter(r=>r.schema_version===ALLOCATION_SCHEMA&&r.asset_id===bank.asset_id&&r.sample_index===sample.index),seen=new Set();
 for(const r of selected){decodeAllocationReceipt(r,bank,sample);if(seen.has(r.receipt_key))throw Error('Duplicate allocation receipt.');seen.add(r.receipt_key);}
 return structuredClone(selected);
}
export function decodeAllocationUploadReview(v,context,bank,sample,bytes,wavSha,retail){
 if(!exact(v,['schema_version','authoring_key','binding','native_audit','historical_inputs','native_content_changed','project_changed','runtime_state','review_key'])||v.schema_version!=='legaia.audio-sample-allocation-source-review.v1'||v.authoring_key!==context.authoringKey||!hash(v.review_key)||v.historical_inputs!==true||v.native_content_changed!==false||v.project_changed!==false||v.runtime_state!=='not_observed')throw Error('Allocation input review differs from Current.');
 const r=decodeAllocationReceipt(v.binding,bank,sample,false),a=v.native_audit,n=a?.sample;
 if(r.wav_sha256!==wavSha||r.byte_length!==bytes.length)throw Error('Allocation review differs from uploaded WAV bytes.');
 inspectInputWav(bytes,r);
 const blocks=r.decoded_frames/28,size=blocks*16+retail.remaining_bytes,delta=size-sample.size_bytes;
 const starts=retail.markers.filter(m=>m.flags===4).map(m=>m.block_index);
 if(retail.termination.reason!=='encoded-end'||retail.markers.some(m=>![0,1,4].includes(m.flags))||retail.markers.filter(m=>m.flags===1).length!==1||starts.some(i=>i>=blocks-1))throw Error('Source markers do not qualify this allocation.');
 const auditKeys=['schema_version','before_entry_sha256','after_entry_sha256','before_size_bytes','after_size_bytes','size_delta_bytes','before_bank_sha256','after_bank_sha256','carrier','before_pieces','after_pieces','samples','bank_size_word_offset','sample_table_offset','bank_tail_sha256','runtime_state','gameplay_verified','source_entry_sha256','source_bank_sha256','sample_index','sample'];
 if(!exact(a,auditKeys)||a.schema_version!=='legaia.audio-carrier-allocation.v1'||a.source_entry_sha256!==bank.source_record.entry_sha256||a.before_entry_sha256!==a.source_entry_sha256||!hash(a.after_entry_sha256)||a.before_size_bytes!==bank.source_record.entry_size_bytes||a.after_size_bytes!==a.before_size_bytes+delta||!integer(a.after_size_bytes,32,4194304)||a.size_delta_bytes!==delta||a.before_bank_sha256!==bank.bank_sha256||a.source_bank_sha256!==bank.bank_sha256||!hash(a.after_bank_sha256)||a.carrier!==bank.source_record.carrier||!equal(a.before_pieces,bank.source_record.pieces)||a.bank_size_word_offset!==12||a.sample_table_offset!==bank.sections.sample_table_offset||!hash(a.bank_tail_sha256)||a.sample_index!==sample.index||a.runtime_state!=='not_observed'||a.gameplay_verified!==false||!Array.isArray(a.samples)||a.samples.length!==bank.samples.length)throw Error('Allocation carrier audit differs from source ownership.');
 const expectedPieces=structuredClone(bank.source_record.pieces);expectedPieces.at(-1).size_bytes+=delta;
 if(!equal(a.after_pieces,expectedPieces))throw Error('Allocation native pieces changed unexpectedly.');
 let shift=0;for(const [index,move] of a.samples.entries()){
  const source=bank.samples[index],selected=index===sample.index,afterSize=selected?size:source.size_bytes;
  if(!exact(move,['sample_index','before_bank_byte_offset','after_bank_byte_offset','before_size_bytes','after_size_bytes','before_sha256','after_sha256','selected'])||move.sample_index!==source.index||move.before_bank_byte_offset!==source.offset||move.after_bank_byte_offset!==source.offset+shift||move.before_size_bytes!==source.size_bytes||move.after_size_bytes!==afterSize||move.before_sha256!==source.source_sha256||move.after_sha256!==(selected?r.candidate_sample_sha256:source.source_sha256)||move.selected!==selected)throw Error('Allocation changed unrelated samples or ordinal spans.');
  if(selected)shift+=delta;
 }
 const nativeKeys=['schema_version','source_sha256','before_sha256','after_sha256','source_size_bytes','before_size_bytes','after_size_bytes','size_delta_bytes','source_decoded_frames','decoded_frames','encoded_blocks','consumed_bytes','remaining_bytes','tail_sha256','termination','preserved_start_blocks','input_wav_sha256','input_pcm_sha256','decoded_pcm_sha256','input_wav_rate','native_sample_rate','sum_squared_error','maximum_absolute_error','encoder','runtime_state'];
 if(!exact(n,nativeKeys)||n.schema_version!=='legaia.audio-sample-allocation.v1'||n.source_sha256!==sample.source_sha256||n.before_sha256!==sample.source_sha256||n.after_sha256!==r.candidate_sample_sha256||n.source_size_bytes!==sample.size_bytes||n.before_size_bytes!==sample.size_bytes||n.after_size_bytes!==size||n.size_delta_bytes!==delta||n.source_decoded_frames!==retail.decoded_frames||n.decoded_frames!==r.decoded_frames||n.encoded_blocks!==blocks||n.consumed_bytes!==blocks*16||n.remaining_bytes!==retail.remaining_bytes||!hash(n.tail_sha256)||!equal(n.termination,{reason:'encoded-end',byte_offset:(blocks-1)*16})||!equal(n.preserved_start_blocks,starts)||n.input_wav_sha256!==wavSha||!hash(n.input_pcm_sha256)||!hash(n.decoded_pcm_sha256)||n.input_wav_rate!==r.input_wav_rate||n.native_sample_rate!==null||!integer(n.sum_squared_error,0,r.decoded_frames*65535**2)||!integer(n.maximum_absolute_error,0,65535)||n.encoder!=='psx-spu-adpcm-closed-loop-exhaustive-v1'||n.runtime_state!=='not_observed')throw Error('Allocation PCM or marker audit differs from uploaded input.');
 return structuredClone(v);
}
