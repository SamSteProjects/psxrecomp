import {mountWorldAnimationTimeline} from './worldmap-animation-timeline.js';
import {mountWorldClipChannels} from './worldmap-clip-channels.js';
import {placementDigest} from './worldmap-placement-replay.js';
import {replayWorldAnimationChannels} from './worldmap-animation-current.js';
const fail=()=>{throw Error('World native channels differ from the registered clip or Current source.');};
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const same=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
const bytes=value=>{if(typeof value!=='string'||value.length>6*1024*1024)fail();const result=Uint8Array.from(atob(value),c=>c.charCodeAt(0));if(result.length<4||result.length>4*1024*1024)fail();return result;};
function clip(bank,record){
  const v=new DataView(bank.buffer,bank.byteOffset,bank.byteLength),count=v.getUint32(0,true),s=record.source_record,index=s.record_index;
  if(count<1||count>4096||4+count*4>bank.length||!Number.isSafeInteger(index)||index<0||index>=count)fail();
  const offsets=Array.from({length:count},(_,i)=>v.getUint32(4+i*4,true));
  if(offsets[0]<4+count*4||offsets.at(-1)>=bank.length||offsets.some((n,i)=>i&&n<=offsets[i-1]))fail();
  const start=offsets[index],end=offsets[index+1]??bank.length,raw=bank.slice(start,end),view=new DataView(raw.buffer);
  if(start!==s.byte_offset||raw.length!==s.byte_length||raw.length<16||view.getUint16(0,true)>>8>1||(view.getUint16(0,true)&255)!==record.channel_count||view.getUint16(2,true)!==record.frame_count||view.getUint16(4,true)!==0x80c||![2,4].includes(view.getUint16(6,true))||raw.length!==16+record.channel_count*record.frame_count*8||raw.slice(-8).some(n=>n))fail();
  return raw;
}
export async function qualifyWorldAnimationChannels(value,record,path,key,binding=null){
  const fields=['schema_version','project_path','source_key','animation_id','record','binding','retail_bank_base64','current_bank_base64','retail_bank_sha256','current_bank_sha256','current_record_sha256','read_only','project_changed','gameplay_verified','timing','runtime_state'];
  if(!value||!same(Object.keys(value).sort(),fields.sort())||value.schema_version!=='legaia.world-animation-channels-inspection.v1'||value.project_path!==path||value.source_key!==key||value.animation_id!==record.id||record.kind!=='animation'||!same(value.record,record)||!same(value.binding,binding)||value.read_only!==true||value.project_changed!==false||value.gameplay_verified!==false||value.timing!=='unresolved'||value.runtime_state!=='not_observed'||!Number.isSafeInteger(record.frame_count)||record.frame_count<1||record.frame_count>512||!Number.isSafeInteger(record.channel_count)||record.channel_count<1||record.channel_count>64)fail();
  const retail=bytes(value.retail_bank_base64),current=bytes(value.current_bank_base64),original=clip(retail,record),saved=clip(current,record);
  if(await placementDigest(retail)!==value.retail_bank_sha256||value.retail_bank_sha256!==record.source_record.animation_slot.decoded_sha256||await placementDigest(current)!==value.current_bank_sha256||await placementDigest(original)!==record.source_record.sha256||await placementDigest(saved)!==value.current_record_sha256)fail();
  let replay=retail;
  if(binding){
    if(binding.schema_version!=='legaia.world-animation-channels.v1'||binding.scene!==record.source_scene||binding.source_bank_sha256!==value.retail_bank_sha256||binding.source_disc_sha256!==record.source_record.disc_sha256||!binding.entries||!Object.keys(binding.entries).length||Object.keys(binding.entries).length>4096)fail();
    let rows=0;for(const [index,entry] of Object.entries(binding.entries).sort()){
      if(!/^[0-9]{4}$/.test(index)||!Array.isArray(entry.edits)||!entry.edits.length||(rows+=entry.edits.length)>4096)fail();
      const result=await replayWorldAnimationChannels(replay,Number(index),entry.source_record_sha256,entry.edits);
      if(!same(result.normalized,entry.edits))fail();replay=result.bank;
    }
  }
  if(replay.length!==current.length||replay.some((n,i)=>n!==current[i]))fail();
  const owned=structuredClone(record),signed=n=>n&2048?n-4096:n;
  const pose=(raw,frame,object)=>{const at=8+(frame*owned.channel_count+object)*8,d=raw.slice(at,at+8);return {translation:[signed(d[0]+(d[2]&15)*256),signed(d[1]+(d[2]>>4)*256),signed(d[3]+(d[4]&15)*256)],rotation_psx:[d[5]*16,d[6]*16,d[7]*16],opaque_nibble:d[4]>>4};};
  return {record:owned,currentRecordHash:value.current_record_sha256,frame(frame){if(!Number.isSafeInteger(frame)||frame<0||frame>=owned.frame_count)fail();return Array.from({length:owned.channel_count},(_,object)=>({frame_index:frame,object_index:object,retail:pose(original,frame,object),current:pose(saved,frame,object)}));}};
}
export function worldAnimationChannelsCsv(plan){
  const rows=['animation_id,record_sha256,frame,object,layer,translation_x,translation_y,translation_z,rotation_x_psx,rotation_y_psx,rotation_z_psx,opaque_nibble'];
  for(let f=0;f<plan.record.frame_count;f++)for(const row of plan.frame(f))for(const layer of ['retail','current'])rows.push([plan.record.id,layer==='retail'?plan.record.source_record.sha256:plan.currentRecordHash,f,row.object_index,layer,...row[layer].translation,...row[layer].rotation_psx,row[layer].opaque_nibble].join(','));
  return rows.join('\n')+'\n';
}
export function mountWorldAnimationChannels({host,record,path,key,getBinding,current,busy,setBusy,onError,api,onApplied}){
  const node=(tag,text)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e;},section=node('section'),inspect=node('button','Inspect Native World Channels'),frame=node('input'),download=node('button','Download Native Channels CSV'),status=node('p'),table=node('div');
  section.dataset.worldNativeChannels='';Object.assign(section.style,{maxWidth:'100%',boxSizing:'border-box',overflowWrap:'anywhere'});frame.type='number';frame.min='0';frame.max=String(record.frame_count-1);frame.value='0';frame.step='1';frame.setAttribute('aria-label','Native World channel frame');Object.assign(table.style,{maxWidth:'100%',overflowX:'auto'});section.append(node('h3','Native Animation Channels'),node('p','Retail and saved Current actor-local values. No model, joint hierarchy, frame rate or runtime activation is inferred. Rotation uses 4096 units per turn; opaque nibbles are source data.'),inspect,frame,download,status,table);host.append(section);
  let plan=null,pending=null,disposed=false,editing=null,timeline=null;
  const valid=()=>!disposed&&current();
  function update(){const blocked=!valid()||busy()||!!pending;inspect.disabled=blocked;frame.disabled=download.disabled=blocked||!plan;editing?.update();timeline?.update();}
  function render(){table.replaceChildren();if(!plan)return;const wanted=frame.value.trim()===''?NaN:Number(frame.value),rows=plan.frame(wanted),t=node('table'),head=node('tr');for(const text of ['Object','Retail XYZ','Current XYZ','Retail Rotation','Current Rotation','Opaque'])head.append(node('th',text));t.append(head);for(const row of rows){const tr=node('tr');for(const text of [row.object_index,row.retail.translation.join(', '),row.current.translation.join(', '),row.retail.rotation_psx.join(', '),row.current.rotation_psx.join(', '),row.retail.opaque_nibble])tr.append(node('td',String(text)));t.append(tr);}table.append(t);status.textContent=`Frame ${wanted} of ${record.frame_count-1} · ${rows.length} rigid channels · Current record ${plan.currentRecordHash}`;}
  frame.oninput=()=>{if(!valid()||busy()||pending)return;try{editing?.sync();render();timeline?.setFrame();}catch(error){table.replaceChildren();timeline?.setFrame();status.textContent=error.message;}};
  async function run(work){if(!valid()||busy()||pending)return;const controller=new AbortController();pending=controller;setBusy(true);update();try{await work(controller.signal);}catch(error){if(error.name!=='AbortError'&&valid()){status.textContent=error.message;onError(error);}}finally{if(pending===controller){pending=null;setBusy(false);update();}}}
  inspect.onclick=()=>run(async signal=>{editing?.dispose();editing=null;timeline?.dispose();timeline=null;plan=null;table.replaceChildren();status.textContent='Qualifying complete Retail and Current native banks…';const binding=structuredClone(getBinding()??null),response=await fetch('/api/worldmap-animation-channels',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({animation_id:record.id,source_key:key}),signal}),raw=await response.text();if(raw.length>16*1024*1024)fail();const value=JSON.parse(raw);if(!response.ok)throw Error(value.error||'World channel inspection failed.');const next=await qualifyWorldAnimationChannels(value,record,path,key,binding);if(!valid()||!same(getBinding()??null,binding))return;plan=next;frame.value='0';render();timeline=mountWorldAnimationTimeline({host:section,plan,getFrame:()=>frame.value.trim()===''?NaN:Number(frame.value),onFrame:f=>{frame.value=String(f);frame.oninput();},current:valid,busy,onError});if(typeof api==='function')editing=mountWorldClipChannels({host:section,source:value,plan,getFrame:()=>frame.value.trim()===''?NaN:Number(frame.value),current:valid,busy,setBusy:value=>{setBusy(value);update();},api,onApplied,onError});});
  download.onclick=()=>run(async signal=>{const held=plan,response=await fetch('/api/state',{signal}),state=await response.json();if(!response.ok||!valid()||held!==plan||state.project?.path!==path||state.project?.mode!=='edit'||state.worldmap_authoring_state_key!==key)fail();const url=URL.createObjectURL(new Blob([worldAnimationChannelsCsv(held)],{type:'text/csv'})),link=node('a');try{link.href=url;link.download=record.source_scene+'-world-animation-'+String(record.source_record.record_index).padStart(4,'0')+'-channels.csv';link.click();}finally{URL.revokeObjectURL(url);}});
  update();return {update,dispose(){disposed=true;pending?.abort();if(pending){pending=null;setBusy(false);}editing?.dispose();editing=null;timeline?.dispose();timeline=null;plan=null;section.remove();}};
}
