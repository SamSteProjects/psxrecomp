import assert from 'node:assert/strict';
import {decodeAudioSequence,openAudioSequence} from '../editor/audio-sequence.js';
const context={assetId:'audio://legaia/prot/0877',sceneId:'scene://town01',sourceKey:'a'.repeat(64),entryHash:'b'.repeat(64)};
const report={schema_version:'legaia.audio-sequence-inspection.v1',asset_id:context.assetId,scene_id:context.sceneId,source_key:context.sourceKey,read_only:true,project_changed:false,runtime_state:'not_observed',source_record:{disc_sha256:'c'.repeat(64),iso_file:'PROT.DAT',prot_entry_index:877,entry_sha256:context.entryHash,entry_byte_offset:2048,entry_size_bytes:2048,sequence_offset:0,sequence_size_bytes:27,sequence_sha256:'d'.repeat(64)},header:{header_variant:'legaia-u32-version',header_size:15,version:1,ppqn:480,initial_tempo_us_per_quarter:500000,time_signature_numerator:4,time_signature_denominator_power:2,event_stream_validated:false},events:[{index:0,offset:15,end_offset:19,delta_ticks:0,ticks:0,time_seconds:0,status:144,channel:0,kind:'note_on',values:[60,100],running_status:false},{index:1,offset:19,end_offset:23,delta_ticks:480,ticks:480,time_seconds:.5,status:144,channel:0,kind:'note_on',values:[60,0],running_status:true},{index:2,offset:23,end_offset:26,delta_ticks:0,ticks:480,time_seconds:.5,status:255,channel:null,kind:'end_of_track',values:[],running_status:false}],event_count:3,event_counts:{note_on:2,end_of_track:1},channels:[0],complete:true,encoded_end_of_track:true,stop_reason:null,stop_offset:null,decoded_byte_end:26,unparsed_bytes:1,decoded_ticks:480,decoded_time_seconds:.5,limitations:['Source timing only.']};
const decoded=decodeAudioSequence(report,context);decoded.events[0].values[0]=1;assert.equal(report.events[0].values[0],60);
for(const change of [r=>r.source_key='f'.repeat(64),r=>r.source_record.entry_sha256='f'.repeat(64),r=>r.source_record.sequence_offset=2048,r=>r.events[0].values[0]=128,r=>r.events[1].offset++,r=>r.events[1].ticks++,r=>r.events[1].time_seconds=1,r=>r.events[0].running_status=true,r=>r.event_counts.note_on=1,r=>r.channels=[1],r=>r.events[2].kind='set_tempo',r=>r.complete=false,r=>r.project_changed=true,r=>r.payload='untrusted',r=>r.header.binary=[],r=>r.events[0].unknown=true]){const bad=structuredClone(report);change(bad);assert.throws(()=>decodeAudioSequence(bad,context));}
const partial=structuredClone(report);partial.events.pop();Object.assign(partial,{event_count:2,event_counts:{note_on:2},complete:false,encoded_end_of_track:false,stop_reason:'Unknown meta length',stop_offset:23,decoded_byte_end:23,unparsed_bytes:4});assert.equal(decodeAudioSequence(partial,context).complete,false);
console.log('Sequence source/timing/running-status/summary qualification, detached metadata and complete/partial boundary checks passed.');

// Exercise withdrawal and late replies without starting a runtime or authoring.
class Element{
 constructor(tag){this.tag=tag;this.style={};this.children=[];this.dataset={};this.value='';this.listeners={};this.textContent='';}
 append(...nodes){this.children.push(...nodes);if(this.tag==='select'&&!this.value&&nodes[0])this.value=nodes[0].value;}
 setAttribute(){} replaceChildren(...nodes){this.children=[...nodes];}
 addEventListener(name,callback){this.listeners[name]=callback;} showModal(){this.open=true;}
 close(){this.open=false;this.listeners.close?.();} remove(){this.removed=true;}
}
globalThis.document={createElement:tag=>new Element(tag),createElementNS:(_,tag)=>new Element(tag),body:new Element('body')};
const find=(node,tag)=>node.tag===tag?node:node.children.map(child=>find(child,tag)).find(Boolean);
let current={...context,projectPath:'C:/private/project'},resolve;
const response=()=>({ok:true,text:async()=>JSON.stringify(report)});
let view=openAudioSequence({record:{id:context.assetId,label:'Source'},getContext:()=>current,busy:()=>false,request:async()=>response()});
try{await view.ready;assert.equal(find(view.dialog,'tbody').children.length,3);const buttons=node=>[...(node.tag==='button'?[node]:[]),...node.children.flatMap(buttons)];buttons(view.dialog).find(n=>n.textContent==='Show note timeline').onclick();const svg=find(view.dialog,'svg');assert(svg);const timeline=find(view.dialog,'section');assert(timeline);assert(svg.children.some(n=>n.tag==='rect'));current={...current,sourceKey:'f'.repeat(64)};await new Promise(done=>setTimeout(done,350));assert.equal(find(view.dialog,'tbody').children.length,0);assert(timeline.removed);assert(view.dialog.children.some(n=>n.textContent?.includes('sources changed')));}finally{view.dispose();}
current={...context,projectPath:'C:/private/project'};
view=openAudioSequence({record:{id:context.assetId,label:'Source'},getContext:()=>current,busy:()=>false,request:()=>new Promise(done=>resolve=done)});view.dispose();resolve(response());await view.ready;assert(view.dialog.removed);assert.equal(find(view.dialog,'tbody').children.length,0);
console.log('Source-context withdrawal clears rows; close aborts ownership and late responses cannot publish events.');
