import fs from 'node:fs';import assert from 'node:assert/strict';
import {qualifyWorldAnimationExport} from '../editor/worldmap-animation-export.js';
const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let refusals=0;
for(const r of rows){const before=structuredClone(r),v=await qualifyWorldAnimationExport(r.result,r.receipt,r.layer,r.fps);assert.equal(v.bytes.length,r.result.audit.byte_length);assert.deepEqual(r,before);
 for(const alter of [v=>v.filename='foreign.glb',v=>v.audit.scene='map00',v=>v.audit.source_key='stale',v=>v.audit.entity_id='foreign',v=>v.audit.layer='proposed',v=>v.audit.fps++,v=>v.audit.bank_sha256='0'.repeat(64),v=>v.audit.record_sha256='0'.repeat(64),v=>v.audit.model_asset_id='foreign',v=>v.audit.placement_included=true,v=>v.audit.gameplay_verified=true,v=>v.audit.model_export.object_count++,v=>v.audit.model_export.source_record={foreign:true},v=>v.glb_base64='AAAA']){const bad=structuredClone(r.result);alter(bad);await assert.rejects(qualifyWorldAnimationExport(bad,r.receipt,r.layer,r.fps));refusals++;}
}
assert.equal(rows.length,10);console.log(`Ten native Retail/Current GLB downloads and ${refusals} source/hash/model/rate refusals passed.`);
