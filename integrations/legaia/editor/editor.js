const $ = (id) => document.getElementById(id);
const escapeHTML = (value) => String(value ?? '').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const numeric = (value) => typeof value === 'number' && Number.isFinite(value);
const format = (value) => numeric(value) ? String(Math.round(value * 1000) / 1000) : 'Unknown';
let state = {project:{}, scene:null, assets:[], selection:{}, history:{}, capabilities:{}};
let busy = false, toastTimer, lastSceneId, grid = true;
const canvas = $('viewport'), ctx = canvas.getContext('2d');
const camera = {yaw:-0.65,pitch:0.66,distance:2000,target:{x:0,y:0,z:0}};
let width=1, height=1, projected=[], handles=[], drag=null, draft=null;
let sceneRenderer=null,scenePreview=null,sceneKey=null,scenePendingKey=null,sceneFailedKey=null,sceneAbort=null,sceneError=null,modelsEnabled=true,cameraRevision=0;
const modelToggle=document.createElement('button');modelToggle.id='scene-model-toggle';modelToggle.textContent='Models';modelToggle.className='active';modelToggle.setAttribute('aria-pressed','true');modelToggle.hidden=true;$('frame-all').before(modelToggle);
modelToggle.onclick=()=>{if(sceneError){sceneFailedKey=null;sceneKey=null;scenePreview=null;sceneError=null;modelsEnabled=true;}else modelsEnabled=!modelsEnabled;modelToggle.classList.toggle('active',modelsEnabled);modelToggle.setAttribute('aria-pressed',modelsEnabled);refreshScenePreview();draw();};
const sceneSelect=document.createElement('select');sceneSelect.className='scene-selector';sceneSelect.setAttribute('aria-label','Active scene');$('viewport-title').after(sceneSelect);
sceneSelect.onchange=()=>api('/api/scene',{scene_id:sceneSelect.value});
const runtimeBox=document.createElement('div');runtimeBox.className='runtime-status';$('inspector').before(runtimeBox);
const buildButton=document.createElement('button');buildButton.id='build-button';buildButton.textContent='Build';buildButton.title='Build the project with supported edits or as a verified retail baseline';$('save-button').after(buildButton);
const buildDialog=document.createElement('dialog');buildDialog.className='project-dialog';document.body.append(buildDialog);
const templateDialog=document.createElement('dialog');templateDialog.id='template-dialog';document.body.append(templateDialog);
const templateButton=document.createElement('button');templateButton.className='template-library-button';templateButton.textContent='Authored transform templates…';$('assets').before(templateButton);
templateButton.onclick=()=>showTemplates();
const runButton=document.createElement('button');runButton.id='run-button';runButton.textContent='Build & Run';runButton.className='accent';buildButton.after(runButton);
const runDialog=document.createElement('dialog');runDialog.id='run-dialog';document.body.append(runDialog);
const runRibbon=document.createElement('div');runRibbon.className='run-ribbon';runRibbon.hidden=true;document.querySelector('.viewport-toolbar').after(runRibbon);
let runPoll=null, runRibbonKey=null;
runButton.onclick=()=>showRunDialog();
function showRunDialog(){
  const config=state.launch_config ?? {};
  runDialog.innerHTML=`<form id="run-form"><div class="dialog-heading"><h2>Build & Run</h2><button type="button" id="close-run" aria-label="Close">×</button></div><p>Launch a private copy of your selected runtime with this project's build.</p><label>Runtime executable<input id="run-exe" required value="${escapeHTML(config.runtime_executable)}" placeholder="C:\\path\\to\\LegaiaRecomp.exe" spellcheck="false"></label><label>BIOS image<input id="run-bios" required value="${escapeHTML(config.bios)}" placeholder="C:\\path\\to\\SCPH1001.BIN" spellcheck="false"></label><label>Game configuration<input id="run-config" required value="${escapeHTML(config.game_config)}" placeholder="C:\\path\\to\\game.toml" spellcheck="false"></label><label>Renderer<select id="run-renderer"><option value="software">Software</option><option value="opengl">OpenGL</option><option value="vulkan">Vulkan (requires runtime support)</option></select></label><label>Runtime debug port<input id="run-port" required type="number" min="1024" max="65535" value="${escapeHTML(config.debug_port ?? 4391)}"></label><p class="field-note">Each run has private mods, saves and logs under the project. Readiness verifies the game and enabled package; it does not establish gameplay correctness.</p><div id="run-summary"></div><div class="dialog-actions"><button type="submit" class="accent" id="launch-run">Build & launch</button></div><p class="dialog-error" role="alert"></p></form>`;
  $('run-renderer').value=config.renderer ?? 'software';
  $('close-run').onclick=()=>runDialog.close();
  $('run-form').onsubmit=async event=>{
    event.preventDefault();
    const config={runtime_executable:$('run-exe').value,bios:$('run-bios').value,game_config:$('run-config').value,debug_port:Number($('run-port').value),renderer:$('run-renderer').value};
    if(await api('/api/run/configure',config)){
      if(await api('/api/run',{}, {dialog:runDialog,success:'Private runtime launched. Checking identity and mod plan…'}))scheduleRunPoll();
    }
  };
  renderRunStatus();runDialog.showModal();
}
function renderRunStatus(){
  const run=state.run,active=run && (run.running || !['failed','exited','stopped'].includes(run.state));
  runRibbon.hidden=!run;
  const ribbonKey=JSON.stringify([run?.state,run?.pid,run?.ready,active]);
  if(run && ribbonKey!==runRibbonKey){runRibbon.replaceChildren();const text=document.createElement('span');text.textContent=`Run ${run.state}${run.pid?' · PID '+run.pid:''}${run.ready?' · Identity and mod plan verified':''}`;const details=document.createElement('button');details.textContent='Details';details.onclick=showRunDialog;runRibbon.append(text,details);if(active){const stop=document.createElement('button');stop.textContent='Stop';stop.onclick=()=>api('/api/run/stop',{});runRibbon.append(stop);}if(run.ready){const attach=document.createElement('button');attach.textContent='Attach';attach.onclick=()=>api('/api/run/attach',{});runRibbon.append(attach);}}
  runRibbonKey=ribbonKey;
  if($('run-summary')){$('run-summary').innerHTML=run?`<p><strong>${escapeHTML(run.state)}</strong> · ${escapeHTML(run.reason ?? '')}</p><label>Run folder<input readonly value="${escapeHTML(run.directory)}"></label><details><summary>Runtime and package evidence</summary><pre class="diagnostic-detail">${escapeHTML(JSON.stringify({pid:run.pid,executable_sha256:run.runtime_executable_sha256,identity:run.runtime_identity,mods:run.mod_status},null,2))}</pre></details>`:'';$('launch-run').disabled=busy||!!active;}
  runButton.disabled=busy||!state.capabilities?.build_and_run||!canEdit()||!!active;
}
function scheduleRunPoll(){
  clearTimeout(runPoll);
  if(!state.run || (!state.run.running && ['failed','exited','stopped'].includes(state.run.state)))return;
  runPoll=setTimeout(async()=>{try{const response=await fetch('/api/run/status');const data=await response.json();if(response.ok){state.run=data.run;renderRunStatus();}}catch(error){notify('Runtime status is unavailable: '+error.message,true);}scheduleRunPoll();},2000);
}
buildButton.onclick=async()=>{
  if(await api('/api/build',{})){
    const result=state.build;
    buildDialog.innerHTML=`<div class="dialog-heading"><h2>${result.build_kind==='retail'?'Retail baseline built':'Private mod package built'}</h2><button id="close-build" aria-label="Close">×</button></div><p>${result.build_kind==='retail'?'Retail baseline · no modified bytes':`${escapeHTML(result.changed_fields)} placement fields · ${escapeHTML(result.overlay_count)} scene overlays`}</p><p>Runtime launch has not been validated for this package.</p><label>Package path<input readonly value="${escapeHTML(result.path)}"></label><p>${escapeHTML(result.install_instruction)}</p>`;
    $('close-build').onclick=()=>buildDialog.close();buildDialog.showModal();
  }
};
document.querySelectorAll('[data-panel]').forEach(button=>{if(button.tagName==='BUTTON')button.onclick=()=>{document.querySelector('.workspace').dataset.panel=button.dataset.panel;document.querySelectorAll('.workspace-tabs button').forEach(tab=>tab.classList.toggle('active',tab===button));resize();};});

