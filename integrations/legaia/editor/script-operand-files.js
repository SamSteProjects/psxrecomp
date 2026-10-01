export const operandOwnerContext=(state,owner)=>JSON.stringify((state.authored_assets??[]).find(row=>row.id===owner)?.authored??null);
const COMPONENTS=['ScriptMovement','ScriptFlags','ScriptWaits','ScriptModelSelectors','Transitions'];
export function decodeOperandReview(value,file,owner,scene){
  const entries=value?.entries;
  if(value?.schema_version!=='legaia.script-operand-review.v1'||value.owner_id!==owner||value.scene_id!==scene||value.source_import_sha256!==file.source_import_sha256||file.owner_id!==owner||file.scene_id!==scene||file.schema_version!=='legaia.script-operand-file.v1'||!/^[0-9a-f]{64}$/.test(value.review_key)||!Array.isArray(entries)||entries.length>256||new Set(entries.map(row=>row.component+'|'+row.operand_id)).size!==entries.length||value.change_count!==entries.filter(row=>row.changed===true).length)throw new Error('Operand review differs from file or active script');
  const expected=Object.entries(file.components??{}).flatMap(([component,data])=>Object.entries(data.entries??{}).map(([operand_id,after])=>({component,operand_id,after}))).sort((a,b)=>a.component.localeCompare(b.component)||a.operand_id.localeCompare(b.operand_id));
  if(expected.length!==entries.length||entries.some(row=>!COMPONENTS.includes(row.component)||typeof row.changed!=='boolean'||!row.after||typeof row.after!=='object')||JSON.stringify(expected)!==JSON.stringify(entries.map(({component,operand_id,after})=>({component,operand_id,after}))))throw new Error('Operand review entries differ from file');
  return structuredClone(value);
}
export function mountScriptOperandFiles(host,{owner,scene,current,busy,setBusy,api,reopen,onError}){
  const controls=document.createElement('div');controls.className='dialog-actions';controls.dataset.operandFiles='';
  const download=document.createElement('button'),inspect=document.createElement('button');download.textContent='Download operand JSON';inspect.textContent='Inspect operand JSON file';controls.append(download,inspect);host.append(controls);
  download.onclick=async()=>{if(busy()||!current())return;setBusy(true);try{
    const response=await fetch('/api/script-operand-export',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({entity_id:owner})}),value=await response.json();
    if(!response.ok||value.error)throw new Error(value.error??'Operand export failed');if(!current())return;
    if(value.schema_version!=='legaia.script-operand-file.v1'||value.owner_id!==owner||value.scene_id!==scene)throw new Error('Operand export returned a different owner');
    const url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)+'\n'],{type:'application/json'})),link=document.createElement('a');link.href=url;link.download='authored-script-operands.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }catch(error){onError(error);}finally{setBusy(false);}};
  inspect.onclick=()=>{if(busy()||!current())return;const dialog=document.createElement('dialog'),controller=new AbortController();dialog.id='script-operand-file-dialog';dialog.className='project-dialog';
    dialog.innerHTML='<h2>Inspect script operand file</h2><p>Source-bound authored numeric operands only. Supplied entries replace their authored fields; other entries and components remain unchanged. No instructions or dialogue are transferred.</p><label>Operand JSON<input type="file" accept=".json,application/json"></label><div data-review></div><p role="alert" class="dialog-error"></p><button data-apply disabled>Apply reviewed operands</button><button data-close>Close</button>';document.body.append(dialog);
    let content=null,report=null,revision=0;const input=dialog.querySelector('input'),apply=dialog.querySelector('[data-apply]'),error=dialog.querySelector('[role="alert"]'),valid=()=>dialog.open&&current()&&!controller.signal.aborted;
    input.onchange=async()=>{const ticket=++revision;report=null;content=null;apply.disabled=true;error.textContent='';dialog.querySelector('[data-review]').replaceChildren();const file=input.files[0];if(!file)return;if(file.size>65536){error.textContent='Operand file exceeds 64 KiB';return;}input.disabled=true;setBusy(true);
      try{const candidate=await file.text();if(!valid()||ticket!==revision)return;const parsed=JSON.parse(candidate),response=await fetch('/api/script-operand-review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({entity_id:owner,content:candidate}),signal:controller.signal}),value=await response.json();if(!response.ok||value.error)throw new Error(value.error??'Operand review failed');if(!valid()||ticket!==revision)return;
        report=decodeOperandReview(value,parsed,owner,scene);content=candidate;
        appendOperandReview(dialog.querySelector('[data-review]'),report);apply.disabled=!report.change_count;
      }catch(exc){if(exc.name!=='AbortError'&&valid())error.textContent=exc.message;}finally{setBusy(false);input.disabled=false;}
    };
    apply.onclick=async()=>{if(busy()||!valid()||!report?.change_count||!content)return;const accepted=report;apply.disabled=true;
      if(await api('/api/command',{type:'import_script_operands',entity_id:owner,content,review_key:accepted.review_key})){dialog.close();await reopen();}else{report=null;content=null;error.textContent='Source, file or script changed. Inspect the file again.';}
    };
    dialog.querySelector('[data-close]').onclick=()=>dialog.close();dialog.addEventListener('close',()=>{revision++;controller.abort();dialog.remove();});dialog.showModal();
  };
}

export function appendOperandReview(host,report){
  const summary=document.createElement('p');summary.textContent=report.change_count+' changed entries · one Undo command';
  const families={ScriptMovement:'Movement',ScriptFlags:'Flag',ScriptWaits:'Wait',ScriptModelSelectors:'Model selector',Transitions:'Transition'};
  const fields={x:'X',z:'Z',move_id:'Move selector',bit:'Bit',duration_ticks:'Ticks',model_selector_signed:'Signed selector',entry_x_encoded:'Entry X byte',entry_z_encoded:'Entry Z byte',direction_encoded:'Direction byte'};
  const format=values=>values===null?'Inherit retail':Object.entries(values).map(([key,value])=>(fields[key]??key)+': '+value).join(' · ');
  const table=document.createElement('table');table.className='operand-review-table';const heading=document.createElement('tr');
  for(const label of ['Operand','Instruction','Current authored','Proposed authored']){const cell=document.createElement('th');cell.textContent=label;heading.append(cell);}table.append(heading);
  for(const row of report.entries){const tr=document.createElement('tr');for(const value of [families[row.component],'0x'+row.operand_id.split('/').at(-1),format(row.before),format(row.after)]){const cell=document.createElement('td');cell.textContent=value;tr.append(cell);}table.append(tr);}
  const details=document.createElement('details'),label=document.createElement('summary'),data=document.createElement('pre');label.textContent='Complete source-bound authored changes';data.className='diagnostic-detail';data.textContent=JSON.stringify(report.entries,null,2);details.append(label,data);
  host.append(summary,table,details);
}
