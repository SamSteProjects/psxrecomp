import assert from 'node:assert/strict';
import fs from 'node:fs';
import {decodeFlagResource} from '../editor/flag-resource.js';
import {decodeAssetReferences} from '../editor/asset-references.js';
const {group,report}=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const decoded=decodeFlagResource(group);assert.equal(decoded.references[0].effective_index,group.references[0].authored_index);
decodeAssetReferences(report,report.asset_id,report.source_key);
for(const mutate of [g=>delete g.references[0].authored_qualification,g=>g.references[0].authored_qualification.schema_version='legaia.flag-operand-qualification.v1',g=>g.references[0].authored_qualification.extended_target=g.extended_target===null?1:null]){const bad=structuredClone(group);mutate(bad);assert.throws(()=>decodeFlagResource(bad));}
const bad=structuredClone(report);bad.incoming.find(e=>e.kind==='effective_controller_flag_reference').flag_binding_evidence.effective_index=0;assert.throws(()=>decodeAssetReferences(bad,bad.asset_id,bad.source_key));
console.log(`${group.bank} controller bit: Retail/Current resource and graph decoding, missing/foreign/stale proof refusal passed.`);
