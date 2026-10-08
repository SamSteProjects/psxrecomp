import assert from 'node:assert/strict';
import {npcGroundPlacement} from '../editor/npc-ground-placement.js';
const scene='scene://fixture',ground='environment://fixture/field-map/ground',vertex=[128,-900,256],hit={entity_id:ground,geometry_key:'ground-key',asset_id:ground,vertex_index:0,decoded_model_position:vertex};
const doc={scene_id:scene,entities:[{entity_id:ground,asset_id:ground,geometry_key:'ground-key',renderable:true,pose_kind:'source_heightfield'}],assets:[{asset_id:ground,geometry_key:'ground-key',preview:{vertices:[vertex]}}]};
const result=npcGroundPlacement(doc,hit,scene);assert.deepEqual(result.position,{x:128,z:256});assert.equal(result.height,'not_authored');result.position.x=999;assert.equal(vertex[0],128);
for(const mutate of [d=>d.scene_id='other',d=>d.entities[0].pose_kind='actor',d=>d.entities[0].renderable=false,d=>d.entities[0].asset_id='other',d=>d.assets[0].preview.vertices[0][0]=0,d=>d.assets[0].preview.vertices[0][2]=65,d=>d.assets[0].preview.vertices[0][0]=16448]){const changed=structuredClone(doc);mutate(changed);assert.throws(()=>npcGroundPlacement(changed,hit,scene));}
assert.throws(()=>npcGroundPlacement(doc,{...hit,decoded_model_position:[999,-900,256]},scene));assert.throws(()=>npcGroundPlacement(doc,{...hit,vertex_index:-1},scene));assert.throws(()=>npcGroundPlacement(doc,null,scene));
console.log('Ground placement binds exact current source geometry/corner and native X/Z grid, keeps height un-authored and rejects models/stale/unsupported points.');

for(const x of [0,65,16448]){const changed=structuredClone(doc);changed.assets[0].preview.vertices[0][0]=x;assert.throws(()=>npcGroundPlacement(changed,{...hit,decoded_model_position:[x,-900,256]},scene),/native NPC X\/Z grid/);}
