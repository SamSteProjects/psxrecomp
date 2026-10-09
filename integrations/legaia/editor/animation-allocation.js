// Reviewed independent rigid clips; no guessed cadence or runtime assignment.
import {animationGlbContext} from './animation-glb.js';
const hash=value=>typeof value==='string'&&/^[0-9a-f]{64}$/.test(value);
const integer=(value,lo,hi)=>Number.isSafeInteger(value)&&value>=lo&&value<=hi;
const object=value=>value!==null&&typeof value==='object'&&!Array.isArray(value);
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const same=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
const fail=message=>{throw new Error(message);};
const actor=(value,scene)=>typeof value==='string'&&value.startsWith(scene+'/actors/man-p1/')&&/^\d{4}$/.test(value.slice((scene+'/actors/man-p1/').length));
const uuid=value=>typeof value==='string'&&/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(value);

function capturedEntry(entry,scene){
 const keys=['record_id','entity_id','channel_owner_entity_id','model_source_entity_id','donor_animation_id','donor_asset_id','donor_record_sha256','effective_donor_record_sha256','donor_frame_count','object_count','donor_edits','source_frame_indices','edits','record_sha256'];
 if(!object(entry)||Object.keys(entry).length!==keys.length||keys.some(k=>!Object.hasOwn(entry,k))||!uuid(entry.record_id)||['entity_id','channel_owner_entity_id','model_source_entity_id'].some(k=>!actor(entry[k],scene))||!hash(entry.donor_record_sha256)||!hash(entry.effective_donor_record_sha256)||!hash(entry.record_sha256)||!integer(entry.donor_frame_count,1,512)||!integer(entry.object_count,1,64)||!Array.isArray(entry.source_frame_indices)||!integer(entry.source_frame_indices.length,1,512)||entry.source_frame_indices.some(n=>!integer(n,0,entry.donor_frame_count-1)))fail('Captured allocation source has invalid identity or frame bounds.');
 const axes=(rows,count)=>{const seen=new Set();if(!Array.isArray(rows)||rows.length>4096)fail('Captured axis list exceeds bounds.');for(const row of rows){if(!object(row)||Object.keys(row).some(k=>!['frame_index','object_index','translation','rotation_psx'].includes(k))||!integer(row.frame_index,0,count-1)||!integer(row.object_index,0,entry.object_count-1)||seen.has(row.frame_index+':'+row.object_index)||!['translation','rotation_psx'].some(k=>Object.hasOwn(row,k)))fail('Captured axis identity differs from its source.');seen.add(row.frame_index+':'+row.object_index);for(const field of ['translation','rotation_psx'])if(Object.hasOwn(row,field)){const values=row[field];if(!object(values)||!Object.keys(values).length||Object.keys(values).some(k=>!['x','y','z'].includes(k))||Object.values(values).some(n=>!integer(n,field==='translation'?-2048:0,field==='translation'?2047:4080)||field==='rotation_psx'&&n%16))fail('Captured axis value exceeds native bounds.');}}};axes(entry.donor_edits,entry.donor_frame_count);axes(entry.edits,entry.source_frame_indices.length);return entry;
}
export function flattenRetainedSequence(entry,indices,edits){
 const rows=new Map();for(let destination=0;destination<indices.length;destination++)for(const old of entry.edits)if(old.frame_index===indices[destination]){const row=structuredClone(old);row.frame_index=destination;rows.set(destination+':'+row.object_index,row);}
 for(const edit of edits){const key=edit.frame_index+':'+edit.object_index,row=rows.get(key)??{frame_index:edit.frame_index,object_index:edit.object_index};for(const field of ['translation','rotation_psx'])if(Object.hasOwn(edit,field))row[field]={...row[field],...edit[field]};rows.set(key,row);}
 return {source_frame_indices:indices.map(i=>entry.source_frame_indices[i]),edits:[...rows.values()].sort((a,b)=>a.frame_index-b.frame_index||a.object_index-b.object_index)};
}