function notify(message, error=false) {
  $('toast').textContent=message; $('toast').classList.toggle('error',error); $('toast').hidden=false;
  clearTimeout(toastTimer); toastTimer=setTimeout(()=>{$('toast').hidden=true;},error?8500:3200);
}
function setBusy(value) {
  busy=value;
  for(const id of ['import-button','save-button','project-button','empty-import']) $(id).disabled=value;
  $('undo-button').disabled=value || !state.history?.can_undo;
  $('redo-button').disabled=value || !state.history?.can_redo;
  buildButton.disabled=value || !state.capabilities?.build || !canEdit();
  renderRunStatus();
  document.querySelectorAll('[data-axis]').forEach(input=>input.disabled=value || !canEdit());
}
async function api(path, payload, {dialog,success}={}) {
  if(busy) return false;
  setBusy(true);
  if(dialog) dialog.querySelector('.dialog-error').textContent='';
  try {
    const response=await fetch(path,{method:payload===undefined?'GET':'POST',headers:payload===undefined?{}:{'Content-Type':'application/json'},body:payload===undefined?undefined:JSON.stringify(payload)});
    const data=await response.json();
    if(!response.ok || data.error) throw new Error(typeof data.error==='string'?data.error:JSON.stringify(data.error ?? data));
    if(!data.project || !('scene' in data)) throw new Error('Project service returned an invalid state response.');
    state=data; render();
    $('connection-dot').classList.add('connected');
    if(dialog) dialog.close();
    if(success) notify(success);
    return true;
  } catch(error) {
    // Failed runtime capture can clear transient state; a launch failure can
    // still leave an owned child that must remain reachable through Stop.
    if(path.startsWith('/api/run') || path.startsWith('/api/runtime') || path==='/api/mode'){
      try{const response=await fetch('/api/state');const fresh=await response.json();if(response.ok && fresh.project && 'scene' in fresh){state=fresh;render();}}catch{}
    }
    if(dialog) dialog.querySelector('.dialog-error').textContent=error.message;
    else notify(error.message,true);
    $('status').textContent=error.message;
    return false;
  } finally {setBusy(false);}
}
function entities(){return state.scene?.entities ?? [];}
function selected(){return entities().find(e=>e.id===state.selection?.entity_id);}
function canEdit(){return (state.project?.mode ?? 'edit').toLowerCase()==='edit' && state.capabilities?.edit_transform!==false;}
function displayPosition(value){const p={x:numeric(value?.x)?value.x:0,y:numeric(value?.y)?value.y:0,z:numeric(value?.z)?value.z:0},matrix=activeScenePreview()?.position_to_display;return matrix?{x:matrix[0]*p.x+matrix[1]*p.y+matrix[2]*p.z+matrix[3],y:matrix[4]*p.x+matrix[5]*p.y+matrix[6]*p.z+matrix[7],z:matrix[8]*p.x+matrix[9]*p.y+matrix[10]*p.z+matrix[11]}:p;}
function position(entity){return displayPosition(entity.components?.Transform?.effective?.position ?? entity.components?.Transform?.imported?.position);}
function authored(entity){return Object.keys(entity.components?.Transform?.authored?.position ?? {}).length>0;}
function showDialog(id){const d=$(id);d.querySelector('.dialog-error')?.replaceChildren();d.showModal();}
document.querySelectorAll('[data-close]').forEach(button=>button.addEventListener('click',()=>button.closest('dialog').close()));
$('project-button').onclick=()=>{ $('project-name-input').value=state.project?.name ?? 'Legaia project'; $('project-path-input').value=state.project?.path ?? '';showDialog('project-dialog'); };
for(const id of ['import-button','empty-import']) $(id).onclick=()=>showDialog('import-dialog');
$('project-form').onsubmit=async event=>{event.preventDefault();await api('/api/project/new',{name:$('project-name-input').value,path:$('project-path-input').value},{dialog:$('project-dialog'),success:'Project created.'});};
$('open-project').onclick=async()=>{if(!$('project-path-input').reportValidity())return;await api('/api/project/open',{path:$('project-path-input').value},{dialog:$('project-dialog'),success:'Project opened.'});};
$('import-form').onsubmit=async event=>{event.preventDefault();$('status').textContent='Importing scene from local disc image…';await api('/api/import',{disc:$('disc-input').value,scene:$('scene-input').value},{dialog:$('import-dialog'),success:'Scene imported.'});};
$('save-button').onclick=()=>api('/api/project/save',{}, {success:'Project saved.'});
$('undo-button').onclick=()=>api('/api/undo',{});
$('redo-button').onclick=()=>api('/api/redo',{});
$('edit-mode').onclick=()=>api('/api/mode',{mode:'edit'});
$('live-mode').onclick=()=>api('/api/mode',{mode:'live'});
$('entity-search').oninput=renderHierarchy;
$('frame-all').onclick=()=>frame();
$('frame-selected').onclick=()=>{const entity=selected();if(entity)frame(entity);};
$('grid-toggle').onclick=()=>{grid=!grid;$('grid-toggle').classList.toggle('active',grid);$('grid-toggle').setAttribute('aria-pressed',grid);draw();};
$('diagnostics-button').onclick=()=>{
  $('diagnostics').replaceChildren();
  const diagnostics=state.diagnostics ?? [];
  if(!diagnostics.length){const p=document.createElement('p');p.textContent='No project diagnostics reported.';$('diagnostics').append(p);}
  for(const diagnostic of diagnostics){const item=document.createElement('div');item.className='diagnostic';const title=document.createElement('strong');title.textContent=diagnostic.code ?? diagnostic.severity ?? 'Diagnostic';const p=document.createElement('p');p.textContent=diagnostic.message ?? (typeof diagnostic==='string'?diagnostic:JSON.stringify(diagnostic));item.append(title,p);$('diagnostics').append(item);}
  if(scenePreview||sceneError){const details=document.createElement('details');details.className='scene-preview-evidence';details.innerHTML='<summary>Scene model evidence and limits</summary><pre></pre>';details.querySelector('pre').textContent=JSON.stringify({source_key:sceneKey,error:sceneError,metrics:scenePreview?.metrics,limits:scenePreview?.limits,entities:scenePreview?.entities},null,2);$('diagnostics').append(details);}
  $('diagnostics-dialog').showModal();
};
document.addEventListener('keydown',event=>{
  if(event.target.matches('input,textarea') || document.querySelector('dialog[open]')) return;
  if((event.ctrlKey||event.metaKey) && event.key.toLowerCase()==='s'){event.preventDefault();if(!busy)api('/api/project/save',{}, {success:'Project saved.'});}
  if((event.ctrlKey||event.metaKey) && event.key.toLowerCase()==='z'){event.preventDefault();const redo=event.shiftKey;if(redo?state.history?.can_redo:state.history?.can_undo)api(redo?'/api/redo':'/api/undo',{});}
  if(event.key.toLowerCase()==='f' && selected())frame(selected());
});
window.addEventListener('beforeunload',event=>{if(state.project?.dirty){event.preventDefault();event.returnValue='';}});

