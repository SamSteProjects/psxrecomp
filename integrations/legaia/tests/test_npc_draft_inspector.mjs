import assert from 'node:assert/strict';
import {npcAnimationSceneTarget,npcDonorAnimationBinding,renderNpcDraftInspector} from '../editor/npc-draft-inspector.js';
const property=(id,path,state)=>({id,label:id,path,type:'string',state}),schema={schema_version:'legaia.inspector-schema.v1',live_writes:false,property_states:{'read-only-project':{label:'Project',note:'Metadata'},'authored-through-command':{label:'Authored',note:'Command'},derived:{label:'Derived',note:'Source sample'},unresolved:{label:'Unresolved',note:'Unknown'}},components:{
 NpcDraftIdentity:{label:'NPC draft identity',layout:'read-only-properties',properties:[property('identity',['entity_id'],'read-only-project')],details:[{label:'Donor',path:['donor']}]},
 NpcDraftTransform:{label:'Authored placement',layout:'read-only-properties',properties:[property('X',['draft','position','x'],'authored-through-command')]},
 NpcDraftPreview:{label:'Preview snapshot',layout:'read-only-properties',properties:[property('X',['preview','position','x'],'derived'),property('Y',['preview','position','y'],'unresolved'),property('Surface Y',['preview','preview_position','y'],'derived')]}}};
const snapshot={entity_id:'authored-actor://fixture',draft:{position:{x:128,z:256}},donor:{source:'<retail>'},preview:{position:{x:192,y:null,z:256},preview_position:{x:192,y:12,z:256}}},before=structuredClone(snapshot),html=renderNpcDraftInspector(schema,snapshot,'current');
for(const id of Object.keys(schema.components))assert(html.includes(`data-npc-draft-component="${id}"`));assert(html.includes('<code>128</code>'));assert(html.includes('<code>192</code>'));assert(html.includes('<code>12</code>'));assert(html.includes('<code>—</code>'));assert(html.includes('&lt;retail&gt;'));assert(!html.includes('<input'));assert.deepEqual(snapshot,before);
for(const id of Object.keys(schema.components))assert(html.includes(`data-inspector-component-section="${id}"`));assert(!html.includes('data-inspector-action'));
assert(renderNpcDraftInspector(schema,snapshot,'pending').includes('refresh pending'));assert(renderNpcDraftInspector(schema,snapshot,'source-during-proposal').includes('Proposed viewport coordinates are not substituted'));
const missing=renderNpcDraftInspector(schema,{...snapshot,preview:undefined},'unavailable');assert(missing.includes('No NPC draft preview snapshot'));assert.equal((missing.match(/<code>128<\/code>/g)??[]).length,1);assert(!missing.includes('<code>192</code>'));assert(!missing.includes('<code>12</code>'));
assert.throws(()=>renderNpcDraftInspector(schema,snapshot,'proposal'));assert.throws(()=>renderNpcDraftInspector({...schema,components:{...schema.components,NpcDraftTransform:{...schema.components.NpcDraftTransform,properties:[{id:'X',authoring:{}}]}}},snapshot,'current'));
console.log('SDK NPC draft sections, authored/source preview separation, unknowns, safe details and pending/proposal labels passed.');

const id='authored-actor://00000000-0000-4000-8000-000000000001',donorId='scene://town01/actors/man-p1/0001',modelId='asset://town01/models/0';
const animationState={scene:{id:'scene://town01'},actor_drafts:{[id]:{scene_id:'scene://town01',donor_entity_id:donorId,name:'NPC'}},authored_assets:[{id,kind:'actor',draft:true,scene_id:'scene://town01',donor_entity_id:donorId,name:'NPC',model_reference:{source_id:id,source_name:'NPC',target_id:modelId,scene_id:'scene://town01',kind:'draft_initial_model_assignment',imported:false,effective:true,effective_donor_id:donorId,runtime_binding:'not_asserted'}}],entities:[{id:donorId,components:{ModelRenderer:{asset_id:'asset://authored-appearance/other'}}}]};
const animationPreview={entity_id:id,kind:'actor_draft',donor_entity_id:donorId,asset_id:modelId,pose_kind:'imported_scene_animation_frame0'};
assert.deepEqual(npcDonorAnimationBinding(animationState,id,animationPreview),{assetId:modelId,entityId:donorId,clipId:'scene-header',representation:'imported'});
assert.equal(npcDonorAnimationBinding(animationState,id,{...animationPreview,pose_kind:'authored_scene_animation_frame0'}).clipId,'authored-channels');
assert.equal(npcDonorAnimationBinding(animationState,id,{...animationPreview,pose_kind:'reference_party_idle'}),null);
assert.throws(()=>npcDonorAnimationBinding(animationState,id,{...animationPreview,asset_id:'asset://authored-appearance/other'}));
assert.throws(()=>npcDonorAnimationBinding(animationState,id,{...animationPreview,donor_entity_id:'other'}));
console.log('NPC animation binding follows retail donor model, preserves shared authored channel representation and rejects mismatched snapshots.');

animationState.actor_drafts[id].position={x:128,z:256};animationState.scene_preview_source_key='a'.repeat(64);
const targetScene={scene_id:'scene://town01',source_key:animationState.scene_preview_source_key,entities:[{...animationPreview,authored_position:{x:128,z:256}}]},posePreview={semantic_id:modelId};
assert.equal(npcAnimationSceneTarget(animationState,targetScene,posePreview,donorId,id),id);
assert.equal(npcAnimationSceneTarget(animationState,targetScene,posePreview,null,id),id);
for(const edit of [v=>v.source_key='stale',v=>v.entities[0].asset_id='other',v=>v.entities[0].donor_entity_id='other',v=>v.entities[0].authored_position.x=64,v=>v.entities.push(structuredClone(v.entities[0]))]){const bad=structuredClone(targetScene);edit(bad);assert.throws(()=>npcAnimationSceneTarget(animationState,bad,posePreview,donorId,id));}
assert.throws(()=>npcAnimationSceneTarget(animationState,targetScene,{semantic_id:'other'},donorId,id));
assert.throws(()=>npcAnimationSceneTarget(animationState,targetScene,posePreview,'other',id));
console.log('NPC animation scene targeting retains authored placement and qualifies source, model, donor and unique entity binding.');
