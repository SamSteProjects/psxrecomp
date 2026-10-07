// Encoded native values only: lines are stepped, with no inferred timing/interpolation.
const integer=(v,a,b)=>Number.isSafeInteger(v)&&v>=a&&v<=b;
export function nativeChannelSeries(frames,objectIndex,kind){
  if(!Array.isArray(frames)||!integer(frames.length,1,4096)||!integer(objectIndex,0,1023)||!['translation','rotation_psx'].includes(kind))throw new Error('Choose a bounded native clip, rigid object and channel kind.');
  const values=frames.map((frame,i)=>{
    const rows=frame?.object_transforms,row=rows?.[objectIndex];
    if(frame?.frame_index!==i||!Array.isArray(rows)||!integer(rows.length,1,1024)||rows.length!==frames[0]?.object_transforms?.length||rows.length*frames.length>262144||row?.object_index!==objectIndex||!Array.isArray(row[kind])||row[kind].length!==3||row[kind].some(v=>kind==='translation'?!integer(v,-2048,2047):!integer(v,0,4080)||v%16))throw new Error('Native channel frame or value is unavailable or outside its encoded grid.');
    return [...row[kind]];
  });
  return values;
}
export function channelGraphWindow(values,start,size){
  if(!Array.isArray(values)||!integer(values.length,1,4096)||!integer(start,0,values.length-1)||![16,32,64,128].includes(size)||values.some(row=>!Array.isArray(row)||row.length!==3||row.some(v=>!Number.isFinite(v))))throw new Error('Invalid channel graph window.');
  const end=Math.min(values.length-1,start+size-1),rows=values.slice(start,end+1),flat=rows.flat(),min=Math.min(...flat),max=Math.max(...flat);
  return {start,end,rows:structuredClone(rows),min,max};
}
export function channelGraphFrame(clientX,left,width,start,end){
  if(![clientX,left,width].every(Number.isFinite)||width<=0||!integer(start,0,4095)||!integer(end,start,4095))throw new Error('Invalid channel graph frame selection.');
  // SVG plot occupies 64..620 of its 640-unit viewBox.
  const x=(clientX-left)/width*640,t=Math.max(0,Math.min(1,(x-64)/556));
  return Math.round(start+t*(end-start));
}
export function createAnimationChannelGraph(host,{onFrame,onObject,onEdit=null,editAvailability=()=>({available:false,reason:"No native authoring target."})}){
  const el=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
  const section=el('details'),heading=el('summary','Inspect native animation channels');section.append(heading);
  const note=el('p','Encoded object-local channels · PSX Y points down. Rotation uses 0–4080 PSX units in steps of 16; 4096 is one turn. Frame indices are zero based. Stepped lines connect stored samples; timing and in-game interpolation are not inferred. The plot scrolls horizontally on narrow windows. Click the plot or use Left/Right, Home/End to inspect that frame.');
  const controls=el('div');controls.style.cssText='display:flex;flex-wrap:wrap;gap:12px';
  const makeSelect=(label,aria,options)=>{const l=el('label',label),s=el('select');l.style.cssText='display:flex;flex-direction:column;align-items:stretch;flex:1 1 140px;min-width:0';s.style.cssText='width:100%;max-width:none;flex:none';s.setAttribute('aria-label',aria);for(const [value,text] of options){const o=el('option',text);o.value=value;s.append(o);}l.append(s);controls.append(l);return s;};
  const object=makeSelect('Rigid object','Channel graph rigid object',[]),kind=makeSelect('Channels','Channel graph kind',[['translation','Translation XYZ'],['rotation_psx','Rotation XYZ']]),size=makeSelect('Frame window','Channel graph frame window',[16,32,64,128].map(n=>[String(n),String(n)]));size.value='64';
  const earlier=el('button','Earlier channel frames'),later=el('button','Later channel frames');for(const b of [earlier,later]){b.type='button';controls.append(b);}
  const edit=el('button','Edit inspected native channel');edit.type='button';edit.hidden=onEdit===null;controls.append(edit);const editNote=el('p');editNote.hidden=onEdit===null;const status=el('p'),readout=el('p'),error=el('p');error.setAttribute('role','alert');error.className='dialog-error';
  const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 640 220');svg.style.cssText='width:100%;min-width:560px;display:block;touch-action:manipulation';svg.setAttribute('tabindex','0');svg.setAttribute('role','group');svg.setAttribute('aria-label','Native channel graph. Left and Right select frames; Home and End select window endpoints.');
  const plot=el('div');plot.style.cssText='width:100%;max-width:100%;overflow-x:auto';plot.append(svg);section.append(note,controls,editNote,status,plot,readout,error);host.append(section);
  let frames=[],values=[],selected=0,start=0,window=null;
  const colors=['#ff8b8b','#8beba2','#90caff'];
  const svgEl=(tag,attrs,text)=>{const n=document.createElementNS(ns,tag);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,String(v));if(text!==undefined)n.textContent=text;svg.append(n);return n;};
  function render(){
    svg.replaceChildren();readout.textContent='';earlier.disabled=later.disabled=true;const availability=editAvailability({frame:selected,object:Number(object.value)});edit.disabled=!values.length||availability.available!==true;editNote.textContent=edit.disabled?availability.reason:'Open the saved native channel editor at this frame/object. The current source is verified again; opening applies no edit.';
    if(!values.length){status.textContent='Decoded native channel samples unavailable for this preview.';return;}
    window=channelGraphWindow(values,start,Number(size.value));const {end,min,max,rows}=window,span=max-min||1;
    const x=f=>64+556*(f-start)/Math.max(1,end-start),y=v=>180-140*(v-min)/span;
    svgEl('rect',{x:64,y:30,width:556,height:150,fill:'#101a20',stroke:'#647780'});
    for(const [v,yy] of [[max,40],[min,180]])svgEl('text',{x:4,y:yy,fill:'currentColor','font-size':14},v);
    for(const [f,xx] of [[start,64],[end,620]])svgEl('text',{x:xx,y:206,'text-anchor':f===start?'start':'end',fill:'currentColor','font-size':14},`Frame ${f}`);
    for(let axis=0;axis<3;axis++){
      let d=`M ${x(start)} ${y(rows[0][axis])}`;for(let i=1;i<rows.length;i++)d+=` H ${x(start+i)} V ${y(rows[i][axis])}`;
      svgEl('path',{d,fill:'none',stroke:colors[axis],'stroke-width':2});svgEl('text',{x:75+axis*170,y:20,fill:colors[axis],'font-size':15},`${'XYZ'[axis]} · ${values[selected][axis]}`);
    }
    if(selected>=start&&selected<=end)svgEl('line',{x1:x(selected),x2:x(selected),y1:30,y2:180,stroke:'#fff','stroke-dasharray':'4 3','data-selected-frame':selected});
    status.textContent=`Object ${object.value} · ${kind.value==='translation'?'Translation (native units)':'Rotation (PSX units)'} · frames ${start}–${end} of ${values.length} · plotted range ${min}–${max}`;
    readout.textContent=`Selected frame ${selected} · X ${values[selected][0]} · Y ${values[selected][1]} · Z ${values[selected][2]}`;earlier.disabled=start===0;later.disabled=end===values.length-1;
  }
  function refresh(){error.textContent='';try{values=nativeChannelSeries(frames,Number(object.value),kind.value);}catch(e){values=[];error.textContent=e.message;}render();}
  function frame(index,follow=true){if(!integer(index,0,frames.length-1))return;selected=index;if(follow&&(index<start||index>=start+Number(size.value)))start=Math.floor(index/Number(size.value))*Number(size.value);render();}
  function choose(index){if(!values.length)return;onFrame(index);}
  svg.onclick=e=>{if(!window||!values.length)return;const r=svg.getBoundingClientRect();choose(channelGraphFrame(e.clientX,r.left,r.width,window.start,window.end));};
  svg.onkeydown=e=>{if(!values.length)return;const index={ArrowLeft:Math.max(0,selected-1),ArrowRight:Math.min(values.length-1,selected+1),Home:window.start,End:window.end}[e.key];if(index!==undefined){e.preventDefault();e.stopPropagation();choose(index);}};
  edit.onclick=async()=>{if(edit.disabled||onEdit===null)return;try{await onEdit({frame:selected,object:Number(object.value)});}catch(e){error.textContent=e.message;}};
  object.onchange=()=>{refresh();onObject(Number(object.value));};kind.onchange=refresh;size.onchange=()=>{start=Math.floor(selected/Number(size.value))*Number(size.value);render();};
  earlier.onclick=()=>{start=Math.max(0,start-Number(size.value));render();};later.onclick=()=>{start=Math.min(values.length-1,start+Number(size.value));render();};
  return {load(model){frames=model?.frames??[];selected=start=0;object.replaceChildren();const count=frames[0]?.object_transforms?.length??0;for(let i=0;i<Math.min(count,1024);i++){const o=el('option',`Object ${i}`);o.value=String(i);object.append(o);}section.hidden=!frames.length;object.disabled=kind.disabled=size.disabled=!count;refresh();},frame,setObject(index){if(integer(index,0,frames[0]?.object_transforms?.length-1)){object.value=String(index);refresh();}}};
}
