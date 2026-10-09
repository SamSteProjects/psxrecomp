import fs from 'node:fs';
import assert from 'node:assert/strict';
import {decodeAssetReferences,assetReferenceInstructionSite,assetReferenceRelationLabel,filterAssetReferences} from '../editor/asset-references.js';
const reports=JSON.parse(fs.readFileSync(process.env.LEGAIA_CONTROLLER_CURRENT_GRAPH+'/reports.json'));
for(const [name,report] of Object.entries(reports)){
 const scope=name.startsWith('project')?'project':'active',decoded=decodeAssetReferences(report,report.asset_id,report.source_key,scope),nodes=new Map(decoded.nodes.map(n=>[n.id,n]));
 const current=decoded.incoming.concat(decoded.outgoing).find(e=>e.kind==='effective_controller_flag_reference');
 assert.equal(assetReferenceInstructionSite(current,nodes,scope).pc,24);assert.equal(assetReferenceInstructionSite(current,nodes,scope).owner_id,'scene://town01/controllers/man-p1/0000');
 assert.match(assetReferenceRelationLabel(current),/Current controller system selector 1157/);
 const filtered=filterAssetReferences(decoded,{layer:'effective'});assert.equal(filtered.incoming.length+filtered.outgoing.length,1);
}
const base=reports['active-flag'];let refusals=0;
for(const mutate of [
 e=>e.layer='decoded',e=>e.kind='effective_script_flag_reference',e=>e.pc=25,e=>e.flag_binding_evidence.effective_index=999,
 e=>e.flag_binding_evidence.source_record_sha256='f'.repeat(64),e=>e.flag_binding_evidence.component_sha256='invalid',
 e=>e.flag_binding_evidence.native_operand_qualification.schema_version='legaia.system-flag-operand-qualification.v1',
 e=>e.flag_binding_evidence.native_operand_qualification.owner_id='scene://town01/actors/man-p1/0001',
 e=>e.flag_binding_evidence.native_operand_qualification.runtime_value=1,e=>e.controller_source_evidence.execution='confirmed',
 e=>e.source_catalog_key='f'.repeat(64),e=>e.flag_reference_evidence.index=1157
]){
 const bad=structuredClone(base);mutate(bad.incoming.find(e=>e.kind==='effective_controller_flag_reference'));assert.throws(()=>decodeAssetReferences(bad,bad.asset_id,bad.source_key));refusals++;
}
for(const mutate of [r=>r.incoming=r.incoming.filter(e=>e.kind!=='controller_flag_reference'),r=>r.incoming.push({...structuredClone(r.incoming.find(e=>e.kind==='effective_controller_flag_reference')),id:'f'.repeat(64)})]){
 const bad=structuredClone(base);mutate(bad);assert.throws(()=>decodeAssetReferences(bad,bad.asset_id,bad.source_key));refusals++;
}
console.log(`Four real active/project controller/flag graphs, effective filtering and exact source navigation passed; ${refusals} forged/pairing refusals.`);
