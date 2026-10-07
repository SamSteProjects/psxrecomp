import fs from 'node:fs';
import assert from 'node:assert/strict';
import {decodeMeshBatchReview} from '../editor/model-mesh-batch.js';
import {decodeMeshSettings,qualifyMeshSettings} from '../editor/model-mesh-settings.js';
if(!process.argv[2])throw Error('Provide a fresh qualified batch animation pose fixture.');
const f=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const check=value=>decodeMeshBatchReview(value,f.source,f.glb_sha256,f.mappings,false,null,0,1,true,[0,0,0],[0,0,0],f.pose);
check(f.review);let refusals=0;
for(const mutate of [v=>v.animation_pose.time_seconds=.25,v=>v.inventory.static_scope.sampled_animation.time_seconds=.25,v=>v.steps[1].review.animation_pose.time_seconds=.25,v=>v.steps[0].review.geometry.static_scope.sampled_animation.time_seconds=.25,v=>delete v.steps[0].review.animation_pose,v=>v.steps[1].review.geometry.static_scope.sampled_animation.sampled_channels[0].key_count=0,v=>v.mappings[0].donor_face_id=f.mappings[1].donor_face_id]){const v=structuredClone(f.review);mutate(v);assert.throws(()=>check(v));refusals++;}
assert.throws(()=>decodeMeshBatchReview(f.review,f.source,f.glb_sha256,f.mappings,false,null,0,1,true));refusals++;
const recipe={kind:'batch',mappings:f.mappings,replace_objects:true,material_colors:false,scene_index:null,uv_set:0,source_scale:1,source_offset:[0,0,0],source_rotation:[0,0,0],animation_pose:f.pose};
decodeMeshSettings(recipe);assert.deepEqual(qualifyMeshSettings(recipe,f.source,f.inventory).missingDonors,[]);
assert.throws(()=>qualifyMeshSettings({...recipe,animation_pose:{...f.pose,time_seconds:.25}},f.source,f.inventory));refusals++;
assert.throws(()=>decodeMeshSettings({...recipe,animation_pose:null}));refusals++;
console.log(JSON.stringify({batch_pose_chain_settings:true,forged_refusals:refusals}));
