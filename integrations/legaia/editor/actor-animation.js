// Initial assignment uses an observed same-model witness. Channel edits retain
// their imported shared-clip ownership and never move with this assignment.
const pin='d6e64c68ede25813d35db20980da82a1a025549b';
const hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
const integer=(v,min,max)=>Number.isSafeInteger(v)&&v>=min&&v<=max;
const text=(v,max=8192)=>typeof v==='string'&&v.length>0&&v.length<=max;
const exact=(v,keys)=>v!==null&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const same=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
const list=v=>Array.isArray(v)&&v.length<=64&&v.every(x=>text(x));
const actor=(id,scene)=>typeof id==='string'&&id.startsWith(scene+'/actors/man-p1/')&&/^[0-9]{4}$/.test(id.slice((scene+'/actors/man-p1/').length));
const clip=(id,scene)=>typeof id==='string'&&id.startsWith('animation://'+scene.slice(8)+'/scene-anm/')&&/^[0-9]{4}$/.test(id.slice(('animation://'+scene.slice(8)+'/scene-anm/').length));
const bindingKeys=['schema_version','semantic_id','asset_semantic_id','actor_semantic_id','clip_id','label','reference_commit','source_record','frame_count','bone_count','header_a','header_flags','coordinate_system','looping','timing','association','skeleton','limitations'];
function component(value,scene){
  if(value===null)return;
  if(!exact(value,['donor_entity_id','animation_asset_id','source_record_sha256'])||!actor(value.donor_entity_id,scene)||!clip(value.animation_asset_id,scene)||!hash(value.source_record_sha256))throw new Error('Invalid authored animation assignment.');
}
function binding(value,scene,nullable=true){
  if(value===null&&nullable)return;
  const s=value?.source_record,a=value?.association,bones=value?.bone_count,index=s?.record_index;
  if(!exact(value,bindingKeys)||value.schema_version!=='legaia.animation-preview.v1'||!clip(value.semantic_id,scene)||!actor(value.actor_semantic_id,scene)||typeof value.asset_semantic_id!=='string'||!value.asset_semantic_id.startsWith('asset://'+scene.slice(8)+'/models/scene-tmd/')||!integer(Number(value.asset_semantic_id.slice(('asset://'+scene.slice(8)+'/models/scene-tmd/').length)),0,239)||!/^[0-9]{4}$/.test(value.asset_semantic_id.slice(('asset://'+scene.slice(8)+'/models/scene-tmd/').length))||value.clip_id!=='placement'||!text(value.label,512)||value.reference_commit!==pin||!integer(value.frame_count,1,512)||!integer(bones,1,64)||!integer(value.header_a,0,0x1ff)||(value.header_a&255)!==bones||![2,4].includes(value.header_flags)||value.coordinate_system!=='retail_psx_actor_local_y_down'||value.looping!==null||!list(value.limitations))throw new Error('Invalid scene animation binding.');
  const locator=['disc','iso_file','prot_entry_index','prot_entry_name',...(s?.source_kind==='raw_streaming_anm'?['source_kind','compression','chunk_header_offset','payload_offset','payload_byte_length','payload_sha256','association_evidence']:['scene_table_offset','descriptor_index','descriptor_type','compressed_stream_offset','compressed_bytes_consumed']),'record_index','byte_offset','byte_length','containing_size','byte_coordinate_space','record_sha256'];
  if(!exact(s,locator)||!exact(s.disc,['sha256','serial'])||!hash(s.disc.sha256)||s.disc.serial!=='SCUS-94254'||s.iso_file!=='PROT.DAT'||s.prot_entry_name!==scene.slice(8)||!integer(s.prot_entry_index,0,0xffffffff)||!integer(index,0,254)||value.semantic_id!==`animation://${scene.slice(8)}/scene-anm/${String(index).padStart(4,'0')}`||!hash(s.record_sha256)||!integer(s.containing_size,16,4*1024*1024)||!integer(s.byte_offset,0,s.containing_size)||s.byte_length!==16+bones*value.frame_count*8||s.byte_length>s.containing_size-s.byte_offset)throw new Error('Invalid animation source record.');
  if(s.source_kind==='raw_streaming_anm'){
    if(s.compression!=='none'||s.byte_coordinate_space!=='raw_scene_anm_chunk'||!integer(s.chunk_header_offset,0,0xffffffff-4)||s.payload_offset!==s.chunk_header_offset+4||s.payload_byte_length!==s.containing_size||!hash(s.payload_sha256)||s.association_evidence!=='type_5_in_verified_man_carrier_with_per_actor_channel_validation')throw new Error('Invalid raw animation carrier.');
  }else if(s.byte_coordinate_space!=='decoded_scene_anm_descriptor'||s.descriptor_type!==5||!integer(s.scene_table_offset,0,0xffffffff)||!integer(s.descriptor_index,0,4095)||!integer(s.compressed_stream_offset,0,0xffffffff)||!integer(s.compressed_bytes_consumed,1,0xffffffff-s.compressed_stream_offset))throw new Error('Invalid compressed animation carrier.');
  if(!exact(a,['kind','animation_id','actor_source_record','active_object_indices','excluded_object_indices'])||a.kind!=='verified_man_header_scene_anm_record_plus_one'||a.animation_id!==index+1||!a.actor_source_record||typeof a.actor_source_record!=='object'||Array.isArray(a.actor_source_record)||Object.keys(a.actor_source_record).length>64||!Array.isArray(a.active_object_indices)||!same(a.active_object_indices,Array.from({length:bones},(_,i)=>i))||!Array.isArray(a.excluded_object_indices)||a.excluded_object_indices.length>1024-bones||!same(a.excluded_object_indices,Array.from({length:a.excluded_object_indices.length},(_,i)=>i+bones)))throw new Error('Invalid observed actor/model association.');
  if(!exact(value.timing,['fps','wire_rate','evidence','note'])||value.timing.fps!==null||value.timing.wire_rate!==null||value.timing.evidence!=='unresolved_scene_actor_playback_rate'||!text(value.timing.note)||!exact(value.skeleton,['semantic_id','topology','hierarchy','channels'])||value.skeleton.semantic_id!=='skeleton://'+value.asset_semantic_id.slice(8)||value.skeleton.topology!=='independent_rigid_objects'||value.skeleton.hierarchy!==null||!Array.isArray(value.skeleton.channels)||value.skeleton.channels.length!==bones||value.skeleton.channels.some((row,i)=>!exact(row,['semantic_id','object_index','parent_index'])||row.semantic_id!==`${value.skeleton.semantic_id}/channels/${String(i).padStart(2,'0')}`||row.object_index!==i||row.parent_index!==null))throw new Error('Invalid animation timing or rigid channels.');
  if(JSON.stringify(value).length>256*1024)throw new Error('Animation metadata exceeds the inspector bound.');
}
function matchesComponent(value,metadata){return value!==null&&metadata!==null&&value.donor_entity_id===metadata.actor_semantic_id&&value.animation_asset_id===metadata.semantic_id&&value.source_record_sha256===metadata.source_record.record_sha256;}
function identity(value,entityId,sourceKey,sceneId,schema){
  if(value?.schema_version!==schema||value.entity_id!==entityId||value.scene_id!==sceneId||!/^scene:\/\/[a-z0-9_]+$/.test(sceneId)||!actor(entityId,sceneId)||!hash(sourceKey)||value.source_key!==sourceKey||!list(value.limitations))throw new Error('Animation assignment sources changed. Reopen the inspector.');
}
export function decodeActorAnimationOptions(value,entityId,sourceKey,sceneId){
  identity(value,entityId,sourceKey,sceneId,'legaia.actor-animation-options.v1');
  if(!exact(value,['schema_version','entity_id','scene_id','source_key','supported','reason','imported','base','effective','authored','choices','limitations'])||typeof value.supported!=='boolean'||value.reason!==null&&!text(value.reason)||!Array.isArray(value.choices)||value.choices.length>255)throw new Error('Invalid animation assignment options.');
  for(const key of ['imported','base','effective'])binding(value[key],sceneId);
  component(value.authored,sceneId);
  if(value.imported!==null&&value.imported.actor_semantic_id!==entityId||value.authored!==null&&!matchesComponent(value.authored,value.effective)||value.authored===null&&!same(value.effective,value.base))throw new Error('Animation layers differ from their source assignment.');
  const ids=[];
  for(const row of value.choices){
    if(!exact(row,['value','label','binding'])||!text(row.label,512))throw new Error('Invalid animation choice.');
    component(row.value,sceneId);binding(row.binding,sceneId,false);
    if(!matchesComponent(row.value,row.binding)||!value.base||row.binding.asset_semantic_id!==value.base.asset_semantic_id||row.binding.association.excluded_object_indices.length)throw new Error('Animation choice is not an observed full same-model binding.');
    ids.push(row.value.animation_asset_id);
  }
  if(new Set(ids).size!==ids.length||!same(ids,[...ids].sort())||value.supported&&(!value.base||!ids.length)||!value.supported&&ids.length||value.supported&&value.reason!==null)throw new Error('Animation choice coverage is invalid.');
  return structuredClone(value);
}
export function decodeActorAnimationReview(value,options,requested){
  identity(value,options.entity_id,options.source_key,options.scene_id,'legaia.actor-animation-review.v1');
  if(!exact(value,['schema_version','entity_id','scene_id','source_key','review_key','animation_asset_id','before','after','imported','base','effective','proposed','project_change','limitations'])||!hash(value.review_key)||value.animation_asset_id!==requested||requested!==null&&!clip(requested,options.scene_id)||typeof value.project_change!=='boolean'||!options.supported)throw new Error('Invalid animation assignment review.');
  for(const key of ['imported','base','effective'])if(!same(value[key],options[key]))throw new Error('Animation layers changed since options were verified.');
  component(value.before,options.scene_id);component(value.after,options.scene_id);binding(value.proposed,options.scene_id,false);
  if(!same(value.before,options.authored)||value.project_change===same(value.before,value.after))throw new Error('Animation review does not describe the current override.');
  const choice=requested===null?null:options.choices.find(row=>row.value.animation_asset_id===requested);
  if(requested!==null&&!choice)throw new Error('Animation review is outside the verified choices.');
  const inherited=requested===null||requested===options.base.semantic_id;
  if(inherited?(value.after!==null||!same(value.proposed,options.base)):(!same(value.after,choice.value)||!same(value.proposed,choice.binding)))throw new Error('Proposed animation differs from the selected source binding.');
  return structuredClone(value);
}
export function actorAnimationContext(state,entityId){
  return {entity_id:entityId,scene_id:state.scene?.id,source_key:state.asset_reference_source_key,project_path:state.project?.path};
}
export function actorAnimationContextCurrent(context,state){
  return state.project?.mode==='edit'&&state.capabilities?.actor_animation_assignment===true&&hash(context.source_key)&&same(context,actorAnimationContext(state,context.entity_id))&&state.selection?.entity_id===context.entity_id&&state.scene?.entities?.some(row=>row.id===context.entity_id)===true;
}
export function actorAnimationAssignmentCommand(review){
  return {type:'set_actor_animation',entity_id:review.entity_id,animation_asset_id:review.animation_asset_id,source_key:review.source_key,review_key:review.review_key};
}
export function openActorAnimationAssignment({entity,getState,busy,api,onPreview,onError=()=>{}}){
  const context=actorAnimationContext(getState(),entity?.id);
  if(busy()||!actorAnimationContextCurrent(context,getState()))return;
  const dialog=document.createElement('dialog');dialog.id='actor-animation-dialog';dialog.className='project-dialog';
  const heading=document.createElement('h2');heading.textContent='Initial actor animation';
  const note=document.createElement('p');note.className='field-note';note.textContent='Choose an observed initial clip for the same model. Scripts may replace this assignment; runtime playback and suitability are unknown. Channel edits remain attached to their imported shared clip.';
  const layers=document.createElement('div'),label=document.createElement('label'),select=document.createElement('select');label.textContent='Initial animation';select.setAttribute('aria-label','Initial actor animation');label.append(select);
  const controls=document.createElement('div');controls.className='dialog-actions';controls.style.flexWrap='wrap';
  const reviewButton=document.createElement('button'),previewButton=document.createElement('button'),applyButton=document.createElement('button');reviewButton.textContent='Review selected animation';previewButton.textContent='Preview verified witness clip';applyButton.textContent='Apply reviewed animation';controls.append(reviewButton,previewButton,applyButton);
  const status=document.createElement('p');status.setAttribute('role','status');status.textContent='Verifying observed animation choices…';
  const result=document.createElement('div'),error=document.createElement('p');error.className='dialog-error';error.setAttribute('role','alert');
  const close=document.createElement('button');close.textContent='Close initial animation';close.onclick=()=>dialog.close();
  dialog.append(heading,note,layers,label,controls,status,result,error,close);document.body.append(dialog);
  let generation=0,controller=null,options=null,review=null,working=false;
  const current=()=>dialog.open&&actorAnimationContextCurrent(context,getState());
  const chosen=()=>select.value===''?null:select.value;
  function update(){const disabled=busy()||working||!current();select.disabled=disabled||!options?.supported;reviewButton.disabled=disabled||!options?.supported;previewButton.disabled=disabled||!review;applyButton.disabled=disabled||!review?.project_change;}
  function invalidate(){generation++;controller?.abort();controller=null;review=null;working=false;result.replaceChildren();update();}
  function fail(e){error.textContent=e.message??String(e);onError(e);}
  function ready(){if(busy()||working)return false;if(current())return true;review=null;fail(new Error('Project, selection or model changed. Reopen initial animation.'));update();return false;}
  function row(host,title,value){const section=document.createElement('section'),h=document.createElement('h3'),p=document.createElement('p');h.textContent=title;p.textContent=value?`${value.semantic_id} · model ${value.asset_semantic_id} · ${value.frame_count} frames / ${value.bone_count} rigid channels`:'Unavailable';section.append(h,p);host.append(section);return section;}
  function showReview(value){
    result.replaceChildren();const section=row(result,'Proposed · not applied',value.proposed),witness=document.createElement('p');witness.textContent=`Observed witness: ${value.proposed.actor_semantic_id} · source record ${value.proposed.source_record.record_index} · SHA-256 ${value.proposed.source_record.record_sha256}`;section.append(witness);
    const details=document.createElement('details'),summary=document.createElement('summary'),pre=document.createElement('pre');summary.textContent='Verified assignment evidence';pre.className='diagnostic-detail';pre.textContent=JSON.stringify(value,null,2);details.append(summary,pre);result.append(details);
    status.textContent=value.project_change?(value.after?'Assignment reviewed · explicit Apply required.':'Clearing reviewed · appearance default will be inherited.'):'Already inherited or assigned · no project change.';
  }
  async function load(route,body,accept){
    if(busy()||!current())return;const token=++generation;controller?.abort();const active=new AbortController();controller=active;working=true;review=null;error.textContent='';result.replaceChildren();update();
    try{const response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:active.signal}),value=await response.json();
      if(token!==generation||active.signal.aborted||!dialog.open)return;
      if(!current())throw new Error('Project, selection or model changed. Reopen initial animation.');
      if(busy())throw new Error('Another editor operation started. Review again when it completes.');
      if(!response.ok||value.error)throw new Error(typeof value.error==='string'?value.error:'Animation verification failed.');
      accept(value);
    }catch(e){if(e.name!=='AbortError'&&token===generation&&dialog.open)fail(e);}
    finally{if(controller===active){controller=null;working=false;update();}}
  }
  select.onchange=()=>{invalidate();status.textContent='Choice changed · review before previewing or applying.';};
  reviewButton.onclick=()=>{if(!ready()||!options?.supported)return;const requested=chosen();if(requested!==null&&!options.choices.some(r=>r.value.animation_asset_id===requested))return;status.textContent='Reverifying selected initial animation…';void load('/api/actor-animation-review',{entity_id:entity.id,animation_asset_id:requested,source_key:context.source_key},value=>{review=decodeActorAnimationReview(value,options,requested);showReview(review);});};
  previewButton.onclick=async()=>{
    if(!ready()||!review)return;const accepted=review,token=++generation;working=true;update();error.textContent='';
    try{await onPreview(structuredClone(accepted));if(token===generation&&dialog.open&&!current()){review=null;fail(new Error('Project sources changed during preview. Reopen initial animation.'));}}
    catch(e){if(token===generation&&dialog.open)fail(e);}
    finally{if(token===generation){working=false;update();}}
  };
  applyButton.onclick=async()=>{
    if(!ready()||!review?.project_change)return;const accepted=review;review=null;working=true;update();error.textContent='';
    try{if(await api('/api/command',actorAnimationAssignmentCommand(accepted),{dialog,success:'Initial animation updated. Undo restores the assignment; Save persists it.'})){if(dialog.open)dialog.close();}
      else if(dialog.open)fail(new Error('Assignment rejected. Reopen and review the current actor.'));}
    catch(e){if(dialog.open)fail(e);}finally{working=false;if(dialog.open)update();}
  };
  dialog.addEventListener('close',()=>{generation++;controller?.abort();controller=null;review=null;dialog.remove();});
  dialog.showModal();update();
  void load('/api/actor-animation-options',{entity_id:entity.id},value=>{
    options=decodeActorAnimationOptions(value,entity.id,context.source_key,context.scene_id);layers.replaceChildren();row(layers,'Imported',options.imported);row(layers,'Inherited appearance default',options.base);row(layers,'Current effective',options.effective);
    const authored=document.createElement('p');authored.textContent=options.authored?`Current authored assignment: ${options.authored.animation_asset_id}`:'Current authored assignment: None · inherit appearance default';layers.append(authored);
    select.replaceChildren();const inherit=document.createElement('option');inherit.value='';inherit.textContent='Inherit appearance default';select.append(inherit);for(const choice of options.choices){const item=document.createElement('option');item.value=choice.value.animation_asset_id;item.textContent=choice.label;select.append(item);}select.value=options.authored?.animation_asset_id??'';
    status.textContent=options.supported?`${options.choices.length} observed same-model clips · select and review.`:options.reason??'No supported same-model animation assignments.';
    const limitations=document.createElement('ul');for(const limitation of options.limitations){const item=document.createElement('li');item.textContent=limitation;limitations.append(item);}layers.append(limitations);
  });
  return dialog;
}
