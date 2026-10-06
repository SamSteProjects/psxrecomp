import assert from 'node:assert/strict';import {validateExternalSampling,validateExternalSamplingRange} from '../editor/animation-glb-sampling.js';
assert.deepEqual(validateExternalSampling({start_seconds:2,rate:-1}),{start_seconds:2,rate:-1});assert.equal(validateExternalSampling({start_seconds:3600,rate:0}).rate,0);
for(const value of [null,[],{}, {start_seconds:0,rate:1,extra:0},{start_seconds:true,rate:1},{start_seconds:-1,rate:1},{start_seconds:3601,rate:1},{start_seconds:0,rate:NaN},{start_seconds:0,rate:17},{start_seconds:0,rate:-17}])assert.throws(()=>validateExternalSampling(value));
console.log('External sampling start, reverse/hold rate, exact fields and numeric guards passed.');

for(const mode of ['repeat','ping_pong'])assert.deepEqual(validateExternalSampling({start_seconds:2,rate:-1,mode}),{start_seconds:2,rate:-1,mode});
assert.deepEqual(validateExternalSampling({start_seconds:0,rate:1,mode:'clamp'}),{start_seconds:0,rate:1});
for(const mode of [null,true,0,'loop',[],{}])assert.throws(()=>validateExternalSampling({start_seconds:0,rate:1,mode}));
const binding={external_sampling:{start_seconds:2,rate:1,mode:'repeat'}};
validateExternalSamplingRange({external_time_range:{start_seconds:2,end_seconds:4}},binding);validateExternalSamplingRange({external_time_range:null},binding);
for(const report of [{},{external_time_range:{}},{external_time_range:{start_seconds:4,end_seconds:2}},{external_time_range:{start_seconds:0,end_seconds:Infinity}}])assert.throws(()=>validateExternalSamplingRange(report,binding));
assert.throws(()=>validateExternalSamplingRange({external_time_range:null},{}));
console.log('Repeat/ping-pong modes, legacy clamp normalization, static range and malformed timeline report rejection passed.');
