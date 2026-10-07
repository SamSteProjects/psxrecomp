import fs from 'node:fs';
import assert from 'node:assert/strict';
import {decodeMeshFile,decodeMeshAppendReview} from '../editor/model-mesh-append.js';
import {decodeMeshSettings,qualifyMeshSettings} from '../editor/model-mesh-settings.js';
if(!process.argv[2])throw Error('Provide a freshly qualified animation-pose mesh fixture.');
const f=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const inventory=decodeMeshFile(f.inventory,f.glb_sha256,1,[0,0,0],[0,0,0],f.pose);
const check=r=>decodeMeshAppendReview(r,f.source,f.donor,f.glb_sha256,false,false,false,null,false,null,0,1,false,[0,0,0],[0,0,0],f.pose);
check(f.review);let refusals=0;
for(const mutate of [v=>v.animation_pose.time_seconds=.25,v=>v.geometry.static_scope.sampled_animation.time_seconds=.25,v=>v.geometry.static_scope.sampled_animation.sampled_channels[0].node_index=0,v=>v.geometry.static_scope.sampled_animation.sampled_channels[0].key_count=0,v=>v.geometry.static_scope.sampled_animation.sampled_channels[0].interpolation='BAD',v=>v.geometry.static_scope.sampled_animation.excluded_channels.push({node_index:1,path:'translation'}),v=>v.geometry.static_scope.sampled_animation.extra=true]){const v=structuredClone(f.review);mutate(v);assert.throws(()=>check(v));refusals++;}
assert.throws(()=>decodeMeshFile(inventory,f.glb_sha256));refusals++;
const recipe={kind:'single',donor_face_id:f.donor,new_group:false,replace_group:false,replace_object:false,preserve_primitives:false,primitive_index:null,material_colors:false,scene_index:null,uv_set:0,source_scale:1,source_offset:[0,0,0],source_rotation:[0,0,0],animation_pose:f.pose};
decodeMeshSettings(recipe);assert.equal(qualifyMeshSettings(recipe,f.source,inventory).missingDonors.length,0);assert.throws(()=>qualifyMeshSettings({...recipe,animation_pose:{...f.pose,time_seconds:.25}},f.source,inventory));refusals++;
assert.throws(()=>decodeMeshSettings({...recipe,animation_pose:null}));refusals++;
console.log(JSON.stringify({pose_inventory_review_settings:true,forged_refusals:refusals}));
