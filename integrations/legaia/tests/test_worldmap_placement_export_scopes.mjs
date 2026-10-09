import assert from 'node:assert/strict';
import fs from 'node:fs';
import {decodePlacementExport} from '../editor/worldmap-geometry.js';

await assert.rejects(()=>decodePlacementExport(null,{},null,'selected','scene://map01/worldmap/ground'));
const path=process.argv[2];
if(path){
 const fixtures=JSON.parse(fs.readFileSync(path,'utf8'));
 assert(fixtures.some(f=>f.scope==='selected'));assert(fixtures.some(f=>f.scope==='source-scene'));assert(fixtures.some(f=>f.scope==='ground'));
 for(const {value,report,scope,entityId} of fixtures){
  const decoded=await decodePlacementExport(value,report,null,scope,entityId);assert.equal(decoded.bytes.length,value.audit.byte_length);
  for(const patch of [v=>v.scope=scope==='ground'?'source-scene':'ground',v=>v.entity_id='scene://map02/worldmap/ground',v=>v.audit.export_scope='unknown',v=>v.audit.worldmap_source.entity_id='scene://map01/worldmap/missing',v=>v.audit.worldmap_source.placement_authoring.current_map_sha256='f'.repeat(64),v=>v.audit.sha256='f'.repeat(64)]){
   const altered=structuredClone(value);patch(altered);await assert.rejects(()=>decodePlacementExport(altered,report,null,scope,entityId));
  }
  if(scope==='selected'){await assert.rejects(()=>decodePlacementExport(value,report,null));const missing=structuredClone(value);delete missing.scope;await assert.rejects(()=>decodePlacementExport(missing,report,null,scope,entityId));}
 }
 console.log('Actual Current scene/ground/selected artifacts verify scoped identity and reject wrong scope, entity, source and bytes');
}else console.log('Malformed scoped export guard passed; private artifact checks SKIPPED without fixture argument');
