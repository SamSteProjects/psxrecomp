import fs from 'node:fs';import assert from 'node:assert/strict';
import {decodeMonsterResources,monsterRecords} from '../editor/monster-archive.js';
import {qualifyMonsterModelInputs,qualifyMonsterModelInputDownload} from '../editor/monster-model-inputs.js';
const c=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),r=c.report;
await decodeMonsterResources(r,{projectPath:r.project_path,sourceKey:r.project_source_key});
const records=monsterRecords(r).filter(x=>x.projectMonsterModelInput);assert.equal(records.length,2);let refusals=0;
for(const [index,v] of c.downloads.entries())await qualifyMonsterModelInputDownload(v,r,records.find(x=>x.data.import_index===index));
for(const change of [r=>r.retained_model_inputs[0].sha256='0'.repeat(64),r=>r.retained_model_inputs[0].model_asset_id='foreign',r=>r.retained_model_inputs.pop(),r=>r.retained_model_inputs[0].import_index=16,r=>r.retained_model_inputs[1].source_record.binding.current_tmd_sha256='0'.repeat(64),r=>r.retained_model_inputs[0].source_record.baseline_sha256='0'.repeat(64),r=>r.retained_model_inputs[0].references=[],r=>r.retained_model_inputs.push(structuredClone(r.retained_model_inputs[0]))]){const changed=structuredClone(r);change(changed);assert.throws(()=>qualifyMonsterModelInputs(changed));refusals++;}
for(const change of [v=>v.import_index=1,v=>v.current_tmd_sha256='0'.repeat(64),v=>v.glb_base64=Buffer.from('changed').toString('base64'),v=>v.filename='../input.glb',v=>v.retained_source.review_key='0'.repeat(64),v=>v.project_source_key='foreign']){const changed=structuredClone(c.downloads[0]);change(changed);await assert.rejects(qualifyMonsterModelInputDownload(changed,r,records.find(x=>x.data.import_index===0)));refusals++;}
console.log(`Two historical monster model inputs and exact originals qualify; ${refusals} altered or incomplete receipts refuse`);
