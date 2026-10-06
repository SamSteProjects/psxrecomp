import assert from 'node:assert/strict';
import {linkedVertexGroup,invertVertexGroup} from '../editor/model-vertex-connectivity.js';
const p={vertices:Array.from({length:9},()=>[0,0,0]),triangles:[[0,1,2],[3,4,5],[4,5,6],[7,8,8]],objects:[{object_index:0,vertex_start:0,vertex_count:3,triangle_start:0,triangle_count:1},{object_index:1,vertex_start:3,vertex_count:6,triangle_start:1,triangle_count:3}]};
assert.deepEqual(linkedVertexGroup(p,1,[0]),[0,1,2,3]);assert.deepEqual(linkedVertexGroup(p,1,[4]),[4,5]);assert.deepEqual(linkedVertexGroup(p,1,[0,4]),[0,1,2,3,4,5]);assert.deepEqual(invertVertexGroup(p,1,[0,2]),[1,3,4,5]);assert.deepEqual(invertVertexGroup(p,0,[0,1,2]),[]);assert.deepEqual(linkedVertexGroup(p,0,[0]),[0,1,2]);
const before=structuredClone(p);const changed=linkedVertexGroup(p,1,[0]);changed.push(99);assert.deepEqual(p,before);
const invalid=structuredClone(p);invalid.triangles[1][0]=0;assert.throws(()=>linkedVertexGroup(invalid,1,[0]));
for(const indices of [[],[0,0],[true],[6]])assert.throws(()=>linkedVertexGroup(p,1,indices));
const large={vertices:Array(4098).fill([0,0,0]),objects:[{object_index:0,vertex_start:0,vertex_count:4098,triangle_start:0,triangle_count:4096}],triangles:Array.from({length:4096},(_,i)=>[i,i+1,i+2])};assert.throws(()=>linkedVertexGroup(large,0,[0]),/exceeds 4096/);assert.throws(()=>invertVertexGroup(large,0,[0]),/exceeds 4096/);
console.log('Current triangle connectivity and inverse groups preserve object scope, separate coincident/disconnected vertices, retain source data and reject overflow/invalid references atomically.');
