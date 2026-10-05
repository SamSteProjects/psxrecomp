import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const code=await readFile(new URL('../editor/asset-references.js',import.meta.url),'utf8');
const {decodeAssetReferences,assetReferenceNavigationNode,assetReferenceRelationLabel}=await import('data:text/javascript;base64,'+Buffer.from(code).toString('base64'));
const hash='a'.repeat(64),root='scene://fixture',actor=root+'/actors/0001';
const value={schema_version:'legaia.asset-references.v1',asset_id:root,source_key:hash,read_only:true,nodes:[{id:root,kind:'scene',scene_id:root,label:'Fixture',available:true},{id:actor,kind:'actor',scene_id:root,label:'Actor 0001',available:true}],incoming:[],outgoing:[{id:'b'.repeat(64),source_id:root,target_id:actor,kind:'scene_actor',scene_id:root,layer:'imported',runtime_binding:'not_asserted',source_import_sha256:hash}],coverage:{verified_scene_ids:[root],resource_scene_id:root,unresolved_reference_count:1},limitations:['Recorded source only']};
const result=decodeAssetReferences(value,root,hash);result.nodes[0].label='Detached';assert.equal(value.nodes[0].label,'Fixture');
for(const mutate of [v=>v.read_only=false,v=>v.source_key='c'.repeat(64),v=>v.nodes.push(v.nodes[0]),v=>v.outgoing[0].target_id='missing',v=>v.outgoing[0].runtime_binding='confirmed',v=>v.outgoing[0].layer='live',v=>v.outgoing[0].kind='inferred_model',v=>v.coverage.verified_scene_ids=[],v=>v.nodes[1].scene_id='scene://missing',v=>v.outgoing[0].pc=-1,v=>v.outgoing[0].layer='decoded']){const bad=structuredClone(value);mutate(bad);assert.throws(()=>decodeAssetReferences(bad,root,hash));}
console.log('asset reference decoder: bounded source contract, detached output and invalid records passed');
const material=structuredClone(value);material.asset_id='asset://model';material.nodes[0]={id:material.asset_id,kind:'model',scene_id:root,label:'Model',available:true};material.nodes[1]={id:'texture://fixture',kind:'texture',scene_id:root,label:'TIM',available:true};Object.assign(material.outgoing[0],{source_id:material.asset_id,target_id:'texture://fixture',kind:'static_material_texture_source',layer:'decoded',source_catalog_key:hash,material_evidence:{material_index:0,tpage:128,clut:0,uv_bounds:[0,0,1,1],model_source_sha256:hash,evidence:'static_vram_addresses_not_runtime_residency'}});decodeAssetReferences(material,material.asset_id,hash);
for(const mutate of [v=>v.outgoing[0].material_evidence.tpage=512,v=>v.outgoing[0].material_evidence.uv_bounds=[2,0,1,1],v=>v.outgoing[0].material_evidence.model_source_sha256='bad',v=>v.outgoing[0].material_evidence.evidence='live',v=>v.material_diagnostics={model_id:v.asset_id,materials:[{status:'confirmed'}]}]){const bad=structuredClone(material);mutate(bad);assert.throws(()=>decodeAssetReferences(bad,bad.asset_id,hash));}
const clip=structuredClone(value);clip.asset_id=actor;clip.nodes[0]={id:actor,kind:'actor',scene_id:root,label:'Actor',available:true};clip.nodes[1]={id:'animation://fixture/0',kind:'animation',scene_id:root,label:'Clip',available:true};Object.assign(clip.outgoing[0],{source_id:actor,target_id:'animation://fixture/0',kind:'effective_initial_animation_binding',layer:'effective',source_catalog_key:hash,effective_animation_evidence:{donor_entity_id:actor,model_id:'asset://fixture/0',initial_animation_id:2}});decodeAssetReferences(clip,actor,hash);
for(const mutate of [v=>v.outgoing[0].layer='live',v=>v.outgoing[0].effective_animation_evidence.initial_animation_id=0,v=>v.outgoing[0].effective_animation_evidence.model_id='',v=>v.outgoing[0].source_catalog_key='bad']){const bad=structuredClone(clip);mutate(bad);assert.throws(()=>decodeAssetReferences(bad,actor,hash));}

