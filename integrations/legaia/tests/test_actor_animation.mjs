import assert from 'node:assert/strict';
import {decodeActorAnimationOptions,decodeActorAnimationReview,actorAnimationContext,actorAnimationContextCurrent,actorAnimationAssignmentCommand} from '../editor/actor-animation.js';
const scene='scene://town0b',entity=scene+'/actors/man-p1/0019',donor=scene+'/actors/man-p1/0049',key='1'.repeat(64),sourceHash='2'.repeat(64),alternateHash='3'.repeat(64),reviewHash='4'.repeat(64),model='asset://town0b/models/scene-tmd/0102';
function binding(id,record,frames,sha){
  const skeleton='skeleton://town0b/models/scene-tmd/0102';
  return {schema_version:'legaia.animation-preview.v1',semantic_id:`animation://town0b/scene-anm/${String(record).padStart(4,'0')}`,asset_semantic_id:model,actor_semantic_id:id,clip_id:'placement',label:`Imported animation ${record+1}`,reference_commit:'d6e64c68ede25813d35db20980da82a1a025549b',
    source_record:{disc:{sha256:'5'.repeat(64),serial:'SCUS-94254'},iso_file:'PROT.DAT',prot_entry_index:10,prot_entry_name:'town0b',scene_table_offset:24,descriptor_index:3,descriptor_type:5,compressed_stream_offset:128,compressed_bytes_consumed:256,record_index:record,byte_offset:1600,byte_length:16+6*frames*8,containing_size:8192,byte_coordinate_space:'decoded_scene_anm_descriptor',record_sha256:sha},
    frame_count:frames,bone_count:6,header_a:6,header_flags:2,coordinate_system:'retail_psx_actor_local_y_down',looping:null,timing:{fps:null,wire_rate:null,evidence:'unresolved_scene_actor_playback_rate',note:'Preview rate is explicit.'},
    association:{kind:'verified_man_header_scene_anm_record_plus_one',animation_id:record+1,actor_source_record:{record_index:Number(id.slice(-4))},active_object_indices:[0,1,2,3,4,5],excluded_object_indices:[]},
    skeleton:{semantic_id:skeleton,topology:'independent_rigid_objects',hierarchy:null,channels:Array.from({length:6},(_,i)=>({semantic_id:`${skeleton}/channels/${String(i).padStart(2,'0')}`,object_index:i,parent_index:null}))},limitations:['Initial source association; runtime playback unknown.']};
}
const imported=binding(entity,13,15,sourceHash),alternate=binding(donor,12,30,alternateHash);
const value=b=>({donor_entity_id:b.actor_semantic_id,animation_asset_id:b.semantic_id,source_record_sha256:b.source_record.record_sha256});
const options={schema_version:'legaia.actor-animation-options.v1',entity_id:entity,scene_id:scene,source_key:key,supported:true,reason:null,imported,base:imported,effective:imported,authored:null,choices:[{value:value(alternate),label:'Scene clip 0012',binding:alternate},{value:value(imported),label:'Scene clip 0013',binding:imported}],limitations:['Only observed same-model associations.']};
const review={schema_version:'legaia.actor-animation-review.v1',entity_id:entity,scene_id:scene,source_key:key,review_key:reviewHash,animation_asset_id:alternate.semantic_id,before:null,after:value(alternate),imported,base:imported,effective:imported,proposed:alternate,project_change:true,limitations:['Runtime playback unknown.']};
const before=structuredClone(options),decoded=decodeActorAnimationOptions(options,entity,key,scene),accepted=decodeActorAnimationReview(review,decoded,alternate.semantic_id);
decoded.choices[0].binding.source_record.record_sha256='9'.repeat(64);accepted.proposed.association.active_object_indices.pop();assert.deepEqual(options,before);assert.equal(review.proposed.association.active_object_indices.length,6);
for(const change of [v=>v.source_key='6'.repeat(64),v=>v.entity_id=donor,v=>v.scene_id='scene://town01',v=>v.supported='yes',v=>v.choices.push(v.choices[0]),v=>v.choices.reverse(),v=>v.choices[0].binding.asset_semantic_id='asset://town0b/models/scene-tmd/0103',v=>v.choices[0].binding.source_record.record_index=13,v=>v.choices[0].value.source_record_sha256=sourceHash,v=>v.choices[0].binding.source_record.byte_offset=8192,v=>v.choices[0].binding.source_record.byte_length=32,v=>v.choices[0].binding.association.excluded_object_indices=[6],v=>v.choices[0].binding.reference_commit='unknown',v=>v.choices[0].binding.frames=[],v=>v.choices[0].binding.timing.fps=30,v=>v.choices[0].binding.skeleton.channels[0].parent_index=0,v=>v.authored=value(alternate),v=>v.read_only=true]){
  const bad=structuredClone(options);change(bad);assert.throws(()=>decodeActorAnimationOptions(bad,entity,key,scene));
}
for(const change of [v=>v.review_key='old',v=>v.animation_asset_id=imported.semantic_id,v=>v.before=value(imported),v=>v.after=null,v=>v.proposed=imported,v=>v.base=alternate,v=>v.project_change=false,v=>v.proposed.source_record.record_sha256=sourceHash]){
  const bad=structuredClone(review);change(bad);assert.throws(()=>decodeActorAnimationReview(bad,options,alternate.semantic_id));
}
const authoredOptions={...options,authored:value(alternate),effective:alternate};
decodeActorAnimationOptions(authoredOptions,entity,key,scene);
const clear={...review,animation_asset_id:null,before:value(alternate),after:null,effective:alternate,proposed:imported};
assert.equal(decodeActorAnimationReview(clear,authoredOptions,null).after,null);
assert.equal(decodeActorAnimationReview({...clear,animation_asset_id:imported.semantic_id},authoredOptions,imported.semantic_id).after,null);
decodeActorAnimationReview({...review,animation_asset_id:null,after:null,proposed:imported,project_change:false},options,null);
const unsupported={...options,supported:false,reason:'No observed alternative supported.',imported:null,base:null,effective:null,choices:[]};
decodeActorAnimationOptions(unsupported,entity,key,scene);assert.throws(()=>decodeActorAnimationReview(review,unsupported,alternate.semantic_id));
const rawOptions=structuredClone(options);
for(const b of [rawOptions.imported,rawOptions.base,rawOptions.effective,...rawOptions.choices.map(r=>r.binding)]){
  const s=b.source_record;for(const k of ['scene_table_offset','descriptor_index','descriptor_type','compressed_stream_offset','compressed_bytes_consumed'])delete s[k];Object.assign(s,{source_kind:'raw_streaming_anm',compression:'none',chunk_header_offset:100,payload_offset:104,payload_byte_length:8192,payload_sha256:'7'.repeat(64),association_evidence:'type_5_in_verified_man_carrier_with_per_actor_channel_validation',byte_coordinate_space:'raw_scene_anm_chunk'});
}
decodeActorAnimationOptions(rawOptions,entity,key,scene);
const state={project:{path:'C:/private/project',mode:'edit'},scene:{id:scene,entities:[{id:entity}]},asset_reference_source_key:key,selection:{entity_id:entity},capabilities:{actor_animation_assignment:true}},context=actorAnimationContext(state,entity);
assert.equal(actorAnimationContextCurrent(context,state),true);
for(const change of [s=>s.asset_reference_source_key='8'.repeat(64),s=>s.scene.id='scene://town01',s=>s.selection.entity_id=donor,s=>s.project.path='C:/other',s=>s.project.mode='live',s=>s.scene.entities=[],s=>s.capabilities.actor_animation_assignment=false]){const changed=structuredClone(state);change(changed);assert.equal(actorAnimationContextCurrent(context,changed),false);}
const command=actorAnimationAssignmentCommand(review);assert.deepEqual(command,{type:'set_actor_animation',entity_id:entity,animation_asset_id:alternate.semantic_id,source_key:key,review_key:reviewHash});command.entity_id='other';assert.equal(review.entity_id,entity);assert.equal(actorAnimationAssignmentCommand(clear).animation_asset_id,null);
console.log('Actor animation metadata, same-model witness, source/range/count guards, reviewed set/clear, detached values and stale context checks passed.');
