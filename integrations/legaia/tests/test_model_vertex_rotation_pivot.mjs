import assert from 'node:assert/strict';
import {vertexGroupRotatePreview,vertexGroupAnglePreview} from '../editor/model-vertex-move.js';
const source={preview:{objects:[{object_index:0,vertex_start:0,vertex_count:3}],vertices:[[0,0,0],[10,0,0],[0,10,0]],normals:[[0,1,0]],triangles:[[0,1,2]]}},before=structuredClone(source),pivot=[10,-20,30];
assert.deepEqual(vertexGroupRotatePreview(source,0,[0,1],'y',1,pivot).vertices,[[-20,0,40],[-20,0,30],[0,10,0]]);
assert.deepEqual(vertexGroupAnglePreview(source,0,[0,1],'y',512,pivot).vertices,[[-18,0,16],[-11,0,9],[0,10,0]]);
for(const axis of ['x','y','z'])for(const [turn,angle] of [[-1,3072],[1,1024],[2,2048]])assert.deepEqual(vertexGroupAnglePreview(source,0,[0,1],axis,angle,pivot),vertexGroupRotatePreview(source,0,[0,1],axis,turn,pivot));
assert.deepEqual(vertexGroupAnglePreview(source,0,[0,1],'y',0,[-32768,32767,0]).vertices,source.preview.vertices);
for(const invalid of [null,[],[0],[0,0],[0,0,0,0],[true,0,0],[0.5,0,0],['0',0,0],[32768,0,0],[-32769,0,0],Array(3)]){
 assert.throws(()=>vertexGroupRotatePreview(source,0,[0,1],'y',1,invalid));assert.throws(()=>vertexGroupAnglePreview(source,0,[0,1],'y',512,invalid));
}
assert.throws(()=>vertexGroupRotatePreview(source,0,[0,1],'y',2,[32767,0,0]));assert.throws(()=>vertexGroupAnglePreview(source,0,[0,1],'y',2048,[32767,0,0]));assert.deepEqual(source,before);
console.log('Explicit rotation pivots: literal words, cardinal parity, no-op, bounds and immutable source passed.');
