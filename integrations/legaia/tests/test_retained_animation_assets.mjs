import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const code=await readFile(new URL('../editor/retained-animation-assets.js',import.meta.url),'utf8');
const {decodeRetainedAnimationAsset,qualifyRetainedAnimationPreview,retainedAnimationEditContext,retainedAnimationAssignmentContext,retainedAnimationAssignmentTargets,retainedAnimationAssignedActors,retainedAnimationAssignedTarget,openRetainedAnimationAsset}=await import('data:text/javascript;base64,'+Buffer.from(code).toString('base64'));
const uuid='12345678-1234-4123-8123-123456789abc',id=`animation://fixture/authored-record/${uuid}`,actor='scene://fixture/actors/man-p1/0001',model='asset://legaia/models/global-special/00f0',hash='a'.repeat(64);
const row={record_id:uuid,animation_id:id,entity_id:actor,channel_owner_entity_id:actor,model_source_entity_id:actor,donor_asset_id:model,donor_animation_id:'animation://fixture/scene-anm/0001',record_sha256:hash,frame_count:2,object_count:1,active:false,runtime_assigned:false,assigned_actor_ids:[]};
const value={semantic_id:id,asset_kind:'animation',scope:'authored-retained',authored_animation_record:true,frame_count:2,bone_count:1,model_asset_id:model,retained_record:row,source_record:{source_kind:'authored_animation_record',record_id:uuid,record_sha256:hash,ledger_sha256:hash,donor_record_sha256:hash,donor_animation_id:row.donor_animation_id}};
const decoded=decodeRetainedAnimationAsset({id,data:value});decoded.retained_record.entity_id='changed';assert.equal(value.retained_record.entity_id,actor);
for(const mutate of [v=>v.semantic_id+='bad',v=>v.scope='global-field',v=>v.frame_count=3,v=>v.retained_record.object_count=65,v=>v.retained_record.assigned_actor_ids=[actor],v=>v.retained_record.entity_id='scene://other/actors/man-p1/0001',v=>v.retained_record.donor_animation_id='animation://other/scene-anm/0001',v=>v.retained_record.extra=true,v=>v.source_record.record_sha256='bad',v=>v.source_record.ledger_sha256='bad',v=>v.source_record.donor_record_sha256='bad',v=>v.source_record.extra=true]){const bad=structuredClone(value);mutate(bad);assert.throws(()=>decodeRetainedAnimationAsset(bad));}
const preview={semantic_id:model,vertices:[[0,0,0]],animation:{semantic_id:id,asset_semantic_id:model,frame_count:2,bone_count:1,representation:'allocated_record',asset_source:value,source_record:{record_sha256:hash}},frames:[{frame_index:0,vertices:[[0,0,0]]},{frame_index:1,vertices:[[1,0,0]]}]};qualifyRetainedAnimationPreview(preview,value);
for(const mutate of [v=>v.animation.semantic_id+='bad',v=>v.animation.representation='live',v=>v.frames.pop(),v=>v.animation.asset_source.retained_record.active=true,v=>v.animation.asset_source.model_asset_id='asset://wrong',v=>v.semantic_id='asset://wrong',v=>v.frames[1].frame_index=2,v=>v.frames[1].vertices=[],v=>v.frames[1].vertices[0][0]=Infinity,v=>v.animation.source_record.record_sha256='bad']){const bad=structuredClone(preview);mutate(bad);assert.throws(()=>qualifyRetainedAnimationPreview(bad,value));}
const active=structuredClone(value);active.retained_record.active=true;active.retained_record.assigned_actor_ids=[actor];decodeRetainedAnimationAsset(active);
console.log('Retained AssetDB metadata: stable source/scene/model identities, active/retired assignments, exact hashes/counts, detached output and preview source guards passed.');
const {decodeAssetReferences}=await import('../editor/asset-references.js');
const scene='scene://fixture',proof={...value.source_record,model_id:model,channel_owner_entity_id:actor,model_source_entity_id:actor,frame_count:2,object_count:1,active:false};
const graph={schema_version:'legaia.asset-references.v1',asset_id:id,source_key:hash,read_only:true,nodes:[{id,kind:'animation',scene_id:scene,label:'Retained clip',available:true},{id:model,kind:'model',scene_id:scene,label:'Model',available:true}],incoming:[],outgoing:[{id:'b'.repeat(64),source_id:id,target_id:model,kind:'retained_model_capture',scene_id:scene,layer:'authored',runtime_binding:'not_asserted',source_import_sha256:hash,source_catalog_key:hash,retained_capture_evidence:proof}],coverage:{verified_scene_ids:[scene],resource_scene_id:scene,unresolved_reference_count:0},limitations:['Captured source only']};
decodeAssetReferences(graph,id,hash);
for(const mutate of [v=>v.outgoing[0].retained_capture_evidence.active='yes',v=>v.outgoing[0].retained_capture_evidence.frame_count=513,v=>v.outgoing[0].retained_capture_evidence.object_count=65,v=>v.outgoing[0].retained_capture_evidence.donor_record_sha256='bad',v=>v.outgoing[0].retained_capture_evidence.native_animation_id=1,v=>v.outgoing[0].layer='decoded',v=>v.outgoing[0].kind='recorded_model_clip_binding']){const bad=structuredClone(graph);mutate(bad);assert.throws(()=>decodeAssetReferences(bad,id,hash));}
console.log('Retained capture references: active/retired source witnesses and layers are qualified without asserting a native slot or runtime binding.');
const state={project:{mode:'edit'},scene:{id:scene},capabilities:{actor_animation_authoring:true},scene_preview_source_key:hash};
const edit=retainedAnimationEditContext(value,state);assert.equal(edit.assetId,id);assert.equal(edit.entityId,actor);assert.equal(edit.row.active,false);assert.equal(Object.hasOwn(edit.row,'assigned_actor_ids'),false);edit.row.record_sha256='bad';assert.equal(value.retained_record.record_sha256,hash);
for(const change of [s=>s.project.mode='live',s=>s.capabilities.actor_animation_authoring=false,s=>s.scene.id='scene://other',s=>s.scene_preview_source_key='bad']){const bad=structuredClone(state);change(bad);assert.throws(()=>retainedAnimationEditContext(value,bad));}
console.log('Direct retained asset editing: detached legacy row, captured owner, active scene/Edit/capability/source guards and retired eligibility passed.');
// Exercise the actual Asset Inspector action with a minimal DOM; native browser
// evidence covers the full existing GLB editor, download and Apply workflow.
class Element{
 constructor(tag){this.tag=tag;this.children=[];this.open=false;this.listeners={};}
 append(child){this.children.push(child);}
 replaceChildren(){this.children=[];}
 setAttribute(){}
 addEventListener(name,callback){this.listeners[name]=callback;}
 showModal(){this.open=true;}
 close(){this.open=false;this.listeners.close?.();}
 remove(){this.removed=true;}
}
globalThis.document={createElement:tag=>new Element(tag),body:new Element('body')};
const find=(node,text)=>node.textContent===text?node:node.children.map(c=>find(c,text)).find(Boolean);
let current={...structuredClone(state),project:{mode:'edit',path:'fixture'}},pending=false,result=null,errors=[];
const options={record:{id,data:value},getState:()=>current,busy:()=>pending,onGlb:context=>{result=context;},onError:e=>errors.push(e.message)};
let dialog=openRetainedAnimationAsset(options);let action=find(dialog,'Edit retained GLB');assert.equal(action.hidden,false);
pending=true;await action.onclick();assert.equal(result,null);assert.equal(dialog.open,true);assert.match(errors.pop(),/current operation/);
pending=false;current.scene_preview_source_key='b'.repeat(64);await action.onclick();assert.equal(result,null);assert.match(errors.pop(),/source changed/);dialog.close();
current=structuredClone({...state,project:{mode:'edit',path:'fixture'}});dialog=openRetainedAnimationAsset(options);await find(dialog,'Edit retained GLB').onclick();
assert.equal(dialog.removed,true);assert.equal(result.assetId,id);assert.equal(result.row.active,false);assert.equal(Object.hasOwn(result.row,'assigned_actor_ids'),false);assert.deepEqual(errors,[]);
current.project.mode='live';dialog=openRetainedAnimationAsset(options);action=find(dialog,'Edit retained GLB');assert.equal(action.hidden,true);result=null;await action.onclick();assert.equal(result,null);assert.match(errors.pop(),/Edit mode/);dialog.close();
current.project.mode='edit';current.capabilities.actor_animation_authoring=false;dialog=openRetainedAnimationAsset(options);assert.equal(find(dialog,'Edit retained GLB').hidden,true);dialog.close();
console.log('Retained asset GLB action: guarded detached capture handoff, close/disposal, busy/stale rejection and Live/capability visibility passed.');
current=structuredClone({...state,project:{mode:'edit',path:'fixture'}});result=null;
dialog=openRetainedAnimationAsset({...options,onLifecycle:context=>{result=context;}});
await find(dialog,'Manage retained lifecycle').onclick();assert.equal(dialog.removed,true);assert.equal(result.assetId,id);assert.equal(result.row.record_id,uuid);assert.equal(result.row.active,false);
dialog=openRetainedAnimationAsset(options);assert.equal(find(dialog,'Manage retained lifecycle').hidden,true);dialog.close();
console.log('Retained asset lifecycle action reuses the qualified captured-record handoff.');
current.capabilities.actor_animation_assignment=true;const target=actor.replace('0001','0002');current.scene.entities=[{id:target,name:'Compatible actor',components:{ActorAppearance:{effective:{asset_id:model}}}}];
assert.equal(retainedAnimationAssignmentContext(active,current,target).targetEntityId,target);
assert.throws(()=>retainedAnimationAssignmentContext(value,current,target),/active retained clip/);
for(const invalid of [null,'scene://other/actors/man-p1/0002','npc://fixture/0002'])assert.throws(()=>retainedAnimationAssignmentContext(active,current,invalid),/Choose a compatible imported actor/);
result=null;dialog=openRetainedAnimationAsset({...options,record:{id,data:active},onAssign:context=>{result=context;},getAssignmentTarget:()=>target});await find(dialog,'Review assignment to actor').onclick();assert.equal(result.targetEntityId,target);assert.equal(result.entityId,actor);assert.equal(dialog.removed,true);
dialog=openRetainedAnimationAsset({...options,onAssign:()=>{}});assert.equal(find(dialog,'Review assignment to actor').hidden,true);dialog.close();
current.capabilities.actor_animation_assignment=false;assert.throws(()=>retainedAnimationAssignmentContext(active,current,target),/assignment capability/);
console.log('Retained asset assignment: explicit distinct target, active clip, scene and capability guards passed.');

