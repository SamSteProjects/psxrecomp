import assert from 'node:assert/strict';
import fs from 'node:fs';
const source=fs.readFileSync(new URL('../editor/runtime-review.js',import.meta.url),'utf8');
const {captureRuntimeReview,parseRuntimeReview,validateRuntimeReview,compareRuntimeReviews,historicalRuntimePositions,historicalRuntimeComparisonPositions,historicalSampleHits,MAX_REVIEW_BYTES}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
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

const baseline=structuredClone(review),later=structuredClone(review);
later.nodes[0].observed_position={x:65,y:null,z:3};later.nodes[0].decoded_fields[0].confidence='uncertain';
later.nodes[0].decoded_fields[0].unresolved=true;
later.nodes.push({...structuredClone(later.nodes[0]),runtime_node_id:'new-key'});
baseline.nodes.push({...structuredClone(baseline.nodes[0]),runtime_node_id:'old-key'});
const comparison=compareRuntimeReviews(baseline,later),pair=comparison.rows.find(row=>row.runtime_node_id===node.runtime_node_id);
assert.equal(pair.status,'paired_changed');assert.deepEqual(pair.position_delta,{x:64,y:null,z:0});
assert.equal(pair.changed_fields[0].before.confidence,'supported');assert.equal(pair.changed_fields[0].after.unresolved,true);
assert.equal(comparison.rows.find(row=>row.runtime_node_id==='old-key').status,'before_only');
assert.equal(comparison.rows.find(row=>row.runtime_node_id==='new-key').status,'after_only');
assert(comparison.historical&&comparison.read_only&&!comparison.identity_confirmed);assert(comparison.rows.every(row=>!row.identity_confirmed));
later.nodes[0].observed_position.x=500;assert.equal(pair.after.observed_position.x,65);
for(const key of ['scene_id','epoch_id','profile_id']){const other=structuredClone(review);other[key]='different';if(key==='epoch_id')other.nodes[0].epoch_id='different';assert.throws(()=>compareRuntimeReviews(review,other),/same declared/);}
const reorder=structuredClone(review);reorder.nodes[0].decoded_fields[0]=Object.fromEntries(Object.entries(reorder.nodes[0].decoded_fields[0]).reverse());
assert.equal(compareRuntimeReviews(review,reorder).rows[0].status,'paired_unchanged');
const hugeA=structuredClone(review),hugeB=structuredClone(review);hugeA.nodes[0].observed_position.x=-Number.MAX_VALUE;hugeB.nodes[0].observed_position.x=Number.MAX_VALUE;
assert.equal(compareRuntimeReviews(hugeA,hugeB).rows[0].position_delta.x,null);
assert.throws(()=>compareRuntimeReviews({...review,historical:false},review));
console.log('Historical comparison: context rejection, detached evidence, unknown coordinates, field changes, file-only keys, semantic ordering and overflow passed.');

const spatial=historicalRuntimePositions(review,{scene_id:'scene://town01',mode:'edit'});assert.equal(spatial.nodes.length,1);assert.equal(spatial.skipped,0);spatial.nodes[0].observed_position.x=40;assert.equal(review.nodes[0].observed_position.x,1);
for(const context of [{scene_id:'scene://town02',mode:'edit'},{scene_id:'scene://town01',mode:'live'},{}])assert.throws(()=>historicalRuntimePositions(review,context));
const incomplete=structuredClone(review);incomplete.nodes[0].observed_position.y=null;assert.equal(historicalRuntimePositions(incomplete,{scene_id:review.scene_id,mode:'edit'}).skipped,1);incomplete.nodes[0].observed_position.y=1e9;assert.equal(historicalRuntimePositions(incomplete,{scene_id:review.scene_id,mode:'edit'}).nodes.length,0);assert.throws(()=>historicalRuntimePositions({...review,historical:false},{scene_id:review.scene_id,mode:'edit'}));
console.log('Historical viewport samples: detached metadata, matching Edit scene, complete bounded XYZ and authority rejection passed.');

const spatialA=structuredClone(review),spatialB=structuredClone(review);spatialB.nodes[0].observed_position.x+=64;
spatialA.nodes.push({...structuredClone(spatialA.nodes[0]),runtime_node_id:'before-only'});spatialB.nodes.push({...structuredClone(spatialB.nodes[0]),runtime_node_id:'after-only'});spatialB.nodes.push({...structuredClone(spatialB.nodes[0]),runtime_node_id:'incomplete',observed_position:{x:1,y:null,z:3}});
const ctx={scene_id:review.scene_id,mode:'edit'},spatialCompare=historicalRuntimeComparisonPositions(spatialA,spatialB,ctx);assert.equal(spatialCompare.nodes.length,4);assert.equal(spatialCompare.skipped,1);assert.equal(spatialCompare.pairs.length,1);assert.equal(spatialCompare.pairs[0].after.x-spatialCompare.pairs[0].before.x,64);assert.equal(spatialCompare.comparison.identity_confirmed,false);assert.deepEqual(spatialCompare.nodes.map(n=>n.sample_layer),['baseline','baseline','comparison','comparison']);
assert.equal(historicalRuntimeComparisonPositions(spatialA,spatialB,ctx,'baseline').nodes.length,2);assert.equal(historicalRuntimeComparisonPositions(spatialA,spatialB,ctx,'baseline').skipped,0);assert.equal(historicalRuntimeComparisonPositions(spatialA,spatialB,ctx,'comparison').skipped,1);assert.equal(historicalRuntimeComparisonPositions(spatialA,spatialB,ctx,'comparison').pairs.length,0);assert.equal(historicalRuntimeComparisonPositions(review,review,ctx).pairs.length,0);
spatialCompare.nodes[0].observed_position.x=500;assert.equal(spatialA.nodes[0].observed_position.x,1);for(const context of [{...ctx,mode:'live'},{...ctx,scene_id:'scene://foreign'}])assert.throws(()=>historicalRuntimeComparisonPositions(spatialA,spatialB,context));assert.throws(()=>historicalRuntimeComparisonPositions(spatialA,spatialB,ctx,'future'));assert.throws(()=>historicalRuntimeComparisonPositions(spatialA,{...spatialB,profile_id:'foreign'},ctx));
const bound=structuredClone(review);bound.nodes=Array.from({length:128},(_,i)=>({...structuredClone(review.nodes[0]),runtime_node_id:'key-'+i}));assert.equal(historicalRuntimeComparisonPositions(bound,bound,ctx).nodes.length,256);
console.log('Historical spatial comparison: validated source files, detached colored layers, complete-key segments, file-only/missing samples, context and 256-sample bounds passed.');

assert.deepEqual(historicalSampleHits([{id:'paired-key',x:10,y:20},{id:'paired-key',x:10,y:20},{id:'other',x:11,y:21},{id:'far',x:80,y:90}],{x:10,y:20}),['paired-key','other']);assert.deepEqual(historicalSampleHits([],{x:0,y:0}),[]);for(const samples of [Array(257).fill({id:'key',x:1,y:1}),[{id:'key',x:NaN,y:0}],[null]])assert.throws(()=>historicalSampleHits(samples,{x:0,y:0}));assert.throws(()=>historicalSampleHits([],{x:Infinity,y:0}));console.log('Historical sample picking: bounded screen-space hits, paired-key deduplication, ambiguity and invalid geometry guards passed.');
