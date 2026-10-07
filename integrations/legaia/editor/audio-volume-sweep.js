// runtime/src/spu.c sweep_env_write/step/chan_volume, under a continuous active mix clock.
// Its phase/sign-domain choice is documented as unverified against hardware.
import {MAX_ENVELOPE_FRAMES,spuCounterDelta} from './audio-envelope.js';
import {directVoiceVolume} from './audio-static-stereo.js';
export function simulateVolumeRegister(raw,initialLevel,frameCount){
 if(!Number.isSafeInteger(raw)||raw<0||raw>65535||!Number.isSafeInteger(initialLevel)||initialLevel< -32768||initialLevel>32767||!Number.isSafeInteger(frameCount)||frameCount<1||frameCount>MAX_ENVELOPE_FRAMES)throw Error('Choose a u16 volume register, signed16 starting level and bounded preview window.');
 const levels=new Int16Array(frameCount),sweep=!!(raw&32768),exponential=!!(raw&16384),decrease=!!(raw&8192),negative=!!(raw&4096),rate=raw&127;
 let level=sweep?initialLevel:directVoiceVolume(raw),divider=0;
 for(let frame=0;frame<frameCount;frame++){
  if(sweep){let working=Math.max(0,Math.min(32767,negative?-level:level));const [increment,advance]=spuCounterDelta(127,rate,exponential,decrease,decrease,working);divider+=advance;if(divider&32768){divider=0;working=Math.max(0,Math.min(32767,working+increment));level=negative?-working:working;}}
  levels[frame]=level;
 }
 return {model:'recomp-sweep-counter-v1',clock:'continuous-active-mix-window',raw,initialLevel,initialDivider:0,frameCount,levels,finalLevel:level,finalDivider:divider,sweep};
}
export function renderSweepStereo(bytes,registers,initialLevels){
 if(!(bytes instanceof Uint8Array)||!bytes.length||bytes.length%2||bytes.length>MAX_ENVELOPE_FRAMES*2||!Array.isArray(registers)||registers.length!==2||!Array.isArray(initialLevels)||initialLevels.length!==2)throw Error('Volume sweep audition needs bounded mono PCM and two explicit registers/starting levels.');
 const curves=registers.map((raw,i)=>simulateVolumeRegister(raw,initialLevels[i],bytes.length/2)),input=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),output=new Uint8Array(bytes.length*2),view=new DataView(output.buffer);
 for(let frame=0;frame<bytes.length/2;frame++)for(let c=0;c<2;c++)view.setInt16((frame*2+c)*2,Math.max(-32768,Math.min(32767,Math.floor(input.getInt16(frame*2,true)*curves[c].levels[frame]/32768))),true);
 return {bytes:output,channels:2,frameCount:bytes.length/2,registers:[...registers],initialLevels:[...initialLevels],finalLevels:curves.map(row=>row.finalLevel),volumeMode:'register-sweep',counterModel:curves[0].model,clockModel:curves[0].clock};
}
