import {placementDigest} from './worldmap-placement-replay.js';
import {worldAnimationTimelineFrame as pickFrame} from './worldmap-animation-timeline.js';
const fields=['translation','rotation_psx'],axes=['x','y','z'],fail=()=>{throw Error('Battle pack timeline requires the qualified Retail ANM, existing native part and axis.');};
const integer=(value,min,max)=>Number.isSafeInteger(value)&&value>=min&&value<=max;

export async function battlePackChannelTrack(playback,part,field,axis){
 const clip=playback?.clip,index=axes.indexOf(axis),source=clip?.source_record,recordIndex=source?.record_index,slot=integer(recordIndex,0,8)?0:integer(recordIndex,9,17)?1:integer(recordIndex,18,26)?2:null;
 if(!clip||slot===null||clip.model_asset_id!==`asset://legaia/models/battle-character/${String(slot).padStart(4,'0')}`||clip.semantic_id!==`animation://legaia/battle-character-pack/${String(recordIndex).padStart(4,'0')}`||clip.bone_count!==(slot===1?16:15)||!integer(clip.frame_count,1,512)||!integer(part,0,clip.bone_count-1)||!fields.includes(field)||index<0||source.prot_entry_index!==1203||source.container_section!==2||typeof playback.byteStream!=='function'||typeof playback.channel!=='function')fail();
 const bytes=playback.byteStream();
 if(!(bytes instanceof Uint8Array)||bytes.length!==16+clip.bone_count*clip.frame_count*8||bytes.length!==source.byte_length||bytes.length>262160||await placementDigest(bytes)!==source.sha256)fail();
 const view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
 if(view.getUint16(0,true)!==0x100+clip.bone_count||clip.header_a!==0x100+clip.bone_count||view.getUint16(2,true)!==clip.frame_count||view.getUint16(4,true)!==0x080c||![0x201,0x401,0x402].includes(clip.header_flags)||view.getUint16(6,true)!==clip.header_flags||bytes.subarray(-8).some(n=>n))fail();
 const signed=n=>n>=2048?n-4096:n,samples=[];
 for(let frame=0;frame<clip.frame_count;frame++){
  const at=8+(frame*clip.bone_count+part)*8,translation=[signed(bytes[at]+(bytes[at+2]&15)*256),signed(bytes[at+1]+(bytes[at+2]>>4)*256),signed(bytes[at+3]+(bytes[at+4]&15)*256)],rotation=[bytes[at+5]*16,bytes[at+6]*16,bytes[at+7]*16],row=playback.channel(frame,part);
  if(row?.object_index!==part||!Array.isArray(row.translation)||!Array.isArray(row.rotation_psx)||row.translation.length!==3||row.rotation_psx.length!==3||row.translation.some((v,i)=>v!==translation[i])||row.rotation_psx.some((v,i)=>v!==rotation[i])||row.opaque_nibble!==bytes[at+4]>>4)fail();
  samples.push(Object.freeze({frame,retail:field==='translation'?translation[index]:rotation[index]}));
 }
 return Object.freeze({animation_id:clip.semantic_id,part_index:part,field,axis,min:Math.min(...samples.map(s=>s.retail)),max:Math.max(...samples.map(s=>s.retail)),samples:Object.freeze(samples)});
}

