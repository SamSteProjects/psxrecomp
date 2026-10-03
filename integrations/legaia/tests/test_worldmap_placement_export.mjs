import assert from 'node:assert/strict';
import fs from 'node:fs';
import {decodePlacementExport} from '../editor/worldmap-placement-editor.js';
const path=process.env.LEGAIA_PLACEMENT_EXPORT_FIXTURE;
if(!path){
 await assert.rejects(()=>decodePlacementExport(null,{},null));
 console.log('Malformed export guard passed; private artifact checks SKIPPED without LEGAIA_PLACEMENT_EXPORT_FIXTURE');
}else{
const fixture=JSON.parse(fs.readFileSync(path,'utf8'));
for(const [value,report,proposal] of [[fixture.current,fixture.report,null],[fixture.proposed,fixture.reviewed,fixture.proposal]]){
 const result=await decodePlacementExport(value,report,proposal);assert.equal(result.bytes.length,value.audit.byte_length);
 for(const mutate of [v=>v.representation='retail-source',v=>v.review_key='f'.repeat(64),v=>v.audit.worldmap_source.placement_authoring.override_scope='unknown',v=>v.audit.worldmap_source.placement_authoring.exported_map_sha256='f'.repeat(64),v=>v.audit.worldmap_source.placement_authoring.gameplay_verified=true,v=>v.audit.sha256='f'.repeat(64),v=>v.filename='unsafe.glb']){const altered=structuredClone(value);mutate(altered);await assert.rejects(()=>decodePlacementExport(altered,report,proposal));}
}
await assert.rejects(()=>decodePlacementExport(fixture.proposed,fixture.report,null));
console.log('Current/Proposed placement export guards verify real private artifacts and reject stale, wrong-scope, gameplay and binary claims');
}
