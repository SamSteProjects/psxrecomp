import assert from 'node:assert/strict';
import {scriptedPlacementPattern as plan} from '../editor/worldmap-scripted-creation-pattern.js';
const ids=Array.from({length:32},(_,i)=>'placement://authored/88888888-8888-4888-8888-'+String(i+1).padStart(12,'0'));
const source={donors:[{seed:{source_cell:100}}],remaining_creation_capacity:32,free_record_indices:[4,6,8,9],target_cells:[126,254,382,127,125,124]};
const draft={count:3,col_step:0,row_step:1,target_cell:126,donor_cell:100,record_index:4,values:{offset:{x:128,y:-16,z:48},yaw_units:1024},shared_script:true},held=JSON.stringify({source,draft,ids});
const result=plan(source,draft,ids);assert.deepEqual(result.map(r=>r.target_cell),[126,254,382]);assert.deepEqual(result.map(r=>r.record_index),[4,6,8]);assert.deepEqual(result.map(r=>r.placement_id),ids.slice(0,3));assert.deepEqual(result[0].values,draft.values);
assert.deepEqual(plan(source,{...draft,count:1,col_step:0,row_step:0},ids),[{placement_id:ids[0],donor_cell:100,target_cell:126,record_index:4,values:draft.values,shared_script:true}]);
assert.deepEqual(plan(source,{...draft,col_step:-1,row_step:0},ids).map(r=>r.target_cell),[126,125,124]);
const maximum={...source,free_record_indices:Array.from({length:32},(_,i)=>i+4),target_cells:Array.from({length:32},(_,i)=>i*128)};
const all=plan(maximum,{...draft,count:32,target_cell:0},ids);assert.equal(all.length,32);assert.equal(all.at(-1).target_cell,31*128);assert.equal(new Set(all.map(r=>r.record_index)).size,32);
assert.equal(JSON.stringify({source,draft,ids}),held);result[0].values.offset.x=0;assert.equal(result[1].values.offset.x,128);assert.equal(draft.values.offset.x,128);
let refusals=0;
for(const bad of [{count:0},{count:33},{count:true},{col_step:1,row_step:0},{col_step:0,row_step:0},{row_step:-1},{row_step:128},{col_step:.5},{record_index:8},{donor_cell:101},{target_cell:129},{shared_script:false},{extra:true},{values:{offset:{x:32768,y:0,z:0},yaw_units:0}}]){assert.throws(()=>plan(source,{...draft,...bad},ids));refusals++;}
for(const badIds of [[],ids.slice(0,2),[ids[0],ids[0],ids[1]],['missing',ids[1],ids[2]]]){assert.throws(()=>plan(source,draft,badIds));refusals++;}
assert.throws(()=>plan({...source,remaining_creation_capacity:2},draft,ids));refusals++;
console.log(JSON.stringify({positive_cases:4,refusals,source_draft_unchanged:true}));
