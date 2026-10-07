import assert from 'node:assert/strict';
import {textureSceneUsage,textureMatchedPlacementIds} from '../editor/texture-usage.js';
const id='texture://fixture/image',palette='texture://fixture/palette';
const source={scene_id:'scene://fixture',source_key:'hash',representation:'authored',assets:[
 {asset_id:'model://shared',geometry_key:'g1',preview:{materials:[{textured:true},{textured:false}],textures:[{material_index:0,status:'address_match',source_ids:[id,palette]},{material_index:1,status:'unsupported',reason:'material is untextured'}]}},
 {asset_id:'model://partial',geometry_key:'g2',preview:{materials:[{textured:true}],textures:[{material_index:0,status:'ambiguous',source_ids:[id],reason:'overlap'}]}}
],entities:[{entity_id:'actor-a',geometry_key:'g1',asset_id:'model://shared',renderable:true},{entity_id:'draft-a',kind:'actor_draft',geometry_key:'g1',asset_id:'model://shared',renderable:true},{entity_id:'prop-a',kind:'environment',geometry_key:'g2',renderable:true},{entity_id:'marker',renderable:false}]};
const before=structuredClone(source),result=textureSceneUsage(source,id);
assert.equal(result.matches.length,1);assert.equal(result.matching_instance_count,2);assert.equal(result.candidates.length,1);assert.equal(result.textured_material_count,2);assert.equal(result.unresolved_material_count,1);assert.equal(result.unavailable_instance_count,1);
assert.equal(textureSceneUsage(source,palette).matching_instance_count,2);
assert.equal(textureSceneUsage(source,'texture://unknown').matches.length,0);
result.matches[0].instances[0].id='changed';result.matches[0].materials[0].source_ids.length=0;assert.deepEqual(source,before);
assert.throws(()=>textureSceneUsage({...source,assets:Array(129).fill({})},id));
console.log('Texture usage: shared/draft instances, CLUT contributor, unresolved candidate, untextured exclusion, detached data and bounds passed.');

const eligible=new Set(['actor-a','draft-a','prop-a']);
assert.deepEqual(textureMatchedPlacementIds(source,id,eligible),['actor-a','draft-a']);
assert.deepEqual(textureMatchedPlacementIds(source,palette,eligible),['actor-a','draft-a']);
assert.deepEqual(textureMatchedPlacementIds(source,'texture://unknown',eligible),[]);
const duplicates=structuredClone(source);duplicates.entities.push({...duplicates.entities[0]});assert.throws(()=>textureMatchedPlacementIds(duplicates,id,eligible));
const geometryDuplicate=structuredClone(source);geometryDuplicate.assets.push({...geometryDuplicate.assets[0]});assert.throws(()=>textureMatchedPlacementIds(geometryDuplicate,id,eligible));
assert.throws(()=>textureMatchedPlacementIds(source,id,[]));
const shared=structuredClone(source);shared.entities.push({entity_id:'ground',geometry_key:'g1',asset_id:'model://shared',renderable:true});assert.deepEqual(textureMatchedPlacementIds(shared,id,eligible),['actor-a','draft-a']);
const many=structuredClone(source);many.entities=Array.from({length:129},(_,i)=>({entity_id:'actor-'+i,geometry_key:'g1',asset_id:'model://shared',renderable:true}));
assert.throws(()=>textureMatchedPlacementIds(many,id,new Set(many.entities.map(row=>row.entity_id))),/at most 128/);assert.deepEqual(source,before);
console.log('Texture placement matches: canonical actor/NPC IDs, image/CLUT ownership, partial/unavailable/ground exclusion, conflicting scene/geometry and atomic overflow refusal passed.');

for(const textureId of ['',null,17,'x'.repeat(1025)])assert.throws(()=>textureMatchedPlacementIds(source,textureId,eligible));
const wrongBinding=structuredClone(source);wrongBinding.entities[0].asset_id='model://foreign';assert.throws(()=>textureMatchedPlacementIds(wrongBinding,id,eligible));

const scenery=structuredClone(source);scenery.entities[2]={entity_id:'prop-a',kind:'environment',asset_id:'model://shared',geometry_key:'g1',renderable:true};
assert.deepEqual(textureMatchedPlacementIds(scenery,id,eligible),['actor-a','draft-a','prop-a']);
const unavailable=new Set([...eligible,'marker']);assert.deepEqual(textureMatchedPlacementIds(source,id,unavailable),['actor-a','draft-a']);
assert.deepEqual(textureMatchedPlacementIds({...many,entities:many.entities.slice(0,128)},id,new Set(many.entities.map(row=>row.entity_id))),many.entities.slice(0,128).map(row=>row.entity_id).sort());
