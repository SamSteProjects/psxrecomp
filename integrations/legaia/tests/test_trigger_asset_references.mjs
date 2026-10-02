import assert from 'node:assert/strict';
import {decodeAssetReferences,assetReferenceRelationLabel,assetReferenceTriggerEvidenceLabel,assetReferenceNavigationNode} from '../editor/asset-references.js';

const key='a'.repeat(64),catalogKey='b'.repeat(64),rowHash='c'.repeat(64),scriptHash='d'.repeat(64),scene='scene://fixture';
const scriptId='script://fixture/scripts/man-p2/0000';
function report(){
  const nodes=[{id:scriptId,kind:'script',scene_id:scene,label:'Partition 2 script 0',available:true}];
  const incoming=[];
  for(const [table,index] of [['primary',0],['primary',1],['fallback',0]]){
    const trigger=`trigger://fixture/field-map/${table}/kind-1/${String(index).padStart(4,'0')}`;
    nodes.push({id:trigger,kind:'trigger',scene_id:scene,label:`${table} source row ${index}`,available:true});
    incoming.push({id:String(incoming.length+1).repeat(64),source_id:trigger,target_id:scriptId,kind:'field_trigger_script_reference',scene_id:scene,layer:'decoded',runtime_binding:'not_asserted',source_import_sha256:key,source_catalog_key:catalogKey,
      trigger_reference_evidence:{trigger_source_record_sha256:rowHash,script_source_record_sha256:scriptHash,table_source:table,table_kind:1,trigger_row_index:index,partition_two_record_index:0,gate:1,reachability:'not_evaluated'}});
  }
  return {schema_version:'legaia.asset-references.v1',asset_id:scriptId,source_key:key,read_only:true,nodes,incoming,outgoing:[],coverage:{verified_scene_ids:[scene],resource_scene_id:scene,unresolved_reference_count:3},limitations:['Encoded source references only; activation and gameplay reachability are not established.']};
}
const baseline=report(),before=structuredClone(baseline),decoded=decodeAssetReferences(baseline,scriptId,key);
assert.equal(decoded.incoming.length,3);
assert.deepEqual(decoded.incoming.map(edge=>edge.trigger_reference_evidence.table_source),['primary','primary','fallback']);
assert.notEqual(decoded.incoming[0].source_id,decoded.incoming[1].source_id);
decoded.incoming[0].trigger_reference_evidence.gate=0;assert.deepEqual(baseline,before);
for(const edge of baseline.incoming){
  assert.match(assetReferenceRelationLabel(edge),/encoded gate-1 trigger.*partition 2 source record 0.*activation not evaluated/);
  const label=assetReferenceTriggerEvidenceLabel(edge);
  assert.ok(label.includes(rowHash));assert.ok(label.includes(scriptHash));assert.ok(label.includes(edge.trigger_reference_evidence.table_source));
  assert.match(label,/activation, script execution and gameplay reachability are not established/);
}
assert.equal(assetReferenceTriggerEvidenceLabel({kind:'scene_actor'}),null);

