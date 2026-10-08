import fs from 'node:fs';import assert from 'node:assert/strict';
const {decodeModelResolution}=await import('data:text/javascript;base64,'+Buffer.from(fs.readFileSync(new URL('../editor/model-resolution.js',import.meta.url))).toString('base64'));
const source=JSON.parse(fs.readFileSync(process.env.LEGAIA_MODEL_RESOLUTION_EVIDENCE)),scene=source.scene_id,key=source.source_key;
const value=decodeModelResolution(source,scene,key);assert.equal(value.rows.length,6);value.rows[0].retail.model_index=0;assert.notEqual(source.rows[0].retail.model_index,0);
const resolved=structuredClone(source);Object.assign(resolved.rows[0].current,{model_index:240,model_pool:'global_special',slot_index:0,asset_id:'asset://legaia/models/global-special/00f0',status:'resolved'});resolved.counts.current_unresolved=5;assert.equal(decodeModelResolution(resolved,scene,key).rows[0].current.asset_id,'asset://legaia/models/global-special/00f0');
const resolvedScene=structuredClone(resolved);Object.assign(resolvedScene.rows[0].current,{model_index:0,model_pool:'scene_tmd',slot_index:0,asset_id:'asset://taiku2/models/scene-tmd/0000'});assert.equal(decodeModelResolution(resolvedScene,scene,key).rows[0].current.slot_index,0);
let count=0;
for(const mutate of [v=>v.scene_id='scene://foreign',v=>v.source_key='0'.repeat(64),v=>v.read_only=false,v=>v.gameplay_verified=true,v=>v.coverage='runtime_models',v=>v.counts.retail_unresolved=5,v=>v.rows.push(v.rows[0]),v=>v.rows[0].retail.asset_id='asset://guessed',v=>v.rows[0].retail.model_index=true,v=>v.rows[0].retail.slot_index=0,v=>v.rows[0].retail.status='resolved',v=>v.rows[0].retail.source_actor_id='scene://foreign/actors/man-p1/0001',v=>v.rows[0].retail.source_record.disc.sha256='0'.repeat(64),v=>v.rows[0].retail.source_record.byte_length=0,v=>v.rows[0].retail.source_record.containing_decoded_size=1]){
 const forged=structuredClone(source);mutate(forged);assert.throws(()=>decodeModelResolution(forged,scene,key));count++;
}
console.log(`Model resolution contract passed; ${count} forged responses refused.`);
