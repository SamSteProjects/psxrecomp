import assert from 'node:assert/strict';
import {vertexMovePreview,pickProjectedVertex,objectMovePreview,qualifyObjectMoveReview} from '../editor/model-vertex-move.js';
const source={preview:{objects:[{object_index:0,vertex_start:0,vertex_count:1},{object_index:1,vertex_start:1,vertex_count:2}],vertices:[[1,2,3],[4,5,6],[7,8,9]],triangles:[[0,1,2]],normals:[[0,4096,0]]}},before=structuredClone(source);
const proposed=vertexMovePreview(source,1,1,[-32768,16,32767]);
assert.deepEqual(proposed.vertices,[[1,2,3],[4,5,6],[-32768,16,32767]]);assert.deepEqual(source,before);assert.deepEqual(proposed.triangles,source.preview.triangles);assert.deepEqual(proposed.normals,source.preview.normals);proposed.vertices[0][0]=99;assert.deepEqual(source,before);
for(const [object,index,values] of [[2,0,[0,0,0]],[0,1,[0,0,0]],[1,-1,[0,0,0]],[1,0,[0,0,32768]],[1,0,[0,0,-32769]],[1,0,[0,0,.5]],[1,0,[0,NaN,0]],[1,0,[0,0]]])assert.throws(()=>vertexMovePreview(source,object,index,values));
console.log('Vertex draft: exact object-local row, signed16 bounds, immutable Current and retained topology/normals passed');
assert.equal(pickProjectedVertex([{index:8,x:10,y:10,depth:9},{index:3,x:10,y:10,depth:4},{index:2,x:10,y:10,depth:4}],10,10),2);
assert.equal(pickProjectedVertex([{index:0,x:10,y:10,depth:2},{index:1,x:11,y:11,depth:1}],11,11),1);
assert.equal(pickProjectedVertex([{index:0,x:10,y:10,depth:2}],20,10),0);
assert.equal(pickProjectedVertex([{index:0,x:10,y:10,depth:2}],20.1,10),null);
assert.equal(pickProjectedVertex([null,{index:0,x:NaN,y:10,depth:2}],10,10),null);
assert.throws(()=>pickProjectedVertex([],Infinity,0));assert.throws(()=>pickProjectedVertex([],0,0,33));
console.log('Vertex picking: bounded screen radius, nearest point, depth/index ties and malformed projections passed');

const translated=objectMovePreview(source,1,[16,-8,32]);
assert.deepEqual(translated.vertices,[[1,2,3],[20,-3,38],[23,0,41]]);assert.deepEqual(source,before);assert.deepEqual(translated.normals,source.preview.normals);assert.deepEqual(translated.triangles,source.preview.triangles);
for(const [owner,offset] of [[2,[0,0,0]],[1,[32767,0,0]],[1,[0,-32769,0]],[1,[0,0,.5]],[1,[0,0,NaN]],[1,[0,0]]])assert.throws(()=>objectMovePreview(source,owner,offset));
console.log('Object translation: all owned rows, other object unchanged, immutable Current, overflow and retained normals/topology passed');
assert.throws(()=>objectMovePreview({preview:{objects:[{object_index:0,vertex_start:0,vertex_count:1}],vertices:[[-32768,0,0]]}},0,[-1,0,0]));

const boundSource=structuredClone(source);boundSource.preview.bounds={min:[1,2,3],max:[7,8,9]};const boundMove=objectMovePreview(boundSource,1,[16,-8,32]);assert.deepEqual(boundMove.bounds,{min:[1,-3,3],max:[23,2,41]});
const request={asset_id:'asset://fixture/model/0',object_index:1,expected_sha256:'a'.repeat(64)},expected={source_sha256:'b'.repeat(64),current_preview:source.preview,preview:translated},report={asset_id:request.asset_id,object_index:1,operation:'translation',source_sha256:expected.source_sha256,effective_sha256:request.expected_sha256,project_changed:false,proposed_sha256:'c'.repeat(64),current_preview:source.preview,preview:translated};
assert.deepEqual(qualifyObjectMoveReview(report,request,expected),report);
for(const mutation of [r=>r.object_index=0,r=>r.source_sha256='d'.repeat(64),r=>r.effective_sha256='d'.repeat(64),r=>r.project_changed=true,r=>r.proposed_sha256=request.expected_sha256,r=>r.preview.vertices[0][0]++,r=>r.current_preview.normals[0][0]++]){const changed=structuredClone(report);mutation(changed);assert.throws(()=>qualifyObjectMoveReview(changed,request,expected));}
console.log('Movement review: complete Current/Proposed geometry, exact source/owner/hash, bounds and forged/no-op replies passed');
assert.deepEqual(qualifyObjectMoveReview({...report,preview:Object.fromEntries(Object.entries(report.preview).reverse())},request,expected).preview,report.preview);
const enriched=structuredClone(report);enriched.preview.textures=[];enriched.current_preview.animation_support={status:'unposed'};assert.deepEqual(qualifyObjectMoveReview(enriched,request,expected),enriched);
