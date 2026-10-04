import assert from 'node:assert/strict';
import {decodeAllocatedAssignmentReview,decodeAllocatedAssignmentPose,openAnimationRecordLibrary} from '../editor/animation-record-library.js';
const entity='scene://town01/actors/man-p1/0011',asset='asset://town01/models/scene-tmd/0105',id='11111111-1111-4111-8111-111111111111';
const context={projectPath:'C:/private',sceneId:'scene://town01',sourceKey:'a'.repeat(64),mode:'edit'};
const row={record_id:id,animation_id:'animation://town01/authored-record/'+id,entity_id:entity,channel_owner_entity_id:entity,model_source_entity_id:entity,donor_asset_id:asset,donor_animation_id:'animation://town01/scene-anm/0012',record_sha256:'b'.repeat(64),frame_count:3,object_count:6,active:true,runtime_assigned:false};
const binding={scene_id:context.sceneId,record_id:id,record_sha256:row.record_sha256,model_asset_id:asset};
const request={entity_id:entity,record_id:id,expected_source_key:context.sourceKey};
const report=(clear=false,before=null)=>({schema_version:'legaia.allocated-animation-assignment-review.v1',entity_id:entity,scene_id:context.sceneId,record_id:clear?null:id,project_source_key:context.sourceKey,review_key:'c'.repeat(64),candidate_man_sha256:'d'.repeat(64),effective_bank_sha256:'e'.repeat(64),before,proposed_component:clear?null:binding,animation_id:clear?null:row.animation_id,channel_owner_entity_id:entity,native_animation_id:clear?13:70,native_record_index:69,frame_count:3,object_count:6,project_changed:false,project_change:true,gameplay_verified:false,capabilities:{apply:true,build_assignment:true,pose_preview:!clear},changes:[],limitations:['Gameplay unverified.']});
const pose=r=>({schema_version:'legaia.model-preview.v1',semantic_id:asset,frames:[{},{},{}],animation:{representation:'allocated_assignment_preview',clip_id:'allocated-assignment-preview',entity_id:entity,semantic_id:row.animation_id,source_record:{record_id:id,record_sha256:row.record_sha256},frame_count:3,bone_count:6,assignment_proposal:r}});
decodeAllocatedAssignmentReview(report(),request,row);decodeAllocatedAssignmentPose(pose(report()),report(),row);
decodeAllocatedAssignmentReview(report(true,binding),{...request,record_id:null},row,binding);
for(const edit of [r=>r.entity_id+='x',r=>r.before=binding,r=>r.proposed_component.record_sha256='0'.repeat(64),r=>r.native_animation_id=71,r=>r.gameplay_verified=true,r=>r.capabilities.apply=false]){const r=structuredClone(report());edit(r);assert.throws(()=>decodeAllocatedAssignmentReview(r,request,row));}
const wrong=pose(report());wrong.animation.assignment_proposal.review_key='0'.repeat(64);assert.throws(()=>decodeAllocatedAssignmentPose(wrong,report(),row));
class Node{constructor(tag){this.children=[];this.style={};this.dataset={};this.value='';this.open=false;this.disabled=false;}append(...nodes){for(const n of nodes){this.children.push(n);n.parent=this;}}setAttribute(){}showModal(){this.open=true;}close(){this.open=false;this.onclose?.();}remove(){if(this.parent)this.parent.children=this.parent.children.filter(n=>n!==this);}}
const tree=n=>[n,...n.children.flatMap(tree)],action=(c,k)=>tree(c.dialog).find(n=>n.dataset.action===k);
const old={document:globalThis.document,fetch:globalThis.fetch};globalThis.document={body:new Node('body'),createElement:t=>new Node(t)};
try{
 let current={...context},before=null,busy=false,calls=[],applied=0,returnPreview;
 globalThis.fetch=async(path,settings)=>{const body=JSON.parse(settings.body);calls.push({path,body});return {ok:true,json:async()=>path.endsWith('-library')?{schema_version:'legaia.animation-record-library.v1',scene_id:context.sceneId,project_source_key:context.sourceKey,revision:1,records:[row],activation_available:true,build_available:true,gameplay_verified:false}:path.endsWith('-review')?report(body.record_id===null,before):path.endsWith('-pose')?pose(report(false,before)):{project:{mode:'edit'}}};};
 const options=()=>({entityId:entity,getContext:()=>current,assignment:before,modelAssetId:asset,busy:()=>busy,setBusy:v=>busy=v,onApplied:()=>applied++,onPosePreview:async(_,callbacks)=>returnPreview=callbacks.returnToEditor});
 let control=await openAnimationRecordLibrary(options());await control.ready;
 assert.equal(action(control,'clear-assignment').disabled,true);assert.equal(action(control,'assignment-pose').disabled,true);
 assert.equal(await action(control,'assign').onclick(),true);assert.deepEqual(calls.at(-1).body,request);assert.equal(action(control,'apply').disabled,false);
 assert.equal(await action(control,'assignment-pose').onclick(),true);assert.equal(control.dialog.open,false);assert.equal(returnPreview(),true);assert.equal(action(control,'apply').disabled,false);
 assert.equal(await action(control,'apply').onclick(),true);assert.equal(calls.at(-1).path,'/api/allocated-animation-assignment');assert.equal(calls.at(-1).body.review_key,report().review_key);assert.equal(applied,1);assert.equal(busy,false);
 before=binding;control=await openAnimationRecordLibrary(options());await control.ready;assert.equal(await action(control,'clear-assignment').onclick(),true);assert.equal(calls.at(-1).body.record_id,null);assert.equal(action(control,'assignment-pose').disabled,true);
 assert.equal(await action(control,'apply').onclick(),true);assert.equal(calls.at(-1).body.record_id,null);assert.equal(applied,2);
 control=await openAnimationRecordLibrary(options());await control.ready;await action(control,'assign').onclick();current={...current,sourceKey:'f'.repeat(64)};control.updateState();assert.equal(action(control,'apply').disabled,true);assert.equal(await action(control,'apply').onclick(),false);control.dispose();
}finally{Object.assign(globalThis,old);}
console.log('Allocated assignment Review, exact identity/pose, Apply, clear, retained Return and stale source checks passed.');
