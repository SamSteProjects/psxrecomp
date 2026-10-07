import assert from 'node:assert/strict';
import {growVertexGroup,shrinkVertexGroup} from '../editor/model-vertex-connectivity.js';
const p={vertices:Array.from({length:9},()=>[0,0,0]),triangles:[[0,1,2],[3,4,5],[4,5,6],[7,8,8]],objects:[{object_index:0,vertex_start:0,vertex_count:3,triangle_start:0,triangle_count:1},{object_index:1,vertex_start:3,vertex_count:6,triangle_start:1,triangle_count:3}]},before=structuredClone(p);
assert.deepEqual(growVertexGroup(p,1,[0]),[0,1,2]);assert.deepEqual(growVertexGroup(p,1,[0,1,2]),[0,1,2,3]);assert.deepEqual(growVertexGroup(p,1,[0,4]),[0,1,2,4,5]);
assert.deepEqual(shrinkVertexGroup(p,1,[0,1,2]),[0]);assert.deepEqual(shrinkVertexGroup(p,1,[0,1,2,3]),[0,1,2,3]);assert.deepEqual(shrinkVertexGroup(p,1,[4]),[]);assert.deepEqual(shrinkVertexGroup(p,1,[4,5]),[4,5]);
const isolated={vertices:[[0,0,0],[0,0,0]],objects:[{object_index:0,vertex_start:0,vertex_count:2,triangle_start:0,triangle_count:0}],triangles:[]};assert.deepEqual(growVertexGroup(isolated,0,[1]),[1]);assert.deepEqual(shrinkVertexGroup(isolated,0,[1]),[1]);
const selected=[2,1,0],saved=selected.slice();growVertexGroup(p,1,selected);shrinkVertexGroup(p,1,selected);assert.deepEqual(selected,saved);assert.deepEqual(p,before);
for(const fn of [growVertexGroup,shrinkVertexGroup]){
 for(const indices of [[],[0,0],[true],[6]])assert.throws(()=>fn(p,1,indices));
 const invalid=structuredClone(p);invalid.triangles[1][0]=0;assert.throws(()=>fn(invalid,1,[0]));invalid.triangles[1]=[3,4];assert.throws(()=>fn(invalid,1,[0]));
}
const large={vertices:Array(4098).fill([0,0,0]),objects:[{object_index:0,vertex_start:0,vertex_count:4098,triangle_start:0,triangle_count:4096}],triangles:Array.from({length:4096},(_,i)=>[0,i+1,i+2])};assert.throws(()=>growVertexGroup(large,0,[0]),/exceeds 4096/);assert.deepEqual(shrinkVertexGroup(large,0,[0]),[]);
console.log('One-ring growth and boundary erosion preserve object scope, isolated/full-component vertices and immutable inputs; malformed topology and growth overflow reject atomically.');
