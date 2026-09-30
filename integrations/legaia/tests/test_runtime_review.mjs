import assert from 'node:assert/strict';
import fs from 'node:fs';
const source=fs.readFileSync(new URL('../editor/runtime-review.js',import.meta.url),'utf8');
const {captureRuntimeReview,parseRuntimeReview,validateRuntimeReview,MAX_REVIEW_BYTES}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
const node={runtime_node_id:'runtime://sample/0x80001000',epoch_id:'epoch-1',observed_position:{x:1,y:-2,z:3},position_capture_frames:{before:10,after:11},candidate_entity_ids:['scene://town01/actors/man-p1/0001'],binding_confirmed:false,reason:null,
decoded_fields:[{property:'heading_yaw',raw_numeric_value:1024,interpreted_value:{units:1024,degrees:90},confidence:'supported',evidence:['source'],applicability:'actor',unresolved:false,notes:'Captured sample'}],raw_prefix_base64:'DO_NOT_EXPORT',guard_token:'DO_NOT_EXPORT'};
const input={scene_id:'scene://town01',epoch_id:'epoch-1',nodes:[node],exported_at:'2026-09-30T00:00:00.000Z'};
const review=captureRuntimeReview(input),serialized=JSON.stringify(review,null,2)+'\n';
assert(!serialized.includes('DO_NOT_EXPORT'));assert(review.historical&&review.read_only);assert.equal(review.profile_id,null);
assert.deepEqual(parseRuntimeReview(serialized),review);node.observed_position.x=999;assert.equal(review.nodes[0].observed_position.x,1);
for(const change of [r=>r.historical=false,r=>r.read_only=false,r=>r.nodes[0].binding_confirmed=true,r=>r.nodes[0].epoch_id='other',r=>r.nodes.push(structuredClone(r.nodes[0])),r=>r.nodes[0].raw_prefix_base64='payload',r=>r.nodes[0].observed_position.x=Infinity,r=>r.nodes[0].position_capture_frames.after=9,r=>r.nodes[0].candidate_entity_ids.push(r.nodes[0].candidate_entity_ids[0]),r=>r.nodes[0].decoded_fields.push(structuredClone(r.nodes[0].decoded_fields[0])),r=>r.nodes[0].decoded_fields[0].interpreted_value={nested:{more:{deep:{bad:1}}}},r=>r.nodes=Array.from({length:129},()=>structuredClone(r.nodes[0])),r=>r.guard_token='secret']){
 const copy=structuredClone(review);change(copy);assert.throws(()=>validateRuntimeReview(copy));
}
assert.throws(()=>parseRuntimeReview(' '.repeat(MAX_REVIEW_BYTES+1)));
console.log('Runtime metadata review: detached roundtrip, decoded heading, payload redaction, historical/epoch/identity/type/depth/size guards passed.');
