import assert from 'node:assert/strict';
import fs from 'node:fs';
import {decodePlacementExport} from '../editor/worldmap-geometry.js';
await assert.rejects(()=>decodePlacementExport(null,{},null,'source-scene',null,{}));
const path=process.env.LEGAIA_BATCH_EXPORT_FIXTURE;
if(!path)console.log('Malformed batch artifact refused; private GLB checks skipped without LEGAIA_BATCH_EXPORT_FIXTURE.');
else{
 const {value,report,batch}=JSON.parse(fs.readFileSync(path,'utf8'));
 const decoded=await decodePlacementExport(value,report,null,'source-scene',null,batch);assert.equal(decoded.bytes.length,value.audit.byte_length);
 for(const mutate of [v=>v.batch_proposal.delta.x++,v=>v.audit.worldmap_source.placement_authoring.batch_proposal.record_ids.reverse(),v=>v.review_key='0'.repeat(64),v=>v.audit.worldmap_source.placement_authoring.exported_map_sha256='0'.repeat(64),v=>v.audit.sha256='0'.repeat(64),v=>v.scope='ground',v=>v.gameplay_verified=true]){const altered=structuredClone(value);mutate(altered);await assert.rejects(()=>decodePlacementExport(altered,report,null,'source-scene',null,batch));}
 await assert.rejects(()=>decodePlacementExport(value,report,null));
 await assert.rejects(()=>decodePlacementExport(value,report,{review_key:batch.review_key},'source-scene',null,batch));
 console.log('Real batch GLB hash/source/Review/scope validation passed; forged batch, stale MAP, binary, gameplay and mixed proposal claims refused.');
}
