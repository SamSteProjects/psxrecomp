import assert from 'node:assert/strict';
import {decodeMeshSettings,qualifyMeshSettings} from '../editor/model-mesh-settings.js';
const recipe={kind:'single',material_colors:false,scene_index:null,uv_set:0,source_scale:1,source_offset:[0,0,0],source_rotation:[0,0,0],donor_face_id:'native-face',new_group:true,replace_group:false,replace_object:false,preserve_primitives:false,primitive_index:null};
const source={topology:{faces:[{face_id:'native-face',object_index:0,current_primitive_index:0},{face_id:'quad',object_index:0,current_primitive_index:1}]},objects:[{primitives:[{corner_count:3},{corner_count:4}]}]};
const inventory={source_scale:1,source_offset:[0,0,0],source_rotation:[0,0,0],scene_source:{scene_index:0},uv_sets:[[0,1],[0]],primitives:[{primitive_index:0},{primitive_index:1}]};
const original=structuredClone(recipe),decoded=decodeMeshSettings(recipe);decoded.source_offset[0]=99;assert.deepEqual(recipe,original);
assert.deepEqual(qualifyMeshSettings(recipe,source,inventory).missingDonors,[]);
for(const change of [r=>r.extra=true,r=>delete r.kind,r=>r.source_scale=NaN,r=>r.source_scale=0,r=>r.source_rotation[0]=361,r=>r.source_offset[0]=32768,r=>r.scene_index=64,r=>r.uv_set=8,r=>{r.new_group=false;r.preserve_primitives=true;},r=>{r.replace_group=true;r.replace_object=true;},r=>r.primitive_index=-1]){const r=structuredClone(recipe);change(r);assert.throws(()=>decodeMeshSettings(r));}
for(const change of [r=>r.scene_index=1,r=>r.uv_set=2,r=>r.primitive_index=2,r=>r.source_scale=2,r=>r.source_offset[0]=1,r=>r.source_rotation[0]=1]){const r=structuredClone(recipe);change(r);assert.throws(()=>qualifyMeshSettings(r,source,inventory));}
for(const donor of ['missing','quad'])assert.deepEqual(qualifyMeshSettings({...recipe,donor_face_id:donor},source,inventory).missingDonors,[donor]);
const {donor_face_id,new_group,replace_group,replace_object,preserve_primitives,primitive_index,...common}=recipe;
const batch={...common,kind:'batch',replace_objects:false,mappings:[{primitive_index:0,donor_face_id:'native-face',replace_group:false,uv_set:1},{primitive_index:1,donor_face_id:'missing',replace_group:true}]};
assert.deepEqual(qualifyMeshSettings(batch,source,inventory).missingDonors,['missing']);
for(const change of [r=>r.mappings=[],r=>r.mappings.reverse(),r=>r.mappings[1].primitive_index=0,r=>r.mappings[0].extra=true,r=>r.mappings[0].uv_set=8,r=>r.replace_objects=true,r=>r.mappings[1].primitive_index=2]){const r=structuredClone(batch);change(r);assert.throws(()=>qualifyMeshSettings(r,source,inventory));}
assert.deepEqual(recipe,original);console.log('Mesh settings validation and Current draft qualification passed.');
