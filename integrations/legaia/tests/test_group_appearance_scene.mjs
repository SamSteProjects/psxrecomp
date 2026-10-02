import assert from 'node:assert/strict';
import {decodeGroupAppearanceScene} from '../editor/group-appearance.js';
const row=id=>({entity_id:id,asset_id:'old',source_actor_id:id,appearance_authored:false,renderable:true,geometry_key:'old',position:{x:128,y:null,z:256},model_to_scene:[1,0,0,128]});
const current={schema:'legaia.scene-preview.v1',scene_id:'scene',source_key:'source',coordinate_system:'source',position_to_display:[1],entities:['a','b','c'].map(row),assets:[{geometry_key:'old',asset_id:'old',preview:{vertices:[[1,2,3]]}}]};
const report={scene_id:'scene',review_key:'review',donor_entity_id:'donor',targets:[{entity_id:'a'},{entity_id:'b'}],options:[{donor_entity_id:'donor',asset_id:'new'}]};
const scene=structuredClone(current);scene.representation='authored';scene.source_key='proposal';scene.assets.push({geometry_key:'new',asset_id:'new',preview:{vertices:[[4,5,6]]}});
for(const target of scene.entities.slice(0,2))Object.assign(target,{asset_id:'new',source_actor_id:'donor',appearance_authored:true,geometry_key:'new'});
const response={schema_version:'legaia.actor-appearance-scene.v1',scene_id:'scene',project_source_key:'source',review_key:'review',scene},before=structuredClone(response);
const decoded=decodeGroupAppearanceScene(response,report,current);decoded.entities[0].position.x=0;assert.deepEqual(response,before);
for(const edit of [r=>r.review_key='stale',r=>r.project_source_key='stale',r=>r.scene.entities[0].position.x=0,r=>r.scene.entities[1].source_actor_id='wrong',r=>r.scene.entities[1].asset_id='wrong',r=>r.scene.entities[2].source_actor_id='wrong',r=>r.scene.assets[0].preview.vertices[0][0]=0,r=>r.scene.entities.pop(),r=>r.scene.entities[1].entity_id='a',r=>r.scene.assets.pop()]){const bad=structuredClone(response);edit(bad);assert.throws(()=>decodeGroupAppearanceScene(bad,report,current));}
console.log('Group appearance source/review/donor binding, exact placements, unaffected geometry and detached projection passed.');

const attributed=structuredClone(response),attributedBase=structuredClone(current);
attributedBase.assets[0].preview.pose={actor_semantic_id:'c',association:{actor_source_record:{record_index:3},animation_id:13}};
attributed.scene.assets[0].preview.pose={actor_semantic_id:'a',association:{actor_source_record:{record_index:1},animation_id:13}};
assert.doesNotThrow(()=>decodeGroupAppearanceScene(attributed,report,attributedBase));
attributed.scene.assets[0].preview.pose.association.animation_id=57;assert.throws(()=>decodeGroupAppearanceScene(attributed,report,attributedBase));
console.log('Shared pose source actor attribution is tolerated; changed animation evidence is rejected.');

const retainedBase=structuredClone(current),retained=structuredClone(response);
Object.assign(retainedBase.entities[0],{animation_assignment_authored:true,source_actor_id:'clip-witness',source_record:{record_index:49},model_reference:{asset_semantic_id:'new'}});
Object.assign(retained.scene.entities[0],{animation_assignment_authored:true,source_actor_id:'clip-witness',source_record:{record_index:49},model_reference:{asset_semantic_id:'new'}});
assert.doesNotThrow(()=>decodeGroupAppearanceScene(retained,report,retainedBase));
for(const mutate of [r=>r.scene.entities[0].source_actor_id='other-witness',r=>r.scene.entities[0].source_record.record_index=50,r=>r.scene.entities[0].model_reference.asset_semantic_id='other-model',r=>r.scene.entities[0].animation_assignment_authored=false]){
  const bad=structuredClone(retained);mutate(bad);assert.throws(()=>decodeGroupAppearanceScene(bad,report,retainedBase));
}
assert.throws(()=>decodeGroupAppearanceScene(retained,report,current));
console.log('A retained verified initial-animation witness survives same-model appearance proposals; changed or fabricated witnesses reject.');
