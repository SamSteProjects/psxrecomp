import fs from 'node:fs';
import assert from 'node:assert/strict';
import {decodePlayerArts} from '../editor/player-art-animation.js';
import {qualifyPlayerArtCurrentExport} from '../editor/player-art-export.js';
const cases=JSON.parse(fs.readFileSync(process.argv[2],'utf8')).cases;let refused=0;
for(const c of cases){const ar=await decodePlayerArts(c.art_report,{projectPath:c.art_report.project_path,sourceKey:c.art_report.project_source_key},c.model_report),record={id:c.model.semantic_id,data:c.model},qualify=v=>qualifyPlayerArtCurrentExport(v,ar,c.model_report,record,c.selection,c.inspection);await qualify(c.export);
  for(const change of [v=>v.motion_layer='retail',v=>v.inspection.current_slot_sha256='stale',v=>v.audit.source_record.motion.current_body_sha256='stale',v=>v.audit.representation='player-art-selected-equipment-assembly',v=>v.filename='original.glb',v=>v.audit.object_count++]){const v=structuredClone(c.export);change(v);await assert.rejects(()=>qualify(v));refused++;}
}
console.log(`${cases.length} Current motion exports qualified against full geometry/tracks/images; ${refused} motion/source/audit refusals passed`);
