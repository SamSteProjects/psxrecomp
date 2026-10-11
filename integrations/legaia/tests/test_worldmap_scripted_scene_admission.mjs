import {readFileSync,writeFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {qualifyScriptedWorldScene} from '../editor/worldmap-scripted-placement-scene.js';
const cases=JSON.parse(readFileSync(process.argv[2],'utf8')),held=JSON.stringify(cases);let refusals=0;
for(const row of cases){
 const {retail,current,options}=row,view=await qualifyScriptedWorldScene(retail,current,options);
 assert.equal(view.entities.length,current.scene_graph.entities.length);
 assert.equal(view.assets.length,current.scene_graph.assets.length);
 const scripted=view.entities.filter(e=>e.placement_scope==='authored_scripted_seed');
 assert.equal(scripted.length,current.placement_source.authored_scripted_placements.length);assert.ok(scripted.length);
 for(const e of view.entities){
  assert.equal(e.geometry_key,e.asset_id);
  for(let r=0;r<4;r++)for(let c=0;c<4;c++)assert.equal(e.model_to_scene[r*4+c],e.source_to_world[c*4+r]*(r===1?-1:1));
 }
 const modifications=[
  c=>c.scene='map00',c=>c.project_source_key='0'.repeat(64),c=>c.ground_layer='current',c=>c.gameplay_verified=true,c=>c.extra=true,
  c=>c.authored_entity_count++,c=>c.changed_source_entity_count++,c=>c.authored_geometry=false,
  c=>c.scene_graph.entities.reverse(),c=>c.scene_graph.entities.pop(),
  c=>c.scene_graph.entities.find(e=>e.retail_seed).retail_seed.source_position.x++,
  c=>c.scene_graph.entities.find(e=>e.authored_placement_kind==='scripted').placement_scope='authored_spawn_seed',
  c=>c.scene_graph.entities.find(e=>e.authored_placement_kind==='scripted').native_entity_id='scene://map00/worldmap/placements/0000',
  c=>c.scene_graph.entities.find(e=>e.authored_placement_kind==='scripted').source_to_world[12]++,
  c=>c.scene_graph.entities.find(e=>e.authored_placement_kind==='scripted').authored_placement.native_seed.source_position.y++,
  c=>c.scene_graph.metrics.drawn_triangle_count++,c=>c.scene_graph.coverage.unresolved_count++,c=>c.scene_graph.limitations.pop(),
  c=>c.scene_graph.assets[0].preview.vertices[0][0]++,
  c=>c.placement_source.current_map_sha256='0'.repeat(64),c=>c.placement_source.floor_lut[0]++,
  c=>c.placement_source.authored_scripted_placements.pop(),c=>c.placement_source.binding.operations[0].proposed_map_sha256='0'.repeat(64)
 ];
 for(const change of modifications){const altered=structuredClone(current);change(altered);await assert.rejects(()=>qualifyScriptedWorldScene(retail,altered,options));refusals++;}
 const altered=structuredClone(options);altered.overrides[`worldmap://${retail.scene}/scripted-placement-allocations`].WorldMapScriptedPlacementAllocations.operations[0].proposed_map_sha256='0'.repeat(64);
 await assert.rejects(()=>qualifyScriptedWorldScene(retail,current,altered));refusals++;
 const forgedRetail=structuredClone(retail),forgedCurrent=structuredClone(current),original=forgedRetail.scene_graph.entities.find(e=>e.placement_scope!=='source_ground');original.source_position.x++;
 forgedCurrent.scene_graph.entities.find(e=>e.entity_id===original.entity_id).retail_seed=structuredClone(original);
 await assert.rejects(()=>qualifyScriptedWorldScene(forgedRetail,forgedCurrent,options));refusals++;
 const unknown=structuredClone(options);unknown.overrides[`worldmap://${retail.scene}/scripted-placement-allocations`].Unsupported={};
 await assert.rejects(()=>qualifyScriptedWorldScene(retail,current,unknown));refusals++;
 console.log(row.name,'complete scene, authored identity and render transforms match');
}
assert.equal(JSON.stringify(cases),held);
const proof={cases:cases.length,refusals,complete_scene_admitted:true,inputs_unchanged:true,browser_rendered:false,gameplay_verified:false};
if(process.argv[3])writeFileSync(process.argv[3],JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify(proof));
