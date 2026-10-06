import assert from 'node:assert/strict';
import {decodeModelSourceLibrary,filterModelSourceLibrary,decodeLibraryRemoval} from '../editor/model-source-library.js';
const path='C:/private/project',scene='scene://town01',asset='asset://town01/models/scene-tmd/0000';
const row={schema_version:'legaia.model-source.v1',scene_id:scene,asset_id:asset,receipt_key:'a'.repeat(64),glb_sha256:'b'.repeat(64),candidate_sha256:'c'.repeat(64),review_key:'d'.repeat(64),byte_length:28,binding:{schema_version:'legaia.model-glb-binding.v1',scene_id:scene,asset_id:asset,profile:{objects:[{}]},external_object_nodes:[0]}};
const value={schema_version:'legaia.model-source-library.v1',project_path:path,library_key:'e'.repeat(64),mode:'edit',imports:[row],receipt_count:1,distinct_glb_count:1,registered_byte_length:28,project_changed:false,historical_inputs:true};
assert.deepEqual(decodeModelSourceLibrary(value,path),value);
for(const mutate of [v=>v.project_path+='other',v=>v.project_changed=true,v=>v.imports.push(structuredClone(row)),v=>v.distinct_glb_count=2,v=>v.registered_byte_length=29,v=>v.imports[0].binding.asset_id='other',v=>v.imports[0].binding.external_object_nodes=[-1],v=>v.library_key='bad',v=>v.mode='unknown']){const bad=structuredClone(value);mutate(bad);assert.throws(()=>decodeModelSourceLibrary(bad,path));}
assert.equal(filterModelSourceLibrary(value.imports,'TOWN01 model',scene).length,1);assert.equal(filterModelSourceLibrary(value.imports,'absent').length,0);assert.equal(filterModelSourceLibrary(value.imports,'','scene://other').length,0);
const removal={schema_version:'legaia.model-library-removal.v1',project_path:path,library_key:value.library_key,receipt_key:row.receipt_key,glb_sha256:row.glb_sha256,scene_id:scene,asset_id:asset,receipt_count_before:1,receipt_count_after:0,registered_bytes_released:28,native_content_changed:false,source_file_deleted:false,review_key:'f'.repeat(64)};
assert.deepEqual(decodeLibraryRemoval(removal,value,row),removal);
for(const mutate of [v=>v.native_content_changed=true,v=>v.source_file_deleted=true,v=>v.library_key='a'.repeat(64),v=>v.receipt_count_after=1,v=>v.registered_bytes_released=0,v=>v.asset_id='other']){const bad=structuredClone(removal);mutate(bad);assert.throws(()=>decodeLibraryRemoval(bad,value,row));}
console.log('Project model input library qualification, filtering and removal guards passed.');
