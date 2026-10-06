import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {decodeMeshLibrary,filterMeshLibrary,qualifyMeshLibraryDownload,navigateMeshSource,decodeMeshComparison} from '../editor/mesh-source-library.js';
const path='fixture',key='a'.repeat(64),bytes=Buffer.alloc(32,17),recipe={kind:'single',material_colors:false,scene_index:null,uv_set:0,source_scale:1,source_offset:[0,0,0],source_rotation:[0,0,0],donor_face_id:'fixture',new_group:true,replace_group:false,replace_object:false,preserve_primitives:false,primitive_index:null};
const row={scene_id:'scene://town01',receipt:{schema_version:'legaia.model-mesh-source.v1',asset_id:'asset://town01/models/scene-tmd/0009',glb_sha256:createHash('sha256').update(bytes).digest('hex'),byte_length:32,first_operation:0,operation_count:1,operations_sha256:'b'.repeat(64),input_sha256:'c'.repeat(64),proposed_sha256:'d'.repeat(64),receipt_key:'e'.repeat(64),recipe}};
const catalog={schema_version:'legaia.mesh-source-library.v1',project_path:path,mode:'edit',library_key:key,imports:[row],receipt_count:1,distinct_glb_count:1,registered_byte_length:32,project_changed:false,historical_inputs:true};
const value=()=>({...structuredClone(catalog),selected:structuredClone(row),content_base64:bytes.toString('base64')});
const clone=decodeMeshLibrary(catalog,path);clone.imports[0].receipt.recipe.source_offset[0]=1;assert.equal(recipe.source_offset[0],0);
assert.equal(filterMeshLibrary(catalog.imports,'town01 single').length,1);assert.equal(filterMeshLibrary(catalog.imports,'batch').length,0);assert.equal(filterMeshLibrary(catalog.imports,'','scene://town0c').length,0);
for(const change of [v=>v.extra=true,v=>v.registered_byte_length=31,v=>v.imports.push(v.imports[0]),v=>v.imports[0].scene_id='scene://town0c',v=>v.imports[0].receipt.recipe.extra=true,v=>v.imports[0].receipt.operation_count=0]){const v=structuredClone(catalog);change(v);assert.throws(()=>decodeMeshLibrary(v,path));}
assert.deepEqual(Buffer.from((await qualifyMeshLibraryDownload(value(),catalog,row,()=>true)).bytes),bytes);
for(const change of [v=>v.library_key='f'.repeat(64),v=>v.selected.receipt.recipe.source_scale=2,v=>v.content_base64=Buffer.alloc(32,18).toString('base64'),v=>v.mode='live']){const v=value();change(v);await assert.rejects(qualifyMeshLibraryDownload(v,catalog,row,()=>true));}
let checks=0;await assert.rejects(qualifyMeshLibraryDownload(value(),catalog,row,()=>++checks<3));
let state={project:{path,mode:'edit'},scene:{id:'scene://town0c'},assets:[],model_overrides:{}},opened=[],reads=0;
const options={record:row,catalog,getState:()=>state,readLibrary:async()=>{reads++;return catalog;},changeScene:async id=>{state={...state,scene:{id},assets:[{id:row.receipt.asset_id}]};return true;},openModel:async(...args)=>opened.push(args)};
await navigateMeshSource(options);assert.equal(reads,2);assert.deepEqual(opened,[[row.receipt.asset_id,'imported']]);
await assert.rejects(navigateMeshSource({...options,readLibrary:async()=>({...catalog,library_key:'f'.repeat(64)})}));
await assert.rejects(navigateMeshSource({...options,busy:()=>true}));console.log('Mesh library validation, exact recovery, hash-time context and qualified scene navigation passed.');

const comparison={schema_version:'legaia.mesh-source-native-comparison.v1',project_path:path,library_key:key,receipt_key:row.receipt.receipt_key,scene_id:row.scene_id,asset_id:row.receipt.asset_id,historical_candidate_sha256:row.receipt.proposed_sha256,current_sha256:row.receipt.proposed_sha256,current_byte_length:512,matches_current:true,imported_face_count:2,active_imported_face_count:2,retired_imported_face_count:0,comparison_scope:'complete_native_model_and_imported_face_lifetime',face_content_match_asserted:false,project_changed:false,native_content_changed:false,gameplay_verified:false};
assert.deepEqual(decodeMeshComparison(comparison,catalog,row),comparison);
assert.equal(decodeMeshComparison({...comparison,current_sha256:'f'.repeat(64),matches_current:false,active_imported_face_count:1,retired_imported_face_count:1},catalog,row).retired_imported_face_count,1);
for(const change of [v=>v.extra=true,v=>v.library_key='f'.repeat(64),v=>v.current_sha256='bad',v=>v.matches_current=false,v=>v.active_imported_face_count=1,v=>v.face_content_match_asserted=true,v=>v.gameplay_verified=true,v=>v.current_byte_length=0,v=>{v.active_imported_face_count=1;v.retired_imported_face_count=1;}]){const v=structuredClone(comparison);change(v);assert.throws(()=>decodeMeshComparison(v,catalog,row));}
console.log('Current native mesh comparison identity, hash truth, face lifetime and no-write claims passed.');
