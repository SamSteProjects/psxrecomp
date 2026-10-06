import {openAnimationSources} from './animation-sources.js';
import {glbAnimationChoices,populateGlbClipSelect,selectedGlbClipIndex} from './animation-glb-clips.js';
// External rigid-channel interchange; preview and review never author the project.
const MAX_GLB=32*1024*1024,MAX_BINDING=128*1024,MAX_AXES=4096*6;
const HASH=/^[0-9a-f]{64}$/;
const object=value=>value!==null&&typeof value==='object'&&!Array.isArray(value)&&[Object.prototype,null].includes(Object.getPrototypeOf(value));
const exact=(value,keys)=>object(value)&&Object.keys(value).length===keys.length&&keys.every(key=>Object.hasOwn(value,key));
const integer=(value,min,max)=>Number.isSafeInteger(value)&&value>=min&&value<=max;
const hash=value=>typeof value==='string'&&HASH.test(value);
const finite=(value,min,max)=>typeof value==='number'&&Number.isFinite(value)&&value>=min&&value<=max;
const text=(value,max=8192)=>typeof value==='string'&&value.length>0&&value.length<=max;
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const clone=value=>structuredClone(value);
const fail=message=>{throw new Error(message);};
const actor=(value,scene)=>typeof value==='string'&&value.startsWith(scene+'/actors/man-p1/')&&/^\d{4}$/.test(value.slice((scene+'/actors/man-p1/').length));
const bindingKeys=['schema_version','entity_id','scene_id','asset_id','animation_id','source_record_sha256','effective_record_sha256','project_source_key','frame_count','object_count','clip_fps','coordinate_conversion','node_names'];
const reviewKeys=['schema_version','entity_id','project_source_key','review_key','candidate_sha256','glb_sha256','changed_axes','frame_count','object_count','maximum_translation_error','maximum_angular_error_degrees','changes','ownership','project_changed','limitations'];
const reviewMetadata=['animation_id','source_record_sha256','effective_record_sha256','fps','sampled_channel_count','quantization','scope','gameplay_verified','file_animation_index'];

export function animationGlbContext(value){
  if(!exact(value,['projectPath','sceneId','mode','sourceKey'])||!text(value.projectPath,32768)||!/^scene:\/\/[A-Za-z0-9_-]{1,128}$/.test(value.sceneId)||value.mode!=='edit'||!hash(value.sourceKey))fail('Animation import requires the current editable scene and source key.');
  return clone(value);
}

export function decodeAnimationGlbBinding(value,entityId,context){
  context=animationGlbContext(context);
  const assigned=value?.schema_version==='legaia.animation-glb-binding.v2',keys=assigned?[...bindingKeys,'channel_owner_entity_id','model_source_entity_id']:bindingKeys;
  if(assigned&&(!actor(value.channel_owner_entity_id,context.sceneId)||!actor(value.model_source_entity_id,context.sceneId)))fail('Assigned clip binding has invalid source witnesses.');
  if(!actor(entityId,context.sceneId)||!exact(value,keys)||!['legaia.animation-glb-binding.v1','legaia.animation-glb-binding.v2'].includes(value.schema_version)||value.entity_id!==entityId||value.scene_id!==context.sceneId||!text(value.asset_id,512)||!/^asset:\/\/[A-Za-z0-9_./-]+$/.test(value.asset_id)||!text(value.animation_id,512)||!value.animation_id.startsWith('animation://'+context.sceneId.slice(8)+'/scene-anm/')||!/^\d{4}$/.test(value.animation_id.split('/').at(-1))||!hash(value.source_record_sha256)||!hash(value.effective_record_sha256)||value.project_source_key!==context.sourceKey||!integer(value.frame_count,1,4096)||!integer(value.object_count,1,64)||value.frame_count*value.object_count>4096||!finite(value.clip_fps,1,120)||value.coordinate_conversion!=='[x,-y,z]; rigid Rz*Ry*Rx'||!Array.isArray(value.node_names)||!same(value.node_names,Array.from({length:value.object_count},(_,index)=>'object-'+index)))fail('The binding does not match this actor, source, or existing rigid clip. Export a fresh binding.');
  if(JSON.stringify(value).length>MAX_BINDING)fail('Animation binding exceeds 128 KiB.');
  return clone(value);
}

