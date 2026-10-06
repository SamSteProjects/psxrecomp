import {decodeBuildHistory} from './build-history.js';
const hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
const int=(v,a,b)=>Number.isSafeInteger(v)&&v>=a&&v<=b;
const hex=pc=>'0x'+pc.toString(16).toUpperCase().padStart(4,'0');
const fail=()=>{throw new Error('Saved script comparison is invalid or belongs to changed inputs.');};

export async function decodeSourceBuildScript(value,owner,id,key){
  if(value?.schema_version!=='legaia.source-build-script.v1'||value.owner_id!==owner||value.state_key!==key||!hash(key)||value.scene_id!==owner.split('/').slice(0,3).join('/')||value.read_only!==true||value.gameplay_verified!==false||value.representation!=='saved_build'||value.runtime_binding!=='not_asserted'||!hash(value.project_source_key)||!/^[0-9a-f]{40}$/.test(value.reference_commit)||!hash(value.generated_man_sha256))fail();
  const b=value.build;
  if(b?.id!==id||!/^[0-9a-f]{16}$/.test(id)||b.integrity!=='verified'||b.matches_current_inputs!==true||b.source_disc_integrity!=='verified'||!hash(b.archive_sha256)||!hash(b.source_disc_sha256)||!['relocated_PROT','fixed_span_PROT_overlays'].includes(b.delivery))fail();
  for(const record of [value.source,value.generated]){
    if(!int(record?.byte_offset,0,4*1024*1024)||!int(record.byte_length,1,65536)||!int(record.script_offset,0,record.byte_length)||typeof record.raw_hex!=='string'||record.raw_hex.length!==record.byte_length*2||!/^[0-9a-f]+$/.test(record.raw_hex)||!hash(record.sha256))fail();
    const bytes=Uint8Array.from(record.raw_hex.match(/../g),v=>parseInt(v,16));
    const actual=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),v=>v.toString(16).padStart(2,'0')).join('');if(actual!==record.sha256)fail();
    const r=record.inspection;
    if(!['partial','decoded_supported_paths'].includes(r?.status)||!['instructions','dialogues','stops','opaque_regions'].every(k=>Array.isArray(r[k])&&r[k].length<=8192))fail();
    const seen=new Set();for(const row of [...r.instructions,...r.dialogues]){if(!int(row.pc,0,record.byte_length-1)||!int(row.length,1,record.byte_length-row.pc)||seen.has(row.pc))fail();seen.add(row.pc);if(row.raw_hex!==record.raw_hex.slice(row.pc*2,(row.pc+row.length)*2))fail();}
  }
  if(value.source.byte_length!==value.generated.byte_length||value.source.script_offset!==value.generated.script_offset||!Array.isArray(value.changed_bytes)||value.changed_bytes.length>65536)fail();
  const expected=[];for(let i=0;i<value.source.byte_length;i++){const retail=parseInt(value.source.raw_hex.slice(i*2,i*2+2),16),generated=parseInt(value.generated.raw_hex.slice(i*2,i*2+2),16);if(retail!==generated)expected.push({pc:i,retail,generated});}
  if(JSON.stringify(expected)!==JSON.stringify(value.changed_bytes)||!Array.isArray(value.limitations)||value.limitations.length>16||value.limitations.some(v=>typeof v!=='string'||v.length>8192))fail();
  return structuredClone(value);
}

