import {worldAnimationTimelineFrame as pickFrame} from './worldmap-animation-timeline.js';
const fields=['translation','rotation_psx'],axes=['x','y','z'];
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const fail=()=>{throw Error('Monster timeline requires qualified matching native streams and an existing part/axis.');};
function stream(value,clip){
 if(typeof value!=='string'||value.length>200000||!Number.isSafeInteger(clip.part_count)||clip.part_count<1||clip.part_count>64||!Number.isSafeInteger(clip.frame_count)||clip.frame_count<1||clip.frame_count>255)fail();
 let bytes;try{bytes=Uint8Array.from(atob(value),c=>c.charCodeAt(0));}catch{fail();}
 if(bytes.length!==2+clip.part_count*clip.frame_count*9||bytes.length!==clip.source_record?.byte_length||bytes[0]!==clip.part_count||bytes[1]!==clip.frame_count)fail();return bytes;
}
function component(bytes,frame,part,parts,field,axis){
 const at=2+(frame*parts+part)*9,b=bytes.subarray(at,at+9),v=field==='translation'?[b[0]|(b[2]&15)<<8,b[1]|(b[2]>>4)<<8,b[3]|(b[5]&15)<<8]:[b[4]|(b[5]>>4)<<8,b[6]|(b[8]&15)<<8,b[7]|(b[8]>>4)<<8];
 return field==='translation'&&v[axis]&2048?v[axis]-4096:v[axis];
}

// The caller qualifies source hashes, Current replay and Review identity first.
// This pure view decoder never registers edits or infers interpolation/timing.
export function monsterChannelTrack(inspection,part,field,axis,review=null){
 const clip=inspection?.clip,index=axes.indexOf(axis);
 if(!clip?.preview_supported||!Number.isSafeInteger(part)||part<0||part>=clip.part_count||!fields.includes(field)||index<0)fail();
 const values=[inspection.retail_motion_base64??inspection.source_motion_base64,inspection.source_motion_base64];
 if(review){if(!same(review.clip,clip)||review.source_motion_base64!==inspection.source_motion_base64||review.projection?.animation_id!==clip.semantic_id||review.project_path!==inspection.project_path||review.project_source_key!==inspection.project_source_key||review.catalog_source_key!==inspection.catalog_source_key||review.asset_id!==inspection.asset_id)fail();values.push(review.candidate_motion_base64);}
 const bytes=values.map(v=>stream(v,clip));
 const samples=Array.from({length:clip.frame_count},(_,frame)=>Object.freeze({frame,retail:component(bytes[0],frame,part,clip.part_count,field,index),current:component(bytes[1],frame,part,clip.part_count,field,index),...(review?{proposed:component(bytes[2],frame,part,clip.part_count,field,index)}:{})}));
 const all=samples.flatMap(s=>review?[s.retail,s.current,s.proposed]:[s.retail,s.current]);return Object.freeze({animation_id:clip.semantic_id,part_index:part,field,axis,min:Math.min(...all),max:Math.max(...all),samples:Object.freeze(samples)});
}