export function decodeAnimationGlbReview(value,binding,entityId,context,glbHash,animationIndex=null){
  binding=decodeAnimationGlbBinding(binding,entityId,context);
  if(animationIndex===null?Object.hasOwn(value??{},'file_animation_index'):value?.file_animation_index!==animationIndex||!integer(animationIndex,0,63))fail('Review differs from the selected GLB animation.');
  if(!object(value)||!reviewKeys.every(key=>Object.hasOwn(value,key))||Object.keys(value).some(key=>!reviewKeys.includes(key)&&!reviewMetadata.includes(key))||value.schema_version!=='legaia.animation-glb-review.v1'||value.entity_id!==entityId||value.project_source_key!==context.sourceKey||!hash(value.review_key)||!hash(value.candidate_sha256)||!hash(value.glb_sha256)||value.glb_sha256!==glbHash||value.frame_count!==binding.frame_count||value.object_count!==binding.object_count||!integer(value.changed_axes,0,MAX_AXES)||!Array.isArray(value.changes)||value.changes.length!==value.changed_axes||!finite(value.maximum_translation_error,0,.5)||!finite(value.maximum_angular_error_degrees,0,2.2)||value.project_changed!==false||!Array.isArray(value.limitations)||value.limitations.length>64||value.limitations.some(line=>!text(line)))fail('Animation review differs from the selected files or current source. Review them again.');
  for(const [key,expected] of Object.entries({animation_id:binding.animation_id,source_record_sha256:binding.source_record_sha256,effective_record_sha256:binding.effective_record_sha256,fps:binding.clip_fps,sampled_channel_count:binding.frame_count*binding.object_count,scope:'existing-rigid-animation-channels-only',gameplay_verified:false}))if(Object.hasOwn(value,key)&&value[key]!==expected)fail('Animation review metadata differs from its source binding.');
  if(Object.hasOwn(value,'quantization')){
    const q=value.quantization;
    if(!exact(q,['translation','rotation','rotation_step_degrees','maximum_angular_error_degrees','baseline_equivalence_radians','preserved_rotation_channels','timeline','coordinate_conversion'])||['translation','rotation','timeline','coordinate_conversion'].some(key=>!text(q[key]))||q.rotation_step_degrees!==360/256||q.maximum_angular_error_degrees!==2.2||!finite(q.baseline_equivalence_radians,0,.001)||!integer(q.preserved_rotation_channels,0,binding.frame_count*binding.object_count))fail('Animation quantization metadata is invalid.');
  }
  const identities=new Set();
  for(const row of value.changes){
    const match=/^(translation|rotation_psx)\.([xyz])$/.exec(row?.field);
    const valid=number=>match?.[1]==='translation'?integer(number,-2048,2047):integer(number,0,4080)&&number%16===0;
    const key=JSON.stringify([row?.frame_index,row?.object_index,row?.field]);
    if(!exact(row,['frame_index','object_index','field','before_value','after_value','channel_byte_offset'])||!integer(row.frame_index,0,binding.frame_count-1)||!integer(row.object_index,0,binding.object_count-1)||!match||!valid(row.before_value)||!valid(row.after_value)||row.before_value===row.after_value||row.channel_byte_offset!==8+(row.frame_index*binding.object_count+row.object_index)*8||identities.has(key))fail('Animation review contains invalid or duplicated channel changes.');
    identities.add(key);
  }
  const ownership=value.ownership,owner=binding.channel_owner_entity_id??entityId,ownershipKeys=['actor_axis_count_before','actor_axis_count_after','other_contributors'];if(binding.schema_version==='legaia.animation-glb-binding.v2')ownershipKeys.push('channel_owner_entity_id');
  if(!exact(ownership,ownershipKeys)||binding.schema_version==='legaia.animation-glb-binding.v2'&&ownership.channel_owner_entity_id!==owner||!integer(ownership.actor_axis_count_before,0,MAX_AXES)||!integer(ownership.actor_axis_count_after,0,MAX_AXES)||!Array.isArray(ownership.other_contributors)||ownership.other_contributors.length>512||ownership.other_contributors.some(id=>!actor(id,context.sceneId)||id===owner)||new Set(ownership.other_contributors).size!==ownership.other_contributors.length||!same(ownership.other_contributors,[...ownership.other_contributors].sort()))fail('Animation contribution ownership is invalid.');
  if((value.changed_axes===0)!==(value.candidate_sha256===binding.effective_record_sha256))fail('Animation review changes contradict the effective record hash.');
  return clone(value);
}

