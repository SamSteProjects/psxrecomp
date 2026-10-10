import fs from 'node:fs';import assert from 'node:assert/strict';
import {decodeWorldmapTexture} from '../editor/worldmap-texture.js';
const reports=JSON.parse(fs.readFileSync(process.argv[2]));assert.ok(reports.length>=3);
for(const entry of reports){const v=entry.preview,context={record:entry.record,root:entry.root,key:v.source_key,path:v.project_path,palette:v.palette_index},held=structuredClone(v),decoded=await decodeWorldmapTexture(v,context);assert.equal(decoded.rgba.length,v.width*v.height*4);assert.equal(decoded.stp.length,v.width*v.height);decoded.metadata.source_record.pack_slot=999;assert.deepEqual(v,held);
 for(const mutate of [r=>r.source_key='0'.repeat(64),r=>r.texture_id='foreign',r=>r.project_path='foreign',r=>r.palette_index++,r=>r.palette_count++,r=>r.width++,r=>r.source_record.decoded_member_sha256='0'.repeat(64),r=>r.source_provenance.bundle_sha256='0'.repeat(64),r=>r.rgba_base64='',r=>r.stp_sha256='0'.repeat(64),r=>r.project_changed=true,r=>r.extra=true]){const bad=structuredClone(v);mutate(bad);await assert.rejects(()=>decodeWorldmapTexture(bad,context));}
}
console.log(`Native TIM reports (${reports.length}) retain exact source/palette/dimensions/byte hashes and detached metadata; twelve forged responses refused for each.`);