export function parseAnimationFrameSequence(text,frameCount,maximum=512){
  if(typeof text!=='string'||text.length>8192||!integer(frameCount,1,512)||!integer(maximum,0,512))fail('Choose a bounded source frame sequence.');
  const frames=[];
  for(const token of text.split(',')){
    const match=/^(\d+)(?:-(\d+))?$/.exec(token.trim());
    if(!match)fail('Use comma-separated frame numbers or inclusive ranges, such as 0-9,9-0,0.');
    const first=Number(match[1]),last=Number(match[2]??match[1]);
    if(!integer(first,0,frameCount-1)||!integer(last,0,frameCount-1))fail(`Source frames must be 0 through ${frameCount-1}.`);
    if(frames.length+Math.abs(last-first)+1>maximum)fail('The frame sequence exceeds the remaining allocation budget.');
    const step=first<=last?1:-1;
    for(let frame=first;;frame+=step){frames.push(frame);if(frame===last)break;}
  }
  return frames;
}

export function decodeAnimationAllocationOptions(value,entityId,context){
  context=animationGlbContext(context);
  const prefix='animation://'+context.sceneId.slice(8)+'/scene-anm/';
  if(!object(value)||!['legaia.animation-record-allocation-options.v1','legaia.animation-record-allocation-options.v2'].includes(value.schema_version)||value.entity_id!==entityId||value.scene_id!==context.sceneId||value.project_source_key!==context.sourceKey||!actor(entityId,context.sceneId)||!actor(value.channel_owner_entity_id,context.sceneId)||!actor(value.model_source_entity_id,context.sceneId)||typeof value.donor_animation_id!=='string'||!value.donor_animation_id.startsWith(prefix)||!/^\d{4}$/.test(value.donor_animation_id.slice(prefix.length))||typeof value.donor_asset_id!=='string'||!/^asset:\/\/[A-Za-z0-9_./-]+$/.test(value.donor_asset_id)||!integer(value.donor_frame_count,1,512)||!integer(value.object_count,1,64)||!integer(value.maximum_frame_count,0,512)||!integer(value.remaining_channel_count,0,4096)||!integer(value.remaining_record_count,0,64)||value.maximum_frame_count*value.object_count>value.remaining_channel_count||typeof value.build_available!=='boolean'||value.gameplay_verified!==false)fail('Allocation options differ from the selected actor or current source.');
  if(value.schema_version==='legaia.animation-record-allocation-options.v2'){const entry=capturedEntry(value.source_allocated_entry,context.sceneId);if(value.source_animation_id!=='animation://'+context.sceneId.slice(8)+'/authored-record/'+entry.record_id||value.donor_frame_count!==entry.source_frame_indices.length||value.object_count!==entry.object_count||value.donor_asset_id!==entry.donor_asset_id||value.donor_animation_id!==entry.donor_animation_id||value.channel_owner_entity_id!==entry.channel_owner_entity_id||value.model_source_entity_id!==entry.model_source_entity_id)fail('Allocated source options differ from the frozen donor recipe.');}
  return structuredClone(value);
}

