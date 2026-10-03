import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const source=await readFile(new URL('../editor/draft-review.js',import.meta.url),'utf8');
const {decodeDraftOutputReview}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
const key='a'.repeat(64),owner='scene://fixture/actors/man-p1/0001';
const row={owner_id:owner,facing_id:'script://fixture/actors/man-p1/0001/facing/0011',pc:17,decoded_byte_offset:101,source_decoded_byte_offset:98,before_byte:129,after_byte:130,before_sector:1,after_sector:2,source_record_sha256:key,appended_man_sha256:key};
const value={schema_version:'legaia.draft-output-review.v1',project_source_key:key,source_disc_sha256:key,source_prot_sha256:key,result_prot_sha256:key,archive_bytes:128,draft_count:1,experimental:true,normal_build_ready:false,output_written:false,gameplay_verified:false,scenes:[{scene_id:'scene://fixture',draft_count:1,final_man_sha256:key,facing_changes:[row]}],limitations:['Source script sectors; gameplay remains unverified.'],allocation:{}};
const decoded=decodeDraftOutputReview(value,key);assert.deepEqual(decoded,value);decoded.scenes[0].facing_changes[0].after_byte=0;assert.equal(row.after_byte,130);
for(const mutate of [v=>v.project_source_key='b'.repeat(64),v=>v.output_written=true,v=>v.normal_build_ready=true,v=>v.gameplay_verified=true,v=>v.draft_count=2,v=>v.scenes.push(structuredClone(v.scenes[0])),v=>v.scenes[0].facing_changes[0].after_byte=2,v=>v.scenes[0].facing_changes[0].owner_id='scene://other/actors/man-p1/0001',v=>v.scenes[0].facing_changes.push(structuredClone(v.scenes[0].facing_changes[0])),v=>v.scenes[0].facing_changes[0].decoded_byte_offset=Infinity]){const invalid=structuredClone(value);mutate(invalid);assert.throws(()=>decodeDraftOutputReview(invalid,key));}
console.log('NPC output review rejects stale sources, write/gameplay claims, duplicate scenes/bytes and altered facing flags.');
