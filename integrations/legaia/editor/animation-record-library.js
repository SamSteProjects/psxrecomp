import {validateRetainedAxes} from './animation-record-edit.js';
import {animationGlbContext} from './animation-glb.js';
const object=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
const hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
const uuid=v=>typeof v==='string'&&/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(v);
const integer=(v,a,b)=>Number.isSafeInteger(v)&&v>=a&&v<=b;
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const fail=message=>{throw new Error(message);};
const actor=(id,scene)=>typeof id==='string'&&id.startsWith(scene+'/actors/man-p1/')&&/^\d{4}$/.test(id.slice((scene+'/actors/man-p1/').length));
export function allocatedAnimationExportRequest(animation,context,frameIndex,clipFps=null){
  context=animationGlbContext(context);
  const representation=animation?.representation,record=animation?.source_record;
  if(!['allocated_record','allocated_assignment_preview','allocated_initial_assignment'].includes(representation)||!uuid(record?.record_id)||!hash(record.record_sha256))fail('Export requires a retained allocated clip identity.');
  const request={scene_id:context.sceneId,record_id:record.record_id,expected_source_key:context.sourceKey,representation};
  if(representation==='allocated_assignment_preview'){
    const review=animation.assignment_proposal;
    if(review?.project_source_key!==context.sourceKey||review.record_id!==record.record_id||review.proposed_component?.record_sha256!==record.record_sha256||!hash(review.review_key)||!actor(review.entity_id,context.sceneId))fail('Assignment export Review is stale or differs from the previewed record.');
    request.entity_id=review.entity_id;request.review_key=review.review_key;
  }else if(representation==='allocated_initial_assignment'){
    if(animation.authored_assignment?.record_id!==record.record_id||animation.authored_assignment.record_sha256!==record.record_sha256||animation.authored_assignment.scene_id!==context.sceneId||!actor(animation.entity_id,context.sceneId))fail('Assigned export differs from its retained identity.');
    request.entity_id=animation.entity_id;
  }else if(animation.saved_record?.record_id!==record.record_id||animation.saved_record.record_sha256!==record.record_sha256)fail('Saved export differs from its captured record.');
  if(clipFps===null){if(!integer(frameIndex,0,animation.frame_count-1))fail('Choose a retained animation frame.');request.frame_index=frameIndex;}
  else{if(typeof clipFps!=='number'||!Number.isFinite(clipFps)||clipFps<1||clipFps>120)fail('Choose an explicit clip rate from 1 to 120 fps.');request.clip_fps=clipFps;}
  return request;
}
export function decodeAnimationRecordLibrary(value,context){
  context=animationGlbContext(context);
  if(!object(value)||value.schema_version!=='legaia.animation-record-library.v1'||value.scene_id!==context.sceneId||value.project_source_key!==context.sourceKey||!integer(value.revision,0,64)||!Array.isArray(value.records)||value.records.length>64||typeof value.activation_available!=='boolean'||value.activation_available!==(value.revision<64)||typeof value.build_available!=='boolean'||value.gameplay_verified!==false)fail('Saved clip library differs from the current scene source.');
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
export function decodeAllocatedAssignmentReview(value,request,row,before=null){
  const clear=request.record_id===null,component=value?.proposed_component;
  if(!object(value)||value.schema_version!=='legaia.allocated-animation-assignment-review.v1'||value.entity_id!==request.entity_id||value.scene_id!==request.entity_id.split('/actors/')[0]||value.project_source_key!==request.expected_source_key||value.record_id!==request.record_id||!hash(value.review_key)||!hash(value.candidate_man_sha256)||!same(value.before,before)||value.project_changed!==false||value.gameplay_verified!==false||typeof value.project_change!=='boolean'||value.capabilities?.apply!==true||typeof value.capabilities?.build_assignment!=='boolean'||!integer(value.native_animation_id,1,255)||!Array.isArray(value.changes)||value.changes.length>2||!Array.isArray(value.limitations)||value.limitations.length>16||value.limitations.some(s=>typeof s!=='string'||s.length>8192))fail('Initial assignment Review differs from the actor, retained clip or current source.');
  if(clear){if(!before||component!==null||value.animation_id!==null||value.capabilities.pose_preview!==false)fail('Clear Review does not restore the inherited initial clip.');}
  else if(!row?.active||!object(component)||Object.keys(component).length!==4||component.scene_id!==value.scene_id||component.record_id!==row.record_id||component.record_sha256!==row.record_sha256||component.model_asset_id!==row.donor_asset_id||value.animation_id!==row.animation_id||value.channel_owner_entity_id!==row.channel_owner_entity_id||value.frame_count!==row.frame_count||value.object_count!==row.object_count||!integer(value.native_record_index,0,254)||value.native_animation_id!==value.native_record_index+1||!hash(value.effective_bank_sha256)||value.capabilities.pose_preview!==true)fail('Initial assignment Review differs from the captured model, record or selector.');
  for(const change of value.changes)if(!object(change)||!['model_index','animation_id'].includes(change.field)||!integer(change.decoded_byte_offset,0,4*1024*1024)||!integer(change.before_byte,0,255)||!integer(change.after_byte,0,255))fail('Invalid initial header change audit.');
  return structuredClone(value);
}
export function decodeAllocatedAssignmentPose(value,report,row){
  const a=value?.animation;
  if(value?.schema_version!=='legaia.model-preview.v1'||value.semantic_id!==row.donor_asset_id||a?.representation!=='allocated_assignment_preview'||a.clip_id!=='allocated-assignment-preview'||a.entity_id!==report.entity_id||!same(a.assignment_proposal,report)||a.semantic_id!==row.animation_id||a.source_record?.record_id!==row.record_id||a.source_record?.record_sha256!==row.record_sha256||a.frame_count!==row.frame_count||a.bone_count!==row.object_count||!Array.isArray(value.frames)||value.frames.length!==row.frame_count)fail('Proposed initial pose differs from the reviewed assignment.');
  return structuredClone(value);
}
export function decodeAnimationRecordDuplicateReview(value,request,row,library){
  const source=value?.source_entry,copy=value?.duplicate_entry,ledger=value?.proposed_ledger;
  if(value?.schema_version!=='legaia.animation-record-duplicate-review.v1'||value.scene_id!==request.scene_id||value.record_id!==row.record_id||value.project_source_key!==request.expected_source_key||!hash(value.review_key)||!hash(value.effective_bank_sha256)||!hash(value.candidate_bank_sha256)||value.project_changed!==false||value.gameplay_verified!==false||value.assignments_changed!==false||value.source_active!==row.active||!object(source)||source.record_id!==row.record_id||source.record_sha256!==row.record_sha256||source.entity_id!==row.entity_id||source.channel_owner_entity_id!==row.channel_owner_entity_id||source.model_source_entity_id!==row.model_source_entity_id||source.donor_animation_id!==row.donor_animation_id||source.donor_asset_id!==row.donor_asset_id||source.object_count!==row.object_count||source.source_frame_indices?.length!==row.frame_count||!uuid(copy?.record_id)||library.records.some(r=>r.record_id===copy.record_id)||!same(copy,{...source,record_id:copy.record_id})||ledger?.schema_version!=='legaia.animation-record-ledger.v1'||ledger.source_scene_id!==request.scene_id||!hash(ledger.source_bank_sha256)||ledger.revision!==library.revision+1||ledger.records?.length!==library.records.length+1||!same(ledger.records?.at(-1),copy)||!Array.isArray(ledger.removed_record_ids)||ledger.removed_record_ids.includes(copy.record_id)||ledger.removed_record_ids.includes(row.record_id)===row.active)fail('Duplicate Review differs from this retained clip or current source.');
  const keys=['record_id','entity_id','channel_owner_entity_id','model_source_entity_id','donor_animation_id','donor_asset_id','donor_record_sha256','effective_donor_record_sha256','donor_frame_count','object_count','donor_edits','source_frame_indices','edits','record_sha256'].sort();
  for(const entry of ledger.records){
    if(!object(entry)||!same(Object.keys(entry).sort(),keys)||!uuid(entry.record_id)||!actor(entry.entity_id,request.scene_id)||!actor(entry.channel_owner_entity_id,request.scene_id)||!actor(entry.model_source_entity_id,request.scene_id)||!hash(entry.donor_record_sha256)||!hash(entry.effective_donor_record_sha256)||!hash(entry.record_sha256)||!integer(entry.donor_frame_count,1,512)||!integer(entry.object_count,1,64)||!Array.isArray(entry.source_frame_indices)||!integer(entry.source_frame_indices.length,1,512)||entry.source_frame_indices.some(n=>!integer(n,0,entry.donor_frame_count-1)))fail('Duplicate Review contains an invalid frozen donor recipe.');
    validateRetainedAxes(entry.donor_edits,entry.donor_frame_count,entry.object_count);validateRetainedAxes(entry.edits,entry.source_frame_indices.length,entry.object_count);
  }
  if(new Set(ledger.records.map(e=>e.record_id)).size!==ledger.records.length||ledger.records.length>64||ledger.revision>64||ledger.records.reduce((sum,e)=>sum+e.source_frame_indices.length*e.object_count,0)>4096||new Set(ledger.removed_record_ids).size!==ledger.removed_record_ids.length||ledger.removed_record_ids.some(id=>!ledger.records.some(e=>e.record_id===id)))fail('Duplicate Review exceeds retained identity or channel budgets.');
  const projected=ledger.records.slice(0,-1);
  for(const existing of library.records){const entry=projected.find(e=>e.record_id===existing.record_id);if(!entry||entry.record_sha256!==existing.record_sha256||entry.entity_id!==existing.entity_id||entry.donor_asset_id!==existing.donor_asset_id||entry.object_count!==existing.object_count||entry.source_frame_indices?.length!==existing.frame_count||ledger.removed_record_ids.includes(existing.record_id)===existing.active)fail('Duplication changed an existing retained clip.');}
  return structuredClone(value);
}
export function qualifyRetainedLibraryRow(library,expected){
  const row=library?.records?.find(r=>r.record_id===expected?.record_id);
  if(!row||Object.keys(row).length!==Object.keys(expected).length||Object.keys(row).some(k=>row[k]!==expected[k]))fail('Retained clip differs from the inspected asset. Refresh assets.');
  return structuredClone(row);
}
const element=(tag,text)=>{const node=document.createElement(tag);if(text!==undefined)node.textContent=text;return node;};
const button=(label,action)=>{const node=element('button',label);node.type='button';node.dataset.action=action;return node;};
export async function openAnimationRecordLibrary({entityId,getContext,assignment=null,modelAssetId=null,retainedRecord=null,assetAssignment=false,duplicateOnly=false,getLabel=()=>null,busy=()=>false,setBusy=()=>{},onApplied=()=>{},onPosePreview=null,onEdit=null,onGlb=null,onError=()=>{}}){
  const context=animationGlbContext(getContext());
  if(!actor(entityId,context.sceneId))fail('Choose an imported actor in the editable scene.');
  if(typeof assetAssignment!=='boolean'||assetAssignment&&(retainedRecord===null||retainedRecord.active!==true))fail('Asset assignment requires an active inspected retained record.');
  if(typeof duplicateOnly!=='boolean'||duplicateOnly&&(assetAssignment||!retainedRecord?.active||assignment?.record_id!==retainedRecord.record_id||assignment?.record_sha256!==retainedRecord.record_sha256||assignment?.model_asset_id!==retainedRecord.donor_asset_id||assignment?.scene_id!==context.sceneId))fail('Assigned clip duplication requires its exact active record, hash, model and scene.');
  if(retainedRecord!==null&&!assetAssignment&&!duplicateOnly&&retainedRecord.entity_id!==entityId)fail('Retained lifecycle owner differs from its inspected capture.');
  const dialog=element('dialog');dialog.className='project-dialog';dialog.style.maxWidth='52rem';dialog.style.maxHeight='90vh';dialog.style.overflowY='auto';
  const select=element('select');select.setAttribute('aria-label','Saved allocated clip');Object.assign(select.style,{width:'100%',maxWidth:'100%',minWidth:'0'});
  const inspect=button('Preview saved clip','pose'),reviewButton=button('Review retirement','review'),apply=button('Apply reviewed change','apply'),close=button('Close','close');inspect.hidden=onPosePreview===null||assetAssignment;reviewButton.hidden=assetAssignment||duplicateOnly;
  const duplicate=button('Review independent duplicate','duplicate');duplicate.hidden=assetAssignment;
  const actions=element('div');actions.className='dialog-actions';Object.assign(actions.style,{flexWrap:'wrap',justifyContent:'flex-start'});actions.append(inspect,reviewButton,duplicate,apply,close);
  const assign=button('Review initial assignment','assign'),clearAssignment=button('Review clear assignment','clear-assignment'),previewAssignment=button('Preview reviewed assignment','assignment-pose');previewAssignment.hidden=onPosePreview===null;
  if(retainedRecord!==null&&!assetAssignment){assign.hidden=clearAssignment.hidden=previewAssignment.hidden=true;}
  if(assetAssignment)clearAssignment.hidden=true;
  actions.append(assign,clearAssignment,previewAssignment);
  const editContent=button('Edit retained content','edit-content');editContent.hidden=onEdit===null;actions.append(editContent);
  const glbContent=button('Edit retained GLB','edit-glb');glbContent.hidden=onGlb===null;actions.append(glbContent);
  const details=element('p'),status=element('p','Verifying retained clips…'),error=element('p');status.setAttribute('role','status');error.className='dialog-error';error.setAttribute('role','alert');for(const node of [details,status,error])node.style.overflowWrap='anywhere';
  dialog.append(element('h2',duplicateOnly?'Duplicate assigned clip':assetAssignment?'Retained clip initial assignment':retainedRecord!==null?'Retained clip lifecycle':'Saved allocated clips'),element('p',duplicateOnly?'Create an independent active copy of this assigned clip. The original record and actor assignment stay intact. Review before Apply; the copy starts unassigned. Gameplay remains unverified.':assetAssignment?'Review this retained asset as the target actor initial clip. Exact captured-model compatibility is checked by Review; retargeting is unsupported.':retainedRecord!==null?'Review retirement or restoration of this retained asset. Identity and captured bytes are preserved. Existing authored initial assignments must be cleared before retirement. Gameplay remains unverified.':'Independent saved donor snapshots. Review an active clip as this actor’s initial animation, or review retirement/restoration separately. Initial headers can be changed later by scripts. Playback and gameplay remain unverified.'),element('p',assetAssignment?`Target actor: ${entityId}`:retainedRecord!==null?'Lifecycle changes do not assign actors.':assignment?`Current allocated initial clip: ${assignment.record_id}`:'Current initial clip: inherited/imported'),select,details,actions,status,error);document.body.append(dialog);
  let library=null,held=null,closed=false,stale=false,pending=null,generation=0,controller=null,owner=null;
  const current=()=>{try{return !closed&&!stale&&same(context,animationGlbContext(getContext()));}catch{return false;}};
  const allowed=row=>retainedRecord!==null?row.record_id===retainedRecord.record_id:modelAssetId?row.donor_asset_id===modelAssetId:row.entity_id===entityId;
  const selected=()=>library?.records.find(row=>row.record_id===select.value&&allowed(row));
  const release=token=>{if(owner===token){owner=null;setBusy(false);}};
  function invalidate(){generation++;controller?.abort();controller=null;pending=null;if(owner)release(owner);held=null;}
  function updateState(){
    if(!closed&&!stale&&!current()){invalidate();stale=true;status.textContent='Scene, actor or source changed. Reopen the saved clip library.';}
    const row=selected(),blocked=!current()||pending!==null||busy()!==false;
    select.disabled=blocked||!row;inspect.disabled=blocked||!row;reviewButton.disabled=blocked||!row||!library.activation_available;apply.disabled=blocked||!held||held.row!==row||held.report.project_change===false;close.disabled=pending==='apply';
    assign.disabled=blocked||retainedRecord!==null&&!assetAssignment||!row?.active;clearAssignment.disabled=blocked||retainedRecord!==null||!assignment;previewAssignment.disabled=blocked||retainedRecord!==null&&!assetAssignment||held?.kind!=='assignment'||!held.row||held.request.record_id===null;
    editContent.disabled=blocked||!row;
    glbContent.disabled=blocked||!row;
    duplicate.disabled=blocked||assetAssignment||!row||!library?.activation_available||library.records.length>=64||library.records.reduce((sum,r)=>sum+r.frame_count*r.object_count,0)+(row?.frame_count??0)*(row?.object_count??0)>4096;
    if(row){details.textContent=`${row.animation_id} · ${row.frame_count} frames · ${row.object_count} objects · ${row.active?'Active':'Retired'} · ${assignment?.record_id===row.record_id?'assigned as this actor’s initial clip':'retained capture'}`;reviewButton.textContent=row.active?'Review retirement':'Review restoration';}
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
  reviewButton.onclick=()=>{const row=selected();if(assetAssignment||duplicateOnly||!row||!library.activation_available)return false;held=null;return run('review',async(signal,valid)=>{
    const request={scene_id:context.sceneId,record_id:row.record_id,active:!row.active,expected_source_key:context.sourceKey};
    const result=await post('/api/animation-record-activation-preview',request,signal);if(!valid()||row!==selected())return false;
    const report=decodeRecordActivationReview(result,request,row);held={kind:'activation',request,report,row};status.textContent=`Reviewed ${row.active?'retirement':'restoration'} · not applied. Identity and captured bytes are retained.`;return true;
  });};
  duplicate.onclick=()=>{const row=selected();if(duplicate.disabled||assetAssignment||!row)return false;held=null;return run('duplicate-review',async(signal,valid)=>{
    const request={scene_id:context.sceneId,record_id:row.record_id,expected_source_key:context.sourceKey};
    const value=await post('/api/animation-record-duplicate-review',request,signal);if(!valid()||row!==selected())return false;
    const report=decodeAnimationRecordDuplicateReview(value,request,row,library);held={kind:'duplicate',request,report,row};
    status.textContent=`Reviewed independent duplicate ${report.duplicate_entry.record_id} · identical native content · not applied. Source clip and actor assignments stay intact. The new clip is active and unassigned; edit or assign it after Apply.`;return true;
  });};
  apply.onclick=()=>{const captured=held;if(!captured||captured.row!==selected())return false;return run('apply',async(signal,valid)=>{
    try{const next=await post(captured.kind==='assignment'?'/api/allocated-animation-assignment':captured.kind==='duplicate'?'/api/animation-record-duplicate':'/api/animation-record-activation',{...captured.request,review_key:captured.report.review_key},signal);if(!valid()||captured!==held)return false;if(!object(next?.project)||next.project.mode!=='edit')fail('Change returned invalid project state.');held=null;await onApplied(next,structuredClone({kind:captured.kind,request:captured.request,review:captured.report}));dispose();return true;}
    catch(e){if(valid()){held=null;status.textContent='Change failed. Review again.';}throw e;}
  });};
  function reviewAssignment(clear){
    const row=selected();if(duplicateOnly||retainedRecord!==null&&!assetAssignment||assetAssignment&&clear||(clear&&!assignment)||(!clear&&!row?.active))return false;held=null;
    return run('assignment-review',async(signal,valid)=>{
      const request={entity_id:entityId,record_id:clear?null:row.record_id,expected_source_key:context.sourceKey};
      const value=await post('/api/allocated-animation-assignment-review',request,signal);if(!valid()||row!==selected())return false;
      const report=decodeAllocatedAssignmentReview(value,request,row,assignment);held={kind:'assignment',request,report,row};
      status.textContent=`${report.project_change?'Reviewed · not applied':'Already assigned · no change'} · ${clear?'Restore inherited initial clip':row.animation_id} · native selector ${report.native_animation_id} · ${report.capabilities.build_assignment?'Build supported':'Build combination unsupported'}. ${report.limitations.join(' ')}`;return true;
    });
  }
  assign.onclick=()=>reviewAssignment(false);clearAssignment.onclick=()=>reviewAssignment(true);
  previewAssignment.onclick=()=>{const captured=held;if(captured?.kind!=='assignment'||!captured.row||captured.request.record_id===null||onPosePreview===null)return false;return run('assignment-pose',async(signal,valid)=>{
    const value=await post('/api/allocated-animation-assignment-pose',{...captured.request,review_key:captured.report.review_key},signal);if(!valid()||held!==captured)return false;
    const data=decodeAllocatedAssignmentPose(value,captured.report,captured.row);
    const returnToEditor=()=>{if(!current()||held!==captured){dispose();return false;}delete dialog.dataset.poseRetained;if(!dialog.open)dialog.showModal();updateState();return true;};
    dialog.dataset.poseRetained='true';dialog.close();try{const result=await onPosePreview(data,{returnToEditor});if(!valid()||result===false){returnToEditor();return false;}return true;}catch(e){returnToEditor();throw e;}
  });};
  inspect.onclick=()=>{const row=selected();if(!row||onPosePreview===null)return false;return run('pose',async(signal,valid)=>{
    const result=await post('/api/animation-record-pose',{scene_id:context.sceneId,record_id:row.record_id,expected_source_key:context.sourceKey},signal);if(!valid()||row!==selected())return false;
    const data=decodeSavedAnimationPose(result,row),returnToEditor=()=>{if(!current()||row!==selected()){dispose();return false;}delete dialog.dataset.poseRetained;if(!dialog.open)dialog.showModal();updateState();return true;};
    dialog.dataset.poseRetained='true';dialog.close();
    try{const result=await onPosePreview(data,{returnToEditor});if(!valid()||result===false){returnToEditor();return false;}return true;}catch(e){returnToEditor();throw e;}
  });};
  close.onclick=()=>{if(pending==='apply')return false;dispose();return true;};dialog.oncancel=e=>{if(pending==='apply')e.preventDefault();};dialog.onclose=()=>{if(!dialog.open&&dialog.dataset.poseRetained!=='true')dispose();};
  editContent.onclick=async()=>{const row=selected();if(!row||!current()||pending!==null||busy()!==false||onEdit===null)return false;dispose();try{await onEdit(row);return true;}catch(e){onError(e);return false;}};
  glbContent.onclick=async()=>{const row=selected();if(!row||!current()||pending!==null||busy()!==false||onGlb===null)return false;dispose();try{await onGlb(row);return true;}catch(e){onError(e);return false;}};
  dialog.showModal();updateState();
  const ready=run('list',async(signal,valid)=>{const result=await post('/api/animation-record-library',{scene_id:context.sceneId,expected_source_key:context.sourceKey},signal);if(!valid())return false;const verified=decodeAnimationRecordLibrary(result,context);if(retainedRecord!==null)qualifyRetainedLibraryRow(verified,retainedRecord);library=verified;const rows=library.records.filter(allowed);for(const row of rows){const option=element('option',`${row.active?'Active':'Retired'} · ${row.frame_count} frames · ${getLabel(row.animation_id)??row.record_id}`);option.value=row.record_id;select.append(option);}select.value=rows.find(r=>r.record_id===assignment?.record_id)?.record_id??rows[0]?.record_id??'';status.textContent=duplicateOnly?'Verified assigned clip. Review its independent duplicate; the original record and assignment stay intact.':assetAssignment?'Verified retained asset. Review its initial assignment to the target actor.':retainedRecord!==null?'Verified retained asset. Preview or review its lifecycle change.':rows.length?'Choose a clip to Preview, review initial assignment, or review a lifecycle change.':'No retained clips match this actor’s model.';return true;});
  return {dialog,ready,updateState,dispose};
}
