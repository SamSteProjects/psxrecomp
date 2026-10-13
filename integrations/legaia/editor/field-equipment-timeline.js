import {createFieldEquipmentPlaybackSampler} from './field-equipment-playback.js';
import {worldAnimationTimelineFrame} from './worldmap-animation-timeline.js';

const fail=()=>{throw Error('Field equipment timeline requires a qualified eight-byte source channel and an existing native part, axis or frame.');};
const fields=['translation','rotation_psx'],axes=['x','y','z'],models=new WeakMap();

// Format validation alone does not qualify a record's source. The inspector
// only mounts models created from a complete qualified playback receipt.
export function decodeFieldEquipmentTimelineChannel(record,frame,part){
 if(!(record instanceof Uint8Array)||record.length<16||record.length>16+512*80)fail();
 const v=new DataView(record.buffer,record.byteOffset,record.byteLength),a=v.getUint16(0,true),count=v.getUint16(2,true);
 if((a&255)!==10||a>>8>1||v.getUint16(4,true)!==0x080c||![2,4].includes(v.getUint16(6,true))||count<1||count>512||record.length!==16+count*80||record.subarray(-8).some(n=>n)||!Number.isSafeInteger(frame)||frame<0||frame>=count||!Number.isSafeInteger(part)||part<0||part>=10)fail();
 const at=8+(frame*10+part)*8,d=record.subarray(at,at+8),signed=n=>n>=2048?n-4096:n;
 return {object_index:part,translation:[signed(d[0]+(d[2]&15)*256),signed(d[1]+(d[2]>>4)*256),signed(d[3]+(d[4]&15)*256)],rotation_psx:[d[5]*16,d[6]*16,d[7]*16],opaque_nibble:d[4]>>4};
}

export async function createFieldEquipmentTimeline(receipt,context){
 const qualified=await createFieldEquipmentPlaybackSampler(receipt,context),record=Uint8Array.from(atob(receipt.record_base64),c=>c.charCodeAt(0)),frames=[];
 for(let frame=0;frame<qualified.frameCount;frame++)frames.push(Object.freeze(Array.from({length:10},(_,part)=>{const row=decodeFieldEquipmentTimelineChannel(record,frame,part);Object.freeze(row.translation);Object.freeze(row.rotation_psx);return Object.freeze(row);} )));
 const model=Object.freeze({frameCount:qualified.frameCount,initialFrame:qualified.initialFrame,partCount:10,
  recordHash:qualified.recordHash,animationId:receipt.preview.animation.semantic_id,clipId:context.clipId,
  modelLayer:context.modelLayer,codec:'field_rigid_8byte_translation12_rotation8',sourceOnly:true});
 models.set(model,{frames:Object.freeze(frames),tracks:new Map()});return model;
}

export function fieldEquipmentChannelTrack(model,part,field,axis){
 const held=models.get(model),a=axes.indexOf(axis);if(!held||!Number.isSafeInteger(part)||part<0||part>=10||!fields.includes(field)||a<0)fail();
 const key=part+':'+field+':'+axis;if(held.tracks.has(key))return held.tracks.get(key);
 const samples=Object.freeze(held.frames.map((rows,frame)=>Object.freeze({frame,retail:rows[part][field][a],opaque_nibble:rows[part].opaque_nibble}))),values=samples.map(row=>row.retail);
 const track=Object.freeze({part_index:part,field,axis,min:Math.min(...values),max:Math.max(...values),samples});held.tracks.set(key,track);return track;
}