export function decodeAnimationAllocationReview(value,options,request){
  const row=value?.allocation?.allocated_records?.[0],ledger=value?.proposed_ledger,entry=ledger?.records?.at(-1),captured=options.schema_version==='legaia.animation-record-allocation-options.v2',flat=captured?flattenRetainedSequence(options.source_allocated_entry,request.source_frame_indices,request.edits):request;
  if(Object.hasOwn(request,'source_record_id')&&(!captured||request.source_record_id!==options.source_allocated_entry.record_id))fail('Variant source differs from the selected retained clip.');
  if(captured&&(!same(value?.source_allocated_entry,options.source_allocated_entry)||value.source_animation_id!==options.source_animation_id||!same(value.requested_source_frame_indices,request.source_frame_indices)||!same(value.requested_edits,request.edits)))fail('Allocated source capture differs from the reviewed retained poses.');
  if(!object(value)||value.schema_version!==(captured?'legaia.animation-record-allocation-review.v3':'legaia.animation-record-allocation-review.v2')||value.entity_id!==request.entity_id||value.scene_id!==options.scene_id||value.project_source_key!==request.expected_source_key||value.donor_animation_id!==options.donor_animation_id||value.channel_owner_entity_id!==options.channel_owner_entity_id||value.model_source_entity_id!==options.model_source_entity_id||value.donor_asset_id!==options.donor_asset_id||!hash(value.review_key)||!hash(value.candidate_bank_sha256)||value.project_changed!==false||value.gameplay_verified!==false||!object(value.capabilities)||value.capabilities.review!==true||value.capabilities.apply!==true||value.capabilities.build!==options.build_available||value.capabilities.actor_assignment!==false||value.allocation?.candidate_bank_sha256!==value.candidate_bank_sha256||value.allocation?.allocated_records?.length!==1||!uuid(row?.record_id)||row.frame_count!==request.source_frame_indices.length||row.object_count!==options.object_count||!hash(row.candidate_record_sha256)||!object(ledger)||ledger.schema_version!=='legaia.animation-record-ledger.v1'||ledger.source_scene_id!==options.scene_id||!hash(ledger.source_bank_sha256)||!integer(ledger.revision,1,64)||!Array.isArray(ledger.records)||!integer(ledger.records.length,1,64)||!Array.isArray(ledger.removed_record_ids)||entry?.record_id!==row.record_id||entry.record_sha256!==row.candidate_record_sha256||entry.entity_id!==request.entity_id||entry.channel_owner_entity_id!==options.channel_owner_entity_id||entry.model_source_entity_id!==options.model_source_entity_id||entry.donor_animation_id!==options.donor_animation_id||entry.donor_asset_id!==options.donor_asset_id||entry.donor_frame_count!==(captured?options.source_allocated_entry.donor_frame_count:options.donor_frame_count)||entry.object_count!==options.object_count||!same(entry.source_frame_indices,flat.source_frame_indices)||!same(entry.edits,flat.edits)||value.animation_id!=='animation://'+options.scene_id.slice(8)+'/authored-record/'+row.record_id)fail('Allocation review differs from this frame sequence, actor, or source. Review again.');
  if(captured&&!same(entry,{...options.source_allocated_entry,record_id:row.record_id,entity_id:request.entity_id,source_frame_indices:flat.source_frame_indices,edits:flat.edits,record_sha256:row.candidate_record_sha256}))fail('Allocated capture lost its independent frozen Retail recipe.');
  const ids=ledger.records.map(entry=>entry?.record_id);
  if(ids.some(id=>!uuid(id))||new Set(ids).size!==ids.length||ledger.removed_record_ids.includes(row.record_id))fail('Allocated animation identities are invalid.');
  return structuredClone(value);
}

export function decodeAnimationAllocationPose(value,review,options){
  const animation=value?.animation,entry=review.proposed_ledger.records.at(-1);
  if(!object(value)||value.schema_version!=='legaia.model-preview.v1'||value.semantic_id!==options.donor_asset_id||!same(value.report,review)||!object(animation)||animation.semantic_id!==review.animation_id||animation.entity_id!==options.entity_id||animation.representation!=='allocation_preview'||animation.clip_id!=='allocation-preview'||animation.source_clip_id!==options.donor_animation_id||animation.frame_count!==entry.source_frame_indices.length||animation.bone_count!==options.object_count||animation.association?.runtime_assigned!==false||animation.source_record?.record_id!==entry.record_id||animation.source_record?.record_sha256!==entry.record_sha256||animation.source_record?.bank_sha256!==review.candidate_bank_sha256||!Array.isArray(value.frames)||value.frames.length!==animation.frame_count)fail('Pose preview differs from the reviewed unassigned clip.');
  return structuredClone(value);
}

const element=(tag,text)=>{const node=document.createElement(tag);if(text!==undefined)node.textContent=text;return node;};
const button=(label,action)=>{const node=element('button',label);node.type='button';node.dataset.action=action;return node;};

