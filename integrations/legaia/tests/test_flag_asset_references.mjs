import assert from 'node:assert/strict';
import {decodeAssetReferences,assetReferenceInstructionSite,assetReferenceRelationLabel} from '../editor/asset-references.js';
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

const current=structuredClone(report);
current.asset_id=script;current.nodes[1].id=`flag-reference://fixture/scripts/man-p2/0004/current/global/2`;
current.outgoing=current.incoming;current.incoming=[];
const edge=current.outgoing[0];edge.target_id=current.nodes[1].id;edge.kind='effective_script_flag_reference';edge.layer='effective';edge.pc=5;
edge.flag_reference_evidence={bank:'global',index:2,scope:'host_global_flags',extended_target:null,grouping_layer:'retail',operation:'set',mnemonic:'GFLAG_SET'};
edge.flag_binding_evidence={operand_id:script+'/flag-bit/0005',retail_index:2,effective_index:3,source_record_sha256:'d'.repeat(64),component_sha256:'e'.repeat(64)};
assert.equal(decodeAssetReferences(current,script,sourceKey).outgoing[0].flag_binding_evidence.effective_index,3);
for(const mutate of [r=>delete r.outgoing[0].flag_binding_evidence,r=>r.outgoing[0].flag_binding_evidence.operand_id=script+'/flag-bit/0007',r=>r.outgoing[0].flag_binding_evidence.retail_index=3,r=>r.outgoing[0].flag_binding_evidence.effective_index=32,r=>r.outgoing[0].flag_binding_evidence.source_record_sha256='invalid',r=>r.outgoing[0].flag_binding_evidence.component_sha256='invalid',r=>r.outgoing[0].flag_reference_evidence.mnemonic='SYSFLAG_SET',r=>r.outgoing[0].kind='script_flag_reference',r=>r.outgoing[0].source_catalog_key='invalid',r=>r.outgoing[0].flag_binding_evidence.runtime_value=1]){
 const invalid=structuredClone(current);mutate(invalid);assert.throws(()=>decodeAssetReferences(invalid,script,sourceKey));
}
console.log('Current flag operand provenance and source grouping guards passed.');

for(const mutate of [r=>r.outgoing[0].pc=65536,r=>r.outgoing[0].flag_reference_evidence.scope='host_extra_flags',r=>r.outgoing[0].scene_id='scene://other',r=>r.nodes[0].scene_id='scene://other',r=>r.outgoing[0].flag_binding_evidence.effective_index=true]){
 const invalid=structuredClone(current);mutate(invalid);assert.throws(()=>decodeAssetReferences(invalid,script,sourceKey));
}
for(const [bank,prefix,index,bit] of [['local','LFLAG',2,16],['context','CFLAG',2,8],['context','CFLAG',8,2]]){
 const invalid=structuredClone(current),e=invalid.outgoing[0];e.flag_reference_evidence={...e.flag_reference_evidence,bank,index,scope:bank==='local'?'dispatch_context_local_flags':'dispatch_context_flags',mnemonic:prefix+'_SET'};e.target_id=e.source_id.replace('script://','flag-reference://')+'/current/'+bank+'/'+index;invalid.nodes[1].id=e.target_id;e.flag_binding_evidence.retail_index=index;e.flag_binding_evidence.effective_index=bit;assert.throws(()=>decodeAssetReferences(invalid,script,sourceKey));
}

const site=assetReferenceInstructionSite(edge,new Map(current.nodes.map(n=>[n.id,n])));assert.equal(site.pc,5);assert.equal(site.source_record_sha256,'d'.repeat(64));assert.equal(site.script_id,script);
assert(assetReferenceRelationLabel(edge).includes('Current authored global flag operand 3'));
