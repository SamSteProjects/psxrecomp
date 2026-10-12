import fs from 'node:fs';import assert from 'node:assert/strict';
import {decodePlayerBattles,playerBattleProjectRecords} from '../editor/player-battle.js';
import {qualifyPlayerActionRange,playerActionRangeEdits} from '../editor/player-action-editor.js';
const cases=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let refused=0;
for(const {report,inspection,review,spec} of cases){const r=await decodePlayerBattles(report,{projectPath:report.project_path,sourceKey:report.project_source_key}),record=playerBattleProjectRecords(r).find(v=>v.id===inspection.record.semantic_id);await qualifyPlayerActionRange(review,inspection,r,record,spec);assert.equal(playerActionRangeEdits(inspection,spec).length,3);
 for(const mutate of [v=>v.operation='edit',v=>v.range_spec.frame_end++,v=>v.projection.channels[0].after_value++,v=>v.proposed_action_base64=v.current_action_base64]){const bad=structuredClone(review);mutate(bad);await assert.rejects(qualifyPlayerActionRange(bad,inspection,r,record,spec));refused++;}
 for(const change of [{frame_start:true},{part_index:999},{mode:'wrap'},{axis:'q'},{value:.5}])assert.throws(()=>playerActionRangeEdits(inspection,{...spec,...change}));
}
console.log(`Two literal range Reviews and ${refused} altered range receipts pass`);
