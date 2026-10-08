import fs from 'node:fs';
import assert from 'node:assert/strict';
import {decodeNpcArrivalReview} from '../editor/npc-arrival-authoring.js';
import {npcArrivalPreviewMarkers} from '../editor/npc-arrival-preview.js';
const fixture=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),{request,state}=fixture;
const report=decodeNpcArrivalReview(fixture.report,request,state);
assert.deepEqual(report.proposed_encoded,{entry_x_encoded:128,entry_z_encoded:1,direction_encoded:255});
assert.equal(report.native_review.inspection.record.raw_hex.slice(124,130),'8001ff');
assert(report.authored_change);
for(const mutate of [v=>v.authored_change=false,v=>v.proposed_encoded.direction_encoded=7,v=>v.native_review.changes[0].decoded_byte_offset++,v=>v.native_review.proposed.name='Foreign',v=>v.request.arrival.x=192,v=>v.preview.height_known=true,v=>v.preview.source.draft.transitions.entries[request.transition_id].direction_encoded=0]){
 const bad=structuredClone(fixture.report);mutate(bad);assert.throws(()=>decodeNpcArrivalReview(bad,request,state));
}
assert.throws(()=>decodeNpcArrivalReview(fixture.report,request,{...state,project:{mode:'live'}}));
assert.throws(()=>decodeNpcArrivalReview(fixture.report,request,{...state,npc_arrival_preview_state_key:'0'.repeat(64)}));
const marker=npcArrivalPreviewMarkers(report.preview,5,{draft:false,proposed_arrival:{x:128,z:192,facing_angle_12bit:3584}}).at(-1);
assert.deepEqual([marker.layer,marker.x,marker.y,marker.z,marker.facing_angle_12bit],['Proposed',128,5,192,3584]);
assert.deepEqual(fixture.report,report);
console.log('Actual NPC destination Review, complete source record bytes, direction high bits, native audits, independent ownership, Proposed marker and malformed/Live/stale refusal passed.');
