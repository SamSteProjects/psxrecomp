import assert from 'node:assert/strict';
import fs from 'node:fs';
import {decodeAssetReferences,assetReferenceRelationLabel} from '../editor/asset-references.js';
const report=JSON.parse(fs.readFileSync(process.env.LEGAIA_CONTROLLER_REFERENCE_EVIDENCE));
const read=value=>decodeAssetReferences(value,report.asset_id,report.source_key);
const decoded=read(report),edge=decoded.incoming[0];
assert.equal(edge.kind,'scene_entry_controller_source');
assert.match(assetReferenceRelationLabel(edge),/runtime execution not asserted/);
assert.equal(decoded.outgoing.length,0);
edge.controller_source_evidence.source_record.sha256='changed';
assert.notEqual(report.incoming[0].controller_source_evidence.source_record.sha256,'changed');
let refusals=0;
for(const change of [
 v=>v.incoming[0].source_id=v.asset_id,v=>v.incoming[0].layer='imported',v=>v.incoming[0].runtime_binding='confirmed',
 v=>v.incoming[0].kind='actor_script_record',v=>v.incoming[0].pc=0,
 v=>v.incoming.push({...structuredClone(v.incoming[0]),id:'0'.repeat(64)}),
 v=>v.nodes.find(n=>n.id===v.asset_id).kind='script',
 v=>v.incoming[0].controller_source_evidence.execution='confirmed',
 v=>v.incoming[0].controller_source_evidence.relationship='runtime_binding',
 v=>v.incoming[0].controller_source_evidence.entry_pc++,
 v=>v.incoming[0].controller_source_evidence.local_count=true,
 ...['disc_identity','iso_file','prot_entry','prot_entry_name','record_kind','record_index','byte_coordinate_space','byte_offset','byte_length','containing_decoded_size','sha256'].map(key=>v=>v.incoming[0].controller_source_evidence.source_record[key]=null)
]){const bad=structuredClone(report);change(bad);assert.throws(()=>read(bad));refusals++;}
console.log(`Controller ownership decoder passed; ${refusals} forged relationships refused.`);
