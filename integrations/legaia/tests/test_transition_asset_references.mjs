import assert from 'node:assert/strict';
import {decodeAssetReferences,assetReferenceNavigationNode,assetReferenceRelationLabel,assetReferenceTransitionEvidenceLabel} from '../editor/asset-references.js';

const sourceKey='a'.repeat(64),catalogKey='b'.repeat(64),recordHash='c'.repeat(64),nameHash='d'.repeat(64),scene='scene://fixture';
function report({partition=1,name='town02',extended=null}={}){
  const route=partition===1?'actors/man-p1':'scripts/man-p2',script=`script://fixture/${route}/0001`,transition=`transition://fixture/${route}/0001/0005`,destination=name===null?null:'scene://'+name;
  const proof={transition_id:script+'/transition/0005',source_record_sha256:recordHash,destination_scene_id:destination,extended_target:extended,name_sha256:nameHash,status:name===null?'unsupported_name_encoding':'encoded_named_reference',reachability:'not_evaluated'};
  const common={scene_id:scene,layer:'decoded',pc:5,runtime_binding:'not_asserted',source_import_sha256:sourceKey,source_catalog_key:catalogKey,transition_reference_evidence:proof};
  const nodes=[{id:script,kind:'script',scene_id:scene,label:'Source script',available:true},{id:transition,kind:'transition',scene_id:scene,label:'Encoded transition',available:true}];
  if(destination!==null)nodes.push({id:destination,kind:'scene',scene_id:destination,label:name,available:false});
  return {schema_version:'legaia.asset-references.v1',asset_id:transition,source_key:sourceKey,read_only:true,nodes,incoming:[{...structuredClone(common),id:'e'.repeat(64),source_id:script,target_id:transition,kind:'script_transition_reference'}],outgoing:destination===null?[]:[{...structuredClone(common),id:'f'.repeat(64),source_id:transition,target_id:destination,kind:'transition_destination_source'}],coverage:{verified_scene_ids:[scene],resource_scene_id:scene,unresolved_reference_count:name===null?1:0},limitations:['Encoded source instructions only; execution and gameplay reachability remain unresolved.']};
}
for(const options of [{},{partition:2,extended:255},{partition:1,extended:0},{partition:2,name:null,extended:7}]){
  const value=report(options),before=structuredClone(value),decoded=decodeAssetReferences(value,value.asset_id,sourceKey);
  decoded.incoming[0].transition_reference_evidence.source_record_sha256='1'.repeat(64);assert.deepEqual(value,before);
  assert.match(assetReferenceRelationLabel(value.incoming[0]),/source script instruction.*reachability not evaluated/);
  const label=assetReferenceTransitionEvidenceLabel(value.incoming[0]);assert.ok(label.includes(value.incoming[0].transition_reference_evidence.transition_id));assert.ok(label.includes(recordHash));assert.match(label,/gameplay connection are not established/);
  if(options.name===null)assert.match(label,/Destination name unresolved/);
}
const baseline=report();
for(const mutation of [
  value=>value.nodes[0].kind='actor',value=>value.nodes[1].kind='script',value=>value.nodes[1].scene_id='scene://foreign',value=>value.nodes[2].kind='transition',value=>value.nodes[2].scene_id=scene,
  value=>value.incoming[0].layer='authored',value=>value.incoming[0].runtime_binding='confirmed',value=>delete value.incoming[0].source_catalog_key,value=>value.incoming[0].source_import_sha256='bad',value=>value.incoming[0].source_catalog_key='bad',value=>value.incoming[0].pc=6,value=>value.incoming[0].pc=65536,value=>delete value.incoming[0].pc,value=>value.incoming[0].scene_id='scene://other',
  value=>value.incoming[0].kind='script_dialogue_segment',value=>value.outgoing[0].kind='encoded_scene_change',value=>delete value.incoming[0].transition_reference_evidence,
  value=>value.incoming[0].transition_reference_evidence.transition_id='script://fixture/actors/man-p1/0001/transition/0006',value=>value.incoming[0].transition_reference_evidence.transition_id=value.asset_id,value=>value.incoming[0].transition_reference_evidence.source_record_sha256='invalid',value=>value.incoming[0].transition_reference_evidence.name_sha256='invalid',value=>value.incoming[0].transition_reference_evidence.extended_target=256,value=>value.incoming[0].transition_reference_evidence.extended_target=false,value=>value.incoming[0].transition_reference_evidence.destination_scene_id='scene://Town02',value=>value.incoming[0].transition_reference_evidence.destination_scene_id=['scene://town02'],value=>value.incoming[0].transition_reference_evidence.destination_scene_id=null,value=>value.incoming[0].transition_reference_evidence.status='confirmed',value=>value.incoming[0].transition_reference_evidence.reachability='reachable',value=>value.incoming[0].transition_reference_evidence.trigger_position={x:0,z:0},value=>value.incoming[0].transition_reference_evidence.runtime_value=1,
  value=>value.outgoing[0].transition_reference_evidence.destination_scene_id='scene://town03',value=>value.outgoing[0].transition_reference_evidence.source_record_sha256='1'.repeat(64),value=>value.outgoing[0].transition_reference_evidence.name_sha256='1'.repeat(64),value=>value.outgoing[0].transition_reference_evidence.extended_target=2,value=>value.outgoing[0].source_import_sha256='1'.repeat(64),value=>value.outgoing[0].source_catalog_key='1'.repeat(64),value=>value.incoming.push({...structuredClone(value.incoming[0]),id:'2'.repeat(64)}),value=>value.outgoing.push({...structuredClone(value.outgoing[0]),id:'2'.repeat(64)}),value=>value.incoming[0].material_evidence={evidence:'extra assertion'}
]){const bad=structuredClone(baseline);mutation(bad);assert.throws(()=>decodeAssetReferences(bad,bad.asset_id,sourceKey));}
const unknown=report({name:null});unknown.incoming[0].transition_reference_evidence.status='encoded_named_reference';assert.throws(()=>decodeAssetReferences(unknown,unknown.asset_id,sourceKey));

