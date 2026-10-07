// Offline decoded PCM × native counter preview. Explicit encoded PCM loop option.
import {simulateEnvelope,ENVELOPE_RATE,MAX_ENVELOPE_FRAMES} from './audio-envelope.js';
import {PREVIEW_RATES} from './audio-audition.js';
import {decodeSampleOptions,decodeSamplePcm,equal} from './audio-sample-contract.js';
import {encodedPcmLoop,validatePcmLoop,pcmLoopFrame} from './audio-pcm-loop.js';

export function renderEnvelopePcm(bytes,rate,adsr1,adsr2,window={},loop=null){
 if(!(bytes instanceof Uint8Array)||!bytes.length||bytes.length%2||bytes.length>229376||!PREVIEW_RATES.includes(rate))throw Error('Choose an explicit supported sample rate for bounded mono PCM.');
 const model=simulateEnvelope(adsr1,adsr2,window),output=new Uint8Array(model.frameCount*2),input=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),out=new DataView(output.buffer),frames=bytes.length/2;
 if(loop!==null)loop=validatePcmLoop(loop,frames);
 // Repeat already decoded PCM; predictor history is not re-decoded at a wrap.
 for(let i=0;i<model.frameCount;i++){
  const numerator=i*rate,position=Math.floor(numerator/ENVELOPE_RATE);if(position>=frames&&loop===null)break;
  const at=loop?pcmLoopFrame(position,frames,loop):position,next=loop?pcmLoopFrame(position+1,frames,loop):Math.min(at+1,frames-1);
  const fraction=(numerator%ENVELOPE_RATE)/ENVELOPE_RATE,a=input.getInt16(at*2,true),b=input.getInt16(next*2,true);
  out.setInt16(i*2,Math.trunc((a+(b-a)*fraction)*model.levels[i]/32768),true);
 }
 return {bytes:output,model,sourceRate:rate,outputRate:ENVELOPE_RATE,pcmLoop:loop};
}
export function encodeEnvelopeWav(bytes){
 if(!(bytes instanceof Uint8Array)||!bytes.length||bytes.length%2||bytes.length>MAX_ENVELOPE_FRAMES*2)throw Error('Envelope WAV requires a bounded 44.1kHz mono preview.');
 const wav=new Uint8Array(44+bytes.length),view=new DataView(wav.buffer),text=(at,s)=>{for(let i=0;i<s.length;i++)wav[at+i]=s.charCodeAt(i);};
 text(0,'RIFF');view.setUint32(4,wav.length-8,true);text(8,'WAVE');text(12,'fmt ');view.setUint32(16,16,true);view.setUint16(20,1,true);view.setUint16(22,1,true);view.setUint32(24,ENVELOPE_RATE,true);view.setUint32(28,ENVELOPE_RATE*2,true);view.setUint16(32,2,true);view.setUint16(34,16,true);text(36,'data');view.setUint32(40,bytes.length,true);wav.set(bytes,44);return wav;
}

