import {qualifyWorldAnimationChannels} from './worldmap-animation-channels.js';
import {replayWorldAnimationChannels} from './worldmap-animation-current.js';
import {placementDigest} from './worldmap-placement-replay.js';
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const same=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
const fail=()=>{throw Error('Native clip proposal differs from its reviewed source and channels.');};
export function worldClipChannelDraft(plan,binding,frame,object,values){
  const poses=plan.frame(frame);if(!Number.isSafeInteger(object)||object<0||object>=poses.length)fail();
  for(const field of ['translation','rotation_psx']){
    if(!values?.[field]||!same(Object.keys(values[field]).sort(),['x','y','z']))fail();
    for(const value of Object.values(values[field]))if(!Number.isSafeInteger(value)||(field==='translation'?value < -2048||value > 2047:value<0||value>4080||value%16))fail();
  }
  const index=String(plan.record.source_record.record_index).padStart(4,'0'),rows=structuredClone(binding?.entries[index]?.edits??[]).filter(e=>e.frame_index!==frame||e.object_index!==object);
  rows.push({frame_index:frame,object_index:object,...structuredClone(values)});if(rows.length>4096)fail();
  return rows.sort((a,b)=>a.frame_index-b.frame_index||a.object_index-b.object_index);
}
// A range is anchored at the inspected frame; native timing stays unknown.
function rangeRows(plan,binding,frame,object,start,end){
  const poses=plan.frame(frame);
  if(!Number.isSafeInteger(object)||object<0||object>=poses.length||!Number.isSafeInteger(start)||!Number.isSafeInteger(end)||start<0||end<start||end>=plan.record.frame_count||frame<start||frame>end)throw Error('Choose an inclusive range within the clip containing the inspected frame.');
  const index=String(plan.record.source_record.record_index).padStart(4,'0');
  return structuredClone(binding?.entries[index]?.edits??[]).filter(e=>e.object_index!==object||e.frame_index<start||e.frame_index>end);
}
export function worldClipChannelRangeDraft(plan,binding,frame,object,values,start,end,mode){
  if(!['hold','offset'].includes(mode))fail();
  // Share six-axis admission with single-frame drafting.
  worldClipChannelDraft(plan,binding,frame,object,values);
  const rows=rangeRows(plan,binding,frame,object,start,end),anchor=plan.frame(frame)[object].current;
  for(let f=start;f<=end;f++){
    const source=plan.frame(f)[object].current,pose={};
    for(const field of ['translation','rotation_psx'])pose[field]=Object.fromEntries([...'xyz'].map((axis,i)=>{
      let value=mode==='hold'?values[field][axis]:source[field][i]+values[field][axis]-anchor[field][i];
      if(field==='rotation_psx')value=((value%4096)+4096)%4096;
      else if(value < -2048||value > 2047)throw Error(`Offset exceeds native translation capacity at frame ${f}, axis ${axis.toUpperCase()}.`);
      return [axis,value];
    }));
    rows.push({frame_index:f,object_index:object,...pose});
  }
  if(rows.length>4096)throw Error('This range exceeds the saved channel budget.');
  return rows.sort((a,b)=>a.frame_index-b.frame_index||a.object_index-b.object_index);
}
export function worldClipChannelRetailDraft(plan,binding,frame,object,start=frame,end=start){
  return rangeRows(plan,binding,frame,object,start,end);
}
export async function qualifyWorldClipChannelReview(value,source,plan,edits){
  const fields=['schema_version','source','edits','binding','shared_record','proposed_bank_base64','proposed_bank_sha256','proposed_record_sha256','changed_bytes','project_change','read_only','project_changed','gameplay_verified','review_key'];
  if(!value||!same(Object.keys(value).sort(),fields.sort())||value.schema_version!=='legaia.world-clip-channel-review.v1'||!same(value.source,source)||!same(value.edits,edits)||value.shared_record!==true||typeof value.project_change!=='boolean'||value.read_only!==true||value.project_changed!==false||value.gameplay_verified!==false||typeof value.review_key!=='string'||!/^[0-9a-f]{64}$/.test(value.review_key))fail();
  const record=plan.record,s=record.source_record,retail=Uint8Array.from(atob(source.retail_bank_base64),c=>c.charCodeAt(0)),current=Uint8Array.from(atob(source.current_bank_base64),c=>c.charCodeAt(0)),replayed=await replayWorldAnimationChannels(retail,s.record_index,s.sha256,edits);
  const binding=structuredClone(source.binding)??{schema_version:'legaia.world-animation-channels.v1',scene:record.source_scene,source_disc_sha256:s.disc_sha256,source_bank_sha256:source.retail_bank_sha256,entries:{}},index=String(s.record_index).padStart(4,'0');
  if(replayed.normalized.length)binding.entries[index]={source_record_sha256:s.sha256,edits:replayed.normalized};else delete binding.entries[index];
  const expected=Object.keys(binding.entries).length?binding:null;if(!same(value.binding,expected)||value.project_change===same(expected,source.binding))fail();
  const proposed=current.slice();proposed.set(replayed.bank.slice(s.byte_offset,s.byte_offset+s.byte_length),s.byte_offset);
  if(await placementDigest(proposed)!==value.proposed_bank_sha256||await placementDigest(proposed.slice(s.byte_offset,s.byte_offset+s.byte_length))!==value.proposed_record_sha256)fail();
  const changed=[];for(let i=0;i<current.length;i++)if(current[i]!==proposed[i])changed.push({byte_offset:i,before_byte:current[i],after_byte:proposed[i]});if(!same(value.changed_bytes,changed))fail();
  const response={...structuredClone(source),binding:expected,current_bank_base64:value.proposed_bank_base64,current_bank_sha256:value.proposed_bank_sha256,current_record_sha256:value.proposed_record_sha256};
  const next=await qualifyWorldAnimationChannels(response,record,source.project_path,source.source_key,expected);
  return {review:structuredClone(value),proposed:next};
}
export function mountWorldClipChannels({host,source,plan,getFrame,current,busy,setBusy,api,onApplied,onError}){
  const node=(tag,text)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e;},box=node('details'),object=node('input'),consent=node('input'),status=node('p'),comparison=node('div'),scope=node('select'),start=node('input'),end=node('input'),display=node('input'),retail=node('button','Review Restore Retail Clip Channels'),reviewButton=node('button','Review Native Clip Channels'),preview=node('button','Preview Native Channel Changes'),apply=node('button','Apply Native Clip Channels'),discard=node('button','Discard Native Clip Draft'),inputs={};
  box.dataset.worldClipChannelEditor='';Object.assign(box.style,{maxWidth:'100%',boxSizing:'border-box',overflowWrap:'anywhere'});Object.assign(comparison.style,{maxWidth:'100%',overflowX:'auto'});box.append(node('summary','Author Native Clip Channels'),node('p','Edit one frame, hold a pose or offset existing motion over an inclusive range in native actor-local units. This native record can be shared by unknown consumers. Preview compares channel data; no model pose, runtime binding or activation is inferred.'));
  Object.assign(object.style,{width:'100%',maxWidth:'100%',boxSizing:'border-box'});object.type='number';object.min='0';object.max=String(plan.record.channel_count-1);object.step='1';object.value='0';object.setAttribute('aria-label','Native clip rigid object');box.append(object);
  scope.setAttribute('aria-label','Native clip draft scope');for(const [value,text] of [['frame','Single Frame'],['hold','Hold Pose Across Frame Range'],['offset','Offset Motion Across Frame Range']]){const option=node('option',text);option.value=value;scope.append(option);}Object.assign(scope.style,{width:'100%',maxWidth:'100%',boxSizing:'border-box'});box.append(scope);
  for(const [input,text] of [[start,'Native clip range start'],[end,'Native clip range end']]){input.type='number';input.min='0';input.max=String(plan.record.frame_count-1);input.step='1';input.setAttribute('aria-label',text);Object.assign(input.style,{width:'100%',boxSizing:'border-box'});const label=node('label',text);label.append(input);box.append(label);}
  box.append(node('p','Ranges include the inspected frame. Offset preserves each Current frame’s motion; rotations wrap and translation overflow refuses the whole proposal. Restore Retail removes only this object’s saved rows within the selected scope. Preview frame navigation does not change the edit frame or reviewed proposal.'));
  for(const field of ['translation','rotation_psx'])for(const axis of 'xyz'){const input=node('input'),label=node('label',`${field==='translation'?'Translation':'Rotation'} ${axis.toUpperCase()}`);input.type='number';input.min=field==='translation'?'-2048':'0';input.max=field==='translation'?'2047':'4080';input.step=field==='translation'?'1':'16';input.setAttribute('aria-label',`Native clip ${field} ${axis}`);Object.assign(input.style,{width:'100%',boxSizing:'border-box'});label.append(input);box.append(label);inputs[field+'.'+axis]=input;}
  consent.type='checkbox';Object.assign(consent.style,{width:'auto',display:'inline-block',marginRight:'8px'});consent.setAttribute('aria-label','Shared native clip consent');const label=node('label','Edit this shared native animation record');Object.assign(label.style,{display:'flex',alignItems:'center',gap:'8px'});label.prepend(consent);box.append(label,reviewButton,retail,preview,apply,discard,status,comparison);host.append(box);let review=null,proposed=null,pending=null,shown=false,disposed=false;
  const valid=()=>!disposed&&current();
  function update(){const blocked=!valid()||busy()||!!pending;for(const input of [object,consent,scope,...Object.values(inputs)])input.disabled=blocked;start.disabled=end.disabled=blocked||scope.value==='frame';reviewButton.disabled=retail.disabled=blocked||!consent.checked;display.disabled=blocked||!review;preview.disabled=blocked||!review;apply.disabled=blocked||!review?.project_change||!shown;discard.disabled=!!pending;}
  function invalidate(){review=proposed=null;shown=false;comparison.replaceChildren();status.textContent='Draft changed; Review and Preview before Apply.';update();}
  function populate(){invalidate();try{const pose=plan.frame(getFrame())[Number(object.value)]?.current;if(!pose)fail();for(const field of ['translation','rotation_psx'])for(const [i,axis] of [...'xyz'].entries())inputs[field+'.'+axis].value=String(pose[field][i]);}catch(error){status.textContent=error.message;}}
  scope.onchange=invalidate;start.oninput=end.oninput=invalidate;
  object.oninput=populate;consent.onchange=invalidate;for(const input of Object.values(inputs))input.oninput=invalidate;
  async function reviewDraft(restore=false){if((restore?retail:reviewButton).disabled)return;invalidate();const controller=new AbortController();pending=controller;setBusy(true);update();try{
    const values=Object.fromEntries(['translation','rotation_psx'].map(field=>[field,Object.fromEntries([...'xyz'].map(axis=>[axis,inputs[field+'.'+axis].value.trim()===''?NaN:Number(inputs[field+'.'+axis].value)]))])),index=object.value.trim()===''?NaN:Number(object.value),lo=scope.value==='frame'?getFrame():start.value.trim()===''?NaN:Number(start.value),hi=scope.value==='frame'?getFrame():end.value.trim()===''?NaN:Number(end.value),edits=restore?worldClipChannelRetailDraft(plan,source.binding,getFrame(),index,lo,hi):scope.value==='frame'?worldClipChannelDraft(plan,source.binding,getFrame(),index,values):worldClipChannelRangeDraft(plan,source.binding,getFrame(),index,values,lo,hi,scope.value),response=await fetch('/api/worldmap-clip-channel-review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({animation_id:plan.record.id,source_key:source.source_key,edits,shared_record:true}),signal:controller.signal}),raw=await response.text();if(raw.length>48*1024*1024)fail();const value=JSON.parse(raw);if(!response.ok)throw Error(value.error||'Native clip Review failed.');const qualified=await qualifyWorldClipChannelReview(value,source,plan,edits);if(!valid()||pending!==controller)return;review=qualified.review;proposed=qualified.proposed;status.textContent=review.project_change?`${review.changed_bytes.length} native bytes reviewed. Preview the channel data before Apply.`:'Current channels unchanged; no history step is needed.';
  }catch(error){if(error.name!=='AbortError'&&valid()){status.textContent=error.message;onError(error);}}finally{if(pending===controller){pending=null;setBusy(false);update();}}}
  reviewButton.onclick=()=>reviewDraft();retail.onclick=()=>reviewDraft(true);
  display.type='number';display.min='0';display.max=String(plan.record.frame_count-1);display.step='1';display.setAttribute('aria-label','Native clip preview frame');Object.assign(display.style,{width:'100%',boxSizing:'border-box'});
  function renderComparison(){
    if(!review||!proposed)return;const f=display.value.trim()===''?NaN:Number(display.value),index=Number(object.value),before=plan.frame(f)[index],after=proposed.frame(f)[index],table=node('table'),head=node('tr');for(const text of ['Axis','Retail','Current','Proposed'])head.append(node('th',text));table.append(head);for(const field of ['translation','rotation_psx'])for(const [i,axis] of [...'xyz'].entries()){const row=node('tr');for(const text of [field+'.'+axis,before.retail[field][i],before.current[field][i],after.current[field][i]])row.append(node('td',String(text)));table.append(row);}comparison.replaceChildren(node('p',`Native Data Preview · Frame ${f}, Object ${index}`),display,table);shown=true;update();
  }
  display.oninput=()=>{if(display.disabled||!valid())return;try{renderComparison();}catch(error){shown=false;comparison.replaceChildren(display,node('p',error.message));update();}};
  preview.onclick=()=>{if(preview.disabled)return;try{display.value=String(getFrame());renderComparison();}catch(error){shown=false;update();onError(error);}};
  apply.onclick=async()=>{if(apply.disabled)return;const held=review;try{const result=await api('/api/worldmap-clip-channel-apply',{animation_id:plan.record.id,source_key:source.source_key,edits:held.edits,shared_record:true,review_key:held.review_key});if(result!==true)throw Error('Native clip Apply failed; inspect fresh Current channels before retrying.');onApplied(result);}catch(error){invalidate();status.textContent=error.message;onError(error);}};
  function sync(){start.value=end.value=String(getFrame());populate();}
  discard.onclick=sync;sync();update();return {update,sync,dispose(){disposed=true;pending?.abort();if(pending){pending=null;setBusy(false);}review=proposed=null;box.remove();}};
}
