import assert from 'node:assert/strict';
import {rescaleStoredNormal} from '../editor/model-normal-length.js';
for(const [vector,length,expected] of [[[3,4,0],10,[6,8,0]],[[-3,-4,0],10,[-6,-8,0]],[[0,0,0],4096,[0,0,0]],[[-32768,0,0],32767,[-32767,0,0]],[[1,1,1],1,[1,1,1]]])assert.deepEqual(rescaleStoredNormal(vector,length),expected);
for(const [vector,length] of [[[0,0,1],true],[[0,0,1],0],[[0,0,1],32768],[[0,0,1],1.5],[[32768,0,0],4096],[[0,0],4096]])assert.throws(()=>rescaleStoredNormal(vector,length));
console.log('Exact stored-normal rescaling, zeros, signed extremes and input domains passed.');
