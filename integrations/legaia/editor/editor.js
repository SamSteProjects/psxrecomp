const $ = (id) => document.getElementById(id);
const escapeHTML = (value) => String(value ?? '').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const numeric = (value) => typeof value === 'number' && Number.isFinite(value);
const format = (value) => numeric(value) ? String(Math.round(value * 1000) / 1000) : 'Unknown';
let state = {project:{}, scene:null, assets:[], selection:{}, history:{}, capabilities:{}};
let busy = false, toastTimer, lastSceneId, grid = true;
const canvas = $('viewport'), ctx = canvas.getContext('2d');
const camera = {yaw:-0.65,pitch:0.66,distance:2000,target:{x:0,y:0,z:0}};
let width=1, height=1, projected=[], handles=[], drag=null, draft=null;
const sceneSelect=document.createElement('select');sceneSelect.className='scene-selector';sceneSelect.setAttribute('aria-label','Active scene');$('viewport-title').after(sceneSelect);
sceneSelect.onchange=()=>api('/api/scene',{scene_id:sceneSelect.value});
const runtimeBox=document.createElement('div');runtimeBox.className='runtime-status';$('inspector').before(runtimeBox);
const buildButton=document.createElement('button');buildButton.id='build-button';buildButton.textContent='Build';buildButton.title='Build a private mod package from supported authored placements';$('save-button').after(buildButton);
const buildDialog=document.createElement('dialog');buildDialog.className='project-dialog';document.body.append(buildDialog);
const runButton=document.createElement('button');runButton.id='run-button';runButton.textContent='Build & Run';runButton.className='accent';buildButton.after(runButton);
const runDialog=document.createElement('dialog');runDialog.id='run-dialog';document.body.append(runDialog);
const runRibbon=document.createElement('div');runRibbon.className='run-ribbon';runRibbon.hidden=true;document.querySelector('.viewport-toolbar').after(runRibbon);
let runPoll=null, runRibbonKey=null;
runButton.onclick=()=>showRunDialog();
function showRunDialog(){
  const config=state.launch_config ?? {};
  runDialog.innerHTML=`<form id="run-form"><div class="dialog-heading"><h2>Build & Run</h2><button type="button" id="close-run" aria-label="Close">×</button></div><p>Launch a private copy of your selected runtime with this project's authored placement package.</p><label>Runtime executable<input id="run-exe" required value="${escapeHTML(config.runtime_executable)}" placeholder="C:\\path\\to\\LegaiaRecomp.exe" spellcheck="false"></label><label>BIOS image<input id="run-bios" required value="${escapeHTML(config.bios)}" placeholder="C:\\path\\to\\SCPH1001.BIN" spellcheck="false"></label><label>Game configuration<input id="run-config" required value="${escapeHTML(config.game_config)}" placeholder="C:\\path\\to\\game.toml" spellcheck="false"></label><label>Renderer<select id="run-renderer"><option value="software">Software</option><option value="opengl">OpenGL</option><option value="vulkan">Vulkan (requires runtime support)</option></select></label><label>Runtime debug port<input id="run-port" required type="number" min="1024" max="65535" value="${escapeHTML(config.debug_port ?? 4391)}"></label><p class="field-note">Each run has private mods, saves and logs under the project. Readiness verifies the game and enabled package; it does not establish gameplay correctness.</p><div id="run-summary"></div><div class="dialog-actions"><button type="submit" class="accent" id="launch-run">Build & launch</button></div><p class="dialog-error" role="alert"></p></form>`;
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
    buildDialog.innerHTML=`<div class="dialog-heading"><h2>Private mod package built</h2><button id="close-build" aria-label="Close">×</button></div><p>${escapeHTML(result.changed_fields)} placement fields · ${escapeHTML(result.overlay_count)} scene overlays</p><p>Runtime launch has not been validated for this package.</p><label>Package path<input readonly value="${escapeHTML(result.path)}"></label><p>${escapeHTML(result.install_instruction)}</p>`;
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
function position(entity){const p=entity.components?.Transform?.effective?.position ?? entity.components?.Transform?.imported?.position ?? {}; return {x:numeric(p.x)?p.x:0,y:numeric(p.y)?p.y:0,z:numeric(p.z)?p.z:0};}
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
  document.querySelector('.preview-badge span').textContent=live?'Authored scene reference · Live samples in Inspector':'Markers · models inspected separately';
  $('frame-selected').disabled=!selected();
  $('status').textContent=state.scene?.id ? `${state.scene.name} · ${entities().length} entities · ${state.project?.dirty?'Changes not saved':'Project ready'}` : 'Ready · Create or open a project to begin';
  renderHierarchy();renderAssets();renderInspector();
  renderRunStatus();scheduleRunPoll();
  if(lastSceneId!==state.scene?.id){lastSceneId=state.scene?.id;frame();}else draw();
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
function renderInspector(){
  const entity=selected();
  $('selection-summary').textContent=entity?entity.name ?? entity.id:'No entity selected';
  if(!entity){$('inspector').innerHTML='<div class="empty-panel">Select an entity in the scene<br>or hierarchy to inspect it.</div>';return;}
  const components=entity.components ?? {}, transform=components.Transform ?? {}, original=transform.imported?.position ?? {}, override=transform.authored?.position ?? {}, effective=transform.effective?.position ?? original;
  let html=`<div class="entity-heading"><h2>${escapeHTML(entity.name ?? entity.id)}</h2><code>${escapeHTML(entity.id)}</code></div><section class="component"><h3>Transform <small>Scene units</small></h3><div class="transform-table"><span></span><span class="column-title">Imported</span><span class="column-title">Authored</span><span class="column-title">Effective</span>`;
  for(const axis of ['x','y','z'])html+=`<span class="axis-${axis}">${axis.toUpperCase()}</span><output title="${format(original[axis])}">${format(original[axis])}</output><input data-axis="${axis}" aria-label="Authored ${axis.toUpperCase()}" type="number" step="1" placeholder="—" value="${numeric(override[axis])?override[axis]:''}" ${canEdit()?'':'disabled'}><output class="effective">${format(effective[axis])}</output>`;
  html+='</div><p class="field-note">Edits are project overrides. Empty authored fields inherit the imported value. Unknown heights appear at zero in this preview.</p></section>';
  if(components.ModelRenderer){const model=components.ModelRenderer;html+=`<section class="component"><h3>Model renderer <small>Imported reference</small></h3>${property('Asset',model.asset_id)}${property('Resolution',model.resolution_status)}<p class="field-note">The scene uses placement markers. Inspect decoded objects separately, without assuming a skeleton or pose.</p>${model.asset_id?'<button id="inspect-model" class="model-preview-button">Inspect model objects</button>':''}</section>`;}
  if(components.Animation)html+=`<section class="component"><h3>Animation</h3>${property('Imported ID',components.Animation.imported_id)}<p class="field-note">An association is not a verified playable animation.</p></section>`;
  if(components.RuntimeCorrelation){const correlation=components.RuntimeCorrelation;html+=`<section class="component"><h3>Runtime observation <small>Read only · sampled</small></h3>${property('Correlation',correlation.status ?? correlation.state ?? 'Unresolved')}<p class="field-note">Candidate associations preserve ambiguity. They do not replace imported or authored values.</p><details><summary>Epoch, candidates and evidence</summary><pre>${escapeHTML(JSON.stringify(correlation,null,2))}</pre></details></section>`;}
  if(components.RetailMetadata){const retail=components.RetailMetadata,source=retail.source_record;const summary=source&&typeof source==='object'?(source.prot_entry_name ?? source.scene ?? source.kind ?? 'Imported record'):source;html+=`<section class="component"><h3>Retail metadata <small>Read only</small></h3>${property('Source',summary)}<details><summary>Source, evidence and unresolved fields</summary><pre>${escapeHTML(JSON.stringify({source_record:source,claims:retail.claims,unresolved:retail.unresolved},null,2))}</pre></details></section>`;}
  $('inspector').innerHTML=html;
  if($('inspect-model'))$('inspect-model').onclick=()=>openModel(components.ModelRenderer.asset_id);
  $('inspector').querySelectorAll('[data-axis]').forEach(input=>input.addEventListener('change',async()=>{
    const axis=input.dataset.axis;
    if(input.value===''){await api('/api/command',{type:'clear_transform',entity_id:entity.id,axes:[axis]});return;}
    const value=Number(input.value);if(!Number.isFinite(value)){notify('Transform values must be finite numbers.',true);renderInspector();return;}
    await api('/api/command',{type:'set_transform',entity_id:entity.id,position:{[axis]:value}});
  }));
}

function frame(entity){
  const points=entity?[position(entity)]:entities().map(position);
  if(!points.length){camera.target={x:0,y:0,z:0};camera.distance=2000;draw();return;}
  const min={x:Infinity,y:Infinity,z:Infinity},max={x:-Infinity,y:-Infinity,z:-Infinity};
  for(const p of points)for(const axis of ['x','y','z']){min[axis]=Math.min(min[axis],p[axis]);max[axis]=Math.max(max[axis],p[axis]);}
  for(const axis of ['x','y','z'])camera.target[axis]=(min[axis]+max[axis])/2;
  camera.distance=entity?Math.max(100,camera.distance*.35):Math.max(200,Math.hypot(max.x-min.x,max.y-min.y,max.z-min.z)*1.3);
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
  if(grid){const spacing=10**Math.floor(Math.log10(camera.distance/7)),half=spacing*12,cx=Math.round(camera.target.x/spacing)*spacing,cz=Math.round(camera.target.z/spacing)*spacing;for(let i=-12;i<=12;i++){line({x:cx+i*spacing,y:0,z:cz-half},{x:cx+i*spacing,y:0,z:cz+half},i===0?'#39504f88':'#33474c66');line({x:cx-half,y:0,z:cz+i*spacing},{x:cx+half,y:0,z:cz+i*spacing},i===0?'#39504f88':'#33474c66');}}
  const items=entities().map(entity=>{const world=draft?.id===entity.id?draft.position:position(entity);return {entity,world,p:project(world)};}).filter(item=>item.p).sort((a,b)=>b.p.depth-a.p.depth);
  for(const {entity,world,p} of items){const active=entity.id===state.selection?.entity_id,radius=active?7:4.5;projected.push({id:entity.id,x:p.x,y:p.y});ctx.beginPath();ctx.ellipse(p.x,p.y+5,active?12:7,active?4:2.5,0,0,Math.PI*2);ctx.fillStyle='#02090966';ctx.fill();ctx.beginPath();ctx.moveTo(p.x,p.y-radius);ctx.lineTo(p.x+radius,p.y);ctx.lineTo(p.x,p.y+radius);ctx.lineTo(p.x-radius,p.y);ctx.closePath();ctx.fillStyle=active?'#c9edce':authored(entity)?'#d2ae70':'#759d8d';ctx.fill();ctx.strokeStyle=active?'#f1fff0':'#a8c6b6';ctx.lineWidth=active?1.5:1;ctx.stroke();if(active){ctx.font='11px "Segoe UI", sans-serif';ctx.fillStyle='#c8ddd1';ctx.fillText(entity.name ?? entity.id,p.x+12,p.y-10);if(canEdit()){const length=camera.distance*.085;for(const [axis,color] of [['x','#e0988a'],['z','#8bbbdc']]){const end={...world,[axis]:world[axis]+length},q=project(end);if(!q)continue;line(world,end,color,2);ctx.fillStyle=color;ctx.beginPath();ctx.arc(q.x,q.y,4,0,Math.PI*2);ctx.fill();ctx.font='bold 10px "Segoe UI", sans-serif';ctx.fillText(axis.toUpperCase(),q.x+7,q.y+3);handles.push({axis,x:q.x,y:q.y,start:p});}}}}
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
    else if(drag.type==='orbit'){camera.yaw-=dx*.006;camera.pitch=Math.max(.12,Math.min(1.42,camera.pitch+dy*.005));}
    else {const b=basis(),scale=camera.distance/Math.max(1,Math.min(width,height)*.9);camera.target.x-=dx*scale*b.right.x;camera.target.z-=dx*scale*b.right.z;camera.target.x-=dy*scale*Math.sin(camera.yaw)/Math.max(.15,Math.sin(camera.pitch));camera.target.z-=dy*scale*Math.cos(camera.yaw)/Math.max(.15,Math.sin(camera.pitch));}
    draw();
  }
  drag.last=p;
});
canvas.addEventListener('pointerup',async event=>{
  if(!drag)return;const finished=drag,p=pointer(event),edit=draft;drag=null;draft=null;canvas.classList.remove('dragging');
  if(finished.type==='transform' && edit){const axis=finished.handle.axis;if(edit.position[axis]!==finished.original[axis])await api('/api/command',{type:'set_transform',entity_id:finished.entity,position:{[axis]:edit.position[axis]}});}
  else if(!finished.moved && event.button===0){const hit=[...projected].reverse().find(item=>Math.hypot(item.x-p.x,item.y-p.y)<12);if(hit)await api('/api/selection',{entity_id:hit.id});}
  draw();
});
canvas.addEventListener('pointercancel',()=>{drag=null;draft=null;canvas.classList.remove('dragging');draw();});
canvas.addEventListener('wheel',event=>{event.preventDefault();camera.distance=Math.max(20,Math.min(1e8,camera.distance*Math.exp(event.deltaY*.001)));draw();},{passive:false});

