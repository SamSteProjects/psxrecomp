import {playerActionChannelTrack} from './player-action-timeline.js';
import {worldAnimationTimelineFrame} from './worldmap-animation-timeline.js';

// The inspector supplies this receipt only after independent ME/model replay.
export function playerArtChannelTrack(receipt,part,field,axis){
  if(receipt?.schema_version!=='legaia.player-art-playback.v1'||receipt.timing!=='not_observed')throw Error('Inspect a qualified PLAYER art stream first.');
  return playerActionChannelTrack({current_clip:receipt.stream,original_action_base64:receipt.decoded_stream_base64,current_action_base64:receipt.decoded_stream_base64},part,field,axis);
}

export function mountPlayerArtTimeline({host,getState,current,busy,onFrame,onError,labelPrefix="PLAYER Art",title="Native PLAYER Art Channel Timeline",note="Original ME channels for either geometry layer. Discrete frames; rotation uses packed PSX units. Native timing and interpolation are unobserved.",trackFor=playerArtChannelTrack,layers=["retail"]}){
  const node=(tag,text)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e;};
  const box=node('section'),part=node('select'),axis=node('select'),status=node('p'),svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
  box.dataset.playerArtTimeline='';part.setAttribute('aria-label',`${labelPrefix} Timeline Native Part`);axis.setAttribute('aria-label',`${labelPrefix} Timeline Channel Axis`);
  for(const field of ['translation','rotation_psx'])for(const a of 'xyz'){const option=node('option',`${field==='translation'?'Translation':'Rotation'} ${a.toUpperCase()}`);option.value=field+'.'+a;axis.append(option);}
  for(const input of [part,axis])Object.assign(input.style,{width:'100%',boxSizing:'border-box'});
  svg.setAttribute('viewBox','0 0 640 230');svg.setAttribute('role','group');svg.setAttribute('aria-label',`${labelPrefix} Native Channel Timeline`);svg.setAttribute('tabindex','0');Object.assign(svg.style,{width:'100%',height:'220px',display:'block'});
  box.append(node('h4',title),node('p',note),part,axis,svg,status);host.append(box);
  let disposed=false,identity=null,track=null;
  const valid=()=>!disposed&&current()&&!busy(),el=(tag,attrs,text)=>{const e=document.createElementNS(svg.namespaceURI,tag);for(const [k,v]of Object.entries(attrs))e.setAttribute(k,String(v));if(text!==undefined)e.textContent=String(text);return e;};
  function update(){if(disposed)return;const s=getState();box.hidden=!s.receipt;part.disabled=axis.disabled=!valid()||!s.receipt;svg.setAttribute('aria-disabled',String(!valid()||!s.receipt));track=null;svg.replaceChildren();if(!s.receipt)return;
    try{const key=s.receipt.stream.semantic_id;if(key!==identity){part.replaceChildren();for(let i=0;i<s.receipt.stream.part_count;i++){const o=node('option',`Native Part ${i}`);o.value=String(i);part.append(o);}identity=key;}
      const [field,a]=axis.value.split('.');track=trackFor(s.receipt,Number(part.value),field,a);const x=f=>track.samples.length===1?336:48+576*f/(track.samples.length-1),y=v=>190-150*(v-track.min)/Math.max(1,track.max-track.min);
      svg.append(el('path',{d:'M48 32V190H624',fill:'none',stroke:'#63747e'}));for(const [layer,color]of [['retail','#68d7ec'],['current','#f2b66d'],['proposed','#c49bff']]){if(!layers.includes(layer)||track.samples[0][layer]===undefined)continue;for(const row of track.samples)svg.append(el('circle',{cx:x(row.frame),cy:y(row[layer]),r:2,fill:color,'data-layer':layer}));}
      const row=track.samples[s.frame];if(row){svg.append(el('line',{x1:x(s.frame),x2:x(s.frame),y1:30,y2:193,stroke:'#fff','data-selected-frame':s.frame}));status.textContent=`Native Part ${track.part_index} · Frame ${s.frame} · ${field} ${a.toUpperCase()}: ${layers.filter(k=>row[k]!==undefined).map(k=>`${k}: ${row[k]}`).join(' · ')} · Range ${track.min} to ${track.max}`;}else status.textContent='Choose an existing whole native frame.';
      svg.append(el('text',{x:48,y:211,fill:'#9faeb6'},'0'),el('text',{x:624,y:211,fill:'#9faeb6','text-anchor':'end'},track.samples.length-1));
    }catch(error){track=null;svg.replaceChildren();status.textContent=error.message;onError(error);}
  }
  part.onchange=axis.onchange=update;
  svg.onclick=e=>{if(!valid()||!track)return;const r=svg.getBoundingClientRect();onFrame(worldAnimationTimelineFrame(e.clientX,r.left,r.width,track.samples.length));};
  svg.onkeydown=e=>{if(!valid()||!track||!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();const n=getState().frame;onFrame(e.key==='Home'?0:e.key==='End'?track.samples.length-1:Math.max(0,Math.min(track.samples.length-1,n+(e.key==='ArrowLeft'?-1:1))));};
  update();return {update,dispose(){disposed=true;svg.onclick=svg.onkeydown=null;box.remove();}};
}
