import assert from 'node:assert/strict';
import {decodeVectorAllocationSource,vectorAllocationRequests,decodeVectorAllocationReview} from '../editor/model-vector-allocation.js';
const key='a'.repeat(64),proposed='b'.repeat(64),asset='model';
const face={face_id:`face://source/${key}/0/0`,origin:'source',object_index:0,group_index:0,source_primitive_index:0,current_primitive_index:0};
const preview={vertices:[[0,0,0],[1,0,0],[0,1,0]],objects:[{object_index:0,vertex_start:0,vertex_count:3,triangle_start:0,triangle_count:1}],triangles:[[0,1,2]],materials:[],triangle_colors:[null],triangle_uvs:[null],triangle_materials:[null],triangle_normals:[null]};
const source={schema_version:'legaia.model-vector-allocation-source.v1',asset_id:asset,source_sha256:key,effective_sha256:key,project_source_key:key,allocated_vector_count:0,remaining_vector_budget:4096,new_vector_limit:4096,addressable_table_limit:8192,objects:[{object_index:0,vertex_count:3,normal_count:1,primitive_count:1}],topology:{source_sha256:key,proposed_sha256:key,proposed_byte_length:128,faces:[face]},preview,project_changed:false,gameplay_verified:false};
decodeVectorAllocationSource(source,asset,key);
const requests=vectorAllocationRequests(source,0,'vertices','3, 4, 5');assert.deepEqual(requests,[{object_index:0,kind:'vertices',vectors:[[3,4,5]]}]);
assert.deepEqual(vectorAllocationRequests(source,0,'normals','-32768, +32767, 0\n\n4096,0,0')[0].vectors,[[-32768,32767,0],[4096,0,0]]);
for(const text of ['', '1,2','1,2,3,4','1.5,2,3','NaN,0,0','32768,0,0'])assert.throws(()=>vectorAllocationRequests(source,0,'vertices',text));
assert.throws(()=>vectorAllocationRequests(source,0,'other','1,2,3'));assert.throws(()=>vectorAllocationRequests(source,true,'vertices','1,2,3'));
const audit={...source.topology,proposed_sha256:proposed,allocated_vector_count:1,vector_allocation_count:1,removed_face_ids:[]};
const report={schema_version:'legaia.model-vector-allocation-review.v1',asset_id:asset,source_sha256:key,effective_sha256:key,project_source_key:key,proposed_sha256:proposed,requests,topology:audit,allocation:{source_sha256:key,proposed_sha256:proposed,source_byte_length:128,proposed_byte_length:136,growth_bytes:8,new_vectors:[{object_index:0,kind:'vertices',first_index:3,added_count:1,byte_offset:76}],pointer_relocations:[0,8,16].map(table_field_offset=>({object_index:0,table_field_offset,source_offset:40,current_offset:40}))},current_preview:preview,preview:{...preview,vertices:[...preview.vertices,[3,4,5]],objects:[{...preview.objects[0],vertex_count:4}]},project_changed:false,gameplay_verified:false};
decodeVectorAllocationReview(report,source,requests);
for(const mutate of [v=>v.remaining_vector_budget=1,v=>v.objects[0].vertex_count=4,v=>v.topology.faces[0].object_index='0',v=>v.topology.faces=[],v=>v.topology.proposed_byte_length=1,v=>v.preview.vertices=[[1.5,0,0],[1,0,0],[0,1,0]]]){
  const bad=structuredClone(source);mutate(bad);assert.throws(()=>decodeVectorAllocationSource(bad,asset,key));
}
for(const mutate of [v=>v.proposed_sha256=key,v=>v.allocation.growth_bytes=16,v=>v.allocation.new_vectors[0].first_index=2,v=>v.allocation.pointer_relocations.pop(),v=>v.topology.allocated_vector_count=2,v=>v.topology.faces=[],v=>v.preview.vertices=[[0,0,0],[1,0,0],[0,1,0],[9,9,9]],v=>v.preview.triangles=[[0,1,3]],v=>v.preview.triangle_normals=[[1,2,3]],v=>v.project_changed=true]){
  const bad=structuredClone(report);mutate(bad);assert.throws(()=>decodeVectorAllocationReview(bad,source,requests));
}
const exhausted={...source,allocated_vector_count:4096,remaining_vector_budget:0,topology:{...source.topology,allocated_vector_count:4096}};
assert.throws(()=>vectorAllocationRequests(exhausted,0,'vertices','1,2,3'));
const nativeFull={...source,objects:[{...source.objects[0],normal_count:8192}]};
assert.throws(()=>vectorAllocationRequests(nativeFull,0,'normals','1,2,3'));
assert.throws(()=>decodeVectorAllocationReview(report,source,[...requests,...requests]));
const secondFace={...face,face_id:`face://source/${key}/1/0`,object_index:1};
const multiPreview={...preview,vertices:[...preview.vertices,[10,0,0],[11,0,0],[10,1,0]],
  objects:[preview.objects[0],{...preview.objects[0],object_index:1,vertex_start:3,triangle_start:1}],triangles:[[0,1,2],[3,4,5]]};
const multiSource={...source,objects:[source.objects[0],{...source.objects[0],object_index:1}],
  topology:{...source.topology,proposed_byte_length:256,faces:[face,secondFace]},preview:multiPreview};
const multiReport={...report,topology:{...audit,faces:[face,secondFace]},
  allocation:{...report.allocation,source_byte_length:256,proposed_byte_length:264,new_vectors:[{...report.allocation.new_vectors[0],byte_offset:92}],
    pointer_relocations:[0,1].flatMap(object_index=>report.allocation.pointer_relocations.map(row=>({...row,object_index,source_offset:56,current_offset:56})))},
  current_preview:multiPreview,preview:{...multiPreview,vertices:[...preview.vertices,[3,4,5],[10,0,0],[11,0,0],[10,1,0]],
    objects:[{...preview.objects[0],vertex_count:4},{...multiPreview.objects[1],vertex_start:4}],triangles:[[0,1,2],[4,5,6]]}};
decodeVectorAllocationReview(multiReport,multiSource,requests);
const wrongRemap=structuredClone(multiReport);wrongRemap.preview.triangles[1]=[3,4,5];
assert.throws(()=>decodeVectorAllocationReview(wrongRemap,multiSource,requests));
console.log('Vector source, signed XYZ, native/global budgets, exact reviewed ranges, preserved face content and tamper guards passed.');
