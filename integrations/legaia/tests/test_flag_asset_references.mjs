import assert from 'node:assert/strict';
import {decodeAssetReferences} from '../editor/asset-references.js';
const sourceKey='a'.repeat(64),catalogKey='b'.repeat(64),scene='scene://fixture';
const script='script://fixture/scripts/man-p2/0004',flag='flag-reference://fixture/scripts/man-p2/0004/extended-7/system/32771';
const proof={bank:'system',index:32771,scope:'system_bank_encoded_selector',extended_target:7,grouping_layer:'retail',operation:'test',mnemonic:'SYSFLAG_TEST'};
const report={schema_version:'legaia.asset-references.v1',asset_id:flag,source_key:sourceKey,read_only:true,
  nodes:[{id:script,kind:'script',scene_id:scene,label:'Script',available:true},{id:flag,kind:'flag',scene_id:scene,label:'Encoded reference',available:true}],
  incoming:[{id:'c'.repeat(64),source_id:script,target_id:flag,kind:'script_flag_reference',scene_id:scene,layer:'decoded',pc:17,runtime_binding:'not_asserted',source_import_sha256:sourceKey,source_catalog_key:catalogKey,flag_reference_evidence:proof}],outgoing:[],
  coverage:{verified_scene_ids:[scene],resource_scene_id:scene,unresolved_reference_count:0},limitations:['Encoded source references only.']};
const decoded=decodeAssetReferences(report,flag,sourceKey);
decoded.incoming[0].flag_reference_evidence.index=0;assert.equal(proof.index,32771);
for(const mutate of [r=>r.incoming[0].layer='effective',r=>r.incoming[0].pc=undefined,r=>r.incoming[0].flag_reference_evidence.grouping_layer='effective',r=>r.incoming[0].flag_reference_evidence.index=3,r=>r.incoming[0].flag_reference_evidence.bank='global',r=>r.incoming[0].flag_reference_evidence.extended_target=8,r=>r.incoming[0].flag_reference_evidence.runtime_value=1,r=>r.incoming[0].flag_reference_evidence.operation='execute',r=>r.nodes[0].kind='actor',r=>r.incoming[0].kind='script_dialogue_segment']){
  const invalid=structuredClone(report);mutate(invalid);assert.throws(()=>decodeAssetReferences(invalid,flag,sourceKey));
}
console.log('Source-scoped flag graph evidence and fabricated runtime relationship guards passed.');
