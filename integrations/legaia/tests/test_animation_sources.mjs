import assert from 'node:assert/strict';
import {decodeAnimationSources} from '../editor/animation-sources.js';
const request={scene_id:'scene://town01',target_id:'scene://town01/actors/man-p1/0011',kind:'imported',expected_source_key:'a'.repeat(64)};
const record={schema_version:'legaia.animation-source.v1',scene_id:request.scene_id,target_id:request.target_id,kind:'imported',receipt_key:'b'.repeat(64),glb_sha256:'c'.repeat(64),candidate_sha256:'d'.repeat(64),review_key:'e'.repeat(64),byte_length:28,binding:{scene_id:request.scene_id},animation_index:null};
const value={schema_version:'legaia.animation-sources.v1',scene_id:request.scene_id,target_id:request.target_id,kind:'imported',project_source_key:request.expected_source_key,imports:[record],project_changed:false,historical_inputs:true};
assert.deepEqual(decodeAnimationSources(value,request),value);
for(const mutate of [v=>v.project_changed=true,v=>v.historical_inputs=false,v=>v.target_id='other',v=>v.project_source_key='f'.repeat(64),v=>v.imports.push(structuredClone(record)),v=>v.imports[0].byte_length=33554433,v=>v.imports[0].animation_index=true,v=>v.imports[0].glb_sha256='invalid',v=>v.imports[0].binding.scene_id='scene://other']){
  const invalid=structuredClone(value);mutate(invalid);assert.throws(()=>decodeAnimationSources(invalid,request));
}
console.log('Animation source recovery target, context, receipt, byte and clip guards passed.');

const {decodeAnimationSourceRemoval}=await import('../editor/animation-sources.js');
const removal={schema_version:'legaia.animation-source-removal.v1',scene_id:request.scene_id,target_id:request.target_id,kind:request.kind,project_source_key:request.expected_source_key,receipt_key:record.receipt_key,glb_sha256:record.glb_sha256,review_key:'f'.repeat(64),collection_key:'a'.repeat(64),native_key:'b'.repeat(64),native_content_changed:false,source_file_deleted:false,receipt_count_before:2,receipt_count_after:1,shared_blob_receipts:1,registered_bytes_released:28};
assert.deepEqual(decodeAnimationSourceRemoval(removal,request,record),removal);
for(const mutate of [v=>v.native_content_changed=true,v=>v.source_file_deleted=true,v=>v.receipt_count_after=0,v=>v.receipt_count_before=33,v=>v.registered_bytes_released=0,v=>v.shared_blob_receipts=3,v=>v.review_key='bad',v=>v.target_id='other']){const bad=structuredClone(removal);mutate(bad);assert.throws(()=>decodeAnimationSourceRemoval(bad,request,record));}
assert.equal(decodeAnimationSourceRemoval({...removal,shared_blob_receipts:2,registered_bytes_released:0},request,record).registered_bytes_released,0);
console.log('Reviewed animation source removal context, budget and native-preservation guards passed.');
