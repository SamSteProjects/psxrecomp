import fs from 'node:fs';
import assert from 'node:assert/strict';
import {decodePlayerArts} from '../editor/player-art-animation.js';
import {qualifyPlayerArtInspection,qualifyPlayerArtReview,qualifyPlayerArtProposedPose} from '../editor/player-art-authoring.js';
import {placementDigest} from '../editor/worldmap-placement-replay.js';
const cases=JSON.parse(fs.readFileSync(process.argv[2],'utf8')).cases;assert.equal(cases.length,2);let refused=0;
for(const c of cases){
  const i=c.inspection,id=i.base_playback.stream.semantic_id,ar=await decodePlayerArts(c.art_report,{projectPath:i.project_path,sourceKey:i.project_source_key},c.model_report),record={id:c.model.semantic_id,data:c.model},args=[ar,c.model_report,record,c.selection],desired=c.review.projection.after;
  await qualifyPlayerArtInspection(i,...args,0,0);await qualifyPlayerArtReview(c.review,i,...args,desired);await qualifyPlayerArtProposedPose(c.pose,c.review,i,...args,desired);
  for(const mutate of [v=>delete v.owners[id].glb_import,v=>delete v.owners[id],v=>v.owners[id].glb_import.baseline_slot_sha256='0'.repeat(64),v=>v.owners[id].glb_import.import_digest='0'.repeat(64),v=>v.owners[id].glb_import.glb_sha256='0'.repeat(64),v=>v.owners[id].decoded_sha256='0'.repeat(64),v=>v.owners[id].edits[0].translation[0]++]){
    const bad=structuredClone(i);mutate(bad);await assert.rejects(()=>qualifyPlayerArtInspection(bad,...args,0,0));refused++;
  }
  // Alter both copies of metadata: equality alone must not qualify a baseline.
  for(const mutate of [e=>e.baseline_slot_sha256='f'.repeat(64),e=>e.baseline_owners[id]={...structuredClone(i.owners[id]),glb_import:structuredClone(i.owners[id].glb_import)}]){
    const bad=structuredClone(i),report=structuredClone(ar);mutate(bad.owners[id].glb_import);report.retained_art_inputs[0].source_record=structuredClone(bad.owners[id].glb_import);
    await assert.rejects(()=>qualifyPlayerArtInspection(bad,report,c.model_report,record,c.selection,0,0));refused++;
  }
  if(c.edited_baseline){
    const bad=structuredClone(i),report=structuredClone(ar),e=bad.owners[id].glb_import;const neighbor=Object.keys(e.baseline_owners).find(k=>k!==id);e.baseline_owners[neighbor].edits[0].translation[0]++;
    report.retained_art_inputs[0].source_record=structuredClone(e);
    await assert.rejects(()=>qualifyPlayerArtInspection(bad,report,c.model_report,record,c.selection,0,0));refused++;
  }
  for(const mutate of [v=>delete v.ownership_after.glb_import,v=>v.ownership_after.glb_import.fps=24,v=>v.ownership_after.glb_import.baseline_owners={}]){
    const bad=structuredClone(c.review);mutate(bad);if(JSON.stringify(bad)===JSON.stringify(c.review))continue;
    await assert.rejects(()=>qualifyPlayerArtReview(bad,i,...args,desired));refused++;
  }
  const bad=structuredClone(i),data=Buffer.from(bad.current_slot_base64,'base64');data[data.length-1]^=1;bad.current_slot_base64=data.toString('base64');bad.current_slot_sha256=await placementDigest(data);
  await assert.rejects(()=>qualifyPlayerArtInspection(bad,...args,0,0));refused++;
  for(const mutate of [v=>v.proposed_pose.geometry.vertices[0][0]++,v=>v.current_pose.object_transforms[0].translation[0]++,v=>v.proposed_pose.geometry.bounds.max[0]++]){
    const changed=structuredClone(c.pose);mutate(changed);await assert.rejects(()=>qualifyPlayerArtProposedPose(changed,c.review,i,...args,desired));refused++;
  }
}
console.log(`Two imported owner/baseline Current/numeric Review/pose cases independently qualified; ${refused} receipt/ledger/registry/baseline/neighbor/pose-byte refusals passed`);