// Script neighborhoods retain the established direct destination relationship.
const legacy=report(),script=legacy.nodes[0].id;legacy.asset_id=script;legacy.outgoing=[{...structuredClone(legacy.outgoing[0]),id:'3'.repeat(64),source_id:script,kind:'encoded_scene_change'},legacy.incoming[0]];delete legacy.outgoing[0].transition_reference_evidence;legacy.incoming=[];
assert.deepEqual(decodeAssetReferences(legacy,script,sourceKey).outgoing.map(edge=>edge.kind),['encoded_scene_change','script_transition_reference']);
const hiddenProof=structuredClone(legacy);hiddenProof.outgoing[0].transition_reference_evidence=structuredClone(baseline.incoming[0].transition_reference_evidence);assert.throws(()=>decodeAssetReferences(hiddenProof,script,sourceKey));

// The transition stays navigable in its source scene; destination navigation uses its own import.
const project=report({partition:2,extended:7}),destination='scene://town02',destinationHash='4'.repeat(64),destinationCatalog='5'.repeat(64);
project.schema_version='legaia.project-asset-references.v1';project.nodes[2].available=true;
for(const node of project.nodes){node.scene_ids=[node.scene_id];node.navigable_scene_ids=[node.scene_id];}
project.coverage={verified_scene_ids:[scene,destination],resource_scene_id:scene,unresolved_reference_count:0,scenes:[{scene_id:scene,source_import_sha256:sourceKey,status:'available',resource_source_key:catalogKey,reason:null,limitations:[]},{scene_id:destination,source_import_sha256:destinationHash,status:'available',resource_source_key:destinationCatalog,reason:null,limitations:[]}]};
const decoded=decodeAssetReferences(project,project.asset_id,sourceKey,'project');
assert.equal(assetReferenceNavigationNode(decoded.nodes[0],decoded.incoming[0],'project').scene_id,scene);assert.equal(assetReferenceNavigationNode(decoded.nodes[2],decoded.outgoing[0],'project').scene_id,destination);
for(const mutation of [value=>value.incoming[0].source_import_sha256=destinationHash,value=>value.outgoing[0].source_catalog_key=destinationCatalog,value=>value.nodes[1].scene_ids=[destination],value=>value.nodes[0].scene_id=destination,value=>value.outgoing[0].scene_id=destination]){const bad=structuredClone(project);mutation(bad);assert.throws(()=>decodeAssetReferences(bad,bad.asset_id,sourceKey,'project'));}
assert.throws(()=>decodeAssetReferences(project,project.asset_id,sourceKey));assert.equal(assetReferenceTransitionEvidenceLabel({kind:'scene_actor'}),null);
console.log('Transition reference source identities, named/unknown destinations, exact detached evidence, legacy edges and active/project navigation passed.');
