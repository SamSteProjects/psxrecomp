import {decodeDraftRepeatScene} from './draft-repeat.js';
import {decodeActorPlacementScene} from './actor-placement-batch.js';
import {NPC_PRESET_SCOPE} from './npc-preset-metadata.js';
import {presetExportButton} from './preset-files.js';
export {NPC_PRESET_SCOPE};
const canonical=v=>JSON.stringify(v&&typeof v==='object'?Array.isArray(v)?v.map(x=>JSON.parse(canonical(x))):Object.fromEntries(Object.keys(v).sort().map(k=>[k,JSON.parse(canonical(v[k]))])):v);
const equal=(a,b)=>canonical(a)===canonical(b);
const hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
export function decodeNpcPresetReview(value,request,state){
  const template=state.actor_templates?.find(t=>t.id===request.template_id),draft=value?.draft;
  if(!template||template.scope!==NPC_PRESET_SCOPE||template.source.scene_id!==state.scene?.id||
    Object.keys(request).sort().join(',')!=='expected_source_key,name,position,template_id'||request.expected_source_key!==state.project_copy_source_key||!hash(request.expected_source_key)||
    value?.schema_version!=='legaia.npc-preset-review.v1'||value.project_source_key!==request.expected_source_key||value.scene_preview_source_key!==state.scene_preview_source_key||value.scene_id!==state.scene.id||
    !equal(value.request,request)||!equal(value.template,Object.fromEntries(Object.entries(template).filter(([k])=>k!=='application')))||!hash(value.review_key)||value.gameplay_verified!==false||
    typeof value.entity_id!=='string'||!/^authored-actor:\/\/[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}$/.test(value.entity_id)||state.actor_drafts?.[value.entity_id]||
    !equal(draft,{scene_id:state.scene.id,name:request.name,donor_entity_id:template.components.NpcDraft.donor_entity_id,position:request.position,...(template.components.NpcDraft.dialogue?{dialogue:template.components.NpcDraft.dialogue}:{}),...(template.components.NpcDraft.appearance?{appearance:template.components.NpcDraft.appearance}:{}),...(template.components.NpcDraft.waits?{waits:template.components.NpcDraft.waits}:{})})||
    typeof request.name!=='string'||!request.name.trim()||request.name.length>120||request.name!==request.name.trim()||Object.keys(request.position??{}).sort().join(',')!=='x,z'||Object.values(request.position).some(n=>!Number.isSafeInteger(n)||n%64||n<64||n>16384)||
    !Array.isArray(value.limitations)||value.limitations.length>32||value.limitations.some(s=>typeof s!=='string'||!s||s.length>2048))throw new Error('NPC preset report differs from the current project and requested instance.');
  return structuredClone(value);
}
export function decodeNpcPresetScene(response,report,base){
  if(response?.schema_version!=='legaia.npc-preset-scene.v1'||!equal(response.review,report)||base.source_key!==report.scene_preview_source_key)throw new Error('NPC preset scene differs from its review.');
  const scene=decodeDraftRepeatScene({schema_version:'legaia.draft-repeat-scene.v1',project_source_key:base.source_key,review_key:report.review_key,scene_id:report.scene_id,scene:response.scene},{scene_id:report.scene_id,review_key:report.review_key,copies:[{entity_id:report.entity_id,draft:report.draft}]},base);
  const row=scene.entities.find(r=>r.entity_id===report.entity_id);
  if(!equal(row.authored_position,report.draft.position)||!Array.isArray(row.model_to_scene)||row.model_to_scene.length!==16||row.model_to_scene[3]!==row.display_position.x||row.model_to_scene[7]!==row.display_position.y||row.model_to_scene[11]!==row.display_position.z)throw new Error('NPC preset transform differs from reviewed placement.');
  decodeActorPlacementScene({schema_version:'legaia.actor-placement-scene.v1',scene_id:report.scene_id,project_source_key:base.source_key,review_key:report.review_key,positions:[row]},{scene_id:report.scene_id,review_key:report.review_key,targets:[{entity_id:report.entity_id,proposed:{...report.draft.position,y:null}}]},base.source_key);
  return scene;
}

