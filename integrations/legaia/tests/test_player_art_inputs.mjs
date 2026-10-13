import fs from 'node:fs';
import assert from 'node:assert/strict';
import {decodePlayerArts,playerArtProjectRecords} from '../editor/player-art-animation.js';
import {qualifyPlayerArtInputs,playerArtInputRecords,qualifyPlayerArtInputExport} from '../editor/player-art-inputs.js';
const c=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const report=await decodePlayerArts(c.art_report,{projectPath:c.art_report.project_path,sourceKey:c.art_report.project_source_key},c.model_report);
const records=playerArtInputRecords(report);assert.equal(records.length,1);assert.equal(playerArtProjectRecords(report).length,197);
const bytes=await qualifyPlayerArtInputExport(c.export,report,records[0]);assert.equal(bytes.length,records[0].data.source_record.glb_byte_length);
let refusals=0;
for(const mutate of [r=>r.retained_art_inputs.push(structuredClone(r.retained_art_inputs[0])),r=>r.retained_art_inputs[0].stream_asset_id='wrong',r=>r.retained_art_inputs[0].current_body_sha256='wrong',r=>r.retained_art_inputs[0].relationship='final_current',r=>r.retained_art_inputs[0].source_record.model_source_sha256='0'.repeat(64),r=>r.retained_art_inputs[0].source_record.glb_byte_length=true,r=>r.retained_art_inputs[0].source_record.baseline_slot_byte_length=0,r=>r.retained_art_inputs[0].source_record.fps=NaN,r=>r.retained_art_inputs[0].source_record.equipped[0]=true,r=>r.retained_art_inputs[0].source_record.object_part_indices[0]=999,r=>r.retained_art_inputs[0].source_record.extra=true,r=>r.retained_art_inputs[0].source_record.object_node_indices=[0]]){
 const bad=structuredClone(report);mutate(bad);assert.throws(()=>qualifyPlayerArtInputs(bad));refusals++;
}
for(const mutate of [v=>v.project_source_key='stale',v=>v.filename='current.glb',v=>v.record.current_decoded_sha256='0'.repeat(64),v=>v.project_changed=true,v=>v.glb_base64=Buffer.from('changed').toString('base64')]){
 const bad=structuredClone(c.export);mutate(bad);await assert.rejects(()=>qualifyPlayerArtInputExport(bad,report,records[0]));refusals++;
}
console.log(`One retained art record, 197 total art assets and exact historical download qualified; ${refusals} registration/export refusals passed`);
