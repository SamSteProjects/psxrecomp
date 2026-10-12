import fs from 'node:fs';
import assert from 'node:assert/strict';
import {decodePlayerBattles,playerBattleProjectRecords,qualifyPlayerPose,qualifyPlayerExport} from '../editor/player-battle.js';
import {qualifyPlayerCurrent} from '../editor/player-model-review.js';
const {report,cases,corners}=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
let refused=0,files=0,vertices=0;
for(const {raw,posed,exports} of cases){
 const source=structuredClone(report);source.project_source_key=raw.project_source_key;
 const r=await decodePlayerBattles(source,{projectPath:source.project_path,sourceKey:source.project_source_key});
 const record=playerBattleProjectRecords(r).find(v=>v.id===raw.record.semantic_id);
 const base=await qualifyPlayerCurrent(raw,r,record);
 qualifyPlayerPose(posed,r,record,base,posed.clip,posed.frame_index);vertices+=posed.geometry.vertices.length;
 for(const mutate of [v=>v.layer='retail',v=>v.effective_file_sha256='0'.repeat(64),v=>v.project_source_key='0'.repeat(64),v=>v.geometry.vertices[0][0]++,v=>v.object_transforms[0].part_index=63]){
  const bad=structuredClone(posed);mutate(bad);assert.throws(()=>qualifyPlayerPose(bad,r,record,base,posed.clip,posed.frame_index));refused++;
 }
 for(const {result,selection} of exports){
  await qualifyPlayerExport(result,r,record,base,selection);files++;
  for(const mutate of [v=>v.layer='retail',v=>v.effective_file_sha256='0'.repeat(64),v=>v.audit.source_record.current_sha256='0'.repeat(64),v=>v.filename='../model.glb',v=>v.audit.sha256='0'.repeat(64),v=>v.assembly.tmd_sha256='0'.repeat(64)]){
   const bad=structuredClone(result);mutate(bad);await assert.rejects(qualifyPlayerExport(bad,r,record,base,selection));refused++;
  }
 }
}
assert.equal(files,12);console.log(`${files} Current exports, ${vertices} posed vertices, ${corners} exported corners and ${refused} altered receipt refusals pass`);