export function mountNpcPresets(options){
  const {container,getState,getSelection,canEdit,isBusy,api}=options,section=document.createElement('section');section.className='component';section.id='npc-preset-library';
  section.innerHTML='<h3>NPC draft presets</h3><p>Capture a frozen retail donor, name, X/Z defaults and supported own dialogue/initial appearance/wait targets. Place independent NPC drafts in the owning scene. Shared asset edits remain project-wide; runtime behavior needs gameplay verification.</p><form><label>NPC preset name<input required maxlength="80" aria-label="NPC preset name"></label><button type="submit">Capture selected NPC preset</button></form><div data-presets></div><p data-error role="alert"></p>';
  container.append(section);const state=getState(),selected=getSelection(),draft=state.actor_drafts?.[selected],eligible=canEdit()&&!isBusy()&&draft?.scene_id===state.scene?.id;
  for(const input of section.querySelectorAll('form input,form button'))input.disabled=!eligible;
  section.querySelector('form').onsubmit=async event=>{event.preventDefault();if(isBusy()||!canEdit()||getSelection()!==selected)return;await api('/api/command',{type:'create_npc_preset',entity_id:selected,name:section.querySelector('input').value});};
  const templates=(state.actor_templates??[]).filter(t=>t.scope===NPC_PRESET_SCOPE),list=section.querySelector('[data-presets]');
  if(!templates.length)list.textContent='No NPC presets captured yet.';
  for(const template of templates){
    const card=document.createElement('section');card.className='template-card';const name=document.createElement('strong');name.textContent=template.name;
    const note=document.createElement('p');note.className='field-note';note.textContent=`${template.source.scene_id} · donor ${template.source.entity_id} · X ${template.components.Transform.position.x} / Z ${template.components.Transform.position.z} · ${Object.keys(template.components.NpcDraft.dialogue?.runs??{}).length} own text runs · ${Object.keys(template.components.NpcDraft.waits?.entries??{}).length} own wait targets${template.components.NpcDraft.appearance?" · appearance witness "+template.components.NpcDraft.appearance.donor_entity_id:""}`;
    const provenance=document.createElement('details'),summary=document.createElement('summary'),source=document.createElement('p');summary.textContent='Captured source provenance';source.textContent=`Draft ${template.source.capture_draft_id} · import SHA-256 ${template.source.import_sha256} · ${template.source.disc_identity}`;source.style.overflowWrap='anywhere';provenance.append(summary,source);
    const place=document.createElement('button');place.textContent='Review new NPC instance';place.dataset.owningScene=template.source.scene_id;place.disabled=!canEdit()||isBusy()||template.source.scene_id!==state.scene.id;place.onclick=()=>{if(isBusy()||!canEdit())return;container.close();openNpcPreset({...options,template});};
    const remove=document.createElement('button');remove.textContent='Delete NPC preset';remove.disabled=!canEdit()||isBusy();remove.onclick=()=>{if(!isBusy()&&canEdit())api('/api/command',{type:'delete_actor_template',template_id:template.id});};
    const rename=document.createElement('form'),label=document.createElement('label'),input=document.createElement('input'),save=document.createElement('button');label.textContent='Rename NPC preset';input.value=template.name;input.required=true;input.maxLength=80;save.textContent='Save preset name';input.disabled=save.disabled=!canEdit()||isBusy();label.append(input);rename.append(label,save);rename.onsubmit=event=>{event.preventDefault();if(!isBusy()&&canEdit())api('/api/command',{type:'rename_actor_template',template_id:template.id,name:input.value});};
    const exportButton=presetExportButton({template,getState,isBusy,setBusy:options.setBusy,onError:message=>{if(container.open)section.querySelector('[data-error]').textContent=message;}});
    card.append(name,note,provenance,place,remove,rename,exportButton);list.append(card);
  }
  const update=()=>{const disabled=isBusy()||!canEdit();for(const c of section.querySelectorAll('input,button'))c.disabled=disabled;for(const c of section.querySelectorAll(':scope > form input,:scope > form button'))c.disabled=disabled||!draft||draft.scene_id!==getState().scene?.id||getSelection()!==selected;for(const c of section.querySelectorAll('[data-owning-scene]'))c.disabled=disabled||c.dataset.owningScene!==getState().scene?.id;};update();return {update};
}

