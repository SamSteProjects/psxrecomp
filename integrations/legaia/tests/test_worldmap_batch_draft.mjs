import assert from 'node:assert/strict';
import {worldPlacementBatchDraft} from '../editor/worldmap-placement-state.js';
const row=(id,x,count=1)=>({record_id:id,writable:true,source_cell_count:count,placements:Array.from({length:count},(_,i)=>({entity_id:id+'/'+i})),current_values:{offset:{x,y:0,z:0},yaw_units:0}}),source={records:[row('0001',-30000,2),row('0002',0)]},held=structuredClone(source);
const proposal=worldPlacementBatchDraft(source,['0001'],{x:40000,y:-16,z:64,yaw_units:-256},true);
assert.deepEqual(proposal.records[0].current_values,{offset:{x:10000,y:-16,z:64},yaw_units:3840});assert.deepEqual(proposal.records[1],source.records[1]);assert.deepEqual(source,held);
for(const [ids,delta,shared] of [[['0001'],{x:0,y:0,z:0,yaw_units:0},false],[['0002','0001'],{x:0,y:0,z:0,yaw_units:0},true],[['0001','0001'],{x:0,y:0,z:0,yaw_units:0},true],[['0003'],{x:0,y:0,z:0,yaw_units:0},true],[['0001'],{x:-40000,y:0,z:0,yaw_units:0},true],[['0001'],{x:65536,y:0,z:0,yaw_units:0},true],[['0001'],{x:0,y:0,z:0,yaw_units:4096},true]])assert.throws(()=>worldPlacementBatchDraft(source,ids,delta,shared));
const incomplete=structuredClone(source);incomplete.records[0].placements.pop();assert.throws(()=>worldPlacementBatchDraft(incomplete,['0001'],{x:0,y:0,z:0,yaw_units:0},true));
console.log('Batch draft native arithmetic, yaw wrap, large deltas, ownership/consent/bounds and immutable Current source passed.');