const actorState=structuredClone(current);actorState.scene.entities=[{id:actor,name:'Actor 0001',components:{ActorAllocatedAnimation:{authored:{scene_id:scene,record_id:uuid,record_sha256:hash,model_asset_id:model}},ActorAnimation:{effective:{animation_asset_id:id,source_kind:'allocated_record',record_id:uuid}}}}];
assert.deepEqual(retainedAnimationAssignedActors(active,actorState),[{id:actor,label:'Actor 0001'}]);assert.equal(retainedAnimationAssignedTarget(active,actorState,actor),actor);assert.throws(()=>retainedAnimationAssignedTarget(active,actorState,target));
for(const mutate of [s=>s.scene.entities=[],s=>s.scene.entities.push(structuredClone(s.scene.entities[0])),s=>s.scene.entities[0].components.ActorAllocatedAnimation.authored.record_sha256='b'.repeat(64),s=>s.scene.entities[0].components.ActorAllocatedAnimation.authored.model_asset_id='asset://other',s=>s.scene.entities[0].components.ActorAnimation.effective.animation_asset_id='animation://other',s=>s.scene.id='scene://other']){const bad=structuredClone(actorState);mutate(bad);assert.throws(()=>retainedAnimationAssignedActors(active,bad));}
assert.throws(()=>retainedAnimationAssignedActors(value,actorState),/differ/);
current=actorState;result=null;dialog=openRetainedAnimationAsset({...options,record:{id,data:active},onActor:target=>{result=target;}});action=find(dialog,'Select assigned actor');assert.equal(action.disabled,false);pending=true;await action.onclick();assert.equal(result,null);assert.match(errors.pop(),/current operation/);pending=false;current.scene.entities[0].components.ActorAllocatedAnimation.authored.record_sha256='b'.repeat(64);await action.onclick();assert.equal(result,null);assert.match(errors.pop(),/differ/);dialog.close();
current=structuredClone(actorState);current.scene.entities[0].components.ActorAllocatedAnimation.authored.record_sha256=hash;dialog=openRetainedAnimationAsset({...options,record:{id,data:active},onActor:target=>{result=target;}});await find(dialog,'Select assigned actor').onclick();assert.equal(result,actor);assert.equal(dialog.removed,true);assert.deepEqual(errors,[]);
console.log('Retained assignment user navigation: complete current authored/effective witnesses, duplicate/missing/forged users, busy/stale guards and readonly actor handoff passed.');

