import fs from 'node:fs';
import assert from 'node:assert/strict';
import {decodePlayerArts} from '../editor/player-art-animation.js';
import {qualifyPlayerArtGlbReview,qualifyPlayerArtGlbPose} from '../editor/player-art-glb.js';
import {placementDigest} from '../editor/worldmap-placement-replay.js';
const cases=JSON.parse(fs.readFileSync(process.argv[2],'utf8')).cases;assert.equal(cases.length,2);let refusals=0;
for(const c of cases){
  const i=c.inspection,ar=await decodePlayerArts(c.art_report,{projectPath:i.project_path,sourceKey:i.project_source_key},c.model_report),record={id:c.model.semantic_id,data:c.model},input=new Uint8Array(Buffer.from(c.input_base64,'base64')),args=[i,ar,c.model_report,record,c.selection,input,c.options];
  await qualifyPlayerArtGlbReview(c.review,...args);await qualifyPlayerArtGlbPose(c.pose,c.review,...args);
  for(const mutate of [v=>v.glb_import.glb_sha256='0'.repeat(64),v=>v.glb_import.fps++,v=>v.glb_import.edits[0].translation[0]++,v=>v.glb_import.attachment_alias_checks++,v=>v.glb_import.maximum_translation_error=1,v=>v.glb_import.maximum_angular_error_degrees=1,v=>v.glb_import.allocation=true,v=>v.retained_input.baseline_slot_sha256='0'.repeat(64),v=>v.retained_input.baseline_owners={},v=>v.retained_input.object_part_indices[0]=999,v=>v.retained_input.animation_index=0,v=>v.projection.native_body_policy='current_body',v=>v.projection.canonicalized_body_bytes++,v=>v.projection.changed_current_part_frames++,v=>v.projection.retail_relative_part_frames++,v=>v.candidate_body_sha256='0'.repeat(64),v=>v.capacity.growth=true,v=>v.geometry_layer='foreign',v=>v.inspection.current_slot_sha256='stale']){
    const bad=structuredClone(c.review);mutate(bad);if(JSON.stringify(bad)===JSON.stringify(c.review))continue;
    await assert.rejects(()=>qualifyPlayerArtGlbReview(bad,...args));refusals++;
  }
  if(c.review.ownership_after){const bad=structuredClone(c.review);delete bad.ownership_after.glb_import;await assert.rejects(()=>qualifyPlayerArtGlbReview(bad,...args));refusals++;}
  else{const bad=structuredClone(c.review);bad.ownership_after={};await assert.rejects(()=>qualifyPlayerArtGlbReview(bad,...args));refusals++;assert(c.review.projection.canonicalized_body_bytes>0);}
  const bad=structuredClone(c.review),raw=Buffer.from(bad.candidate_slot_base64,'base64');raw[raw.length-1]^=1;bad.candidate_slot_base64=raw.toString('base64');bad.candidate_slot_sha256=await placementDigest(raw);
  await assert.rejects(()=>qualifyPlayerArtGlbReview(bad,...args));refusals++;
  const changed=input.slice();changed[changed.length-1]^=1;await assert.rejects(()=>qualifyPlayerArtGlbReview(c.review,...args.slice(0,-2),changed,c.options));refusals++;
  for(const mutate of [v=>v.proposed_pose.geometry.vertices[0][0]++,v=>v.current_pose.object_transforms[0].translation[0]++,v=>v.proposed_pose.geometry.bounds.max[0]++,v=>v.proposed_pose.geometry.textures=[],v=>v.review_key='stale']){
    const badPose=structuredClone(c.pose);mutate(badPose);await assert.rejects(()=>qualifyPlayerArtGlbPose(badPose,c.review,...args));refusals++;
  }
}
console.log(`Two GLB import/restoration Review/Proposed cases passed independent channel, canonical full-slot and full-pose replay; ${refusals} input/source/ledger/body/geometry refusals passed`);
