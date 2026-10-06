import assert from 'node:assert/strict';
import {validateObjectMapping,withObjectMapping} from '../editor/animation-glb-mapping.js';
assert.deepEqual(validateObjectMapping([2,1,0],3),[2,1,0]);
for(const v of [[],[0,1],[0,1,1],[true,1,2],[-1,1,2],[4096,1,2]])assert.throws(()=>validateObjectMapping(v,3));
assert.deepEqual(withObjectMapping({object_count:3},'2, 1, 0'),{object_count:3,external_object_nodes:[2,1,0]});assert.deepEqual(withObjectMapping({object_count:3},''),{object_count:3});assert.throws(()=>withObjectMapping({object_count:3},'0, 1, x'));
console.log('Explicit rigid object mapping count, unique indices and binding guards passed.');
