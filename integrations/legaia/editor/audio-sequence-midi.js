// Standard MIDI File format 0. This is encoded interchange, not game synthesis.
const integer=(v,a,b)=>Number.isSafeInteger(v)&&v>=a&&v<=b;
const kinds={0x80:'note_off',0x90:'note_on',0xa0:'poly_aftertouch',0xb0:'control_change',0xc0:'program_change',0xd0:'channel_aftertouch',0xe0:'pitch_bend'};
const vlq=value=>{const bytes=[value&127];while((value=Math.floor(value/128))>0)bytes.unshift((value&127)|128);return bytes;};
export function encodeSequenceMidi(report){
  const h=report?.header,events=report?.events;
  if(report?.complete!==true||report.encoded_end_of_track!==true||report.stop_reason!==null||!h||!integer(h.ppqn,1,32767)||!integer(h.initial_tempo_us_per_quarter,1,16777215)||!integer(h.time_signature_numerator,1,255)||!integer(h.time_signature_denominator_power,0,7)||!Array.isArray(events)||!integer(events.length,1,32768)||report.event_count!==events.length)throw Error('MIDI export requires a complete decoded track, an encoded ending and PPQN within 1–32767.');
  const tempo=n=>[(n>>16)&255,(n>>8)&255,n&255];
  // Metronome and notation fields use SMF conventions; SEQ declares neither.
  const track=[0,255,0x51,3,...tempo(h.initial_tempo_us_per_quarter),0,255,0x58,4,h.time_signature_numerator,h.time_signature_denominator_power,24,8];
  let ticks=0;
  for(const [i,e] of events.entries()){
    if(e?.index!==i||!integer(e.delta_ticks,0,0x0fffffff)||!integer(e.status,128,255)||!Array.isArray(e.values)||!integer(ticks+e.delta_ticks,0,0x7fffffff)||(ticks+=e.delta_ticks)!==e.ticks)throw Error('MIDI export encountered invalid event timing or identity.');
    track.push(...vlq(e.delta_ticks));
    if(e.kind==='set_tempo'){
      if(e.status!==255||e.channel!==null||e.values.length!==1||!integer(e.values[0],1,16777215))throw Error('Invalid encoded tempo event.');
      track.push(255,0x51,3,...tempo(e.values[0]));
    }else if(e.kind==='end_of_track'){
      if(i!==events.length-1||e.status!==255||e.channel!==null||e.values.length)throw Error('Only the final encoded end-of-track can terminate MIDI export.');
      track.push(255,0x2f,0);
    }else{
      const status=e.status&0xf0,width=[0xc0,0xd0].includes(status)?1:2;
      if(i===events.length-1||kinds[status]!==e.kind||e.channel!==(e.status&15)||e.values.length!==width||e.values.some(v=>!integer(v,0,127)))throw Error('Invalid or unresolved channel event in MIDI export.');
      track.push(e.status,...e.values); // Explicit status also after SEQ meta events.
    }
  }
  if(ticks!==report.decoded_ticks||events.at(-1).kind!=='end_of_track'||track.length>512*1024)throw Error('MIDI export timing, ending or byte budget differs from the decoded track.');
  const bytes=new Uint8Array(22+track.length),view=new DataView(bytes.buffer);
  bytes.set([77,84,104,100,0,0,0,6,0,0,0,1,h.ppqn>>8,h.ppqn&255,77,84,114,107]);view.setUint32(18,track.length,false);bytes.set(track,22);return bytes;
}
export function downloadSequenceMidi(report,filename){
  const bytes=encodeSequenceMidi(report),url=URL.createObjectURL(new Blob([bytes],{type:'audio/midi'})),link=document.createElement('a');link.href=url;link.download=filename;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);return bytes.length;
}
