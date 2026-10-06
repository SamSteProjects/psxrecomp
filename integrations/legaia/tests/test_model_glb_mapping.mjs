import assert from 'node:assert/strict';
import {validateModelObjectMapping,withModelObjectMapping,modelNodeInventory} from '../editor/model-glb-mapping.js';
const binding={profile:{objects:[{},{}]}};
assert.deepEqual(withModelObjectMapping(binding,'1, 0'),{...binding,external_object_nodes:[1,0]});assert.deepEqual(withModelObjectMapping(binding,''),binding);assert.equal(binding.external_object_nodes,undefined);
for(const value of [null,[],[0],[0,0],[0,true],[0,1.5],[0,1024]])assert.throws(()=>validateModelObjectMapping(value,2));
for(const text of ['0,0','1','0, -1','0,1.0','0,1024','0,1e0','0,01'])assert.throws(()=>withModelObjectMapping(binding,text));
const json=JSON.stringify({asset:{version:'2.0'},nodes:[{name:'Part <one>',mesh:1},{name:'Parent\n'}]}),padded=json+' '.repeat((4-json.length%4)%4),bytes=new Uint8Array(20+padded.length),view=new DataView(bytes.buffer);view.setUint32(0,0x46546c67,true);view.setUint32(4,2,true);view.setUint32(8,bytes.length,true);view.setUint32(12,padded.length,true);view.setUint32(16,0x4e4f534a,true);bytes.set(new TextEncoder().encode(padded),20);
assert.equal(modelNodeInventory(bytes),'0: Part <one> · mesh 1\n1: Parent  · group or empty object');
console.log('Model GLB explicit mapping bounds, typed indices, immutable choices and node inventory passed.');
