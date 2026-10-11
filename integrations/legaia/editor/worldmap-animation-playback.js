import {qualifyWorldAnimationPreview,poseWorldAnimationGeometry} from './worldmap-object-animation.js';
const fail=()=>{throw Error('World frame sampling requires a qualified clip, raw Current model and bounded display controls.');};
export async function createWorldAnimationSampler(preview,source){
  const bank=Uint8Array.from(atob(preview.bank_base64),c=>c.charCodeAt(0));
  await qualifyWorldAnimationPreview(preview,source,bank,preview.frame_index);
  const record=Uint8Array.from(atob(preview.record_base64),c=>c.charCodeAt(0)),geometry=structuredClone(source),frames=preview.frame_count,channels=preview.channel_count,signed=n=>n&2048?n-4096:n;
  return {frameCount:frames,initialFrame:preview.frame_index,recordHash:preview.record_sha256,bankHash:preview.bank_sha256,sample(frame){
    if(!Number.isSafeInteger(frame)||frame<0||frame>=frames)fail();
    const transforms=Array.from({length:channels},(_,i)=>{const at=8+(frame*channels+i)*8,d=record.slice(at,at+8);return {object_index:i,translation:[signed(d[0]+(d[2]&15)*256),signed(d[1]+(d[2]>>4)*256),signed(d[3]+(d[4]&15)*256)],rotation_psx:[d[5]*16,d[6]*16,d[7]*16],opaque_nibble:d[4]>>4};});
    return {frame_index:frame,object_transforms:transforms,geometry:poseWorldAnimationGeometry(geometry,transforms)};
  }};
}

export function sampledWorldFrame(start,count,fps,elapsed){
  if(!Number.isSafeInteger(count)||count<1||count>512||!Number.isSafeInteger(start)||start<0||start>=count||!Number.isSafeInteger(fps)||fps<1||fps>60||!Number.isFinite(elapsed)||elapsed<0)fail();
  return Math.min(count-1,start+Math.floor(elapsed*fps/1000));
}

export function mountWorldAnimationPlayback({host,current,busy,onFrame,onError,update:outerUpdate,labelPrefix='World animation',playLabel='Play sampled frames'}){
  const node=(tag,text)=>{const e=document.createElement(tag);if(text)e.textContent=text;return e;},panel=node('div'),scrub=node('input'),fps=node('input'),play=node('button',playLabel),note=node('p','Local one-pass display sampling only. Display fps does not establish native timing or looping.');
  panel.dataset.worldAnimationPlayback='';scrub.type='range';scrub.min='0';scrub.max='0';scrub.step='1';scrub.value='0';scrub.setAttribute('aria-label',`${labelPrefix} frame scrubber`);Object.assign(scrub.style,{width:'100%',boxSizing:'border-box'});
  fps.type='number';fps.min='1';fps.max='60';fps.step='1';fps.value='12';fps.setAttribute('aria-label',`${labelPrefix} display fps`);const label=node('label','Display fps (1–60)');label.append(fps);play.type='button';panel.append(scrub,label,play,note);host.append(panel);
  let sampler=null,index=0,start=0,rate=12,time=null,request=null,playing=false,disposed=false;
  const valid=()=>!disposed&&current()&&!busy(),number=()=>fps.value.trim()===''?NaN:Number(fps.value),validRate=()=>Number.isSafeInteger(number())&&number()>=1&&number()<=60;
  function refresh(){if(playing&&!valid())pause();scrub.disabled=!valid()||!sampler;fps.disabled=!valid()||!sampler;play.disabled=!valid()||!sampler||!validRate();play.textContent=playing?'Pause sampled frames':playLabel;panel.dataset.playing=String(playing);panel.dataset.frame=String(index);}
  function pause(){playing=false;if(request!==null)cancelAnimationFrame(request);request=null;time=null;refresh();}
  function display(frame){if(!valid()||!sampler)return false;const value=sampler.sample(frame);onFrame(value);index=frame;scrub.value=String(frame);refresh();return true;}
  function tick(now){request=null;if(!playing||!valid()){pause();return;}try{if(time===null)time=now;const frame=sampledWorldFrame(start,sampler.frameCount,rate,now-time);if(frame!==index)display(frame);if(frame===sampler.frameCount-1){pause();note.textContent='Last frame reached; one-pass sampling stopped. Native timing and looping remain unknown.';return;}request=requestAnimationFrame(tick);}catch(e){pause();note.textContent=e.message;onError(e);}}
  scrub.oninput=()=>{pause();try{display(Number(scrub.value));}catch(e){note.textContent=e.message;onError(e);}outerUpdate();};
  fps.oninput=()=>{pause();note.textContent=validRate()?'Display rate changed; native timing remains unknown.':'Choose a whole display fps from 1 to 60.';refresh();};
  play.onclick=()=>{if(play.disabled)return;if(playing){pause();return;}try{if(index===sampler.frameCount-1)display(0);start=index;rate=number();playing=true;time=null;note.textContent='Sampling packed source frames once at the selected display fps; no interpolation or runtime observation.';refresh();request=requestAnimationFrame(tick);}catch(e){pause();note.textContent=e.message;onError(e);}};
  const hidden=()=>{if(document.hidden)pause();};document.addEventListener('visibilitychange',hidden);
  refresh();return {update:refresh,set(value){pause();sampler=value;index=value.initialFrame;scrub.max=String(value.frameCount-1);scrub.value=String(index);note.textContent='Qualified clip retained locally; scrub or play one pass. Native timing and looping remain unknown.';refresh();},seek(frame){pause();return display(frame);},clear(){pause();sampler=null;index=0;scrub.max='0';scrub.value='0';refresh();},dispose(){disposed=true;pause();sampler=null;document.removeEventListener('visibilitychange',hidden);panel.remove();}};
}
