import fs from 'node:fs';
import assert from 'node:assert/strict';
import {worldModelComparisonGeometry,qualifyWorldModelComparison,worldModelVertexSelection} from '../editor/worldmap-model-comparison.js';
const rows=JSON.parse(fs.readFileSync(process.argv[2]));
for(const item of rows){
 const source={...item.source,tmd:new Uint8Array(Buffer.from(item.source.tmd_base64,'base64'))},candidate=new Uint8Array(Buffer.from(item.expected_base64,'base64'));
 assert.deepEqual(worldModelComparisonGeometry(source,source.tmd),item.current_geometry);
 assert.deepEqual(worldModelComparisonGeometry(source,candidate),item.proposed_geometry);
 const receipt={request:{asset_id:item.name,source_key:'key'},review_key:'review',proposed_sha256:'candidate'};source.metadata.tmd_sha256='current';
 const value={schema_version:'legaia.worldmap-model-comparison.v1',project_path:'project',asset_id:item.name,source_key:'key',review_key:'review',current_sha256:'current',proposed_sha256:'candidate',current:item.current_geometry,proposed:item.proposed_geometry,coordinate_system:'retail_tmd_object_local_y_down',read_only:true,project_changed:false,gameplay_verified:false},options={source,candidate,receipt,path:'project'},held=structuredClone(value);
 const qualified=qualifyWorldModelComparison(value,options);qualified.current.vertices[0][0]++;assert.deepEqual(value,held);
 for(const mutate of [v=>v.extra=true,v=>v.project_path='foreign',v=>v.asset_id='foreign',v=>v.source_key='stale',v=>v.review_key='stale',v=>v.current_sha256='stale',v=>v.proposed_sha256='stale',v=>v.current.vertices[0][0]++,v=>v.proposed.vertices[0][1]++,v=>v.proposed.triangles[0][0]++,v=>v.current.triangles=[],v=>v.coordinate_system='y_up',v=>v.read_only=false,v=>v.project_changed=true,v=>v.gameplay_verified=true]){const bad=structuredClone(value);mutate(bad);assert.throws(()=>qualifyWorldModelComparison(bad,options));}
}
assert(rows.length);console.log(rows.length+' native/synthetic comparison pairs: exact independent vertices and packet topology, detached results and fifteen forged ownership/geometry claims each passed.');

const source={metadata:{layer:'current'},shape:{objects:[{vertices:[]},{vertices:[[1,2,3],[4,5,6],[7,8,9]]},{vertices:[[10,11,12],[13,14,15],[16,17,18]]}]}},geometry={vertices:[[1,2,3],[4,5,6],[7,8,9],[20,21,22],[23,24,25],[26,27,28]],triangles:[[3,4,5]]},hit={vertex_index:4,triangle_index:0,decoded_model_position:[23,24,25]},original=structuredClone(source);
const selection=worldModelVertexSelection(source,geometry,hit);assert.deepEqual(selection,{object_index:2,vector_index:1,flat_index:4,triangle_index:0,current_xyz:[13,14,15],displayed_xyz:[23,24,25]});selection.current_xyz[0]++;selection.displayed_xyz[0]++;assert.deepEqual(source,original);assert.deepEqual(geometry.vertices[4],[23,24,25]);
for(const change of [{vertex_index:-1},{vertex_index:1.5},{vertex_index:99},{vertex_index:1},{triangle_index:-1},{triangle_index:1},{decoded_model_position:[0,0,0]}])assert.throws(()=>worldModelVertexSelection(source,geometry,{...hit,...change}));assert.throws(()=>worldModelVertexSelection({...source,metadata:{layer:'retail'}},geometry,hit));
console.log('Picked corner maps across empty/native object tables to Current coordinates; displayed Proposed coordinates stay distinct, copies detached, foreign/out-of-face/out-of-range corners refused.');