export function decodeAnimationGlbPosePreview(value,review,binding,entityId,context,glbHash,animationIndex=null){
  if(!object(value)||value.schema_version!=='legaia.model-preview.v1'||!object(value.animation)||value.animation.entity_id!==entityId||value.animation.representation!=='file_preview'||value.animation.clip_id!=='file-preview'||value.animation.source_clip_id!==binding.animation_id)fail('Pose preview belongs to a different actor or clip.');
  const report=decodeAnimationGlbReview(value.report,binding,entityId,context,glbHash,animationIndex);
  if(!same(report,review))fail('Pose preview differs from the reviewed animation. Review the files again.');
  return clone(value);
}

function glbBytes(value,length){
  if(!text(value,Math.ceil(MAX_GLB/3)*4)||value.length%4!==0||!/^[A-Za-z0-9+/]*={0,2}$/.test(value)||!integer(length,20,MAX_GLB))fail('Animation export has invalid GLB bytes or exceeds 32 MiB.');
  const raw=atob(value),bytes=Uint8Array.from(raw,character=>character.charCodeAt(0));
  if(bytes.length!==length)fail('Animation GLB byte length differs from its export.');
  validateGlb(bytes);
  return bytes;
}
function validateGlb(bytes){
  if(!(bytes instanceof Uint8Array)||bytes.length<20||bytes.length>MAX_GLB)fail('Choose a GLB from 20 bytes to 32 MiB.');
  const view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
  if(view.getUint32(0,true)!==0x46546c67||view.getUint32(4,true)!==2||view.getUint32(8,true)!==bytes.length)fail('Choose a complete glTF 2 binary (.glb) file.');
}
function encode(bytes){let raw='';for(let start=0;start<bytes.length;start+=32768)raw+=String.fromCharCode(...bytes.subarray(start,start+32768));return btoa(raw);}
async function byteHash(bytes){const result=await crypto.subtle.digest('SHA-256',bytes);return Array.from(new Uint8Array(result),value=>value.toString(16).padStart(2,'0')).join('');}
function element(tag,label){const value=document.createElement(tag);if(label!==undefined)value.textContent=label;return value;}
function button(label,action){const value=element('button',label);value.type='button';value.dataset.action=action;return value;}
function download(data,type,filename){
  let url,link;
  try{url=URL.createObjectURL(new Blob([data],{type}));link=element('a');link.href=url;link.download=filename;document.body.append(link);link.click();}
  finally{link?.remove();if(url)URL.revokeObjectURL(url);}
}
function filename(value,fallback){return typeof value==='string'&&value.length>0&&value.length<=160&&!/[\\/\x00-\x1f]/.test(value)?value:fallback;}

/** Explicit export, two chosen files, read-only review/pose preview, then Apply.
 * The parent owns the current context and applies the returned server state.
 */
