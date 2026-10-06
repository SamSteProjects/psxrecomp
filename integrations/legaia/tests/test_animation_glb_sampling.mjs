import assert from 'node:assert/strict';import {validateExternalSampling} from '../editor/animation-glb-sampling.js';
assert.deepEqual(validateExternalSampling({start_seconds:2,rate:-1}),{start_seconds:2,rate:-1});assert.equal(validateExternalSampling({start_seconds:3600,rate:0}).rate,0);
for(const value of [null,[],{}, {start_seconds:0,rate:1,extra:0},{start_seconds:true,rate:1},{start_seconds:-1,rate:1},{start_seconds:3601,rate:1},{start_seconds:0,rate:NaN},{start_seconds:0,rate:17},{start_seconds:0,rate:-17}])assert.throws(()=>validateExternalSampling(value));
console.log('External sampling start, reverse/hold rate, exact fields and numeric guards passed.');