const other='scene://other',catalogKey='d'.repeat(64),otherHash='e'.repeat(64),otherCatalog='f'.repeat(64);
const project=structuredClone(material);project.schema_version='legaia.project-asset-references.v1';
project.coverage={verified_scene_ids:[root,other],resource_scene_id:root,unresolved_reference_count:0,scenes:[{scene_id:root,source_import_sha256:hash,status:'available',resource_source_key:catalogKey,reason:null,limitations:[]},{scene_id:other,source_import_sha256:otherHash,status:'available',resource_source_key:otherCatalog,reason:null}]};
for(const node of project.nodes){node.scene_ids=[root,other];node.navigable_scene_ids=[root,other];}
project.outgoing[0].source_catalog_key=catalogKey;
project.outgoing.push({...structuredClone(project.outgoing[0]),id:'1'.repeat(64),scene_id:other,source_import_sha256:otherHash,source_catalog_key:otherCatalog});
const shared=decodeAssetReferences(project,project.asset_id,hash,'project');assert.deepEqual(shared.nodes[1].scene_ids,[root,other]);shared.nodes[1].scene_ids.pop();assert.equal(project.nodes[1].scene_ids.length,2);
assert.throws(()=>decodeAssetReferences(project,project.asset_id,hash));assert.throws(()=>decodeAssetReferences(value,root,hash,'project'));assert.throws(()=>decodeAssetReferences(value,root,hash,'all'));
for(const mutate of [v=>v.source_key='0'.repeat(64),v=>v.coverage.scenes.reverse(),v=>v.coverage.scenes.pop(),v=>v.coverage.scenes[0].source_import_sha256='bad',v=>v.coverage.scenes[0].resource_source_key='bad',v=>v.coverage.scenes[0].reason='unexpected',v=>v.coverage.scenes[0].status='partial',v=>v.coverage.scenes[0].limitations='invalid',v=>v.nodes[0].scene_ids.reverse(),v=>v.nodes[0].scene_ids.push(root),v=>v.nodes[0].scene_ids=[],v=>v.nodes[0].scene_id='scene://unknown',v=>v.nodes[0].scene_ids=[root,'scene://unknown'],v=>v.outgoing[1].source_import_sha256=hash,v=>v.outgoing[1].source_catalog_key=catalogKey,v=>v.nodes[0].scene_ids=[root],v=>{v.coverage.scenes[1].status='unavailable';v.coverage.scenes[1].reason='Unavailable decoder';v.coverage.scenes[1].resource_source_key=null;}]){const bad=structuredClone(project);mutate(bad);assert.throws(()=>decodeAssetReferences(bad,bad.asset_id,hash,'project'));}
// Imported membership remains navigable when only its derived resource catalog is unavailable.
const partial=structuredClone(value);partial.schema_version='legaia.project-asset-references.v1';for(const node of partial.nodes){node.scene_ids=[root];node.navigable_scene_ids=[root];}partial.coverage.scenes=[{scene_id:root,source_import_sha256:hash,status:'unavailable',resource_source_key:null,reason:'Resource decoder unavailable'}];decodeAssetReferences(partial,root,hash,'project');
for(const mutate of [v=>v.coverage.scenes[0].reason='',v=>v.coverage.scenes[0].resource_source_key=hash,v=>v.outgoing[0].source_import_sha256=otherHash]){const bad=structuredClone(partial);mutate(bad);assert.throws(()=>decodeAssetReferences(bad,root,hash,'project'));}
const external=structuredClone(partial);external.nodes[1]={id:'scene://external',kind:'scene',scene_id:'scene://external',scene_ids:['scene://external'],navigable_scene_ids:[],label:'External scene',available:false};external.outgoing[0].target_id='scene://external';external.outgoing[0].kind='encoded_scene_change';external.outgoing[0].layer='imported';decodeAssetReferences(external,root,hash,'project');
console.log('project asset reference decoder: shared membership, per-scene provenance, partial coverage and stale/scope rejection passed');

const sharedPartial=structuredClone(project);sharedPartial.nodes[1].navigable_scene_ids=[other];sharedPartial.nodes[1].scene_id=other;decodeAssetReferences(sharedPartial,sharedPartial.asset_id,hash,'project');
assert.equal(sharedPartial.nodes[1].scene_ids.includes(root),true);assert.equal(sharedPartial.nodes[1].navigable_scene_ids.includes(root),false);
for(const mutate of [v=>v.nodes[1].navigable_scene_ids=[],v=>v.nodes[1].navigable_scene_ids=[other,root],v=>v.nodes[1].navigable_scene_ids=[other,other],v=>v.nodes[1].navigable_scene_ids=['scene://unknown'],v=>v.nodes[1].scene_id=root,v=>v.nodes[1].available=false,v=>delete v.nodes[1].navigable_scene_ids]){const bad=structuredClone(sharedPartial);mutate(bad);assert.throws(()=>decodeAssetReferences(bad,bad.asset_id,hash,'project'));}
console.log('project asset reference navigation: membership does not imply local catalog availability');

assert.equal(assetReferenceNavigationNode(sharedPartial.nodes[1],sharedPartial.outgoing[0],'project').scene_id,other);
assert.equal(assetReferenceNavigationNode(sharedPartial.nodes[1],sharedPartial.outgoing[1],'project').scene_id,other);
assert.equal(assetReferenceNavigationNode(project.nodes[1],project.outgoing[1],'project').scene_id,other);
assert.equal(assetReferenceNavigationNode(project.nodes[1],project.outgoing[1]).scene_id,root);

