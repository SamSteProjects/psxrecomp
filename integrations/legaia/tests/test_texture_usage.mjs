import assert from 'node:assert/strict';
import {textureSceneUsage} from '../editor/texture-usage.js';
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
