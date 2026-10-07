// Integer counter model of runtime/src/spu.c calc_vc_delta/adsr_run/key_on/key_off.
// No sample synthesis, runtime voice, driver transformation or note assignment.
export const ENVELOPE_RATE=44100,MAX_ENVELOPE_FRAMES=220500;
const integer=(v,max)=>Number.isSafeInteger(v)&&v>=0&&v<=max;
const names=['Attack','Decay','Sustain','Release','Off'];
function delta(zs,speed,exponential,decrease,invert,current){
 let increment=7-(speed&3),divider=32768;
 if(invert)increment=~increment;
 if(speed<44)increment<<=(47-speed)>>2;
 if(speed>=48)divider>>=(speed-44)>>2;
 if(exponential){if(decrease)increment=(current*increment)>>15;
 else if((current&32767)>=24576){if(speed<40)increment>>=2;else if(speed>=44)divider>>=2;else{increment>>=1;divider>>=1;}}}
 if(divider===0&&speed<zs)divider=1;
 return [increment,divider];
}
export function simulateEnvelope(adsr1,adsr2,{keyOffFrame=22050,frameCount=110250}={}){
 if(!integer(adsr1,65535)||!integer(adsr2,65535)||!integer(frameCount,MAX_ENVELOPE_FRAMES)||frameCount<1||!integer(keyOffFrame,frameCount-1))throw Error('Envelope preview requires native u16 words and a bounded explicit key-off window.');
 const attack=(adsr1>>>8)&127,decay=((adsr1>>>4)&15)<<2,sustain=(adsr2>>>6)&127,release=(adsr2&31)<<2,target=((adsr1&15)+1)<<11;
 const levels=new Uint16Array(frameCount),phases=new Uint8Array(frameCount);let level=0,divider=0,phase=0;
 for(let frame=0;frame<frameCount;frame++){
  if(frame===keyOffFrame){phase=3;divider=0;}
  if(phase!==4){
   if(phase===0&&level===32767)phase=1;
   const decrease=phase===1||phase===3||phase===2&&!!(adsr2&16384);
   const exponential=phase===0?!!(adsr1&32768):phase===1?true:phase===2?!!(adsr2&32768):!!(adsr2&32);
   const speed=[attack,decay,sustain,release][phase],zeroSpeed=phase===0||phase===2?127:124;
   const [increment,advance]=delta(zeroSpeed,speed,exponential,decrease,decrease,level);
   divider+=advance;
   if(divider&32768){const previous=level;divider=0;level=(level+increment)&65535;
    if(phase===0){if(((previous^level)&level)&32768)level=32767;}
    else if(level&32768)level=decrease?0:32767;
    if(phase===1&&level<target)phase=2;
   }
   if(phase===3&&level===0)phase=4;
  }
  levels[frame]=level;phases[frame]=phase;
 }
 return {model:'runtime-spu-counter-v1',adsr1,adsr2,sampleRate:ENVELOPE_RATE,keyOffFrame,frameCount,levels,phases,endPhase:names[phase],endLevel:level};
}

export function mountEnvelopePreview(host,{fresh=()=>true}={}){
 const el=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;},toggle=el('button','Show envelope counter preview'),keyOff=el('select'),label=el('label','Preview key-off time'),canvas=el('canvas'),status=el('p');
 canvas.width=720;canvas.height=220;Object.assign(canvas.style,{width:'100%',height:'220px'});canvas.setAttribute('aria-label','Retail Current and reviewed Proposed envelope counter curves');keyOff.setAttribute('aria-label','Envelope preview key-off');
 for(const ms of [250,500,1000,2000]){const option=el('option',ms+' ms');option.value=String(ms);keyOff.append(option);}keyOff.value='500';label.append(keyOff);status.setAttribute('role','status');host.append(el('h3','Envelope counter comparison'),el('p','44.1kHz SPU counter model, zero at key-on, with explicit key-off. No waveform, instrument assignment or game playback is inferred.'),toggle,label,canvas,status);
 let config=null,enabled=false;const cache=new Map(),observer=typeof ResizeObserver==='function'?new ResizeObserver(()=>{if(config&&enabled)draw();}):null;
 function clear(){observer?.disconnect();config=null;enabled=false;cache.clear();host.hidden=true;canvas.hidden=true;status.textContent='';}
 function draw(){if(config&&!fresh()){clear();return;}canvas.hidden=!enabled||!config;label.hidden=!enabled;toggle.textContent=enabled?'Hide envelope counter preview':'Show envelope counter preview';if(!enabled||!config){status.textContent='';return;}
  const off=Number(keyOff.value)*ENVELOPE_RATE/1000,ctx=canvas.getContext('2d');canvas.width=Math.max(240,Math.min(720,host.clientWidth||720));const right=canvas.width-10,span=right-42;ctx.clearRect(0,0,canvas.width,220);ctx.strokeStyle='#4a6066';ctx.beginPath();ctx.moveTo(42,12);ctx.lineTo(42,190);ctx.lineTo(right,190);ctx.stroke();ctx.fillStyle='#b5c9cf';ctx.font='12px sans-serif';ctx.fillText('32767',0,16);ctx.fillText('0',24,190);ctx.fillText('0 ms',42,210);ctx.fillText('2500 ms',canvas.width-60,210);const summaries=[];
  try{if(![250,500,1000,2000].includes(Number(keyOff.value)))throw Error('Choose an explicit envelope preview key-off time.');for(const row of config){const key=[row.adsr1,row.adsr2,off].join(':');let model=cache.get(key);if(!model){model=simulateEnvelope(row.adsr1,row.adsr2,{keyOffFrame:off});if(cache.size>=6)cache.clear();cache.set(key,model);}ctx.strokeStyle=row.color;ctx.lineWidth=1.5;ctx.beginPath();const points=[],width=Math.ceil(model.frameCount/512);for(let i=0;i<model.frameCount;i+=width){let low=32767,high=0;const end=Math.min(model.frameCount,i+width);for(let j=i;j<end;j++){low=Math.min(low,model.levels[j]);high=Math.max(high,model.levels[j]);}const x=42+(i+width/2)/model.frameCount*span;ctx.moveTo(x,190-high/32767*178);ctx.lineTo(x,190-low/32767*178);points.push([x,190-model.levels[end-1]/32767*178]);}ctx.stroke();ctx.beginPath();ctx.moveTo(42,190);for(const [x,y] of points)ctx.lineTo(x,y);ctx.stroke();summaries.push(row.label+': '+model.endPhase+' / counter '+model.endLevel);}ctx.strokeStyle='#ffffff';const x=42+off/110250*span;ctx.beginPath();ctx.moveTo(x,12);ctx.lineTo(x,190);ctx.stroke();status.textContent='Retail teal · Current blue · Reviewed Proposed orange · key-off '+keyOff.value+' ms. At 2500 ms: '+summaries.join('; ')+'. Unfinished phases remain bounded previews.';}
  catch(error){cache.clear();ctx.clearRect(0,0,canvas.width,220);status.textContent=error.message;}
 }
 toggle.onclick=()=>{if(!config)return;enabled=!enabled;draw();};keyOff.onchange=draw;
 return {update(rows){config=rows?structuredClone(rows):null;host.hidden=!config;toggle.disabled=!config;if(!config){observer?.disconnect();cache.clear();enabled=false;}else observer?.observe(host);draw();},clear};
}
