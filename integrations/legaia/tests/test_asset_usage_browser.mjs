import assert from 'node:assert/strict';
import {filterAssetUsage} from '../editor/asset-usage-browser.js';
const refs=Array.from({length:165},(_,i)=>({source_id:'scene://fixture/actors/'+String(i).padStart(4,'0'),source_name:'Actor '+i,scene_id:i<100?'scene://first':'scene://second',imported:i%2===0,effective:i%2===1,kind:'initial_animation_assignment',effective_source:{record_id:'proof'}})),held=structuredClone(refs);
let result=filterAssetUsage(refs);assert.equal(result.rows.length,64);assert.equal(result.pages,3);assert.equal(result.matching,165);
result=filterAssetUsage(refs,{page:1});assert.equal(result.rows[0].source_id,refs[64].source_id);assert.equal(result.rows.length,64);
result=filterAssetUsage(refs,{page:99});assert.equal(result.page,2);assert.equal(result.rows.length,37);
for(const layer of ['retail','current']){const r=filterAssetUsage(refs,{layer,scene:'scene://first',search:'Actor 1'});const expected=refs.filter(ref=>ref[layer==='retail'?'imported':'effective']&&ref.scene_id==='scene://first'&&ref.source_name.toLowerCase().includes('actor 1'));assert.equal(r.matching,expected.length);assert.deepEqual(r.rows,expected);}
assert.equal(filterAssetUsage(refs,{search:refs[164].source_id.toUpperCase()}).matching,1);assert.equal(filterAssetUsage(refs,{scene:'missing'}).matching,0);
result.rows[0].effective_source.record_id='changed';assert.deepEqual(refs,held);
for(const [records,filters] of [[refs,{layer:'live'}],[refs,{page:-1}],[refs,{search:'x'.repeat(1025)}],[[refs[0],{...refs[0],scene_id:'other'}],{}],[[{...refs[0],imported:false,effective:false}],{}],[[{...refs[0],effective:'yes'}],{}]])assert.throws(()=>filterAssetUsage(records,filters));
assert.deepEqual(filterAssetUsage([]),{total:0,matching:0,page:0,pages:1,rows:[]});
console.log('Asset usage layer/scene/name/ID filters, 64-row pages, clamping, detached nested evidence and invalid/ambiguous metadata refusal passed.');
