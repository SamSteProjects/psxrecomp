import {animationGlbContext} from './animation-glb.js';
const object=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
const hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
const uuid=v=>typeof v==='string'&&/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(v);
const integer=(v,a,b)=>Number.isSafeInteger(v)&&v>=a&&v<=b;
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const fail=message=>{throw new Error(message);};
const actor=(id,scene)=>typeof id==='string'&&id.startsWith(scene+'/actors/man-p1/')&&/^\d{4}$/.test(id.slice((scene+'/actors/man-p1/').length));
export function decodeAnimationRecordLibrary(value,context){
  context=animationGlbContext(context);
  if(!object(value)||value.schema_version!=='legaia.animation-record-library.v1'||value.scene_id!==context.sceneId||value.project_source_key!==context.sourceKey||!integer(value.revision,0,64)||!Array.isArray(value.records)||value.records.length>64||typeof value.activation_available!=='boolean'||value.activation_available!==(value.revision<64)||value.build_available!==false||value.gameplay_verified!==false)fail('Saved clip library differs from the current scene source.');
  const ids=new Set(),prefix='animation://'+context.sceneId.slice(8);
  for(const row of value.records){
    if(!object(row)||!uuid(row.record_id)||ids.has(row.record_id)||row.animation_id!==prefix+'/authored-record/'+row.record_id||!actor(row.entity_id,context.sceneId)||!actor(row.channel_owner_entity_id,context.sceneId)||!actor(row.model_source_entity_id,context.sceneId)||typeof row.donor_asset_id!=='string'||!/^asset:\/\/[A-Za-z0-9_./-]+$/.test(row.donor_asset_id)||typeof row.donor_animation_id!=='string'||!row.donor_animation_id.startsWith(prefix+'/scene-anm/')||!/^\d{4}$/.test(row.donor_animation_id.slice((prefix+'/scene-anm/').length))||!hash(row.record_sha256)||!integer(row.frame_count,1,512)||!integer(row.object_count,1,64)||typeof row.active!=='boolean'||row.runtime_assigned!==false)fail('Saved clip identity, provenance or counts are invalid.');
    ids.add(row.record_id);
  }
  if((value.records.length===0)!==(value.revision===0))fail('Saved clip library revision is invalid.');
  return structuredClone(value);
}
export function decodeSavedAnimationPose(value,row){
  const a=value?.animation;
  if(!object(value)||value.schema_version!=='legaia.model-preview.v1'||value.semantic_id!==row.donor_asset_id||!object(a)||a.representation!=='allocated_record'||a.clip_id!=='allocated-record'||a.semantic_id!==row.animation_id||a.entity_id!==row.entity_id||a.frame_count!==row.frame_count||a.bone_count!==row.object_count||!same(a.saved_record,row)||a.source_record?.record_id!==row.record_id||a.source_record?.record_sha256!==row.record_sha256||a.source_record?.byte_coordinate_space!=='retained_native_animation_record'||a.association?.runtime_assigned!==false||!Array.isArray(value.frames)||value.frames.length!==row.frame_count)fail('Saved pose differs from the selected retained clip.');
  return structuredClone(value);
}
export function decodeRecordActivationReview(value,request,row){
  const ledger=value?.proposed_ledger,entry=ledger?.records?.find(e=>e.record_id===row.record_id);
  if(!object(value)||value.schema_version!=='legaia.animation-record-activation-review.v1'||value.scene_id!==request.scene_id||value.record_id!==row.record_id||value.active!==request.active||value.project_source_key!==request.expected_source_key||!hash(value.review_key)||!hash(value.candidate_bank_sha256)||value.project_changed!==false||value.gameplay_verified!==false||!object(ledger)||ledger.schema_version!=='legaia.animation-record-ledger.v1'||ledger.source_scene_id!==request.scene_id||!Array.isArray(ledger.removed_record_ids)||!integer(ledger.revision,1,64)||entry?.record_sha256!==row.record_sha256||entry?.entity_id!==row.entity_id||request.active===ledger.removed_record_ids.includes(row.record_id))fail('Retirement/restoration review differs from the selected clip and source.');
  return structuredClone(value);
}
const element=(tag,text)=>{const node=document.createElement(tag);if(text!==undefined)node.textContent=text;return node;};
const button=(label,action)=>{const node=element('button',label);node.type='button';node.dataset.action=action;return node;};
export async function openAnimationRecordLibrary({entityId,getContext,busy=()=>false,setBusy=()=>{},onApplied=()=>{},onPosePreview=null,onError=()=>{}}){
  const context=animationGlbContext(getContext());
  if(!actor(entityId,context.sceneId))fail('Choose an imported actor in the editable scene.');
  const dialog=element('dialog');dialog.className='project-dialog';dialog.style.maxWidth='52rem';dialog.style.maxHeight='90vh';dialog.style.overflowY='auto';
  const select=element('select');select.setAttribute('aria-label','Saved allocated clip');
  const inspect=button('Preview saved clip','pose'),reviewButton=button('Review retirement','review'),apply=button('Apply reviewed change','apply'),close=button('Close','close');inspect.hidden=onPosePreview===null;
  const actions=element('div');actions.append(inspect,reviewButton,apply,close);
  const details=element('p'),status=element('p','Verifying retained clips…'),error=element('p');status.setAttribute('role','status');error.className='dialog-error';error.setAttribute('role','alert');
  dialog.append(element('h2','Saved allocated clips'),element('p','Independent saved donor snapshots. Retired clips retain their identity and can be previewed or restored. Clips are unassigned; normal Build delivery is pending.'),select,details,actions,status,error);document.body.append(dialog);
  let library=null,held=null,closed=false,stale=false,pending=null,generation=0,controller=null,owner=null;
  const current=()=>{try{return !closed&&!stale&&same(context,animationGlbContext(getContext()));}catch{return false;}};
  const selected=()=>library?.records.find(row=>row.record_id===select.value&&row.entity_id===entityId);
  const release=token=>{if(owner===token){owner=null;setBusy(false);}};
  function invalidate(){generation++;controller?.abort();controller=null;pending=null;if(owner)release(owner);held=null;}
  function updateState(){
    if(!closed&&!stale&&!current()){invalidate();stale=true;status.textContent='Scene, actor or source changed. Reopen the saved clip library.';}
    const row=selected(),blocked=!current()||pending!==null||busy()!==false;
    select.disabled=blocked||!row;inspect.disabled=blocked||!row;reviewButton.disabled=blocked||!row||!library.activation_available;apply.disabled=blocked||!held||held.row!==row;close.disabled=pending==='apply';
    if(row){details.textContent=`${row.animation_id} · ${row.frame_count} frames · ${row.object_count} objects · ${row.active?'Active':'Retired'} · unassigned`;reviewButton.textContent=row.active?'Review retirement':'Review restoration';}
  }
  function dispose(){if(closed)return;closed=true;invalidate();if(dialog.open)dialog.close();dialog.remove();}
  async function post(path,body,signal){const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal});const value=await response.json();if(!response.ok||value?.error)fail(value?.error??'Saved clip request failed.');return value;}
  async function run(kind,work){
    if(!current()||pending!==null||busy()!==false)return false;
    const token={},version=++generation;owner=token;controller=new AbortController();const signal=controller.signal;pending=kind;setBusy(true);error.textContent='';updateState();
    const valid=()=>current()&&version===generation&&!signal.aborted;
    try{return await work(signal,valid);}catch(e){if(valid()&&e?.name!=='AbortError'){error.textContent=e.message??String(e);onError(e);}return false;}
    finally{if(version===generation){controller=null;pending=null;}release(token);updateState();}
  }
  select.onchange=()=>{invalidate();status.textContent='Selection changed. Review before Apply.';updateState();};
  reviewButton.onclick=()=>{const row=selected();if(!row||!library.activation_available)return false;held=null;return run('review',async(signal,valid)=>{
    const request={scene_id:context.sceneId,record_id:row.record_id,active:!row.active,expected_source_key:context.sourceKey};
    const result=await post('/api/animation-record-activation-preview',request,signal);if(!valid()||row!==selected())return false;
    const report=decodeRecordActivationReview(result,request,row);held={request,report,row};status.textContent=`Reviewed ${row.active?'retirement':'restoration'} · not applied. Identity and captured bytes are retained.`;return true;
  });};
  apply.onclick=()=>{const captured=held;if(!captured||captured.row!==selected())return false;return run('apply',async(signal,valid)=>{
    try{const next=await post('/api/animation-record-activation',{...captured.request,review_key:captured.report.review_key},signal);if(!valid()||captured!==held)return false;if(!object(next?.project)||next.project.mode!=='edit')fail('Activation returned invalid project state.');held=null;await onApplied(next);dispose();return true;}
    catch(e){if(valid()){held=null;status.textContent='Change failed. Review again.';}throw e;}
  });};
  inspect.onclick=()=>{const row=selected();if(!row||onPosePreview===null)return false;return run('pose',async(signal,valid)=>{
    const result=await post('/api/animation-record-pose',{scene_id:context.sceneId,record_id:row.record_id,expected_source_key:context.sourceKey},signal);if(!valid()||row!==selected())return false;
    const data=decodeSavedAnimationPose(result,row),returnToEditor=()=>{if(!current()||row!==selected()){dispose();return false;}delete dialog.dataset.poseRetained;if(!dialog.open)dialog.showModal();updateState();return true;};
    dialog.dataset.poseRetained='true';dialog.close();
    try{const result=await onPosePreview(data,{returnToEditor});if(!valid()||result===false){returnToEditor();return false;}return true;}catch(e){returnToEditor();throw e;}
  });};
  close.onclick=()=>{if(pending==='apply')return false;dispose();return true;};dialog.oncancel=e=>{if(pending==='apply')e.preventDefault();};dialog.onclose=()=>{if(!dialog.open&&dialog.dataset.poseRetained!=='true')dispose();};
  dialog.showModal();updateState();
  const ready=run('list',async(signal,valid)=>{const result=await post('/api/animation-record-library',{scene_id:context.sceneId,expected_source_key:context.sourceKey},signal);if(!valid())return false;library=decodeAnimationRecordLibrary(result,context);const rows=library.records.filter(row=>row.entity_id===entityId);for(const row of rows){const option=element('option',`${row.active?'Active':'Retired'} · ${row.frame_count} frames · ${row.record_id}`);option.value=row.record_id;select.append(option);}select.value=rows[0]?.record_id??'';status.textContent=rows.length?'Choose a clip to Preview or review a lifecycle change.':'This actor has no retained allocated clips.';return true;});
  return {dialog,ready,updateState,dispose};
}
