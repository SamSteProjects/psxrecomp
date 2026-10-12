import fs from 'node:fs';import assert from 'node:assert/strict';
import {decodePlayerBattles,playerBattleProjectRecords} from '../editor/player-battle.js';
import {qualifyPlayerActionRestore,playerActionRestoreEdits} from '../editor/player-action-editor.js';
const {restore_reviews:cases}=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let axes=0,refused=0;
for(const {inspection,review,report} of cases){const r=await decodePlayerBattles(report,{projectPath:report.project_path,sourceKey:report.project_source_key}),record=playerBattleProjectRecords(r).find(v=>v.id===inspection.record.semantic_id);await qualifyPlayerActionRestore(review,inspection,r,record);axes+=review.projection.channels.length;assert(playerActionRestoreEdits(inspection).length>0);
 for(const mutate of [v=>v.operation='edit',v=>v.proposed_action_base64=v.current_action_base64,v=>v.projection.channels[0].after_value++,v=>v.projection.source_action_sha256='0'.repeat(64)]){const bad=structuredClone(review);mutate(bad);await assert.rejects(qualifyPlayerActionRestore(bad,inspection,r,record));refused++;}
}
assert.equal(cases.length,2);console.log(`Two complete Retail action restorations, ${axes} axes and ${refused} altered restore receipts pass`);
