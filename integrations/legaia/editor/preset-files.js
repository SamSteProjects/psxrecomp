const MAX_BYTES=8*1024;
const context=getState=>{const s=getState();return JSON.stringify([s.project?.path,s.scenes,s.actor_templates]);};
export function presetExportButton({template,getState,isBusy,setBusy,onError}){
  const button=document.createElement('button');button.textContent='Export preset JSON';button.dataset.presetExport=template.id;
  button.onclick=async()=>{if(isBusy())return;const key=context(getState);setBusy(true);try{
    const response=await fetch('/api/actor-preset-file',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({template_id:template.id})}),value=await response.json();
    if(!response.ok||value.error)throw new Error(value.error??'Preset export failed');
    if(key!==context(getState)||!button.isConnected||!button.closest('dialog')?.open)throw new Error('Preset library changed during export');
    if(value.schema_version!=='legaia.actor-preset-file.v1'||value.template?.id!==template.id||value.template?.name!==template.name||value.template?.scope!==template.scope||value.source_import_sha256?.length!==64)throw new Error('Preset export differs from the selected metadata');
    const content=JSON.stringify(value,null,2)+'\n';if(new TextEncoder().encode(content).length>MAX_BYTES)throw new Error('Preset export exceeds 8 KiB');
    const url=URL.createObjectURL(new Blob([content],{type:'application/json'})),link=document.createElement('a');link.href=url;link.download='actor-preset.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }catch(e){onError(e.message);}finally{setBusy(false);}};return button;
}
export function appendPresetImport({container,getState,canEdit,isBusy,setBusy,api}){
  const label=document.createElement('label'),input=document.createElement('input');label.textContent='Import preset JSON';input.type='file';input.accept='.json';input.setAttribute('aria-label','Import actor preset JSON');input.disabled=!canEdit();label.append(input);container.append(label);
  input.onchange=async()=>{const file=input.files?.[0],key=context(getState);if(!file||isBusy()||!canEdit())return;
    try{if(file.size>MAX_BYTES)throw new Error('Preset file exceeds 8 KiB');const content=await file.text();
      if(!input.isConnected||!container.open||input.files?.[0]!==file||key!==context(getState)||!canEdit())return;
      let suggested='Imported preset';try{const name=JSON.parse(content)?.template?.name;if(typeof name==='string'&&name.trim())suggested=name.trim().slice(0,80);}catch{}
      if(getState().actor_templates.some(row=>row.name.toLowerCase()===suggested.toLowerCase()))suggested=suggested.slice(0,70)+' imported';
      openImportReview({content,suggested,getState,canEdit,isBusy,setBusy,api});
    }catch(e){if(input.isConnected&&container.open){const error=document.createElement('p');error.className='dialog-error';error.setAttribute('role','alert');error.textContent=e.message;label.after(error);}}
    finally{input.value='';}
  };
}
function openImportReview({content,suggested,getState,canEdit,isBusy,setBusy,api}){
  const dialog=document.createElement('dialog');dialog.id='preset-import-review';dialog.className='project-dialog';
  dialog.innerHTML='<h2>Import actor preset</h2><p>Adds an independent source-bound library preset. No actors change.</p><label>Imported preset name<input aria-label="Imported preset name" maxlength="80" required></label><button data-review>Review preset file</button><div data-result></div><p role="alert" class="dialog-error"></p><button data-apply disabled>Import reviewed preset</button><button data-close>Cancel preset import</button>';
  document.body.append(dialog);const name=dialog.querySelector('input'),key=context(getState),controller=new AbortController();let report=null,revision=0;name.value=suggested;
  const current=()=>dialog.open&&key===context(getState)&&canEdit();
  const apply=dialog.querySelector('[data-apply]'),preview=dialog.querySelector('[data-review]'),error=dialog.querySelector('[role="alert"]');
  name.oninput=()=>{revision++;report=null;apply.disabled=true;dialog.querySelector('[data-result]').replaceChildren();};
  dialog.querySelector('[data-close]').onclick=()=>dialog.close();dialog.addEventListener('close',()=>{controller.abort();dialog.remove();},{once:true});
  preview.onclick=async()=>{if(isBusy()||!current())return;const token=++revision,chosen=name.value;report=null;apply.disabled=true;name.disabled=true;preview.disabled=true;setBusy(true);error.textContent='';
    try{const response=await fetch('/api/actor-preset-import-review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({content,name:chosen}),signal:controller.signal}),value=await response.json();
      if(!response.ok||value.error)throw new Error(value.error??'Preset import review failed');if(token!==revision||!current()||name.value!==chosen)return;
      if(value.schema_version!=='legaia.actor-preset-import-review.v1'||value.template?.name!==chosen||typeof value.template?.id!=='string'||!value.template.id.startsWith('template://')||!/^[0-9a-f]{64}$/.test(value.review_key))throw new Error('Preset import review differs from the file/name');
      report=value;const result=dialog.querySelector('[data-result]');result.replaceChildren();const summary=document.createElement('p'),scope={'authored-position-v1':'Position','authored-appearance-v1':'Appearance','authored-actor-preset-v1':'Position and appearance'};summary.textContent=`${value.template.name} · ${scope[value.template.scope]??value.template.scope} · source ${value.template.source.scene_id}`;result.append(summary);
      const positions=value.template.components.Transform?.position;if(positions){const p=document.createElement('p');p.textContent='Absolute coordinates: '+Object.entries(positions).map(([axis,position])=>axis.toUpperCase()+' '+position).join(' · ');result.append(p);}
      const donor=value.template.components.ActorAppearance?.donor_entity_id;if(donor){const p=document.createElement('p');p.textContent='Appearance donor: '+donor;result.append(p);}
      const provenance=document.createElement('details'),title=document.createElement('summary'),details=document.createElement('pre');title.textContent='Source provenance';details.className='diagnostic-detail';details.textContent=JSON.stringify({source:value.template.source,source_import_sha256:value.source_import_sha256},null,2);provenance.append(title,details);result.append(provenance);
      for(const note of value.limitations){const p=document.createElement('p');p.textContent=note;result.append(p);}
    }catch(e){if(e.name!=='AbortError'&&current())error.textContent=e.message;}
    finally{setBusy(false);if(dialog.open){name.disabled=preview.disabled=!current();apply.disabled=!current()||!report;}}
  };
  apply.onclick=async()=>{if(isBusy()||!current()||!report)return;const accepted=report;report=null;apply.disabled=true;
    if(await api('/api/command',{type:'import_actor_template',content,name:name.value,review_key:accepted.review_key}))dialog.close();else if(dialog.open)error.textContent='Preset library/source changed or import rejected. Review the file again.';};
  dialog.showModal();preview.click();
}
