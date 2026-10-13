import {mountMonsterChannelTimeline} from './monster-channel-timeline.js';
import {qualifyMonsterPreview} from './monster-archive.js';
import {samplePlayerActionBytes} from './player-action-playback.js';
import {mountMonsterMotionGlb} from './monster-motion-glb.js';
import {qualifyMonsterMotionComparison,mountMonsterMotionComparison} from './monster-motion-comparison.js';
import {qualifyMonsterMotionBytes} from './monster-motion-replay.js';
import {placementDigest} from './worldmap-placement-replay.js';
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b),hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v),fail=()=>{throw Error('Monster native frame source or channels changed.');};
const decode=s=>{if(typeof s!=='string'||s.length>200000)fail();return Uint8Array.from(atob(s),c=>c.charCodeAt(0));};
function channels(raw,at){const v=[raw[at]|(raw[at+2]&15)<<8,raw[at+1]|(raw[at+2]>>4)<<8,raw[at+3]|(raw[at+5]&15)<<8,raw[at+4]|(raw[at+5]>>4)<<8,raw[at+6]|(raw[at+8]&15)<<8,raw[at+7]|(raw[at+8]>>4)<<8];return {translation:v.slice(0,3).map(n=>n&2048?n-4096:n),rotation_psx:v.slice(3)};}
function packed(t,r){const [x,y,z]=t.map(v=>v&4095),[rx,ry,rz]=r;return [x&255,y&255,x>>8|(y>>8)<<4,z&255,rx&255,z>>8|(rx>>8)<<4,ry&255,rz&255,ry>>8|(rz>>8)<<4];}
export async function qualifyMonsterFrameInspection(v,report,record,choice,part){
 const clip=report.catalog.animations.find(c=>c.semantic_id===choice.animation_id);
 if(!clip?.preview_supported||clip.model_asset_id!==record.id||v?.schema_version!=='legaia.monster-frame-inspection.v1'||v.project_path!==report.project_path||v.project_source_key!==report.project_source_key||v.catalog_source_key!==report.catalog.source_key||v.asset_id!==record.id||!same(v.clip,clip)||v.frame_index!==choice.frame_index||v.part_index!==part||!Number.isSafeInteger(part)||part<0||part>=clip.part_count||!Number.isSafeInteger(choice.frame_index)||choice.frame_index<0||choice.frame_index>=clip.frame_count||!hash(v.current_block_sha256)||v.layer!=='current'||v.read_only!==true||v.project_changed!==false||v.gameplay_verified!==false)fail();
 const raw=await qualifyMonsterMotionBytes(v,clip);if(raw.length!==clip.source_record.byte_length||raw[0]!==clip.part_count||raw[1]!==clip.frame_count||!same(v.channels,{object_index:part,...channels(raw,2+(choice.frame_index*clip.part_count+part)*9)}))fail();return structuredClone(v);
}
export async function qualifyMonsterFrameReview(v,observed,translation,rotation,range=null){
 for(const [values,low,high] of [[translation,-2048,2047],[rotation,0,4095]])if(!Array.isArray(values)||values.length!==3||values.some(n=>!Number.isSafeInteger(n)||n<low||n>high))fail();
 const p=v?.projection,clip=observed.clip,raw=decode(observed.source_motion_base64),expected=new Uint8Array(raw),retail=decode(observed.retail_motion_base64??observed.source_motion_base64),at=2+(observed.frame_index*clip.part_count+observed.part_index)*9,edits=[];if(range){if(!['hold','offset','restore'].includes(range.range_operation)||!Number.isSafeInteger(range.frame_start)||!Number.isSafeInteger(range.frame_end)||range.frame_start<0||range.frame_start>observed.frame_index||range.frame_end<observed.frame_index||range.frame_end>=clip.frame_count)fail();for(let f=range.frame_start;f<=range.frame_end;f++){const pos=2+(f*clip.part_count+observed.part_index)*9,b=channels(raw,pos),values=range.range_operation==='restore'?channels(retail,pos):range.range_operation==='hold'?{translation,rotation_psx:rotation}:{translation:b.translation.map((n,a)=>n+translation[a]-observed.channels.translation[a]),rotation_psx:b.rotation_psx.map((n,a)=>((n+rotation[a]-observed.channels.rotation_psx[a])%4096+4096)%4096)};if(values.translation.some(n=>n< -2048||n>2047))fail();expected.set(packed(values.translation,values.rotation_psx),pos);edits.push({frame_index:f,part_index:observed.part_index,...values});}if(!same(p?.range,{frame_start:range.frame_start,frame_end:range.frame_end,operation:range.range_operation,edits}))fail();}else{if(p?.range)fail();expected.set(packed(translation,rotation),at);}const desired=channels(expected,at);
 if(v?.schema_version!=='legaia.monster-frame-review.v1'||v.project_path!==observed.project_path||v.project_source_key!==observed.project_source_key||v.catalog_source_key!==observed.catalog_source_key||v.asset_id!==observed.asset_id||!same(v.clip,clip)||v.frame_index!==observed.frame_index||v.part_index!==observed.part_index||p?.schema_version!=='legaia.monster-frame-projection.v1'||p.animation_id!==clip.semantic_id||p.frame_index!==observed.frame_index||p.part_index!==observed.part_index||p.source_block_sha256!==observed.current_block_sha256||!hash(p.candidate_block_sha256)||p.source_motion_sha256!==await placementDigest(decode(observed.source_motion_base64))||!same(p.before,{translation:observed.channels.translation,rotation_psx:observed.channels.rotation_psx})||!same(p.after,desired)||v.source_motion_base64!==observed.source_motion_base64||v.layer!=='proposed'||v.persistence!=='not_applied'||v.read_only!==true||v.project_changed!==false||v.gameplay_verified!==false||!hash(v.review_key))fail();
 const candidate=decode(v.candidate_motion_base64);
 if(p.byte_offset!==clip.source_record.byte_offset+at||candidate.length!==raw.length||!same([...candidate],[...expected])||await placementDigest(expected)!==p.candidate_motion_sha256||!same(desired,p.after)||p.byte_change_count!==raw.filter((n,i)=>n!==expected[i]).length)fail();return structuredClone(v);
}
export function mountMonsterMotionAuthoring({host,record,report,current,busy,choice,onPending,onError,onApplied,onFrame,selectionIdentity=()=>null}){
 const node=(tag,text)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e;};
 const section=node('section'),part=node('input'),inspect=node('button','Inspect Native Monster Channels'),review=node('button','Review Native Monster Frame'),apply=node('button','Apply Reviewed Monster Frame'),preview=node('button','Preview Proposed Monster Frame'),restoreView=node('button','Return To Reviewed Edit Frame'),status=node('p','Choose a Stored Action and Frame above, then inspect its native channels.'),inputs={translation:[],rotation_psx:[]};
 part.type='number';part.min='0';part.step='1';part.value='0';part.setAttribute('aria-label','Monster Native Part');const label=node('label','Native Part Index');label.append(part);
 section.append(node('h3','Native Motion Channels'),node('p','Translation uses native signed 12-bit units (−2048 to 2047). Rotation uses 0–4095 units per turn. Review is unsaved; Apply saves one persistent native frame change.'),status,label,inspect);
 let disposed=false,pending=null,observed=null,owner=null,held=null,body=null,previewKey=null,glb=null,timeline=null,timelineInspection=null,previewing=false,previewFrame=0,samplers=null,sourceIdentity=selectionIdentity();
 const valid=()=>!disposed&&current(),key=()=>JSON.stringify([choice().animation_id,choice().frame_index,part.value]),values=field=>inputs[field].map(e=>e.value.trim()?Number(e.value):NaN);
 function withdrawReview(){held=body=null;previewKey=null;previewing=false;samplers=null;comparison.withdraw();}
 function withdrawInspection(){observed=null;owner=null;withdrawReview();}
 for(const field of Object.keys(inputs))for(const axis of 'XYZ'){
  const e=node('input');e.type='number';e.min=field==='translation'?'-2048':'0';e.max=field==='translation'?'2047':'4095';e.step='1';e.value='0';const name=`Monster Native ${field==='translation'?'Translation':'Rotation'} ${axis}`;e.setAttribute('aria-label',name);const l=node('label',name);l.append(e);section.append(l);inputs[field].push(e);
  e.oninput=()=>{withdrawReview();status.textContent='Channel draft changed; review again.';update();};
 }
 const rangeMode=node('select'),rangeStart=node('input'),rangeEnd=node('input');rangeMode.setAttribute('aria-label','Monster Motion Range Operation');
 for(const [value,text] of [['single','Selected Frame'],['hold','Hold Values Across Range'],['offset','Offset Motion Across Range'],['restore','Restore Retail Across Range']]){const o=node('option',text);o.value=value;rangeMode.append(o);}
 for(const [e,name] of [[rangeStart,'Monster Motion Range Start'],[rangeEnd,'Monster Motion Range End']]){e.type='number';e.min='0';e.step='1';e.value='0';e.setAttribute('aria-label',name);const l=node('label',name);l.append(e);section.append(l);}
 section.append(node('p','Inclusive range for this part. Offset uses the difference from the inspected frame and preserves each frame’s motion; rotation wraps one turn. Restore uses Retail values.'),rangeMode,review,preview,restoreView,apply);host.append(section);const comparison=mountMonsterMotionComparison(section);
 function update(){
  const c=choice(),clip=report.catalog.animations.find(r=>r.semantic_id===c.animation_id),nextSource=selectionIdentity();
  if(!valid()||nextSource!==sourceIdentity){withdrawInspection();timelineInspection=null;sourceIdentity=nextSource;}
  if(timelineInspection&&timelineInspection.clip.semantic_id!==c.animation_id){timelineInspection=null;withdrawInspection();}
  if(owner!==null&&owner!==key()){withdrawInspection();status.textContent='Frame or part changed; inspect again.';}
  part.max=String(Math.max(0,(clip?.part_count??0)-1));
  const blocked=!valid()||busy()||!!pending||!!glb?.pending(),allowed=clip?.preview_supported&&Number.isSafeInteger(c.frame_index)&&c.frame_index>=0&&c.frame_index<clip.frame_count&&part.value.trim()&&Number.isSafeInteger(Number(part.value))&&Number(part.value)>=0&&Number(part.value)<clip.part_count;
  inspect.disabled=blocked||!allowed;part.disabled=blocked;for(const field of Object.keys(inputs))for(const e of inputs[field])e.disabled=blocked||!observed;
  review.disabled=blocked||!observed||Object.keys(inputs).some(f=>values(f).some(n=>!Number.isSafeInteger(n)||n<(f==='translation'?-2048:0)||n>(f==='translation'?2047:4095)));
  rangeMode.disabled=rangeStart.disabled=rangeEnd.disabled=blocked;rangeStart.max=rangeEnd.max=String((clip?.frame_count??1)-1);
  if(rangeMode.value!=='single'&&(!rangeStart.value.trim()||!rangeEnd.value.trim()||!Number.isSafeInteger(Number(rangeStart.value))||!Number.isSafeInteger(Number(rangeEnd.value))||Number(rangeStart.value)<0||Number(rangeStart.value)>c.frame_index||Number(rangeEnd.value)<c.frame_index||Number(rangeEnd.value)>=(clip?.frame_count??0)))review.disabled=true;
  preview.disabled=blocked||!held;restoreView.hidden=!previewing;restoreView.disabled=blocked||!previewing;comparison.setDisabled(blocked);apply.disabled=blocked||!held||previewKey!==held.review_key||!held.projection.byte_change_count;glb?.update();timeline?.update();
 }
 async function run(route,args,accept){
  if(!valid()||busy()||pending)return;const startedKey=key(),startedSource=selectionIdentity();pending=new AbortController();onPending(true);update();
  try{const r=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(args),signal:pending.signal}),text=await r.text();if(text.length>8*1024*1024)fail();const v=JSON.parse(text);if(!r.ok)throw Error(v.error||'Monster frame operation failed');const stillCurrent=()=>valid()&&startedKey===key()&&startedSource===selectionIdentity();if(stillCurrent())await accept(v,stillCurrent);}
  catch(e){if(valid()&&e.name!=='AbortError'){status.textContent=e.message;onError(e);}}
  finally{pending=null;onPending(false);update();}
 }
 const context=()=>({expected_project_path:report.project_path,expected_source_key:report.project_source_key,asset_id:record.id,catalog_source_key:report.catalog.source_key,animation_id:choice().animation_id,frame_index:choice().frame_index,part_index:Number(part.value)});
 inspect.onclick=()=>{update();if(inspect.disabled)return;const selected=choice(),index=Number(part.value);withdrawInspection();owner=key();run('/api/monster-frame-inspect',context(),async (v,stillCurrent)=>{const qualified=await qualifyMonsterFrameInspection(v,report,record,selected,index);if(!stillCurrent())return;observed=qualified;timelineInspection=observed;for(const f of Object.keys(inputs))inputs[f].forEach((e,i)=>e.value=String(observed.channels[f][i]));rangeStart.value=rangeEnd.value=String(observed.frame_index);status.textContent='Current native part/frame channels inspected.';});};
 part.oninput=update;for(const e of [rangeMode,rangeStart,rangeEnd])e.oninput=e.onchange=()=>{withdrawReview();status.textContent='Range draft changed; review again.';update();};
 review.onclick=()=>{update();if(review.disabled)return;const t=values('translation'),r=values('rotation_psx'),inspection=observed;withdrawReview();body={...context(),expected_current_block_sha256:observed.current_block_sha256,translation:t,rotation_psx:r,...(rangeMode.value==='single'?{}:{frame_start:Number(rangeStart.value),frame_end:Number(rangeEnd.value),range_operation:rangeMode.value})};const range=rangeMode.value==='single'?null:{frame_start:body.frame_start,frame_end:body.frame_end,range_operation:body.range_operation};run('/api/monster-frame-review',body,async (v,stillCurrent)=>{const qualified=await qualifyMonsterFrameReview(v,inspection,t,r,range);if(!stillCurrent()||observed!==inspection)return;held=qualified;status.textContent=`Proposed native frame / ${held.projection.byte_change_count} byte changes / not applied`;});};
 preview.onclick=()=>{update();if(preview.disabled)return;previewKey=null;previewing=false;samplers=null;comparison.withdraw();const reviewed=held;run('/api/monster-frame-pose',{...body,review_key:reviewed.review_key},async (v,stillCurrent)=>{
  const poses=await qualifyMonsterMotionComparison(v,reviewed,report,record),base=await qualifyMonsterPreview(v.current_pose.base_preview,report,record,'current');if(!stillCurrent()||held!==reviewed)return;
  if(base.objects.length!==reviewed.clip.part_count)fail();const mapping=base.objects.map((_,i)=>i);samplers={current:samplePlayerActionBytes(decode(reviewed.source_motion_base64),base,mapping),proposed:samplePlayerActionBytes(decode(reviewed.candidate_motion_base64),base,mapping)};
  comparison.show(poses);previewing=true;previewFrame=reviewed.frame_index;previewKey=reviewed.review_key;status.textContent='Reviewed Current/Proposed poses qualified; not applied.';
 });};
 function displayFrame(frame){
  if(!held||!samplers||!Number.isSafeInteger(frame)||frame<0||frame>=held.clip.frame_count)fail();
  const layer=section.querySelector('[aria-label="Monster Motion Comparison Layer"]'),selected=layer?.value;comparison.show({current:samplers.current.sample(frame).geometry,proposed:samplers.proposed.sample(frame).geometry});if(layer&&selected&&selected!=='proposed'){layer.value=selected;layer.dispatchEvent(new Event('change'));}
  previewFrame=frame;status.textContent=`Current/Proposed Preview Frame ${frame} · Reviewed Edit Frame ${held.frame_index} · Not Applied`;update();
 }
 restoreView.onclick=()=>{update();if(!restoreView.disabled)displayFrame(held.frame_index);};
 apply.onclick=()=>{update();if(!apply.disabled)run('/api/monster-frame-apply',{...body,review_key:held.review_key},v=>{if(v.monster_motion_apply?.history_steps!==1)fail();onApplied(v);});};
 timeline=mountMonsterChannelTimeline({host:section,getState:()=>({inspection:timelineInspection,review:held,frame:choice().frame_index,part:part.value.trim()?Number(part.value):NaN,previewing,previewFrame}),current:valid,busy:()=>busy()||!!pending||!!glb?.pending(),onError,
  onFrame:frame=>{if(previewing&&held){displayFrame(frame);return;}if(typeof onFrame!=='function'){onError(Error('Monster timeline frame navigation is unavailable.'));return;}withdrawInspection();onFrame(frame);status.textContent='Frame changed; inspect its native channels before editing.';update();},
  onPart:index=>{part.value=String(index);withdrawInspection();status.textContent='Native part changed; inspect its channels before editing.';update();}
 });
 glb=mountMonsterMotionGlb({host:section,record,report,onApplied,current:valid,busy:()=>busy()||!!pending,getInspection:()=>observed,onPending:v=>{onPending(v);update();},onError});
 update();return {update,pending:()=>!!pending||!!glb?.pending(),dispose:()=>{disposed=true;pending?.abort();timeline?.dispose();comparison.dispose();glb?.dispose();section.remove();}};
}
