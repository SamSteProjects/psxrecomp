import fs from 'node:fs';import assert from 'node:assert/strict';
const code=fs.readFileSync(new URL('../editor/catalog-scene-preview.js',import.meta.url),'utf8').replace(/^import .*;\r?\n/gm,'');
const {decodeCatalogScenePreview}=await import('data:text/javascript;base64,'+Buffer.from(code+'\n//# sourceURL=catalog-scene-preview-contract.js').toString('base64'));
const source=JSON.parse(fs.readFileSync(process.env.LEGAIA_CATALOG_PREVIEW_EVIDENCE)),key=source.project_source_key,disc=source.disc_identity;
assert.equal(decodeCatalogScenePreview(source,'taiku',key,disc).preview.entities.length,290);
const detached=decodeCatalogScenePreview(source,'taiku',key,disc);detached.preview.entities[0].name='changed';assert.notEqual(source.preview.entities[0].name,'changed');
let count=0;
for(const mutate of [v=>v.scene_id='scene://foreign',v=>v.project_source_key='0'.repeat(64),v=>v.disc_identity='sha256:'+'0'.repeat(64),v=>v.read_only=false,v=>v.project_imported=true,v=>v.representation='authored',v=>v.gameplay_verified=true,v=>v.preview.scene_id='scene://foreign',v=>v.preview.environment_authoring={},v=>v.preview.entities[0].kind='actor_draft',v=>v.preview.entities[0].authored_position={x:128,z:256},v=>v.preview.entities[0].model_to_scene[0]=null,v=>v.preview.entities.push(v.preview.entities[0]),v=>v.preview.metrics.total_renderable_count=0]){
 const forged=structuredClone(source);mutate(forged);assert.throws(()=>decodeCatalogScenePreview(forged,'taiku',key,disc));count++;
}
console.log(`Catalog scene preview contract passed; ${count} forged responses refused.`);
