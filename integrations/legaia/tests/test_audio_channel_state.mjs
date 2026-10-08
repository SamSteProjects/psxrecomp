import assert from 'node:assert/strict';
import {encodedChannelState,createChannelStateInspector} from '../editor/audio-channel-state.js';
const events=[],add=(kind,channel,values,ticks=0)=>events.push({index:events.length,offset:15+events.length*4,end_offset:19+events.length*4,kind,channel,values,ticks,time_seconds:ticks/480});
add('note_on',0,[60,100]);add('program_change',0,[0]);add('program_change',1,[12]);
add('control_change',0,[64,127]);add('control_change',0,[121,0]);add('control_change',0,[64,1]);
add('pitch_bend',0,[0,0]);add('pitch_bend',1,[127,127]);add('poly_aftertouch',0,[60,24]);
add('channel_aftertouch',0,[0]);add('set_tempo',null,[500000],10);add('end_of_track',null,[],10);
const report={events,complete:true},before=structuredClone(report);
const initial=encodedChannelState(report,0,0);assert.equal(initial.program,null);assert.equal(initial.pitch_wheel,null);assert.deepEqual(initial.controllers,{});
assert.equal(encodedChannelState(report,1,0).program.value,0);assert.equal(encodedChannelState(report,4,0).controllers[64].value,127);
const state=encodedChannelState(report,11,0);assert.deepEqual(state.controllers[64],{value:1,event_index:5,offset:35,end_offset:39});assert.equal(state.controllers[121].value,0);assert.equal(state.pitch_wheel.value,0);assert.equal(state.channel_pressure.value,0);assert.equal(state.key_pressure[60].value,24);assert.equal(state.driver_effects,'not_evaluated');assert.equal(state.ticks,10);
const other=encodedChannelState(report,11,1);assert.equal(other.program.value,12);assert.equal(other.pitch_wheel.value,16383);assert.deepEqual(other.controllers,{});assert.equal(other.channel_pressure,null);
state.controllers[64].value=88;assert.deepEqual(report,before);
assert.equal(encodedChannelState({...report,complete:false},9,0).complete_source,false);
for(const [index,ch] of [[-1,0],[12,0],[0,-1],[0,16],[0,NaN]])assert.throws(()=>encodedChannelState(report,index,ch));
for(const change of [r=>r.events[0].index=1,r=>r.events[0].values[0]=128,r=>r.events[0].offset=-1,r=>r.events[0].time_seconds=NaN,r=>r.events[0].channel=null,r=>r.events[0].kind='unknown',r=>r.events[0].values.push(0),r=>r.events[1].ticks=-1]){const bad=structuredClone(report);change(bad);assert.throws(()=>encodedChannelState(bad,11,0));}
const dense={complete:false,events:Array.from({length:32768},(_,i)=>({index:i,offset:15+i*4,end_offset:19+i*4,kind:'control_change',channel:0,values:[1,i%128],ticks:i,time_seconds:i}))};assert.equal(encodedChannelState(dense,32767,0).controllers[1].event_index,32767);assert.throws(()=>encodedChannelState({...dense,events:[...dense.events,dense.events[0]]},0,0));
class Element{constructor(tag){this.tag=tag;this.children=[];this.style={};this.textContent='';this.value='';}append(...nodes){this.children.push(...nodes);}replaceChildren(...nodes){this.children=nodes;}setAttribute(k,v){this[k]=v;}remove(){this.removed=true;}}
globalThis.document={createElement:tag=>new Element(tag)};
const text=n=>[n.textContent,...n.children.map(text)].join(' '),find=(n,tag)=>n.tag===tag?n:n.children.map(c=>find(c,tag)).find(Boolean);
let fresh=true,busy=false;const view=createChannelStateInspector({fresh:()=>fresh,busy:()=>busy});
view.setLayers([['Source',report]],0);assert(text(view.root).includes('Unknown'));const select=find(view.root,'select');assert.equal(select.value,'0');select.value='1';select.onchange();assert(text(view.root).includes('channel 1'));
view.setLayers([['Retail',report],['Current',report],['Proposed',null]],11);assert.equal(select.value,'1');assert(text(view.root).includes('Not reviewed'));assert(text(view.root).includes('16383'));
const proposed=structuredClone(report);proposed.events[2].values[0]=99;view.setLayers([['Retail',report],['Current',report],['Proposed',proposed]],11);assert(text(view.root).includes('99 · event 2'));assert(!text(view.root).includes('Not reviewed'));
busy=true;view.lock();assert(select.disabled);busy=false;view.lock();assert(!select.disabled);
view.clear();assert(select.disabled);assert.equal(select.value,'');view.setLayers([['Source',report]],11);assert(text(view.root).includes('Choose a channel'));
fresh=false;view.setLayers([['Source',report]],0);assert(!text(view.root).includes('Through event'));view.dispose();assert(view.root.removed);view.setLayers([['Source',report]],1);
console.log('Encoded last-write state, unknown values, inclusive same-tick ordering, channel isolation, literal controller reset, pressure, 14-bit pitch bounds, detached/partial/bounded prefixes and shared UI lifecycle passed.');
