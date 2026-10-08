import assert from 'node:assert/strict';
import {resolveActorAnimationGlbTarget} from '../editor/actor-animation-glb-target.js';
const entity='scene://town01/actors/man-p1/0011',donor=entity.replace('0011','0012'),id='11111111-1111-4111-8111-111111111111',asset='asset://town01/models/scene-tmd/0105';
const initial={projectPath:'C:/private/project',sceneId:'scene://town01',mode:'edit',sourceKey:'a'.repeat(64)};
const binding={scene_id:initial.sceneId,record_id:id,record_sha256:'b'.repeat(64),model_asset_id:asset};
const row={record_id:id,animation_id:'animation://town01/authored-record/'+id,entity_id:donor,channel_owner_entity_id:donor,model_source_entity_id:donor,donor_asset_id:asset,donor_animation_id:'animation://town01/scene-anm/0012',record_sha256:binding.record_sha256,frame_count:3,object_count:6,active:true,runtime_assigned:false};
const library=()=>({schema_version:'legaia.animation-record-library.v1',scene_id:initial.sceneId,project_source_key:initial.sourceKey,revision:1,records:[structuredClone(row)],activation_available:true,build_available:true,gameplay_verified:false});
let actor,context,calls;
function reset(){actor={id:entity,components:{ActorAllocatedAnimation:{authored:structuredClone(binding)}}};context={...initial};calls=[];}
const settings={entityId:entity,getActor:()=>actor,getContext:()=>context,fetcher:async(path,request)=>{calls.push({path,body:JSON.parse(request.body)});return {ok:true,json:async()=>library()};}};
reset();assert.deepEqual(await resolveActorAnimationGlbTarget(settings),row);
assert.deepEqual(calls,[{path:'/api/animation-record-library',body:{scene_id:initial.sceneId,expected_source_key:initial.sourceKey}}]);
reset();let reorderedReply;const reordered=resolveActorAnimationGlbTarget({...settings,fetcher:()=>new Promise(resolve=>reorderedReply=resolve)});
actor.components.ActorAllocatedAnimation.authored=Object.fromEntries(Object.entries(actor.components.ActorAllocatedAnimation.authored).reverse());
reorderedReply({ok:true,json:async()=>library()});assert.deepEqual(await reordered,row);
reset();actor.components={};assert.equal(await resolveActorAnimationGlbTarget(settings),null);assert.equal(calls.length,0);
reset();actor.id=donor;await assert.rejects(resolveActorAnimationGlbTarget(settings),/Selected actor/);assert.equal(calls.length,0);
for(const mutate of [v=>v.scene_id='scene://town02',v=>v.extra=true]){reset();mutate(actor.components.ActorAllocatedAnimation.authored);await assert.rejects(resolveActorAnimationGlbTarget(settings),/invalid/);assert.equal(calls.length,0);}
for(const mutate of [v=>v.records[0].active=false,v=>v.records[0].record_sha256='c'.repeat(64),v=>v.records[0].donor_asset_id='asset://town01/models/scene-tmd/0106',v=>v.records=[],v=>v.project_source_key='c'.repeat(64)]){
 reset();const value=library();mutate(value);await assert.rejects(resolveActorAnimationGlbTarget({...settings,fetcher:async()=>({ok:true,json:async()=>value})}));
}
for(const mutate of [()=>context.sourceKey='c'.repeat(64),()=>context.projectPath='C:/other/project',()=>context.mode='play',()=>actor.id=donor,()=>actor.components.ActorAllocatedAnimation.authored.record_sha256='c'.repeat(64),()=>actor.components={}]){
 reset();let release;const held=resolveActorAnimationGlbTarget({...settings,fetcher:()=>new Promise(resolve=>release=resolve)});mutate();release({ok:true,json:async()=>library()});await assert.rejects(held);
}
reset();await assert.rejects(resolveActorAnimationGlbTarget({...settings,fetcher:async()=>({ok:false,json:async()=>({error:'Disc verification failed'})})}),/Disc verification failed/);
console.log('Actor GLB routing: imported fallback, shared donor, exact assignment/library and late context guards passed.');
