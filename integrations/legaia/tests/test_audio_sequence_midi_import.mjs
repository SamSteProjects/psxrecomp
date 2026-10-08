import assert from 'node:assert/strict';
import {encodeSequenceMidi} from '../editor/audio-sequence-midi.js';
import {sequenceMidiOperandEdits} from '../editor/audio-sequence-midi-import.js';
const h={ppqn:480,initial_tempo_us_per_quarter:500000,time_signature_numerator:4,time_signature_denominator_power:2};
const row=(index,status,kind,channel,values,delta_ticks=0,ticks=0)=>({index,offset:15+index*8,status,kind,channel,values,delta_ticks,ticks});
const report=events=>({header:h,complete:true,encoded_end_of_track:true,stop_reason:null,event_count:events.length,decoded_ticks:events.at(-1).ticks,events});
const source=report([row(0,144,'note_on',0,[60,100]),row(1,144,'note_on',0,[60,0],480,480),row(2,255,'end_of_track',null,[],0,480)]);
const before=structuredClone(source),midi=encodeSequenceMidi(source);
assert.deepEqual(sequenceMidiOperandEdits(midi,source),[]);
const edited=structuredClone(source);edited.events[0].values=[62,110];edited.events[1].values=[62,0];
assert.deepEqual(sequenceMidiOperandEdits(encodeSequenceMidi(edited),source),[{event_offset:15,values:[62,110]},{event_offset:23,values:[62,0]}]);
assert.deepEqual(source,before);
const wrap=new Uint8Array(midi.length+10);wrap.set(midi,5);assert.deepEqual(sequenceMidiOperandEdits(wrap.subarray(5,-5),source),[]);
// Literal track uses running status for the second channel event.
const running=[0,255,81,3,7,161,32,0,255,88,4,4,2,24,8,0,144,62,110,131,96,62,0,0,255,47,0];
const file=track=>{const b=new Uint8Array(22+track.length);b.set(midi.subarray(0,22));new DataView(b.buffer).setUint32(18,track.length);b.set(track,22);return b;};
assert.deepEqual(sequenceMidiOperandEdits(file(running),source),[{event_offset:15,values:[62,110]},{event_offset:23,values:[62,0]}]);
const kinds=['note_off','note_on','poly_aftertouch','control_change','program_change','channel_aftertouch','pitch_bend'];
const all=report([...kinds.map((k,i)=>row(i,(128+i*16)|15,k,15,i===4||i===5?[10]:[10,20])),row(7,255,'set_tempo',null,[600000]),row(8,255,'end_of_track',null,[])]);
const changed=structuredClone(all);for(const e of changed.events.slice(0,-1))e.values=e.values.map(v=>v+1);
assert.equal(sequenceMidiOperandEdits(encodeSequenceMidi(changed),all).length,8);
for(const [caseIndex,mutate] of [b=>b[8]=1,b=>b[11]=2,b=>b[12]=128,b=>b[13]++,b=>b[4]=1,b=>b[18]=1,b=>b[0]=0,b=>b[22]=128,b=>b[28]=0,b=>b[39]=145,b=>b[40]=128,b=>b[43]=97,b=>b[49]=1].entries()){
 const b=midi.slice();mutate(b);assert.throws(()=>sequenceMidiOperandEdits(b,source),undefined,`case ${caseIndex}`);
}
for(let i=0;i<midi.length;i++)assert.throws(()=>sequenceMidiOperandEdits(midi.subarray(0,i),source));
assert.throws(()=>sequenceMidiOperandEdits(file([...running,0]),source));
assert.throws(()=>sequenceMidiOperandEdits(file([...running.slice(0,19),0,255,1,0,...running.slice(19)]),source));
assert.throws(()=>sequenceMidiOperandEdits(new Uint8Array(512*1024+23),source));
const extent=n=>report([...Array.from({length:n},(_,i)=>row(i,192,'program_change',0,[1])),row(n,255,'end_of_track',null,[])]);
for(const n of [256,257]){const s=extent(n),e=structuredClone(s);for(const r of e.events.slice(0,-1))r.values=[2];if(n===256)assert.equal(sequenceMidiOperandEdits(encodeSequenceMidi(e),s).length,256);else assert.throws(()=>sequenceMidiOperandEdits(encodeSequenceMidi(e),s));}
console.log('Matching MIDI operands, literal running status, all channel families/tempo, byte views, immutability, malformed/partial/layout refusal and native extent passed');