function openNpcPreset({template,getState,canEdit,isBusy,setBusy,api,canInspectScene,getScenePreview,inspectScene}){
  const dialog=document.createElement('dialog');dialog.id='npc-preset-dialog';document.body.append(dialog);
  dialog.innerHTML='<h2>Place NPC preset</h2><p data-source></p><form><label>New NPC name<input name="name" required maxlength="120" aria-label="Preset NPC instance name"></label><label>X<input name="x" type="number" required min="64" max="16384" step="64" aria-label="Preset NPC X"></label><label>Z<input name="z" type="number" required min="64" max="16384" step="64" aria-label="Preset NPC Z"></label><div class="dialog-actions"><button type="submit" data-review>Review NPC instance</button><button type="button" data-inspect disabled>Inspect NPC instance in scene</button><button type="button" data-apply disabled>Apply NPC instance</button></div></form><p data-error role="alert"></p><div data-report></div><button type="button" data-close>Close NPC preset</button>';
  for(const actions of dialog.querySelectorAll('.dialog-actions')){actions.style.flexWrap='wrap';actions.style.justifyContent='flex-start';}
  dialog.querySelector('[data-source]').textContent=`${template.name} · ${template.source.scene_id} · script donor ${template.source.entity_id}${template.components.NpcDraft.appearance?" · appearance witness "+template.components.NpcDraft.appearance.donor_entity_id:""}`;
  const form=dialog.querySelector('form');form.elements.name.value=template.components.NpcDraft.name;for(const a of ['x','z'])form.elements[a].value=template.components.Transform.position[a];
  const context=getState().project_copy_source_key,current=()=>canEdit()&&getState().project_copy_source_key===context;
  let report=null,generation=0,controller=null,keepClose=false;
  const request=()=>({template_id:template.id,name:form.elements.name.value.trim(),position:{x:Number(form.elements.x.value),z:Number(form.elements.z.value)},expected_source_key:context});
  function update(){if(!dialog.open)return;for(const c of form.querySelectorAll('input,button'))c.disabled=isBusy()||!current();dialog.querySelector('[data-review]').disabled=isBusy()||!current()||!form.checkValidity();dialog.querySelector('[data-inspect]').disabled=isBusy()||!current()||!report||!canInspectScene();dialog.querySelector('[data-apply]').disabled=isBusy()||!current()||!report;}
  async function post(route,body,signal){const r=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal}),v=await r.json();if(!r.ok||v.error)throw new Error(v.error||'NPC preset request failed.');return v;}
  for(const c of form.querySelectorAll('input'))c.oninput=()=>{generation++;controller?.abort();report=null;dialog.querySelector('[data-report]').replaceChildren();update();};
  dialog.querySelector('[data-close]').onclick=()=>dialog.close();dialog.addEventListener('close',()=>{if(keepClose){keepClose=false;return;}generation++;controller?.abort();dialog.remove();});
  form.onsubmit=async event=>{event.preventDefault();if(isBusy()||!current()||!form.checkValidity())return;const body=request(),token=++generation,active=new AbortController();controller=active;report=null;setBusy(true);update();dialog.querySelector('[data-error]').textContent='';
    try{const value=await post('/api/npc-preset-review',body,active.signal);if(token!==generation||!dialog.open||!current()||!equal(body,request()))return;report=decodeNpcPresetReview(value,body,getState());const result=dialog.querySelector('[data-report]');result.replaceChildren();for(const text of [`${report.draft.name}: X ${report.draft.position.x} / Z ${report.draft.position.z} · new identity ${report.entity_id}`, ...report.limitations]){const p=document.createElement('p');p.textContent=text;p.style.overflowWrap='anywhere';result.append(p);}}
    catch(e){if(e.name!=='AbortError'&&dialog.open&&token===generation)dialog.querySelector('[data-error]').textContent=e.message;}finally{if(controller===active){controller=null;setBusy(false);}update();}};
  dialog.querySelector('[data-inspect]').onclick=async()=>{if(isBusy()||!current()||!report||!canInspectScene())return;const accepted=report,base=getScenePreview(),token=++generation,active=new AbortController();controller=active;setBusy(true);update();
    try{const response=await post('/api/npc-preset-scene',{...accepted.request,review_key:accepted.review_key},active.signal);if(token!==generation||!dialog.open||!current()||getScenePreview()!==base||!canInspectScene())return;const proposed=decodeNpcPresetScene(response,accepted,base),back=()=>{if(token!==generation||!current()||report!==accepted)return false;dialog.showModal();update();return true;};inspectScene(proposed,accepted,back,current);keepClose=true;dialog.close();}
    catch(e){if(e.name!=='AbortError'&&dialog.open&&token===generation)dialog.querySelector('[data-error]').textContent=e.message;}finally{if(controller===active){controller=null;setBusy(false);}update();}};
  dialog.querySelector('[data-apply]').onclick=async()=>{if(isBusy()||!current()||!report)return;const accepted=report;report=null;update();if(await api('/api/command',{type:'instantiate_npc_preset',...accepted.request,review_key:accepted.review_key},{success:'Created NPC preset instance. Undo removes the new draft.'}))dialog.close();else{dialog.querySelector('[data-error]').textContent='NPC instance rejected. Review current inputs again.';update();}};
  dialog.showModal();update();
}