export function mountMonsterChannelTimeline({host,getState,onFrame,onPart,current,busy,onError}){
 const node=(tag,text)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e;},box=node('section'),part=node('select'),axis=node('select'),status=node('p'),svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
 box.dataset.monsterChannelTimeline='';Object.assign(box.style,{maxWidth:'100%',boxSizing:'border-box',overflowWrap:'anywhere'});box.append(node('h4','Native Monster Channel Timeline'),node('p','Discrete native frames. Click or use Left/Right, Home/End. During Proposed comparison, navigation changes the display frame and keeps the reviewed edit fixed. Native timing and interpolation remain unresolved.'));
 part.setAttribute('aria-label','Monster Timeline Native Part');axis.setAttribute('aria-label','Monster Timeline Channel Axis');for(const field of fields)for(const a of axes){const option=node('option',`${field==='translation'?'Translation':'Rotation'} ${a.toUpperCase()}`);option.value=field+'.'+a;axis.append(option);}for(const input of [part,axis])Object.assign(input.style,{width:'100%',maxWidth:'100%',boxSizing:'border-box'});
 const legend=node('p'),proposedLabel=node('span','Proposed · Unsaved Review');proposedLabel.style.color='#c49bff';for(const [text,color] of [['Retail','#68d7ec'],['Current','#f2b66d']]){const span=node('span',text);span.style.color=color;span.style.marginRight='18px';legend.append(span);}legend.append(proposedLabel);
 svg.setAttribute('viewBox','0 0 640 230');svg.setAttribute('role','group');svg.setAttribute('aria-label','Monster Native Channel Timeline');svg.setAttribute('aria-roledescription','Discrete frame timeline');svg.setAttribute('tabindex','0');Object.assign(svg.style,{width:'100%',height:'220px',display:'block',touchAction:'pan-y'});status.setAttribute('role','status');box.append(part,axis,legend,svg,status);host.append(box);let disposed=false,identity=null,track=null,drawing=null,marker=null;
 const valid=()=>!disposed&&current()&&!busy(),el=(tag,attrs,text)=>{const e=document.createElementNS(svg.namespaceURI,tag);for(const [key,value] of Object.entries(attrs))e.setAttribute(key,String(value));if(text!==undefined)e.textContent=String(text);return e;};
 function selectFrame(s){
  marker?.remove();marker=null;const selected=s.previewing?s.previewFrame:s.frame,row=track.samples[selected];if(!row){status.textContent='Choose an existing whole frame.';return;}
  const x=track.samples.length===1?336:48+selected/(track.samples.length-1)*576;marker=el('line',{x1:x,x2:x,y1:16,y2:186,stroke:'#fff','stroke-dasharray':'3 3','data-selected-frame':selected});svg.append(marker);
  status.textContent=`${s.previewing?'Preview Frame':'Frame'} ${selected} · Native Part ${track.part_index} · ${track.field}.${track.axis}: Retail ${row.retail}, Current ${row.current}${s.review?`, Proposed ${row.proposed}`:''}. ${track.field==='translation'?'Signed native translation.':'PSX rotation: 4096 units per turn.'}`;
 }
 function update(){
  if(disposed)return;const s=getState(),blocked=!valid()||!s.inspection;box.hidden=!s.inspection;part.disabled=axis.disabled=blocked;svg.setAttribute('aria-disabled',String(blocked));proposedLabel.hidden=!s.review;
  if(!s.inspection){track=drawing=marker=null;identity=null;svg.replaceChildren();status.textContent='Inspect native channels to view the timeline.';return;}
  try{const clip=s.inspection.clip,key=clip.semantic_id+':'+clip.part_count;if(key!==identity){part.replaceChildren();for(let i=0;i<clip.part_count;i++){const o=node('option',`Native Part ${i}`);o.value=String(i);part.append(o);}identity=key;}if(!s.previewing){if(!Number.isSafeInteger(s.part)||s.part<0||s.part>=clip.part_count){track=drawing=marker=null;svg.replaceChildren();status.textContent='Choose an existing Native Part Index.';return;}part.value=String(s.part);}const [field,a]=axis.value.split('.');
   if(track&&drawing?.inspection===s.inspection&&drawing.review===s.review&&drawing.part===part.value&&drawing.axis===axis.value){selectFrame(s);return;}
   track=monsterChannelTrack(s.inspection,Number(part.value),field,a,s.review);drawing={inspection:s.inspection,review:s.review,part:part.value,axis:axis.value};marker=null;svg.replaceChildren(el('rect',{x:48,y:16,width:576,height:170,fill:'#101a20'}));const x=f=>track.samples.length===1?336:48+f/(track.samples.length-1)*576,low=track.min===track.max?track.min-1:track.min,high=track.min===track.max?track.max+1:track.max,y=v=>186-(v-low)/(high-low)*170;
   for(const n of [track.max,track.min])svg.append(el('text',{x:42,y:y(n)+4,'text-anchor':'end',fill:'#9faeb6','font-size':12},n));
   for(const row of track.samples)for(const [layer,color,r] of s.review?[['retail','#68d7ec',4],['current','#f2b66d',2],['proposed','#c49bff',6]]:[['retail','#68d7ec',4],['current','#f2b66d',2]]){const dot=el('circle',{cx:x(row.frame),cy:y(row[layer]),r,stroke:color,fill:layer==='current'?color:'none','data-frame':row.frame,'data-layer':layer,'data-value':row[layer]});dot.append(el('title',{},`Frame ${row.frame} · ${layer}: ${row[layer]}`));svg.append(dot);}
   svg.append(el('text',{x:48,y:211,fill:'#9faeb6','font-size':12},'0'),el('text',{x:624,y:211,fill:'#9faeb6','font-size':12,'text-anchor':'end'},track.samples.length-1),el('text',{x:336,y:228,fill:'#9faeb6','font-size':12,'text-anchor':'middle'},'Native frame index'));selectFrame(s);
  }catch(e){track=drawing=marker=null;svg.replaceChildren();status.textContent=e.message;onError(e);}
 }
 part.onchange=()=>{if(!valid()||!getState().inspection)return;if(!getState().previewing)onPart(Number(part.value));update();};axis.onchange=()=>{if(valid())update();};
 svg.onclick=e=>{if(!valid()||!track)return;try{const r=svg.getBoundingClientRect();onFrame(pickFrame(e.clientX,r.left,r.width,track.samples.length));update();}catch(error){onError(error);}};
 svg.onkeydown=e=>{if(!valid()||!track||!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();try{const s=getState(),selected=s.previewing?s.previewFrame:s.frame,frame=Number.isSafeInteger(selected)?selected:0;onFrame(e.key==='Home'?0:e.key==='End'?track.samples.length-1:Math.max(0,Math.min(track.samples.length-1,frame+(e.key==='ArrowLeft'?-1:1))));update();}catch(error){onError(error);}};
 update();return {update,dispose(){disposed=true;svg.onclick=svg.onkeydown=part.onchange=axis.onchange=null;track=identity=drawing=marker=null;box.remove();}};
}