const referenceCommit='d6e64c68ede25813d35db20980da82a1a025549b';
function pinnedClip(slot,clipId){
  const model=`asset://legaia/models/global-special/${(0xf0+slot).toString(16).padStart(4,'0')}`,index=slot<3?slot*7+(clipId==='idle'?1:0):slot+18;
  const animation=`animation://legaia/field-locomotion/${String(index).padStart(4,'0')}`,channels=slot<3?10:slot===3?3:2,frames=12,length=16+frames*channels*8;
  const evidence={reference_commit:referenceCommit,model_id:model,clip_id:clipId,record_index:index,frame_count:frames,channel_count:channels,source_record:{disc:{sha256:hash,serial:'SCUS-94254'},iso_file:'PROT.DAT',prot_entry_index:874,container_section:1,compressed_stream_offset:4096,compressed_bytes_consumed:2048,record_index:index,byte_offset:96,byte_length:length,byte_coordinate_space:'decoded_lzs_section',containing_size:96+length+32}};
  return {...structuredClone(value),asset_id:animation,nodes:[{id:animation,kind:'animation',scene_id:root,label:'Reference clip',available:true},{id:model,kind:'model',scene_id:root,label:'Pinned model',available:true}],outgoing:[{id:'2'.repeat(64),source_id:animation,target_id:model,kind:'reference_pinned_model_clip',scene_id:root,layer:'decoded',runtime_binding:'not_asserted',source_import_sha256:hash,source_catalog_key:hash,reference_clip_evidence:evidence}]};
}
for(const [slot,clipIds] of [[0,['idle','walk']],[1,['idle','walk']],[2,['idle','walk']],[3,['loop']],[4,['loop']]])for(const clipId of clipIds){
  const reference=pinnedClip(slot,clipId),decoded=decodeAssetReferences(reference,reference.asset_id,hash);
  assert.equal(assetReferenceRelationLabel(decoded.outgoing[0]),`pinned model/clip association · clip ${clipId} · actor playback unknown`);
  decoded.outgoing[0].reference_clip_evidence.source_record.disc.sha256='3'.repeat(64);assert.equal(reference.outgoing[0].reference_clip_evidence.source_record.disc.sha256,hash);
  const modelRoot=structuredClone(reference);modelRoot.asset_id=modelRoot.nodes[1].id;modelRoot.incoming=modelRoot.outgoing;modelRoot.outgoing=[];decodeAssetReferences(modelRoot,modelRoot.asset_id,hash);
}
const pinned=pinnedClip(3,'loop');
const malformedPinned=[
  v=>v.outgoing[0].runtime_binding='confirmed',v=>v.outgoing[0].layer='effective',v=>v.outgoing[0].kind='initial_animation_binding',
  v=>v.nodes[0].kind='actor',v=>v.nodes[1].kind='actor',v=>v.outgoing[0].pc=123,v=>v.outgoing[0].effective_animation_evidence={initial_animation_id:1},
  v=>v.outgoing[0].reference_clip_evidence.reference_commit='0'.repeat(40),v=>v.outgoing[0].reference_clip_evidence.model_id='asset://other',
  v=>v.outgoing[0].reference_clip_evidence.clip_id='idle',v=>v.outgoing[0].reference_clip_evidence.record_index=22,
  v=>v.outgoing[0].reference_clip_evidence.channel_count=10,v=>v.outgoing[0].reference_clip_evidence.frame_count=true,
  v=>{const e=v.outgoing[0].reference_clip_evidence;e.frame_count=513;e.source_record.byte_length=16+513*3*8;e.source_record.containing_size=96+e.source_record.byte_length;},
  v=>v.outgoing[0].reference_clip_evidence.actor_semantic_id=actor,v=>delete v.outgoing[0].reference_clip_evidence.channel_count,
  v=>v.outgoing[0].reference_clip_evidence.source_record.disc.sha256='BAD',v=>v.outgoing[0].reference_clip_evidence.source_record.disc.serial='SLUS-00000',
  v=>v.outgoing[0].reference_clip_evidence.source_record.disc.live=true,v=>v.outgoing[0].reference_clip_evidence.source_record.iso_file='OTHER.DAT',
  v=>v.outgoing[0].reference_clip_evidence.source_record.container_section=0,v=>v.outgoing[0].reference_clip_evidence.source_record.prot_entry_index=873,
  v=>v.outgoing[0].reference_clip_evidence.source_record.record_index=22,v=>v.outgoing[0].reference_clip_evidence.source_record.byte_coordinate_space='compressed_stream',
  v=>v.outgoing[0].reference_clip_evidence.source_record.byte_offset=95,v=>v.outgoing[0].reference_clip_evidence.source_record.byte_length++,
  v=>{const s=v.outgoing[0].reference_clip_evidence.source_record;s.byte_offset=s.containing_size-s.byte_length+1;},
  v=>v.outgoing[0].reference_clip_evidence.source_record.containing_size=4*1024*1024+1,
  v=>v.outgoing[0].reference_clip_evidence.source_record.compressed_stream_offset=-1,v=>v.outgoing[0].reference_clip_evidence.source_record.compressed_bytes_consumed=0,
  v=>{const s=v.outgoing[0].reference_clip_evidence.source_record;s.compressed_stream_offset=0xffffffff;s.compressed_bytes_consumed=1;},
  v=>v.outgoing[0].reference_clip_evidence.source_record.byte_payload=[]
];
for(const mutate of malformedPinned){const invalid=structuredClone(pinned);mutate(invalid);assert.throws(()=>decodeAssetReferences(invalid,invalid.asset_id,hash));}
// Re-keying a clip or both model endpoints cannot disguise a different pinned association.
for(const target of ['animation','model']){const invalid=structuredClone(pinned),edge=invalid.outgoing[0];if(target==='animation'){invalid.asset_id='animation://legaia/field-locomotion/0022';invalid.nodes[0].id=invalid.asset_id;edge.source_id=invalid.asset_id;}else{invalid.nodes[1].id='asset://legaia/models/global-special/00f4';edge.target_id=invalid.nodes[1].id;edge.reference_clip_evidence.model_id=edge.target_id;}assert.throws(()=>decodeAssetReferences(invalid,invalid.asset_id,hash));}
const largeContainer=structuredClone(pinned);largeContainer.outgoing[0].reference_clip_evidence.source_record.compressed_stream_offset=5*1024*1024;decodeAssetReferences(largeContainer,largeContainer.asset_id,hash);
const projectPinned=structuredClone(pinned);projectPinned.schema_version='legaia.project-asset-references.v1';projectPinned.coverage=structuredClone(project.coverage);
for(const node of projectPinned.nodes){node.scene_ids=[root,other];node.navigable_scene_ids=[root,other];}
projectPinned.outgoing[0].source_catalog_key=catalogKey;projectPinned.outgoing.push({...structuredClone(projectPinned.outgoing[0]),id:'4'.repeat(64),scene_id:other,source_import_sha256:otherHash,source_catalog_key:otherCatalog});
const projectClip=decodeAssetReferences(projectPinned,projectPinned.asset_id,hash,'project');assert.equal(projectClip.outgoing.length,2);assert.equal(assetReferenceNavigationNode(projectClip.nodes[1],projectClip.outgoing[1],'project').scene_id,other);
assert.throws(()=>decodeAssetReferences({...pinned,schema_version:'legaia.asset-references.v2'},pinned.asset_id,hash));
console.log('pinned model/clip references: eight exact associations, source bounds, detached provenance, project navigation and actor/live rejection passed');