export function mountBattlePackTimeline({host,getPlayback,getFrame,onFrame,current,busy,onError}){
 const node=(tag,text)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e;},box=node('section'),part=node('select'),axis=node('select'),svg=document.createElementNS('http://www.w3.org/2000/svg','svg'),status=node('p');
 box.dataset.battlePackTimeline='';Object.assign(box.style,{maxWidth:'100%',boxSizing:'border-box',overflowWrap:'anywhere'});box.append(node('h4','Native Battle Pack Channel Timeline'),node('p','Retail pack/viewer ANM samples, separate from PLAYER battle assembly. Click a frame or use Left/Right, Home/End. Native timing, interpolation and runtime use remain unresolved.'));
 part.setAttribute('aria-label','Battle Pack Timeline Native Part');axis.setAttribute('aria-label','Battle Pack Timeline Channel Axis');for(const field of fields)for(const a of axes){const option=node('option',`${field==='translation'?'Translation':'Rotation'} ${a.toUpperCase()}`);option.value=field+'.'+a;axis.append(option);}for(const input of [part,axis])Object.assign(input.style,{width:'100%',maxWidth:'100%',boxSizing:'border-box'});
 svg.setAttribute('viewBox','0 0 640 230');svg.setAttribute('role','group');svg.setAttribute('aria-label','Battle Pack Native Channel Timeline');svg.setAttribute('aria-roledescription','Discrete frame timeline');svg.setAttribute('tabindex','0');Object.assign(svg.style,{width:'100%',height:'220px',display:'block',touchAction:'pan-y'});status.setAttribute('role','status');const legend=node('p','Retail · Source Frames');legend.style.color='#68d7ec';box.append(part,axis,legend,svg,status);host.append(box);
 let disposed=false,identity=null,track=null,marker=null,drawing=null,loading=null,generation=0;
 const valid=()=>!disposed&&current(),el=(tag,attrs,text)=>{const e=document.createElementNS(svg.namespaceURI,tag);for(const [key,value] of Object.entries(attrs))e.setAttribute(key,String(value));if(text!==undefined)e.textContent=String(text);return e;};
 function clear(){generation++;track=marker=drawing=loading=null;svg.replaceChildren();svg.removeAttribute('aria-busy');}
 function selectFrame(){marker?.remove();marker=null;if(!track)return;const frame=getFrame(),row=track.samples[frame];if(!integer(frame,0,track.samples.length-1)||!row){status.textContent='Select an existing whole native frame.';return;}const x=track.samples.length===1?336:48+frame/(track.samples.length-1)*576;marker=el('line',{x1:x,x2:x,y1:16,y2:186,stroke:'#fff','stroke-dasharray':'3 3','data-selected-frame':frame});svg.append(marker);status.textContent=`Frame ${frame} · Native Part ${track.part_index} · ${track.field}.${track.axis}: Retail ${row.retail}. ${track.field==='translation'?'Signed native translation.':'Reduced eight-bit rotation × 16; 4096 native units per turn.'}`;}
 function draw(){svg.replaceChildren(el('rect',{x:48,y:16,width:576,height:170,fill:'#101a20'}));marker=null;const x=f=>track.samples.length===1?336:48+f/(track.samples.length-1)*576,low=track.min===track.max?track.min-1:track.min,high=track.min===track.max?track.max+1:track.max,y=v=>186-(v-low)/(high-low)*170;
  for(const n of new Set([track.max,track.min]))svg.append(el('text',{x:42,y:y(n)+4,'text-anchor':'end',fill:'#9faeb6','font-size':12},n));
  for(const row of track.samples){const dot=el('circle',{cx:x(row.frame),cy:y(row.retail),r:3,fill:'#68d7ec','data-frame':row.frame,'data-layer':'retail','data-value':row.retail});dot.append(el('title',{},`Frame ${row.frame} · Retail: ${row.retail}`));svg.append(dot);}
  svg.append(el('text',{x:48,y:211,fill:'#9faeb6','font-size':12},'0'),el('text',{x:624,y:211,fill:'#9faeb6','font-size':12,'text-anchor':'end'},track.samples.length-1),el('text',{x:336,y:228,fill:'#9faeb6','font-size':12,'text-anchor':'middle'},'Native frame index'));selectFrame();
 }
 function update(){
  if(disposed)return;const playback=getPlayback(),blocked=!valid()||busy()||!playback;box.hidden=!valid()||!playback;part.disabled=axis.disabled=blocked;svg.setAttribute('aria-disabled',String(blocked));
  if(!valid()||!playback){clear();identity=null;part.replaceChildren();status.textContent='Load a qualified Retail pack clip to view its native channels.';return;}
  if(playback!==identity){clear();identity=playback;part.replaceChildren();for(let p=0;p<(playback.clip?.bone_count??0);p++){const option=node('option',`Native Part ${p}`);option.value=String(p);part.append(option);}}
  const selected=part.value,chosenAxis=axis.value;
  if(track&&drawing?.playback===playback&&drawing.part===selected&&drawing.axis===chosenAxis){selectFrame();return;}
  if(loading?.playback===playback&&loading.part===selected&&loading.axis===chosenAxis)return;
  clear();const ticket=generation;loading={playback,part:selected,axis:chosenAxis};status.textContent='Qualifying Retail native channel samples…';svg.setAttribute('aria-busy','true');
  const [field,a]=chosenAxis.split('.');battlePackChannelTrack(playback,selected.trim()?Number(selected):NaN,field,a).then(value=>{if(!valid()||ticket!==generation||getPlayback()!==playback||part.value!==selected||axis.value!==chosenAxis)return;track=value;drawing={playback,part:selected,axis:chosenAxis};loading=null;svg.removeAttribute('aria-busy');draw();}).catch(error=>{if(valid()&&ticket===generation){loading=null;svg.removeAttribute('aria-busy');status.textContent=error.message;onError(error);}});
 }
 part.onchange=axis.onchange=()=>{if(!valid()||busy())return;update();};
 const pick=frame=>{if(!valid()||busy()||!track)return;onFrame(frame);update();};
 svg.onclick=e=>{if(!valid()||busy()||!track)return;try{const r=svg.getBoundingClientRect();pick(pickFrame(e.clientX,r.left,r.width,track.samples.length));}catch(error){onError(error);}};
 svg.onkeydown=e=>{if(!valid()||busy()||!track||!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();const f=getFrame(),frame=integer(f,0,track.samples.length-1)?f:0;try{pick(e.key==='Home'?0:e.key==='End'?track.samples.length-1:Math.max(0,Math.min(track.samples.length-1,frame+(e.key==='ArrowLeft'?-1:1))));}catch(error){onError(error);}};
 update();return {update,dispose(){disposed=true;clear();identity=null;svg.onclick=svg.onkeydown=part.onchange=axis.onchange=null;box.remove();}};
}
