import assert from 'node:assert/strict';
import {hierarchyGroupExpanded,revealHierarchyEntity,revealHierarchyEntities,matchingHierarchyPlacementIds} from '../editor/hierarchy-groups.js';
const state={collapsed:new Set(['actors','script'])};
assert.equal(hierarchyGroupExpanded('actors',state),false);assert.equal(hierarchyGroupExpanded('environment',state),true);
assert.equal(hierarchyGroupExpanded('actors',state,'actor 0002'),true);assert.equal(hierarchyGroupExpanded('actors',state,'  '),false);
assert.deepEqual([...state.collapsed],['actors','script']);
for(const id of ['Unknown','__proto__','constructor',null])assert.throws(()=>hierarchyGroupExpanded(id,state));
assert.throws(()=>hierarchyGroupExpanded('actors',{collapsed:[]}));
console.log('Hierarchy folds use explicit UI groups; search expands presentation without changing saved folds.');
const events=[],header={dataset:{hierarchyGroup:'actors'},getAttribute:()=> 'false',click(){events.push('expand');row.hidden=false;}};
const row={title:'scene://fixture/actors/man-p1/0001',hidden:true,disabled:false,previousElementSibling:header,scrollIntoView:options=>events.push(['scroll',options]),focus:options=>events.push(['focus',options])},root={querySelectorAll:()=>[row]};
assert.equal(revealHierarchyEntity(root,row.title),true);assert.deepEqual(events,['expand',['scroll',{block:'nearest'}],['focus',{preventScroll:true}]]);
assert.equal(revealHierarchyEntity(root,'unknown'),false);row.disabled=true;assert.equal(revealHierarchyEntity(root,row.title),false);assert.equal(revealHierarchyEntity(root,null),false);
console.log('Reveal expands an exact selected row and focuses without dispatching its entity selection action.');

const groupEvents=[],one={title:'actor',hidden:true,disabled:false},two={title:'scenery',hidden:true,disabled:false},unrelated={title:'script',hidden:true};
const actorHeading={dataset:{hierarchyGroup:'actors'},getAttribute:()=> 'false',click(){groupEvents.push('actors');one.hidden=false;}},sceneryHeading={dataset:{hierarchyGroup:'environment'},getAttribute:()=> 'false',click(){groupEvents.push('environment');two.hidden=false;}};
one.previousElementSibling=actorHeading;two.previousElementSibling=sceneryHeading;
for(const item of [one,two]){item.scrollIntoView=()=>groupEvents.push('scroll '+item.title);item.focus=()=>groupEvents.push('focus '+item.title);}
const groupRoot={querySelectorAll:()=>[one,two,unrelated]};assert.equal(revealHierarchyEntities(groupRoot,['actor','scenery'],'scenery'),true);assert.deepEqual(groupEvents,['actors','environment','scroll scenery','focus scenery']);assert.equal(unrelated.hidden,true);
groupEvents.length=0;one.hidden=true;two.hidden=true;
for(const ids of [[],['actor','actor'],['actor','missing'],Array(2),[null],Array.from({length:129},(_,i)=>String(i))])assert.equal(revealHierarchyEntities(groupRoot,ids),false);
assert.equal(revealHierarchyEntities(groupRoot,['actor','scenery'],'missing'),false);two.disabled=true;assert.equal(revealHierarchyEntities(groupRoot,['actor','scenery']),false);assert.deepEqual(groupEvents,[]);assert.equal(one.hidden,true);
console.log('Group reveal: all selected folds expand, active focus held, unrelated folds preserved, invalid/duplicate/missing/disabled/oversized requests refused before presentation changes.');

const matchesRoot={querySelectorAll:()=>[{title:'actor',hidden:true},{title:'scenery',hidden:false},{title:'resource'},{title:'draft'},{title:'disabled',disabled:true}]},eligible=new Set(['actor','scenery','draft','disabled']);
assert.deepEqual(matchingHierarchyPlacementIds(matchesRoot,eligible),['actor','draft','scenery']);
assert.throws(()=>matchingHierarchyPlacementIds(matchesRoot,[]));assert.throws(()=>matchingHierarchyPlacementIds(matchesRoot,new Set([null])));
assert.throws(()=>matchingHierarchyPlacementIds({querySelectorAll:()=>[{title:'actor'},{title:'actor'}]},eligible),/duplicate/);
assert.throws(()=>matchingHierarchyPlacementIds({querySelectorAll:()=>Array.from({length:129},(_,i)=>({title:String(i)}))},new Set(Array.from({length:129},(_,i)=>String(i)))),/128/);
console.log('Typed-query placement results: exact eligible identities, folded rows included, resources/disabled rows excluded, canonical IDs and duplicate/overflow refusal passed.');