export async function openAnimationAllocationEditor({entityId,getContext,sourceRecordId=null,sourceRecordSha256=null,busy=()=>false,setBusy=()=>{},onError=()=>{},onApplied=()=>{},onPosePreview=null}){
  const context=animationGlbContext(getContext());
  if(!actor(entityId,context.sceneId))fail('Choose an imported actor in the editable scene.');
  if(sourceRecordId!==null&&!uuid(sourceRecordId))fail('Choose an existing retained clip for the variant.');
  if(sourceRecordSha256!==null&&(sourceRecordId===null||!hash(sourceRecordSha256)))fail('Variant source requires the selected retained content hash.');
  const donorRequest=sourceRecordId===null?{}:{source_record_id:sourceRecordId};
  const dialog=element('dialog');dialog.className='project-dialog animation-allocation-dialog';dialog.style.maxWidth='52rem';dialog.style.maxHeight='90vh';dialog.style.overflowY='auto';
  const note=element('p','Create an independent clip from the current donor poses, including an assigned allocated clip. The frame sequence can repeat, reverse or extend source frames. Review and Preview do not apply changes. Apply retains a new clip without changing the actor assignment. Build support depends on the source carrier; gameplay verification remains separate.');note.className='field-note';
  const donor=element('p','Verifying donor…'),label=element('label','Source frame sequence (zero based)'),frames=element('textarea');frames.rows=3;frames.setAttribute('aria-label','Source frame sequence');label.append(frames);
  const help=element('p','Inclusive ranges and single frames, separated by commas: 0-9,9-0,0. Preview playback rate is a viewer choice.');help.className='field-note';
  const inspect=button('Review clip','review'),pose=button('Preview reviewed clip','pose'),apply=button('Apply allocated clip','apply'),close=button('Close','close');pose.hidden=onPosePreview===null;
  const actions=element('div');actions.append(inspect,pose,apply,close);
  const status=element('p','Loading donor…');status.setAttribute('role','status');const error=element('p');error.className='dialog-error';error.setAttribute('role','alert');const summary=element('section');summary.hidden=true;
  dialog.append(element('h2',sourceRecordId===null?'Allocate animation clip':'Create animation clip variant'),note,donor,label,help,actions,status,error,summary);document.body.append(dialog);
  let closed=false,stale=false,pending=null,generation=0,revision=0,controller=null,owner=null,options=null,review=null;
  const current=()=>{try{return !closed&&!stale&&same(context,animationGlbContext(getContext()));}catch{return false;}};
  const accepted=value=>current()&&value===review&&value?.revision===revision;
  const release=token=>{if(owner===token){owner=null;setBusy(false);}};
  function invalidate(){generation++;controller?.abort();controller=null;pending=null;if(owner)release(owner);review=null;summary.hidden=true;summary.replaceChildren();}
  function updateState(){
    if(!closed&&!stale&&!current()){invalidate();stale=true;status.textContent='Project, scene, actor or source changed. Reopen allocation.';}
    const blocked=!current()||pending!==null||busy()!==false;
    frames.disabled=blocked||!options;inspect.disabled=blocked||!options||options.maximum_frame_count===0;pose.disabled=apply.disabled=blocked||!accepted(review);close.disabled=pending==='apply';
  }
  function dispose(){if(closed)return;closed=true;invalidate();if(dialog.open)dialog.close();dialog.remove();}
  async function post(path,body,signal){const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal});const value=await response.json();if(!response.ok||value?.error)fail(value?.error??'Animation request failed.');return value;}
  async function run(kind,work){
    if(!current()||pending!==null||busy()!==false)return false;
    const token={},version=++generation;owner=token;controller=new AbortController();const signal=controller.signal;pending=kind;error.textContent='';setBusy(true);updateState();
    const valid=()=>current()&&generation===version&&!signal.aborted;
    try{return await work(signal,valid,token);}catch(value){if(valid()&&value?.name!=='AbortError'){error.textContent=value?.message??String(value);onError(value);}return false;}
    finally{if(generation===version){pending=null;controller=null;}release(token);updateState();}
  }
  frames.oninput=()=>{revision++;invalidate();error.textContent='';status.textContent='Sequence changed. Review before Preview or Apply.';updateState();};
  inspect.onclick=()=>run('review',async(signal,valid)=>{
    const request={entity_id:entityId,source_frame_indices:parseAnimationFrameSequence(frames.value,options.donor_frame_count,options.maximum_frame_count),edits:[],expected_source_key:context.sourceKey,...donorRequest};
    const value=await post('/api/animation-record-allocation-preview',request,signal);if(!valid())return false;
    const report=decodeAnimationAllocationReview(value,options,request);review={report,request,revision};summary.replaceChildren(element('h3','Reviewed · not applied'),element('p',`${request.source_frame_indices.length} frames · ${options.object_count} rigid objects · independent donor snapshot`),element('p',report.animation_id),element('p',`Save/Open and Undo/Redo supported. ${options.build_available?'Native package Build delivery is supported.':'Build delivery for this carrier is unavailable.'} Assign the retained clip separately through its library. Gameplay remains unverified.`));summary.hidden=false;status.textContent='Review complete. Preview or explicitly Apply.';return true;
  });
  pose.onclick=()=>{if(!accepted(review)||onPosePreview===null)return false;const held=review;return run('pose',async(signal,valid)=>{
    const value=await post('/api/animation-record-allocation-pose-preview',{...held.request,review_key:held.report.review_key},signal);if(!valid()||!accepted(held))return false;
    const data=decodeAnimationAllocationPose(value,held.report,options);
    const returnToEditor=()=>{if(!accepted(held)){dispose();return false;}delete dialog.dataset.poseRetained;if(!dialog.open)dialog.showModal();status.textContent='Review retained. Explicit Apply is required.';updateState();return true;};
    dialog.dataset.poseRetained='true';dialog.close();
    try{const result=await onPosePreview(data,{returnToEditor});if(!valid()||!accepted(held)||result===false){returnToEditor();return false;}return true;}
    catch(value){returnToEditor();throw value;}
  });};
  apply.onclick=()=>{if(!accepted(review))return false;const held=review;return run('apply',async(signal,valid,token)=>{
    let next;
    try{next=await post('/api/animation-record-allocation',{...held.request,review_key:held.report.review_key},signal);if(!object(next?.project)||next.project.mode!=='edit')fail('Allocation returned invalid project state.');}
    catch(value){if(valid()){review=null;summary.hidden=true;status.textContent='Apply failed. Review again.';}throw value;}
    if(!valid()||!accepted(held))return false;review=null;release(token);await onApplied(next,structuredClone({kind:sourceRecordId===null?'allocation':'variant',request:held.request,review:held.report}));dispose();return true;
  });};
  close.onclick=()=>{if(pending==='apply')return false;dispose();return true;};dialog.oncancel=event=>{if(pending==='apply')event.preventDefault();};dialog.onclose=()=>{if(!dialog.open&&dialog.dataset.poseRetained!=='true')dispose();};
  dialog.showModal();updateState();
  const ready=run('options',async(signal,valid)=>{const value=await post('/api/animation-record-allocation-options',{entity_id:entityId,expected_source_key:context.sourceKey,...donorRequest},signal);if(!valid())return false;const decoded=decodeAnimationAllocationOptions(value,entityId,context);if(sourceRecordId!==null&&(decoded.source_allocated_entry?.record_id!==sourceRecordId||sourceRecordSha256!==null&&decoded.source_allocated_entry?.record_sha256!==sourceRecordSha256))fail('Variant options differ from the selected retained clip.');options=decoded;frames.value=options.donor_frame_count===1?'0':`0-${options.donor_frame_count-1}`;donor.textContent=`${options.source_animation_id??options.donor_animation_id} · ${options.donor_frame_count} source frames · ${options.object_count} rigid objects. Donor actor: ${options.channel_owner_entity_id}.`;status.textContent=options.maximum_frame_count?'Choose a sequence, then Review.':'Allocation budget is exhausted.';return true;});
  return {dialog,ready,updateState,dispose};
}