function render(){
  $('project-name').textContent=state.project?.name ?? 'No project';
  $('dirty').hidden=!state.project?.dirty;
  $('scene-name').textContent=state.scene?.name ?? 'No scene imported';
  $('viewport-title').textContent=state.scene?.name ?? 'Scene';
  $('entity-count').textContent=entities().length;
  $('asset-count').textContent=(state.assets ?? []).length;
  $('diagnostic-count').textContent=(state.diagnostics ?? []).length;
  $('viewport-empty').hidden=!!state.scene?.id;
  sceneSelect.replaceChildren();for(const scene of state.scenes ?? []){const option=document.createElement('option');option.value=scene.id;option.textContent=scene.name;option.selected=scene.id===state.scene?.id;sceneSelect.append(option);}sceneSelect.hidden=(state.scenes ?? []).length<2;
  const live=(state.project?.mode ?? 'edit').toLowerCase()==='live';
  $('edit-mode').classList.toggle('active',!live);$('live-mode').classList.toggle('active',live);$('live-mode').disabled=!state.capabilities?.live_mode;
  document.querySelector('.inspector-panel .tag').textContent=live?'LIVE':'EDIT';
  $('live-mode').title=state.capabilities?.live_mode?'Observe runtime state':state.runtime?.reason?.message ?? 'Runtime observation is unavailable';
  runtimeBox.replaceChildren();runtimeBox.hidden=!state.capabilities?.runtime_discovery;
  if(!runtimeBox.hidden){const text=document.createElement('span');text.textContent=state.runtime?.available?'Runtime connected · Read-only observation':state.runtime?.reason?.message ?? 'Runtime has not been checked';const button=document.createElement('button');button.textContent='Check runtime';button.onclick=()=>api('/api/runtime/discover',{});runtimeBox.append(text,button);}
  if(state.runtime?.available){const observe=document.createElement('button');observe.textContent='Observe actors';observe.onclick=()=>api('/api/runtime/observe',{include_actors:true});runtimeBox.append(observe);}
  document.querySelector('.preview-badge').firstChild.textContent=live?'AUTHORED SCENE · LIVE OBSERVATIONS SEPARATE':'SCENE PREVIEW';
  $('frame-selected').disabled=!selected();
  $('status').textContent=state.scene?.id ? `${state.scene.name} · ${entities().length} entities · ${state.project?.dirty?'Changes not saved':'Project ready'}` : 'Ready · Create or open a project to begin';
  renderHierarchy();renderAssets();renderInspector();
  templateButton.disabled=!state.capabilities?.authored_transform_templates;
  if(templateDialog.open)renderTemplates();
  renderRunStatus();scheduleRunPoll();
  if(lastSceneId!==state.scene?.id){lastSceneId=state.scene?.id;frame();}else draw();
  refreshScenePreview();
}
function activeScenePreview(){return scenePreview&&sceneKey===state.scene_preview_source_key&&scenePreview.scene_id===state.scene?.id?scenePreview:null;}
function sceneModelsReady(){return modelsEnabled&&activeScenePreview()&&sceneRenderer&&!sceneRenderer.lost&&!sceneError;}
function sceneView(){return {camera,basis:basis(),width,height,grid,positions:new Map(entities().map(entity=>[entity.id,draft?.id===entity.id?draft.position:position(entity)]))};}
function updateSceneBadge(){
  const ready=sceneModelsReady(),count=ready?sceneRenderer.instances.length:0;
  $('scene-models').hidden=!ready;
  modelToggle.hidden=!state.capabilities?.scene_preview;modelToggle.textContent=sceneError?'Retry models':'Models';modelToggle.title=sceneError ?? 'Show supported SDK meshes at authored placements';
  document.querySelector('.preview-badge span').textContent=sceneError?'Models unavailable · placement markers remain usable':scenePendingKey?'Loading supported scene models…':ready?`${count} / ${entities().length} models · unresolved objects remain markers`:modelsEnabled?'Placement markers · model data unavailable':'Placement markers · models hidden';
  $('coordinate-note').textContent=activeScenePreview()?'Unknown height: ground plane · unknown facing: preview convention':'Unknown heights are shown on the ground plane.';
  $('coordinate-note').title=JSON.stringify(activeScenePreview()?.limits ?? []);
}
async function refreshScenePreview(){
  const key=state.scene_preview_source_key;
  if(!state.capabilities?.scene_preview||!key||!modelsEnabled){sceneAbort?.abort();scenePendingKey=null;updateSceneBadge();return;}
  if(sceneKey===key||scenePendingKey===key||sceneFailedKey===key){updateSceneBadge();return;}
  sceneAbort?.abort();const controller=new AbortController();sceneAbort=controller;scenePendingKey=key;sceneError=null;scenePreview=null;sceneRenderer?.clear();
  const expectedScene=state.scene?.id,revision=cameraRevision;updateSceneBadge();draw();
  try{
    if(!sceneRenderer){const module=await import('/scene-renderer.js');if(controller.signal.aborted)return;sceneRenderer=new module.SceneRenderer($('scene-models'),message=>{sceneError=message;updateSceneBadge();draw();});}
    const response=await fetch('/api/scene-preview',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}',signal:controller.signal});
    const data=await response.json();if(!response.ok||data.error)throw new Error(typeof data.error==='string'?data.error:'Scene preview failed');
    if(controller.signal.aborted||state.scene_preview_source_key!==key||state.scene?.id!==expectedScene)return;
    if(data.source_key!==key||data.scene_id!==expectedScene)throw new Error('Scene preview source changed while loading; retry models.');
    if(!Array.isArray(data.position_to_display)||data.position_to_display.length!==16||!data.position_to_display.every(numeric))throw new Error('SDK did not provide a valid scene display conversion.');
    const failures=sceneRenderer.load(data);scenePreview=data;sceneKey=key;sceneFailedKey=null;scenePendingKey=null;
    if(failures.length)notify(`${failures.length} model assets could not be rendered; their placement markers remain available.`,true);
    renderInspector();if(revision===cameraRevision&&!drag)frame();else draw();
  }catch(error){if(error.name!=='AbortError'&&state.scene_preview_source_key===key){sceneFailedKey=key;sceneError=error.message;scenePendingKey=null;sceneRenderer?.clear();notify(error.message,true);}}
  finally{if(sceneAbort===controller){sceneAbort=null;scenePendingKey=null;updateSceneBadge();draw();}}
}
function renderHierarchy(){
  const list=$('hierarchy');list.replaceChildren();
  const filter=$('entity-search').value.toLowerCase();
  for(const entity of entities().filter(e=>`${e.name} ${e.id}`.toLowerCase().includes(filter))){
    const row=document.createElement('button');row.className='entity-row';row.setAttribute('role','treeitem');row.setAttribute('aria-selected',entity.id===state.selection?.entity_id);row.classList.toggle('selected',entity.id===state.selection?.entity_id);row.title=entity.id;
    row.innerHTML=`<span class="entity-icon">◇</span><span class="entity-name">${escapeHTML(entity.name ?? entity.id)}</span>${authored(entity)?'<span class="authored-dot" title="Authored transform"></span>':''}`;
    row.onclick=()=>api('/api/selection',{entity_id:entity.id});row.ondblclick=()=>frame(entity);list.append(row);
  }
  if(!list.children.length){const p=document.createElement('div');p.className='empty-panel';p.textContent=entities().length?'No matching entities.':'Imported actors will appear here.';list.append(p);}
}
function renderAssets(){
  const list=$('assets');list.replaceChildren();
  for(const asset of state.assets ?? []){const card=document.createElement('button');card.className='asset-card';card.title=asset.id;card.innerHTML=`<span class="asset-symbol">⬡</span><strong>${escapeHTML(asset.name ?? asset.label ?? asset.id)}</strong><small>${escapeHTML(asset.kind ?? asset.type ?? 'Imported asset')}</small>`;card.onclick=()=>openModel(asset.id);list.append(card);}
  if(!list.children.length){const p=document.createElement('div');p.className='field-note';p.style.gridColumn='1 / -1';p.textContent='Stable asset references from your imported scene.';list.append(p);}
}
function property(label,value){return `<dl class="property"><dt>${escapeHTML(label)}</dt><dd>${escapeHTML(value ?? 'Unknown')}</dd></dl>`;}
function showTemplates(){renderTemplates();templateDialog.showModal();}
function renderTemplates(){
  const entity=selected(),position=entity?.components?.Transform?.authored?.position ?? {},templates=state.actor_templates ?? [];
  const axes=Object.entries(position).map(([axis,value])=>`${axis.toUpperCase()} ${format(value)}`).join(' · ');
  templateDialog.innerHTML=`<div class="dialog-heading"><h2>Authored transform templates</h2><button type="button" id="close-templates" aria-label="Close">×</button></div><p>Save authored position axes and apply their absolute values to an existing imported actor. Other axes stay unchanged.</p><p class="field-note">Position only: no native actor spawning, model or animation presets. Height stays project-only; Build still requires representable X/Z values.</p><form id="create-template-form"><label>Template name<input id="template-name" required maxlength="80" placeholder="For example, courtyard position" ${canEdit() && axes?'':'disabled'}></label><p class="field-note">${entity?`Selected: ${escapeHTML(entity.name)} · ${axes?escapeHTML(axes):'Author a position axis to capture a template.'}`:'Select an imported actor to capture or apply a template.'}</p><button type="submit" ${canEdit() && axes?'':'disabled'}>Capture authored position</button></form><div id="template-list" class="template-list"></div><p class="field-note">Template changes use Undo / Redo. Save the project to keep the library.</p>`;
  $('close-templates').onclick=()=>templateDialog.close();
  const errorMessage=document.createElement('p');errorMessage.className='dialog-error';errorMessage.setAttribute('role','alert');templateDialog.append(errorMessage);
  const command=async body=>{const result=await api('/api/command',body);if(!result)errorMessage.textContent=$('status').textContent;return result;};
  $('create-template-form').onsubmit=async event=>{event.preventDefault();await command({type:'create_actor_template',entity_id:entity.id,name:$('template-name').value});};
  for(const template of templates){
    const card=document.createElement('section');card.className='template-card';
    const values=Object.entries(template.components.Transform.position).map(([axis,value])=>`${axis.toUpperCase()} ${format(value)}`).join(' · ');
    card.innerHTML=`<strong>${escapeHTML(template.name)}</strong><p>${escapeHTML(values)}</p><details><summary>Source provenance</summary><p>${escapeHTML(template.source.scene_id)}<br>${escapeHTML(template.source.entity_id)}</p><code>${escapeHTML(template.source.disc_identity)}</code></details><div class="template-actions"><button data-apply ${canEdit() && entity?'':'disabled'}>Apply to ${escapeHTML(entity?.name ?? 'selected actor')}</button><button data-delete ${canEdit()?'':'disabled'}>Delete</button></div>`;
    card.querySelector('[data-apply]').onclick=()=>command({type:'apply_actor_template',template_id:template.id,entity_id:entity.id});
    card.querySelector('[data-delete]').onclick=()=>command({type:'delete_actor_template',template_id:template.id});
    $('template-list').append(card);
  }
  if(!templates.length)$('template-list').innerHTML='<p class="field-note">No authored transform templates yet.</p>';
}
function renderInspector(){
  const entity=selected();
  $('selection-summary').textContent=entity?entity.name ?? entity.id:'No entity selected';
  if(!entity){$('inspector').innerHTML='<div class="empty-panel">Select an entity in the scene<br>or hierarchy to inspect it.</div>';return;}
  const components=entity.components ?? {}, transform=components.Transform ?? {}, original=transform.imported?.position ?? {}, override=transform.authored?.position ?? {}, effective=transform.effective?.position ?? original;
  let html=`<div class="entity-heading"><h2>${escapeHTML(entity.name ?? entity.id)}</h2><code>${escapeHTML(entity.id)}</code></div><section class="component"><h3>Transform <small>Scene units</small></h3><div class="transform-table"><span></span><span class="column-title">Imported</span><span class="column-title">Authored</span><span class="column-title">Effective</span>`;
  for(const axis of ['x','y','z'])html+=`<span class="axis-${axis}">${axis.toUpperCase()}</span><output title="${format(original[axis])}">${format(original[axis])}</output><input data-axis="${axis}" aria-label="Authored ${axis.toUpperCase()}" type="number" step="1" placeholder="—" value="${numeric(override[axis])?override[axis]:''}" ${canEdit()?'':'disabled'}><output class="effective">${format(effective[axis])}</output>`;
  html+='</div><p class="field-note">Edits are project overrides. Empty authored fields inherit the imported value. Unknown heights use the ground plane. Scene display axes follow the SDK conversion.</p></section>';
  if(state.capabilities?.authored_transform_templates)html+='<section class="component"><h3>Authored templates <small>Position only</small></h3><p class="field-note">Capture authored axes or apply saved positions to this existing actor.</p><button id="inspect-templates">Open transform templates…</button></section>';
  if(components.ModelRenderer){const model=components.ModelRenderer;html+=`<section class="component"><h3>Model renderer <small>Imported reference</small></h3>${property('Asset',model.asset_id)}${property('Resolution',model.resolution_status)}<p class="field-note">Scene meshes use supported SDK poses. Unresolved objects stay as placement markers; individual assets can be inspected separately.</p>${model.asset_id?'<button id="inspect-model" class="model-preview-button">Inspect model objects</button>':''}</section>`;}
  if(components.Animation)html+=`<section class="component"><h3>Animation</h3>${property('Imported ID',components.Animation.imported_id)}<p class="field-note">An association is not a verified playable animation.</p></section>`;
  if(components.RuntimeCorrelation){const correlation=components.RuntimeCorrelation;html+=`<section class="component"><h3>Runtime observation <small>Read only · sampled</small></h3>${property('Correlation',correlation.status ?? correlation.state ?? 'Unresolved')}<p class="field-note">Candidate associations preserve ambiguity. They do not replace imported or authored values.</p><details><summary>Epoch, candidates and evidence</summary><pre>${escapeHTML(JSON.stringify(correlation,null,2))}</pre></details></section>`;}
  if(components.RetailMetadata){const retail=components.RetailMetadata,source=retail.source_record;const summary=source&&typeof source==='object'?(source.prot_entry_name ?? source.scene ?? source.kind ?? 'Imported record'):source;html+=`<section class="component"><h3>Retail metadata <small>Read only</small></h3>${property('Source',summary)}<details><summary>Source, evidence and unresolved fields</summary><pre>${escapeHTML(JSON.stringify({source_record:source,claims:retail.claims,unresolved:retail.unresolved},null,2))}</pre></details></section>`;}
  $('inspector').innerHTML=html;
  if($('inspect-model'))$('inspect-model').onclick=()=>openModel(components.ModelRenderer.asset_id);
  const animatedAsset=(state.assets ?? []).find(asset=>asset.id===components.ModelRenderer?.asset_id && asset.animation_support?.supported);
  if(animatedAsset && $('inspect-model')){const button=document.createElement('button');button.className='model-preview-button';button.textContent='Preview reference locomotion';button.title='Decoded idle/walk clips for this model; separate from the placement animation ID';button.onclick=()=>openModel(animatedAsset.id,'idle');$('inspect-model').after(button);}
  if($('inspect-templates'))$('inspect-templates').onclick=showTemplates;
  $('inspector').querySelectorAll('[data-axis]').forEach(input=>input.addEventListener('change',async()=>{
    const axis=input.dataset.axis;
    if(input.value===''){await api('/api/command',{type:'clear_transform',entity_id:entity.id,axes:[axis]});return;}
    const value=Number(input.value);if(!Number.isFinite(value)){notify('Transform values must be finite numbers.',true);renderInspector();return;}
    await api('/api/command',{type:'set_transform',entity_id:entity.id,position:{[axis]:value}});
  }));
}

