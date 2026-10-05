// Readonly retained AssetDB inspection; authored identity does not imply live playback.
const hash=x=>typeof x==='string'&&/^[0-9a-f]{64}$/.test(x);
const exact=(x,keys)=>x&&typeof x==='object'&&!Array.isArray(x)&&Object.keys(x).length===keys.length&&keys.every(k=>Object.hasOwn(x,k));
const integer=(x,min,max)=>Number.isSafeInteger(x)&&x>=min&&x<=max;
export function decodeRetainedAnimationAsset(record){
  const data=record?.data??record,id=record?.id??data?.semantic_id;
  const match=/^animation:\/\/([a-z0-9]{1,12})\/authored-record\/([0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})$/.exec(id);
  if(!match||data.semantic_id!==id||data.asset_kind!=='animation'||data.scope!=='authored-retained'||data.authored_animation_record!==true)throw new Error('Invalid retained animation asset identity.');
  const row=data.retained_record,source=data.source_record,scene='scene://'+match[1],actor=x=>typeof x==='string'&&new RegExp('^'+scene+'/actors/man-p1/[0-9]{4}$').test(x);
  const keys=['record_id','animation_id','entity_id','channel_owner_entity_id','model_source_entity_id','donor_asset_id','donor_animation_id','record_sha256','frame_count','object_count','active','runtime_assigned','assigned_actor_ids'];
  if(!exact(row,keys)||row.record_id!==match[2]||row.animation_id!==id||![row.entity_id,row.channel_owner_entity_id,row.model_source_entity_id].every(actor)||typeof row.donor_asset_id!=='string'||!row.donor_asset_id.startsWith('asset://')||row.donor_asset_id!==data.model_asset_id||!new RegExp('^animation://'+match[1]+'/scene-anm/[0-9]{4}$').test(row.donor_animation_id)||!hash(row.record_sha256)||!integer(row.frame_count,1,512)||!integer(row.object_count,1,64)||row.frame_count!==data.frame_count||row.object_count!==data.bone_count||typeof row.active!=='boolean'||row.runtime_assigned!==false||!Array.isArray(row.assigned_actor_ids)||row.assigned_actor_ids.length>4096||row.assigned_actor_ids.some(id=>!actor(id))||new Set(row.assigned_actor_ids).size!==row.assigned_actor_ids.length||!row.active&&row.assigned_actor_ids.length)throw new Error('Invalid retained animation capture or assignment metadata.');
  if(!exact(source,['source_kind','record_id','record_sha256','ledger_sha256','donor_record_sha256','donor_animation_id'])||source.source_kind!=='authored_animation_record'||source.record_id!==row.record_id||source.record_sha256!==row.record_sha256||source.donor_animation_id!==row.donor_animation_id||![source.record_sha256,source.ledger_sha256,source.donor_record_sha256].every(hash))throw new Error('Invalid retained animation source witnesses.');
  return structuredClone(data);
}
export function qualifyRetainedAnimationPreview(value,data){
  data=decodeRetainedAnimationAsset(data);
  const actual=decodeRetainedAnimationAsset(value?.animation?.asset_source);
  const same=(a,b)=>Object.keys(a).length===Object.keys(b).length&&Object.keys(a).every(k=>JSON.stringify(a[k])===JSON.stringify(b[k]));
  const vector=v=>Array.isArray(v)&&v.length===3&&v.every(x=>typeof x==='number'&&Number.isFinite(x));
  if(value?.semantic_id!==data.model_asset_id||value.animation.semantic_id!==data.semantic_id||value.animation.asset_semantic_id!==data.model_asset_id||value.animation.representation!=='allocated_record'||!same(actual.source_record,data.source_record)||!same(actual.retained_record,data.retained_record)||actual.model_asset_id!==data.model_asset_id||value.animation.frame_count!==data.frame_count||value.animation.bone_count!==data.bone_count||!Array.isArray(value.vertices)||!value.vertices.length||!value.vertices.every(vector)||!Array.isArray(value.frames)||value.frames.length!==data.frame_count||value.frames.some((frame,i)=>frame.frame_index!==i||!Array.isArray(frame.vertices)||frame.vertices.length!==value.vertices.length||!frame.vertices.every(vector))||value.animation.source_record?.record_sha256!==data.source_record.record_sha256)throw new Error('Retained preview differs from its inspected asset source. Refresh assets.');
  return value;
}
export function retainedAnimationEditContext(record,state){
  const data=decodeRetainedAnimationAsset(record);
  if(state?.project?.mode!=='edit'||state.capabilities?.actor_animation_authoring!==true||!hash(state.scene_preview_source_key)||state.scene?.id!=='scene://'+data.semantic_id.split('/')[2])throw new Error('Retained content editing requires its current scene in Edit mode.');
  const row=structuredClone(data.retained_record);delete row.assigned_actor_ids;
  return {assetId:data.semantic_id,entityId:row.entity_id,row};
}
export function openRetainedAnimationAsset({record,getState,busy,onPreview,onModel,onActor,onEdit=null,onGlb=null,onError=()=>{}}){
  if(busy())return;
  const data=decodeRetainedAnimationAsset(record),initial=getState(),key=initial.scene_preview_source_key,scene=initial.scene?.id,path=initial.project?.path;
  if(!hash(key)||scene!=='scene://'+data.semantic_id.split('/')[2])throw new Error('Retained clip requires its current scene source.');
  const dialog=document.createElement('dialog');dialog.id='retained-animation-asset-dialog';dialog.className='project-dialog';
  const add=(tag,text,parent=dialog)=>{const node=document.createElement(tag);if(text!==undefined)node.textContent=text;parent.append(node);return node;};
  const heading=add('div');heading.className='dialog-heading';add('h2',record.label??data.name,heading);
  const close=add('button','Close',heading);close.onclick=()=>dialog.close();
  add('p',`${data.retained_record.active?'Active in the authored bank':'Retired; absent from the generated bank'} | ${data.frame_count} frames | ${data.bone_count} rigid channels`);
  add('p',data.semantic_id);add('p',`Authored initial assignments: ${data.retained_record.assigned_actor_ids.length}. Runtime playback and timing are unresolved.`);
  const status=add('p');status.setAttribute('role','status');const actions=add('div');actions.className='dialog-actions';
  const preview=add('button','Preview retained clip',actions),model=add('button','Inspect captured model',actions),owner=add('button','Select capture actor',actions);
  const edit=add('button','Edit retained content',actions);edit.hidden=typeof onEdit!=='function'||initial.project?.mode!=='edit'||initial.capabilities?.actor_animation_authoring!==true;
  edit.onclick=async()=>{try{guard();const context=retainedAnimationEditContext(data,getState());dialog.close();await onEdit(context);}catch(e){if(dialog.open)status.textContent=e.message;onError(e);}};
  const glb=add('button','Edit retained GLB',actions);glb.hidden=typeof onGlb!=='function'||initial.project?.mode!=='edit'||initial.capabilities?.actor_animation_authoring!==true;
  glb.onclick=async()=>{try{guard();const context=retainedAnimationEditContext(data,getState());dialog.close();await onGlb(context);}catch(e){if(dialog.open)status.textContent=e.message;onError(e);}};
  const details=add('details');add('summary','Retained source and provenance',details);add('pre',JSON.stringify(data,null,2),details).className='diagnostic-detail';
  let controller=null,pending=false;
  const current=()=>dialog.open&&getState().scene_preview_source_key===key&&getState().scene?.id===scene&&getState().project?.path===path;
  const guard=()=>{if(!current())throw new Error('Project source changed. Reopen the retained clip.');if(busy()||pending)throw new Error('Finish the current operation before inspecting this clip.');};
  model.onclick=async()=>{try{guard();dialog.close();await onModel(data.model_asset_id);}catch(e){onError(e);}};
  owner.onclick=async()=>{try{guard();dialog.close();await onActor(data.retained_record.entity_id);}catch(e){onError(e);}};
  preview.onclick=async()=>{try{guard();pending=true;preview.disabled=model.disabled=owner.disabled=edit.disabled=glb.disabled=true;controller=new AbortController();status.textContent='Verifying retained clip and current model geometry...';
    const response=await fetch('/api/retained-animation-preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:data.semantic_id,expected_source_key:key}),signal:controller.signal});const value=await response.json();
    if(!current()){if(dialog.open)status.textContent='Project source changed. Reopen the retained clip.';return;}if(!response.ok||value.error)throw new Error(value.error||'Retained clip preview failed.');qualifyRetainedAnimationPreview(value,data);dialog.close();await onPreview(data,value);
  }catch(e){if(e.name!=='AbortError'&&dialog.open){status.textContent=e.message;onError(e);}}finally{pending=false;if(dialog.open)preview.disabled=model.disabled=owner.disabled=edit.disabled=glb.disabled=!current();}};
  dialog.addEventListener('close',()=>{controller?.abort();dialog.remove();});document.body.append(dialog);dialog.showModal();return dialog;
}
