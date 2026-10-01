import assert from 'node:assert/strict';
import {decodeActorPlacementScene} from '../editor/actor-placement-batch.js';
const proposal={scene_id:'scene://fixture',review_key:'review',targets:[
  {entity_id:'a',proposed:{x:128,y:null,z:256}},
  {entity_id:'b',proposed:{x:512,y:12,z:1024}}]};
const response={schema_version:'legaia.actor-placement-scene.v1',scene_id:proposal.scene_id,review_key:'review',project_source_key:'source',positions:[
  {entity_id:'a',position:{x:128,y:null,z:256},preview_position:{x:128,y:10,z:256},display_position:{x:128,y:-10,z:256},preview_height_status:'source_surface'},
  {entity_id:'b',position:{x:512,y:12,z:1024},preview_position:{x:512,y:12,z:1024},display_position:{x:512,y:-12,z:1024},preview_height_status:'explicit'}]};
const before=structuredClone(response),positions=decodeActorPlacementScene(response,proposal,'source');
assert.equal(positions.size,2);assert.equal(positions.get('a').y,-10);positions.get('a').x=0;assert.deepEqual(response,before);
for(const edit of [r=>r.review_key='old',r=>r.project_source_key='old',r=>r.positions.push(r.positions[0]),r=>r.positions[1].entity_id='a',r=>r.positions[0].position.x=192,r=>r.positions[0].display_position.x=192,r=>r.positions[0].display_position.y=10,r=>r.positions[0].preview_height_status='explicit',r=>r.positions[1].preview_position.y=13,r=>r.positions[1].display_position.z=NaN]){
  const bad=structuredClone(response);edit(bad);assert.throws(()=>decodeActorPlacementScene(bad,proposal,'source'));
}
const unknown=structuredClone(response);unknown.positions[0].preview_position.y=null;unknown.positions[0].display_position.y=0;unknown.positions[0].preview_height_status='unresolved_no_source_surface';assert.equal(decodeActorPlacementScene(unknown,proposal,'source').get('a').y,0);
console.log('Actor group scene identity, exact proposal coordinates, elevation conventions, bounds and detached maps passed.');
