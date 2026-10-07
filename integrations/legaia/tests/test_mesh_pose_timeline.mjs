import assert from 'node:assert/strict';
import {meshPoseTimeRange} from '../editor/mesh-pose-timeline.js';
const row={node_index:1,path:'translation',key_count:2,interpolation:'LINEAR',start_time:2,end_time:5};
const sampled={animation_index:1,sampled_channels:[row,{...row,node_index:2,path:'rotation',start_time:3,end_time:8}],excluded_channels:[{node_index:3,path:'translation'}]};
const range=meshPoseTimeRange(sampled,1);assert.equal(range.start,2);assert.equal(range.end,8);assert.equal(range.channels.length,2);range.channels[0].start_time=0;assert.equal(row.start_time,2);
assert.equal(meshPoseTimeRange(sampled,0),null);assert.equal(meshPoseTimeRange(null,1),null);assert.equal(meshPoseTimeRange({...sampled,sampled_channels:[]},1),null);
assert.deepEqual(meshPoseTimeRange({animation_index:0,sampled_channels:[{...row,key_count:1,start_time:4,end_time:4}]},0),{start:4,end:4,channels:[{...row,key_count:1,start_time:4,end_time:4}]});
let refused=0;for(const change of [r=>r.start_time=-1,r=>r.end_time=3601,r=>r.start_time=NaN,r=>r.end_time=1,r=>r.key_count=0,r=>r.node_index=true,r=>r.interpolation='BAD',r=>r.path='unknown']){const bad=structuredClone(sampled);change(bad.sampled_channels[0]);assert.throws(()=>meshPoseTimeRange(bad,1));refused++;}
assert.throws(()=>meshPoseTimeRange({...sampled,sampled_channels:[row,row]},1));refused++;
console.log(JSON.stringify({selected_channel_union:true,constant_track:true,absent_or_other_clip_hidden:true,detached_metadata:true,refusals:refused}));
