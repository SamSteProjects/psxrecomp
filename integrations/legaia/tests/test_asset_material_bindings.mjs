import assert from 'node:assert/strict';
import {materialBindingRows} from '../editor/asset-material-bindings.js';
const hash='a'.repeat(64),scene='scene://fixture',model='asset://fixture/model',texture='texture://fixture/0001';
const nodes=[{id:model,kind:'model',label:'Model',scene_id:scene,scene_ids:[scene],navigable_scene_ids:[scene],available:true},{id:texture,kind:'texture',label:'Texture',scene_id:scene,scene_ids:[scene],navigable_scene_ids:[scene],available:true}];
const evidence={material_index:0,tpage:0,clut:0,uv_bounds:[0,0,1,1],evidence:'static_vram_addresses_not_runtime_residency',model_source_sha256:hash};
const edges=['static_material_texture_source','effective_material_texture_source'].map((kind,i)=>({id:(i?'c':'b').repeat(64),source_id:model,target_id:texture,kind,scene_id:scene,layer:i?'effective':'decoded',runtime_binding:'not_asserted',source_import_sha256:hash,source_catalog_key:hash,material_evidence:i?{...evidence,model_current_sha256:'d'.repeat(64),authored_materials_sha256:'e'.repeat(64)}:evidence}));
const report=id=>({schema_version:'legaia.project-asset-references.v1',asset_id:id,source_key:hash,read_only:true,nodes,incoming:id===texture?edges:[],outgoing:id===model?edges:[],coverage:{verified_scene_ids:[scene],resource_scene_id:scene,unresolved_reference_count:0,scenes:[{scene_id:scene,source_import_sha256:hash,status:'available',resource_source_key:hash,reason:null,limitations:[]}]},limitations:['Static sources only']});
for(const [type,id,target] of [['model',model,texture],['texture',texture,model]]){
 const source=report(id),result=materialBindingRows(source,{assetId:id,sourceKey:hash,type});assert.deepEqual(result.rows.map(row=>row.layer),['retail','current']);assert.ok(result.rows.every(row=>row.target.id===target&&row.sceneId===scene));assert.equal(result.rows[1].evidence.material_evidence.model_current_sha256,'d'.repeat(64));result.rows[0].evidence.material_evidence.uv_bounds[0]=9;assert.equal(evidence.uv_bounds[0],0);
 assert.throws(()=>materialBindingRows(source,{assetId:id,sourceKey:'f'.repeat(64),type}));assert.throws(()=>materialBindingRows(source,{assetId:id,sourceKey:hash,type:type==='model'?'texture':'model'}));
 const missing=structuredClone(source);missing.incoming=missing.outgoing=[];assert.equal(materialBindingRows(missing,{assetId:id,sourceKey:hash,type}).rows.length,0);
 const bad=structuredClone(source);(type==='model'?bad.outgoing:bad.incoming)[0].material_evidence.evidence='runtime_resident';assert.throws(()=>materialBindingRows(bad,{assetId:id,sourceKey:hash,type}));
}
console.log('Model/texture direction, separate Retail/Current evidence, source-scene navigation, detached provenance and unknown/stale/type rejection passed.');
