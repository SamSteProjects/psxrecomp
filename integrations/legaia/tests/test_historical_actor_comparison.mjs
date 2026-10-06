import assert from 'node:assert/strict';
import {historicalActorComparison} from '../editor/historical-actor-comparison.js';

const id='scene://town01/actors/man-p1/0005';
const review={schema_version:'legaia.runtime-node-review.v1',historical:true,read_only:true,exported_at:'2026-10-06T10:00:00Z',scene_id:'scene://town01',epoch_id:'file-epoch',profile_id:null,nodes:[{runtime_node_id:'sample',epoch_id:'file-epoch',observed_position:{x:192,y:16,z:320},position_capture_frames:{before:10,after:11},candidate_entity_ids:[id],decoded_fields:[],binding_confirmed:false,reason:null}]};
const context={scene_id:review.scene_id,mode:'edit',representation:'authored',source_key:'a'.repeat(64),node_id:'sample',overlay:{review},actor:{id,components:{Transform:{imported:{position:{x:64,y:null,z:256}},effective:{position:{x:128,y:null,z:256}},authored:{position:{x:128}}}}},preview:{entity_id:id,position:{x:128,y:null,z:256},preview_position:{x:128,y:8,z:256},preview_height_status:'source_surface'}};
const before=structuredClone(context),report=historicalActorComparison(context);
assert.deepEqual(context,before);assert(report.historical&&report.read_only&&!report.identity_confirmed);
assert.deepEqual(report.samples[0].delta_from_imported,{x:128,y:null,z:64});
assert.deepEqual(report.samples[0].delta_from_effective,{x:64,y:null,z:64});
assert.deepEqual(report.samples[0].delta_from_viewport_surface,{x:64,y:8,z:64});
assert.deepEqual(report.actor.authored_position,{x:128});assert.equal(report.actor.imported_position.y,null);assert.equal(report.samples[0].listed_actor_candidate,true);
report.samples[0].candidate_entity_ids.length=0;assert.equal(review.nodes[0].candidate_entity_ids.length,1);
const retail=structuredClone(context);retail.representation='retail';retail.preview.position.x=retail.preview.preview_position.x=64;assert.equal(historicalActorComparison(retail).actor.viewport_native_position.x,64);
const later=structuredClone(review);later.nodes[0].observed_position.x=256;
const paired={...context,overlay:{review,comparison:{before:review,after:later},layer:'both'}};
assert.deepEqual(historicalActorComparison(paired).samples.map(s=>[s.layer,s.observed_position.x]),[['baseline',192],['comparison',256]]);
paired.overlay.layer='comparison';assert.equal(historicalActorComparison(paired).samples.length,1);
paired.overlay.comparison.after.nodes=[];assert.throws(()=>historicalActorComparison(paired),/no complete/);
for(const alter of [c=>c.mode='live',c=>c.source_key='',c=>c.representation='proposed',c=>c.actor.id='scene://other/actors/man-p1/0005',c=>c.actor.id='npc://town01/example',c=>c.node_id='missing',c=>c.preview.entity_id='foreign',c=>c.preview.position.x=64,c=>c.preview.preview_height_status='assumed',c=>c.overlay.review.scene_id='scene://other',c=>c.overlay.review.nodes[0].observed_position.y=null,c=>c.overlay.review.nodes[0].binding_confirmed=true,c=>c.actor.components.Transform.effective.position.x=Infinity]){
 const bad=structuredClone(context);alter(bad);assert.throws(()=>historicalActorComparison(bad));
}
console.log('Historical actor comparison: exact retail/current/surface deltas, unknown native height, authored inheritance, both file layers, detached candidate metadata and scene/source/viewport/authority rejection passed.');
