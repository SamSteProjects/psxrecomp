import {qualifyWorldAnimationGlb,worldAnimationGlbFiles} from './worldmap-animation-glb.js';
import {createWorldAnimationSampler,mountWorldAnimationPlayback} from './worldmap-animation-playback.js';
import {qualifyWorldAnimationCurrent,qualifyWorldAnimationEdit} from './worldmap-animation-current.js';
import {qualifyWorldAnimationBuildPose} from './worldmap-animation-build-navigation.js';
const node=(tag,text)=>{const e=document.createElement(tag);if(text)e.textContent=text;return e;};

function validateWorldChannel(held,objectIndex,values){
  const p=held?.preview;
  if(!p||!Number.isSafeInteger(objectIndex)||objectIndex<0||objectIndex>=p.channel_count)throw Error('Choose an existing rigid object channel.');
  for(const field of ['translation','rotation_psx']){
    const axes=values?.[field];if(!axes||Object.keys(axes).sort().join(',')!=='x,y,z')throw Error('Provide every translation and rotation axis.');
    for(const value of Object.values(axes))if(!Number.isSafeInteger(value)||(field==='translation'?value < -2048||value > 2047:value < 0||value > 4080||value%16))throw Error('Translation must be -2048..2047; rotation must be 0..4080 in exact steps of 16.');
  }
  return p;
}

// A single-channel draft keeps all other saved frames/objects in the shared record.
export function worldAnimationChannelDraft(held,objectIndex,values){
  const p=validateWorldChannel(held,objectIndex,values),index=String(p.record_index).padStart(4,'0'),rows=structuredClone(held.binding?.entries[index]?.edits??[]).filter(e=>e.frame_index!==p.frame_index||e.object_index!==objectIndex);
  rows.push({frame_index:p.frame_index,object_index:objectIndex,translation:{...values.translation},rotation_psx:{...values.rotation_psx}});
  if(rows.length>4096)throw Error('This record exceeds the saved channel budget.');
  return rows.sort((a,b)=>a.frame_index-b.frame_index||a.object_index-b.object_index);
}

// Hold one explicit pose across an inclusive range; no native interpolation is inferred.
export function worldAnimationRangeDraft(held,objectIndex,values,start,end){
  const p=held?.preview;
  if(!p||!Number.isSafeInteger(p.frame_index)||!Number.isSafeInteger(p.frame_count)||p.frame_count<1||p.frame_count>512||!Number.isSafeInteger(start)||!Number.isSafeInteger(end)||start<0||end<start||end>=p.frame_count||p.frame_index<start||p.frame_index>end)throw Error('Choose an inclusive frame range within the clip that includes the inspected frame.');
  validateWorldChannel(held,objectIndex,values);
  const index=String(p.record_index).padStart(4,'0'),rows=structuredClone(held.binding?.entries[index]?.edits??[]).filter(e=>e.object_index!==objectIndex||e.frame_index<start||e.frame_index>end);
  for(let frame=start;frame<=end;frame++)rows.push({frame_index:frame,object_index:objectIndex,translation:{...values.translation},rotation_psx:{...values.rotation_psx}});
  if(rows.length>4096)throw Error('This range exceeds the saved channel budget.');
  return rows.sort((a,b)=>a.frame_index-b.frame_index||a.object_index-b.object_index);
}

// Preserve each Current frame's motion by adding the inspected-pose delta.
export async function worldAnimationOffsetRangeDraft(held,objectIndex,values,start,end){
  const p=validateWorldChannel(held,objectIndex,values);
  // Reuse range admission without mutating the held receipt.
  worldAnimationRangeDraft(held,objectIndex,values,start,end);
  const sampler=await createWorldAnimationSampler(p,held.source.current_model_geometry),anchor=p.object_transforms[objectIndex];
  const delta=Object.fromEntries(['translation','rotation_psx'].map(field=>[field,[...'xyz'].map((axis,i)=>values[field][axis]-anchor[field][i])]));
  const index=String(p.record_index).padStart(4,'0'),rows=structuredClone(held.binding?.entries[index]?.edits??[]).filter(e=>e.object_index!==objectIndex||e.frame_index<start||e.frame_index>end);
  for(let frame=start;frame<=end;frame++){
    const source=sampler.sample(frame).object_transforms[objectIndex],pose={};
    for(const field of ['translation','rotation_psx'])pose[field]=Object.fromEntries([...'xyz'].map((axis,i)=>{
      let value=source[field][i]+delta[field][i];
      if(field==='rotation_psx')value=((value%4096)+4096)%4096;
      else if(value < -2048||value > 2047)throw Error(`Offset exceeds native translation capacity at frame ${frame}, axis ${axis.toUpperCase()}.`);
      return [axis,value];
    }));
    rows.push({frame_index:frame,object_index:objectIndex,...pose});
  }
  if(rows.length>4096)throw Error('This range exceeds the saved channel budget.');
  return rows.sort((a,b)=>a.frame_index-b.frame_index||a.object_index-b.object_index);
}

