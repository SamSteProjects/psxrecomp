import assert from 'node:assert/strict';
import {worldmapSceneView} from '../editor/worldmap-scene.js';

const ground='asset://map01/worldmap/walk-ground',model='asset://map01/worldmap/models/0001';
const identity=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
const geometry=()=>({vertices:[[0,0,0],[1,0,0],[0,1,0]],triangles:[[0,1,2]],triangle_materials:[0],
  triangle_uvs:[null],triangle_colors:[[[128,128,128],[128,128,128],[128,128,128]]],
  materials:[{textured:false}],textures:[{status:'unsupported',material_index:0}]});
const report=()=>({scene:'map01',semantic_id:ground,scene_graph:{schema_version:'legaia.worldmap-scene-graph.v1',
  coordinate_system:'retail_field_y_down',matrix_convention:'column-major-affine',
  metrics:{asset_count:2,entity_count:2,stored_triangle_count:2,drawn_triangle_count:2,texture_output_bytes:0},
  coverage:{candidate_count:1,resolved_count:1,rendered_count:1,unresolved_count:0,excluded_count:0,inspected_cell_count:16384,unresolved:[],excluded:[]},
  assets:[{asset_id:ground,source_record:{map_sha256:'a'.repeat(64)},preview:geometry()},
          {asset_id:model,source_record:{decoded_member_sha256:'b'.repeat(64)},preview:geometry()}],
  entities:[{entity_id:'scene://map01/worldmap/ground',asset_id:ground,source_position:{x:0,y:0,z:0},
    source_to_world:identity.slice(),placement_scope:'source_ground',runtime_visibility:'not_evaluated',runtime_resting_position:'unknown'},
    {entity_id:'scene://map01/worldmap/placements/0081',asset_id:model,source_position:{x:128,y:-64,z:256},
      source_to_world:[1,0,0,0,0,1,0,0,0,0,1,0,128,-64,256,1],source_record_sha256:'c'.repeat(64),
      placement_scope:'source_spawn_seed',runtime_visibility:'not_evaluated',runtime_resting_position:'unknown'}]}});

const original=report(),before=JSON.stringify(original),view=worldmapSceneView(original);
assert.equal(view.assets.length,2);assert.equal(view.entities.length,2);
assert.equal(view.entities[1].geometry_key,model);
assert.deepEqual(view.entities[1].model_to_scene.map(value=>value||0),[1,0,0,128,0,-1,0,64,0,0,1,256,0,0,0,1],
  'Column-major source seed becomes row-major renderer matrix with one display Y flip.');
assert.equal(JSON.stringify(original),before,'Scene inspection preserves source transforms and geometry.');
for(const mutate of [
  r=>r.scene_graph.assets.push(r.scene_graph.assets[0]),r=>r.scene_graph.entities.push(r.scene_graph.entities[1]),
  r=>r.scene_graph.assets[1].asset_id='asset://map02/worldmap/models/0001',
  r=>r.scene_graph.entities[1].entity_id='scene://map02/worldmap/placements/0081',
  r=>r.scene_graph.entities[1].asset_id='asset://map01/worldmap/models/9999',
  r=>r.scene_graph.entities[1].source_to_world[12]++,r=>r.scene_graph.entities[1].source_to_world[0]=Infinity,
  r=>r.scene_graph.entities[1].source_to_world[15]=0,r=>r.scene_graph.entities[1].source_record_sha256='stale',
  r=>r.scene_graph.entities[1].runtime_visibility='verified',r=>r.scene_graph.entities[1].runtime_resting_position='known',
  r=>r.scene_graph.assets[1].preview.triangles[0][1]=3,r=>r.scene_graph.assets[1].preview.vertices[0][0]=NaN,
  r=>r.scene_graph.assets[1].preview.triangle_uvs=[[[0,0],[1,0],[0,NaN]]],
  r=>r.scene_graph.assets[1].preview.triangle_colors[0][0][0]=256,
  r=>r.scene_graph.assets[1].preview.textures[0].material_index=1,
  r=>r.scene_graph.assets[1].preview.textures[0].status='invented_texture',
  r=>r.scene_graph.assets[1].source_record.decoded_member_sha256='stale',
  r=>r.scene_graph.schema_version='foreign',r=>r.scene_graph.coordinate_system='display_y_up',
  r=>r.scene_graph.metrics.entity_count=3,r=>r.scene_graph.metrics.drawn_triangle_count=200001,
  r=>r.scene_graph.coverage.resolved_count=2,r=>r.scene_graph.coverage.unresolved_count=1,
  r=>r.scene_graph.entities=Array(513).fill(r.scene_graph.entities[1]),
  r=>r.scene_graph.assets=Array(129).fill(r.scene_graph.assets[0]),
]){const candidate=report();mutate(candidate);assert.throws(()=>worldmapSceneView(candidate));}
console.log('Kingdom source ownership, ground entity, alias/index/budget guards and single display Y conversion passed.');
