import assert from 'node:assert/strict';
import fs from 'node:fs';
import {decodeFlagQualification} from '../editor/flag-qualification.js';
import {decodeFlagResource} from '../editor/flag-resource.js';
import {decodeAssetReferences} from '../editor/asset-references.js';
const expected={owner_id:'scene://fixture/actors/man-p1/0003',operand_id:'script://fixture/actors/man-p1/0003/system-flag/0005',source_record_sha256:'a'.repeat(64),pc:5,mnemonic:'SYSFLAG_SET',extended_target:null,retail_index:326,authored_index:4095};
const proof={schema_version:'legaia.system-flag-operand-qualification.v1',...expected,maximum:4095};
assert.deepEqual(decodeFlagQualification(proof,expected),proof);
for(const patch of [{maximum:31},{schema_version:'legaia.flag-operand-qualification.v1'},{extended_target:0},{authored_index:4096},{operand_id:expected.operand_id.replace('/system-flag/','/flag-bit/')},{source_record_sha256:'b'.repeat(64)}])assert.throws(()=>decodeFlagQualification({...proof,...patch},expected));
if(process.argv[2]){
 const data=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
 const asset=decodeFlagResource(data.asset),graph=decodeAssetReferences(data.graph,data.graph.asset_id,data.graph.source_key);
 const authored=asset.references.find(r=>r.authored_index!==null);
 assert.equal(authored.retail_index,326);assert.equal(authored.effective_index,4095);
 const edge=graph.incoming.find(e=>e.kind==='effective_script_flag_reference');assert.equal(edge.flag_binding_evidence.effective_index,4095);
 for(const mutate of [a=>delete a.references.find(r=>r.authored_index!==null).authored_qualification,a=>a.references.find(r=>r.authored_index!==null).authored_qualification.maximum=31,a=>a.references.find(r=>r.authored_index!==null).effective_index=4096]){const bad=structuredClone(data.asset);mutate(bad);assert.throws(()=>decodeFlagResource(bad));}
 for(const mutate of [e=>delete e.flag_binding_evidence.native_operand_qualification,e=>e.flag_binding_evidence.effective_index=4096,e=>e.flag_reference_evidence.extended_target=0,e=>e.flag_binding_evidence.operand_id=e.flag_binding_evidence.operand_id.replace('/system-flag/','/flag-bit/')]){const bad=structuredClone(data.graph);mutate(bad.incoming.find(e=>e.kind==='effective_script_flag_reference'));assert.throws(()=>decodeAssetReferences(bad,bad.asset_id,bad.source_key));}
 const inherited=graph.incoming.filter(e=>e.kind==='npc_script_flag_operand');assert(inherited.length);assert(inherited.every(e=>e.npc_flag_operand_evidence.authored_index===null&&e.npc_flag_operand_evidence.effective_index===326));
 console.log('Actual Retail resource/graph client readback and donor-versus-NPC selector separation passed.');
}
console.log('System selector native qualifier bounds, family and ownership guards passed.');