export function mountFieldEquipmentTimeline({host,current,busy,onNavigate,onError}){
 const node=(tag,text)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e;},box=node('section'),part=node('select'),axis=node('select'),legend=node('p'),status=node('p'),svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
 box.dataset.fieldEquipmentTimeline='';Object.assign(box.style,{maxWidth:'100%',boxSizing:'border-box',overflowWrap:'anywhere'});
 box.append(node('h4','Native Field Channel Timeline'),node('p','Retail motion source only. Ten independent rigid parts, signed 12-bit translation and reduced PSX rotation. Choose a part and axis; click a sample or use Left/Right, Home/End to navigate and pause playback. No authored animation, native timing or interpolation is inferred.'));
 part.setAttribute('aria-label','Field timeline native part');for(let i=0;i<10;i++){const option=node('option',`Native Part ${i}`);option.value=String(i);part.append(option);}
 axis.setAttribute('aria-label','Field timeline channel axis');for(const field of fields)for(const a of axes){const option=node('option',`${field==='translation'?'Translation':'Rotation'} ${a.toUpperCase()}`);option.value=field+'.'+a;axis.append(option);}
 for(const input of [part,axis])Object.assign(input.style,{width:'100%',maxWidth:'100%',boxSizing:'border-box'});
 svg.setAttribute('viewBox','0 0 640 230');svg.setAttribute('role','slider');svg.setAttribute('aria-label','Field equipment native channel timeline');svg.setAttribute('aria-roledescription','Discrete native frame timeline');svg.setAttribute('tabindex','0');svg.setAttribute('aria-valuemin','0');Object.assign(svg.style,{width:'100%',height:'220px',display:'block',touchAction:'pan-y'});status.setAttribute('role','status');box.append(part,axis,legend,svg,status);host.append(box);
 let disposed=false,model=null,track=null,frame=0,graphs=new Map(),marker=null;
 const valid=()=>!disposed&&current()&&!busy()&&!!model;
 const el=(tag,attrs,text)=>{const e=document.createElementNS(svg.namespaceURI,tag);for(const [key,value] of Object.entries(attrs))e.setAttribute(key,String(value));if(text!==undefined)e.textContent=String(text);return e;};
 const x=f=>model.frameCount===1?336:48+f/(model.frameCount-1)*576;
 function select(){
  if(!model||!track||!marker)return;const row=track.samples[frame];if(!row)fail();const px=x(frame);marker.setAttribute('x1',String(px));marker.setAttribute('x2',String(px));marker.dataset.selectedFrame=String(frame);svg.setAttribute('aria-valuenow',String(frame));svg.setAttribute('aria-valuemax',String(model.frameCount-1));svg.setAttribute('aria-valuetext',`Frame ${frame}, native part ${track.part_index}, ${track.field}.${track.axis}, Retail source ${row.retail}`);box.dataset.frame=String(frame);
  status.textContent=`Frame ${frame} / ${model.frameCount-1} · Native Part ${track.part_index} · Retail ${track.field}.${track.axis}: ${row.retail}${track.field==='rotation_psx'?' PSX units (4096 per turn; stored in steps of 16)':' signed native units'} · opaque nibble ${row.opaque_nibble}. Source channel values only.`;
 }
 function draw(){
  if(!model)return;track=fieldEquipmentChannelTrack(model,Number(part.value),...axis.value.split('.'));const key=track.part_index+':'+track.field+':'+track.axis;
  if(!graphs.has(key)){
   const group=el('g',{'data-field-timeline-track':key}),low=track.min===track.max?track.min-1:track.min,high=track.min===track.max?track.max+1:track.max,y=v=>186-(v-low)/(high-low)*170;
   group.append(el('rect',{x:48,y:16,width:576,height:170,fill:'#101a20'}));
   for(const value of new Set([track.max,track.min]))group.append(el('text',{x:42,y:y(value)+4,'text-anchor':'end',fill:'#9faeb6','font-size':12},value));
   for(const row of track.samples){const dot=el('circle',{cx:x(row.frame),cy:y(row.retail),r:4,fill:'#68d7ec','data-frame':row.frame,'data-value':row.retail});dot.append(el('title',{},`Frame ${row.frame} · Retail ${track.field}.${track.axis}: ${row.retail}`));group.append(dot);}
   group.append(el('text',{x:48,y:211,fill:'#9faeb6','font-size':12},'0'),el('text',{x:624,y:211,'text-anchor':'end',fill:'#9faeb6','font-size':12},model.frameCount-1),el('text',{x:336,y:228,'text-anchor':'middle',fill:'#9faeb6','font-size':12},'Stored native frame index'));graphs.set(key,group);
  }
  if(!marker)marker=el('line',{y1:16,y2:186,stroke:'#fff','stroke-dasharray':'3 3','pointer-events':'none'});
  svg.replaceChildren(graphs.get(key),marker);select();
 }
 function update(){if(disposed)return;const blocked=!valid();part.disabled=axis.disabled=blocked;svg.setAttribute('aria-disabled',String(blocked));svg.setAttribute('tabindex',blocked?'-1':'0');}
 const redraw=()=>{if(!valid()){if(track){part.value=String(track.part_index);axis.value=track.field+'.'+track.axis;}return;}try{draw();}catch(e){onError(e);}};part.onchange=axis.onchange=redraw;
 svg.onclick=e=>{if(!valid()||!track)return;try{const dot=e.target.closest?.('circle[data-frame]'),rect=svg.getBoundingClientRect(),next=dot?Number(dot.dataset.frame):worldAnimationTimelineFrame(e.clientX,rect.left,rect.width,model.frameCount);onNavigate(next);}catch(error){onError(error);}};
 svg.onkeydown=e=>{if(!valid()||!track||!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();try{onNavigate(e.key==='Home'?0:e.key==='End'?model.frameCount-1:Math.max(0,Math.min(model.frameCount-1,frame+(e.key==='ArrowLeft'?-1:1))));}catch(error){onError(error);}};
 function clear(){model=track=marker=null;frame=0;graphs.clear();svg.replaceChildren();svg.removeAttribute('aria-valuenow');svg.removeAttribute('aria-valuemax');svg.removeAttribute('aria-valuetext');delete box.dataset.frame;legend.textContent='Inspect a qualified idle or walk variant to load Retail source channels.';status.textContent='No qualified field clip loaded.';update();}
 clear();return {set(next){if(disposed)return;if(!models.has(next))fail();clear();model=next;frame=next.initialFrame;part.value='0';axis.value='translation.x';legend.textContent=`${model.modelLayer==='current'?'Current model / Current textures':'Retail model / Retail textures'} · Retail ${model.clipId} motion source (cyan). Model and texture edits do not author these channels.`;draw();update();},frame(next){if(disposed||!model)return;if(!Number.isSafeInteger(next)||next<0||next>=model.frameCount)fail();frame=next;select();},update,clear,dispose(){disposed=true;clear();svg.onclick=svg.onkeydown=part.onchange=axis.onchange=null;box.remove();}};
}
