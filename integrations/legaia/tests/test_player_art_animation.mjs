import fs from 'node:fs';
import assert from 'node:assert/strict';
import {decodePlayerArts,playerArtProjectRecords,createPlayerArtSampler,qualifyPlayerArtPose} from '../editor/player-art-animation.js';

import {playerArtChannelTrack} from '../editor/player-art-timeline.js';
const fixture=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let frames=0,refusals=0;
for(const c of fixture.cases){
  const expected={projectPath:c.art_report.project_path,sourceKey:c.art_report.project_source_key},report=await decodePlayerArts(c.art_report,expected,c.model_report),record={id:c.model.semantic_id,data:c.model};
  const sampler=await createPlayerArtSampler(c.playback,report,c.model_report,record,c.selection);
  for(const pose of c.poses){await qualifyPlayerArtPose(pose,report,c.model_report,record,c.selection,pose.frame_index);const v=sampler.sample(pose.frame_index);assert.equal(v.geometry.vertices.length,pose.geometry.vertices.length);frames++;}
  const records=playerArtProjectRecords(report);assert.equal(records.length,196);assert.equal(new Set(records.map(r=>r.id)).size,196);assert.equal(records.filter(r=>r.projectPlayerArt.artRecordId===null).length,87);
  for(const part of new Set(c.playback.base_inspection.assembly.animation_part_indices))for(const field of ['translation','rotation_psx'])for(const [a,axis] of [...'xyz'].entries()){const track=playerArtChannelTrack(c.playback,part,field,axis);for(const pose of c.poses){const tr=pose.object_transforms.find(t=>t.part_index===part);assert.equal(track.samples[pose.frame_index].retail,tr[field][a]);}}
  assert.throws(()=>playerArtChannelTrack(c.playback,-1,'translation','x'));assert.throws(()=>playerArtChannelTrack(c.playback,0,'translation','bad'));
  const held=sampler.sample(0),x=held.geometry.vertices[0][0];held.geometry.vertices[0][0]+=200;assert.equal(sampler.sample(0).geometry.vertices[0][0],x);
  for(const edit of [v=>v.project_source_key='stale',v=>v.art_source_key='stale',v=>v.stream.part_count++,v=>v.art_record.stream_source++,v=>v.layer='foreign',v=>v.effective_file_sha256='0'.repeat(64),v=>v.source_slot_base64=Buffer.from('changed').toString('base64'),v=>v.decoded_stream_base64=Buffer.from('changed').toString('base64'),v=>v.base_inspection.assembly.animation_part_indices[0]=63,v=>v.base_inspection.geometry.vertices[0][0]++]){
    const changed=structuredClone(c.playback);edit(changed);await assert.rejects(()=>createPlayerArtSampler(changed,report,c.model_report,record,c.selection));refusals++;
  }
  for(const edit of [v=>v.geometry.vertices[0][0]++,v=>v.object_transforms[0].translation[0]++,v=>v.frame_index++,v=>v.geometry.textures=[],v=>v.geometry.bounds.min[0]++]){
    const changed=structuredClone(c.poses[0]);edit(changed);await assert.rejects(()=>qualifyPlayerArtPose(changed,report,c.model_report,record,c.selection,c.poses[0].frame_index));refusals++;
  }
  for(const edit of [v=>v.project_path+='foreign',v=>v.catalog.source_key='0'.repeat(64),v=>v.catalog.streams.pop(),v=>v.catalog.archives[0].slot_index++,v=>v.catalog.records[0].stream_source=255,v=>v.catalog.records[0].source_record.byte_offset++,v=>v.catalog.streams[0].source_record.decoded_sha256='bad']){
    const changed=structuredClone(c.art_report);edit(changed);await assert.rejects(()=>decodePlayerArts(changed,expected,c.model_report));refusals++;
  }
}
console.log(`${fixture.cases.length} Retail/Current explicit archive samplers / ${frames} source poses / ${refusals} source, mapping, texture, pose and record refusals pass`);
