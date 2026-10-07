// Derived encoded-note relationships. This does not evaluate instruments or sustain.
export function analyzeSequenceNotes(report){
 const notes=[],unmatchedReleases=[],pending=new Map();let overlapCount=0;
 for(const event of report.events){
  if(!['note_on','note_off'].includes(event.kind))continue;
  const key=event.channel+':'+event.values[0];
  if(event.kind==='note_on'&&event.values[1]>0){
   let queue=pending.get(key);if(!queue){queue={rows:[],head:0,ambiguous:false};pending.set(key,queue);}
   if(queue.head<queue.rows.length){queue.ambiguous=true;overlapCount++;}
   const note={channel:event.channel,key:event.values[0],velocity:event.values[1],start_event:event.index,end_event:null,start_ticks:event.ticks,end_ticks:null,start_seconds:event.time_seconds,end_seconds:null,ambiguous:false};
   notes.push(note);queue.rows.push(note);
  }else{
   const queue=pending.get(key);
   if(!queue||queue.head===queue.rows.length){unmatchedReleases.push(event.index);continue;}
   const note=queue.rows[queue.head++];Object.assign(note,{end_event:event.index,end_ticks:event.ticks,end_seconds:event.time_seconds,ambiguous:queue.ambiguous});
   if(queue.head===queue.rows.length)pending.delete(key);
  }
 }
 for(const queue of pending.values())for(let i=queue.head;i<queue.rows.length;i++)queue.rows[i].ambiguous=queue.ambiguous;
 return {policy:'same-channel-key-first-in-first-out',sustain_evaluated:false,complete_source:report.complete,decoded_ticks:report.decoded_ticks,notes,unmatched_releases:unmatchedReleases,unmatched_starts:notes.filter(n=>n.end_event===null).map(n=>n.start_event),overlap_count:overlapCount};
}