const mutations=[
  value=>value.nodes[0].kind='actor',value=>value.nodes[0].scene_id='scene://foreign',value=>value.nodes[1].kind='region',value=>value.nodes[1].scene_id='scene://foreign',
  value=>value.incoming[0].kind='field_map_table_source',value=>value.incoming[0].layer='authored',value=>value.incoming[0].scene_id='scene://foreign',value=>value.incoming[0].runtime_binding='executed',value=>delete value.incoming[0].source_catalog_key,value=>value.incoming[0].source_catalog_key='bad',value=>value.incoming[0].source_import_sha256='bad',value=>value.incoming[0].pc=0,value=>value.incoming[0].material_evidence={},value=>delete value.incoming[0].trigger_reference_evidence,
  value=>value.incoming[0].trigger_reference_evidence.table_source='fallback',value=>value.incoming[0].trigger_reference_evidence.table_source='unknown',value=>value.incoming[0].trigger_reference_evidence.table_kind=0,value=>value.incoming[0].trigger_reference_evidence.table_kind=true,value=>value.incoming[0].trigger_reference_evidence.trigger_row_index=1,value=>value.incoming[0].trigger_reference_evidence.trigger_row_index=true,value=>value.incoming[0].trigger_reference_evidence.trigger_row_index=2043,value=>value.incoming[0].trigger_reference_evidence.partition_two_record_index=1,value=>value.incoming[0].trigger_reference_evidence.partition_two_record_index=256,value=>value.incoming[0].trigger_reference_evidence.partition_two_record_index=false,value=>value.incoming[0].trigger_reference_evidence.gate=0,value=>value.incoming[0].trigger_reference_evidence.gate=true,value=>value.incoming[0].trigger_reference_evidence.reachability='reachable',value=>value.incoming[0].trigger_reference_evidence.trigger_source_record_sha256='invalid',value=>value.incoming[0].trigger_reference_evidence.script_source_record_sha256='invalid',value=>value.incoming[0].trigger_reference_evidence.runtime_value=1,value=>value.incoming.push({...structuredClone(value.incoming[0]),id:'e'.repeat(64)}),
  value=>value.incoming[1].trigger_reference_evidence.script_source_record_sha256='e'.repeat(64),value=>value.incoming[1].source_catalog_key='e'.repeat(64),value=>value.incoming[1].source_import_sha256='e'.repeat(64)
];
for(const mutation of mutations){const bad=structuredClone(baseline);mutation(bad);assert.throws(()=>decodeAssetReferences(bad,scriptId,key));}
for(const wrong of ['trigger://fixture/field-map/primary/kind-0/0000','trigger://other/field-map/primary/kind-1/0000','trigger://fixture/field-map/primary/kind-1/0','trigger://fixture/field-map/primary/kind-1/2043']){
  const bad=structuredClone(baseline);bad.nodes[1].id=bad.incoming[0].source_id=wrong;assert.throws(()=>decodeAssetReferences(bad,scriptId,key));
}
for(const wrong of ['script://fixture/actors/man-p1/0000','script://other/scripts/man-p2/0000','script://fixture/scripts/man-p2/0001','script://fixture/scripts/man-p2/0']){
  const bad=structuredClone(baseline);bad.nodes[0].id=bad.asset_id=wrong;for(const edge of bad.incoming)edge.target_id=wrong;assert.throws(()=>decodeAssetReferences(bad,wrong,key));
}

// Trigger neighborhoods still retain their separate collision-table dependency.
const trigger=structuredClone(baseline);trigger.asset_id=trigger.incoming[0].source_id;trigger.outgoing=[trigger.incoming[0]];trigger.incoming=[];trigger.nodes=trigger.nodes.slice(0,2);
const collision='collision://fixture/field-map';trigger.nodes.push({id:collision,kind:'collision',scene_id:scene,label:'Source collision',available:true});
trigger.outgoing.push({id:'f'.repeat(64),source_id:trigger.asset_id,target_id:collision,kind:'field_map_table_source',scene_id:scene,layer:'decoded',runtime_binding:'not_asserted',source_import_sha256:key,source_catalog_key:catalogKey});
assert.deepEqual(decodeAssetReferences(trigger,trigger.asset_id,key).outgoing.map(edge=>edge.kind),['field_trigger_script_reference','field_map_table_source']);
const crossKind=structuredClone(trigger);crossKind.outgoing[1].trigger_reference_evidence=structuredClone(trigger.outgoing[0].trigger_reference_evidence);assert.throws(()=>decodeAssetReferences(crossKind,crossKind.asset_id,key));

const project=structuredClone(baseline),other='scene://other';project.schema_version='legaia.project-asset-references.v1';
for(const node of project.nodes){node.scene_ids=[scene];node.navigable_scene_ids=[scene];}
project.coverage={verified_scene_ids:[scene,other],resource_scene_id:scene,unresolved_reference_count:3,scenes:[{scene_id:scene,source_import_sha256:key,status:'available',resource_source_key:catalogKey,reason:null,limitations:[]},{scene_id:other,source_import_sha256:'e'.repeat(64),status:'available',resource_source_key:'f'.repeat(64),reason:null,limitations:[]}]};
const projectDecoded=decodeAssetReferences(project,scriptId,key,'project');assert.equal(projectDecoded.incoming.length,3);
assert.equal(assetReferenceNavigationNode(projectDecoded.nodes[1],projectDecoded.incoming[0],'project').scene_id,scene);
for(const mutation of [value=>value.incoming[0].source_import_sha256='e'.repeat(64),value=>value.incoming[0].source_catalog_key='f'.repeat(64),value=>value.nodes[1].scene_ids=[other],value=>value.nodes[0].scene_id=other]){const bad=structuredClone(project);mutation(bad);assert.throws(()=>decodeAssetReferences(bad,scriptId,key,'project'));}
console.log('Gate-1 primary/fallback/shared P2 source relationships, strict evidence, detached records and active/project navigation passed.');
