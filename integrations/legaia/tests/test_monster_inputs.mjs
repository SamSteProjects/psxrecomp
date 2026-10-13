import fs from 'node:fs';
import assert from 'node:assert/strict';
import {decodeMonsterResources,monsterRecords} from '../editor/monster-archive.js';
import {qualifyMonsterInputs,qualifyMonsterInputDownload} from '../editor/monster-inputs.js';

const proof=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),report=proof.report;
await decodeMonsterResources(report,{projectPath:report.project_path,sourceKey:report.project_source_key});
const record=monsterRecords(report).find(r=>r.projectMonsterInput);
assert(record);const bytes=await qualifyMonsterInputDownload(proof.download,report,record);
assert.equal(bytes.length,record.data.byte_length);
let refusals=0;
for(const change of [r=>r.retained_inputs[0].sha256='0'.repeat(64),r=>r.retained_inputs[0].texture_asset_id='foreign',r=>r.retained_inputs.push(structuredClone(r.retained_inputs[0])),r=>r.retained_inputs[0].source_record.palette_index=15,r=>r.retained_inputs[0].references=[],r=>r.retained_inputs[0].current_pool_sha256='bad']){
 const altered=structuredClone(report);change(altered);assert.throws(()=>qualifyMonsterInputs(altered));refusals++;
}
for(const change of [v=>v.kind='stp',v=>v.current_pool_sha256='0'.repeat(64),v=>v.png_base64=Buffer.from('changed').toString('base64'),v=>v.retained_source.palette_mode='existing',v=>v.filename='../input.png',v=>v.project_source_key='foreign']){
 const altered=structuredClone(proof.download);change(altered);await assert.rejects(qualifyMonsterInputDownload(altered,report,record));refusals++;
}
const masked=structuredClone(report),row=masked.retained_inputs[0];row.source_record.stp_sha256=row.source_record.png_sha256;row.source_record.stp_byte_length=row.source_record.png_byte_length;
assert.throws(()=>qualifyMonsterInputs(masked));
console.log(`Retained monster input metadata and exact recovery qualify; ${refusals+1} altered or incomplete receipts refuse`);