current=structuredClone({...state,project:{mode:'edit',path:'fixture'},capabilities:{actor_animation_authoring:true,actor_animation_assignment:true}});
current.scene.entities=[{id:actor,name:'Capture',components:{ActorAppearance:{effective:{asset_id:model}}}},{id:target,name:'<script>Target</script>',components:{ActorAppearance:{effective:{asset_id:model}}}},{id:actor.replace('0001','0003'),components:{ActorAppearance:{effective:{asset_id:'asset://other'}}}}];
current.scene.entities.push({id:'npc://fixture/draft',components:{ActorAppearance:{effective:{asset_id:model}}}});
assert.deepEqual(retainedAnimationAssignmentTargets(active,current).map(row=>row.id),[actor,target]);
for(const mutate of [s=>s.scene.entities.push(structuredClone(s.scene.entities[0])),s=>s.scene.entities=null,s=>s.project.mode='live',s=>s.scene.id='scene://other']){const bad=structuredClone(current);mutate(bad);assert.throws(()=>retainedAnimationAssignmentTargets(active,bad));}
const collect=(node,tag)=>[...(node.tag===tag?[node]:[]),...node.children.flatMap(child=>collect(child,tag))];
result=null;dialog=openRetainedAnimationAsset({...options,record:{id,data:active},onAssign:context=>{result=context;}});
const picker=collect(dialog,'select')[0];action=find(dialog,'Review assignment to actor');assert.equal(picker.value,'');assert.equal(action.disabled,true);
picker.value=target;picker.onchange();assert.equal(action.disabled,false);await action.onclick();assert.equal(result.targetEntityId,target);assert.equal(dialog.removed,true);
result=null;dialog=openRetainedAnimationAsset({...options,record:{id,data:active},onAssign:context=>{result=context;},getAssignmentTarget:()=>target});
const stalePicker=collect(dialog,'select')[0];assert.equal(stalePicker.value,target);current.scene.entities[1].components.ActorAppearance.effective.asset_id='asset://other';await find(dialog,'Review assignment to actor').onclick();assert.equal(result,null);assert.match(errors.pop(),/compatible imported actor/);stalePicker.onchange();assert.equal(stalePicker.value,'');assert.equal(find(dialog,'Review assignment to actor').disabled,true);dialog.close();
console.log('Compatible assignment picker: exact effective model, explicit choice, independent hierarchy target, missing target refusal, duplicate/source/mode guards passed.');

