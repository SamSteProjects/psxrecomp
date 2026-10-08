// Derived from qualified decoded events. This records literal writes, not driver state.
const integer=(v,min,max)=>Number.isSafeInteger(v)&&v>=min&&v<=max;
const arity={note_off:2,note_on:2,poly_aftertouch:2,control_change:2,program_change:1,channel_aftertouch:1,pitch_bend:2,set_tempo:1,end_of_track:0};
export function encodedChannelState(report,index,channel){
 if(!report||!Array.isArray(report.events)||report.events.length>32768||typeof report.complete!=='boolean'||!integer(index,0,report.events.length-1)||!integer(channel,0,15))throw Error('Choose a decoded event and encoded channel.');
 const result={policy:'last-encoded-write-through-selected-event',driver_effects:'not_evaluated',complete_source:report.complete,selected_event:index,channel,ticks:null,declared_seconds:null,program:null,pitch_wheel:null,channel_pressure:null,controllers:{},key_pressure:{}};
 let ticks=0,seconds=0,end=0;
 for(let i=0;i<=index;i++){
  const e=report.events[i],meta=e?.kind==='set_tempo'||e?.kind==='end_of_track';
  if(!e||e.index!==i||!Object.hasOwn(arity,e.kind)||!integer(e.offset,end,4194304)||!integer(e.end_offset,e.offset+1,4194304)||!integer(e.ticks,ticks,2147483647)||!Number.isFinite(e.time_seconds)||e.time_seconds<seconds||!(meta?e.channel===null:integer(e.channel,0,15))||!Array.isArray(e.values)||e.values.length!==arity[e.kind]||e.values.some(v=>!integer(v,e.kind==='set_tempo'?1:0,e.kind==='set_tempo'?16777215:127)))throw Error('Invalid encoded channel-state prefix.');
  ticks=e.ticks;seconds=e.time_seconds;end=e.end_offset;
  if(e.channel!==channel)continue;
  const write=value=>({value,event_index:i,offset:e.offset,end_offset:e.end_offset});
  if(e.kind==='program_change')result.program=write(e.values[0]);
  if(e.kind==='control_change')result.controllers[e.values[0]]=write(e.values[1]);
  if(e.kind==='channel_aftertouch')result.channel_pressure=write(e.values[0]);
  if(e.kind==='poly_aftertouch')result.key_pressure[e.values[0]]=write(e.values[1]);
  if(e.kind==='pitch_bend')result.pitch_wheel={...write(e.values[0]|e.values[1]<<7),lsb:e.values[0],msb:e.values[1]};
 }
 result.ticks=ticks;result.declared_seconds=seconds;return result;
}

export function createChannelStateInspector({fresh,busy=()=>false,id='audio-channel-state'}){
 const el=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
 const root=el('section'),channel=el('select'),body=el('div'),position=el('p'),label=el('label','Encoded state channel ');
 root.id=id;channel.disabled=true;channel.setAttribute('aria-label','Encoded state channel');label.append(channel);
 const blank=el('option','Choose channel');blank.value='';channel.append(blank);
 for(let i=0;i<16;i++){const o=el('option',String(i));o.value=String(i);channel.append(o);}
 root.append(el('h3','Encoded Channel State'),el('p','Last literal writes through the selected event, inclusive. Unseen values are Unknown. Only written controllers and keys are listed. Controller effects, instrument ownership, bend range and game-driver state are not evaluated.'),label,position,body);
 let layers=[],selected=null,lastSelected=null,disposed=false;
 function render(){
  body.replaceChildren();channel.disabled=disposed||busy()||!layers.length;
  if(disposed||!fresh()||!layers.length)return;
  if(channel.value===''){position.textContent='Choose a channel for this meta event.';return;}
  const states=layers.map(([name,report])=>[name,report?encodedChannelState(report,selected,Number(channel.value)):null]);
  const primary=states.find(([,s])=>s)?.[1];position.textContent=`Through event ${selected} · channel ${channel.value} · tick ${primary.ticks} · ${primary.declared_seconds.toFixed(6)} declared seconds${primary.complete_source?'':' · partial decoded source'}`;
  const table=el('table'),head=el('tr');Object.assign(table.style,{width:'100%',tableLayout:'fixed',fontSize:'12px'});head.append(el('th','Encoded field'));for(const [name] of states)head.append(el('th',name));table.append(head);
  const rows=[['Program',s=>s.program],['Pitch Wheel (raw 14-bit)',s=>s.pitch_wheel],['Channel Pressure',s=>s.channel_pressure]];
  for(const [property,title] of [['controllers','Controller'],['key_pressure','Key Pressure']])for(const key of [...new Set(states.flatMap(([,s])=>Object.keys(s?.[property]??{})))].sort((a,b)=>Number(a)-Number(b)))rows.push([`${title} ${key}`,s=>s[property][key]]);
  for(const [name,get] of rows){const row=el('tr');row.append(el('th',name));for(const [,s] of states){const w=s&&get(s),cell=el('td',!s?'Not reviewed':!w?'Unknown':`${w.value} · event ${w.event_index} · byte 0x${w.offset.toString(16)}${w.lsb===undefined?'':` · LSB ${w.lsb}, MSB ${w.msb}`}`);Object.assign(cell.style,{overflowWrap:'anywhere',padding:'6px',verticalAlign:'top'});row.append(cell);}table.append(row);}body.append(table);
 }
 channel.onchange=()=>{if(!disposed&&fresh()&&!busy())render();};
 return {root,setLayers(next,index){if(disposed)return;layers=next;selected=index;if(index!==lastSelected){const e=next.find(([,r])=>r)?.[1]?.events[index];if(e?.channel!==null&&e?.channel!==undefined)channel.value=String(e.channel);lastSelected=index;}render();},clear(){layers=[];lastSelected=null;channel.value='';position.textContent='';body.replaceChildren();channel.disabled=true;},lock(){channel.disabled=disposed||busy()||!layers.length;},dispose(){disposed=true;layers=[];root.remove();}};
}