function frame(entity){
  const points=entity?[position(entity)]:entities().map(position);
  const hasMesh=sceneModelsReady()&&(!entity||sceneRenderer.hasEntity(entity.id));
  if(hasMesh)points.push(...sceneRenderer.bounds(sceneView().positions,entity?.id));
  if(!points.length){camera.target={x:0,y:0,z:0};camera.distance=2000;draw();return;}
  const min={x:Infinity,y:Infinity,z:Infinity},max={x:-Infinity,y:-Infinity,z:-Infinity};
  for(const p of points)for(const axis of ['x','y','z']){min[axis]=Math.min(min[axis],p[axis]);max[axis]=Math.max(max[axis],p[axis]);}
  for(const axis of ['x','y','z'])camera.target[axis]=(min[axis]+max[axis])/2;
  const span=Math.hypot(max.x-min.x,max.y-min.y,max.z-min.z);
  camera.distance=entity?(hasMesh?Math.max(20,span*2.2):Math.max(100,camera.distance*.35)):Math.max(200,span*1.3);cameraRevision++;
  draw();
}
function basis(){const s=Math.sin(camera.yaw),c=Math.cos(camera.yaw),sp=Math.sin(camera.pitch),cp=Math.cos(camera.pitch);return {right:{x:c,y:0,z:-s},up:{x:-s*sp,y:cp,z:-c*sp},forward:{x:-s*cp,y:-sp,z:-c*cp}};}
function project(p){const b=basis(),d={x:p.x-camera.target.x,y:p.y-camera.target.y,z:p.z-camera.target.z},dot=v=>d.x*v.x+d.y*v.y+d.z*v.z,depth=camera.distance+dot(b.forward);if(depth<=camera.distance*.01)return null;const scale=Math.min(width,height)*.9/depth;return {x:width/2+dot(b.right)*scale,y:height/2-dot(b.up)*scale,depth,scale};}
function groundAt(x,y,planeY){
  const b=basis(),f=Math.min(width,height)*.9;
  const origin={x:camera.target.x-camera.distance*b.forward.x,y:camera.target.y-camera.distance*b.forward.y,z:camera.target.z-camera.distance*b.forward.z};
  const ray={};for(const axis of ['x','y','z'])ray[axis]=b.forward[axis]+(x-width/2)/f*b.right[axis]-(y-height/2)/f*b.up[axis];
  if(Math.abs(ray.y)<.00001)return null;const t=(planeY-origin.y)/ray.y;if(t<0)return null;
  return {x:origin.x+t*ray.x,y:planeY,z:origin.z+t*ray.z};
}
function line(a,b,color,widthPx=1){const p=project(a),q=project(b);if(!p||!q)return;ctx.strokeStyle=color;ctx.lineWidth=widthPx;ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(q.x,q.y);ctx.stroke();}
function draw(){
  if(!ctx)return;ctx.clearRect(0,0,width,height);projected=[];handles=[];
  if(sceneModelsReady()){try{sceneRenderer.draw(sceneView());}catch(error){sceneError=error.message;}}
  updateSceneBadge();
  if(grid&&!sceneModelsReady()){const spacing=10**Math.floor(Math.log10(camera.distance/7)),half=spacing*12,cx=Math.round(camera.target.x/spacing)*spacing,cz=Math.round(camera.target.z/spacing)*spacing;for(let i=-12;i<=12;i++){line({x:cx+i*spacing,y:0,z:cz-half},{x:cx+i*spacing,y:0,z:cz+half},i===0?'#39504f88':'#33474c66');line({x:cx-half,y:0,z:cz+i*spacing},{x:cx+half,y:0,z:cz+i*spacing},i===0?'#39504f88':'#33474c66');}}
  const items=entities().map(entity=>{const world=draft?.id===entity.id?draft.position:position(entity);return {entity,world,p:project(world)};}).filter(item=>item.p).sort((a,b)=>b.p.depth-a.p.depth);
  for(const {entity,world,p} of items){
    const active=entity.id===state.selection?.entity_id,rendered=sceneModelsReady()&&sceneRenderer.hasEntity(entity.id),radius=active?7:4.5;
    if(rendered&&!active)continue;
    projected.push({id:entity.id,x:p.x,y:p.y});ctx.beginPath();ctx.ellipse(p.x,p.y+5,active?12:7,active?4:2.5,0,0,Math.PI*2);ctx.fillStyle='#02090966';ctx.fill();
    ctx.beginPath();ctx.moveTo(p.x,p.y-radius);ctx.lineTo(p.x+radius,p.y);ctx.lineTo(p.x,p.y+radius);ctx.lineTo(p.x-radius,p.y);ctx.closePath();ctx.fillStyle=active?'#c9edce':authored(entity)?'#d2ae70':'#759d8d';ctx.fill();ctx.strokeStyle=active?'#f1fff0':'#a8c6b6';ctx.lineWidth=active?1.5:1;ctx.stroke();
    if(active){
      ctx.font='11px "Segoe UI", sans-serif';ctx.fillStyle='#c8ddd1';ctx.fillText(entity.name ?? entity.id,p.x+12,p.y-10);
      if(authored(entity)||draft?.id===entity.id){
        const original=displayPosition(entity.components?.Transform?.imported?.position),q=project(original);
        if(q&&Math.hypot(q.x-p.x,q.y-p.y)>3){ctx.save();ctx.setLineDash([4,4]);line(original,world,'#d6ad6c',1.5);ctx.setLineDash([]);ctx.strokeStyle='#d6ad6c';ctx.strokeRect(q.x-4,q.y-4,8,8);ctx.fillStyle='#e7c188';ctx.fillText('Imported',q.x+8,q.y+14);ctx.restore();}
      }
      if(canEdit()){const length=camera.distance*.085;for(const [axis,color] of [['x','#e0988a'],['z','#8bbbdc']]){const end={...world,[axis]:world[axis]+length},q=project(end);if(!q)continue;line(world,end,color,2);ctx.fillStyle=color;ctx.beginPath();ctx.arc(q.x,q.y,4,0,Math.PI*2);ctx.fill();ctx.font='bold 10px "Segoe UI",sans-serif';ctx.fillText(axis.toUpperCase(),q.x+7,q.y+3);handles.push({axis,x:q.x,y:q.y,start:p});}}
    }
  }
}
function resize(){const rect=canvas.getBoundingClientRect(),dpr=window.devicePixelRatio||1;width=rect.width;height=rect.height;canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);draw();}
new ResizeObserver(resize).observe(canvas);
function pointer(event){const r=canvas.getBoundingClientRect();return {x:event.clientX-r.left,y:event.clientY-r.top};}
canvas.addEventListener('contextmenu',event=>event.preventDefault());
canvas.addEventListener('pointerdown',event=>{
  if(busy)return;const p=pointer(event),entity=selected();canvas.focus();canvas.setPointerCapture(event.pointerId);
  const handle=event.button===0 && entity && canEdit()?handles.find(h=>Math.hypot(h.x-p.x,h.y-p.y)<12):null;
  drag={start:p,last:p,moved:false,type:handle?'transform':event.button===2||event.button===1||event.shiftKey?'pan':'orbit',handle,entity:entity?.id,original:entity?position(entity):null};
  if(handle)drag.ground=groundAt(p.x,p.y,drag.original.y);
  canvas.classList.add('dragging');
});
canvas.addEventListener('pointermove',event=>{
  if(!drag)return;const p=pointer(event),dx=p.x-drag.last.x,dy=p.y-drag.last.y;
  if(Math.hypot(p.x-drag.start.x,p.y-drag.start.y)>3)drag.moved=true;
  if(drag.moved){
    if(drag.type==='transform'){const point=groundAt(p.x,p.y,drag.original.y);if(point&&drag.ground){const axis=drag.handle.axis;draft={id:drag.entity,position:{...drag.original,[axis]:Math.round(drag.original[axis]+point[axis]-drag.ground[axis])}};}}
    else if(drag.type==='orbit'){camera.yaw-=dx*.006;camera.pitch=Math.max(.12,Math.min(1.42,camera.pitch+dy*.005));cameraRevision++;}
    else {const b=basis(),scale=camera.distance/Math.max(1,Math.min(width,height)*.9);camera.target.x-=dx*scale*b.right.x;camera.target.z-=dx*scale*b.right.z;camera.target.x-=dy*scale*Math.sin(camera.yaw)/Math.max(.15,Math.sin(camera.pitch));camera.target.z-=dy*scale*Math.cos(camera.yaw)/Math.max(.15,Math.sin(camera.pitch));cameraRevision++;}
    draw();
  }
  drag.last=p;
});
canvas.addEventListener('pointerup',async event=>{
  if(!drag)return;const finished=drag,p=pointer(event),edit=draft;drag=null;draft=null;canvas.classList.remove('dragging');
  if(finished.type==='transform' && edit){const axis=finished.handle.axis;if(edit.position[axis]!==finished.original[axis])await api('/api/command',{type:'set_transform',entity_id:finished.entity,position:{[axis]:edit.position[axis]}});}
  else if(!finished.moved && event.button===0){let hit=[...projected].reverse().find(item=>Math.hypot(item.x-p.x,item.y-p.y)<12)?.id;if(!hit&&sceneModelsReady()){try{hit=sceneRenderer.pick(p.x,p.y,sceneView());}catch(error){notify(error.message,true);}}if(hit)await api('/api/selection',{entity_id:hit});}
  draw();
});
canvas.addEventListener('pointercancel',()=>{drag=null;draft=null;canvas.classList.remove('dragging');draw();});
canvas.addEventListener('wheel',event=>{event.preventDefault();camera.distance=Math.max(20,Math.min(1e8,camera.distance*Math.exp(event.deltaY*.001)));cameraRevision++;draw();},{passive:false});