export function mountSourceBuildScript(parent,{owner,getContext,current,busy,setBusy}){
  const section=document.createElement('section');section.className='source-build-script';
  const title=document.createElement('h3');title.textContent='Retail versus saved Build';
  const note=document.createElement('p');note.className='field-note';note.textContent='Inspect the exact delivered record from a Build matching current project inputs. This does not require running the game.';
  const load=document.createElement('button');load.textContent='Find matching Builds';
  const select=document.createElement('select');select.setAttribute('aria-label','Saved script Build');select.hidden=true;
  const compare=document.createElement('button');compare.textContent='Compare delivered script';compare.hidden=true;
  const status=document.createElement('p');status.setAttribute('role','status');const output=document.createElement('div');
  section.append(title,note,load,select,compare,status,output);parent.append(section);
  const controller=new AbortController();let disposed=false,acceptedContext=null,entries=[];
  const context=()=>JSON.stringify(getContext());
  const valid=key=>!disposed&&current()&&key===context();
  async function request(route,body,key){
    if(!valid(key))throw new Error('Project changed. Reopen script inspection.');
    const response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:controller.signal});const value=await response.json();if(!response.ok)throw new Error(value.error||'Saved script request failed');
    const latestResponse=await fetch('/api/state',{cache:'no-store',signal:controller.signal});if(!latestResponse.ok)throw new Error('Could not verify current editor inputs.');const latest=await latestResponse.json(),c=getContext();
    if(!valid(key)||latest.project?.path!==c.projectPath||latest.scene?.id!==c.sceneId||latest.script_authoring_state_key!==c.scriptKey)throw new Error('Server inputs changed. Reopen script inspection.');
    return value;
  }
  async function run(action){if(busy()||!current()||disposed)return;const key=context();setBusy(true);updateState();try{await action(key);}catch(error){if(valid(key))status.textContent=error.message;}finally{setBusy(false);updateState();}}
  load.onclick=()=>run(async key=>{output.replaceChildren();compare.hidden=true;select.hidden=true;entries=[];status.textContent='Reading saved completion receipts…';const history=decodeBuildHistory(await request('/api/builds',{},key));entries=history.builds.filter(r=>r.status==='completed'&&r.matches_current_inputs);select.replaceChildren();for(const row of entries){const o=document.createElement('option');o.value=row.id;o.textContent=`${row.id} · ${row.build_kind}`;select.append(o);}acceptedContext=key;compare.hidden=select.hidden=!entries.length;status.textContent=entries.length?`${entries.length} matching Builds. Select one to verify its package and emitted record.`:'No matching Build. Save and Build the current project first.';if(history.truncated)status.textContent+=' Build history is bounded; additional entries may be omitted.';});
  select.onchange=()=>{output.replaceChildren();status.textContent='Select Compare to verify this Build.';};
  compare.onclick=()=>run(async key=>{
    output.replaceChildren();if(key!==acceptedContext)throw new Error('Inputs changed. Find matching Builds again.');const id=select.value,entry=entries.find(r=>r.id===id);if(!entry)throw new Error('Choose a matching Build.');status.textContent='Verifying package and decoding emitted MAN…';
    const report=await decodeSourceBuildScript(await request('/api/source-build-script',{entity:owner,build_id:id},key),owner,id,getContext().scriptKey);
    if(!valid(key)||report.build.archive_sha256!==entry.archive_sha256||report.build.source_disc_sha256!==entry.source_disc_sha256)throw new Error('Saved Build receipt changed. Find matching Builds again.');
    status.textContent=`${report.changed_bytes.length} changed record bytes · package and retail disc verified · gameplay unverified`;
    const summary=document.createElement('p');summary.className='field-note';summary.textContent=`Retail MAN offset ${report.source.byte_offset}; Build MAN offset ${report.generated.byte_offset}. Record PCs retain their own coordinate space. Retail decoder: ${report.source.inspection.status}; Build decoder: ${report.generated.inspection.status}.`;
    output.append(summary);
    function table(headers,rows){const wrap=document.createElement('div');wrap.className='script-table-wrap';const t=document.createElement('table'),head=document.createElement('thead'),h=document.createElement('tr');for(const text of headers){const c=document.createElement('th');c.textContent=text;h.append(c);}head.append(h);const body=document.createElement('tbody');for(const row of rows){const tr=document.createElement('tr');for(const text of row){const td=document.createElement('td');td.textContent=text;tr.append(td);}body.append(tr);}t.append(head,body);wrap.append(t);output.append(wrap);}
    table(['Record PC','Retail byte','Build byte'],report.changed_bytes.slice(0,256).map(r=>[hex(r.pc),hex(r.retail),hex(r.generated)]));
    const left=new Map([...report.source.inspection.instructions,...report.source.inspection.dialogues].map(r=>[r.pc,r])),right=new Map([...report.generated.inspection.instructions,...report.generated.inspection.dialogues].map(r=>[r.pc,r]));
    const pcs=[...new Set([...left.keys(),...right.keys()])].sort((a,b)=>a-b),label=row=>row?`${row.mnemonic??'MES_SEGMENT'} · ${JSON.stringify(row.operands??row.text)}`:'Not decoded on this side';
    table(['Record PC','Retail decoded path','Build decoded path'],pcs.slice(0,512).map(pc=>[hex(pc),label(left.get(pc)),label(right.get(pc))]));
    const limits=document.createElement('p');limits.className='field-note';limits.textContent=`Showing ${Math.min(report.changed_bytes.length,256)} of ${report.changed_bytes.length} byte differences and ${Math.min(pcs.length,512)} of ${pcs.length} decoded PCs. Full bytes, stops and opaque regions are in the download. ${report.limitations.join(' ')}`;output.append(limits);
    const download=document.createElement('button');download.textContent='Download script comparison';download.onclick=()=>{if(busy()||!valid(key))return;const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download=`script-comparison-${id}-${owner.split('/').at(-1)}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),0);};output.append(download);
  });
  function updateState(){for(const b of [load,compare,select,...output.querySelectorAll('button')])b.disabled=disposed||busy()||!current()||(b===compare&&acceptedContext!==context());}
  updateState();return{updateState,dispose(){disposed=true;controller.abort();section.remove();}};
}
