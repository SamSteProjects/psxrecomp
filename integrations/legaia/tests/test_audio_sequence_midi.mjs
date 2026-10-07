import assert from 'node:assert/strict';
import {encodeSequenceMidi} from '../editor/audio-sequence-midi.js';
const header={ppqn:480,initial_tempo_us_per_quarter:500000,time_signature_numerator:4,time_signature_denominator_power:2};
const event=(index,status,kind,channel,values,delta_ticks=0,ticks=0)=>({index,status,kind,channel,values,delta_ticks,ticks});
const report={header,complete:true,encoded_end_of_track:true,stop_reason:null,event_count:3,decoded_ticks:480,events:[event(0,0x90,'note_on',0,[60,100]),event(1,0x90,'note_on',0,[60,0],480,480),event(2,255,'end_of_track',null,[],0,480)]};
const before=structuredClone(report),bytes=encodeSequenceMidi(report);
const literal=[0,255,81,3,7,161,32,0,255,88,4,4,2,24,8,0,144,60,100,131,96,144,60,0,0,255,47,0];
assert.deepEqual([...bytes],[77,84,104,100,0,0,0,6,0,0,0,1,1,224,77,84,114,107,0,0,0,literal.length,...literal]);assert.deepEqual(report,before);
// Independent reader checks standard chunk lengths, meta sizes and event delta times.
export function readMidi(bytes){
 const data=Buffer.from(bytes);assert.equal(data.toString('ascii',0,4),'MThd');assert.equal(data.readUInt32BE(4),6);assert.equal(data.readUInt16BE(8),0);assert.equal(data.readUInt16BE(10),1);assert.equal(data.toString('ascii',14,18),'MTrk');assert.equal(data.readUInt32BE(18),data.length-22);
 let pos=22,ticks=0;const rows=[];while(pos<data.length){let delta=0,b;do{b=data[pos++];delta=delta*128+(b&127);}while(b&128);ticks+=delta;const status=data[pos++];let values,kind;if(status===255){kind=data[pos++];const n=data[pos++];values=[...data.subarray(pos,pos+n)];pos+=n;}else{kind=status&240;const n=kind===192||kind===208?1:2;values=[...data.subarray(pos,pos+n)];pos+=n;}rows.push({delta,ticks,status,kind,values});}assert.equal(pos,data.length);assert.equal(rows.at(-1).kind,47);return {ppqn:data.readUInt16BE(12),rows};
}
const parsed=readMidi(bytes);assert.equal(parsed.ppqn,480);assert.equal(parsed.rows.at(-1).ticks,480);assert.deepEqual(parsed.rows[3].values,[60,0]);
const kinds=['note_off','note_on','poly_aftertouch','control_change','program_change','channel_aftertouch','pitch_bend'];let ticks=0;const events=kinds.map((kind,i)=>{const delta=[0,127,128,16383,16384,2097151,268435455][i];ticks+=delta;return event(i,(128+i*16)|15,kind,15,i===4||i===5?[127]:[0,127],delta,ticks);});events.push(event(7,255,'set_tempo',null,[600000],0,ticks),event(8,0x9f,'note_on',15,[42,1],0,ticks),event(9,255,'end_of_track',null,[],1,++ticks));const all={...report,events,event_count:events.length,decoded_ticks:ticks};const decoded=readMidi(encodeSequenceMidi(all));assert.equal(decoded.rows.at(-1).ticks,ticks);assert.deepEqual(decoded.rows.at(-2).values,[42,1]);
for(const change of [r=>r.complete=false,r=>r.encoded_end_of_track=false,r=>r.stop_reason='partial',r=>r.header.ppqn=32768,r=>r.header.ppqn=0,r=>r.events[0].values[0]=128,r=>r.events[0].channel=1,r=>r.events[0].kind='unknown',r=>r.events[1].delta_ticks=0x10000000,r=>r.events[1].ticks++,r=>r.events[0].index=1,r=>r.events[2].values=[0],r=>r.events[2].kind='note_on',r=>r.decoded_ticks++,r=>r.event_count--]){const bad=structuredClone(report);change(bad);assert.throws(()=>encodeSequenceMidi(bad));}
console.log('SMF literal bytes, all channel families, meta lengths, VLQ boundaries, exact ticks, immutability and partial/malformed refusal passed');