export async function openAnimationGlbEditor({entityId,getContext,busy,setBusy,onApplied,onError=()=>{},onPosePreview=null}){
  if([getContext,busy,setBusy,onApplied,onError].some(callback=>typeof callback!=='function')||onPosePreview!==null&&typeof onPosePreview!=='function')fail('Animation GLB editor requires source, state, and error callbacks.');
  const context=animationGlbContext(getContext());
  if(!actor(entityId,context.sceneId))fail('Choose an imported actor in the current scene.');
  const dialog=element('dialog');dialog.id='animation-glb-dialog';dialog.className='project-dialog';Object.assign(dialog.style,{width:'min(760px,94vw)',maxHeight:'92vh',overflowY:'auto'});
  const heading=element('div');heading.className='dialog-heading';const close=button('×','close');close.setAttribute('aria-label','Close animation GLB');heading.append(element('h2','Edit animation in a GLB file'),close);
  const note=element('p','Edit the existing rigid objects and frame count. STEP, LINEAR and CUBICSPLINE tracks are sampled into the existing frames. Translation returns to signed 12-bit coordinates and rotation to the retail angle grid. Timing uses your selected export rate; retail playback FPS is unknown.');note.className='field-note';
  const exported=element('section');exported.append(element('h3','Export for external editing'));
  const fps=element('input');fps.type='number';fps.min='1';fps.max='120';fps.step='any';fps.value='15';fps.setAttribute('aria-label','Caller-selected export FPS');Object.assign(fps.style,{width:'90px',margin:'0'});
  const fpsLabel=element('label','Export FPS · caller-selected ');Object.assign(fpsLabel.style,{display:'flex',flexDirection:'row',alignItems:'center',flexWrap:'wrap',gap:'8px'});fpsLabel.append(fps);
  const exportActions=element('div');exportActions.className='dialog-actions';exportActions.style.flexWrap='wrap';const prepare=button('Prepare GLB export','export'),getGlb=button('Download GLB','download-glb'),getBinding=button('Download binding JSON','download-binding');exportActions.append(prepare,getGlb,getBinding);exported.append(fpsLabel,exportActions);
  const imported=element('section');imported.append(element('h3','Review edited files'));
  const glb=element('input');glb.type='file';glb.accept='.glb,model/gltf-binary';glb.setAttribute('aria-label','Edited animation GLB');
  const manifest=element('input');manifest.type='file';manifest.accept='.json,application/json';manifest.setAttribute('aria-label','Source binding JSON');
  for(const [label,input] of [['Edited GLB · maximum 32 MiB',glb],['Binding JSON from the export · maximum 128 KiB',manifest]]){const node=element('label',label);node.append(input);imported.append(node);}
  const recover=element('button','Recover animation sources');recover.type='button';imported.append(recover);recover.onclick=()=>openAnimationSources({getContext,targetId:entityId,kind:'imported',onError,busy,setBusy,onApplied:async next=>{await onApplied(next);dispose();}});
  const clipSelect=element('select');clipSelect.setAttribute('aria-label','Animation in edited GLB');const clipLabel=element('label','Animation in edited GLB');clipLabel.append(clipSelect);imported.append(clipLabel);
  const actions=element('div');actions.className='dialog-actions';actions.style.flexWrap='wrap';const inspect=button('Review selected files','review'),pose=button('Preview reviewed animation','pose'),apply=button('Apply reviewed animation','apply');pose.hidden=onPosePreview===null;actions.append(inspect,pose,apply);imported.append(actions);
  const status=element('p','Choose both edited files to review.');status.setAttribute('role','status');const error=element('p');error.className='dialog-error';error.setAttribute('role','alert');const summary=element('section');summary.hidden=true;
  dialog.append(heading,note,exported,imported,status,error,summary);document.body.append(dialog);
  let closed=false,stale=false,pending=null,generation=0,revision=0,controller=null,busyOwner=null,review=null,candidate=null,exportData=null,retainedClose=false;
  const contextCurrent=()=>{try{return !closed&&!stale&&same(context,animationGlbContext(getContext()));}catch{return false;}};
  const acceptedCurrent=value=>contextCurrent()&&value===review&&value?.revision===revision&&candidate===value?.candidate;
  const release=token=>{if(busyOwner===token){busyOwner=null;setBusy(false);}};
  function abort(){generation++;controller?.abort();controller=null;pending=null;if(busyOwner)release(busyOwner);}
  function invalidate(){abort();review=null;summary.hidden=true;summary.replaceChildren();}
  function showError(value){error.textContent=value?.message??String(value);onError(value instanceof Error?value:new Error(String(value)));}
  function updateState(){
    if(!closed&&!stale&&!contextCurrent()){invalidate();stale=true;candidate=null;exportData=null;status.textContent='Project, scene or source changed. Reopen animation import.';}
    const current=contextCurrent(),blocked=!current||pending!==null||busy()!==false;
    fps.disabled=prepare.disabled=blocked;glb.disabled=manifest.disabled=!current||pending==='apply'||busy()!==false&&pending===null;
    getGlb.disabled=getBinding.disabled=blocked||!exportData;
    recover.disabled=blocked;    clipSelect.disabled=blocked||!candidate;inspect.disabled=blocked||!candidate||candidate.clipChoices.length>1&&clipSelect.value==='';pose.disabled=blocked||!acceptedCurrent(review);apply.disabled=blocked||!acceptedCurrent(review)||review?.report.changed_axes===0;close.disabled=pending==='apply';
  }
  function dispose(){if(closed)return;closed=true;invalidate();candidate=exportData=null;if(dialog.open)dialog.close();dialog.remove();}
  async function run(kind,work){
    if(!contextCurrent()||pending!==null||busy()!==false)return false;
    const token={},ticket=++generation;controller=new AbortController();const signal=controller.signal;pending=kind;busyOwner=token;setBusy(true);error.textContent='';updateState();
    const valid=()=>contextCurrent()&&generation===ticket&&!signal.aborted;
    try{return await work(signal,valid);}catch(value){if(valid()&&value?.name!=='AbortError')showError(value);return false;}
    finally{release(token);if(generation===ticket){controller=null;pending=null;updateState();}}
  }
  async function post(route,body,signal){const response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal});const value=await response.json();if(!response.ok||value?.error)fail(value?.error??'Animation GLB request failed.');return value;}
  function appendReview(report){
    summary.replaceChildren();summary.hidden=false;
    const errorLabel=value=>Number(value.toPrecision(6)).toString();
    summary.append(element('h3','Reviewed · not applied'),element('p',`${report.changed_axes} changed axes · ${report.frame_count} frames · ${report.object_count} rigid objects`),element('p',`Maximum quantization error: ${errorLabel(report.maximum_translation_error)} translation units · ${errorLabel(report.maximum_angular_error_degrees)}° rotation`),element('p',`Clip owner’s authored axes: ${report.ownership.actor_axis_count_before} → ${report.ownership.actor_axis_count_after}. Other contributors: ${report.ownership.other_contributors.length}.`));
    if(report.ownership.channel_owner_entity_id)summary.append(element('p','Shared clip contribution owner: '+report.ownership.channel_owner_entity_id+'. Selected actor: '+entityId+'. Apply edits this clip contribution.'));
    const table=element('table');table.className='operand-review-table';const heading=element('tr');for(const label of ['Frame / object','Axis','Current','Proposed'])heading.append(element('th',label));table.append(heading);
    for(const row of report.changes.slice(0,200)){const tr=element('tr');for(const value of [`${row.frame_index} / ${row.object_index}`,row.field,String(row.before_value),String(row.after_value)])tr.append(element('td',value));table.append(tr);}
    const scroll=element('div');scroll.style.overflowX='auto';scroll.append(table);summary.append(scroll);
    if(report.changes.length>200)summary.append(element('p',`Showing 200 of ${report.changes.length} changed axes.`));
    for(const limitation of report.limitations){const line=element('p',limitation);line.className='field-note';summary.append(line);}
    const details=element('details');details.append(element('summary','Complete reviewed changes and ownership'));const data=element('pre',JSON.stringify({changes:report.changes,ownership:report.ownership},null,2));data.className='diagnostic-detail';Object.assign(data.style,{maxHeight:'240px',overflow:'auto'});details.append(data);summary.append(details);
  }
  async function readFiles(){
    if(!contextCurrent()||pending==='apply')return false;
    revision++;invalidate();candidate=null;error.textContent='';status.textContent='Choose both edited files to review.';updateState();
    const edited=glb.files?.[0],bindingFile=manifest.files?.[0],fileRevision=revision;
    if(!edited||!bindingFile)return false;
    return run('files',async(_signal,valid)=>{
      if(!integer(edited.size,20,MAX_GLB)||!edited.name?.toLowerCase().endsWith('.glb'))fail('Choose an edited .glb file up to 32 MiB.');
      if(!integer(bindingFile.size,1,MAX_BINDING)||!bindingFile.name?.toLowerCase().endsWith('.json'))fail('Choose its binding .json file up to 128 KiB.');
      const [buffer,content]=await Promise.all([edited.arrayBuffer(),bindingFile.text()]);
      if(!valid()||revision!==fileRevision)return false;
      const bytes=new Uint8Array(buffer);validateGlb(bytes);if(bytes.length!==edited.size||content.length>MAX_BINDING)fail('Selected file contents differ from their bounded sizes.');
      const binding=decodeAnimationGlbBinding(JSON.parse(content),entityId,context),glbHash=await byteHash(bytes);
      if(!valid()||revision!==fileRevision)return false;
      const clipChoices=glbAnimationChoices(bytes);populateGlbClipSelect(clipSelect,clipChoices);
      candidate={glb_base64:encode(bytes),binding,glbHash,revision:fileRevision,clipChoices,animation_index:null};status.textContent=`Ready to review ${edited.name} with ${bindingFile.name}.`;return true;
    });
  }
  glb.onchange=manifest.onchange=readFiles;
  clipSelect.onchange=()=>{if(!contextCurrent()||pending!==null||!candidate)return;revision++;invalidate();candidate={...candidate,revision,animation_index:clipSelect.value===''?null:selectedGlbClipIndex(clipSelect,candidate.clipChoices)};status.textContent='Animation selection changed. Review again.';updateState();};
  fps.oninput=()=>{if(!contextCurrent()||pending!==null)return;exportData=null;error.textContent='';updateState();};
  prepare.onclick=()=>run('export',async(signal,valid)=>{
    const clipFps=Number(fps.value);if(!fps.value.trim()||!finite(clipFps,1,120))fail('Choose a caller-selected export rate from 1 to 120 FPS.');
    status.textContent='Preparing source-bound animation export…';const value=await post('/api/animation-glb-export',{entity_id:entityId,clip_fps:clipFps},signal);if(!valid())return false;
    const binding=decodeAnimationGlbBinding(value?.binding,entityId,context);if(binding.clip_fps!==clipFps||!object(value.audit))fail('Export differs from the selected rate or binding.');
    const bytes=glbBytes(value.glb_base64,value.byte_length);exportData={bytes,binding,filename:filename(value.filename,'animation.glb'),bindingFilename:filename(value.binding_filename,filename(value.filename,'animation.glb').replace(/\.glb$/i,'.binding.json'))};status.textContent='Export ready. Download both files and retain the binding JSON for review.'+(binding.channel_owner_entity_id?' Shared clip owner: '+binding.channel_owner_entity_id+'.':'');return true;
  });
  for(const [control,key] of [[getGlb,'glb'],[getBinding,'binding']])control.onclick=()=>{if(control.disabled||!contextCurrent()||!exportData||busy()!==false)return false;try{if(key==='glb')download(exportData.bytes,'model/gltf-binary',exportData.filename);else download(JSON.stringify(exportData.binding,null,2)+'\n','application/json',exportData.bindingFilename);error.textContent='';return true;}catch(value){showError(value);return false;}};
  const body=value=>({entity_id:entityId,glb_base64:value.glb_base64,binding:clone(value.binding),...(value.animation_index===null?{}:{animation_index:value.animation_index})});
  inspect.onclick=()=>{
    if(inspect.disabled||!candidate)return false;review=null;summary.hidden=true;const accepted=candidate,fileRevision=revision;
    return run('review',async(signal,valid)=>{status.textContent='Reviewing selected rigid channels…';const value=await post('/api/animation-glb-preview',body(accepted),signal);if(!valid()||revision!==fileRevision||candidate!==accepted)return false;const report=decodeAnimationGlbReview(value,accepted.binding,entityId,context,accepted.glbHash,accepted.animation_index);review={report,candidate:accepted,revision:fileRevision};appendReview(report);status.textContent=report.changed_axes?'Review complete. Explicit Apply is required.':'The files produce no effective channel changes.';return true;});
  };
  pose.onclick=()=>{
    if(pose.disabled||!acceptedCurrent(review)||onPosePreview===null)return false;const accepted=review;
    return run('pose',async(signal,valid)=>{
      status.textContent='Preparing reviewed pose preview…';const value=await post('/api/animation-glb-pose-preview',body(accepted.candidate),signal);if(!valid()||!acceptedCurrent(accepted))return false;const data=decodeAnimationGlbPosePreview(value,accepted.report,accepted.candidate.binding,entityId,context,accepted.candidate.glbHash,accepted.candidate.animation_index);
      const returnToEditor=()=>{if(!acceptedCurrent(accepted)){dispose();return false;}if(!dialog.open)dialog.showModal();status.textContent='Review retained. Explicit Apply is required.';updateState();return true;};
      const result=await onPosePreview(data,{returnToEditor});if(!valid()||!acceptedCurrent(accepted)||result===false)return false;retainedClose=true;dialog.close();return true;
    });
  };
  apply.onclick=()=>{
    if(apply.disabled||!acceptedCurrent(review)||!review.report.changed_axes)return false;const accepted=review;
    return run('apply',async(signal,valid)=>{
      status.textContent='Applying reviewed animation…';let state;
      try{state=await post('/api/animation-glb-import',{...body(accepted.candidate),review_key:accepted.report.review_key},signal);if(!object(state)||!object(state.project)||state.project.mode!=='edit')fail('Animation import returned invalid project state.');}
      catch(value){if(valid()){review=null;summary.hidden=true;status.textContent='Apply failed. Review the selected files again.';}throw value;}
      if(!valid()||!acceptedCurrent(accepted))return false;review=null;candidate=null;summary.hidden=true;await onApplied(state);if(!closed)dispose();return true;
    });
  };
  close.onclick=()=>{if(pending==='apply')return false;dispose();return true;};dialog.oncancel=event=>{if(pending==='apply'){event.preventDefault();status.textContent='Apply is in progress; wait for its result.';}};dialog.onclose=()=>{if(retainedClose){retainedClose=false;return;}dispose();};
  dialog.showModal();updateState();return {dialog,ready:Promise.resolve(true),updateState,dispose};
}