// Removing saved rows restores native Retail axes; it never copies a sampled pose
// across a range, where Retail values may differ from frame to frame.
export function worldAnimationRetailPoseDraft(held,objectIndex,start=held?.frame_index,end=start){
  const p=held?.preview;
  if(!p||!Number.isSafeInteger(p.channel_count)||p.channel_count<1||p.channel_count>64||!Number.isSafeInteger(objectIndex)||objectIndex<0||objectIndex>=p.channel_count)throw Error('Choose a rigid object within the inspected clip.');
  if(!Number.isSafeInteger(held.frame_index)||!Number.isSafeInteger(p.frame_count)||p.frame_count<1||p.frame_count>512||!Number.isSafeInteger(start)||!Number.isSafeInteger(end)||start<0||end>=p.frame_count||end<start||held.frame_index<start||held.frame_index>end)throw Error('Choose an inclusive frame range within the clip that includes the inspected frame.');
  const index=String(p.record_index).padStart(4,'0');
  return structuredClone(held.binding?.entries[index]?.edits??[]).filter(e=>e.object_index!==objectIndex||e.frame_index<start||e.frame_index>end);
}

export function mountWorldAnimationEditor({host,currentReport,entityId,path,current,busy,setBusy,api,onApplied,getBinding,onPose,onReturn,onError,update:outerUpdate,onInspect}){
  const panel=node('details'),fields=node('div'),actions=node('div'),status=node('p'),evidence=node('pre');panel.dataset.worldAnimationEditor='';
  panel.append(node('summary','Saved World Animation Channels'),node('p','Edit one frame, hold a pose, or offset existing motion across a frame range in native actor-local units. Translation is -2048..2047; rotation uses 4096 units per turn in exact steps of 16. This ANM record is shared by every object selecting it. Other saved frames and records are retained. The preview poses the selected scene object; the saved record affects every matching selector. Timing, looping and runtime activation remain unverified.'));
  Object.assign(fields.style,{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(150px,1fr))',gap:'8px'});actions.className='dialog-actions';actions.style.flexWrap='wrap';Object.assign(evidence.style,{whiteSpace:'pre-wrap',overflowWrap:'anywhere',maxHeight:'240px',overflow:'auto'});evidence.className='diagnostic-detail';status.setAttribute('role','status');
  const inputs={},buttons={},readouts={};
  for(const [key,label,lo,hi,step] of [['frame','World animation edit frame',0,511,1],['object','World animation rigid object',0,63,1],...['translation','rotation_psx'].flatMap(field=>[... 'xyz'].map(axis=>[`${field}.${axis}`,`World animation ${field==='translation'?'translation':'rotation'} ${axis.toUpperCase()}`,field==='translation'?-2048:0,field==='translation'?2047:4080,field==='translation'?1:16]))]){
    const i=node('input'),l=node('label',label);i.type='number';i.min=String(lo);i.max=String(hi);i.step=String(step);i.value='0';i.setAttribute('aria-label',label);Object.assign(i.style,{display:'block',width:'100%',maxWidth:'100%',boxSizing:'border-box'});if(key.includes('.')){const readout=node('small');readout.dataset.worldAnimationValues=key;readouts[key]=readout;l.append(readout);readout.style.display='block';}l.append(i);fields.append(l);inputs[key]=i;
  }
  const mode=node('select'),rangeStart=node('input'),rangeEnd=node('input');mode.setAttribute('aria-label','World animation draft scope');for(const [value,text] of [['frame','Single Frame'],['range','Hold Pose Across Frame Range'],['offset','Offset Pose Across Frame Range']]){const o=node('option',text);o.value=value;mode.append(o);}const scopeLabel=node('label','Draft Scope');scopeLabel.style.gridColumn='1 / -1';Object.assign(mode.style,{width:'100%',boxSizing:'border-box'});scopeLabel.append(mode);fields.append(scopeLabel);
  for(const [input,text] of [[rangeStart,'World animation range start'],[rangeEnd,'World animation range end']]){const l=node('label',text);input.type='number';input.min='0';input.max='511';input.step='1';input.value='0';input.setAttribute('aria-label',text);Object.assign(input.style,{display:'block',width:'100%',boxSizing:'border-box'});l.append(input);fields.append(l);}
  panel.append(node('p','Offset Pose Across Frame Range adds the difference between these values and the inspected Current pose to each Current frame, preserving motion. Rotations wrap within one turn; translation overflow refuses the entire proposal. Hold Pose Across Frame Range holds these translation and rotation values on the selected rigid object at every included frame. Include the inspected frame. Other objects and frames outside the range retain their saved edits. Restore Retail Object Pose removes only this object’s saved rows in the selected frame scope, restoring each frame’s original native pose. No interpolation or native timing is inferred.'));
  const consent=node('input'),consentLabel=node('label','Edit this shared World animation record');consent.type='checkbox';consent.setAttribute('aria-label','Edit this shared World animation record');Object.assign(consent.style,{width:'auto',display:'inline-block',margin:'0',flex:'none'});Object.assign(consentLabel.style,{display:'flex',flexDirection:'row',alignItems:'center',gap:'8px'});consentLabel.prepend(consent);panel.append(fields,consentLabel);
  for(const [key,label] of [['inspect','Inspect Current animation channels'],['review','Review World animation channels'],['glb','Review World animation GLB'],['retail','Review restore Retail object pose'],['reset','Review reset of shared World animation record'],['preview','Preview reviewed World animation'],['apply','Apply reviewed World animation'],['discard','Discard World animation draft']]){const b=node('button',label);b.type='button';buttons[key]=b;actions.append(b);}
  panel.append(actions,status,evidence);host.append(panel);let held=null,review=null,controller=null,generation=0,kind=null,displayed=false,disposed=false,glbRequest=null,proposedSampler=null,currentSampler=null,comparisonFrame=0;
  const glbControls=node('details');glbControls.append(node('summary','World Animation GLB Import'),node('p','Choose an edited GLB and its fresh World export audit. Import replaces this shared clip’s rigid channels with source-quantized poses; mesh edits are ignored. Original GLB bytes are retained with Apply. Native timing and activation remain unverified.'));
  const glbFile=node('input'),auditFile=node('input'),animationChoice=node('input'),objectMapping=node('input');glbFile.type=auditFile.type='file';glbFile.accept='.glb';auditFile.accept='.json';animationChoice.type='number';animationChoice.min='0';animationChoice.max='63';animationChoice.step='1';
  for(const [input,label] of [[glbFile,'World animation GLB file'],[auditFile,'World animation export audit file'],[animationChoice,'World GLB animation index (blank for one clip)'],[objectMapping,'World GLB object node indices (blank for native identities)']]){input.setAttribute('aria-label',label);Object.assign(input.style,{display:'block',width:'100%',boxSizing:'border-box'});const wrapper=node('label',label);wrapper.append(input);glbControls.append(wrapper);input.onchange=()=>invalidate();if(input.type!=='file')input.oninput=()=>invalidate();}panel.insertBefore(glbControls,actions);
  const fresh=()=>!disposed&&current();
  const proposedHost=node('section');proposedHost.dataset.worldAnimationProposed='';proposedHost.hidden=true;proposedHost.append(node('h4','Reviewed Animation Comparison'));const comparison=node('select'),comparisonLabel=node('label','Comparison Layer');comparison.setAttribute('aria-label','World animation comparison layer');for(const [value,text] of [['proposed','Proposed — Unsaved Review'],['current','Current — Saved Channels']]){const option=node('option',text);option.value=value;comparison.append(option);}Object.assign(comparison.style,{display:'block',width:'100%',boxSizing:'border-box'});comparisonLabel.append(comparison);proposedHost.append(comparisonLabel);panel.insertBefore(proposedHost,status);
  const proposedPlayback=mountWorldAnimationPlayback({host:proposedHost,current:()=>fresh()&&displayed&&!!review&&!controller,busy,onError,update:outerUpdate,labelPrefix:'Reviewed World animation',playLabel:'Play compared frames',onFrame:value=>{comparisonFrame=value.frame_index;onPose(value.geometry);status.textContent=`${comparison.value==='proposed'?'Proposed unsaved':'Current saved'} frame ${value.frame_index}; Current placement retained. Native timing and looping unknown.`;refresh();outerUpdate();}});
  comparison.onchange=()=>{if(!fresh()||busy()||controller||!displayed||!review)return;try{const sampler=comparison.value==='proposed'?proposedSampler:comparison.value==='current'?currentSampler:null;if(!sampler)throw Error('Choose a qualified Current or Proposed layer.');const frame=comparisonFrame;proposedPlayback.set(sampler);proposedPlayback.seek(frame);refresh();outerUpdate();}catch(e){onError(e);}};
  function restore(){proposedPlayback.clear();proposedHost.hidden=true;proposedSampler=currentSampler=null;comparison.value='proposed';comparisonFrame=0;if(displayed){displayed=false;onReturn();}}
  function invalidate(){if(review||displayed)status.textContent='Draft changed; Review and Preview again before Apply.';restore();review=null;glbRequest=null;evidence.textContent='';refresh();outerUpdate();}
  function populate(){if(!held)return;const index=Number(inputs.object.value),t=held.preview.object_transforms[index];if(!t)return;for(const field of ['translation','rotation_psx'])for(const [i,axis] of [...'xyz'].entries()){inputs[`${field}.${axis}`].value=String(t[field][i]);readouts[`${field}.${axis}`].textContent=`Retail ${held.source.before.preview.object_transforms[index][field][i]} · Current ${t[field][i]}`;}}
  for(const [key,i] of Object.entries(inputs))i.oninput=()=>{invalidate();if(key==='frame'){held=null;status.textContent='Inspect the new frame before editing.';}if(key==='object')populate();refresh();};
  consent.onchange=invalidate;
  mode.onchange=invalidate;rangeStart.oninput=rangeEnd.oninput=invalidate;
  function refresh(){const available=fresh()&&!busy()&&!controller;buttons.inspect.disabled=!available||displayed;buttons.review.disabled=buttons.retail.disabled=buttons.reset.disabled=!available||!held||!consent.checked||displayed;buttons.glb.disabled=!available||!held||!consent.checked||displayed||!glbFile.files?.[0]||!auditFile.files?.[0];for(const input of [glbFile,auditFile,animationChoice,objectMapping])input.disabled=!available||!held;buttons.preview.disabled=!available||!review||displayed;buttons.apply.disabled=!available||!review||!displayed||comparison.value!=='proposed'||!review.project_change||typeof api!=='function';buttons.discard.disabled=!!controller;inputs.frame.disabled=!available||displayed;inputs.object.disabled=!available||!held||displayed;for(const [key,i] of Object.entries(inputs))if(key.includes('.'))i.disabled=!available||!held;consent.disabled=!available||!held;mode.disabled=!available||!held;rangeStart.disabled=rangeEnd.disabled=!available||!held||!['range','offset'].includes(mode.value);comparison.disabled=!available||!displayed;proposedPlayback.update();}
  async function request(route,body,signal){const response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal}),raw=await response.text();if(new TextEncoder().encode(raw).length>160*1024*1024)throw Error('World animation exceeds its private response budget.');const v=JSON.parse(raw);if(!response.ok)throw Error(v.error||'World animation request failed.');return v;}
  function begin(action){controller=new AbortController();kind=action;const token=++generation;setBusy(true);refresh();outerUpdate();return {token,signal:controller.signal};}
  function finish(token){if(token!==generation)return;controller=null;kind=null;setBusy(false);refresh();outerUpdate();}
  const body=frame=>({scene:currentReport.scene,source_key:currentReport.project_source_key,entity_id:entityId,frame_index:frame});
  buttons.inspect.onclick=async()=>{
    if(buttons.inspect.disabled)return;onInspect();invalidate();held=null;const frame=Number(inputs.frame.value);if(inputs.frame.value.trim()===''||!Number.isSafeInteger(frame)||frame<0||frame>511){status.textContent='Choose a whole frame 0..511.';return;}
    const {token,signal}=begin('inspect');try{const v=await request('/api/worldmap-object-animation-current',body(frame),signal),qualified=await qualifyWorldAnimationCurrent(v,currentReport,entityId,path,frame,getBinding());if(token!==generation||!fresh())return;held=qualified;inputs.frame.max=rangeStart.max=rangeEnd.max=String(v.preview.frame_count-1);rangeStart.value=rangeEnd.value=String(frame);inputs.object.max=String(v.preview.channel_count-1);inputs.object.value='0';consent.checked=false;populate();status.textContent=`Current frame ${frame}; ${v.preview.channel_count} rigid objects. ${v.animation_id}. Confirm shared-record scope before Review.`;}catch(e){if(e.name!=='AbortError'&&token===generation&&fresh()){status.textContent=e.message;onError(e);}}finally{finish(token);}
  };
  async function reviewDraft(reset,retail=false){
    if((reset?buttons.reset:retail?buttons.retail:buttons.review).disabled)return;review=null;glbRequest=null;const {token,signal}=begin('review');
    try{const values=Object.fromEntries(['translation','rotation_psx'].map(field=>[field,Object.fromEntries([...'xyz'].map(axis=>[axis,inputs[`${field}.${axis}`].value.trim()===''?NaN:Number(inputs[`${field}.${axis}`].value)]))])),object=inputs.object.value.trim()===''?NaN:Number(inputs.object.value),edits=reset?[]:retail?worldAnimationRetailPoseDraft(held,object,['range','offset'].includes(mode.value)?(rangeStart.value.trim()===''?NaN:Number(rangeStart.value)):held.frame_index,['range','offset'].includes(mode.value)?(rangeEnd.value.trim()===''?NaN:Number(rangeEnd.value)):held.frame_index):mode.value==='offset'?await worldAnimationOffsetRangeDraft(held,object,values,rangeStart.value.trim()===''?NaN:Number(rangeStart.value),rangeEnd.value.trim()===''?NaN:Number(rangeEnd.value)):mode.value==='range'?worldAnimationRangeDraft(held,object,values,rangeStart.value.trim()===''?NaN:Number(rangeStart.value),rangeEnd.value.trim()===''?NaN:Number(rangeEnd.value)):worldAnimationChannelDraft(held,object,values),v=await request('/api/worldmap-animation-edit-review',{...body(held.frame_index),edits,shared_record:true},signal),qualified=await qualifyWorldAnimationEdit(v,held,currentReport,entityId,path,held.frame_index,edits);
      const sampler=await createWorldAnimationSampler(qualified.proposed_preview,qualified.source.current_model_geometry),beforeSampler=await createWorldAnimationSampler(qualified.current_preview,qualified.source.current_model_geometry);if(token!==generation||!fresh())return;review=qualified;proposedSampler=sampler;currentSampler=beforeSampler;evidence.textContent=JSON.stringify({animation_id:v.animation_id,shared_record:true,reset_selected_record:reset,draft_scope:reset?'Reset Shared Record':retail?{operation:'Restore Retail Object Pose',object_index:object,start:['range','offset'].includes(mode.value)?Number(rangeStart.value):held.frame_index,end:['range','offset'].includes(mode.value)?Number(rangeEnd.value):held.frame_index}:['range','offset'].includes(mode.value)?{object_index:object,start:Number(rangeStart.value),end:Number(rangeEnd.value),sampling:mode.value==='offset'?'current_pose_delta':'constant_pose'}:'Single Frame',current_bank_sha256:v.current_bank_sha256,proposed_bank_sha256:v.proposed_bank_sha256,changed_bytes:v.changed_bytes,source_record_sha256:v.source.audit.source_record_sha256},null,2);status.textContent=v.project_change?'Complete Current/Proposed native replay qualified. Preview before Apply; project unchanged.':'The proposal matches Current. No history command is needed.';
    }catch(e){if(e.name!=='AbortError'&&token===generation&&fresh()){status.textContent=e.message;onError(e);}}finally{finish(token);}
  }
  buttons.glb.onclick=async()=>{if(buttons.glb.disabled)return;review=null;glbRequest=null;const captured=held,{token,signal}=begin('review');try{const draft=await worldAnimationGlbFiles(glbFile.files[0],auditFile.files[0],captured,{scene:currentReport.scene,source_key:currentReport.project_source_key,entity_id:entityId},animationChoice.value,objectMapping.value),value=await request('/api/worldmap-animation-glb-review',draft,signal),qualified=await qualifyWorldAnimationGlb(value,captured,currentReport,entityId,path,draft),sampler=await createWorldAnimationSampler(qualified.native.proposed_preview,qualified.native.source.current_model_geometry),beforeSampler=await createWorldAnimationSampler(qualified.native.current_preview,qualified.native.source.current_model_geometry);if(token!==generation||!fresh()||held!==captured)return;review=qualified.native;glbRequest=qualified.request;proposedSampler=sampler;currentSampler=beforeSampler;evidence.textContent=JSON.stringify({glb_sha256:value.glb_sha256,candidate_record_sha256:value.candidate_record_sha256,animation_index:value.animation_index,object_nodes:value.object_nodes,shared_record:true,retained_on_apply:true,changed_bytes:review.changed_bytes},null,2);status.textContent=review.project_change?'World GLB native replay qualified. Preview before Apply; original input will be retained.':'The GLB matches Current; no Apply or history entry is needed.';}catch(e){if(e.name!=='AbortError'&&token===generation&&fresh()){status.textContent=e.message;onError(e);}}finally{finish(token);}};
  buttons.review.onclick=()=>reviewDraft(false);buttons.retail.onclick=()=>reviewDraft(false,true);buttons.reset.onclick=()=>reviewDraft(true);
  buttons.preview.onclick=()=>{if(buttons.preview.disabled)return;try{onPose(review.proposed_preview.geometry);displayed=true;comparison.value='proposed';comparisonFrame=review.frame_index;proposedHost.hidden=false;proposedPlayback.set(proposedSampler);status.textContent='Reviewed proposed pose displayed with Current placement. Compare Current and Proposed at the same display frame, then Apply Proposed or discard.';refresh();outerUpdate();}catch(e){status.textContent=e.message;onError(e);}};
  buttons.apply.onclick=async()=>{
    if(buttons.apply.disabled||comparison.value!=='proposed')return;const captured=review,target={scene:currentReport.scene,projectPath:path,entityId};kind='apply';controller=new AbortController();refresh();
    try{const result=await (glbRequest?api('/api/worldmap-animation-glb-apply',glbRequest):api('/api/worldmap-animation-edit-apply',{...body(captured.frame_index),edits:captured.edits,shared_record:true,review_key:captured.review_key}));if(result!==true)throw Error('World animation Apply failed. Inspect Current before retrying.');cancel();await onApplied(target);}catch(e){status.textContent=e.message;onError(e);}finally{controller=null;kind=null;refresh();}
  };
  function cancel(){generation++;controller?.abort();controller=null;if(kind==='inspect'||kind==='review')setBusy(false);kind=null;restore();held=review=null;glbRequest=null;consent.checked=false;evidence.textContent='';refresh();}
  buttons.discard.onclick=()=>{cancel();status.textContent='World animation draft discarded; project unchanged.';outerUpdate();};
  refresh();return {update:refresh,cancel,async openBuild(record,change){
    if(!fresh()||busy()||controller)throw Error('Current World animation Inspector is unavailable.');
    panel.open=true;inputs.frame.value=String(change.frame_index);await buttons.inspect.onclick();
    if(!fresh()||!held)throw Error('Built World animation could not be inspected in Current.');let currentValue,retailValue;
    try{const values=qualifyWorldAnimationBuildPose(held,record,change);currentValue=values.current;retailValue=values.retail;if(!inputs[change.field])throw Error('Built axis is unsupported.');}catch(error){cancel();throw error;}
    inputs.object.value=String(change.object_index);mode.value='frame';populate();status.textContent=`Built ${change.field}: Retail ${retailValue} → Current ${currentValue}. Frame ${change.frame_index}, object ${change.object_index}; shared clip affects every matching selector. No project change.`;refresh();inputs[change.field].focus();inputs[change.field].scrollIntoView({block:'nearest'});return true;
  },dispose(){disposed=true;cancel();proposedPlayback.dispose();panel.remove();}};
}
