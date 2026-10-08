import {encodeSequenceMidi} from './audio-sequence-midi.js';

const kinds={0x80:'note_off',0x90:'note_on',0xa0:'poly_aftertouch',0xb0:'control_change',0xc0:'program_change',0xd0:'channel_aftertouch',0xe0:'pitch_bend'};
const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);

// Complete bounded SMF0 decoding shared by operand mapping and replacement review.
// Unsupported metadata refuses rather than being discarded.
export function decodeSequenceMidi(bytes){
  if(!(bytes instanceof Uint8Array)||bytes.length<26||bytes.length>512*1024+22)throw Error('Choose a MIDI file within the 512 KiB track budget.');
  const view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
  const tag=(i,s)=>[...s].every((c,j)=>bytes[i+j]===c.charCodeAt(0));
  if(!tag(0,'MThd')||view.getUint32(4)!==6||view.getUint16(8)!==0||view.getUint16(10)!==1||!tag(14,'MTrk')||view.getUint32(18)!==bytes.length-22)throw Error('Import requires one complete format-0 MIDI track with no extra chunks.');
  const ppqn=view.getUint16(12);if(ppqn<1||ppqn>32767)throw Error('MIDI requires metrical PPQN; SMPTE is unsupported.');
  let pos=22,ticks=0,running=null;
  const byte=()=>{if(pos>=bytes.length)throw Error('Truncated MIDI event.');return bytes[pos++];};
  const vlq=()=>{let n=0;for(let i=0;i<4;i++){const b=byte();n=n*128+(b&127);if(!(b&128))return n;}throw Error('MIDI variable-length value exceeds four bytes.');};
  const rows=[];
  while(pos<bytes.length){
    const delta_ticks=vlq();ticks+=delta_ticks;
    if(!Number.isSafeInteger(ticks)||ticks>0x7fffffff)throw Error('MIDI timing exceeds the native inspection budget.');
    let status=byte();
    if(status<128){if(running===null)throw Error('MIDI running status has no preceding channel status.');pos--;status=running;}
    let kind,channel=null,values;
    if(status===255){
      running=null;const type=byte(),length=vlq();
      if(length>bytes.length-pos)throw Error('Truncated MIDI meta event.');
      const data=bytes.subarray(pos,pos+length);pos+=length;
      if(type===0x51&&length===3){kind='set_tempo';values=[data[0]*65536+data[1]*256+data[2]];if(!values[0])throw Error('MIDI tempo must be positive.');}
      else if(type===0x58&&length===4){kind='time_signature';values=[...data];}
      else if(type===0x2f&&length===0){kind='end_of_track';values=[];if(pos!==bytes.length)throw Error('MIDI bytes follow end-of-track.');}
      else throw Error('Unsupported MIDI meta event; import does not discard metadata.');
    }else{
      kind=kinds[status&240];if(!kind)throw Error('MIDI system messages and SysEx are unsupported.');
      running=status;channel=status&15;values=Array.from({length:[0xc0,0xd0].includes(status&240)?1:2},byte);
      if(values.some(v=>v>127))throw Error('MIDI channel operands must be seven-bit values.');
    }
    rows.push({status,kind,channel,values,delta_ticks,ticks});
    if(rows.length>32770)throw Error('MIDI event count exceeds the import budget.');
  }
  if(rows.at(-1)?.kind!=='end_of_track')throw Error('MIDI requires a complete encoded ending.');
  return {ppqn,events:rows,decoded_ticks:ticks};
}
export function sequenceMidiOperandEdits(bytes,current){
  encodeSequenceMidi(current);
  const track=decodeSequenceMidi(bytes),rows=track.events;
  if(track.ppqn!==current.header.ppqn)throw Error('MIDI PPQN must match Current; timing conversion is not supported.');
  // Export's two anchors describe the native header, which the operand writer
  // cannot change. Notation/metronome bytes have no native counterpart.
  const tempo=rows.shift(),signature=rows.shift(),h=current.header;
  if(tempo?.kind!=='set_tempo'||tempo.ticks!==0||tempo.values[0]!==h.initial_tempo_us_per_quarter||signature?.kind!=='time_signature'||signature.ticks!==0||!equal(signature.values,[h.time_signature_numerator,h.time_signature_denominator_power,24,8]))throw Error('MIDI must retain the exported initial tempo and time-signature anchors.');
  if(rows.length!==current.events.length||rows.at(-1)?.kind!=='end_of_track')throw Error('MIDI event count and ending must match Current; event insertion and removal are unsupported.');
  const edits=[];let previous=-1;
  for(const [i,row] of rows.entries()){
    const source=current.events[i];
    if(!Number.isSafeInteger(source.offset)||source.offset<=previous)throw Error('Current native event offsets are invalid.');previous=source.offset;
    if(['status','kind','channel','delta_ticks','ticks'].some(k=>row[k]!==source[k]))throw Error(`MIDI event ${i} changes native event identity or timing.`);
    if(!equal(row.values,source.values))edits.push({event_offset:source.offset,values:[...row.values]});
  }
  if(edits.length>256)throw Error('MIDI import exceeds the native limit of 256 changed events.');
  return edits;
}
