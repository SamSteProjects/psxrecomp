import fs from 'node:fs';import assert from 'node:assert/strict';
import {decodePlayerBattles,playerBattleProjectRecords,qualifyPlayerPose,qualifyPlayerExport} from '../editor/player-battle.js';
import {qualifyPlayerCurrent} from '../editor/player-model-review.js';
import {createPlayerActionSampler} from '../editor/player-action-playback.js';
const {report,raw,poses,playback,exported}=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const r=await decodePlayerBattles(report,{projectPath:report.project_path,sourceKey:report.project_source_key}),record=playerBattleProjectRecords(r).find(v=>v.id===raw.record.semantic_id),base=await qualifyPlayerCurrent(raw,r,record);
for(const p of poses)qualifyPlayerPose(p,r,record,base,record.data.actions[p.action_slot],p.frame_index);
const sampler=await createPlayerActionSampler(playback,r,record,base,record.data.actions[0]),sample=sampler.sample(0);
assert.deepEqual(sample.object_transforms,poses[0].object_transforms);
for(const [i,v] of sample.geometry.vertices.entries())for(let k=0;k<3;k++)assert(Math.abs(v[k]-poses[0].geometry.vertices[i][k])<1e-7);
await qualifyPlayerExport(exported,r,record,base,{mode:'clip',action_slot:0,frame_index:null,fps:30});
let refused=0;
for(const mutate of [v=>v.action_file_sha256='0'.repeat(64),v=>v.action_clips[0].source_record.source_entry_sha256='0'.repeat(64),v=>v.action_clips[0].source_record.byte_offset++,v=>v.action_clips[0].frame_count++]){const bad=structuredClone(raw);mutate(bad);await assert.rejects(qualifyPlayerCurrent(bad,r,record));refused++;}
for(const mutate of [v=>v.current_clip.source_record.sha256='0'.repeat(64),v=>v.current_clip=record.data.actions[0],v=>v.action_base64=v.action_base64.slice(4)]){const bad=structuredClone(playback);mutate(bad);await assert.rejects(createPlayerActionSampler(bad,r,record,base,record.data.actions[0]));refused++;}
console.log(`Composed Current action/model client replay, both poses, authored full clip and ${refused} altered action witnesses pass`);
