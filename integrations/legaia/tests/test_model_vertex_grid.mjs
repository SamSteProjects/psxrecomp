import assert from 'node:assert/strict';
import {vertexGroupGridPreview} from '../editor/model-vertex-move.js';
const source={preview:{objects:[{object_index:0,vertex_start:0,vertex_count:2}],vertices:[[-8,8,7],[32767,-32768,0]]}};
const candidate=vertexGroupGridPreview(source,0,[0],['x','y'],16);assert.deepEqual(candidate.vertices,[[-16,16,7],[32767,-32768,0]]);assert.deepEqual(source.preview.vertices[0],[-8,8,7]);assert.deepEqual(vertexGroupGridPreview(source,0,[0,1],['y'],16).vertices,[[-8,16,7],[32767,-32768,0]]);
for(const [indices,axes,spacing] of [[[1],['x'],16],[[0],[],16],[[0],['x','x'],16],[[0],['u'],16],[[0],['x'],true],[[0],['x'],0],[[0],['x'],32769],[[0,0],['x'],16]])assert.throws(()=>vertexGroupGridPreview(source,0,indices,axes,spacing));
assert.deepEqual(vertexGroupGridPreview(source,0,[0,1],['x','y','z'],1).vertices,source.preview.vertices);
console.log('Native-grid preview preserves selected axes, signed halfway rounding, untouched rows, source ownership and atomic overflow rejection.');
