import fs from 'node:fs';import assert from 'node:assert/strict';
import {decodePlayerBattles,playerBattleProjectRecords} from '../editor/player-battle.js';
import {qualifyPlayerCurrent} from '../editor/player-model-review.js';
import {qualifyPlayerActionInspection,qualifyPlayerActionReview} from '../editor/player-action-editor.js';
import {placementDigest} from '../editor/worldmap-placement-replay.js';
const {report,raw,inspection,review,edit}=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),r=await decodePlayerBattles(report,{projectPath:report.project_path,sourceKey:report.project_source_key}),record=playerBattleProjectRecords(r).find(v=>v.id===raw.record.semantic_id),base=await qualifyPlayerCurrent(raw,r,record);
const observed=await qualifyPlayerActionInspection(inspection,r,record,base,0);await qualifyPlayerActionReview(review,observed,r,record,edit);let refused=0;
for(const mutate of [v=>v.current_file_sha256='0'.repeat(64),v=>v.current_bank_sha256='0'.repeat(64),v=>v.current_action_base64=v.current_action_base64.slice(4),v=>v.original_clip.frame_count++]){const bad=structuredClone(inspection);mutate(bad);await assert.rejects(qualifyPlayerActionInspection(bad,r,record,base,0));refused++;}
for(const mutate of [v=>v.layer='current',v=>v.project_changed=true,v=>v.projection.channels[0].after_value++,v=>v.projection.changed_bytes[0].after_byte++,v=>v.projection.source_bank_sha256='0'.repeat(64),v=>v.projection.proposed_action_sha256='0'.repeat(64),v=>v.binding.current_sha256='0'.repeat(64)]){const bad=structuredClone(review);mutate(bad);await assert.rejects(qualifyPlayerActionReview(bad,observed,r,record,edit));refused++;}
const malicious=structuredClone(review),packet=Uint8Array.from(atob(malicious.proposed_action_base64),c=>c.charCodeAt(0));packet[packet.length-1]^=1;malicious.proposed_action_base64=Buffer.from(packet).toString('base64');malicious.projection.proposed_action_sha256=await placementDigest(packet);await assert.rejects(qualifyPlayerActionReview(malicious,observed,r,record,edit));refused++;
console.log(`Literal action channel/byte Review and ${refused} altered inspection/Review receipts pass`);
