const hash=value=>typeof value==='string'&&/^[0-9a-f]{64}$/.test(value);
export function decodeHistory(value){
  if(value?.schema_version!=='legaia.command-history.v1'||!hash(value.source_key)||value.read_only!==true||value.session_only!==true||value.page_size!==50||!Number.isSafeInteger(value.total)||value.total<0||!Number.isSafeInteger(value.offset)||value.offset<0||value.offset>value.total||!Array.isArray(value.records)||value.records.length!==Math.min(50,value.total-value.offset)||value.next_offset!==(value.offset+value.records.length<value.total?value.offset+value.records.length:null))throw new Error('Invalid session history listing');
  const seen=new Set();
  for(const row of value.records){const id=`${row.branch}:${row.index}`;
    if(!['undo','redo'].includes(row.branch)||!Number.isSafeInteger(row.index)||row.index<0||seen.has(id)||!hash(row.record_key)||!(row.recorded_target===null||typeof row.recorded_target==='string')||!row.recorded_owners||typeof row.recorded_owners!=='object'||Array.isArray(row.recorded_owners)||!Number.isSafeInteger(row.byte_length)||row.byte_length<0)throw new Error('Invalid session history record');seen.add(id);
  }return structuredClone(value);
}
export function decodeHistoryRecord(value,report,row){
  if(value?.schema_version!=='legaia.command-history-record.v1'||value.read_only!==true||value.source_key!==report.source_key||value.branch!==row.branch||value.index!==row.index||value.record_key!==row.record_key||!value.record||typeof value.record!=='object'||Array.isArray(value.record)||!Object.hasOwn(value.record,'before')||!Object.hasOwn(value.record,'after'))throw new Error('Invalid or stale session history detail');
  return structuredClone(value.record);
}
export function openCommandHistory(){
  const dialog=document.createElement('dialog');dialog.id='command-history-dialog';dialog.style.width='min(850px, calc(100vw - 32px))';
  const title=document.createElement('h2');title.textContent='Session Command History';
  const note=document.createElement('p');note.textContent='Read-only session records. Command names and timestamps were not recorded. Save keeps history; reopening clears it. Applied: newest first. Undone: next Redo first.';
  const actions=document.createElement('div');actions.className='dialog-actions';actions.style.flexWrap='wrap';
  const status=document.createElement('p'),list=document.createElement('div'),detail=document.createElement('pre');list.style.cssText='max-height:24vh;overflow:auto';detail.style.cssText='max-height:40vh;overflow:auto;white-space:pre-wrap;overflow-wrap:anywhere';
  const button=(label,fn)=>{const b=document.createElement('button');b.textContent=label;b.onclick=fn;actions.append(b);return b;};
  let report=null,generation=0,pending=false;
  const request=async(path,body)=>{const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const data=await response.json();if(!response.ok||data.error)throw new Error(typeof data.error==='string'?data.error:'History request failed');return data;};
  const run=async(fn)=>{if(pending)return;pending=true;const token=++generation;for(const b of actions.querySelectorAll('button'))b.disabled=true;
    try{await fn(token);}catch(error){if(dialog.open&&token===generation){status.textContent=error.message;detail.textContent='Refresh to inspect current session history.';}}
    finally{pending=false;if(dialog.open&&token===generation){refresh.disabled=false;close.disabled=false;previous.disabled=!report||report.offset===0;next.disabled=!report||report.next_offset===null;}}
  };
  const load=offset=>run(async token=>{const value=decodeHistory(await request('/api/command-history',{offset}));if(!dialog.open||token!==generation)return;report=value;list.replaceChildren();detail.textContent='Select a record to inspect exact stored before/after metadata.';status.textContent=`${value.total} session records; showing ${value.records.length?value.offset+1:0}–${value.offset+value.records.length}.`;
    for(const row of value.records){const b=document.createElement('button');b.style.cssText='display:block;width:100%;text-align:left;margin:4px 0;overflow-wrap:anywhere;white-space:normal';b.textContent=`${row.branch==='undo'?'Applied':'Undone'} · Stack ${row.index+1} · ${row.recorded_target??'Target not recorded'}${Object.keys(row.recorded_owners).length?' · '+JSON.stringify(row.recorded_owners):''}`;
      b.onclick=()=>run(async selectedToken=>{const result=await request('/api/command-history/inspect',{source_key:value.source_key,branch:row.branch,index:row.index,record_key:row.record_key});const record=decodeHistoryRecord(result,value,row);if(dialog.open&&selectedToken===generation){detail.textContent=JSON.stringify(record,null,2);status.textContent=`${row.branch==='undo'?'Applied':'Undone'} record ${row.index}; exact stored metadata.`;}});list.append(b);
    }
  });
  const refresh=button('Refresh',()=>load(0)),previous=button('Previous page',()=>load(Math.max(0,report.offset-50))),next=button('Next page',()=>load(report.next_offset)),close=button('Close',()=>dialog.close());
  dialog.append(title,note,actions,status,list,detail);dialog.addEventListener('close',()=>{generation++;dialog.remove();},{once:true});document.body.append(dialog);dialog.showModal();load(0);
}