// Unposed assets stay object-local. Only decoder-provided frames assemble objects.
const modelCanvas=$('model-canvas'), modelContext=modelCanvas.getContext('2d');
const exportDialog=document.createElement('dialog');document.body.append(exportDialog);
let model=null, modelDrag=null, modelRequest=0;
let modelTextures=new Map();
let modelAssetId=null, animationFrame=0, animationTick=null, animationClock=null;
const modelView={yaw:.55,pitch:-.18,zoom:1,center:[0,0,0],radius:1};
async function openModel(assetId,clipId=null){
  if(busy)return;stopAnimation();setBusy(true);$('model-error').textContent='';$('animation-clip').disabled=true;const request=++modelRequest;
  try{
    const response=await fetch(clipId?'/api/animation-preview':'/api/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:assetId,...(clipId?{clip_id:clipId}:{})})});
    const data=await response.json();if(!response.ok||data.error)throw new Error(typeof data.error==='string'?data.error:JSON.stringify(data.error ?? data));
    if(!Array.isArray(data.vertices)||!Array.isArray(data.triangles)||!Array.isArray(data.objects))throw new Error('Model service returned no decoded geometry.');
    if(request!==modelRequest)return;
    if(clipId && (!Array.isArray(data.frames) || !data.frames.length || data.frames.length*data.vertices.length>1000000 || data.frames.some(frame=>frame.coordinate_system!=='retail_psx_actor_local_y_down'||!Array.isArray(frame.vertices)||frame.vertices.length!==data.vertices.length||frame.vertices.some(v=>!Array.isArray(v)||v.length!==3||!v.every(numeric)))))throw new Error('Animation service returned an invalid or oversized posed vertex stream.');
    model=data;modelAssetId=assetId;animationFrame=0;$('model-dialog').querySelector('h2').textContent=assetId.split('/').slice(-2).join(' / ');
    modelTextures=new Map();$('model-textures').replaceChildren();
    for(const texture of model.textures ?? []){
      const card=document.createElement('div');card.className='texture-card';
      if(texture.status==='address_match' && texture.rgba_base64){
        const bytes=Uint8ClampedArray.from(atob(texture.rgba_base64),c=>c.charCodeAt(0));
        if(bytes.length!==texture.width*texture.height*4 || bytes.length>2*1024*1024)throw new Error('Invalid decoded texture size');
        const image=document.createElement('canvas');image.width=texture.width;image.height=texture.height;image.getContext('2d').putImageData(new ImageData(bytes,texture.width,texture.height),0,0);card.append(image);modelTextures.set(texture.material_index,{image,origin:texture.uv_origin});
      }
      const statusLabel={address_match:'Matched texture',missing:'Texture not found',ambiguous:'Multiple possible textures',unsupported:'Unsupported texture',untextured:'Vertex colors'}[texture.status] ?? 'Texture unavailable';
      const label=document.createElement('span');label.textContent=`Material ${texture.material_index} · ${statusLabel}${texture.width?' · '+texture.width+'×'+texture.height:''}`;card.append(label);card.title=texture.reason ?? 'Static texture addresses; runtime residency is not confirmed'; $('model-textures').append(card);
    }
    $('model-description').textContent=`Drag to orbit · Scroll to zoom · ${clipId?'Decoded rigid animation pose':'Retail object-local geometry · Unposed'} · ${modelTextures.size?(model.texture_scope==='field_party'?'Shared party texture bank':'Static texture address matches'):'Vertex colors'} · No texture-window, animated palette or blend reconstruction`;
    $('model-object').replaceChildren();
    if(model.frames?.length){const all=document.createElement('option');all.value='all';all.textContent='Animated assembly · supported objects';$('model-object').append(all);}
    for(let index=0;index<model.objects.length;index++){const object=model.objects[index],option=document.createElement('option');option.value=index;option.textContent=`Object ${object.object_index ?? index} · ${object.triangle_count} triangles`;$('model-object').append(option);}
    $('model-diagnostics').textContent=(model.diagnostics ?? []).map(d=>typeof d==='string'?d:d.message ?? (d.kind==='equipment_templates_excluded'?'Equipment template objects 10 and 11 are excluded from this pose.':JSON.stringify(d))).join(' · ');
    configureAnimation(clipId);
    if(!$('model-dialog').open)$('model-dialog').showModal();
    fitModelObject();
  }catch(error){if($('model-dialog').open){$('model-error').textContent=error.message;$('animation-clip').value=model?.animation?.clip_id ?? '';}else notify(error.message,true);}finally{$('animation-clip').disabled=false;setBusy(false);}
}
function modelObject(){return $('model-object').value==='all' && model?.frames?.length?{vertex_start:0,vertex_count:model.vertices.length,triangle_start:0,triangle_count:model.triangles.length}:model?.objects[Number($('model-object').value)];}
function frameVertices(){return model?.frames?.[animationFrame]?.vertices ?? model?.vertices ?? [];}
function configureAnimation(clipId){
  const support=model.animation_support ?? {},clips=support.clips ?? [],frames=model.frames ?? [];
  $('animation-controls').hidden=!support.supported && !frames.length;
  $('animation-clip').replaceChildren();const unposed=document.createElement('option');unposed.value='';unposed.textContent='Object-local geometry (unposed)';$('animation-clip').append(unposed);
  for(const clip of clips){const option=document.createElement('option');option.value=clip.id;option.textContent=clip.label;$('animation-clip').append(option);}
  $('animation-clip').value=clipId ?? '';
  const timing=model.animation?.timing ?? model.timing ?? {},fps=numeric(timing.fps)?timing.fps:10;
  $('animation-rate').value=fps;$('animation-rate').parentElement.querySelector('span').textContent=numeric(timing.fps)?`Reference rate: ${timing.fps} fps; not verified against a live trace.`:'Preview setting; retail timing is unresolved.';
  $('animation-evidence').textContent=JSON.stringify(model.animation?{...model.animation,geometry_diagnostics:model.diagnostics,texture_catalog:model.texture_catalog}:support,null,2);
  $('animation-error').textContent='';
  for(const id of ['animation-play','animation-previous','animation-next','animation-frame','animation-rate'])$(id).disabled=!frames.length;
  $('animation-frame').max=Math.max(0,frames.length-1);$('animation-frame').value=0;
  $('animation-frame-label').textContent=frames.length?`1 / ${frames.length}`:'No clip loaded';
}
function stopAnimation(){if(animationTick!==null)cancelAnimationFrame(animationTick);animationTick=null;animationClock=null;$('animation-play').textContent='Play';}
function setAnimationFrame(index){const count=model?.frames?.length ?? 0;if(!count)return;animationFrame=((index%count)+count)%count;$('animation-frame').value=animationFrame;$('animation-frame-label').textContent=`${animationFrame+1} / ${count}`;drawModel();}
$('animation-clip').onchange=()=>openModel(modelAssetId,$('animation-clip').value || null);
$('animation-frame').oninput=()=>{stopAnimation();setAnimationFrame(Number($('animation-frame').value));};
$('animation-previous').onclick=()=>{stopAnimation();setAnimationFrame(animationFrame-1);};
$('animation-next').onclick=()=>{stopAnimation();setAnimationFrame(animationFrame+1);};
$('animation-rate').onchange=()=>{const rate=Number($('animation-rate').value);$('animation-rate').value=Number.isFinite(rate)?Math.max(1,Math.min(60,rate)):10;animationClock=null;};
$('animation-play').onclick=()=>{
  if(animationTick!==null){stopAnimation();return;}if(!model?.frames?.length)return;
  $('animation-play').textContent='Pause';
  const tick=time=>{if(!$('model-dialog').open){stopAnimation();return;}if(animationClock===null)animationClock=time;const step=1000/Math.max(1,Math.min(60,Number($('animation-rate').value)||10)),advance=Math.floor((time-animationClock)/step);if(advance){animationClock+=advance*step;setAnimationFrame(animationFrame+advance);}animationTick=requestAnimationFrame(tick);};
  animationTick=requestAnimationFrame(tick);
};
$('model-dialog').addEventListener('close',()=>{stopAnimation();modelRequest++;});
document.addEventListener('visibilitychange',()=>{if(document.hidden)stopAnimation();});
$('model-export').onclick=async()=>{
  if(busy||!modelAssetId)return;stopAnimation();setBusy(true);$('model-export').disabled=true;$('model-error').textContent='';
  const clip=model.animation?.clip_id,payload={asset_id:modelAssetId,...(clip?{clip_id:clip,frame_index:animationFrame}:{})};
  try{
    const response=await fetch('/api/export/model',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    const result=await response.json();if(!response.ok||result.error)throw new Error(result.error ?? 'Model export failed');
    exportDialog.innerHTML=`<div class="dialog-heading"><h2>${result.audit.posed?'Static posed model exported':'Object-local model exported'}</h2><button id="close-export" aria-label="Close">×</button></div><p>${result.audit.object_count} objects · ${result.audit.triangle_count} triangles · ${result.audit.texture_count} embedded textures${result.audit.posed?' · Frame '+(result.audit.frame_index+1):''}</p><label>Private GLB file<input readonly value="${escapeHTML(result.path)}"></label><p>Full model export${result.audit.posed?' with the displayed animation frame baked into geometry':''}. Source units are retained; physical meter scale is unknown. Animation channels and skin hierarchy are not exported.</p><details><summary>Export provenance and limitations</summary><pre class="diagnostic-detail">${escapeHTML(JSON.stringify(result.audit,null,2))}</pre></details>`;
    $('close-export').onclick=()=>exportDialog.close();exportDialog.showModal();
  }catch(error){$('model-error').textContent=error.message;}finally{$('model-export').disabled=false;setBusy(false);}
};
function fitModelObject(){
  const object=modelObject();if(!object)return;
  const streams=model.frames?.length?model.frames.map(frame=>frame.vertices):[model.vertices];
  const min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity];
  for(const vertices of streams)for(let index=object.vertex_start;index<object.vertex_start+object.vertex_count;index++)for(let axis=0;axis<3;axis++){min[axis]=Math.min(min[axis],vertices[index][axis]);max[axis]=Math.max(max[axis],vertices[index][axis]);}
  modelView.center=object.vertex_count?min.map((v,i)=>(v+max[i])/2):[0,0,0];modelView.radius=object.vertex_count?Math.max(1,Math.hypot(...max.map((v,i)=>v-min[i]))/2):1;modelView.zoom=1;
  $('model-counts').textContent=`${object.vertex_count} vertices · ${object.triangle_count} triangles`;
  drawModel();
}
$('model-object').onchange=fitModelObject;
function drawModel(){
  const rect=modelCanvas.getBoundingClientRect(),w=rect.width,h=rect.height,dpr=window.devicePixelRatio||1;if(!w||!h)return;
  modelCanvas.width=Math.round(w*dpr);modelCanvas.height=Math.round(h*dpr);modelContext.setTransform(dpr,0,0,dpr,0,0);modelContext.clearRect(0,0,w,h);
  const object=modelObject();if(!object)return;
  const c=Math.cos(modelView.yaw),s=Math.sin(modelView.yaw),cp=Math.cos(modelView.pitch),sp=Math.sin(modelView.pitch),distance=modelView.radius*4/modelView.zoom,f=Math.min(w,h)*1.3;
  const projectedModel=frameVertices().map(v=>{
    // PSX local +Y points down. Match pinned LegaiaRE d6e64c68 scene_gltf's
    // diag(1,-1,1) display conversion without changing the decoded vertices.
    const x=v[0]-modelView.center[0],y=-(v[1]-modelView.center[1]),z=v[2]-modelView.center[2];const rx=x*c+z*s,rz=-x*s+z*c,ry=y*cp-rz*sp,depth=y*sp+rz*cp+distance;
    return depth>modelView.radius*.02?{x:w/2+rx*f/depth,y:h/2-ry*f/depth,z:depth}:null;
  });
  const faces=[];
  for(let i=object.triangle_start;i<object.triangle_start+object.triangle_count;i++){
    const triangle=model.triangles[i];if(!triangle)continue;const points=triangle.map(index=>projectedModel[index]);if(points.some(p=>!p))continue;
    const colors=model.triangle_colors?.[i];let rgb=[153,187,167];
    if(Array.isArray(colors)&&colors.length){rgb=Array.isArray(colors[0])?[0,1,2].map(axis=>Math.round(colors.reduce((sum,color)=>sum+(Number(color[axis])||0),0)/colors.length)):colors.slice(0,3);}
    faces.push({points,z:points.reduce((sum,p)=>sum+p.z,0)/3,color:`rgb(${rgb.map(value=>Math.max(0,Math.min(255,value))).join(',')})`,texture:modelTextures.get(model.triangle_materials?.[i]),uvs:model.triangle_uvs?.[i]});
  }
  faces.sort((a,b)=>b.z-a.z);
  for(const face of faces){modelContext.beginPath();modelContext.moveTo(face.points[0].x,face.points[0].y);for(const p of face.points.slice(1))modelContext.lineTo(p.x,p.y);modelContext.closePath();if(!drawTexturedFace(face)){modelContext.fillStyle=face.color;modelContext.fill();}modelContext.strokeStyle='#10201825';modelContext.lineWidth=.35;modelContext.stroke();}
  if(!faces.length){modelContext.fillStyle='#819b94';modelContext.font='13px "Segoe UI",sans-serif';modelContext.textAlign='center';modelContext.fillText('This object has no supported drawable triangles.',w/2,h/2);modelContext.textAlign='left';}
}
function drawTexturedFace(face){
  if(!face.texture || !face.uvs)return false;
  const uv=face.uvs.map(p=>[p[0]-face.texture.origin[0]+.5,p[1]-face.texture.origin[1]+.5]),p=face.points;
  const [u0,v0]=uv[0],[u1,v1]=uv[1],[u2,v2]=uv[2];
  const determinant=u0*(v1-v2)+u1*(v2-v0)+u2*(v0-v1);if(Math.abs(determinant)<1e-8)return false;
  const solve=axis=>[(p[0][axis]*(v1-v2)+p[1][axis]*(v2-v0)+p[2][axis]*(v0-v1))/determinant,(p[0][axis]*(u2-u1)+p[1][axis]*(u0-u2)+p[2][axis]*(u1-u0))/determinant,(p[0][axis]*(u1*v2-u2*v1)+p[1][axis]*(u2*v0-u0*v2)+p[2][axis]*(u0*v1-u1*v0))/determinant];
  const x=solve('x'),y=solve('y');modelContext.save();modelContext.clip();modelContext.transform(x[0],y[0],x[1],y[1],x[2],y[2]);modelContext.imageSmoothingEnabled=false;modelContext.drawImage(face.texture.image,0,0);modelContext.restore();return true;
}
new ResizeObserver(drawModel).observe(modelCanvas);
modelCanvas.addEventListener('pointerdown',event=>{modelCanvas.setPointerCapture(event.pointerId);modelDrag={x:event.clientX,y:event.clientY};});
modelCanvas.addEventListener('pointermove',event=>{if(!modelDrag)return;modelView.yaw+=(event.clientX-modelDrag.x)*.009;modelView.pitch+=(event.clientY-modelDrag.y)*.009;modelDrag={x:event.clientX,y:event.clientY};drawModel();});
for(const event of ['pointerup','pointercancel'])modelCanvas.addEventListener(event,()=>{modelDrag=null;});
modelCanvas.addEventListener('wheel',event=>{event.preventDefault();modelView.zoom=Math.max(.15,Math.min(2.5,modelView.zoom*Math.exp(-event.deltaY*.001)));drawModel();},{passive:false});
api('/api/state');
