import fs from 'node:fs';
import assert from 'node:assert/strict';
import {decodeFieldTextures,fieldTextureRecords,qualifyFieldInputDownload} from '../editor/field-textures.js';
import {projectAssetRecords} from '../editor/project-assets.js';
const cases=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),raw=cases.retained_report;
const expected={projectPath:raw.project_path,sourceKey:raw.project_source_key},report=decodeFieldTextures(raw,expected),records=fieldTextureRecords(report),inputs=records.filter(r=>r.projectFieldTextureInput);
assert.equal(records.length,10);assert.equal(inputs.length,2);
const project={scenes:[],assets:[],globalFieldTextures:report};
assert.deepEqual(projectAssetRecords(project,'global-field-party'),records);
assert.deepEqual(projectAssetRecords(project,'all'),records);
assert.deepEqual(projectAssetRecords(project,'global-battle-character'),[]);
assert.throws(()=>projectAssetRecords(project,'foreign-scene'));
let refused=0;
for(const change of [v=>v.retained_inputs[0].semantic_id+='x',v=>v.retained_inputs[0].references=[],v=>v.retained_inputs[0].retail_source.pack_slot=1,v=>v.retained_inputs[0].source_record.asset_id=raw.assets[1].semantic_id,v=>v.retained_inputs[0].layer='current',v=>v.retained_inputs[0].current_tim_sha256='bad',v=>v.retained_inputs.push(structuredClone(v.retained_inputs[0])),v=>v.retained_inputs.pop(),v=>v.retained_inputs[0].byte_length++,v=>v.retained_inputs[0].relationship='final_current_texture',v=>v.retained_inputs[0].source_record.palette_index=raw.assets[0].palette_count,v=>v.retained_inputs[0].source_record.tim_byte_length++]){
 const altered=structuredClone(raw);change(altered);assert.throws(()=>decodeFieldTextures(altered,expected));refused++;
}
for(const record of inputs){const payload=cases.input_downloads.find(v=>v.kind===record.data.kind),content=await qualifyFieldInputDownload(payload,report,record);assert.equal(content.length,record.data.byte_length);
 for(const change of [v=>v.asset_id=raw.assets[1].semantic_id,v=>v.project_source_key='0'.repeat(64),v=>v.current_sha256='0'.repeat(64),v=>v.retained_source.palette_index++,v=>v.layer='current',v=>v.filename='../input.png',v=>v.png_base64=Buffer.from('changed').toString('base64')]){const altered=structuredClone(payload);change(altered);await assert.rejects(qualifyFieldInputDownload(altered,report,record));refused++;}}
console.log(`Ten merged shared texture records, both original downloads and ${refused} altered metadata/download refusals pass`);