// Object previews deliberately do not assemble multipart assets into an invented pose.
const modelCanvas=$('model-canvas'), modelContext=modelCanvas.getContext('2d');
let model=null, modelDrag=null, modelRequest=0;
let modelTextures=new Map();
const modelView={yaw:.55,pitch:-.18,zoom:1,center:[0,0,0],radius:1};
async function openModel(assetId){
  if(busy)return;setBusy(true);const request=++modelRequest;
  try{
    const response=await fetch('/api/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:assetId})});
    const data=await response.json();if(!response.ok||data.error)throw new Error(typeof data.error==='string'?data.error:JSON.stringify(data.error ?? data));
    if(!Array.isArray(data.vertices)||!Array.isArray(data.triangles)||!Array.isArray(data.objects))throw new Error('Model service returned no decoded geometry.');
    if(request!==modelRequest)return;
    model=data;$('model-dialog').querySelector('h2').textContent=assetId.split('/').slice(-2).join(' / ');
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
    $('model-description').textContent=`Drag to orbit · Scroll to zoom · Retail object-local geometry · Unposed · ${modelTextures.size?'Static texture address matches':'Vertex colors'} · No texture-window, animated palette or blend reconstruction`;
    $('model-object').replaceChildren();
    for(let index=0;index<model.objects.length;index++){const object=model.objects[index],option=document.createElement('option');option.value=index;option.textContent=`Object ${object.object_index ?? index} · ${object.triangle_count} triangles`;$('model-object').append(option);}
    $('model-diagnostics').textContent=(model.diagnostics ?? []).map(d=>typeof d==='string'?d:d.message ?? JSON.stringify(d)).join(' · ');
    if(!$('model-dialog').open)$('model-dialog').showModal();
    fitModelObject();
  }catch(error){notify(error.message,true);}finally{setBusy(false);}
}
function fitModelObject(){
  const object=model?.objects[Number($('model-object').value)];if(!object)return;
  const vertices=model.vertices.slice(object.vertex_start,object.vertex_start+object.vertex_count);
  const min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity];
  for(const vertex of vertices)for(let axis=0;axis<3;axis++){min[axis]=Math.min(min[axis],vertex[axis]);max[axis]=Math.max(max[axis],vertex[axis]);}
  modelView.center=vertices.length?min.map((v,i)=>(v+max[i])/2):[0,0,0];modelView.radius=vertices.length?Math.max(1,Math.hypot(...max.map((v,i)=>v-min[i]))/2):1;modelView.zoom=1;
  $('model-counts').textContent=`${object.vertex_count} vertices · ${object.triangle_count} triangles`;
  drawModel();
}
$('model-object').onchange=fitModelObject;
function drawModel(){
  const rect=modelCanvas.getBoundingClientRect(),w=rect.width,h=rect.height,dpr=window.devicePixelRatio||1;if(!w||!h)return;
  modelCanvas.width=Math.round(w*dpr);modelCanvas.height=Math.round(h*dpr);modelContext.setTransform(dpr,0,0,dpr,0,0);modelContext.clearRect(0,0,w,h);
  const object=model?.objects[Number($('model-object').value)];if(!object)return;
  const c=Math.cos(modelView.yaw),s=Math.sin(modelView.yaw),cp=Math.cos(modelView.pitch),sp=Math.sin(modelView.pitch),distance=modelView.radius*4/modelView.zoom,f=Math.min(w,h)*1.3;
  const projectedModel=model.vertices.map(v=>{
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
