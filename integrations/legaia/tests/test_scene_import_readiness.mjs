import assert from 'node:assert/strict';
import fs from 'node:fs';
const {decodeSceneCatalog}=await import('data:text/javascript;base64,'+Buffer.from(fs.readFileSync(new URL('../editor/scene-catalog.js',import.meta.url))).toString('base64'));
const source=JSON.parse(fs.readFileSync(process.env.LEGAIA_SCENE_READINESS_EVIDENCE));
const value=decodeSceneCatalog(source,0,'taiku');assert.equal(value.scenes[1].unresolved_actor_model_count,6);
value.scenes[0].name='changed';assert.equal(source.scenes[0].name,'taiku');
let count=0;
for(const mutate of [v=>v.schema_version='legaia.scene-catalog.v1',v=>v.offset=16,v=>v.limit=64,v=>v.scanned_blocks=1,v=>v.total_blocks=3,v=>v.next_offset=16,v=>v.source.disc_identity='bad',v=>v.qualification='gameplay',v=>v.scenes.push(v.scenes[0]),v=>v.scenes[0].scene_model_count=null,v=>v.scenes[0].global_model_count=0,v=>v.scenes[1].model_resolution_status='resolved',v=>v.scenes[0].semantic_id='scene://foreign',v=>v.scenes[0].bundle_entry=0,v=>v.scenes[0].import_status='unsupported',v=>v.scenes[0].import_reason='refused']){
 const forged=structuredClone(source);mutate(forged);assert.throws(()=>decodeSceneCatalog(forged,0,'taiku'));count++;
}
const partial=structuredClone(source);Object.assign(partial.scenes[1],{import_status:'unsupported',import_reason:'native model slot refuses',model_resolution_status:'unavailable',scene_model_count:null,global_model_count:null,unresolved_actor_model_count:null});assert.equal(decodeSceneCatalog(partial,0,'taiku').scenes[1].import_status,'unsupported');
console.log(`Scene readiness contract passed; ${count} forged responses refused.`);