export function createAudioNoteTimeline({report,fresh,onSelect,id='audio-note-timeline',label='Source'}){
 const analysis=analyzeSequenceNotes(report),el=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;},root=el('section'),title=el('h3','Encoded note timeline'),limits=el('p','Source ticks only. Same-channel/key releases pair with the earliest open start (FIFO); overlaps are ambiguous. Dashed notes have no encoded release in this prefix. Sustain, instruments and audible duration are not evaluated.'),toolbar=el('div'),channel=el('select'),span=el('select'),back=el('button','Earlier notes'),forward=el('button','Later notes'),range=el('span'),summary=el('p'),details=el('p','Select a note to inspect its encoded source events.'),wrap=el('div'),svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
 root.id=id;title.textContent=label==='Source'?'Encoded note timeline':label+' encoded note timeline';channel.setAttribute('aria-label','Note timeline channel');span.setAttribute('aria-label','Note timeline quarter-note window');
 for(const [value,label] of [['all','All note channels'],...report.channels.map(n=>[String(n),'Channel '+n])]){const o=el('option',label);o.value=value;channel.append(o);}
 for(const value of [4,8,16,32,64]){const o=el('option',value+' quarter notes');o.value=String(value);span.append(o);}span.value='16';
 Object.assign(toolbar.style,{display:'flex',flexWrap:'wrap',gap:'8px',alignItems:'center'});Object.assign(wrap.style,{overflowX:'auto',maxWidth:'100%'});svg.setAttribute('role','group');svg.setAttribute('aria-label','Encoded '+label.toLowerCase()+' notes');svg.style.minWidth='760px';svg.style.width='100%';svg.style.background='#111e20';wrap.append(svg);toolbar.append(channel,span,back,forward,range);root.append(title,limits,toolbar,summary,wrap,details);
 const startButton=el('button','Go to note start event'),releaseButton=el('button','Go to note release event'),navigation=el('div');startButton.disabled=releaseButton.disabled=true;navigation.append(startButton,releaseButton);root.append(navigation);let selectedNote=null;
 let start=0,selected=null,disposed=false;
 const active=()=>!disposed&&fresh();
 const node=(tag,attrs,text)=>{const n=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [key,value] of Object.entries(attrs))n.setAttribute(key,String(value));if(text!==undefined)n.textContent=text;return n;};
 const render=()=>{
  if(!active())return;const width=Number(span.value)*report.header.ppqn,maxStart=Math.max(0,Math.floor(Math.max(0,report.decoded_ticks-1)/width)*width);start=Math.min(start,maxStart);const end=start+width,all=analysis.notes.filter(n=>channel.value==='all'||String(n.channel)===channel.value),visible=all.filter(n=>n.start_ticks<end&&(n.end_ticks??report.decoded_ticks)>=start),draw=visible.slice(0,512),keys=all.map(n=>n.key),lo=Math.max(0,Math.min(48,...keys)-2),hi=Math.min(127,Math.max(72,...keys)+2),height=(hi-lo+1)*10+36;
  svg.replaceChildren();svg.setAttribute('viewBox',`0 0 1000 ${height}`);svg.style.height=height+'px';const x=t=>60+(t-start)/width*920,y=key=>26+(hi-key)*10;
  for(let key=lo;key<=hi;key++)if(key%12===0){svg.append(node('line',{x1:60,x2:980,y1:y(key)+5,y2:y(key)+5,stroke:'#304447'}),node('text',{x:4,y:y(key)+9,fill:'#a8bec0','font-size':10},'Key '+key));}
  const step=report.header.ppqn*Math.max(1,Math.ceil(Number(span.value)/16));for(let tick=start;tick<=end;tick+=step)svg.append(node('line',{x1:x(tick),x2:x(tick),y1:24,y2:height-10,stroke:'#304447'}),node('text',{x:x(tick),y:15,fill:'#a8bec0','font-size':10},String(tick)));
  for(const note of draw){
   const left=Math.max(start,note.start_ticks),right=Math.min(end,note.end_ticks??report.decoded_ticks),box=node('rect',{x:x(left),y:y(note.key),width:Math.max(3,x(right)-x(left)),height:8,fill:`hsl(${note.channel*23},65%,${35+note.velocity/127*25}%)`,stroke:selected===note.start_event?'white':note.ambiguous?'#ffbe70':'#90b0b3','stroke-dasharray':note.end_event===null?'3 2':'none',tabindex:0,role:'button','data-note-event':note.start_event,'aria-label':`Note event ${note.start_event}, channel ${note.channel}, key ${note.key}`});
   box.append(node('title',{},`Event ${note.start_event} → ${note.end_event??'unmatched'} · key ${note.key} · velocity ${note.velocity}${note.ambiguous?' · ambiguous overlap':''}`));
   const select=()=>{if(!active())return;const focused=document.activeElement===box;selected=note.start_event;selectedNote=note;startButton.disabled=false;releaseButton.disabled=note.end_event===null;details.textContent=`Channel ${note.channel} · key ${note.key} · velocity ${note.velocity} · start event ${note.start_event} at tick ${note.start_ticks} (${note.start_seconds.toFixed(6)} declared seconds) · ${note.end_event===null?'no encoded release in decoded prefix':`release event ${note.end_event} at tick ${note.end_ticks} (${note.end_seconds.toFixed(6)} declared seconds)`}${note.ambiguous?' · ambiguous overlapping starts; FIFO display pairing':''}.`;onSelect(note.start_event);render();if(focused)svg.querySelector(`[data-note-event="${note.start_event}"]`)?.focus({preventScroll:true});};box.onclick=select;box.onkeydown=event=>{if(['Enter',' '].includes(event.key)){event.preventDefault();select();}};svg.append(box);
  }
  back.disabled=start===0;forward.disabled=start>=maxStart;range.textContent=`Ticks ${start}–${end} · ${report.header.ppqn} ticks/quarter`;summary.textContent=`${analysis.notes.length} starts · ${analysis.unmatched_starts.length} unmatched starts · ${analysis.unmatched_releases.length} unmatched releases · ${analysis.overlap_count} overlapping starts · ${visible.length} notes in window${visible.length>512?' (first 512 shown; narrow the window or channel)':''}${report.complete?'':' · partial source prefix'}`;
 };
 startButton.onclick=()=>{if(active()&&selectedNote)onSelect(selectedNote.start_event);};releaseButton.onclick=()=>{if(active()&&selectedNote?.end_event!==null&&selectedNote)onSelect(selectedNote.end_event);};
 channel.onchange=()=>{start=0;render();};span.onchange=()=>{start=0;render();};back.onclick=()=>{if(active()){start=Math.max(0,start-Number(span.value)*report.header.ppqn);render();}};forward.onclick=()=>{if(active()){start+=Number(span.value)*report.header.ppqn;render();}};render();
 const focusEvent=index=>{if(!active()||!report.events[index])return;const width=Number(span.value)*report.header.ppqn;start=Math.floor(report.events[index].ticks/width)*width;const note=analysis.notes.find(n=>n.start_event===index||n.end_event===index);selected=note?.start_event??null;render();};
 return {root,analysis,focusEvent,dispose:()=>{disposed=true;root.remove();}};
}
