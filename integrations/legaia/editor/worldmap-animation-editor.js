import {qualifyWorldAnimationCurrent,qualifyWorldAnimationEdit} from './worldmap-animation-current.js';
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

export function mountWorldAnimationEditor({host,currentReport,entityId,path,current,busy,setBusy,api,onApplied,getBinding,onPose,onReturn,onError,update:outerUpdate,onInspect}){
  const panel=node('details'),fields=node('div'),actions=node('div'),status=node('p'),evidence=node('pre');panel.dataset.worldAnimationEditor='';
  panel.append(node('summary','Saved World Animation Channels'),node('p','Edit one frame or hold an explicit pose across a frame range in native actor-local units. Translation is -2048..2047; rotation uses 4096 units per turn in exact steps of 16. This ANM record is shared by every object selecting it. Other saved frames and records are retained. The preview poses the selected scene object; the saved record affects every matching selector. Timing, looping and runtime activation remain unverified.'));
  Object.assign(fields.style,{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(150px,1fr))',gap:'8px'});actions.className='dialog-actions';actions.style.flexWrap='wrap';Object.assign(evidence.style,{whiteSpace:'pre-wrap',overflowWrap:'anywhere',maxHeight:'240px',overflow:'auto'});evidence.className='diagnostic-detail';status.setAttribute('role','status');
  const inputs={},buttons={},readouts={};
  for(const [key,label,lo,hi,step] of [['frame','World animation edit frame',0,511,1],['object','World animation rigid object',0,63,1],...['translation','rotation_psx'].flatMap(field=>[... 'xyz'].map(axis=>[`${field}.${axis}`,`World animation ${field==='translation'?'translation':'rotation'} ${axis.toUpperCase()}`,field==='translation'?-2048:0,field==='translation'?2047:4080,field==='translation'?1:16]))]){
    const i=node('input'),l=node('label',label);i.type='number';i.min=String(lo);i.max=String(hi);i.step=String(step);i.value='0';i.setAttribute('aria-label',label);Object.assign(i.style,{display:'block',width:'100%',maxWidth:'100%',boxSizing:'border-box'});if(key.includes('.')){const readout=node('small');readout.dataset.worldAnimationValues=key;readouts[key]=readout;l.append(readout);readout.style.display='block';}l.append(i);fields.append(l);inputs[key]=i;
  }
  const mode=node('select'),rangeStart=node('input'),rangeEnd=node('input');mode.setAttribute('aria-label','World animation draft scope');for(const [value,text] of [['frame','Single Frame'],['range','Hold Pose Across Frame Range']]){const o=node('option',text);o.value=value;mode.append(o);}const scopeLabel=node('label','Draft Scope');scopeLabel.style.gridColumn='1 / -1';Object.assign(mode.style,{width:'100%',boxSizing:'border-box'});scopeLabel.append(mode);fields.append(scopeLabel);
  for(const [input,text] of [[rangeStart,'World animation range start'],[rangeEnd,'World animation range end']]){const l=node('label',text);input.type='number';input.min='0';input.max='511';input.step='1';input.value='0';input.setAttribute('aria-label',text);Object.assign(input.style,{display:'block',width:'100%',boxSizing:'border-box'});l.append(input);fields.append(l);}
  panel.append(node('p','Frame Range holds these translation and rotation values on the selected rigid object at every included frame. Include the inspected frame. Other objects and frames outside the range retain their saved edits. No interpolation or native timing is inferred.'));
  const consent=node('input'),consentLabel=node('label','Edit this shared World animation record');consent.type='checkbox';consent.setAttribute('aria-label','Edit this shared World animation record');Object.assign(consent.style,{width:'auto',display:'inline-block',margin:'0',flex:'none'});Object.assign(consentLabel.style,{display:'flex',flexDirection:'row',alignItems:'center',gap:'8px'});consentLabel.prepend(consent);panel.append(fields,consentLabel);
  for(const [key,label] of [['inspect','Inspect Current animation channels'],['review','Review World animation channels'],['reset','Review reset of shared World animation record'],['preview','Preview reviewed World animation'],['apply','Apply reviewed World animation'],['discard','Discard World animation draft']]){const b=node('button',label);b.type='button';buttons[key]=b;actions.append(b);}
  panel.append(actions,status,evidence);host.append(panel);let held=null,review=null,controller=null,generation=0,kind=null,displayed=false,disposed=false;
  const fresh=()=>!disposed&&current();
  function restore(){if(displayed){displayed=false;onReturn();}}
  function invalidate(){if(review||displayed)status.textContent='Draft changed; Review and Preview again before Apply.';restore();review=null;evidence.textContent='';refresh();outerUpdate();}
  function populate(){if(!held)return;const index=Number(inputs.object.value),t=held.preview.object_transforms[index];if(!t)return;for(const field of ['translation','rotation_psx'])for(const [i,axis] of [...'xyz'].entries()){inputs[`${field}.${axis}`].value=String(t[field][i]);readouts[`${field}.${axis}`].textContent=`Retail ${held.source.before.preview.object_transforms[index][field][i]} · Current ${t[field][i]}`;}}
  for(const [key,i] of Object.entries(inputs))i.oninput=()=>{invalidate();if(key==='frame'){held=null;status.textContent='Inspect the new frame before editing.';}if(key==='object')populate();refresh();};
  consent.onchange=invalidate;
  mode.onchange=invalidate;rangeStart.oninput=rangeEnd.oninput=invalidate;
  function refresh(){const available=fresh()&&!busy()&&!controller;buttons.inspect.disabled=!available||displayed;buttons.review.disabled=buttons.reset.disabled=!available||!held||!consent.checked||displayed;buttons.preview.disabled=!available||!review||displayed;buttons.apply.disabled=!available||!review||!displayed||!review.project_change||typeof api!=='function';buttons.discard.disabled=!!controller;inputs.frame.disabled=!available||displayed;inputs.object.disabled=!available||!held||displayed;for(const [key,i] of Object.entries(inputs))if(key.includes('.'))i.disabled=!available||!held;consent.disabled=!available||!held;mode.disabled=!available||!held;rangeStart.disabled=rangeEnd.disabled=!available||!held||mode.value!=='range';}
  async function request(route,body,signal){const response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal}),raw=await response.text();if(new TextEncoder().encode(raw).length>160*1024*1024)throw Error('World animation exceeds its private response budget.');const v=JSON.parse(raw);if(!response.ok)throw Error(v.error||'World animation request failed.');return v;}
  function begin(action){controller=new AbortController();kind=action;const token=++generation;setBusy(true);refresh();outerUpdate();return {token,signal:controller.signal};}
  function finish(token){if(token!==generation)return;controller=null;kind=null;setBusy(false);refresh();outerUpdate();}
  const body=frame=>({scene:currentReport.scene,source_key:currentReport.project_source_key,entity_id:entityId,frame_index:frame});
  buttons.inspect.onclick=async()=>{
    if(buttons.inspect.disabled)return;onInspect();invalidate();held=null;const frame=Number(inputs.frame.value);if(inputs.frame.value.trim()===''||!Number.isSafeInteger(frame)||frame<0||frame>511){status.textContent='Choose a whole frame 0..511.';return;}
    const {token,signal}=begin('inspect');try{const v=await request('/api/worldmap-object-animation-current',body(frame),signal),qualified=await qualifyWorldAnimationCurrent(v,currentReport,entityId,path,frame,getBinding());if(token!==generation||!fresh())return;held=qualified;inputs.frame.max=rangeStart.max=rangeEnd.max=String(v.preview.frame_count-1);rangeStart.value=rangeEnd.value=String(frame);inputs.object.max=String(v.preview.channel_count-1);inputs.object.value='0';consent.checked=false;populate();status.textContent=`Current frame ${frame}; ${v.preview.channel_count} rigid objects. ${v.animation_id}. Confirm shared-record scope before Review.`;}catch(e){if(e.name!=='AbortError'&&token===generation&&fresh()){status.textContent=e.message;onError(e);}}finally{finish(token);}
  };
  async function reviewDraft(reset){
    if((reset?buttons.reset:buttons.review).disabled)return;review=null;const {token,signal}=begin('review');
    try{const values=Object.fromEntries(['translation','rotation_psx'].map(field=>[field,Object.fromEntries([...'xyz'].map(axis=>[axis,inputs[`${field}.${axis}`].value.trim()===''?NaN:Number(inputs[`${field}.${axis}`].value)]))])),object=inputs.object.value.trim()===''?NaN:Number(inputs.object.value),edits=reset?[]:mode.value==='range'?worldAnimationRangeDraft(held,object,values,rangeStart.value.trim()===''?NaN:Number(rangeStart.value),rangeEnd.value.trim()===''?NaN:Number(rangeEnd.value)):worldAnimationChannelDraft(held,object,values),v=await request('/api/worldmap-animation-edit-review',{...body(held.frame_index),edits,shared_record:true},signal),qualified=await qualifyWorldAnimationEdit(v,held,currentReport,entityId,path,held.frame_index,edits);
      if(token!==generation||!fresh())return;review=qualified;evidence.textContent=JSON.stringify({animation_id:v.animation_id,shared_record:true,reset_selected_record:reset,draft_scope:reset?'Reset Shared Record':mode.value==='range'?{object_index:object,start:Number(rangeStart.value),end:Number(rangeEnd.value),sampling:'constant_pose'}:'Single Frame',current_bank_sha256:v.current_bank_sha256,proposed_bank_sha256:v.proposed_bank_sha256,changed_bytes:v.changed_bytes,source_record_sha256:v.source.audit.source_record_sha256},null,2);status.textContent=v.project_change?'Complete Current/Proposed native replay qualified. Preview before Apply; project unchanged.':'The proposal matches Current. No history command is needed.';
    }catch(e){if(e.name!=='AbortError'&&token===generation&&fresh()){status.textContent=e.message;onError(e);}}finally{finish(token);}
  }
  buttons.review.onclick=()=>reviewDraft(false);buttons.reset.onclick=()=>reviewDraft(true);
  buttons.preview.onclick=()=>{if(buttons.preview.disabled)return;try{onPose(review.proposed_preview.geometry);displayed=true;status.textContent='Reviewed proposed pose displayed with Current placement. Apply or discard.';refresh();outerUpdate();}catch(e){status.textContent=e.message;onError(e);}};
  buttons.apply.onclick=async()=>{
    if(buttons.apply.disabled)return;const captured=review,target={scene:currentReport.scene,projectPath:path,entityId};kind='apply';controller=new AbortController();refresh();
    try{const result=await api('/api/command',{type:'set_world_animation_channels',...body(captured.frame_index),edits:captured.edits,shared_record:true,review_key:captured.review_key});if(result!==true)throw Error('World animation Apply failed. Inspect Current before retrying.');cancel();await onApplied(target);}catch(e){status.textContent=e.message;onError(e);}finally{controller=null;kind=null;refresh();}
  };
  function cancel(){generation++;controller?.abort();controller=null;if(kind==='inspect'||kind==='review')setBusy(false);kind=null;restore();held=review=null;consent.checked=false;evidence.textContent='';refresh();}
  buttons.discard.onclick=()=>{cancel();status.textContent='World animation draft discarded; project unchanged.';outerUpdate();};
  refresh();return {update:refresh,cancel,dispose(){disposed=true;cancel();panel.remove();}};
}