const currentMaterial=structuredClone(material);currentMaterial.outgoing[0].kind='effective_material_texture_source';currentMaterial.outgoing[0].layer='effective';Object.assign(currentMaterial.outgoing[0].material_evidence,{model_current_sha256:'b'.repeat(64),authored_materials_sha256:'c'.repeat(64)});decodeAssetReferences(currentMaterial,currentMaterial.asset_id,hash);
for(const mutate of [v=>v.outgoing[0].layer='decoded',v=>v.outgoing[0].source_catalog_key='bad',v=>v.outgoing[0].material_evidence.model_current_sha256='bad',v=>v.outgoing[0].material_evidence.authored_materials_sha256='bad',v=>v.outgoing[0].material_evidence.extra=true]){const bad=structuredClone(currentMaterial);mutate(bad);assert.throws(()=>decodeAssetReferences(bad,bad.asset_id,hash));}
console.log('Current material references: qualified layer, source/binding/native hashes and strict evidence passed.');

const diagnosed=structuredClone(currentMaterial);diagnosed.current_material_diagnostics={model_id:diagnosed.asset_id,retail_sha256:hash,source_sha256:'b'.repeat(64),materials:[{material_index:0,status:'address_match',source_ids:['texture://fixture']}]};decodeAssetReferences(diagnosed,diagnosed.asset_id,hash);for(const change of [{source_sha256:'d'.repeat(64)},{retail_sha256:'d'.repeat(64)},{materials:[{material_index:0,status:'confirmed',source_ids:[]}]}])assert.throws(()=>decodeAssetReferences({...diagnosed,current_material_diagnostics:{...diagnosed.current_material_diagnostics,...change}},diagnosed.asset_id,hash));
