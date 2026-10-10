import fs from 'node:fs';import assert from 'node:assert/strict';
import {decodeWorldmapTexture} from '../editor/worldmap-texture.js';
const entries=JSON.parse(fs.readFileSync(process.argv[2]));assert.equal(entries.length,6);
for(const entry of entries){
 const v=entry.preview,context={record:entry.record,root:entry.root,key:v.source_key,path:v.project_path,palette:v.palette_index,layer:v.layer},held=structuredClone(v);
 const decoded=await decodeWorldmapTexture(v,context);assert.equal(decoded.rgba.length,v.width*v.height*4);decoded.metadata.source_record.pack_slot=999;assert.deepEqual(v,held);
 for(const mutate of [r=>r.layer=r.layer==='retail'?'current':'retail',r=>r.source_tim_sha256='0'.repeat(64),r=>r.effective_tim_sha256='invalid',r=>r.authored=!r.authored,r=>r.source_key='0'.repeat(64),r=>r.rgba_sha256='0'.repeat(64),r=>r.source_provenance.texture_pack_sha256='0'.repeat(64),r=>r.extra=true]){const bad=structuredClone(v);mutate(bad);await assert.rejects(()=>decodeWorldmapTexture(bad,context));}
}
console.log('Six native Retail/Current reports: exact layer/source/pixel checks, detached metadata and eight forged-response refusals each passed.');