export function mountEnvelopeAudition(host,{bank,fresh=()=>true,available=()=>true,request=fetch,onError=()=>{},audioContext=()=>new AudioContext()}){
 const el=(tag,text)=>{const node=document.createElement(tag);if(text!==undefined)node.textContent=text;return node;},layer=el('select'),rate=el('select'),off=el('select'),playback=el('select'),loopNote=el('p'),load=el('button','Load envelope sample'),play=el('button','Play envelope audition'),stop=el('button','Stop envelope audition'),save=el('button','Save envelope preview WAV'),volume=el('input'),status=el('p'),identity=el('p'),toolbar=el('div');
 const label=(title,node)=>{node.setAttribute('aria-label',title);const wrap=el('label',title);wrap.append(node);return wrap;};
 const blank=el('option','Choose preview sample rate');blank.value='';rate.append(blank);for(const hz of PREVIEW_RATES){const option=el('option',hz+' Hz (preview)');option.value=String(hz);rate.append(option);}rate.value='';
 for(const ms of [250,500,1000,2000]){const option=el('option',ms+' ms');option.value=String(ms);off.append(option);}off.value='500';for(const [value,title] of [['one-pass','One pass'],['encoded-loop','Encoded PCM loop']]){const option=el('option',title);option.value=value;playback.append(option);}playback.value='one-pass';volume.type='range';volume.min='0';volume.max='100';volume.value='20';
 Object.assign(toolbar.style,{display:'flex',flexWrap:'wrap',gap:'8px',alignItems:'end'});Object.assign(host.style,{width:'100%',minWidth:'0'});identity.style.overflowWrap='anywhere';status.setAttribute('role','status');status.setAttribute('data-envelope-audition-status','true');
 toolbar.append(label('Envelope audition layer',layer),label('Envelope sample rate',rate),label('Envelope audition key-off',off),label('Envelope sample playback',playback),load,play,stop,save,label('Envelope audition volume',volume));
 host.append(el('h3','Envelope sample audition'),el('p','Decoded sample × 44.1kHz SPU counter model, with linear preview resampling and explicit key-off. Sample rate is your choice. Optional encoded PCM looping repeats decoded frames through Release; it does not re-decode ADPCM predictor history or establish native looping. No inferred note pitch, Gaussian filter, driver transformation or game mix. Local unreviewed drafts are excluded. WAV uses full preview level; playback volume defaults to 20%.'),identity,toolbar,loopNote,status);
 let config=null,controller=null,loading=false,starting=false,context=null,gain=null,source=null,generation=0;const cache=new Map();
 const selected=()=>config?.layers.find(row=>row.label===layer.value),pcmKey=row=>[row.pcmLayer,row.sampleIndex].join(':'),cached=()=>{const row=selected();return row?cache.get(pcmKey(row)):null;};
 function halt(){generation++;starting=false;if(source){const held=source;source=null;held.onended=null;try{held.stop();}catch{}held.disconnect();}}
 function release(){controller?.abort();controller=null;loading=false;halt();cache.clear();gain?.disconnect();gain=null;if(context){context.close().catch(()=>{});context=null;}}
 function clear(){release();config=null;host.hidden=true;identity.textContent=status.textContent='';refresh();}
 function current(){if(!config)return false;if(!fresh()){clear();return false;}return true;}
 function refresh(){const loop=cached()?.loop??null,option=playback.children[1];option.disabled=!loop;if(playback.value==='encoded-loop'&&!loop)playback.value='one-pass';loopNote.textContent=loop?'Encoded PCM loop: source frames '+loop.startFrame+'–'+(loop.endFrame-1)+'; intro plays once, last encoded loop-start before end/repeat is used. Bounded preview only.':'Encoded PCM loop unavailable: load a complete sample with explicit loop-start and end/repeat markers. No loop point is guessed.';const row=selected(),unavailable=!config||!available()||loading||starting;for(const node of [layer,rate,off,playback,load,play,save,volume])node.disabled=unavailable;load.disabled=unavailable||!Number.isSafeInteger(row?.sampleIndex)||Boolean(cached());play.disabled=save.disabled=unavailable||!cached()||!PREVIEW_RATES.includes(Number(rate.value))||![250,500,1000,2000].includes(Number(off.value));stop.disabled=!source&&!starting;}
 function describe(){const row=selected();identity.textContent=row?row.label+' · '+(Number.isSafeInteger(row.sampleIndex)?'sample '+(row.sampleIndex+1)+' (encoded operand)':'no in-range sample operand')+' · ADSR1 '+row.adsr1+' · ADSR2 '+row.adsr2+' · '+(row.pcmLayer==='retail'?'Retail sample bytes':'Current sample bytes')+(row.reviewKey?' · reviewed proposal '+row.reviewKey:''):'';}
 async function post(path,body,signal){const response=await request(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal}),raw=await response.text();if(new TextEncoder().encode(raw).length>2*1024*1024)throw Error('Envelope sample metadata exceeds its response budget.');const value=JSON.parse(raw);if(!response.ok||value.error)throw Error(value.error??'Envelope sample request failed.');return value;}
 load.onclick=async()=>{
  if(!current()||load.disabled)return;const row=selected(),owned=config,token=++generation,operation=new AbortController();controller=operation;loading=true;refresh();status.textContent='Qualifying '+row.label+' sample bytes…';
  const valid=()=>current()&&config===owned&&token===generation;
  try{
   const sample=bank.samples[row.sampleIndex];if(!sample)throw Error('No qualified sample for this encoded operand.');
   const base={asset_id:bank.asset_id,expected_entry_sha256:bank.source_record.entry_sha256,sample_index:sample.index,expected_authoring_key:owned.context.authoringKey};
   const options=decodeSampleOptions(await post('/api/audio-sample-authoring',base,operation.signal),owned.context,bank,sample);if(!valid())return;
   if(options.current_entry_sha256!==owned.currentEntryHash)throw Error('Current sample entry differs from the inspected bank.');
   const sha=row.pcmLayer==='retail'?sample.source_sha256:options.current_sample_sha256,dto=await post('/api/audio-sample-preview',{...base,layer:row.pcmLayer,expected_sample_sha256:sha},operation.signal);if(!valid())return;
   const decoded=await decodeSamplePcm(dto,owned.context,bank,sample,row.pcmLayer,sha);if(!valid())return;
   if(!equal(decoded.waveform,options[row.pcmLayer]))throw Error('Sample waveform changed after qualification.');cache.set(pcmKey(row),{bytes:decoded.bytes,loop:encodedPcmLoop(decoded.waveform,decoded.bytes.length/2)});status.textContent=decoded.bytes.length/2+' verified source frames. Choose a sample rate to audition; game pitch remains unverified.';
  }catch(error){if(!operation.signal.aborted&&valid()){status.textContent=error.message;onError(error);}}finally{if(config===owned&&controller===operation){controller=null;loading=false;refresh();}}
 };
 const rendered=()=>{const row=selected();return renderEnvelopePcm(cached().bytes,Number(rate.value),row.adsr1,row.adsr2,{keyOffFrame:Number(off.value)*ENVELOPE_RATE/1000},playback.value==='encoded-loop'?cached().loop:null);};
 const change=()=>{if(!current())return;halt();describe();status.textContent='Preview selection changed; choose Play or Save. No project change.';refresh();};layer.onchange=rate.onchange=off.onchange=playback.onchange=change;
 volume.oninput=()=>{if(current()&&gain&&Number.isFinite(Number(volume.value)))gain.gain.value=Math.max(0,Math.min(100,Number(volume.value)))/100;};
 play.onclick=async()=>{
  if(!current()||play.disabled)return;halt();const token=generation;starting=true;refresh();
  try{const preview=rendered();if(!context){context=audioContext();gain=context.createGain();gain.connect(context.destination);}await context.resume();if(!current()||token!==generation)return;
   const buffer=context.createBuffer(1,preview.bytes.length/2,ENVELOPE_RATE),channel=buffer.getChannelData(0),view=new DataView(preview.bytes.buffer);for(let i=0;i<channel.length;i++)channel[i]=view.getInt16(i*2,true)/32768;
   gain.gain.value=Math.max(0,Math.min(100,Number(volume.value)))/100;source=context.createBufferSource();source.buffer=buffer;source.loop=false;source.connect(gain);source.onended=()=>{if(token!==generation)return;source?.disconnect();source=null;if(current()){status.textContent='Envelope sample preview ended.';refresh();}};source.start();starting=false;status.textContent='Playing '+layer.value+' · sample rate '+rate.value+' Hz · output 44100 Hz · key-off '+off.value+' ms · 2500 ms window · '+(preview.pcmLoop?'encoded PCM loop':'one pass')+'.';refresh();
  }catch(error){if(current()&&token===generation){halt();status.textContent=error.message;onError(error);refresh();}}
 };
 stop.onclick=()=>{halt();status.textContent='Envelope sample preview stopped.';refresh();};
 save.onclick=()=>{if(!current()||save.disabled)return;try{const preview=rendered(),url=URL.createObjectURL(new Blob([encodeEnvelopeWav(preview.bytes)],{type:'audio/wav'})),anchor=el('a');anchor.href=url;anchor.download=bank.asset_id.split('/').at(-1)+'-sample-'+(selected().sampleIndex+1)+'-'+layer.value.toLowerCase().replaceAll(' ','-')+(preview.pcmLoop?'-encoded-pcm-loop':'')+'-envelope-'+rate.value+'Hz-keyoff-'+off.value+'ms.wav';anchor.click();setTimeout(()=>URL.revokeObjectURL(url),0);status.textContent='Saved bounded offline envelope WAV. Project and native bank are unchanged.';}catch(error){status.textContent=error.message;onError(error);}};
 clear();return {update(value){if(equal(config,value)){refresh();return;}release();config=value?structuredClone(value):null;host.hidden=!config;layer.replaceChildren();for(const row of config?.layers??[]){const option=el('option',row.label);option.value=row.label;layer.append(option);}layer.value=config?.layers[0]?.label??'';rate.value='';playback.value='one-pass';describe();status.textContent=config?'Load the selected qualified sample; no project change.':'';refresh();},clear,refresh};
}
