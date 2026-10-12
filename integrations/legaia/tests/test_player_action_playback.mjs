import fs from 'node:fs';import assert from 'node:assert/strict';
import {createPlayerActionSampler} from '../editor/player-action-playback.js';
import {decodePlayerBattles,playerBattleProjectRecords} from '../editor/player-battle.js';
import {sampledWorldFrame} from '../editor/worldmap-animation-playback.js';
const cases=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let frames=0,vertices=0,refused=0;
for(const {report,raw,value,frames:native} of cases){
 const r=await decodePlayerBattles(report,{projectPath:report.project_path,sourceKey:report.project_source_key}),record=playerBattleProjectRecords(r).find(v=>v.id===raw.record.semantic_id),clip=value.clip,before=structuredClone(raw);
 const sampler=await createPlayerActionSampler(value,r,record,raw,clip);
 for(const expected of native){
  const sample=sampler.sample(expected.frame_index);assert.deepEqual(sample.object_transforms,expected.object_transforms);
  for(const [i,v] of sample.geometry.vertices.entries())for(let axis=0;axis<3;axis++)assert(Math.abs(v[axis]-expected.geometry.vertices[i][axis])<1e-7);
  for(const key of ['objects','triangles','triangle_uvs','triangle_materials','triangle_colors','materials','textures'])assert.deepEqual(sample.geometry[key],expected.geometry[key]);frames++;vertices+=sample.geometry.vertices.length;
 }
 assert.deepEqual(raw,before);const first=sampler.sample(0),saved=structuredClone(first);first.geometry.vertices[0][0]++;assert.deepEqual(sampler.sample(0),saved);
 const detachedClip=structuredClone(clip),held=await createPlayerActionSampler(value,r,record,raw,detachedClip);detachedClip.frame_count=0;detachedClip.part_count=0;assert.deepEqual(held.sample(0),saved);
 for(const f of [-1,sampler.frameCount,NaN,.5,true])assert.throws(()=>sampler.sample(f));
 for(const mutate of [v=>v.layer='foreign',v=>v.effective_file_sha256='0'.repeat(64),v=>v.project_source_key='0'.repeat(64),v=>v.clip.source_record.sha256='0'.repeat(64),v=>v.action_base64=v.action_base64.slice(4),v=>v.assembly.animation_part_indices[0]=63]){
  const bad=structuredClone(value);mutate(bad);await assert.rejects(createPlayerActionSampler(bad,r,record,raw,clip));refused++;
 }
}
assert.equal(sampledWorldFrame(0,9,12,1e4),8);console.log(`${frames} native Retail/Current frames, ${vertices} vertices and ${refused} altered playback receipts pass`);
