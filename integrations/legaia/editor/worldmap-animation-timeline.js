const fields=['translation','rotation_psx'],axes=['x','y','z'];
const fail=()=>{throw Error('Choose an existing native channel and axis.');};
export function worldAnimationChannelTrack(plan,object,field,axis){
  const record=plan?.record,index=axes.indexOf(axis);
  if(!record||!Number.isSafeInteger(record.frame_count)||record.frame_count<1||record.frame_count>512||!Number.isSafeInteger(record.channel_count)||record.channel_count<1||record.channel_count>64||!Number.isSafeInteger(object)||object<0||object>=record.channel_count||!fields.includes(field)||index<0)fail();
  const samples=[];
  for(let frame=0;frame<record.frame_count;frame++){
    const row=plan.frame(frame)[object],retail=row?.retail?.[field]?.[index],current=row?.current?.[field]?.[index];
    for(const value of [retail,current])if(!Number.isSafeInteger(value)||(field==='translation'?value < -2048||value > 2047:value<0||value>4080||value%16))fail();
    samples.push(Object.freeze({frame,retail,current}));
  }
  const values=samples.flatMap(s=>[s.retail,s.current]);
  return Object.freeze({animation_id:record.id,object_index:object,field,axis,min:Math.min(...values),max:Math.max(...values),samples:Object.freeze(samples)});
}
export function worldAnimationTimelineFrame(clientX,left,width,count){
  if(![clientX,left,width].every(Number.isFinite)||width<=0||!Number.isSafeInteger(count)||count<1||count>512)fail();
  const x=(clientX-left)*640/width;
  return Math.max(0,Math.min(count-1,Math.round((x-48)/(624-48)*(count-1))));
}
export function mountWorldAnimationTimeline({host,plan,getFrame,onFrame,current,busy,onError}){
  const node=(tag,text)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e;},box=node('section'),object=node('select'),axis=node('select'),status=node('p'),svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
  box.dataset.worldAnimationTimeline='';Object.assign(box.style,{maxWidth:'100%',boxSizing:'border-box',overflowWrap:'anywhere'});box.append(node('h4','Native Channel Timeline'),node('p','Discrete native samples; timing and interpolation remain unknown. Choose a channel, then click a frame or use Left/Right, Home/End. Frame selection updates the inspector and withdraws any authored draft.'));
  object.setAttribute('aria-label','Timeline rigid object');for(let i=0;i<plan.record.channel_count;i++){const option=node('option',`Object ${i}`);option.value=String(i);object.append(option);}
  axis.setAttribute('aria-label','Timeline channel axis');for(const field of fields)for(const a of axes){const option=node('option',`${field==='translation'?'Translation':'Rotation'} ${a.toUpperCase()}`);option.value=field+'.'+a;axis.append(option);}for(const input of [object,axis])Object.assign(input.style,{width:'100%',maxWidth:'100%',boxSizing:'border-box'});
  const legend=node('p');for(const [text,color] of [['Retail','#68d7ec'],['Current','#f2b66d']]){const span=node('span',text);span.style.color=color;span.style.marginRight='18px';legend.append(span);}svg.setAttribute('viewBox','0 0 640 230');svg.setAttribute('role','group');svg.setAttribute('aria-label','Native channel timeline');svg.setAttribute('aria-roledescription','Discrete frame timeline');svg.setAttribute('tabindex','0');Object.assign(svg.style,{width:'100%',height:'220px',display:'block',touchAction:'pan-y'});status.setAttribute('role','status');box.append(object,axis,legend,svg,status);host.append(box);let track=null,selection=null,disposed=false;
  const valid=()=>!disposed&&current();
  const el=(tag,attrs,text)=>{const e=document.createElementNS(svg.namespaceURI,tag);for(const [k,v] of Object.entries(attrs))e.setAttribute(k,String(v));if(text!==undefined)e.textContent=String(text);return e;};
  const x=f=>track.samples.length===1?336:48+f/(track.samples.length-1)*576;
  function select(){selection?.remove();selection=null;const frame=getFrame();if(!Number.isSafeInteger(frame)||frame<0||frame>=track.samples.length){status.textContent='No valid inspector frame selected.';return;}
    const row=track.samples[frame];selection=el('line',{x1:x(frame),x2:x(frame),y1:16,y2:186,stroke:'#fff','stroke-dasharray':'3 3','data-selected-frame':frame});svg.append(selection);status.textContent=`Frame ${frame} · Object ${track.object_index} · ${track.field}.${track.axis}: Retail ${row.retail}, Current ${row.current}. ${track.field==='translation'?'Signed native translation.':'PSX rotation: 4096 units per turn.'}`;
  }
  function draw(){try{const [field,a]=axis.value.split('.');track=worldAnimationChannelTrack(plan,Number(object.value),field,a);svg.replaceChildren(el('rect',{x:48,y:16,width:576,height:170,fill:'#101a20'}));const low=track.min===track.max?track.min-1:track.min,high=track.min===track.max?track.max+1:track.max,y=v=>186-(v-low)/(high-low)*170;
    for(const [v,label] of [[track.max,track.max],[track.min,track.min]])svg.append(el('text',{x:42,y:y(v)+4,'text-anchor':'end',fill:'#9faeb6','font-size':12},label));
    for(const row of track.samples)for(const [layer,color,r] of [['retail','#68d7ec',4],['current','#f2b66d',2]]){const dot=el('circle',{cx:x(row.frame),cy:y(row[layer]),r,stroke:color,fill:layer==='retail'?'none':color,'data-frame':row.frame,'data-layer':layer,'data-value':row[layer]});dot.append(el('title',{},`Frame ${row.frame} · ${layer}: ${row[layer]}`));svg.append(dot);}
    svg.append(el('text',{x:48,y:211,fill:'#9faeb6','font-size':12},'0'),el('text',{x:624,y:211,'text-anchor':'end',fill:'#9faeb6','font-size':12},track.samples.length-1),el('text',{x:336,y:228,'text-anchor':'middle',fill:'#9faeb6','font-size':12},'Native frame index'));select();
  }catch(error){svg.replaceChildren();status.textContent=error.message;onError(error);}}
  function update(){const blocked=!valid()||busy();object.disabled=axis.disabled=blocked;svg.setAttribute('aria-disabled',String(blocked));}
  object.onchange=axis.onchange=()=>{if(!valid()||busy()){if(track){object.value=String(track.object_index);axis.value=track.field+'.'+track.axis;}return;}draw();};
  svg.onclick=e=>{if(!valid()||busy())return;try{const rect=svg.getBoundingClientRect();onFrame(worldAnimationTimelineFrame(e.clientX,rect.left,rect.width,track.samples.length));}catch(error){onError(error);}};
  svg.onkeydown=e=>{if(!valid()||busy()||!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();const frame=Number.isSafeInteger(getFrame())?getFrame():0;onFrame(e.key==='Home'?0:e.key==='End'?track.samples.length-1:Math.max(0,Math.min(track.samples.length-1,frame+(e.key==='ArrowLeft'?-1:1))));};
  draw();update();return {update,setFrame(){if(!disposed&&track)select();},dispose(){disposed=true;svg.onclick=svg.onkeydown=null;track=selection=null;box.remove();}};
}
