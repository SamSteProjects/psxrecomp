import {MAX_ENVELOPE_FRAMES} from './audio-envelope.js';
export function directVoiceVolume(raw){
 if(!Number.isSafeInteger(raw)||raw<0||raw>32767)throw Error('Static voice register must be an integer0..32767; sweep mode is unsupported.');
 return raw<16384?raw*2:(raw-32768)*2;
}
// One post-envelope voice, static direct volumes, saturating stereo bus.
// runtime/src/spu.c volume_reg_decode, voice cl/cr >>15, clamp16 bus.
export function renderStaticStereo(bytes,left,right){
 if(!(bytes instanceof Uint8Array)||!bytes.length||bytes.length%2||bytes.length>MAX_ENVELOPE_FRAMES*2)throw Error('Static stereo requires bounded signed16 mono envelope PCM.');
 const gains=[directVoiceVolume(left),directVoiceVolume(right)],input=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),output=new Uint8Array(bytes.length*2),view=new DataView(output.buffer);
 for(let i=0;i<bytes.length/2;i++)for(let channel=0;channel<2;channel++)view.setInt16((i*2+channel)*2,Math.max(-32768,Math.min(32767,Math.floor(input.getInt16(i*2,true)*gains[channel]/32768))),true);
 return {bytes:output,channels:2,frameCount:bytes.length/2,registers:[left,right],effectiveGains:gains};
}
