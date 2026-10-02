import assert from 'node:assert/strict';
import {mergeScenePlacementSelection} from '../editor/scene-placement-selection.js';

const actor='scene://town01/actors/man-p1/0012';
const decor='environment://town01/field-map/decorations/01833';
const other='scene://town01/actors/man-p1/0001';
const eligible=new Set([actor,decor,other]);
const current=Object.freeze([actor,actor]),hits=Object.freeze([decor,decor]);
assert.deepEqual(mergeScenePlacementSelection(current,hits,eligible),[decor]);
assert.deepEqual(mergeScenePlacementSelection(current,hits,eligible,true),[decor,actor].sort());
assert.deepEqual(mergeScenePlacementSelection([actor],[actor,actor],eligible),[actor]);
assert.deepEqual(mergeScenePlacementSelection([actor],[],eligible),[]);
assert.deepEqual(mergeScenePlacementSelection([actor],[],eligible,true),[actor]);
assert.deepEqual(mergeScenePlacementSelection([],[],new Set()),[]);
assert.deepEqual(mergeScenePlacementSelection([other,actor],[decor],eligible,true),[other,actor,decor].sort());
const returned=mergeScenePlacementSelection(current,hits,eligible,true);
returned.push(other);
assert.deepEqual(current,[actor,actor]);assert.deepEqual(hits,[decor,decor]);
assert.deepEqual([...eligible],[actor,decor,other]);

for(const args of [
  [null,[],eligible],[[],null,eligible],[{},[],eligible],[[],{},eligible],
  [[],[],[]],[[],[],null],[[],[],eligible,1],[[],[],eligible,null],
  [[],[],new Set([null])],[[],[],new Set([''])],
  [[null],[],eligible],[[],[null],eligible],[[1],[],eligible],[[],[''],eligible],
  [['unknown'],[],eligible],[[],['unknown'],eligible],
  [Array(1),[],eligible],[[],Array(1),eligible],
])assert.throws(()=>mergeScenePlacementSelection(...args));

const many=Array.from({length:129},(_,i)=>`placement-${String(i).padStart(3,'0')}`);
const manyEligible=new Set(many);
assert.deepEqual(mergeScenePlacementSelection([],many.slice(0,128),manyEligible),many.slice(0,128));
assert.deepEqual(mergeScenePlacementSelection(many.slice(0,128),many.slice(0,128),manyEligible,true),many.slice(0,128));
assert.throws(()=>mergeScenePlacementSelection([],many,manyEligible),/at most 128/);
const before=[...many.slice(0,128)],overflowHits=[many[128]];
assert.throws(()=>mergeScenePlacementSelection(before,overflowHits,manyEligible,true),/at most 128/);
assert.deepEqual(before,many.slice(0,128));assert.deepEqual(overflowHits,[many[128]]);
// Replacement may reduce a large current input; the bound belongs to the result.
assert.deepEqual(mergeScenePlacementSelection(many,[actor],new Set([...many,actor])),[actor]);
assert.deepEqual(mergeScenePlacementSelection([],Array(129).fill(actor),eligible),[actor]);
console.log('Scene placement selection replacement/extension, canonical deduplication, active eligibility, 128 bound and immutable atomic rejection passed.');
