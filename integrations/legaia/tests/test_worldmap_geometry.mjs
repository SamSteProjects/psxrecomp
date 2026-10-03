import assert from 'node:assert/strict';
import {decodeWorldmapGeometry} from '../editor/worldmap-geometry.js';

const key='a'.repeat(64),scene='map01';
const report=()=>({schema_version:'legaia.worldmap-geometry.v1',semantic_id:'asset://map01/worldmap/walk-ground',scene,
  project_source_key:key,project_changed:false,gameplay_verified:false,representation:'retail-source',authored_geometry:false,
  source_record:{map_sha256:'c'.repeat(64),bundle_sha256:'d'.repeat(64),floor_lut_sha256:'e'.repeat(64),disc_sha256:'b'.repeat(64),map_entry_index:83,man_slot:{slot_index:2},texture_slot:{slot_index:0}},
  metrics:{cell_count:1,vertex_count:4,triangle_count:2,material_count:1,matched_texture_count:0,unsupported_texture_count:1,texture_output_bytes:0},limitations:['Source walk ground; gameplay unverified.'],
  preview:{coordinate_system:'retail_field_y_down',vertices:[[0,-37,0],[128,-74,0],[0,-111,128],[128,-148,128]],
    triangles:[[0,1,2],[1,3,2]],triangle_uvs:[[[0,31],[31,31],[0,0]],[[31,31],[31,0],[0,0]]],
    triangle_colors:[[[128,128,128],[128,128,128],[128,128,128]],[[128,128,128],[128,128,128],[128,128,128]]],
    triangle_materials:[0,0],materials:[{textured:true,tpage:1,clut:512}],textures:[{status:'missing',material_index:0,reason:'No matching source atlas'}]}});

const accepted=report();
assert.equal(decodeWorldmapGeometry(accepted,scene,key),accepted);
assert.deepEqual(accepted.preview.vertices[0],[0,-37,0],'The decoder retains source Y-down axes; the renderer owns the flip.');
for(const mutate of [
  v=>v.source_record.map_sha256='invalid',v=>v.metrics.vertex_count=5,v=>v.metrics.matched_texture_count=1,
  v=>v.preview.textures[0].material_index=1,v=>v.preview.textures[0].rgba_base64='AAAA',
  v=>v.schema_version='foreign',v=>v.scene='map02',v=>v.semantic_id='asset://map02/worldmap/walk-ground',
  v=>v.project_source_key='c'.repeat(64),v=>v.project_changed=true,v=>v.gameplay_verified=true,
  v=>v.representation='authored',v=>v.authored_geometry=true,v=>v.limitations=[4096],
  v=>v.preview.coordinate_system='display_y_up',v=>v.preview.vertices=[],
  v=>v.preview.vertices[0][1]=Infinity,v=>v.preview.vertices[0][0]=1000001,
  v=>v.preview.vertices[0].push(1),v=>v.preview.triangles[0][0]=4,
  v=>v.preview.triangles[0][0]=.5,v=>v.preview.triangle_materials[0]=1,
  v=>v.preview.triangle_colors[0][0][0]=256,v=>v.preview.triangle_colors[0][0][0]=NaN,
  v=>v.preview.triangle_uvs[0][0][0]=-1,v=>v.preview.triangle_uvs.pop(),
  v=>v.preview.triangle_colors.pop(),v=>v.preview.materials=Array(65).fill({}),
  v=>v.preview.textures=Array(65).fill({}),
]) {const value=report();mutate(value);assert.throws(()=>decodeWorldmapGeometry(value,scene,key));}
for(const badScene of ['town01','map04','../map01',null])assert.throws(()=>decodeWorldmapGeometry(report(),badScene,key));
assert.throws(()=>decodeWorldmapGeometry(report(),scene,'stale'));
const untextured=report();untextured.preview.triangle_uvs=[null,null];untextured.preview.materials[0].textured=false;
assert.equal(decodeWorldmapGeometry(untextured,scene,key).preview.triangle_uvs[0],null,'Missing selectors remain explicit, without fallback UVs.');
const before=JSON.stringify(report()),value=report();decodeWorldmapGeometry(value,scene,key);
assert.equal(JSON.stringify(value),before,'Read-only geometry qualification does not mutate source axes or metadata.');
console.log('World-ground source identity, finite geometry, index/material/color/UV bounds and source-only claims passed.');
