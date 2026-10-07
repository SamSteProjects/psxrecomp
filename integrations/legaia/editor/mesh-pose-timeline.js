// Navigation consumes already-qualified selected-scene channel metadata.
export function meshPoseTimeRange(sampled,clipIndex){
  if(!sampled||sampled.animation_index!==clipIndex)return null;
  const rows=sampled.sampled_channels;
  if(!Array.isArray(rows)||rows.length>256)throw Error('Invalid pose timeline channels.');
  if(!rows.length)return null;
  const seen=new Set();for(const row of rows){
    const key=row?.node_index+':'+row?.path;
    if(!row||!Number.isSafeInteger(row.node_index)||row.node_index<0||row.node_index>63||!['translation','rotation','scale','weights'].includes(row.path)||seen.has(key)||!Number.isSafeInteger(row.key_count)||row.key_count<1||row.key_count>4096||!['STEP','LINEAR','CUBICSPLINE'].includes(row.interpolation)||row.interpolation==='CUBICSPLINE'&&row.key_count<2||typeof row.start_time!=='number'||typeof row.end_time!=='number'||!Number.isFinite(row.start_time)||!Number.isFinite(row.end_time)||row.start_time<0||row.end_time<row.start_time||row.end_time>3600)throw Error('Invalid qualified pose timeline range.');
    seen.add(key);
  }
  return {start:Math.min(...rows.map(r=>r.start_time)),end:Math.max(...rows.map(r=>r.end_time)),channels:structuredClone(rows)};
}

export function meshPoseTimeline({onTime}){
  const host=document.createElement('section'),note=document.createElement('p'),label=document.createElement('label'),slider=document.createElement('input'),start=document.createElement('button'),end=document.createElement('button'),details=document.createElement('details'),summary=document.createElement('summary'),table=document.createElement('table');
  table.style.cssText='width:100%;border-collapse:collapse;font-size:12px;text-align:left';
  label.textContent='Selected-scene animation time';slider.type='range';slider.step='any';slider.setAttribute('aria-label','Selected-scene animation time');label.append(slider);
  start.textContent='Stage range start';end.textContent='Stage range end';summary.textContent='Sampled channel ranges';details.append(summary,table);host.append(note,label,start,end,details);
  let range=null,locked=true,key=null;
  const stage=time=>{if(!locked&&range&&Number.isFinite(time)&&time>=range.start&&time<=range.end)onTime(time);};
  slider.oninput=()=>stage(Number(slider.value));start.onclick=()=>stage(range?.start);end.onclick=()=>stage(range?.end);
  return {host,refresh(sampled,clipIndex,time,disabled){
    range=meshPoseTimeRange(sampled,clipIndex);locked=disabled||!range;
    host.hidden=!range;slider.disabled=locked||range?.start===range?.end;start.disabled=end.disabled=locked;
    if(!range)return;
    slider.min=String(range.start);slider.max=String(range.end);slider.value=String(Number.isFinite(time)?Math.max(range.start,Math.min(range.end,time)):range.start);
    const outside=Number.isFinite(time)&&(time<range.start||time>range.end);
    note.textContent=`Selected-scene channel range: ${range.start}–${range.end} seconds. ${outside?'The numeric draft is outside this range; channels clamp to their endpoints. ':''}Navigation stages the time only. Inspect animation pose to qualify geometry, then Review before Apply. Excluded channels do not define this range.`;
    const next=JSON.stringify(range.channels);if(next!==key){key=next;table.replaceChildren();const head=document.createElement('tr');for(const text of ['Node / channel','Keys','Interpolation','Seconds']){const th=document.createElement('th');th.textContent=text;th.style.padding='4px';head.append(th);}table.append(head);for(const row of range.channels){const tr=document.createElement('tr');for(const text of [`${row.node_index} / ${row.path}`,String(row.key_count),row.interpolation,`${row.start_time}–${row.end_time}`]){const td=document.createElement('td');td.textContent=text;td.style.padding='4px';tr.append(td);}table.append(tr);}}
  }};
}
