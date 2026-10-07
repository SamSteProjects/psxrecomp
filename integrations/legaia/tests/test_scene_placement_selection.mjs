import assert from 'node:assert/strict';
import {mergeScenePlacementSelection,invertScenePlacementSelection,scenePlacementSelectionKind,matchingModelPlacementIds} from '../editor/scene-placement-selection.js';

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

assert.deepEqual(invertScenePlacementSelection([actor,other],[actor,decor,decor],eligible),[decor,other].sort());
assert.deepEqual(invertScenePlacementSelection([actor],[actor],eligible),[]);
assert.deepEqual(invertScenePlacementSelection([actor],[],eligible),[actor]);
assert.deepEqual(invertScenePlacementSelection(many.slice(0,128),many,manyEligible),[many[128]]);
assert.throws(()=>invertScenePlacementSelection([],many,manyEligible),/at most 128/);
for(const [current,hits] of [[['alien'],[]],[[],['alien']],[Array(1),[]],[[],Array(1)],[null,[]],[[],null]])assert.throws(()=>invertScenePlacementSelection(current,hits,eligible));
assert.deepEqual(current,[actor,actor]);assert.deepEqual(hits,[decor,decor]);
console.log('Visible inversion: offscreen selections held, duplicate hits toggle once, empty/exact sets, overflow and malformed input refused without mutation.');

const kinds={actors:new Set([actor,other]),npcs:new Set(['draft']),decorations:new Set([decor])};
assert.equal(scenePlacementSelectionKind([actor,other],kinds),'actors');assert.equal(scenePlacementSelectionKind([decor],kinds),'scenery');assert.equal(scenePlacementSelectionKind([actor,decor],kinds),'mixed');assert.equal(scenePlacementSelectionKind(['draft'],kinds),'mixed');assert.equal(scenePlacementSelectionKind([],kinds),'empty');
assert.throws(()=>scenePlacementSelectionKind(['alien'],kinds));assert.throws(()=>scenePlacementSelectionKind([actor],{...kinds,npcs:new Set([actor])}));assert.throws(()=>scenePlacementSelectionKind([actor],{...kinds,actors:[]}));
console.log('Placement authoring handoff: current SDK actor/scenery sets, mixed/NPC retention, empty and conflicting/foreign identity refusal passed.');

const model='asset://fixture/model/one',second='asset://fixture/model/two';
const modelRows=[{entity_id:actor,asset_id:model},{entity_id:decor,asset_id:model},{entity_id:other,asset_id:second},{entity_id:'ground',asset_id:model},{entity_id:'unbound',asset_id:null}];
const modelBefore=structuredClone(modelRows);
assert.deepEqual(matchingModelPlacementIds(modelRows,actor,eligible),[actor,decor].sort());
assert.deepEqual(matchingModelPlacementIds(modelRows,decor,eligible),[actor,decor].sort());
assert.deepEqual(matchingModelPlacementIds(modelRows,other,eligible),[other]);
assert.deepEqual(modelRows,modelBefore);
const draftRows=[...modelRows,{entity_id:'draft',asset_id:model}];
assert.deepEqual(matchingModelPlacementIds(draftRows,'draft',new Set([...eligible,'draft'])),[actor,decor,'draft'].sort());
for(const rows of [null,Array(1),[...modelRows,modelRows[0]],[{entity_id:actor,asset_id:''}],[{entity_id:actor,asset_id:42}],[{entity_id:'',asset_id:model}],Array(642).fill(modelRows[0])])assert.throws(()=>matchingModelPlacementIds(rows,actor,eligible));
for(const focus of ['foreign','ground','unbound',null])assert.throws(()=>matchingModelPlacementIds(modelRows,focus,new Set([...eligible,'unbound'])));
assert.throws(()=>matchingModelPlacementIds([{entity_id:actor,asset_id:null}],actor,eligible));
assert.throws(()=>matchingModelPlacementIds(many.map(entity_id=>({entity_id,asset_id:model})),many[0],manyEligible),/at most 128/);
assert.deepEqual(matchingModelPlacementIds(many.slice(0,128).map(entity_id=>({entity_id,asset_id:model})),many[0],manyEligible),many.slice(0,128));
console.log('Model-instance selection: exact current model identity, actor/NPC/scenery membership, nonplacement exclusion, detached inputs and missing/duplicate/oversized refusal passed.');
