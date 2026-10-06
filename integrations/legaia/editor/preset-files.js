import {NPC_PRESET_SCOPE,NPC_PRESET_FILE_SCHEMA,NPC_DIALOGUE_PRESET_FILE_SCHEMA} from './npc-preset-metadata.js';
import {ANIMATION_PRESET_SCOPE,presetScopeLabel,validatePresetMetadata} from './preset-animation.js';
const MAX_BYTES=8*1024,MAX_NPC_DIALOGUE_BYTES=512*1024;
const fileLimit=v=>v?.schema_version===NPC_DIALOGUE_PRESET_FILE_SCHEMA?MAX_NPC_DIALOGUE_BYTES:MAX_BYTES;
const context=getState=>{const s=getState();return JSON.stringify([s.project?.path,s.scenes,s.actor_templates]);};
const canonical=value=>Array.isArray(value)?value.map(canonical):value&&typeof value==='object'?Object.fromEntries(Object.keys(value).sort().map(key=>[key,canonical(value[key])])):value;
const same=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
export function decodePresetFileExport(value,template){
  const expected=template.scope===NPC_PRESET_SCOPE?(template.components?.NpcDraft?.dialogue?NPC_DIALOGUE_PRESET_FILE_SCHEMA:NPC_PRESET_FILE_SCHEMA):template.scope===ANIMATION_PRESET_SCOPE?'legaia.actor-preset-file.v2':'legaia.actor-preset-file.v1';
  if(value?.schema_version!==expected||value.template?.id!==template.id||value.template?.name!==template.name||value.template?.scope!==template.scope||!/^[0-9a-f]{64}$/.test(value.source_import_sha256)||!same(value.template?.source,template.source)||!same(value.template?.components,template.components)||Object.keys(value).length!==3)throw new Error('Preset export differs from the selected source-bound metadata');
  validatePresetMetadata(value.template);
  if(template.scope===NPC_PRESET_SCOPE&&value.source_import_sha256!==template.source.import_sha256)throw new Error('NPC preset file import hash differs from its captured provenance.');
  return structuredClone(value);
}
export function decodePresetImportReview(value,content,name){
  if(typeof content!=='string'||new TextEncoder().encode(content).length>MAX_NPC_DIALOGUE_BYTES)throw new Error('Preset file exceeds 512 KiB');
  let original;try{original=JSON.parse(content);}catch{throw new Error('Invalid preset JSON');}
  if(new TextEncoder().encode(content).length>fileLimit(original))throw new Error('Preset file exceeds its schema size bound');
  decodePresetFileExport(original,original?.template??{});
  if(value?.schema_version!=='legaia.actor-preset-import-review.v1'||value.template?.name!==name||!/^[0-9a-f]{64}$/.test(value.review_key)||value.source_import_sha256!==original.source_import_sha256||value.template?.scope!==original.template.scope||!same(value.template?.source,original.template.source)||!same(value.template?.components,original.template.components)||!Array.isArray(value.limitations)||value.limitations.length>64||value.limitations.some(note=>typeof note!=='string'||note.length>8192))throw new Error('Preset import review differs from the source-bound file');
  validatePresetMetadata(value.template);
  return structuredClone(value);
}
export function presetExportButton({template,getState,isBusy,setBusy,onError}){
  const button=document.createElement('button');button.textContent='Export preset JSON';button.dataset.presetExport=template.id;
  button.onclick=async()=>{if(isBusy())return;const key=context(getState);setBusy(true);try{
    const response=await fetch('/api/actor-preset-file',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({template_id:template.id})}),value=await response.json();
    if(!response.ok||value.error)throw new Error(value.error??'Preset export failed');
    if(key!==context(getState)||!button.isConnected||!button.closest('dialog')?.open)throw new Error('Preset library changed during export');
    decodePresetFileExport(value,template);
    const content=JSON.stringify(value,null,2)+'\n';if(new TextEncoder().encode(content).length>fileLimit(value))throw new Error('Preset export exceeds its schema size bound');
    const url=URL.createObjectURL(new Blob([content],{type:'application/json'})),link=document.createElement('a');link.href=url;link.download=template.scope===NPC_PRESET_SCOPE?'npc-preset.json':'actor-preset.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }catch(e){onError(e.message);}finally{setBusy(false);}};return button;
}
export function appendPresetImport({container,getState,canEdit,isBusy,setBusy,api}){
  const label=document.createElement('label'),input=document.createElement('input');label.textContent='Import preset JSON';input.type='file';input.accept='.json';input.setAttribute('aria-label','Import actor preset JSON');input.disabled=!canEdit();label.append(input);container.append(label);
  input.onchange=async()=>{const file=input.files?.[0],key=context(getState);if(!file||isBusy()||!canEdit())return;
    try{if(file.size>MAX_NPC_DIALOGUE_BYTES)throw new Error('Preset file exceeds 512 KiB');const content=await file.text();
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
  dialog.innerHTML='<h2>Import actor or NPC preset</h2><p>Adds an independent source-bound library preset. No actors change.</p><label>Imported preset name<input aria-label="Imported preset name" maxlength="80" required></label><button data-review>Review preset file</button><div data-result></div><p role="alert" class="dialog-error"></p><button data-apply disabled>Import reviewed preset</button><button data-close>Cancel preset import</button>';
  document.body.append(dialog);const name=dialog.querySelector('input'),key=context(getState),controller=new AbortController();let report=null,revision=0;name.value=suggested;
  const current=()=>dialog.open&&key===context(getState)&&canEdit();
  const apply=dialog.querySelector('[data-apply]'),preview=dialog.querySelector('[data-review]'),error=dialog.querySelector('[role="alert"]');
  name.oninput=()=>{revision++;report=null;apply.disabled=true;dialog.querySelector('[data-result]').replaceChildren();};
  dialog.querySelector('[data-close]').onclick=()=>dialog.close();dialog.addEventListener('close',()=>{controller.abort();dialog.remove();},{once:true});
  preview.onclick=async()=>{if(isBusy()||!current())return;const token=++revision,chosen=name.value;report=null;apply.disabled=true;name.disabled=true;preview.disabled=true;setBusy(true);error.textContent='';
    try{const response=await fetch('/api/actor-preset-import-review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({content,name:chosen}),signal:controller.signal}),value=await response.json();
      if(!response.ok||value.error)throw new Error(value.error??'Preset import review failed');if(token!==revision||!current()||name.value!==chosen)return;
      report=decodePresetImportReview(value,content,chosen);const result=dialog.querySelector('[data-result]');result.replaceChildren();const summary=document.createElement('p');summary.textContent=`${value.template.name} · ${presetScopeLabel(value.template.scope)} · source ${value.template.source.scene_id}`;result.append(summary);
      const positions=value.template.components.Transform?.position;if(positions){const p=document.createElement('p');p.textContent='Absolute coordinates: '+Object.entries(positions).map(([axis,position])=>axis.toUpperCase()+' '+position).join(' · ');result.append(p);}
      const npc=value.template.components.NpcDraft;if(npc){const p=document.createElement('p');p.textContent=`NPC default name: ${npc.name} · retail donor: ${npc.donor_entity_id} · ${Object.keys(npc.dialogue?.runs??{}).length} own text runs. Import adds a preset only; review placement separately.`;result.append(p);}
      const donor=value.template.components.ActorAppearance?.donor_entity_id;if(donor){const p=document.createElement('p');p.textContent='Appearance donor: '+donor;result.append(p);}
      const animation=value.template.components.ActorAnimation;if(animation){const p=document.createElement('p');p.textContent=`Initial clip: ${animation.animation_asset_id} · witness ${animation.donor_entity_id} · SHA-256 ${animation.source_record_sha256}`;result.append(p);const note=document.createElement('p');note.className='field-note';note.textContent='Initial MAN animation header only; channel edits retain their imported shared-clip ownership.';result.append(note);}
      const provenance=document.createElement('details'),title=document.createElement('summary'),details=document.createElement('pre');title.textContent='Source provenance';details.className='diagnostic-detail';details.textContent=JSON.stringify({source:value.template.source,source_import_sha256:value.source_import_sha256},null,2);provenance.append(title,details);result.append(provenance);
      for(const note of value.limitations){const p=document.createElement('p');p.textContent=note;result.append(p);}
    }catch(e){if(e.name!=='AbortError'&&current())error.textContent=e.message;}
    finally{setBusy(false);if(dialog.open){name.disabled=preview.disabled=!current();apply.disabled=!current()||!report;}}
  };
  apply.onclick=async()=>{if(isBusy()||!current()||!report)return;const accepted=report;report=null;apply.disabled=true;
    if(await api('/api/command',{type:'import_actor_template',content,name:name.value,review_key:accepted.review_key}))dialog.close();else if(dialog.open)error.textContent='Preset library/source changed or import rejected. Review the file again.';};
  dialog.showModal();preview.click();
}
