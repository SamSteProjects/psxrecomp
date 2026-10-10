import fs from 'node:fs';import assert from 'node:assert/strict';import crypto from 'node:crypto';
import {qualifyWorldReplacementReview} from '../editor/worldmap-tim-replacement.js';
const out=process.argv[2],receipts=JSON.parse(fs.readFileSync(out+'/receipts.json'));assert(receipts.length>=3);
for(const value of receipts){
 const bytes=fs.readFileSync(out+'/'+value.request.texture_id.split('/')[2]+'.tim'),candidateHash=crypto.createHash('sha256').update(bytes).digest('hex'),flags=bytes.readUInt32LE(4),bpp=[4,8,16,24][flags&7],clut=flags&8?{width_words:bytes.readUInt16LE(16),height:bytes.readUInt16LE(18)}:null,start=8+(clut?bytes.readUInt32LE(8):0),width=bytes.readUInt16LE(start+8)*16/bpp,height=bytes.readUInt16LE(start+10),record={source_record:{bpp,width,height,clut}},request={...value.request,content_base64:bytes.toString('base64')},options={record,request,candidateHash,path:value.project_path},held=structuredClone(value);
 const result=await qualifyWorldReplacementReview(value,options);result.metadata.request.palette_index++;assert.deepEqual(value,held);
 for(const mutate of [v=>v.project_path='foreign',v=>v.request.palette_index++,v=>v.byte_length++,v=>v.width++,v=>v.palette_count++,v=>v.candidate_tim_sha256='0'.repeat(64),v=>v.changed_pixel_count=-1,v=>v.changed_palette_words=-1,v=>v.changed_image_bytes=0,v=>v.changed=!v.changed,v=>v.rgba_base64='bad',v=>v.stp_sha256='0'.repeat(64),v=>v.review_key='bad',v=>v.project_changed=true,v=>v.scope='layout-allocation',v=>v.extra=true]){const bad=structuredClone(value);mutate(bad);await assert.rejects(()=>qualifyWorldReplacementReview(bad,options));}
}
console.log(`${receipts.length} native replacement receipts: detached metadata, exact file/pixel hashes and sixteen forged-response refusals each passed.`);