// A successful label change closes the old inspector before handing off the same identity.
const nameState=()=>({...structuredClone(state),project:{mode:'edit',path:'fixture'},animation_labels:{},animation_labels_key:hash});
current=nameState();let namedRequest=null,handoffs=[];
dialog=openRetainedAnimationAsset({...options,onName:async request=>{namedRequest=request;current={...current,animation_labels:{[id]:{name:request.name}},animation_labels_key:'b'.repeat(64)};return true;},onNameApplied:request=>{assert.equal(dialog.open,false);assert.equal(dialog.removed,true);handoffs.push(request);request.name='changed callback copy';}});
collect(dialog,'input')[0].value='  Village Walk  ';await find(dialog,'Save clip name').onclick();assert.equal(handoffs.length,1);assert.equal(handoffs[0].asset_id,id);assert.equal(namedRequest.name,'Village Walk');assert.equal(namedRequest.type,'set_animation_label');
current={...nameState(),animation_labels:{[id]:{name:'Village Walk'}}};handoffs=[];
dialog=openRetainedAnimationAsset({...options,onName:async request=>{namedRequest=request;current={...current,animation_labels:{},animation_labels_key:'b'.repeat(64)};return true;},onNameApplied:request=>handoffs.push(request)});await find(dialog,'Reset clip name').onclick();assert.equal(handoffs.length,1);assert.equal(handoffs[0].type,'clear_animation_label');assert.equal(Object.hasOwn(handoffs[0],'name'),false);
for(const transition of ['decline','close','project','scene','native','mode','error']){
 current=nameState();handoffs=[];dialog=openRetainedAnimationAsset({...options,onName:async()=>{if(transition==='decline')return false;if(transition==='close')dialog.close();if(transition==='project')current={...current,project:{...current.project,path:'other'}};if(transition==='scene')current={...current,scene:{id:'scene://other'}};if(transition==='native')current={...current,scene_preview_source_key:'b'.repeat(64)};if(transition==='mode')current={...current,project:{...current.project,mode:'live'}};if(transition==='error')throw Error('Naming rejected');return true;},onNameApplied:request=>handoffs.push(request)});collect(dialog,'input')[0].value='Village Walk';await find(dialog,'Save clip name').onclick();assert.equal(handoffs.length,0,transition);if(transition==='decline'||transition==='error')assert.equal(dialog.open,true);if(transition==='error')assert.equal(errors.pop(),'Naming rejected');dialog.close();
}
assert.deepEqual(errors,[]);console.log('Retained clip name handoff: close-before-open, exact identity, detached receipt, reset, rejection and canceled/changed source/mode guards passed.');
