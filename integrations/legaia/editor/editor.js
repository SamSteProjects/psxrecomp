const $ = (id) => document.getElementById(id);
const escapeHTML = (value) => String(value ?? '').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const numeric = (value) => typeof value === 'number' && Number.isFinite(value);
const format = (value) => numeric(value) ? String(Math.round(value * 1000) / 1000) : 'Unknown';
let state = {project:{}, scene:null, assets:[], selection:{}, history:{}, capabilities:{}};
let busy = false, toastTimer, lastSceneId, grid = true;
const canvas = $('viewport'), ctx = canvas.getContext('2d');
const transformTools=document.createElement('div');transformTools.className='transform-tools';
transformTools.innerHTML='<label><input id="transform-snap" type="checkbox"> Snap moves</label><label>Step <select id="transform-snap-step" aria-label="Transform snap step"><option value="16">16 units</option><option value="64" selected>64 units</option><option value="256">256 units</option><option value="1024">1024 units</option></select></label><span id="transform-drag-status" role="status">X/Z moves · snap aligns to scene origin</span>';
$('viewport-wrap').before(transformTools);
function snappedTransformCoordinate(value,step){return Math.round(value/(step||1))*(step||1);}
const camera = {yaw:-0.65,pitch:0.66,distance:2000,target:{x:0,y:0,z:0}};
let width=1, height=1, projected=[], handles=[], drag=null, draft=null;
let sceneRenderer=null,scenePreview=null,sceneProjectPath=null,sceneLoadedId=null,sceneKey=null,scenePendingKey=null,sceneFailedKey=null,sceneAbort=null,sceneError=null,modelsEnabled=true,cameraRevision=0;
const sceneLayers={actors:true,scenery:true,ground:true};
let showObservedNodes=false,runtimeNodeHits=[],pickRuntimeNodes=false;
const observedLayerButton=document.createElement('button');observedLayerButton.textContent='Runtime positions';observedLayerButton.setAttribute('aria-pressed','false');observedLayerButton.title='Alt-click a sampled marker to inspect it, including occluded nodes; not confirmed NPC identities';observedLayerButton.onclick=()=>{showObservedNodes=!showObservedNodes;observedLayerButton.setAttribute('aria-pressed',String(showObservedNodes));draw();};$('frame-selected').after(observedLayerButton);
const pickRuntimeButton=document.createElement('button');pickRuntimeButton.textContent='Pick runtime node';pickRuntimeButton.setAttribute('aria-pressed','false');pickRuntimeButton.onclick=()=>{pickRuntimeNodes=!pickRuntimeNodes;pickRuntimeButton.setAttribute('aria-pressed',String(pickRuntimeNodes));if(pickRuntimeNodes){showObservedNodes=true;observedLayerButton.setAttribute('aria-pressed','true');}draw();};$('frame-selected').after(pickRuntimeButton);
const nodesButton=document.createElement('button');nodesButton.textContent='Observed nodes';$('frame-selected').after(nodesButton);
const nodesDialog=document.createElement('dialog');nodesDialog.className='project-dialog observed-nodes-dialog';document.body.append(nodesDialog);
nodesButton.onclick=()=>renderObservedNodes();
function renderObservedNodes(query='',nodeIds=null){
  nodesDialog.replaceChildren();const heading=document.createElement('h2');heading.textContent='Observed runtime nodes';nodesDialog.append(heading);
  const note=document.createElement('p');note.textContent='Captured positions, independent of imported actor matching. Framing changes only the editor camera.';nodesDialog.append(note);
  const epoch=acceptedEpoch(state.runtime),correlation=state.runtime_correlation,context=JSON.stringify([state.project?.path,state.scene?.id]);
  const nodes=state.project?.mode==='live'&&epoch&&correlation?.available===true&&correlation.epoch_id===epoch?(correlation.runtime_nodes??[]).filter(node=>!nodeIds||nodeIds.includes(node.runtime_node_id)):[];
  const search=document.createElement('input');search.type='search';search.value=query;search.placeholder='Filter by node, coordinates, or candidate';search.setAttribute('aria-label','Filter observed nodes');nodesDialog.append(search);
  const list=document.createElement('div');list.className='observed-nodes-list';nodesDialog.append(list);
  const count=document.createElement('p');count.setAttribute('role','status');nodesDialog.append(count);
  const current=()=>state.project?.mode==='live'&&acceptedEpoch(state.runtime)===epoch&&JSON.stringify([state.project?.path,state.scene?.id])===context&&state.runtime_correlation?.available===true&&state.runtime_correlation.epoch_id===epoch;
  const rows=[];
  for(const node of nodes){
    const row=document.createElement('div'),label=document.createElement('p');const p=node.observed_position;label.textContent=`${node.runtime_node_id} | position frames ${node.position_capture_frames?.before??'unknown'}–${node.position_capture_frames?.after??'unknown'} | XYZ ${p?.x??'?'} / ${p?.y??'?'} / ${p?.z??'?'} | ${node.candidate_entity_ids?.length??0} candidate entities`;row.append(label);
    const button=document.createElement('button');button.textContent='Frame node';button.disabled=node.epoch_id!==epoch||!p||!['x','y','z'].every(a=>numeric(p[a]));
    button.onclick=()=>{if(state.project?.mode!=='live'||acceptedEpoch(state.runtime)!==epoch||JSON.stringify([state.project?.path,state.scene?.id])!==context||state.runtime_correlation?.available!==true||state.runtime_correlation.epoch_id!==epoch)return;coordinateProbe={point:{...p},epoch,context};cancelViewportGesture();camera.target=displayPosition(p);camera.distance=800;cameraRevision++;nodesDialog.close();draw();};row.append(button);list.append(row);rows.push({row,text:[node.runtime_node_id,p?.x,p?.y,p?.z,...(node.candidate_entity_ids??[])].join(' ').toLowerCase()});
    const details=document.createElement('details'),summary=document.createElement('summary');summary.textContent='Captured fields and evidence';details.append(summary);
    for(const field of node.decoded_fields??[]){
      const entry=document.createElement('p');const interpreted=field.interpreted_value;
      const value=interpreted===null||interpreted===undefined?'Unknown':typeof interpreted==='object'?JSON.stringify(interpreted):String(interpreted);
      entry.textContent=`${field.property}: ${value} | raw ${field.raw_numeric_value??'unknown'} | ${field.confidence??'unknown'} | applicability ${field.applicability??'unknown'}${field.unresolved?' | unresolved':''}`;
      const evidence=document.createElement('small');evidence.textContent=` ${field.notes??''} ${(field.evidence??[]).join(', ')}`;entry.append(evidence);details.append(entry);
    }
    row.append(details);
    for(const id of node.candidate_entity_ids??[]){
      const entity=entities().find(item=>item.id===id);if(!entity)continue;
      const inspect=document.createElement('button');inspect.textContent=`Inspect candidate ${entity.name??entity.label??id}`;inspect.title='Unconfirmed identity match; opens imported and observed values separately';
      inspect.onclick=async()=>{if(busy||!current())return;nodesDialog.close();await api('/api/selection',{entity_id:id});};row.append(inspect);
    }
  }
  const filter=()=>{const query=search.value.trim().toLowerCase();let shown=0;for(const item of rows){item.row.hidden=!item.text.includes(query);if(!item.row.hidden)shown++;}count.textContent=`${shown} of ${nodes.length} captured nodes`;};search.oninput=filter;filter();
  if(!nodes.length){const empty=document.createElement('p');empty.textContent='No accepted actor sample. Enter Live mode and Observe actors first.';nodesDialog.append(empty);}
  const refresh=document.createElement('button');refresh.textContent='Refresh captured list';refresh.onclick=()=>renderObservedNodes(search.value,nodeIds);nodesDialog.append(refresh);
  const close=document.createElement('button');close.textContent='Close';close.onclick=()=>nodesDialog.close();nodesDialog.append(close);if(!nodesDialog.open)nodesDialog.showModal();
};

let coordinateProbe=null;
const locateButton=document.createElement('button');locateButton.textContent='Locate coordinates';$('frame-selected').after(locateButton);
const locateDialog=document.createElement('dialog');locateDialog.className='project-dialog';locateDialog.innerHTML='<form><h2>Locate guest coordinates</h2><p>Place a reference marker using game coordinates. This changes only the editor camera.</p><label>X <input name="x" type="number" step="any" required></label><label>Y <input name="y" type="number" step="any" required value="0"></label><label>Z <input name="z" type="number" step="any" required></label><button type="submit">Locate</button><button type="button" data-clear>Clear marker</button><button type="button" data-close>Cancel</button></form>';document.body.append(locateDialog);
locateButton.onclick=()=>locateDialog.showModal();
locateDialog.querySelector('[data-close]').onclick=()=>locateDialog.close();
locateDialog.querySelector('[data-clear]').onclick=()=>{coordinateProbe=null;locateDialog.close();draw();};
locateDialog.querySelector('form').onsubmit=event=>{
  event.preventDefault();const point={};for(const axis of ['x','y','z']){const input=locateDialog.querySelector(`[name="${axis}"]`);point[axis]=Number(input.value);if(!input.value.trim()||!Number.isFinite(point[axis]))return;}
  coordinateProbe={point,context:JSON.stringify([state.project?.path,state.scene?.id])};cancelViewportGesture();camera.target=displayPosition(point);camera.distance=1000;cameraRevision++;locateDialog.close();draw();
};
function drawCoordinateProbe(){
  if(!coordinateProbe||coordinateProbe.context!==JSON.stringify([state.project?.path,state.scene?.id]))return;
  if(coordinateProbe.epoch&&(state.project?.mode!=='live'||acceptedEpoch(state.runtime)!==coordinateProbe.epoch||state.runtime_correlation?.available!==true||state.runtime_correlation.epoch_id!==coordinateProbe.epoch))return;
  const world=displayPosition(coordinateProbe.point),p=project(world);if(!p)return;
  ctx.save();ctx.strokeStyle='#ffda78';ctx.fillStyle='#ffda78';ctx.lineWidth=2;ctx.beginPath();ctx.arc(p.x,p.y,9,0,Math.PI*2);ctx.moveTo(p.x-15,p.y);ctx.lineTo(p.x+15,p.y);ctx.moveTo(p.x,p.y-15);ctx.lineTo(p.x,p.y+15);ctx.stroke();ctx.font='12px "Segoe UI",sans-serif';const v=coordinateProbe.point;ctx.fillText(`${coordinateProbe.epoch?'Captured node':'Reference'} X ${v.x} Y ${v.y} Z ${v.z}`,p.x+18,p.y-12);ctx.restore();
}

const frameSamplesButton=document.createElement('button');frameSamplesButton.textContent='Frame live samples';frameSamplesButton.disabled=true;frameSamplesButton.title='Frame all accepted-epoch candidates for the selected actor without changing authored placement';$('frame-selected').after(frameSamplesButton);
frameSamplesButton.onclick=()=>{
  const points=observedCandidatePoints();if(!points.length)return;
  cancelViewportGesture();
  const min={},max={};for(const axis of ['x','y','z']){min[axis]=Math.min(...points.map(p=>p[axis]));max[axis]=Math.max(...points.map(p=>p[axis]));camera.target[axis]=(min[axis]+max[axis])/2;}
  camera.distance=Math.max(800,Math.hypot(max.x-min.x,max.y-min.y,max.z-min.z)*1.5);cameraRevision++;draw();
};

function hiddenSceneEntities(){return new Set((activeScenePreview()?.entities??[]).filter(e=>!sceneLayers[e.kind!=='environment'?'actors':e.entity_id.endsWith('/ground')?'ground':'scenery']).map(e=>e.entity_id));}
for(const [layer,label] of Object.entries({actors:'Actors',scenery:'Scenery',ground:'Ground'})){
  const button=document.createElement('button');button.textContent=label;button.className='active';button.setAttribute('aria-pressed','true');button.title=`Show ${label.toLowerCase()} in the scene view`;
  button.onclick=()=>{sceneLayers[layer]=!sceneLayers[layer];button.classList.toggle('active',sceneLayers[layer]);button.setAttribute('aria-pressed',String(sceneLayers[layer]));cancelViewportGesture();draw();};
  $('frame-all').before(button);
}
const modelToggle=document.createElement('button');modelToggle.id='scene-model-toggle';modelToggle.textContent='Models';modelToggle.className='active';modelToggle.setAttribute('aria-pressed','true');modelToggle.hidden=true;$('frame-all').before(modelToggle);
modelToggle.onclick=()=>{if(sceneError){sceneFailedKey=null;sceneKey=null;scenePreview=null;sceneError=null;modelsEnabled=true;}else modelsEnabled=!modelsEnabled;modelToggle.classList.toggle('active',modelsEnabled);modelToggle.setAttribute('aria-pressed',modelsEnabled);refreshScenePreview();draw();};
const sceneSelect=document.createElement('select');sceneSelect.className='scene-selector';sceneSelect.setAttribute('aria-label','Active scene');$('viewport-title').after(sceneSelect);
sceneSelect.onchange=()=>api('/api/scene',{scene_id:sceneSelect.value});
const runtimeBox=document.createElement('div');runtimeBox.className='runtime-status';$('inspector').before(runtimeBox);
const liveFollow={active:false,timer:null,pending:null,controller:null,generation:0,context:null,epoch:null,count:0,reason:'Not following',runPid:null};
const liveContext=()=>JSON.stringify([state.project?.path,state.scene?.id]);
const acceptedEpoch=runtime=>{const value=runtime?.available&&runtime.observation?.epoch?.epoch_id;return typeof value==='string'&&value?value:null;};
runtimeBox.innerHTML='<span id="runtime-message"></span><div class="runtime-actions"><button id="runtime-check">Check runtime</button><button id="runtime-observe">Observe actors</button><button id="runtime-follow" aria-pressed="false">Follow live</button></div><p id="runtime-follow-status" role="status"></p>';
$('runtime-check').onclick=()=>api('/api/runtime/discover',{});$('runtime-observe').onclick=()=>api('/api/runtime/observe',{include_actors:true});
$('runtime-follow').onclick=()=>liveFollow.active?stopLiveFollow('Stopped by you'):startLiveFollow();
function renderRuntimeControls(){
  runtimeBox.hidden=!state.capabilities?.runtime_discovery;
  $('runtime-message').textContent=state.runtime?.available?'Runtime connected · read-only observation':state.runtime?.reason?.message ?? 'Runtime has not been checked';
  $('runtime-check').disabled=busy||liveFollow.active;$('runtime-observe').hidden=!state.runtime?.available;$('runtime-observe').disabled=busy||liveFollow.active;
  const live=state.project?.mode==='live',button=$('runtime-follow');button.textContent=liveFollow.active?'Stop following':'Follow live';button.setAttribute('aria-pressed',liveFollow.active);button.classList.toggle('active',liveFollow.active);
  button.disabled=!liveFollow.active&&(busy||!!liveFollow.pending||!live||!state.runtime?.available||document.hidden);button.title=live?'Capture actors every 2 seconds after the previous response; stop on guard failure':'Enter Live mode after a guarded runtime observation';
  $('runtime-follow-status').textContent=liveFollow.active?`Following · ${liveFollow.pending?'Capturing…':busy?'Waiting for the current action':`${liveFollow.count} actor samples · next capture in 2 seconds`}`:`Stopped · ${liveFollow.reason}`;
}
function cancelFollowTimer(){clearTimeout(liveFollow.timer);liveFollow.timer=null;}
function stopLiveFollow(reason){
  liveFollow.active=false;liveFollow.generation++;cancelFollowTimer();liveFollow.controller?.abort();liveFollow.epoch=null;liveFollow.context=null;liveFollow.runPid=null;liveFollow.reason=reason;renderRuntimeControls();
}
function reconcileLiveFollow(){
  if(!liveFollow.active)return;
  if(document.hidden)stopLiveFollow('Page hidden; start again when ready');
  else if(state.project?.mode!=='live')stopLiveFollow('Edit mode');
  else if(liveFollow.context!==liveContext())stopLiveFollow('Project or scene changed');
  else if(!state.runtime?.available)stopLiveFollow(state.runtime?.reason?.message ?? 'Runtime observation unavailable');
}
function scheduleLiveFollow(){
  cancelFollowTimer();if(!liveFollow.active||busy||liveFollow.pending||document.hidden)return;
  liveFollow.timer=setTimeout(()=>{liveFollow.timer=null;captureLiveFollow();},2000);
}
function startLiveFollow(){
  if(busy||liveFollow.pending||document.hidden||state.project?.mode!=='live'||!state.runtime?.available)return;
  liveFollow.active=true;liveFollow.generation++;liveFollow.context=liveContext();liveFollow.epoch=null;liveFollow.count=0;liveFollow.reason='';liveFollow.runPid=state.run?.running?state.run.pid:null;captureLiveFollow();
}
function clearDisplayedLive(reason){
  state.capabilities.live_mode=false;$('live-mode').disabled=true;$('live-mode').title=reason;
  state.runtime={...state.runtime,available:false,state:'unavailable',observation:null,actor_bindings:null,reason:{message:reason},historical_observation:true};
  state.runtime_correlation={available:false,status:'unavailable',reason,entities:{}};
  for(const entity of entities())if(entity.components?.RuntimeCorrelation)entity.components.RuntimeCorrelation={status:'unavailable',binding_confirmed:false,candidates:[],reason};
}
function captureLiveFollow(){
  if(!liveFollow.active||busy||liveFollow.pending||document.hidden){scheduleLiveFollow();return;}
  const generation=liveFollow.generation,context=liveFollow.context,controller=new AbortController(),epoch=liveFollow.epoch;
  liveFollow.controller=controller;const timeout=setTimeout(()=>controller.abort(),15000);
  const current=()=>generation===liveFollow.generation&&liveFollow.active&&context===liveContext()&&!document.hidden;
  const task=(async()=>{
    try{
      const response=await fetch('/api/runtime/observe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({include_actors:true,...(epoch?{expected_epoch_id:epoch}:{})}),signal:controller.signal});
      const data=await response.json();if(!current())return;
      if(!response.ok||data.error){
        const reason=typeof data.error==='string'?data.error:'Runtime guard rejected the capture';
        // Read authoritative cleared state once; this does not reconnect or capture.
        try{const refresh=await fetch('/api/state',{signal:controller.signal}),fresh=await refresh.json();if(current()&&refresh.ok&&fresh.project&&'scene' in fresh&&JSON.stringify([fresh.project.path,fresh.scene?.id])===context){state=fresh;}}
        catch{}
        if(!current())return;clearDisplayedLive(reason);stopLiveFollow(reason);render();return;
      }
      if(!data.project||!('scene' in data)||JSON.stringify([data.project.path,data.scene?.id])!==context)throw new Error('Project or scene changed during capture');
      if(!data.runtime?.available){state=data;stopLiveFollow(data.runtime?.reason?.message ?? 'Runtime observation unavailable');render();return;}
      const nextEpoch=acceptedEpoch(data.runtime);if(!nextEpoch)throw new Error('Capture did not return an accepted observation epoch');
      liveFollow.epoch=nextEpoch;liveFollow.count++;state=data;render();
    }catch(error){if(current()){const reason=error.name==='AbortError'?'Runtime capture timed out':`Runtime capture failed: ${error.message}`;clearDisplayedLive(reason);stopLiveFollow(reason);render();}}
    finally{clearTimeout(timeout);}
  })();
  liveFollow.pending=task;renderRuntimeControls();
  void task.finally(()=>{if(liveFollow.pending===task){liveFollow.pending=null;liveFollow.controller=null;renderRuntimeControls();scheduleLiveFollow();}});
}
document.addEventListener('visibilitychange',()=>{if(document.hidden&&liveFollow.active)stopLiveFollow('Page hidden; start again when ready');else renderRuntimeControls();});
window.addEventListener('pagehide',()=>{if(liveFollow.active)stopLiveFollow('Page closed');});

const buildButton=document.createElement('button');buildButton.id='build-button';buildButton.textContent='Build';buildButton.title='Build the project with supported edits or as a verified retail baseline';$('save-button').after(buildButton);
const buildDialog=document.createElement('dialog');buildDialog.className='project-dialog';buildDialog.id='build-report-dialog';document.body.append(buildDialog);
const buildReportButton=document.createElement('button');buildReportButton.id='build-report-button';buildReportButton.textContent='Build report';buildReportButton.title='Review the latest build';buildReportButton.hidden=true;buildButton.after(buildReportButton);buildReportButton.onclick=()=>showBuildReport();
const templateDialog=document.createElement('dialog');templateDialog.id='template-dialog';document.body.append(templateDialog);
const templateButton=document.createElement('button');templateButton.className='template-library-button';templateButton.textContent='Authored actor templates…';$('assets').before(templateButton);
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
  if(liveFollow.active&&liveFollow.runPid&&run?.pid===liveFollow.runPid&&!active){clearDisplayedLive('Owned runtime stopped');stopLiveFollow('Owned runtime stopped');renderInspector();draw();}
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
buildButton.onclick=async()=>{if(await api('/api/build',{}))showBuildReport();};
const placementIssuesButton=document.createElement('button');placementIssuesButton.hidden=true;buildButton.after(placementIssuesButton);
const placementIssuesDialog=document.createElement('dialog');document.body.append(placementIssuesDialog);
placementIssuesButton.onclick=()=>{
  placementIssuesDialog.innerHTML='<div class="dialog-heading"><h2>Placement build issues</h2><button aria-label="Close placement issues">Close</button></div><p>These checks cover authored coordinates across imported scenes. Build still verifies all source data and other authored changes.</p>';
  placementIssuesDialog.querySelector('button').onclick=()=>placementIssuesDialog.close();
  for(const item of state.placement_build_issues ?? []){
    const section=document.createElement('section'),button=document.createElement('button');
    button.textContent=`${item.scene_name}: ${item.entity_id}`;
    button.onclick=async()=>{if(busy)return;placementIssuesDialog.close();if(item.scene_id!==state.scene?.id&&!await api('/api/scene',{scene_id:item.scene_id}))return;if(await api('/api/selection',{entity_id:item.entity_id}))frame(selected());};
    section.append(button);for(const issue of item.issues){const p=document.createElement('p');p.textContent=issue;section.append(p);}placementIssuesDialog.append(section);
  }
  placementIssuesDialog.showModal();
};
function renderBuildStatus(){
  const issueCount=(state.placement_build_issues ?? []).length;
  placementIssuesButton.hidden=!issueCount;placementIssuesButton.disabled=busy;
  placementIssuesButton.textContent=`Placement issues (${issueCount} ${issueCount===1?'actor':'actors'})`;
  buildReportButton.hidden=!state.build;buildReportButton.disabled=busy||!state.build;
  buildReportButton.textContent=state.build?.current===false?'Build report · stale':'Build report';
  buildReportButton.classList.toggle('stale',state.build?.current===false);
  if(buildDialog.open)renderBuildReport();
}
function validBuildReport(report){
  return report?.schema_version==='legaia.build-report.v1'&&Array.isArray(report.changes)&&report.changes.length<=65536&&report.changes.every(change=>change&&typeof change==='object'&&['scene','asset_id','field','scope'].every(key=>typeof change[key]==='string')&&'before' in change&&'after' in change)&&['overlay_bytes','scene_count','change_count'].every(key=>Number.isSafeInteger(report[key])&&report[key]>=0)&&report.validation&&typeof report.validation==='object'&&!Array.isArray(report.validation)&&Object.keys(report.validation).length<=64;
}
function projectSaveStatus(){
  if(!state.project?.dirty)return 'Project saved';
  const sections=state.project.unsaved_sections;
  return Array.isArray(sections)&&sections.length?`Unsaved: ${sections.join(', ')}`:'Project changes are not saved';
}
function buildValue(value){return typeof value==='string'?value:JSON.stringify(value) ?? 'Unknown';}
function buildChangeResource(change){
  if(typeof change.owner_id!=='string')return null;
  return assetRecords().find(record=>['texture','script'].includes(record.type)&&
    record.authoredRecord?.id===change.owner_id) ?? null;
}
async function openBuildChange(change){
  if(busy)return;
  const scene=(state.scenes ?? []).find(item=>item.name===change.scene);
  if(!scene){notify('The source scene is no longer imported.',true);return;}
  const owner=change.owner_id,resource=buildChangeResource(change);
  buildDialog.close();
  if(scene.id!==state.scene?.id&&!await api('/api/scene',{scene_id:scene.id}))return;
  if(resource?.type==='texture'){await openTexture(resource);return;}
  if(resource?.type==='script'){
    await openActorScript({id:resource.authoredRecord.id,name:resource.label,partitionTwo:true},false,change.asset_id);
    return;
  }
  if(!await api('/api/selection',{entity_id:owner}))return;
  frame(selected());
  document.querySelector('.workspace-tabs [data-panel="viewport"]').click();
  if(change.field==='dialogue.text'||change.scope==='encoded-transition-entry-only')await openActorScript(selected(),false,change.asset_id);
}
function renderBuildReport(){
  const result=state.build;
  if(!result){buildDialog.innerHTML='<div class="dialog-heading"><h2>Build report unavailable</h2><button id="close-build" aria-label="Close build report">×</button></div><p>No build report is retained for this project.</p>';$('close-build').onclick=()=>buildDialog.close();return;}
  const report=result.report,valid=validBuildReport(report),current=result.current;
  const freshness=current===true?'Matches current authored state':current===false?'Authored state changed · rebuild to include current edits':'Freshness unavailable · rebuild to compare with the current project';
  buildDialog.innerHTML=`<div class="dialog-heading"><h2>${result.build_kind==='retail'?'Retail baseline build report':'Authored build report'}</h2><button id="close-build" aria-label="Close build report">×</button></div><p class="build-freshness ${current===true?'current':'stale'}">${freshness}</p><p>${result.build_kind==='retail'?'Retail baseline · no modified bytes':'Private authored mod package'}</p>${valid?`<div class="build-report-counts">${property('Changed fields',report.change_count)}${property('Scenes',report.scene_count)}${property('Overlay bytes',report.overlay_bytes.toLocaleString())}</div><section><h3>Package changes</h3><div id="build-changes"></div></section><section><h3>Build validation</h3><div id="build-validation"></div></section>`:'<p class="script-warning">A supported detailed report is unavailable. Build again with this service to review the changes and validation.</p>'}<p class="build-runtime-note">This report covers build validation. The authored-state match does not recheck package or disc integrity. Runtime execution and gameplay behavior are not verified here.</p><details class="resource-provenance"><summary>Package paths, hashes and build identity</summary><pre class="diagnostic-detail"></pre></details>`;
  $('close-build').onclick=()=>buildDialog.close();
  if(valid){
    const changes=$('build-changes');
    if(!report.changes.length){const empty=document.createElement('p');empty.className='field-note';empty.textContent=result.build_kind==='retail'?'No modified bytes: this package is the verified retail baseline.':'No field changes were listed in the build report.';changes.append(empty);}
    else{
      const wrap=document.createElement('div');wrap.className='script-table-wrap build-changes-table';const table=document.createElement('table');table.innerHTML='<thead><tr><th>Scene / asset</th><th>Field</th><th>Before</th><th>After</th><th>Scope</th></tr></thead><tbody></tbody>';
      for(const change of report.changes){const row=document.createElement('tr');for(const [index,value] of [`${change.scene}\n${change.asset_id}`,change.field,buildValue(change.before),buildValue(change.after),change.scope+(Number.isInteger(change.affected_grid_cell_count)?` · ${change.affected_grid_cell_count} grid cells`:'')].entries()){const cell=document.createElement('td');if(index===2||index===3){const text=document.createElement('pre');text.textContent=value;cell.append(text);}else if(index===0&&typeof change.owner_id==='string'&&(change.owner_id.includes('/actors/man-p1/')||buildChangeResource(change))){const link=document.createElement('button');link.type='button';link.textContent=value;link.title='Open authored source';link.onclick=()=>openBuildChange(change);cell.append(link);}else cell.textContent=value;row.append(cell);}table.querySelector('tbody').append(row);}wrap.append(table);changes.append(wrap);
    }
    const labels={retail_provenance:'Retail provenance',unchanged_opaque_bytes:'Unchanged opaque bytes',lz_decode_round_trip:'LZS round trip',live_runtime:'Runtime test'},values={fresh_import_match:'Fresh import matched',not_required_no_MAN_overlay:'Not required · no compressed MAN changes',not_required_unmodified_disc:'Not required · unmodified disc',not_run:'Not run'};
    for(const [key,value] of Object.entries(report.validation)){const item=document.createElement('div');item.className='build-validation-row';const label=document.createElement('span');label.textContent=labels[key] ?? key.replaceAll('_',' ');const outcome=document.createElement('strong');outcome.textContent=value===true?'Passed':value===false?'Failed':values[value] ?? buildValue(value);outcome.classList.toggle('failed',value===false);item.append(label,outcome);$('build-validation').append(item);}
  }
  const {report:details,...metadata}=result;buildDialog.querySelector('pre.diagnostic-detail').textContent=JSON.stringify(metadata,null,2);
}
function showBuildReport(){renderBuildReport();if(!buildDialog.open)buildDialog.showModal();}

document.querySelectorAll('[data-panel]').forEach(button=>{if(button.tagName==='BUTTON')button.onclick=()=>{document.querySelector('.workspace').dataset.panel=button.dataset.panel;document.querySelectorAll('.workspace-tabs button').forEach(tab=>tab.classList.toggle('active',tab===button));resize();};});

function notify(message, error=false) {
  $('toast').textContent=message; $('toast').classList.toggle('error',error); $('toast').hidden=false;
  clearTimeout(toastTimer); toastTimer=setTimeout(()=>{$('toast').hidden=true;},error?8500:3200);
}
function setBusy(value) {
  busy=value;if(value){cancelViewportGesture();cancelFollowTimer();}
  for(const id of ['import-button','save-button','project-button','empty-import']) $(id).disabled=value;
  $('undo-button').disabled=value || !state.history?.can_undo;
  $('redo-button').disabled=value || !state.history?.can_redo;
  buildButton.disabled=value || !state.capabilities?.build || !canEdit();
  renderRunStatus();renderBuildStatus();
  document.querySelectorAll('[data-axis]').forEach(input=>input.disabled=value || !canEdit());
  document.querySelectorAll('[data-appearance-edit]').forEach(button=>button.disabled=value || !canEditAppearance() || button.dataset.unavailable==='true');
  document.querySelectorAll('[data-animation-edit]').forEach(button=>button.disabled=value||state.project.mode!=='edit');
  if($('resource-refresh'))$('resource-refresh').disabled=value || !state.capabilities?.resource_catalog;
  if($('scene-transitions'))$('scene-transitions').disabled=value || !state.capabilities?.scene_transitions;
  if($('scene-flags'))$('scene-flags').disabled=value || !state.capabilities?.scene_flags;
  if($('script-undo'))updateScriptActions();
  if($('texture-undo'))updateTextureActions();
  updateFieldToggle();renderRuntimeControls();if(!value)scheduleLiveFollow();
}
async function api(path, payload, {dialog,success}={}) {
  if(busy) return false;
  if(liveFollow.active){
    const reason=['/api/project/new','/api/project/open','/api/import'].includes(path)?'Project changed':path==='/api/scene'?'Scene changed':path==='/api/mode'?'Mode changed':path==='/api/run/stop'?'Owned runtime stopped':path.startsWith('/api/runtime')||path==='/api/run/attach'?'Manual runtime action':null;
    if(reason)stopLiveFollow(reason);
  }
  setBusy(true);
  // Serialize state-changing API work after this editor's in-flight capture.
  // Only explicit follow cancellation aborts that capture, never another request.
  if(dialog) dialog.querySelector('.dialog-error').textContent='';
  try {
    if(liveFollow.pending)await liveFollow.pending;
    const response=await fetch(path,{method:payload===undefined?'GET':'POST',headers:payload===undefined?{}:{'Content-Type':'application/json'},body:payload===undefined?undefined:JSON.stringify(payload)});
    const data=await response.json();
    if(!response.ok || data.error) throw new Error(typeof data.error==='string'?data.error:JSON.stringify(data.error ?? data));
    if(!data.project || !('scene' in data)) throw new Error('Project service returned an invalid state response.');
    if(path==='/api/selection')environmentSelection=null;state=data; render();
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
let environmentSelection=null;
function environmentEntities(){return activeScenePreview()?.entities.filter(e=>e.kind==='environment') ?? [];}
function selectedEnvironment(){return environmentEntities().find(e=>e.entity_id===environmentSelection);}
function movableSelection(){
  const environment=selectedEnvironment();
  if(!environment)return selected();
  if(!scenePreviewCurrent()||!environment.entity_id.includes('/decorations/')||hiddenSceneEntities().has(environment.entity_id))return null;
  return {id:environment.entity_id,components:{Transform:{effective:{position:environment.position}}}};
}
async function moveDecoration(identifier,axis,worldValue){
  const item=selectedEnvironment();if(!scenePreviewCurrent()||!item||item.entity_id!==identifier)return;
  const source=item.source_record,cell=(source.source_record.grid_byte_offset-0x8000)/2;
  const binding=activeScenePreview()?.environment_authoring;
  const shared=binding?.edits?.find(e=>e.record_index===source.object_record_index);
  const instances=structuredClone(binding?.instances??[]);
  let edit=instances.find(e=>e.cell_index===cell);
  if(!edit){edit={cell_index:cell};instances.push(edit);}
  const inherited=shared?.offset?.[axis]??source.record_offset[axis];
  const current=edit.offset?.[axis]??inherited;
  const value=current+(worldValue-item.position[axis])*(axis==='z'?-1:1);
  if(!Number.isInteger(value)||value < -32768||value > 32767){notify('Move exceeds the supported scenery offset range.',true);return;}
  (edit.offset??={})[axis]=value;
  if(value===inherited){delete edit.offset[axis];if(!Object.keys(edit.offset).length)delete edit.offset;}
  const remaining=instances.filter(e=>e.offset||e.rotation_psx),edits=binding?.edits??[];
  await api('/api/command',remaining.length||edits.length?{type:'set_environment_transforms',entity_id:state.scene.id,value:{source_sha256:source.source_record.map_sha256,edits,instances:remaining}}:{type:'clear_environment_transforms',entity_id:state.scene.id});
}
function selected(){return selectedEnvironment()?null:entities().find(e=>e.id===state.selection?.entity_id);}
function selectEnvironment(identifier){environmentSelection=identifier;cancelViewportGesture();renderHierarchy();renderInspector();$('frame-selected').disabled=false;draw();}
function frameEnvironment(){const item=selectedEnvironment();if(item)frame({id:item.entity_id,components:{Transform:{imported:{position:item.position}}}});}
function canEditAppearance(){return (state.project?.mode ?? 'edit').toLowerCase()==='edit' && state.capabilities?.actor_appearance===true;}
function canEdit(){return (state.project?.mode ?? 'edit').toLowerCase()==='edit' && state.capabilities?.edit_transform!==false;}
function displayPosition(value){const p={x:numeric(value?.x)?value.x:0,y:numeric(value?.y)?value.y:0,z:numeric(value?.z)?value.z:0},matrix=activeScenePreview()?.position_to_display;return matrix?{x:matrix[0]*p.x+matrix[1]*p.y+matrix[2]*p.z+matrix[3],y:matrix[4]*p.x+matrix[5]*p.y+matrix[6]*p.z+matrix[7],z:matrix[8]*p.x+matrix[9]*p.y+matrix[10]*p.z+matrix[11]}:p;}
function position(entity){
  const source=entity.components?.Transform?.effective?.position ?? entity.components?.Transform?.imported?.position;
  const preview=scenePreviewCurrent()?activeScenePreview()?.entities.find(item=>item.entity_id===entity.id):null;
  return displayPosition(preview?.preview_position??source);
}
function authored(entity){return !!entity.components?.Animation?.authored_channels || Object.keys(entity.components?.Transform?.authored?.position ?? {}).length>0 || !!entity.components?.ActorAppearance?.authored?.donor_entity_id || Object.keys(entity.components?.Dialogue?.authored?.runs ?? {}).length>0;}
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
$('frame-selected').onclick=()=>{if(selectedEnvironment())frameEnvironment();else{const entity=selected();if(entity)frame(entity);}};
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
  if(event.key==='Escape'&&drag){event.preventDefault();cancelViewportGesture();return;}
  if(event.target.matches('input,textarea') || document.querySelector('dialog[open]')) return;
  if((event.ctrlKey||event.metaKey) && event.key.toLowerCase()==='s'){event.preventDefault();if(!busy)api('/api/project/save',{}, {success:'Project saved.'});}
  if((event.ctrlKey||event.metaKey) && event.key.toLowerCase()==='z'){event.preventDefault();const redo=event.shiftKey;if(redo?state.history?.can_redo:state.history?.can_undo)api(redo?'/api/redo':'/api/undo',{});}
  if(event.key.toLowerCase()==='f'){if(selectedEnvironment())frameEnvironment();else if(selected())frame(selected());}
});
window.addEventListener('beforeunload',event=>{if(state.project?.dirty){event.preventDefault();event.returnValue='';}});

function render(){
  if(drag?.type==='transform'&&!transformGestureCurrent(drag))cancelViewportGesture();
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
  reconcileLiveFollow();renderRuntimeControls();
  document.querySelector('.preview-badge').firstChild.textContent=live?'AUTHORED SCENE · LIVE OBSERVATIONS SEPARATE':'SCENE PREVIEW';
  $('frame-selected').disabled=!selected()&&!selectedEnvironment();
  $('status').textContent=state.scene?.id ? `${state.scene.name} · ${entities().length} entities · ${state.project?.dirty?'Changes not saved':'Project ready'}` : 'Ready · Create or open a project to begin';
  renderHierarchy();renderAssets();renderInspector();
  templateButton.disabled=!state.capabilities?.authored_transform_templates;
  if(templateDialog.open)renderTemplates();
  renderRunStatus();renderBuildStatus();scheduleRunPoll();
  if(lastSceneId!==state.scene?.id){lastSceneId=state.scene?.id;frame();}else draw();
  refreshScenePreview();
}
function activeScenePreview(){return scenePreview&&state.capabilities?.scene_preview&&state.scene_preview_source_key&&sceneProjectPath===state.project?.path&&scenePreview.scene_id===state.scene?.id?scenePreview:null;}
function scenePreviewCurrent(){return !!activeScenePreview()&&sceneKey===state.scene_preview_source_key&&!sceneError;}
function sceneModelsReady(){return modelsEnabled&&activeScenePreview()&&sceneRenderer&&!sceneRenderer.lost&&!sceneError;}
function sceneView(){const positions=new Map(entities().map(entity=>[entity.id,draft?.id===entity.id?draft.position:position(entity)]));if(draft)positions.set(draft.id,draft.position);return {camera,basis:basis(),width,height,grid,hiddenEntities:hiddenSceneEntities(),positions};}
function updateSceneBadge(){
  $('entity-count').textContent=entities().length+environmentEntities().length;
  const ready=sceneModelsReady(),count=ready?sceneRenderer.instances.length:0;
  const hidden=hiddenSceneEntities(),visible=ready?sceneRenderer.instances.filter(instance=>!hidden.has(instance.entity_id)).length:0;
  $('scene-models').hidden=!ready;
  modelToggle.hidden=!state.capabilities?.scene_preview;modelToggle.textContent=sceneError?'Retry models':'Models';modelToggle.title=sceneError ?? 'Show supported SDK meshes at authored placements';
  document.querySelector('.preview-badge span').textContent=sceneError?'Models unavailable · placement markers remain usable':scenePendingKey?(ready?'Updating scene · showing previous preview (scenery editing paused)':'Loading supported scene models…'):ready?`${count} / ${entities().length+environmentEntities().length} meshes loaded · ${visible} visible`:modelsEnabled?'Placement markers · model data unavailable':'Placement markers · models hidden';
  $('coordinate-note').textContent=environmentEntities().length?'Environment: imported transforms · Actors: unknown height/facing use preview conventions':'Unknown actor heights are shown on the ground plane.';
  $('coordinate-note').title=JSON.stringify(activeScenePreview()?.limits ?? []);
}
async function refreshScenePreview(){
  const key=state.scene_preview_source_key;
  if(!state.capabilities?.scene_preview||!key||!modelsEnabled){sceneAbort?.abort();scenePendingKey=null;updateSceneBadge();return;}
  if(activeScenePreview()&&sceneKey===key){sceneAbort?.abort();sceneAbort=null;scenePendingKey=null;sceneFailedKey=null;sceneError=null;updateSceneBadge();return;}
  if(scenePendingKey===key||sceneFailedKey===key){updateSceneBadge();return;}
  const preserveCamera=sceneLoadedId===state.scene?.id && sceneProjectPath===state.project?.path;
  sceneAbort?.abort();const controller=new AbortController();sceneAbort=controller;scenePendingKey=key;sceneError=null;if(!preserveCamera){scenePreview=null;sceneRenderer?.clear();}
  const expectedScene=state.scene?.id,revision=cameraRevision;updateSceneBadge();draw();
  try{
    if(!sceneRenderer){const module=await import('/scene-renderer.js');if(controller.signal.aborted)return;sceneRenderer=new module.SceneRenderer($('scene-models'),message=>{sceneError=message;updateSceneBadge();draw();});}
    const response=await fetch('/api/scene-preview',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}',signal:controller.signal});
    const data=await response.json();if(!response.ok||data.error)throw new Error(typeof data.error==='string'?data.error:'Scene preview failed');
    if(controller.signal.aborted||state.scene_preview_source_key!==key||state.scene?.id!==expectedScene)return;
    if(data.source_key!==key||data.scene_id!==expectedScene)throw new Error('Scene preview source changed while loading; retry models.');
    if(!Array.isArray(data.position_to_display)||data.position_to_display.length!==16||!data.position_to_display.every(numeric))throw new Error('SDK did not provide a valid scene display conversion.');
    const failures=sceneRenderer.load(data);if(!data.entities.some(e=>e.entity_id===environmentSelection))environmentSelection=null;scenePreview=data;sceneProjectPath=state.project?.path;sceneLoadedId=data.scene_id;sceneKey=key;sceneFailedKey=null;scenePendingKey=null;
    if(failures.length)notify(`${failures.length} model assets could not be rendered; their placement markers remain available.`,true);
    renderHierarchy();renderInspector();if(!preserveCamera&&revision===cameraRevision&&!drag)frame();else draw();
  }catch(error){if(error.name!=='AbortError'&&state.scene_preview_source_key===key){sceneFailedKey=key;sceneError=error.message;scenePendingKey=null;if(!preserveCamera)sceneRenderer?.clear();renderInspector();notify(error.message,true);}}
  finally{if(sceneAbort===controller){sceneAbort=null;scenePendingKey=null;updateSceneBadge();draw();}}
}
function renderHierarchy(){
  const list=$('hierarchy');list.replaceChildren();
  const filter=$('entity-search').value.toLowerCase();
  for(const entity of entities().filter(e=>`${e.name} ${e.id}`.toLowerCase().includes(filter))){
    const row=document.createElement('button');row.className='entity-row';row.setAttribute('role','treeitem');row.setAttribute('aria-selected',!selectedEnvironment()&&entity.id===state.selection?.entity_id);row.classList.toggle('selected',!selectedEnvironment()&&entity.id===state.selection?.entity_id);row.title=entity.id;
    row.innerHTML=`<span class="entity-icon">◇</span><span class="entity-name">${escapeHTML(entity.name ?? entity.id)}</span>${authored(entity)?'<span class="authored-dot" title="Authored override"></span>':''}`;
    row.onclick=()=>{environmentSelection=null;api('/api/selection',{entity_id:entity.id});};row.ondblclick=()=>frame(entity);list.append(row);
  }
  const environment=environmentEntities().filter(e=>`${e.name} ${e.entity_id}`.toLowerCase().includes(filter));
  if(environment.length){const heading=document.createElement('div');heading.className='field-note';heading.textContent=`Environment (${environment.length})`;list.append(heading);}
  for(const item of environment){const row=document.createElement('button');row.className='entity-row';row.setAttribute('role','treeitem');row.setAttribute('aria-selected',item.entity_id===environmentSelection);row.classList.toggle('selected',item.entity_id===environmentSelection);row.textContent=item.name;row.title=item.entity_id;row.onclick=()=>selectEnvironment(item.entity_id);row.ondblclick=()=>{selectEnvironment(item.entity_id);frameEnvironment();};list.append(row);}
  if(!list.children.length){const p=document.createElement('div');p.className='empty-panel';p.textContent=entities().length?'No matching entities.':'Imported actors will appear here.';list.append(p);}
}
// Search SDK records already present in project state, including their provenance.
const assetTools=document.createElement('div');assetTools.className='asset-tools';
assetTools.innerHTML='<label class="asset-search-label"><input id="asset-search" type="search" placeholder="Search ID, type, scene, provenance…" aria-label="Search asset database"></label><select id="asset-category" aria-label="Asset category"><option value="all">All records</option><option value="authored">Authored assets</option><option value="model">Models</option><option value="actor">Actors in active scene</option><option value="scene">Imported scenes</option><option value="texture">Textures</option><option value="animation">Animations</option><option value="script">Scripts</option><option value="dialogue">Dialogue</option><option value="collision">Collision</option><option value="trigger">Triggers</option><option value="region">Regions</option></select><span id="asset-results" role="status"></span><button id="resource-refresh">Refresh scene resources</button><span id="resource-status" role="status">Resource catalog has not been loaded.</span>';
$('assets').before(assetTools);
const assetScope=document.createElement('details');assetScope.className='asset-scope';assetScope.innerHTML='<summary>Catalog scope</summary><p>Models come from imported scenes; actors come from the active scene. Scenes lists imported scenes. Textures are inspected with models. Scripts, dialogue, audio and standalone texture catalogs are not available here.</p>';$('assets').after(assetScope);
const assetDetails=document.createElement('dialog');assetDetails.id='asset-details';document.body.append(assetDetails);
$('asset-search').oninput=renderAssets;$('asset-category').onchange=renderAssets;
let resourceRecords=[],resourceLimitations=[],resourceContextKey=null,resourceKey=null,resourcePendingKey=null,resourceAbort=null,resourceError=null;
const resourceStateKey=()=>JSON.stringify([state.project?.path,state.scene?.id,state.scene_preview_source_key]);
$('resource-refresh').onclick=refreshResources;
const transitionsButton=document.createElement('button');transitionsButton.id='scene-transitions';transitionsButton.textContent='Scene transitions';$('resource-refresh').after(transitionsButton);
const transitionsDialog=document.createElement('dialog');transitionsDialog.id='scene-transitions-dialog';document.body.append(transitionsDialog);
let transitionsAbort=null;
transitionsDialog.addEventListener('close',()=>{if(transitionsAbort){transitionsAbort.abort();transitionsAbort=null;setBusy(false);}transitionsDialog.replaceChildren();});
transitionsButton.onclick=openSceneTransitions;
async function openSceneTransitions(){
  if(busy||!state.capabilities?.scene_transitions)return;
  const key=resourceStateKey(),controller=new AbortController();transitionsAbort=controller;setBusy(true);
  transitionsDialog.innerHTML='<div class="dialog-heading"><h2>Scene transitions</h2><button id="close-scene-transitions" aria-label="Close scene transitions">×</button></div><p id="transitions-summary">Verifying scene scripts…</p><div id="transitions-graph"></div><p class="dialog-error" role="alert"></p>';
  $('close-scene-transitions').onclick=()=>transitionsDialog.close();transitionsDialog.showModal();
  try{
    const response=await fetch('/api/scene-transitions',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}',signal:controller.signal});
    const result=await response.json();if(!response.ok||result.error)throw new Error(result.error ?? 'Transition discovery failed');
    if(controller.signal.aborted||!transitionsDialog.open)return;
    if(key!==resourceStateKey()||result.scene_id!==state.scene?.id||result.source_key!==state.scene_preview_source_key||result.read_only!==true||!Array.isArray(result.edges)||result.edges.length>16384||!Array.isArray(result.nodes)||result.nodes.length>16385)throw new Error('Transition source changed or returned invalid graph bounds.');
    const nodes=new Map(result.nodes.map(node=>[node.id,node]));
    $('transitions-summary').textContent=`${result.edges.length} encoded scene-change references · ${result.coverage.script_count} scripts inspected · ${result.coverage.partial_script_count} partial · ${result.coverage.unavailable_script_count} unavailable. Gameplay reachability has not been evaluated.`;
    const graph=$('transitions-graph');
    for(const edge of result.edges){
      const from=nodes.get(edge.source),to=nodes.get(edge.target);if(!from||!to||edge.reachability!=='not_evaluated')throw new Error('Transition graph has an invalid source or destination.');
      const row=document.createElement('article');row.className='transition-edge';
      row.innerHTML=`<div class="transition-nodes"><div><small>Source scene</small><strong>${escapeHTML(from.name)}</strong></div><span aria-label="Encoded reference to">→</span><div><small>Encoded destination</small><strong>${escapeHTML(to.name ?? 'Unresolved destination')}</strong><small>${to.imported?'Imported':to.in_scene_index?'In retail scene index · not imported':'Destination not resolved in scene index'}</small></div></div><p>${escapeHTML(edge.script_name)} · ${escapeHTML(scriptOffset(edge.reference.pc))} · ${escapeHTML(resourceLabel(edge.script_status))}</p><p>Imported encoded entry: X ${escapeHTML(edge.reference.entry_x_encoded)} / Z ${escapeHTML(edge.reference.entry_z_encoded)} / direction ${escapeHTML(edge.reference.direction_encoded)}</p><div class="dialog-actions"><button class="inspect-transition-script">Inspect source script</button><button class="open-transition-scene" ${to.imported?'':'disabled'}>Open imported destination</button></div><details><summary>Reference provenance</summary><pre class="diagnostic-detail"></pre></details>`;
      if(Object.keys(edge.entry_layers?.authored ?? {}).length){const values=edge.entry_layers.effective,note=document.createElement('p');note.className='field-note';note.textContent=`Authored effective entry: X ${values.entry_x_encoded} / Z ${values.entry_z_encoded} / direction ${values.direction_encoded} · Source reverified on Build`;row.querySelector('.dialog-actions').before(note);}

      row.querySelector('pre').textContent=JSON.stringify(edge,null,2);
      row.querySelector('.inspect-transition-script').onclick=()=>{if(busy||key!==resourceStateKey())return;const owner=edge.partition===2?{id:edge.owner_id,name:edge.script_name,partitionTwo:true}:entities().find(entity=>entity.id===edge.owner_id);if(!owner){notify('The source script owner is unavailable.',true);return;}transitionsDialog.close();openActorScript(owner,false,null,null,edge.reference.pc);};
      row.querySelector('.open-transition-scene').onclick=async()=>{if(busy||!to.imported||key!==resourceStateKey())return;transitionsDialog.close();await api('/api/scene',{scene_id:to.id});};
      graph.append(row);
    }
    if(!result.edges.length)graph.textContent='No scene-change references were decoded in the inspected paths. This does not establish that the scene has no exits.';
    for(const note of result.limitations ?? []){const p=document.createElement('p');p.className='field-note';p.textContent=note;graph.append(p);}
  }catch(error){if(error.name!=='AbortError'&&transitionsDialog.open){$('transitions-graph').replaceChildren();transitionsDialog.querySelector('.dialog-error').textContent=error.message;}}
  finally{if(transitionsAbort===controller){transitionsAbort=null;setBusy(false);}}
}
const flagsButton=document.createElement('button');flagsButton.id='scene-flags';flagsButton.textContent='Flag references';transitionsButton.after(flagsButton);
const flagsDialog=document.createElement('dialog');flagsDialog.id='scene-flags-dialog';document.body.append(flagsDialog);
let flagsAbort=null;
flagsDialog.addEventListener('close',()=>{if(flagsAbort){flagsAbort.abort();flagsAbort=null;setBusy(false);}flagsDialog.replaceChildren();});
flagsButton.onclick=async()=>{
  if(busy||!state.capabilities?.scene_flags)return;
  const key=resourceStateKey(),controller=new AbortController();flagsAbort=controller;setBusy(true);
  flagsDialog.innerHTML='<div class="dialog-heading"><h2>Flag references</h2><button aria-label="Close flag references">×</button></div><p class="flags-summary">Verifying scene scripts…</p><input type="search" aria-label="Search flag references" placeholder="Search bank, index, script or operation"><div class="flags-results"></div><p class="dialog-error" role="alert"></p>';
  flagsDialog.querySelector('button').onclick=()=>flagsDialog.close();flagsDialog.showModal();
  try{
    const response=await fetch('/api/scene-flags',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}',signal:controller.signal});
    const result=await response.json();if(!response.ok||result.error)throw new Error(result.error??'Flag discovery failed');
    if(controller.signal.aborted||!flagsDialog.open)return;
    if(key!==resourceStateKey()||result.scene_id!==state.scene?.id||result.source_key!==state.scene_preview_source_key||result.read_only!==true||!Array.isArray(result.groups)||result.groups.length>16384)throw new Error('Flag references do not match the current scene source.');
    const summary=flagsDialog.querySelector('.flags-summary'),list=flagsDialog.querySelector('.flags-results'),search=flagsDialog.querySelector('input');
    const captured=result.runtime_snapshot,snapshot=document.createElement('details');snapshot.innerHTML='<summary>Captured runtime node flags</summary>';list.before(snapshot);
    const captureNote=document.createElement('p');captureNote.textContent=captured?.available?`Epoch boundary frame ${captured.frame} · ${captured.epoch_id}. ${captured.note}`:'No matching guarded capture. Use the Live bridge to capture this scene, then reopen this view.';snapshot.append(captureNote);
    if(captured?.available)appendResourceTable(snapshot,['Epoch-scoped node','Captured word','Set bit indices'],captured.nodes.map(node=>[node.id,node.value_hex,node.set_bits.join(', ')||'None']),'No supported flag fields in this capture.');
    const pager=document.createElement('div');pager.className='dialog-actions';pager.innerHTML='<button aria-label="Previous flag page">Previous</button><span role="status"></span><button aria-label="Next flag page">Next</button>';list.before(pager);
    const previous=pager.querySelector('button'),next=pager.querySelector('button:last-child'),pageStatus=pager.querySelector('span');let page=0;
    const render=()=>{
      const query=search.value.trim().toLowerCase(),groups=result.groups.filter(group=>[group.id,group.script_name,group.bank,String(group.index),...group.references.map(ref=>ref.operation)].join(' ').toLowerCase().includes(query));
      const pages=Math.max(1,Math.ceil(groups.length/100));page=Math.min(page,pages-1);const start=page*100,end=Math.min(start+100,groups.length);
      summary.textContent=`${result.reference_count} encoded references · ${result.groups.length} source-qualified groups · ${result.coverage.script_count} scripts (${result.coverage.partial_script_count} partial, ${result.coverage.unavailable_script_count} unavailable). Showing ${groups.length?start+1:0}–${end} of ${groups.length} matches. Runtime values are unresolved.`;
      previous.disabled=page===0;next.disabled=page+1>=pages;pageStatus.textContent=`Page ${page+1} of ${pages}`;
      list.replaceChildren();
      for(const group of groups.slice(start,end)){
        const row=document.createElement('section');row.className='resource-provenance';
        row.innerHTML=`<h3>${escapeHTML(group.bank)} ${escapeHTML(group.index)} · ${escapeHTML(group.script_name)}</h3><p>${escapeHTML(group.scope)} · ${escapeHTML(resourceLabel(group.script_status))} · ${group.extended_target===null?'Current script context':`Unresolved extended target ${escapeHTML(group.extended_target)}`}</p><p>${group.references.map(ref=>`${escapeHTML(scriptOffset(ref.pc))}: ${escapeHTML(ref.mnemonic)} (${escapeHTML(resourceLabel(ref.status))})`).join(' · ')}</p><button>Inspect source script</button><details><summary>Source provenance and encoded operands</summary><pre></pre></details>`;
        row.querySelector('pre').textContent=JSON.stringify(group,null,2);
        const inspect=(pc=null)=>{if(busy||key!==resourceStateKey())return;const owner=group.partition===2?{id:group.owner_id,name:group.script_name,partitionTwo:true}:entities().find(entity=>entity.id===group.owner_id);if(!owner){notify('The source script owner is unavailable.',true);return;}flagsDialog.close();openActorScript(owner,false,null,null,pc);};
        row.querySelector('button').onclick=()=>inspect();
        const references=document.createElement('div');references.className='dialog-actions';
        for(const ref of group.references){const button=document.createElement('button');button.textContent=`Inspect ${scriptOffset(ref.pc)} · ${ref.mnemonic}`;button.onclick=()=>inspect(ref.pc);references.append(button);}
        row.querySelector('details').before(references);
        list.append(row);
      }
      for(const note of result.limitations??[]){const p=document.createElement('p');p.className='field-note';p.textContent=note;list.append(p);}
    };
    previous.onclick=()=>{page--;render();};next.onclick=()=>{page++;render();};search.oninput=()=>{page=0;render();};render();
  }catch(error){if(error.name!=='AbortError'&&flagsDialog.open)flagsDialog.querySelector('.dialog-error').textContent=error.message;}
  finally{if(flagsAbort===controller){flagsAbort=null;setBusy(false);}}
};
function synchronizeResources(){
  const current=resourceStateKey();
  if(resourceContextKey!==current){
    if(transitionsDialog.open)transitionsDialog.close();
    if(flagsDialog.open)flagsDialog.close();
    resourceContextKey=current;clearFieldMap();clearTriggerScript();if(fieldDialog.open)fieldDialog.close();
    resourceAbort?.abort();resourceRecords=[];resourceLimitations=[];resourceKey=null;resourcePendingKey=null;resourceError=null;
    if(textureDialog.open&&!(textureCommandPending&&textureSession?.projectKey===textureProjectKey()))textureDialog.close();if(animationResourceDialog.open)animationResourceDialog.close();if(scriptResourceDialog.open)scriptResourceDialog.close();
  }
  updateFieldToggle();
  transitionsButton.hidden=!state.capabilities?.scene_transitions;transitionsButton.disabled=busy||!state.capabilities?.scene_transitions;
  flagsButton.hidden=!state.capabilities?.scene_flags;flagsButton.disabled=busy||!state.capabilities?.scene_flags;
  $('resource-refresh').hidden=!state.capabilities?.resource_catalog;$('resource-refresh').disabled=busy||!state.capabilities?.resource_catalog;
  $('resource-status').textContent=!state.capabilities?.resource_catalog?'Resource catalog is unavailable in this service.':resourceError ?? (resourcePendingKey?'Verifying scene resources…':resourceKey?`${resourceRecords.length} verified resource records`:'Refresh to load textures, animations, scripts, dialogue and field-map metadata.');
}
async function refreshResources(){
  if(busy||!state.capabilities?.resource_catalog)return;
  clearFieldMap();clearTriggerScript();draw();
  const key=resourceStateKey(),sceneId=state.scene?.id,sourceKey=state.scene_preview_source_key,controller=new AbortController();
  resourceAbort?.abort();resourceAbort=controller;resourcePendingKey=key;resourceError=null;resourceRecords=[];resourceLimitations=[];resourceKey=null;setBusy(true);renderAssets();
  try{
    const response=await fetch('/api/resource-catalog',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}',signal:controller.signal});
    const result=await response.json();if(!response.ok||result.error)throw new Error(typeof result.error==='string'?result.error:'Resource catalog verification failed');
    if(controller.signal.aborted||key!==resourceStateKey())return;
    if(result.scene_id!==sceneId||result.source_key!==sourceKey||!Array.isArray(result.records)||result.records.length>4096||result.records.some(record=>typeof record.semantic_id!=='string'||!['texture','animation','script','dialogue','collision','trigger','region'].includes(record.asset_kind)))throw new Error('Resource catalog returned stale or invalid records.');
    resourceLimitations=result.limitations ?? [];resourceRecords=[...new Map(result.records.map(record=>[record.semantic_id,{...record,catalog_limitations:result.limitations}])).values()];resourceKey=key;resourcePendingKey=null;renderAssets();
  }catch(error){if(error.name!=='AbortError'&&key===resourceStateKey()){resourceError=error.message;notify(error.message,true);}}
  finally{if(resourceAbort===controller){resourceAbort=null;resourcePendingKey=null;}setBusy(false);synchronizeResources();}
}
function assetRecords(){
  const records=new Map([
    ...(state.assets ?? []).map(asset=>({id:asset.id,type:asset.kind ?? 'model',label:asset.name ?? asset.label ?? `Model ${asset.id.split('/').at(-1)}`,source:asset.source_record?.prot_entry_name ?? asset.scope ?? 'Imported',data:asset})),
    ...entities().map(actor=>({id:actor.id,type:'actor',label:actor.name ?? actor.id,source:state.scene?.name ?? state.scene?.id,sceneId:state.scene?.id,data:actor})),
    ...(state.scenes ?? []).map(scene=>({id:scene.id,type:'scene',label:scene.name ?? scene.id,source:scene.name ?? scene.id,data:scene})),
    ...resourceRecords.map(record=>({id:record.semantic_id,type:record.asset_kind,label:record.name ?? record.semantic_id,source:record.source_record?.prot_entry_name ?? state.scene?.name,sceneId:state.scene?.id,data:record}))
  ].map(record=>[record.id,record]));
  for(const authored of state.authored_assets ?? []){
    if(typeof authored.id!=='string'||!['actor','texture','template','script','scene'].includes(authored.kind))continue;
    const assetId=authored.kind==='script'?(authored.script_id ?? authored.id):authored.id,existing=records.get(assetId);
    records.set(assetId,{...(existing ?? {id:assetId,type:authored.kind,label:authored.name ?? authored.id,source:authored.source_scene ?? authored.scene_id ?? 'Project library',data:{source_record:authored.source_record}}),sceneId:authored.scene_id,authored:authored.authored ?? {},changes:authored.changes ?? [],authoredRecord:authored});
  }
  return [...records.values()];
}
function initialAssetUsage(record,modelReferences){
  if(record.type==='model')return modelReferences.filter(ref=>ref.target_id===record.id);
  if(record.type!=='animation')return [];
  const bindings=record.data?.bindings??[],references=new Map();
  for(const ref of modelReferences){
    const imported=ref.imported&&bindings.some(binding=>binding.actor_semantic_id===ref.source_id&&binding.model_asset_semantic_id===ref.target_id);
    const effective=ref.effective&&bindings.some(binding=>binding.actor_semantic_id===ref.effective_donor_id&&binding.model_asset_semantic_id===ref.target_id);
    if(!imported&&!effective)continue;
    const previous=references.get(ref.source_id);
    references.set(ref.source_id,{source_id:ref.source_id,scene_id:ref.scene_id,
      imported:!!(imported||previous?.imported),effective:!!(effective||previous?.effective)});
  }
  return [...references.values()];
}
function showAssetDetails(record){
  const isAuthored=!!record.authoredRecord;
  assetDetails.innerHTML=`<div class="dialog-heading"><h2>${escapeHTML(record.label)}</h2><button id="close-asset-details" aria-label="Close asset details">×</button></div>${property('Stable ID',record.id)}${property('Record type',record.type)}${property('Source scene',record.authoredRecord?.source_scene ?? record.source)}${isAuthored?`<section class="asset-authored-details"><h3>Authored project settings</h3><p>${escapeHTML(record.changes.join(' · ') || 'Authored project metadata')}</p><pre class="diagnostic-detail" id="asset-authored-data"></pre><button id="open-authored-asset">${record.type==='template'?'Open template library':record.type==='texture'?'Inspect texture':record.type==='script'?'Open script workspace':record.type==='scene'?'Open scene':'Select actor'}${record.type!=='template'&&record.sceneId!==state.scene?.id?' in source scene':''}</button></section>`:''}<details ${isAuthored?'':'open'}><summary>${isAuthored?'Imported source provenance':'SDK source and provenance'}</summary><pre id="asset-source-data" class="diagnostic-detail"></pre></details>`;
  const source=isAuthored?(record.authoredRecord.source_record ?? record.data?.source_record ?? record.data?.components?.RetailMetadata ?? {note:'No additional imported provenance is attached to this authored record.'}):record.data;
  $('asset-source-data').textContent=JSON.stringify(source,null,2);
  if(['model','animation'].includes(record.type)){
    const usage=document.createElement('section');usage.innerHTML=`<h3>Used by</h3><p>${record.type==='model'?'Initial model assignments across imported scenes.':'Verified initial animation bindings and authored donor assignments.'} Scripts may change these assignments during gameplay.</p>`;
    const references=initialAssetUsage(record,state.model_references??[]);
    for(const ref of references){const button=document.createElement('button');button.textContent=`${ref.source_id} · ${ref.imported?'Imported':''}${ref.imported&&ref.effective?' + ':''}${ref.effective?'Effective':''}`;button.onclick=async()=>{if(busy)return;assetDetails.close();if(ref.scene_id!==state.scene?.id&&!await api('/api/scene',{scene_id:ref.scene_id}))return;if(await api('/api/selection',{entity_id:ref.source_id}))frame(selected());};usage.append(button);}
    if(!references.length){const empty=document.createElement('p');empty.textContent='No imported or effective initial actor assignments in this project.';usage.append(empty);}
    $('asset-source-data').parentElement.before(usage);
  }
  if(isAuthored){$('asset-authored-data').textContent=JSON.stringify(record.authored,null,2);$('open-authored-asset').onclick=()=>{assetDetails.close();activateAsset(record);};}
  $('close-asset-details').onclick=()=>assetDetails.close();assetDetails.showModal();
}
async function activateAsset(record){
  if(busy)return;
  if(record.type==='template'){showTemplates();return;}
  if(record.authoredRecord&&['actor','texture','script'].includes(record.type)&&record.sceneId!==state.scene?.id){
    if(!record.sceneId){notify('This authored item does not identify an imported source scene.',true);return;}
    if(!await api('/api/scene',{scene_id:record.sceneId}))return;
  }
  if(record.type==='script'&&record.authoredRecord){
    await openActorScript({id:record.authoredRecord.id,name:record.label,partitionTwo:true});
  }else if(record.type==='actor'){
    if(await api('/api/selection',{entity_id:record.id})){frame(selected());document.querySelector('.workspace-tabs [data-panel="viewport"]').click();}
  }else if(record.type==='scene'){
    if(await api('/api/scene',{scene_id:record.id}))document.querySelector('.workspace-tabs [data-panel="viewport"]').click();
  }else if(record.type==='model')openModel(record.id);
  else if(record.type==='texture')openTexture(record);
  else if(record.type==='animation')openAnimationResource(record);
  else if(['collision','trigger','region'].includes(record.type))openFieldResource(record);
  else if(['script','dialogue'].includes(record.type))openScriptResource(record);
  else showAssetDetails(record);
}
function renderAssets(){
  synchronizeResources();
  const list=$('assets'),query=$('asset-search').value.trim().toLowerCase().split(/\s+/).filter(Boolean),category=$('asset-category').value;
  assetScope.querySelector('p').textContent=`Models come from imported scenes; actors come from the active scene. Scenes lists imported scenes. Authored assets gathers project-wide actor edits, script dialogue edits, texture replacements and transform templates without a resource refresh. Refresh adds scene texture candidates, referenced scene-header animations, actor and partition-two scripts, dialogue and supported field-map metadata; it does not inventory the shared party bank or every runtime resource. ${state.capabilities?.actor_script_preview?'Script inspection and supported dialogue text tools are available from an actor’s Inspector.':'Script and dialogue inspection is not available in this service.'} Audio is not cataloged here. ${resourceLimitations.map(limit=>typeof limit==='string'?limit:JSON.stringify(limit)).join(' ')}`;
  const records=assetRecords(),filtered=records.filter(record=>(category==='all'||(category==='authored'?!!record.authoredRecord:record.type===category&&(category!=='actor'||record.sceneId===state.scene?.id)))&&query.every(term=>JSON.stringify(record).toLowerCase().includes(term)));
  list.replaceChildren();$('asset-count').textContent=records.length;$('asset-results').textContent=`${filtered.length} / ${records.length} records`;
  for(const record of filtered){
    const row=document.createElement('div');row.className='asset-result';
    const card=document.createElement('button');card.className='asset-card';card.title=record.id;card.innerHTML=`<strong>${escapeHTML(record.label)}${record.authoredRecord?'<span class="asset-authored-badge">Authored</span>':''}</strong><small>${escapeHTML(record.type)} · ${escapeHTML(record.authoredRecord?.source_scene ?? record.source)}</small>${record.authoredRecord?`<span class="asset-change-summary">${escapeHTML(record.changes.join(' · ') || 'Authored project settings')}</span>`:''}<code>${escapeHTML(record.id)}</code>`;
    card.onclick=()=>activateAsset(record);
    const info=document.createElement('button');info.className='asset-info';info.textContent='ⓘ';info.title='View stable ID, source and provenance';info.setAttribute('aria-label',`Details for ${record.label}`);info.onclick=()=>['script','dialogue'].includes(record.type)?openScriptResource(record):['collision','trigger','region'].includes(record.type)?openFieldResource(record):showAssetDetails(record);row.append(card,info);list.append(row);
  }
  if(!filtered.length){const p=document.createElement('p');p.className='field-note';p.textContent=category==='authored'?(records.some(record=>record.authoredRecord)?'No matching authored assets. Try an actor, texture, scene or change description.':'No authored assets yet. Edit an actor, replace a texture or capture a transform template; project edits appear here across scenes.'):['texture','animation','script','dialogue','collision','trigger','region'].includes(category)&&!resourceKey?(state.capabilities?.resource_catalog?'Use Refresh scene resources to verify and load this category.':'Resource catalogs are unavailable in this service.'):records.length?'No matching records. Try a stable ID, model type, scene name or source term.':'Import a scene to populate the catalog.';list.append(p);}
}
const fieldDialog=document.createElement('dialog');fieldDialog.id='field-map-dialog';document.body.append(fieldDialog);
const fieldToggle=document.createElement('button');fieldToggle.id='field-map-toggle';fieldToggle.textContent='Base collision';fieldToggle.hidden=true;fieldToggle.setAttribute('aria-pressed','false');$('grid-toggle').after(fieldToggle);
const fieldNote=document.createElement('div');fieldNote.className='field-map-note';fieldNote.hidden=true;fieldNote.setAttribute('role','status');document.querySelector('.viewport-toolbar').after(fieldNote);
let fieldMap=null,fieldKey=null,fieldAbort=null,fieldPending=false;
const fieldMapScope='Base blocked grid only · Y = 0 is a display placeholder, not decoded height. Runtime/script paints and actors are excluded. Canonical positive-X range only; wrapping and boundary aliases are not shown. Lines are drawn over models.';
function updateFieldToggle(){
  fieldToggle.hidden=!state.capabilities?.field_map_preview;fieldToggle.disabled=busy||fieldPending;
  fieldToggle.classList.toggle('active',!!fieldMap);fieldToggle.setAttribute('aria-pressed',!!fieldMap);fieldToggle.textContent=fieldPending?'Loading collision…':'Base collision';
}
function clearFieldMap(){
  fieldAbort?.abort();fieldAbort=null;fieldMap=null;fieldKey=null;fieldPending=false;fieldNote.hidden=true;updateFieldToggle();
}
function validateFieldMap(result,record,key){
  if(key!==resourceStateKey()||result.source_key!==state.scene_preview_source_key||result.scene_id!==state.scene?.id||result.semantic_id!==record.id||result.asset_kind!=='collision'||result.coordinate_system!=='psx_guest_xz')throw new Error('Field map source changed while loading. Refresh scene resources and retry.');
  if(!Array.isArray(result.rectangles)||result.rectangles.length>65536||result.rectangles.some(r=>!r||![r.x_min,r.x_max,r.z_min,r.z_max].every(numeric)||r.x_min>r.x_max||r.z_min>r.z_max)||!Array.isArray(result.triggers)||result.triggers.length>65536)throw new Error('Field map service returned invalid or oversized geometry.');
  return result;
}
async function loadFieldMap(record){
  if(busy||!state.capabilities?.field_map_preview||resourceKey!==resourceStateKey())return false;
  clearFieldMap();draw();const key=resourceStateKey(),controller=new AbortController();fieldAbort=controller;fieldPending=true;setBusy(true);
  try{
    const response=await fetch('/api/field-map-preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:record.id}),signal:controller.signal});
    const result=await response.json();if(!response.ok||result.error)throw new Error(typeof result.error==='string'?result.error:'Field map verification failed');
    if(controller.signal.aborted)return false;
    fieldMap=validateFieldMap(result,record,key);fieldKey=key;fieldNote.textContent=`${fieldMap.rectangles.length} blocked rectangles · ${fieldMapScope}`;fieldNote.title=(fieldMap.limitations ?? []).map(value=>typeof value==='string'?value:JSON.stringify(value)).join(' ');fieldNote.hidden=false;return true;
  }catch(error){clearFieldMap();if(error.name!=='AbortError'){notify(error.message,true);if(fieldDialog.open)fieldDialog.querySelector('.dialog-error').textContent=error.message;}return false;}
  finally{if(fieldAbort===controller)fieldAbort=null;fieldPending=false;setBusy(false);draw();}
}
fieldToggle.onclick=async()=>{
  if(busy)return;if(fieldMap){clearFieldMap();draw();return;}
  if(resourceKey!==resourceStateKey())await refreshResources();
  const candidates=assetRecords().filter(record=>record.type==='collision');
  if(candidates.length!==1){notify(candidates.length?'Choose a collision record in the asset browser.':'No verified base collision record is available for this scene.',true);return;}
  await loadFieldMap(candidates[0]);
};
function openFieldResource(record){
  if(busy||resourceKey!==resourceStateKey())return;
  const collision=record.type==='collision',data=record.data;
  fieldDialog.innerHTML=`<div class="dialog-heading"><h2>${escapeHTML(record.label)}</h2><button id="close-field-map" aria-label="Close field map inspector">×</button></div>${property('Stable ID',record.id)}${property('Record type',collision?'Base collision grid':record.type==='region'?'Encoded region record':'Encoded trigger record')}<p class="field-note">${collision?fieldMapScope:'Read-only encoded trigger or region fields. Destination scenes, runtime activation and story conditions are not inferred.'}</p><div id="field-record-summary"></div>${collision?'<button id="show-base-collision" class="accent">Show base collision</button>':''}<details class="resource-provenance"><summary>Source provenance and complete metadata</summary><pre class="diagnostic-detail"></pre></details><p class="dialog-error" role="alert"></p>`;
  const summary=$('field-record-summary');
  for(const [key,value] of Object.entries(data))if(!['id','semantic_id','asset_kind','kind','name','layer','scene_id','reference_commit','collision_id','source_record','catalog_limitations','limitations'].includes(key)&&value!==null&&['string','number','boolean'].includes(typeof value))summary.insertAdjacentHTML('beforeend',property(key.replaceAll('_',' '),value));
  for(const [key,label] of [['encoded','Encoded source fields'],['tile_bounds','Half-open tile bounds'],['destination_world','Decoded intra-scene destination (X/Z only)'],['script_reference','Unresolved script reference']]){
    if(data[key]&&typeof data[key]==='object'){const heading=document.createElement('h3');heading.textContent=label;summary.append(heading);appendResourceTable(summary,['Field','Source value'],Object.entries(data[key]).map(([field,value])=>[field.replaceAll('_',' '),value]),'No fields supplied.');}
  }
  if(collision&&Array.isArray(data.elevation_overrides)){
    const heading=document.createElement('h3');heading.textContent='Ramp height adjustments';summary.append(heading);
    const note=document.createElement('p');note.className='field-note';note.textContent='Read-only kind-2 records, primary then fallback; first matching tile wins. Values are Y adjustments to the four-corner height mean when object-cell flag 0x0800 is set, not complete floor heights. Subcells are ordered (0,0), (1,0), (0,1), (1,1); positive Y points down.';summary.append(note);
    const filter=document.createElement('input');filter.type='search';filter.className='ramp-filter';filter.placeholder='Filter ramps, e.g. 25 26';filter.setAttribute('aria-label','Filter ramp records');summary.append(filter);
    const count=document.createElement('p');count.className='field-note';count.setAttribute('role','status');summary.append(count);
    const table=document.createElement('div');summary.append(table);
    const renderRamps=()=>{
      const terms=filter.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
      const rows=data.elevation_overrides.filter(row=>{const words=[row.table_source,String(row.record_index),String(row.tile_x),String(row.tile_z)].map(String);return terms.every(term=>words.includes(term));});
      count.textContent=`${rows.length} / ${data.elevation_overrides.length} ramp records · filter matches table, row or tile coordinates`;
      table.replaceChildren();appendResourceTable(table,['Table / row','Tile X','Tile Z','Signed coarse','Subcell ΔY'],rows.map(row=>[`${row.table_source} / ${row.record_index}`,row.tile_x,row.tile_z,row.coarse_signed,(row.subcell_delta_y ?? []).join(', ')]),'No matching ramp records.');
    };
    filter.oninput=renderRamps;renderRamps();
  }
  if(!collision){const coordinates=document.createElement('p');coordinates.className='field-note';coordinates.textContent='Trigger and region tile coordinates are not collision-grid cells. No trigger or region geometry is inferred in the viewport.';summary.append(coordinates);}
  const limits=document.createElement('p');limits.className='field-note';limits.textContent=(data.limitations ?? []).map(value=>typeof value==='string'?value:JSON.stringify(value)).join(' ');summary.append(limits);
  fieldDialog.querySelector('pre').textContent=JSON.stringify(data,null,2);$('close-field-map').onclick=()=>fieldDialog.close();
  if(collision){$('show-base-collision').disabled=!state.capabilities?.field_map_preview;$('show-base-collision').onclick=async()=>{if(await loadFieldMap(record)){fieldDialog.close();document.querySelector('.workspace-tabs [data-panel="viewport"]').click();}};}
  if(record.type==='trigger'&&state.capabilities?.trigger_script_preview&&(data.script_reference?.partition===2||data.trigger_type==='partition_2_trigger')){
    const button=document.createElement('button');button.className='accent';button.id='inspect-trigger-script';button.textContent='Inspect referenced script';button.onclick=()=>openTriggerScript(record);summary.append(button);
  }
  fieldDialog.showModal();
}
const triggerScriptDialog=document.createElement('dialog');triggerScriptDialog.id='trigger-script-dialog';document.body.append(triggerScriptDialog);
let triggerScriptAbort=null,triggerScriptRequest=0;
function clearTriggerScript(close=true){
  triggerScriptRequest++;const pending=triggerScriptAbort;triggerScriptAbort=null;pending?.abort();if(pending)setBusy(false);
  if(close&&triggerScriptDialog.open)triggerScriptDialog.close();triggerScriptDialog.replaceChildren();
}
triggerScriptDialog.addEventListener('close',()=>clearTriggerScript(false));
function validateTriggerScript(result,record,key){
  const expected=record.data.script_reference?.record_index ?? record.data.encoded?.record_index;
  if(result.read_only!==true||key!==resourceStateKey()||result.source_key!==state.scene_preview_source_key||result.scene_id!==state.scene?.id||result.trigger_id!==record.id||result.partition!==2||!Number.isInteger(result.record_index)||result.record_index<0||(Number.isInteger(expected)&&result.record_index!==expected)||typeof result.script_id!=='string')throw new Error('Referenced script source changed or did not match the trigger. Refresh resources and retry.');
  if(!result.record||![result.record.byte_offset,result.record.byte_length,result.record.script_offset].every(value=>Number.isSafeInteger(value)&&value>=0))throw new Error('Referenced script record bounds are invalid.');
  const report=result.inspection;
  if(!report||typeof report.status!=='string')throw new Error('Referenced script inspection is missing.');
  for(const [key,max] of [['instructions',65536],['dialogues',4096],['opaque_regions',65536],['stops',4096]])if(!Array.isArray(report[key])||report[key].length>max||report[key].some(row=>!row||typeof row!=='object'||Array.isArray(row)))throw new Error('Referenced script report contains invalid or oversized arrays.');
  if(report.instructions.some(row=>!Number.isInteger(row.pc)||row.pc<0||typeof row.mnemonic!=='string'||!Array.isArray(row.successors)||row.successors.length>64||row.successors.some(next=>!next||!Number.isInteger(next.pc))))throw new Error('Referenced script instructions are invalid.');
  let tokens=0;
  for(const dialogue of report.dialogues){if(!Number.isInteger(dialogue.pc)||typeof dialogue.text!=='string'||dialogue.text.length>131072||!Array.isArray(dialogue.tokens)||dialogue.tokens.some(token=>!token||typeof token!=='object'))throw new Error('Referenced dialogue data is invalid.');tokens+=dialogue.tokens.length;}
  if(tokens>65536)throw new Error('Referenced dialogue token count exceeds the preview limit.');
  return report;
}
async function openTriggerScript(record){
  if(busy||!state.capabilities?.trigger_script_preview||resourceKey!==resourceStateKey())return;
  clearTriggerScript();fieldDialog.close();const key=resourceStateKey(),request=++triggerScriptRequest,controller=new AbortController();triggerScriptAbort=controller;
  triggerScriptDialog.innerHTML=`<div class="dialog-heading"><h2>Referenced partition-2 script</h2><button id="close-trigger-script" aria-label="Close referenced script">×</button></div><div class="trigger-script-navigation"><button id="back-trigger">Back to trigger</button><span>Read only · source inspection</span></div><div id="trigger-script-report"><p>Verifying the trigger reference and bounded script record…</p></div><p class="dialog-error" role="alert"></p>`;
  $('close-trigger-script').onclick=()=>clearTriggerScript();$('back-trigger').onclick=()=>{clearTriggerScript();if(key===resourceStateKey())openFieldResource(record);};triggerScriptDialog.showModal();setBusy(true);
  try{
    const response=await fetch('/api/trigger-script',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:record.id}),signal:controller.signal});
    const text=await response.text();if(text.length>8388608)throw new Error('Referenced script exceeds the bounded preview size.');const result=JSON.parse(text);if(!response.ok||result.error)throw new Error(typeof result.error==='string'?result.error:'Referenced script inspection failed');
    if(controller.signal.aborted||request!==triggerScriptRequest||!triggerScriptDialog.open)return;
    const report=validateTriggerScript(result,record,key);renderTriggerScript(result,report);
    const edit=document.createElement('button');edit.textContent='Open dialogue workspace';
    edit.onclick=()=>{if(busy)return;clearTriggerScript();openActorScript({id:result.script_id.replace(/^script:\/\//,'scene://'),name:`Partition 2 script ${result.record_index}`,triggerId:record.id});};
    triggerScriptDialog.querySelector('.trigger-script-navigation').append(edit);
  }catch(error){if(error.name!=='AbortError'&&request===triggerScriptRequest&&triggerScriptDialog.open){$('trigger-script-report').replaceChildren();triggerScriptDialog.querySelector('.dialog-error').textContent=error.message;}}
  finally{if(triggerScriptAbort===controller){triggerScriptAbort=null;setBusy(false);}}
}
function appendScriptOperands(cell,instruction){
  const operands=instruction.operands;
  if(instruction.mnemonic==='DIALOGUE_SEGMENT'){const text=document.createElement('p');text.textContent=operands?.text??'';cell.append(text);return;}
  if(instruction.target_context!==null&&instruction.target_context!==undefined){
    const context=document.createElement('p');context.className='script-warning';
    context.textContent=`Extended target ${instruction.target_context}: actor identity is unresolved.`;cell.append(context);
  }
  if(instruction.mnemonic==='ACTOR_POSITION'&&Array.isArray(operands?.encoded_xyz)&&operands.encoded_xyz.length===3){
    const summary=document.createElement('p');
    const immediate=operands.mode==='immediate';
    const axes=operands.encoded_xyz.map((value,index)=>`${'XYZ'[index]}: ${immediate&&value===65535?'leave unchanged':value}`).join(', ');
    summary.textContent=`${axes}. ${immediate?'Immediate assignment':`Timed movement (${operands.ticks} encoded ticks; interpolation unresolved)`}. Runtime position is not observed.`;
    cell.append(summary);
  }
  if(instruction.mnemonic==='DIALOGUE_PICKER'&&Array.isArray(operands?.options)){
    const options=document.createElement('ol');
    for(const option of operands.options){const item=document.createElement('li');item.textContent=`${option.label} — encoded target ${scriptOffset(option.encoded_target)}`;options.append(item);}
    const note=document.createElement('p');note.className='field-note';note.textContent='Runtime choice and pager continuation are unresolved. Decoded choice paths can be inspected through the successor links.';
    cell.append(options,note);
  }
  const details=document.createElement('details'),label=document.createElement('summary'),raw=document.createElement('pre');
  label.textContent='Encoded operands';raw.textContent=typeof operands==='string'?operands:JSON.stringify(operands??{},null,2);
  details.open=!['ACTOR_POSITION','DIALOGUE_PICKER'].includes(instruction.mnemonic);details.append(label,raw);cell.append(details);
}
function appendScriptInstructions(host,report){
  host.replaceChildren();host.classList.remove('script-table-wrap');
  const messages=(report.dialogues??[]).map(message=>({pc:message.pc,mnemonic:'DIALOGUE_SEGMENT',operands:{text:message.text},
    successors:[{pc:message.pc+message.length,condition:'encoded_continuation'}]}));
  const instructions=[...(report.instructions??[]),...messages].sort((a,b)=>a.pc-b.pc),byPC=new Map(instructions.map(item=>[item.pc,item])),rows=new Map(),incoming=new Map(),history=[];
  let selectedPC=null;
  const navigation=document.createElement('div');navigation.className='script-path-navigation';
  const back=document.createElement('button');back.textContent='Back to previous instruction';back.disabled=true;
  const status=document.createElement('p');status.className='field-note';status.setAttribute('role','status');status.textContent='Follow decoded successors or select an offset. These links do not simulate execution.';
  const predecessors=document.createElement('div');predecessors.className='script-predecessors';
  navigation.append(back,status,predecessors);host.append(navigation);
  for(const instruction of instructions)for(const next of instruction.successors??[]){
    if(!incoming.has(next.pc))incoming.set(next.pc,new Set());incoming.get(next.pc).add(instruction.pc);
  }
  function select(pc,remember=true){
    if(!rows.has(pc))return false;
    if(remember&&selectedPC!==null&&selectedPC!==pc)history.push(selectedPC);
    if(rows.has(selectedPC))rows.get(selectedPC).classList.remove('script-path-selected');
    selectedPC=pc;const row=rows.get(pc);row.classList.add('script-path-selected');row.scrollIntoView({block:'nearest'});row.focus({preventScroll:true});
    back.disabled=!history.length;status.textContent=`Selected ${scriptOffset(pc)} · ${byPC.get(pc).mnemonic} · Decoded incoming edges (execution unknown)`;
    predecessors.replaceChildren();
    for(const source of incoming.get(pc)??[]){const button=document.createElement('button');button.textContent=`From ${scriptOffset(source)}`;button.onclick=()=>select(source);predecessors.append(button);}
    if(!predecessors.childNodes.length)predecessors.textContent='No decoded incoming edges in this report.';
    return true;
  }
  back.onclick=()=>{if(history.length)select(history.pop(),false);};
  const search=document.createElement('input');search.type='search';search.setAttribute('aria-label','Search decoded script paths');search.placeholder='Text, instruction, operand or offset';search.maxLength=256;
  const previous=document.createElement('button');previous.textContent='Previous match';
  const next=document.createElement('button');next.textContent='Next match';
  const matchesStatus=document.createElement('p');matchesStatus.className='field-note';matchesStatus.setAttribute('role','status');
  const searchBar=document.createElement('div');searchBar.className='script-path-search';searchBar.append(search,previous,next);navigation.prepend(searchBar,matchesStatus);
  const searchable=instructions.map(node=>({pc:node.pc,text:`${scriptOffset(node.pc)} ${node.mnemonic} ${JSON.stringify(node.operands??{})}`.toLowerCase()}));
  let matches=[],matchIndex=-1;
  function updateMatches(){
    const query=search.value.trim().toLowerCase();matches=query?searchable.filter(node=>node.text.includes(query)).map(node=>node.pc):[];matchIndex=-1;
    previous.disabled=next.disabled=!matches.length;
    matchesStatus.textContent=query?`${matches.length} matching decoded paths`:'Search covers decoded paths only; opaque bytes are excluded.';
  }
  function stepMatch(direction){if(!matches.length)return;matchIndex=matchIndex<0?(direction>0?0:matches.length-1):(matchIndex+direction+matches.length)%matches.length;select(matches[matchIndex]);matchesStatus.textContent=`Match ${matchIndex+1} of ${matches.length}`;}
  search.oninput=updateMatches;search.onkeydown=event=>{if(event.key==='Enter'){event.preventDefault();stepMatch(event.shiftKey?-1:1);}};
  previous.onclick=()=>stepMatch(-1);next.onclick=()=>stepMatch(1);updateMatches();

  const wrap=document.createElement('div');wrap.className='script-table-wrap';wrap.innerHTML='<table><thead><tr><th>Record offset</th><th>Instruction</th><th>Operands</th><th>Successors</th></tr></thead><tbody></tbody></table>';host.append(wrap);
  const body=wrap.querySelector('tbody');
  for(const instruction of instructions){
    const row=document.createElement('tr');row.tabIndex=-1;rows.set(instruction.pc,row);
    const offset=document.createElement('td'),jump=document.createElement('button');jump.textContent=scriptOffset(instruction.pc);jump.setAttribute('aria-label',`Select instruction ${scriptOffset(instruction.pc)}`);jump.onclick=()=>select(instruction.pc);offset.append(jump);row.append(offset);
    const mnemonic=document.createElement('td');mnemonic.textContent=instruction.mnemonic;row.append(mnemonic);
    const operands=document.createElement('td');appendScriptOperands(operands,instruction);row.append(operands);
    const successors=document.createElement('td');
    for(const next of instruction.successors??[]){
      const condition=next.condition?(typeof next.condition==='string'?next.condition:JSON.stringify(next.condition)):'';
      if(byPC.has(next.pc)){const button=document.createElement('button');button.textContent=`To ${scriptOffset(next.pc)}${condition?' · '+condition:''}`;button.onclick=()=>{if(selectedPC!==instruction.pc)select(instruction.pc);select(next.pc);};successors.append(button);}
      else{const note=document.createElement('p');note.className='field-note';const stop=(report.stops??[]).find(item=>item.pc===next.pc);note.textContent=`${scriptOffset(next.pc)} · Not decoded${condition?' · '+condition:''}${stop?.reason?' · '+stop.reason:''}`;successors.append(note);}
    }
    if(!(instruction.successors??[]).length)successors.textContent='No decoded successor';
    row.append(successors);body.append(row);
  }
  if(!instructions.length){status.textContent='No instructions were decoded.';wrap.hidden=true;}
  return {select};
}
function renderTriggerScript(result,report){
  const host=$('trigger-script-report');
  host.innerHTML=`<p class="script-summary">${report.instructions.length} decoded instructions · ${report.dialogues.length} dialogue segments · ${escapeHTML(report.status==='decoded_supported_paths'?'Supported paths decoded':resourceLabel(report.status))}</p>${property('Script ID',result.script_id)}${property('Partition / record',`2 / ${result.record_index}`)}${property('Decoded MAN byte offset',result.record.byte_offset)}${property('Record byte length',result.record.byte_length)}${property('Script offset in record',scriptOffset(result.record.script_offset))}<p class="field-note">Offsets are relative to this bounded script record. Decoding does not establish trigger activation, branch execution or story state. Substitution tokens remain placeholders. Open the dialogue workspace to check which text runs support editing.</p><div id="trigger-script-warnings"></div><section><h3>Decoded dialogue</h3><div id="trigger-script-dialogues"></div></section><details class="script-instructions" ${report.dialogues.length?'':'open'}><summary>Instruction paths (${report.instructions.length})</summary><div id="trigger-script-instructions"></div></details><details class="script-raw"><summary>Source bounds, raw bytes and complete provenance</summary><pre class="diagnostic-detail"></pre></details>`;
  const warnings=$('trigger-script-warnings');
  if(report.opaque_regions.length||report.stops.length){const notice=document.createElement('p');notice.className='script-warning';notice.textContent=`${report.opaque_regions.length} opaque regions · ${report.stops.length} decoder stops. Unsupported and unvisited bytes remain unresolved.`;warnings.append(notice);}
  for(const item of report.opaque_regions){const line=document.createElement('p');line.className='field-note';line.textContent=`${scriptOffset(item.pc)} · ${item.length ?? 'Unknown'} opaque bytes: ${item.reason ?? 'Unresolved region'}`;warnings.append(line);}
  for(const item of report.stops){const line=document.createElement('p');line.className='field-note';line.textContent=`Stopped at ${scriptOffset(item.pc)}: ${item.reason ?? 'Unsupported path'}`;warnings.append(line);}
  for(const limit of result.limitations ?? []){const line=document.createElement('p');line.className='field-note';line.textContent=typeof limit==='string'?limit:JSON.stringify(limit);warnings.append(line);}
  const dialogues=$('trigger-script-dialogues');if(!report.dialogues.length)dialogues.textContent='No dialogue was decoded in these paths.';
  for(const dialogue of report.dialogues){const card=document.createElement('article');card.className='script-dialogue-card';card.innerHTML=`<small>Imported segment · ${escapeHTML(scriptOffset(dialogue.pc))} · ${escapeHTML(dialogue.length ?? 'Unknown')} bytes</small><p></p><details><summary>Text tokens and source span</summary><pre class="diagnostic-detail"></pre></details>`;card.querySelector('p').textContent=dialogue.text;card.querySelector('pre').textContent=JSON.stringify(dialogue,null,2);dialogues.append(card);}
  appendScriptInstructions($('trigger-script-instructions'),report);
  host.querySelector('.script-raw pre').textContent=JSON.stringify(result,null,2);
}
function drawFieldMap(){
  if(!fieldMap||fieldKey!==resourceStateKey())return;
  ctx.save();ctx.strokeStyle='#e1ac688f';ctx.fillStyle='#d39d4b10';ctx.lineWidth=1;
  for(const rectangle of fieldMap.rectangles){
    const points=[[rectangle.x_min,rectangle.z_min],[rectangle.x_max,rectangle.z_min],[rectangle.x_max,rectangle.z_max],[rectangle.x_min,rectangle.z_max]].map(([x,z])=>project({x,y:0,z}));
    if(points.some(p=>!p||!numeric(p.x)||!numeric(p.y))||points.every(p=>p.x<0)||points.every(p=>p.x>width)||points.every(p=>p.y<0)||points.every(p=>p.y>height))continue;
    ctx.beginPath();ctx.moveTo(points[0].x,points[0].y);for(const point of points.slice(1))ctx.lineTo(point.x,point.y);ctx.closePath();ctx.fill();ctx.stroke();
  }
  ctx.restore();
}
const textureDialog=document.createElement('dialog');textureDialog.id='texture-dialog';document.body.append(textureDialog);
let textureRequest=0,textureAbort=null,textureSession=null,texturePreview=null,textureCommandPending=false;
const textureProjectKey=()=>JSON.stringify([state.project?.path,state.scene?.id]);
const canEditTexture=()=>state.capabilities?.texture_replacement===true&&(state.project?.mode ?? 'edit').toLowerCase()==='edit';
textureDialog.addEventListener('close',()=>{textureRequest++;textureAbort?.abort();});
function textureAuthored(){return state.texture_overrides?state.texture_overrides[textureSession?.record.id] ?? null:texturePreview?.authored ?? null;}
function updateTextureActions(){
  if(!$('texture-undo'))return;
  const pending=!!$('texture-file').files?.length,authored=textureAuthored(),supported=!!state.capabilities?.texture_replacement;
  $('texture-authoring').hidden=!supported;$('texture-history').hidden=!supported;$('texture-layer-label').hidden=!supported;
  $('texture-layer').disabled=busy;$('texture-palette').disabled=busy;
  $('texture-file').disabled=busy||!canEditTexture();$('texture-apply').disabled=busy||!canEditTexture()||!pending;
  $('texture-discard').hidden=!pending;$('texture-discard').disabled=busy;
  $('texture-clear').disabled=busy||pending||!canEditTexture()||!authored;
  $('texture-undo').disabled=busy||pending||!canEditTexture()||!state.history?.can_undo;
  $('texture-redo').disabled=busy||pending||!canEditTexture()||!state.history?.can_redo;
  $('texture-save').disabled=busy||pending||!state.project?.dirty;$('texture-source').disabled=busy;
  $('texture-project-status').textContent=pending?'Selected file is not applied. Apply or discard before project actions.':busy?'Verifying…':projectSaveStatus();
  $('texture-authored').textContent=authored?`Authored TIM replacement · ${authored.byte_length} bytes · SHA-256 ${authored.asset_sha256?.slice(0,12) ?? 'unavailable'}`:'No authored replacement · effective pixels inherit the imported TIM.';
}
async function openTexture(record,paletteIndex=0,layer='effective'){
  if(busy)return;if(!state.capabilities?.texture_preview){notify('Texture decoding is unavailable in this service.',true);return;}
  const key=resourceStateKey(),continuing=textureDialog.open&&textureSession?.record.id===record.id&&textureSession.projectKey===textureProjectKey();
  const authoredBinding=state.texture_overrides?.[record.id],trustedAuthored=!!authoredBinding&&typeof state.scene?.id==='string'&&authoredBinding.source_scene_id===state.scene.id;
  if(!continuing&&resourceKey!==key&&!trustedAuthored){notify('Refresh scene resources or open a current authored texture binding to inspect this texture.',true);return;}
  if(!continuing){
    textureSession={record,projectKey:textureProjectKey(),paletteIndex,layer};texturePreview=null;
    textureDialog.innerHTML=`<div class="dialog-heading"><h2>${escapeHTML(record.label)}</h2><button id="close-texture" aria-label="Close texture preview">×</button></div><div id="texture-history" class="texture-history" hidden><button id="texture-undo">Undo</button><button id="texture-redo">Redo</button><button id="texture-save">Save project</button><span id="texture-project-status"></span></div><div class="texture-view-controls"><label id="texture-layer-label" hidden>Preview layer<select id="texture-layer" aria-label="Texture preview layer"><option value="effective">Effective</option><option value="imported">Imported</option></select></label><label id="texture-palette-label" hidden>Palette<select id="texture-palette" aria-label="Texture palette"></select></label></div><p id="texture-summary">Verifying texture source…</p><div class="texture-bitmap-wrap"><canvas id="texture-bitmap" aria-label="Decoded texture pixels"></canvas></div><section id="texture-authoring" hidden><h3>Authored replacement</h3><p id="texture-authored"></p><button id="texture-source">Download original TIM</button><label>Replacement TIM file<input id="texture-file" type="file" accept=".tim" aria-label="Replacement TIM file"></label><p id="texture-file-status" class="field-note">Choose a TIM file up to 1 MiB. The service requires matching headers, dimensions, bit depth and palette layout.</p><div class="run-actions"><button id="texture-apply" class="accent" disabled>Apply replacement</button><button id="texture-discard" hidden>Discard selected file</button><button id="texture-clear" disabled>Clear override</button></div></section><p class="field-note">Palette and layer selection only affect inspection. Static texture candidates do not establish runtime VRAM residency. PSX semi-transparent blending is not reconstructed.</p><details class="resource-provenance"><summary>Texture source and limitations</summary><pre class="diagnostic-detail"></pre></details><p class="dialog-error" role="alert"></p>`;
    $('close-texture').onclick=()=>textureDialog.close();
    $('texture-undo').onclick=()=>textureProjectAction('/api/undo',{});$('texture-redo').onclick=()=>textureProjectAction('/api/redo',{});$('texture-save').onclick=()=>textureProjectAction('/api/project/save',{});
    $('texture-clear').onclick=()=>textureProjectAction('/api/command',{type:'clear_texture_replacement',asset_id:record.id});
    $('texture-source').onclick=downloadOriginalTexture;$('texture-apply').onclick=applyTextureReplacement;
    $('texture-discard').onclick=()=>{$('texture-file').value='';$('texture-file-status').textContent='No replacement file selected.';updateTextureActions();};
    $('texture-file').onchange=()=>{const file=$('texture-file').files?.[0];if(file&&(!/\.tim$/i.test(file.name)||file.size<1||file.size>1048576)){$('texture-file').value='';$('texture-file-status').textContent='Choose a nonempty .tim file no larger than 1 MiB.';}else $('texture-file-status').textContent=file?`${file.name} · ${file.size} bytes · not applied`:'No replacement file selected.';updateTextureActions();};
    $('texture-layer').onchange=()=>openTexture(record,textureSession.paletteIndex,$('texture-layer').value);
    if(!textureDialog.open)textureDialog.showModal();
  }
  textureSession.paletteIndex=paletteIndex;textureSession.layer=layer;$('texture-layer').value=layer;
  setBusy(true);const request=++textureRequest,controller=new AbortController();textureAbort?.abort();textureAbort=controller;
  textureDialog.querySelector('.dialog-error').textContent='';$('texture-bitmap').width=1;$('texture-bitmap').height=1;$('texture-summary').textContent=`Verifying ${layer} texture palette ${paletteIndex}…`;textureDialog.querySelector('pre').textContent='';
  try{
    const response=await fetch('/api/texture-preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:record.id,palette_index:paletteIndex,...(state.capabilities?.texture_replacement?{layer}:{})}),signal:controller.signal});
    const result=await response.json();if(!response.ok||result.error)throw new Error(typeof result.error==='string'?result.error:'Texture decoding failed');
    if(request!==textureRequest||!textureDialog.open||key!==resourceStateKey())return;
    if(result.source_key!==state.scene_preview_source_key||result.scene_id!==state.scene?.id||result.semantic_id!==record.id||result.palette_index!==paletteIndex||(state.capabilities?.texture_replacement&&result.layer!==layer)||!Number.isInteger(result.width)||!Number.isInteger(result.height)||result.width<1||result.height<1||result.width*result.height>4194304||!Number.isInteger(result.palette_count)||result.palette_count<0||result.palette_count>4096||typeof result.rgba_base64!=='string'||result.rgba_base64.length>22369624)throw new Error('Texture service returned invalid or oversized pixels.');
    const bytes=Uint8ClampedArray.from(atob(result.rgba_base64),value=>value.charCodeAt(0));if(bytes.length!==result.width*result.height*4)throw new Error('Decoded texture dimensions do not match the pixel data.');
    texturePreview=result;const bitmap=$('texture-bitmap');bitmap.width=result.width;bitmap.height=result.height;bitmap.getContext('2d').putImageData(new ImageData(bytes,result.width,result.height),0,0);
    $('texture-summary').textContent=`${layer==='imported'?'Imported TIM':result.authored?'Effective authored TIM':'Effective imported TIM'} · ${result.width} × ${result.height} pixels · ${result.bpp} bpp${result.palette_count>0?' · '+result.palette_count+' palettes':''}`;
    $('texture-palette-label').hidden=result.palette_count<=1;$('texture-palette').replaceChildren();
    for(let index=0;index<result.palette_count;index++){const option=document.createElement('option');option.value=index;option.textContent=`Palette ${index}`;$('texture-palette').append(option);}
    $('texture-palette').value=paletteIndex;$('texture-palette').onchange=()=>openTexture(record,Number($('texture-palette').value),textureSession.layer);
    const {rgba_base64,stp_base64,...provenance}=result;textureDialog.querySelector('pre').textContent=JSON.stringify({...provenance,stp_flags_present:typeof stp_base64==='string',catalog_record:record.data},null,2);
  }catch(error){if(error.name!=='AbortError'&&textureDialog.open)textureDialog.querySelector('.dialog-error').textContent=error.message;}
  finally{if(textureAbort===controller)textureAbort=null;setBusy(false);}
}
async function textureProjectAction(route,body){
  if(busy||!textureSession)return;
  const session=textureSession;textureCommandPending=true;textureDialog.querySelector('.dialog-error').textContent='';
  try{if(await api(route,body)){if(textureDialog.open&&session.projectKey===textureProjectKey()){await openTexture(session.record,session.paletteIndex,session.layer);$('texture-file-status').textContent=state.project?.dirty?'No replacement file selected. Project changes are not saved.':'No replacement file selected. Project saved.';}}else textureDialog.querySelector('.dialog-error').textContent=$('status').textContent;}
  finally{textureCommandPending=false;updateTextureActions();}
}
async function applyTextureReplacement(){
  if(busy||!canEditTexture())return;
  const file=$('texture-file').files?.[0];if(!file||file.size<1||file.size>1048576||!/\.tim$/i.test(file.name))return;
  setBusy(true);textureDialog.querySelector('.dialog-error').textContent='';
  let encoded;
  try{encoded=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(',')[1]);reader.onerror=()=>reject(new Error('The selected TIM could not be read.'));reader.readAsDataURL(file);});}
  catch(error){textureDialog.querySelector('.dialog-error').textContent=error.message;return;}
  finally{setBusy(false);}
  const session=textureSession;textureCommandPending=true;
  try{if(await api('/api/texture-replacement',{asset_id:session.record.id,tim_base64:encoded})){$('texture-file').value='';$('texture-file-status').textContent=state.project?.dirty?'Replacement applied. Save the project to keep it.':'Replacement accepted. Project unchanged.';if(textureDialog.open&&session.projectKey===textureProjectKey())await openTexture(session.record,session.paletteIndex,'effective');}else textureDialog.querySelector('.dialog-error').textContent=$('status').textContent;}
  finally{textureCommandPending=false;updateTextureActions();}
}
async function downloadOriginalTexture(){
  if(busy||!textureSession)return;setBusy(true);textureDialog.querySelector('.dialog-error').textContent='';
  try{
    const response=await fetch('/api/texture-source',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:textureSession.record.id})}),result=await response.json();
    if(!response.ok||result.error)throw new Error(typeof result.error==='string'?result.error:'Original TIM download failed');
    if(typeof result.tim_base64!=='string'||result.tim_base64.length>1398104)throw new Error('Original TIM exceeds the supported download size.');
    const bytes=Uint8Array.from(atob(result.tim_base64),value=>value.charCodeAt(0));if(!bytes.length||bytes.length>1048576)throw new Error('Invalid original TIM size.');
    const filename=String(result.filename ?? 'original-texture.tim').split(/[\\/]/).at(-1),url=URL.createObjectURL(new Blob([bytes],{type:'application/octet-stream'})),link=document.createElement('a');link.href=url;link.download=filename;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    $('texture-file-status').textContent='Original TIM downloaded. Edit its pixels or palettes in a TIM-aware tool, keeping the source layout.';
  }catch(error){textureDialog.querySelector('.dialog-error').textContent=error.message;}
  finally{setBusy(false);}
}
const animationResourceDialog=document.createElement('dialog');animationResourceDialog.id='animation-resource-dialog';document.body.append(animationResourceDialog);
function animationPreviewChoices(record,actorEntities,modelReferences){
  const choices=[];
  for(const ref of initialAssetUsage(record,modelReferences)){
    const entity=actorEntities.find(actor=>actor.id===ref.source_id);
    if(!entity)continue;
    if(ref.imported)choices.push({key:entity.id+'|imported',entity,
      assetId:entity.components.ModelRenderer.asset_id,clipId:'scene-header',
      layer:ref.effective&&!entity.components.ActorAppearance?.authored?.donor_entity_id?'Imported + Effective':'Imported'});
    if(ref.effective&&entity.components.ActorAppearance?.authored?.donor_entity_id)choices.push({key:entity.id+'|authored',entity,
      assetId:entity.components.ActorAppearance.effective.asset_id,clipId:'authored-appearance',layer:'Authored effective'});
  }
  return choices;
}
function openAnimationResource(record){
  if(busy||resourceKey!==resourceStateKey())return;
  const data=record.data,candidates=animationPreviewChoices(record,entities(),state.model_references??[]);
  animationResourceDialog.innerHTML=`<div class="dialog-heading"><h2>${escapeHTML(record.label)}</h2><button id="close-animation-resource" aria-label="Close animation resource">×</button></div>${property('Stable ID',record.id)}${property('Frames',data.frame_count)}${property('Rigid channels',data.bone_count)}<p>Retail playback timing is unresolved. Choose an imported binding or an authored effective assignment; previews preserve that distinction.</p>${candidates.length?'<label>Actor assignment<select id="resource-animation-actor" aria-label="Animation actor"><option value="">Choose an actor assignment…</option></select></label><div class="dialog-actions"><button id="select-resource-actor" disabled>Select actor</button><button id="preview-resource-animation" class="accent" disabled>Preview animation</button></div>':'<p class="field-note">No verified actor assignment is available in the active scene. The record remains available for source inspection.</p>'}<details class="resource-provenance"><summary>Animation bindings, source and limits</summary><pre class="diagnostic-detail"></pre></details>`;
  $('close-animation-resource').onclick=()=>animationResourceDialog.close();animationResourceDialog.querySelector('pre').textContent=JSON.stringify(data,null,2);
  if(candidates.length){
    for(const candidate of candidates){const option=document.createElement('option');option.value=candidate.key;option.textContent=`${candidate.entity.name} · ${candidate.layer} · ${candidate.assetId.split('/').at(-1)}`;$('resource-animation-actor').append(option);}
    const choice=()=>candidates.find(candidate=>candidate.key===$('resource-animation-actor').value);
    $('resource-animation-actor').onchange=()=>{const missing=!choice();$('select-resource-actor').disabled=missing;$('preview-resource-animation').disabled=missing;};
    $('select-resource-actor').onclick=async()=>{const candidate=choice();if(candidate&&await api('/api/selection',{entity_id:candidate.entity.id})){animationResourceDialog.close();frame(selected());document.querySelector('.workspace-tabs [data-panel="viewport"]').click();}};
    $('preview-resource-animation').onclick=()=>{const candidate=choice();if(candidate){animationResourceDialog.close();openModel(candidate.assetId,candidate.clipId,candidate.entity.id);}};
  }
  animationResourceDialog.showModal();
}
const scriptResourceDialog=document.createElement('dialog');scriptResourceDialog.id='script-resource-dialog';document.body.append(scriptResourceDialog);
function resourceValue(value){return value===null||value===undefined?'Unknown':typeof value==='object'?JSON.stringify(value):String(value);}
function resourceLabel(value){return resourceValue(value).replaceAll('_',' ');}
function openScriptResource(record){
  if(record.authoredRecord&&record.type==='script'){activateAsset(record);return;}
  if(busy||resourceKey!==resourceStateKey())return;
  const data=record.data,actor=entities().find(entity=>entity.id===data.actor_semantic_id),dialogue=record.type==='dialogue';
  const scriptOwner=data.partition===2&&typeof data.owner_semantic_id==='string'?{id:data.owner_semantic_id,name:`Partition 2 script ${data.source_record?.record_index}`,partitionTwo:true}:actor;
  const status={decoded_supported_paths:'Supported paths decoded',partial:'Partial inspection',decoded_segment:'Decoded segment',unavailable:'Unavailable'}[data.status] ?? resourceLabel(data.status);
  scriptResourceDialog.innerHTML=`<div class="dialog-heading"><h2>${escapeHTML(record.label)}</h2><button id="close-script-resource" aria-label="Close script resource">×</button></div>${property('Stable ID',record.id)}${property(data.partition===2?'Script owner':'Actor',data.owner_semantic_id ?? data.actor_semantic_id)}${property('Source scene',record.source)}${property('Inspection',status)}${dialogue?`${property('Parent script status',data.script_status==='partial'?'Partial inspection':resourceLabel(data.script_status))}${property('Record offset',scriptOffset(data.pc))}${property('Source bytes',data.byte_length)}${property('Tokens',data.token_count)}${property('Text length',data.text_length)}<p>Catalog metadata contains no dialogue text. Open the verified script report to inspect this segment and any supported text runs.</p>`:`<div class="script-resource-counts">${property('Instructions',data.instruction_count)}${property('Dialogue segments',data.dialogue_count)}${property('Option menus',data.menu_count ?? 'Not cataloged')}${property('Opaque bytes',data.opaque_byte_count)}${property('Decoder stops',data.stop_count)}</div><p>Encoded references are read only. Runtime flag values, story-state reachability and actual scene transitions are not established by this catalog.</p><section id="resource-menus"><h3>Dialogue option menus</h3></section><section id="resource-flags"><h3>Flag references</h3></section><section id="resource-transitions"><h3>Encoded transitions</h3></section>`}<div class="dialog-actions"><button id="select-script-resource-actor" ${actor?'':'disabled'}>Select actor</button><button id="inspect-script-resource" class="accent" ${scriptOwner&&state.capabilities?.actor_script_preview?'':'disabled'}>${dialogue?'Inspect dialogue segment':'Inspect script'}</button></div>${scriptOwner?'':'<p class="field-note">The script owner is not available in the active scene.</p>'}<details class="resource-provenance"><summary>Source records, encoded fields and limitations</summary><pre class="diagnostic-detail"></pre></details>`;
  $('close-script-resource').onclick=()=>scriptResourceDialog.close();scriptResourceDialog.querySelector('.resource-provenance pre').textContent=JSON.stringify(data,null,2);
  $('select-script-resource-actor').onclick=async()=>{if(actor&&!busy&&await api('/api/selection',{entity_id:actor.id})){scriptResourceDialog.close();frame(selected());document.querySelector('.workspace-tabs [data-panel="viewport"]').click();}};
  $('inspect-script-resource').onclick=()=>{if(scriptOwner&&!busy){scriptResourceDialog.close();openActorScript(scriptOwner,false,null,dialogue?{semantic_id:record.id,pc:data.pc}:null);}};
  if(dialogue){
    const script=resourceRecords.find(item=>item.asset_kind==='script'&&item.semantic_id===data.script_id);
    if(script){const button=document.createElement('button');button.className='parent-script-button';button.textContent='View parent script metadata';button.onclick=()=>openScriptResource({id:script.semantic_id,type:'script',label:script.name ?? script.semantic_id,source:script.source_record?.prot_entry_name ?? record.source,data:script});scriptResourceDialog.querySelector('.dialog-actions').before(button);}
  }else{
    const menus=data.menus ?? [],menuHost=$('resource-menus');
    if(!menus.length){const note=document.createElement('p');note.textContent=Array.isArray(data.menus)?'No menus decoded in the inspected paths.':'Refresh the resource catalog to discover menus.';menuHost.append(note);}
    for(const menu of menus){
      const button=document.createElement('button');button.textContent=`Inspect ${menu.option_count}-option menu at ${scriptOffset(menu.pc)}`;
      button.disabled=!scriptOwner||!state.capabilities?.actor_script_preview;
      button.onclick=()=>{if(scriptOwner&&!busy){scriptResourceDialog.close();openActorScript(scriptOwner,false,null,null,menu.pc);}};
      menuHost.append(button);
    }
    const flags=data.flag_references ?? [],transitions=data.transitions ?? [];
    appendResourceTable($('resource-flags'),['Offset','Instruction','Bank / index','Operation','Scope / context','Interpretation'],flags.map(item=>[scriptOffset(item.pc),item.mnemonic,`${resourceLabel(item.bank)} / ${resourceValue(item.index)}`,resourceLabel(item.operation),`${resourceLabel(item.scope)}\n${item.context_resolution==='extended_target_unresolved'?`Extended target ${resourceValue(item.extended_target)} (unresolved)`:resourceLabel(item.context_resolution)}`,`${resourceLabel(item.status)}\n${resourceLabel(item.index_semantics)}`]),'No flag references were decoded in the inspected paths.');
    appendResourceTable($('resource-transitions'),['Offset','Instruction','Target scene label','Status','Encoded entry'],transitions.map(item=>[scriptOffset(item.pc),item.mnemonic,item.target_scene_name ?? 'Unresolved',`${resourceLabel(item.status)}\nReachability: ${resourceLabel(item.reachability)}`,`X ${resourceValue(item.entry_x_encoded)} / Z ${resourceValue(item.entry_z_encoded)} / direction ${resourceValue(item.direction_encoded)}`]),'No transitions were decoded in the inspected paths.');
  }
  if(!scriptResourceDialog.open)scriptResourceDialog.showModal();
}
function appendResourceTable(parent,headings,rows,empty){
  if(!rows.length){const note=document.createElement('p');note.className='field-note';note.textContent=empty;parent.append(note);return;}
  const wrap=document.createElement('div');wrap.className='script-table-wrap';const table=document.createElement('table'),header=document.createElement('thead'),labels=document.createElement('tr'),body=document.createElement('tbody');
  for(const heading of headings){const cell=document.createElement('th');cell.textContent=heading;labels.append(cell);}header.append(labels);
  for(const values of rows){const row=document.createElement('tr');for(const value of values){const cell=document.createElement('td');cell.textContent=resourceValue(value);row.append(cell);}body.append(row);}table.append(header,body);wrap.append(table);parent.append(wrap);
}
function property(label,value){return `<dl class="property"><dt>${escapeHTML(label)}</dt><dd>${escapeHTML(value ?? 'Unknown')}</dd></dl>`;}
function showTemplates(){renderTemplates();templateDialog.showModal();}
function renderTemplates(){
  const entity=selected(),position=entity?.components?.Transform?.authored?.position ?? {},templates=state.actor_templates ?? [];
  const appearance=entity?.components?.ActorAppearance?.authored?.donor_entity_id?entity.components.ActorAppearance.authored:null;
  const axes=Object.entries(position).map(([axis,value])=>`${axis.toUpperCase()} ${format(value)}`).join(' · ');
  templateDialog.innerHTML=`<div class="dialog-heading"><h2>Authored actor templates</h2><button type="button" id="close-templates" aria-label="Close">×</button></div><p>Capture authored position axes or a model-and-animation donor pair, then apply the preset to an existing imported actor.</p><p class="field-note">Appearance presets require a compatible actor in the donor scene and are reverified when applied. No native actor spawning. Height stays project-only; Build requires representable X/Z values.</p><form id="create-template-form"><label>Template name<input id="template-name" required maxlength="80" placeholder="For example, courtyard position" ${canEdit() && (axes||appearance)?'':'disabled'}></label><p class="field-note">${entity?`Selected: ${escapeHTML(entity.name)} · ${axes?escapeHTML(axes):appearance?`Appearance donor: ${escapeHTML(appearance.donor_entity_id)}`:'Author a position or appearance override to capture a template.'}`:'Select an imported actor to capture or apply a template.'}</p><button type="submit" ${canEdit() && axes?'':'disabled'}>Capture authored position</button><button type="button" id="capture-appearance-template" ${canEditAppearance() && appearance?'':'disabled'}>Capture authored appearance</button></form><div id="template-list" class="template-list"></div><p class="field-note">Template changes use Undo / Redo. Save the project to keep the library.</p>`;
  $('close-templates').onclick=()=>templateDialog.close();
  const errorMessage=document.createElement('p');errorMessage.className='dialog-error';errorMessage.setAttribute('role','alert');templateDialog.append(errorMessage);
  const command=async body=>{const result=await api('/api/command',body);if(!result)errorMessage.textContent=$('status').textContent;return result;};
  $('create-template-form').onsubmit=async event=>{event.preventDefault();await command({type:'create_actor_template',entity_id:entity.id,name:$('template-name').value});};
  $('capture-appearance-template').onclick=()=>command({type:'create_actor_template',capture:'appearance',entity_id:entity.id,name:$('template-name').value});
  for(const template of templates){
    const card=document.createElement('section');card.className='template-card';
    const application=template.application??{available:false,reason:'Preset eligibility is unavailable.'};
    const values=template.components.ActorAppearance?`Appearance donor: ${template.components.ActorAppearance.donor_entity_id}`:Object.entries(template.components.Transform.position).map(([axis,value])=>`${axis.toUpperCase()} ${format(value)}`).join(' · ');
    card.innerHTML=`<strong>${escapeHTML(template.name)}</strong><p>${escapeHTML(values)}</p><p class="field-note">${escapeHTML(application.reason)}</p><details><summary>Source provenance</summary><p>${escapeHTML(template.source.scene_id)}<br>${escapeHTML(template.source.entity_id)}</p><code>${escapeHTML(template.source.disc_identity)}</code></details><div class="template-actions"><button data-apply ${canEdit() && entity && application.available?'':'disabled'}>Apply to ${escapeHTML(entity?.name ?? 'selected actor')}</button><button data-delete ${canEdit()?'':'disabled'}>Delete</button></div>`;
    card.querySelector('[data-apply]').onclick=()=>command({type:'apply_actor_template',template_id:template.id,entity_id:entity.id});
    card.querySelector('[data-delete]').onclick=()=>command({type:'delete_actor_template',template_id:template.id});
    const rename=document.createElement('details');rename.innerHTML=`<summary>Rename preset</summary><form><label>New name for ${escapeHTML(template.name)}<input required maxlength="80" value="${escapeHTML(template.name)}" ${canEdit()?'':'disabled'}></label><button type="submit" ${canEdit()?'':'disabled'}>Save name</button></form>`;
    rename.querySelector('form').onsubmit=async event=>{event.preventDefault();await command({type:'rename_actor_template',template_id:template.id,name:rename.querySelector('input').value});};
    card.append(rename);
    $('template-list').append(card);
  }
  if(!templates.length)$('template-list').innerHTML='<p class="field-note">No authored actor templates yet.</p>';
}
function coordinateComparisonRows(transform,observed){
  return ['x','y','z'].map(axis=>{
    const imported=transform?.imported?.position?.[axis],effective=transform?.effective?.position?.[axis],sample=observed?.[axis];
    return {axis,imported:numeric(imported)?imported:null,effective:numeric(effective)?effective:null,
      observed:numeric(sample)?sample:null,delta:numeric(effective)&&numeric(sample)?sample-effective:null};
  });
}
function coordinateComparisonMarkup(entityId,observed){
  const transform=entities().find(entity=>entity.id===entityId)?.components?.Transform;
  const cell=value=>value===null?'Unknown':escapeHTML(String(value));
  return '<table class="coordinate-comparison"><caption>Guest world coordinates - sampled candidate</caption><thead><tr><th>Axis</th><th>Imported</th><th>Effective</th><th>Sampled</th><th>Sample - effective</th></tr></thead><tbody>'+coordinateComparisonRows(transform,observed).map(row=>`<tr><th>${row.axis.toUpperCase()}</th><td>${cell(row.imported)}</td><td>${cell(row.effective)}</td><td>${cell(row.observed)}</td><td>${cell(row.delta)}</td></tr>`).join('')+'</tbody></table><p class="field-note">Values use guest coordinates; the viewport flips Y for display. Unknown height is not zero. Deltas compare current runtime position with authored-effective placement, not a coordinate calibration. Scripts may relocate actors; candidate identity remains unconfirmed.</p>';
}
function runtimeCandidateSummary(correlation,entityId){
  const candidates=correlation.candidates??[];
  if(!candidates.length)return `<p class="field-note">${escapeHTML(correlation.reason??'No accepted candidate observation.')}</p>`;
  return candidates.map(candidate=>{
    const layers=(candidate.appearance_layers??[]).map(layer=>({imported:'Imported',effective:'Effective'})[layer]).filter(Boolean);
    const donor=candidate.effective_donor_id;
    const position=candidate.observed_position??{};
    return `<div class="appearance-layer"><h4>Unconfirmed runtime candidate</h4>${property('Captured node',candidate.runtime_node_id)}${property('Appearance match',layers.join(' + ')||'Not classified')}${donor&&donor!==entityId?property('Effective donor',donor):''}${property('Binding capture frame',candidate.frame)}${property('Position capture frames',candidate.position_capture_frames?`${candidate.position_capture_frames.before}–${candidate.position_capture_frames.after}`:'Unknown')}${property('Placement header matches imported X/Z',candidate.placement_header_agrees_with_import===true?'Yes':candidate.placement_header_agrees_with_import===false?'No':'Unknown')}${property('Captured placement header',`X ${format(candidate.placement_position?.x)} · Z ${format(candidate.placement_position?.z)}`)}${property('Captured world position',`X ${format(position.x)} · Y ${format(position.y)} · Z ${format(position.z)}`)}${coordinateComparisonMarkup(entityId,position)}<p class="field-note">Captured evidence only. Structural compatibility does not establish actor identity.</p></div>`;
  }).join('');
}
function renderInspector(){
  const environment=selectedEnvironment();
  if(environment){
    $('selection-summary').textContent=environment.name;
    const source=environment.source_record,transform=source.imported_transform;
    $('inspector').innerHTML=`<section class="component"><h3>Environment <small>Source and overrides</small></h3>${property('Identity',environment.entity_id)}${property('Model',environment.asset_id ?? 'Unresolved')}${property('Geometry',environment.renderable?environment.pose_kind:environment.reason ?? 'Unavailable')}<button id="frame-environment">Frame object</button></section><section class="component"><h3>Retail transform</h3>${property('Position',JSON.stringify(transform.position))}${property('Rotation · PSX units',JSON.stringify(transform.rotation_psx))}<p class="field-note">4096 angle units equal one turn. Source placement and initial pose; scripts and runtime visibility are not evaluated.</p></section><section class="component"><h3>Source and bindings</h3><pre>${escapeHTML(JSON.stringify({source,evidence:environment.evidence},null,2))}</pre></section>`;
    $('frame-environment').onclick=frameEnvironment;
    if(source.record_offset&&source.source_record?.map_sha256){
      const scopes=environment.entity_id.includes('/decorations/')?['shared','instance']:['shared'];
      for(const scope of scopes){
      const individual=scope==='instance',cell=(source.source_record.grid_byte_offset-0x8000)/2;
      const section=document.createElement('section');section.className='component';
      const title=document.createElement('h3');title.textContent=individual?'Individual decoration override':'Shared transform override';section.append(title);
      const note=document.createElement('p');note.className='field-note';note.textContent=individual?'Changes affect this decoration only and take precedence over shared values. Builds allocate an unused MAP record. In-game behavior has not been verified.':'Changes affect every instance using this placement record unless individually overridden. Saved in the project and included in builds. In-game behavior has not been verified.';section.append(note);
      const binding=activeScenePreview()?.environment_authoring;
      const shared=binding?.edits?.find(e=>e.record_index===source.object_record_index);
      const current=individual?binding?.instances?.find(e=>e.cell_index===cell):shared;
      const inputs=[];
      for(const [field,label,retail] of [['offset','Placement offset',source.record_offset],['rotation_psx','Rotation (4096 units per turn)',transform.rotation_psx]]){
        const base=individual?{...retail,...shared?.[field]}:retail;
        const heading=document.createElement('h4');heading.textContent=label;section.append(heading);
        for(const axis of ['x','y','z']){
          const row=document.createElement('label');row.textContent=`${axis.toUpperCase()} · ${individual?'inherited':'imported'} ${base[axis]} `;
          const input=document.createElement('input');input.type='number';input.step='1';input.min=field==='offset'?'-32768':'0';input.max=field==='offset'?'32767':'4095';input.value=current?.[field]?.[axis]??base[axis];input.setAttribute('aria-label',`${individual?'Individual ':''}${label} ${axis.toUpperCase()}`);input.disabled=state.project?.mode==='live'||!scenePreviewCurrent();row.append(input);section.append(row);inputs.push({field,axis,input,base:base[axis]});
        }
      }
      const effective=document.createElement('p');effective.textContent=`${scenePreviewCurrent()?'Effective position':'Previous preview position (refresh pending)'}: ${JSON.stringify(environment.effective_transform?.position??transform.position)}`;section.append(effective);
      const apply=document.createElement('button');apply.textContent=individual?'Apply individual transform':'Apply shared transform';apply.disabled=state.project?.mode==='live'||!scenePreviewCurrent();
      const inspectorKey=sceneKey;
      apply.onclick=async()=>{
        if(!scenePreviewCurrent()||sceneKey!==inspectorKey)return;
        const edit=individual?{cell_index:cell}:{record_index:source.object_record_index};
        for(const {field,axis,input,base} of inputs){if(!input.value.trim()||!input.checkValidity()){input.reportValidity();return;}const value=Number(input.value);if(value!==base)(edit[field]??={})[axis]=value;}
        const edits=(binding?.edits??[]).filter(e=>individual||e.record_index!==source.object_record_index);
        const instances=(binding?.instances??[]).filter(e=>!individual||e.cell_index!==cell);
        if(edit.offset||edit.rotation_psx)(individual?instances:edits).push(edit);
        await api('/api/command',edits.length||instances.length?{type:'set_environment_transforms',entity_id:state.scene.id,value:{source_sha256:source.source_record.map_sha256,edits,instances}}:{type:'clear_environment_transforms',entity_id:state.scene.id});
      };
      section.append(apply);$('inspector').insertBefore(section,$('inspector').lastElementChild);
      }
    }
    if(Number.isInteger(source.object_record_index)){
      const related=environmentEntities().filter(item=>item.source_record?.object_record_index===source.object_record_index);
      const section=document.createElement('section');section.className='component';
      const heading=document.createElement('h3');heading.textContent='Shared placement record';section.append(heading);
      const note=document.createElement('p');note.className='field-note';note.textContent=`${related.length} imported scene instance${related.length===1?'':'s'} use MAP record ${source.object_record_index}. Shared edits affect every grid use. Static decorations support individual overrides through a separately allocated record.`;section.append(note);
      if(Number.isInteger(source.source_record?.map_reference_count)){
        const count=document.createElement('p');count.className='field-note';count.textContent=`Total source grid references: ${source.source_record.map_reference_count}, including cells outside the preview visibility gates.`;section.append(count);
      }
      if(related.length>1){
        const select=document.createElement('select');select.setAttribute('aria-label','Instances sharing this placement record');
        for(const item of related){const option=document.createElement('option');option.value=item.entity_id;option.textContent=item.name;option.selected=item.entity_id===environment.entity_id;select.append(option);}
        select.onchange=()=>{selectEnvironment(select.value);frameEnvironment();};section.append(select);
      }
      $('inspector').insertBefore(section,$('inspector').lastElementChild);
    }
    return;
  }
  const entity=selected();
  $('selection-summary').textContent=entity?entity.name ?? entity.id:'No entity selected';
  if(!entity){$('inspector').innerHTML='<div class="empty-panel">Select an entity in the scene<br>or hierarchy to inspect it.</div>';return;}
  const components=entity.components ?? {}, transform=components.Transform ?? {}, original=transform.imported?.position ?? {}, override=transform.authored?.position ?? {}, effective=transform.effective?.position ?? original;
  let html=`<div class="entity-heading"><h2>${escapeHTML(entity.name ?? entity.id)}</h2><code>${escapeHTML(entity.id)}</code></div><section class="component"><h3>Transform <small>Scene units</small></h3><div class="transform-table"><span></span><span class="column-title">Imported</span><span class="column-title">Authored</span><span class="column-title">Effective</span>`;
  for(const axis of ['x','y','z'])html+=`<span class="axis-${axis}">${axis.toUpperCase()}</span><output title="${format(original[axis])}">${format(original[axis])}</output><input data-axis="${axis}" aria-label="Authored ${axis.toUpperCase()}" type="number" step="1" placeholder="—" value="${numeric(override[axis])?override[axis]:''}" ${canEdit()?'':'disabled'}><output class="effective">${format(effective[axis])}</output>`;
  html+='</div>'+((entity.components.Transform.build_issues ?? []).map(issue=>`<p class="script-warning">Build: ${escapeHTML(issue)}</p>`).join(''))+'<p class="field-note">Edits are project overrides. Empty authored fields inherit the imported value. Unknown heights use source terrain for preview when available, otherwise the ground plane. Scene display axes follow the SDK conversion.</p></section>';
  const actorPreview=scenePreviewCurrent()?activeScenePreview()?.entities.find(item=>item.entity_id===entity.id):null;
  if(actorPreview?.preview_ground_sample){html+=`<section class="component"><h3>Preview elevation <small>Derived, not authored</small></h3>${property('Guest Y',actorPreview.preview_position.y)}${property('Terrain cell',actorPreview.preview_ground_sample.cell_index)}<p class="field-note">Interpolated from the displayed source terrain. Runtime collision, ramps and script elevation may differ.</p></section>`;}
  else if(actorPreview?.preview_height_status==='unresolved_no_source_surface'){html+='<section class="component"><h3>Preview elevation <small>Unresolved</small></h3><p class="field-note">No displayed source-ground cell exists at this placement. The mesh uses the preview ground plane; this is not a measured game height. Inspect a live sample to compare runtime placement.</p></section>';}


  if(state.capabilities?.actor_appearance && components.ActorAppearance){const appearance=components.ActorAppearance,imported=appearance.imported ?? {},effective=appearance.effective ?? imported,donor=appearance.authored?.donor_entity_id;html+=`<section class="component appearance-component"><h3>Actor appearance <small>Model + animation pair</small></h3><div class="appearance-layer"><h4>Imported</h4>${property('Model',imported.asset_id)}${property('Animation ID',imported.animation_id)}</div><div class="appearance-layer"><h4>Authored override</h4>${property('Donor actor',donor ?? 'None · inherit imported appearance')}</div><div class="appearance-layer"><h4>Effective</h4>${property('Model',effective.asset_id)}${property('Animation ID',effective.animation_id)}</div><p class="field-note">Assign a verified donor pair to this existing actor. Script behavior and gameplay compatibility are not established by a matching model and animation.</p><button id="choose-appearance" class="model-preview-button" data-appearance-edit ${canEditAppearance()?'':'disabled'}>Choose donor appearance…</button>${donor?`<button id="clear-appearance" class="model-preview-button" data-appearance-edit ${canEditAppearance()?'':'disabled'}>Clear appearance override</button><button id="preview-appearance" class="model-preview-button">Preview authored appearance</button>`:''}<details><summary>Appearance evidence and limits</summary><pre>${escapeHTML(JSON.stringify(appearance,null,2))}</pre></details></section>`;}
  if(state.capabilities?.authored_transform_templates)html+='<section class="component"><h3>Authored templates <small>Position / appearance</small></h3><p class="field-note">Capture or apply saved position and appearance presets to this existing actor.</p><button id="inspect-templates">Open actor templates…</button></section>';
  if(components.ModelRenderer){const model=components.ModelRenderer;html+=`<section class="component"><h3>Model renderer <small>Imported reference</small></h3>${property('Asset',model.asset_id)}${property('Resolution',model.resolution_status)}<p class="field-note">Scene meshes use supported SDK poses. Unresolved objects stay as placement markers; individual assets can be inspected separately.</p>${model.asset_id?'<button id="inspect-model" class="model-preview-button">Inspect model objects</button>':''}</section>`;}
  if(components.Animation)html+=`<section class="component"><h3>Animation</h3>${property('Imported ID',components.Animation.imported_id)}<p class="field-note">${components.Animation.preview_support?.supported?'Imported association is eligible for decoding. Preview verifies the source; retail playback timing and live animation remain unknown.':escapeHTML(components.Animation.preview_support?.reason ?? 'No supported imported animation association is available for this actor.')}</p></section>`;
  if(components.RuntimeCorrelation){const correlation=components.RuntimeCorrelation;html+=`<section class="component"><h3>Runtime observation <small>Read only · sampled</small></h3>${property('Correlation',correlation.status ?? correlation.state ?? 'Unresolved')}<p class="field-note">Candidate associations preserve ambiguity. They do not replace imported or authored values.</p>${runtimeCandidateSummary(correlation,entity.id)}<details><summary>Epoch, candidates and evidence</summary><pre>${escapeHTML(JSON.stringify(correlation,null,2))}</pre></details></section>`;}
  if(components.RetailMetadata){const retail=components.RetailMetadata,source=retail.source_record;const summary=source&&typeof source==='object'?(source.prot_entry_name ?? source.scene ?? source.kind ?? 'Imported record'):source;html+=`<section class="component"><h3>Retail metadata <small>Read only</small></h3>${property('Source',summary)}<details><summary>Source, evidence and unresolved fields</summary><pre>${escapeHTML(JSON.stringify({source_record:source,claims:retail.claims,unresolved:retail.unresolved},null,2))}</pre></details></section>`;}
  if(state.capabilities?.actor_script_preview)html+=`<section class="component"><h3>Script and dialogue <small>${state.capabilities?.actor_dialogue_authoring?'Supported text edits':'Read only'}</small></h3><p class="field-note">Inspect decoded dialogue and supported instruction paths. ${state.capabilities?.actor_dialogue_authoring?'Eligible plain-text runs can be authored within their original byte capacity.':'Unknown instructions stop decoding.'}</p><button id="inspect-script" class="model-preview-button">Inspect script and dialogue</button></section>`;
  $('inspector').innerHTML=html;
  if($('choose-appearance'))$('choose-appearance').onclick=()=>openAppearanceOptions(entity);
  if($('clear-appearance'))$('clear-appearance').onclick=()=>api('/api/command',{type:'clear_actor_appearance',entity_id:entity.id});
  if($('preview-appearance'))$('preview-appearance').onclick=()=>openModel(components.ActorAppearance.effective.asset_id,'authored-appearance',entity.id);
  if($('inspect-script'))$('inspect-script').onclick=()=>openActorScript(entity);
  if($('inspect-model'))$('inspect-model').onclick=()=>openModel(components.ModelRenderer.asset_id);
  const animatedAsset=(state.assets ?? []).find(asset=>asset.id===components.ModelRenderer?.asset_id && asset.animation_support?.supported);
  const actorAnimation=components.Animation?.preview_support;
  if(actorAnimation?.supported && $('inspect-model')){const button=document.createElement('button');button.className='model-preview-button';button.textContent='Preview imported scene animation';button.title='Verify and decode this actor’s imported animation association';button.onclick=()=>openModel(components.ModelRenderer.asset_id,'scene-header',entity.id);$('inspect-model').after(button);}
  if(actorAnimation?.supported && $('inspect-model')){const button=document.createElement('button');button.className='model-preview-button';button.dataset.animationEdit='true';button.textContent=components.Animation?.authored_channels?'Edit authored animation channels':'Author animation channels';button.disabled=busy||state.project.mode!=='edit';button.onclick=()=>openAnimationChannels(entity);$('inspect-model').after(button);}
  if(animatedAsset && $('inspect-model')){const button=document.createElement('button');button.className='model-preview-button';button.textContent='Preview reference locomotion';button.title='Decoded idle/walk clips for this model; separate from the placement animation ID';button.onclick=()=>openModel(animatedAsset.id,'idle');$('inspect-model').after(button);}
  if($('inspect-templates'))$('inspect-templates').onclick=showTemplates;
  $('inspector').querySelectorAll('[data-axis]').forEach(input=>input.addEventListener('change',async()=>{
    const axis=input.dataset.axis;
    if(input.value===''){await api('/api/command',{type:'clear_transform',entity_id:entity.id,axes:[axis]});return;}
    const value=Number(input.value);if(!Number.isFinite(value)){notify('Transform values must be finite numbers.',true);renderInspector();return;}
    await api('/api/command',{type:'set_transform',entity_id:entity.id,position:{[axis]:value}});
  }));
}

const animationEditDialog=document.createElement('dialog');animationEditDialog.className='project-dialog';document.body.append(animationEditDialog);
async function openAnimationChannels(entity){
  if(busy||state.project.mode!=='edit')return;
  const context=JSON.stringify([state.project.path,state.scene?.id,entity.id]);
  const current=()=>animationEditDialog.open&&state.project.mode==='edit'&&JSON.stringify([state.project.path,state.scene?.id,state.selection?.entity_id])===context;
  animationEditDialog.innerHTML='<h2>Edit imported animation channels</h2><p>Verifying source…</p><button type="button">Close</button>';
  animationEditDialog.querySelector('button').onclick=()=>animationEditDialog.close();animationEditDialog.showModal();setBusy(true);
  try{
    const response=await fetch('/api/animation-authoring-options',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({entity_id:entity.id})});
    const result=await response.json();if(!response.ok||result.error)throw new Error(result.error||'Could not load animation channels');if(!current())return;
    const binding=result.binding,edits=result.authored?.edits??[];
    animationEditDialog.innerHTML=`<h2>Edit imported animation channels</h2><p>${escapeHTML(binding.semantic_id)}</p><p>Imported actors sharing this clip: ${escapeHTML((result.shared_actor_ids??[]).join(", "))}</p><p>Edits apply to the imported clip. Blank axes remove this actor’s contribution; other shared-clip edits still apply. Build patches the shared scene clip within its original compressed capacity. Other actors using that clip are affected. Conflicting overrides or edits that need relocation are rejected. In-game playback has not yet been verified.</p><form><label>Frame (zero based)<input name="frame" type="number" min="0" max="${binding.frame_count-1}" step="1" value="0" required></label><label>Rigid object (zero based)<input name="object" type="number" min="0" max="${binding.bone_count-1}" step="1" value="0" required></label><div class="animation-channel-fields"></div><p class="dialog-error" role="alert"></p><button type="submit">Apply channel override</button><button type="button" class="clear-animation">Clear this actor’s channel edits</button><button type="button" class="close-animation">Close</button></form>`;
    const form=animationEditDialog.querySelector('form'),fields=form.querySelector('.animation-channel-fields'),error=form.querySelector('[role="alert"]');
    for(const group of ['translation','rotation_psx'])for(const axis of ['x','y','z']){const limits=result[group],label=document.createElement('label');label.textContent=`${group==='translation'?'Translation':'Rotation (PSX units)'} ${axis.toUpperCase()}`;const input=document.createElement('input');input.name=`${group}_${axis}`;input.type='number';input.min=limits.minimum;input.max=limits.maximum;input.step=limits.step;input.placeholder='Retail';label.append(input);fields.append(label);}
    let channelRequest=0,channelDirty=false,channelFrame=0,channelObject=0;
    const discardChannel=document.createElement('button');discardChannel.type='button';discardChannel.textContent='Discard unapplied channel changes';discardChannel.disabled=true;fields.after(discardChannel);
    fields.querySelectorAll('input').forEach(input=>input.oninput=()=>{channelDirty=true;discardChannel.disabled=false;});
    const retail=document.createElement('p');retail.className='field-note';fields.before(retail);
    const refresh=async()=>{
      if(channelDirty){form.elements.frame.value=channelFrame;form.elements.object.value=channelObject;error.textContent='Apply or discard your channel changes before switching frames or objects.';return;}
      const request=++channelRequest,frame=Number(form.elements.frame.value),object=Number(form.elements.object.value);channelFrame=frame;channelObject=object;
      const edit=edits.find(e=>e.frame_index===frame&&e.object_index===object);
      for(const group of ['translation','rotation_psx'])for(const axis of ['x','y','z'])form.elements[`${group}_${axis}`].value=edit?.[group]?.[axis]??'';
      retail.textContent='Loading retail channel…';
      if(!form.elements.frame.checkValidity()||!form.elements.object.checkValidity()){retail.textContent='Choose a valid frame and object.';return;}
      try{const response=await fetch('/api/animation-channel-values',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({entity_id:entity.id,frame_index:frame,object_index:object})});const values=await response.json();if(!current()||request!==channelRequest)return;if(!response.ok||values.error)throw new Error(values.error||'Channel inspection failed');if(values.source_record_sha256!==binding.source_record.record_sha256)throw new Error('Retail animation source changed; reopen the editor.');retail.replaceChildren();for(const [layer,label] of [['retail','Retail'],['effective','Effective after applied shared edits']]){const row=document.createElement('div');row.textContent=`${label} · translation XYZ: ${['x','y','z'].map(a=>values[layer].translation[a]).join(' / ')} · rotation XYZ (PSX units): ${['x','y','z'].map(a=>values[layer].rotation_psx[a]).join(' / ')}`;retail.append(row);}const owners=document.createElement('div');owners.textContent=`Channel contributors: ${(values.contributors??[]).join(', ')||'None'}`;retail.append(owners);}catch(error){if(current()&&request===channelRequest)retail.textContent=String(error.message);}
    };
    form.elements.frame.oninput=refresh;form.elements.object.oninput=refresh;refresh();
    discardChannel.onclick=()=>{if(!current()||busy)return;channelDirty=false;discardChannel.disabled=true;error.textContent='';refresh();};
    const editedLabel=document.createElement('label');editedLabel.textContent='This actor’s applied channel edits';
    const editedSelect=document.createElement('select');editedSelect.setAttribute('aria-label','Jump to applied animation channel');
    const placeholder=document.createElement('option');placeholder.value='';placeholder.textContent=edits.length?`Choose one of ${edits.length} edited channels…`:'No applied channel edits';editedSelect.append(placeholder);
    for(const edit of [...edits].sort((a,b)=>a.frame_index-b.frame_index||a.object_index-b.object_index)){
      const option=document.createElement('option');option.value=JSON.stringify([edit.frame_index,edit.object_index]);
      const axes=['translation','rotation_psx'].flatMap(group=>Object.entries(edit[group]??{}).map(([axis,value])=>`${group==='translation'?'T':'R'}${axis.toUpperCase()}=${value}`));
      option.textContent=`Frame ${edit.frame_index} · object ${edit.object_index} · ${axes.join(', ')}`;editedSelect.append(option);
    }
    editedSelect.disabled=!edits.length;editedSelect.onchange=()=>{if(!editedSelect.value||!current())return;const [frame,object]=JSON.parse(editedSelect.value);form.elements.frame.value=frame;form.elements.object.value=object;refresh();};
    editedLabel.append(editedSelect);form.prepend(editedLabel);
    form.querySelector('.close-animation').onclick=()=>animationEditDialog.close();
    form.querySelector('.clear-animation').disabled=!edits.length;
    const apply=async command=>{if(busy||!current())return;if(!await api('/api/command',command,{dialog:animationEditDialog,success:'Animation override updated. Save project to persist.'}))error.textContent=$('status').textContent;};
    form.querySelector('.clear-animation').onclick=()=>apply({type:'clear_animation_channels',entity_id:entity.id});
    form.onsubmit=async event=>{event.preventDefault();if(!form.reportValidity())return;if(Number(form.elements.frame.value)!==channelFrame||Number(form.elements.object.value)!==channelObject){error.textContent='Channel selection changed; discard the draft and select the channel again.';return;}const edit={frame_index:Number(form.elements.frame.value),object_index:Number(form.elements.object.value)};for(const group of ['translation','rotation_psx'])for(const axis of ['x','y','z']){const input=form.elements[`${group}_${axis}`];if(input.value!=='')(edit[group]??={})[axis]=Number(input.value);}const next=edits.filter(e=>e.frame_index!==edit.frame_index||e.object_index!==edit.object_index);if(edit.translation||edit.rotation_psx)next.push(edit);await apply(next.length?{type:'set_animation_channels',entity_id:entity.id,value:{animation_id:binding.semantic_id,source_record_sha256:binding.source_record.record_sha256,edits:next}}:{type:'clear_animation_channels',entity_id:entity.id});};
  }catch(error){if(animationEditDialog.open)animationEditDialog.querySelector('p').textContent=String(error.message);}finally{setBusy(false);}
}
const appearanceDialog=document.createElement('dialog');appearanceDialog.id='appearance-dialog';document.body.append(appearanceDialog);
async function openAppearanceOptions(entity){
  if(busy||!canEditAppearance())return;setBusy(true);
  appearanceDialog.innerHTML=`<div class="dialog-heading"><h2>Choose donor appearance</h2><button id="close-appearance" aria-label="Close donor appearance">×</button></div><p>Target: ${escapeHTML(entity.name)}. Assign a model and animation together from a verified imported donor.</p><p class="field-note">The existing actor keeps its placement and script. Structural pairing does not prove that the actor’s behavior will work with the new appearance.</p><div id="appearance-options"><p>Verifying available donor pairs…</p></div><p class="dialog-error" role="alert"></p>`;
  $('close-appearance').onclick=()=>appearanceDialog.close();appearanceDialog.showModal();
  try{
    const response=await fetch('/api/actor-appearance-options',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({entity_id:entity.id})});
    const result=await response.json();if(!response.ok||result.error)throw new Error(typeof result.error==='string'?result.error:'Could not verify donor appearances');if(!appearanceDialog.open)return;
    if(!Array.isArray(result.options)||result.options.some(option=>typeof option.donor_entity_id!=='string'||typeof option.asset_id!=='string'))throw new Error('Appearance service returned an invalid donor list.');
    const options=result.options,available=result.supported&&options.length;
    $('appearance-options').innerHTML=available?'<form id="appearance-form"><label>Imported donor actor<select id="appearance-donor" required aria-label="Donor appearance"><option value="">Choose a verified donor…</option></select></label><div id="appearance-donor-details"></div><div class="dialog-actions"><button type="submit" id="apply-appearance" class="accent" data-appearance-edit data-unavailable="true" disabled>Apply donor appearance</button></div></form>':`<p>${escapeHTML(result.reason ?? 'No supported donor appearances are available for this actor.')}</p>`;
    const details=document.createElement('details');details.className='appearance-evidence';details.innerHTML='<summary>Verified options and limitations</summary><pre class="diagnostic-detail"></pre>';details.querySelector('pre').textContent=JSON.stringify(result,null,2);$('appearance-options').append(details);
    if(available){
      for(const option of options){const entry=document.createElement('option');entry.value=option.donor_entity_id;entry.textContent=`${option.label ?? option.donor_entity_id}${option.unchanged?' (same imported pair)':''}`;$('appearance-donor').append(entry);}
      const refresh=()=>{const option=options.find(item=>item.donor_entity_id===$('appearance-donor').value);$('apply-appearance').dataset.unavailable=String(!option);$('apply-appearance').disabled=busy||!canEditAppearance()||!option;$('appearance-donor-details').innerHTML=option?`${property('Donor ID',option.donor_entity_id)}${property('Model asset',option.asset_id)}${property('Animation ID',option.animation_id)}`:'';};
      $('appearance-donor').onchange=refresh;$('appearance-donor').value=entity.components.ActorAppearance?.authored?.donor_entity_id ?? '';refresh();
      $('appearance-form').onsubmit=async event=>{event.preventDefault();const donor=$('appearance-donor').value;if(options.some(option=>option.donor_entity_id===donor))await api('/api/command',{type:'set_actor_appearance',entity_id:entity.id,donor_entity_id:donor},{dialog:appearanceDialog,success:'Authored appearance assigned.'});};
    }
  }catch(error){if(appearanceDialog.open)appearanceDialog.querySelector('.dialog-error').textContent=error.message;}finally{setBusy(false);}
}

const scriptDialog=document.createElement('dialog');scriptDialog.id='script-dialog';document.body.append(scriptDialog);
let scriptEntity=null,scriptReport=null,scriptDrafts=new Map();
const scriptOffset=value=>Number.isInteger(value)?'0x'+value.toString(16).toUpperCase():'Unknown';
async function openActorScript(entity,refresh=false,focusRun=null,focusDialogue=null,focusInstruction=null){
  if(busy||(refresh&&!scriptDialog.open))return;const scroll=refresh?scriptDialog.scrollTop:0;setBusy(true);
  if(!refresh){scriptEntity=entity;scriptDrafts.clear();
  scriptDialog.innerHTML=`<div class="dialog-heading"><h2>Script and dialogue</h2><button id="close-script" aria-label="Close script inspection">×</button></div><p>${escapeHTML(entity.name)} · Instruction graph remains read only</p><div id="script-authoring-toolbar" class="script-authoring-toolbar" hidden><button id="script-undo">Undo</button><button id="script-redo">Redo</button><button id="script-save">Save project</button><span id="script-authoring-status"></span></div><div id="script-report"><p>Verifying the imported script record…</p></div><p class="dialog-error" role="alert"></p>`;
  $('close-script').onclick=()=>scriptDialog.close();scriptDialog.showModal();
  $('script-undo').onclick=()=>scriptProjectAction('/api/undo');$('script-redo').onclick=()=>scriptProjectAction('/api/redo');$('script-save').onclick=()=>scriptProjectAction('/api/project/save');
  }
  try{
    const response=await fetch(entity.triggerId?'/api/trigger-script':entity.partitionTwo?'/api/partition-two-script':'/api/actor-script',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(entity.triggerId?{asset_id:entity.triggerId}:{entity_id:entity.id})});
    let report=await response.json();if(!response.ok||report.error)throw new Error(typeof report.error==='string'?report.error:'Script inspection failed');
    if(entity.triggerId||entity.partitionTwo){if(report.script_id!==entity.id.replace(/^scene:\/\//,'script://')||report.scene_id!==state.scene?.id||report.source_key!==state.scene_preview_source_key)throw new Error('Script identity or source changed.');report={...report,...report.inspection};}
    if(!scriptDialog.open)return;
    if(report.read_only!==true||!Array.isArray(report.instructions)||!Array.isArray(report.dialogues))throw new Error('Script service returned an invalid inspection report.');
    const instructions=report.instructions,dialogues=report.dialogues,opaque=report.opaque_regions ?? [],stops=report.stops ?? [];
    $('script-report').innerHTML=`<p class="script-summary">${instructions.length} decoded instructions · ${dialogues.length} dialogue segments · ${report.status==='partial'?'Partial inspection':'Supported paths decoded'}</p><p class="field-note">Record offsets are relative to the script record. Decoded paths do not establish which branch runs in the game. Name substitutions remain explicit placeholders.</p><div id="script-warnings"></div><section><h3>Decoded dialogue</h3><div id="script-dialogue"></div></section><details class="script-instructions" ${dialogues.length?'':'open'}><summary>Instruction paths (${instructions.length})</summary><div class="script-table-wrap"><table><thead><tr><th>Record offset</th><th>Instruction</th><th>Operands</th><th>Successors</th></tr></thead><tbody></tbody></table></div></details><details class="script-raw"><summary>Source, raw bytes and decoder limits</summary><pre class="diagnostic-detail"></pre></details>`;
    if(opaque.length||stops.length){const warning=document.createElement('div');warning.className='script-warning';warning.textContent=`${opaque.length} opaque regions · ${stops.length} decoder stops. Unvisited bytes and unsupported behavior remain unresolved.`;$('script-warnings').append(warning);for(const region of opaque){const line=document.createElement('p');line.className='field-note';line.textContent=`${scriptOffset(region.pc)} · ${region.length} opaque bytes: ${region.reason}`;$('script-warnings').append(line);}for(const stop of stops){const line=document.createElement('p');line.className='field-note';line.textContent=`${scriptOffset(stop.pc)}: ${stop.reason}`;$('script-warnings').append(line);}}
    if(!dialogues.length)$('script-dialogue').textContent='No dialogue was decoded in the inspected paths.';
    for(const dialogue of dialogues){const card=document.createElement('article');card.className='script-dialogue-card';card.dataset.dialogueId=dialogue.semantic_id;card.dataset.dialoguePc=dialogue.pc;card.innerHTML=`<small>Imported segment · ${escapeHTML(scriptOffset(dialogue.pc))} · ${escapeHTML(dialogue.length)} bytes</small><p></p><details><summary>Text tokens and source span</summary><pre class="diagnostic-detail"></pre></details>`;card.querySelector('p').textContent=dialogue.text ?? '';card.querySelector('pre').textContent=JSON.stringify(dialogue,null,2);$('script-dialogue').append(card);}
    const instructionNavigation=appendScriptInstructions($('script-report').querySelector('.script-instructions > div'),report);

    $('script-report').querySelector('.script-raw pre').textContent=JSON.stringify(report,null,2);
    scriptReport=report;renderDialogueAuthoring();renderTransitionAuthoring();
    scriptDialog.scrollTop=scroll;
    if(Number.isInteger(focusInstruction)){
      $('script-report').querySelector('.script-instructions').open=true;
      if(!instructionNavigation.select(focusInstruction))notify('The selected instruction was not found in the verified report.',true);
    }
  }catch(error){if(scriptDialog.open){scriptDialog.querySelector('.dialog-error').textContent=error.message;if(refresh){scriptReport=null;scriptDialog.querySelectorAll('.dialogue-run,.transition-entry,.transition-unresolved,[data-clear-unresolved]').forEach(item=>item.remove());}}}finally{setBusy(false);if(focusRun&&scriptDialog.open){const input=[...scriptDialog.querySelectorAll('[data-run-input]')].find(item=>item.dataset.runInput===focusRun);if(input){if(focusRun.includes('/transition/'))input.scrollIntoView({block:'center'});input.focus({preventScroll:true});}}else if(focusDialogue&&scriptDialog.open){const cards=[...scriptDialog.querySelectorAll('.script-dialogue-card')],card=cards.find(item=>item.dataset.dialogueId===focusDialogue.semantic_id) ?? cards.find(item=>Number.isInteger(focusDialogue.pc)&&Number(item.dataset.dialoguePc)===focusDialogue.pc);if(card){card.classList.add('dialogue-focus');card.tabIndex=-1;card.scrollIntoView({block:'start'});card.focus({preventScroll:true});}else notify('The selected dialogue segment was not found in the verified report.',true);}}
}

function renderTransitionAuthoring(){
  const authoring=scriptReport?.transition_authoring;if(!authoring||(!authoring.transitions?.length&&!authoring.unresolved_overrides?.length))return;
  const section=document.createElement('section'),heading=document.createElement('h3'),note=document.createElement('p');
  heading.textContent='Transition entries';note.className='field-note';
  note.textContent='Edit encoded entry bytes (0–255). The preview decodes the retail entry format. Destination names remain fixed.';
  section.append(heading,note);$('script-report').append(section);
  for(const identifier of authoring.unresolved_overrides ?? []){
    const row=document.createElement('div'),label=document.createElement('code'),button=document.createElement('button');
    row.className='transition-unresolved';label.textContent=identifier;button.type='button';button.textContent='Clear unresolved transition';button.dataset.clearTransition=identifier;
    button.disabled=busy||!canEditDialogue();button.onclick=async()=>{if(busy||!canEditDialogue())return;
      if(await api('/api/command',{type:'clear_transition_entry',entity_id:scriptEntity.id,transition_id:identifier})){scriptDrafts.delete(identifier);await openActorScript(scriptEntity,true);}else scriptDialog.querySelector('.dialog-error').textContent=$('status').textContent;};
    row.append(label,button);section.append(row);
  }
  if(authoring.reason){const reason=document.createElement('p');reason.className='field-note';reason.textContent=authoring.reason;section.append(reason);}
  for(const entry of authoring.transitions ?? []){
    const form=document.createElement('form');form.className='transition-entry';
    const title=document.createElement('h4');title.textContent=`${entry.destination} at ${scriptOffset(entry.pc)}`;form.append(title);
    if(entry.effective_interpretation){const value=entry.effective_interpretation,preview=document.createElement('p');preview.className='field-note';preview.textContent=`Effective arrival: X ${value.x} / Z ${value.z} / facing ${value.facing_angle_12bit} (12-bit angle). Static retail interpretation; height and live arrival are not verified.`;form.append(preview);}
    const inputs={};
    for(const [field,label] of [['entry_x_encoded','Entry X'],['entry_z_encoded','Entry Z'],['direction_encoded','Direction']]){
      const row=document.createElement('label'),input=document.createElement('input');
      row.textContent=`${label} (imported ${entry.values[field]}) `;input.type='number';input.min='0';input.max='255';input.step='1';input.required=true;
      input.setAttribute('aria-label',`${label} at ${scriptOffset(entry.pc)}`);
      if(field==='entry_x_encoded')input.dataset.runInput=entry.semantic_id;
      input.value=scriptDrafts.get(entry.semantic_id)?.[field] ?? entry.effective_values[field];inputs[field]=input;row.append(input);form.append(row);
      input.oninput=()=>{scriptDrafts.set(entry.semantic_id,Object.fromEntries(Object.entries(inputs).map(([k,v])=>[k,v.value])));updateScriptActions();};
    }
    const apply=document.createElement('button'),clear=document.createElement('button'),discard=document.createElement('button');
    apply.type='submit';apply.textContent='Apply entry';clear.type=discard.type='button';clear.textContent='Clear entry override';discard.textContent='Discard draft';form.append(apply,clear,discard);
    form.updateState=()=>{const editable=!busy&&canEditDialogue()&&!scriptDrafts.has(entry.semantic_id+'/arrival');form.title=scriptDrafts.has(entry.semantic_id+'/arrival')?'Apply or discard the arrival draft before editing encoded bytes.':'';for(const input of Object.values(inputs))input.disabled=!editable;apply.disabled=!editable||!Object.values(inputs).every(i=>i.value!==''&&Number.isInteger(Number(i.value))&&Number(i.value)>=0&&Number(i.value)<=255);clear.disabled=!editable||!Object.keys(entry.authored_values).length;discard.disabled=busy;discard.hidden=!scriptDrafts.has(entry.semantic_id);};
    const send=async(type)=>{if(busy||!canEditDialogue()||scriptDrafts.has(entry.semantic_id+'/arrival'))return;const command={type,entity_id:scriptEntity.id,transition_id:entry.semantic_id};if(type==='set_transition_entry')command.values=Object.fromEntries(Object.entries(inputs).map(([k,v])=>[k,Number(v.value)]));
      if(await api('/api/command',command)){scriptDrafts.delete(entry.semantic_id);await openActorScript(scriptEntity,true);}else scriptDialog.querySelector('.dialog-error').textContent=$('status').textContent;};
    form.onsubmit=e=>{e.preventDefault();if(!apply.disabled)send('set_transition_entry');};clear.onclick=()=>send('clear_transition_entry');discard.onclick=()=>{scriptDrafts.delete(entry.semantic_id);for(const [field,input] of Object.entries(inputs))input.value=entry.effective_values[field];updateScriptActions();};
    section.append(form);form.updateState();
    if(entry.effective_interpretation){
      const arrival=document.createElement('form');arrival.className='transition-entry';const title=document.createElement('h4');title.textContent='Arrival coordinates';arrival.append(title);
      const draftKey=entry.semantic_id+'/arrival',base={x:entry.effective_interpretation.x,z:entry.effective_interpretation.z,facing_sector:entry.effective_values.direction_encoded&7},fields={};
      for(const [key,label] of [['x','Arrival X'],['z','Arrival Z'],['facing_sector','Facing sector']]){
        const row=document.createElement('label'),input=document.createElement('input');row.textContent=label;input.type='number';input.required=true;input.min=key==='facing_sector'?'0':'64';input.max=key==='facing_sector'?'7':'16384';input.step=key==='facing_sector'?'1':'64';input.value=scriptDrafts.get(draftKey)?.[key] ?? base[key];input.setAttribute('aria-label',`${label} at ${scriptOffset(entry.pc)}`);fields[key]=input;row.append(input);arrival.append(row);
        input.oninput=()=>{scriptDrafts.set(draftKey,Object.fromEntries(Object.entries(fields).map(([k,v])=>[k,v.value])));updateScriptActions();};
      }
      const apply=document.createElement('button'),discard=document.createElement('button'),note=document.createElement('p');apply.type='submit';apply.textContent='Apply arrival';discard.type='button';discard.textContent='Discard arrival draft';note.className='field-note';note.textContent='X/Z use exact 64-unit steps. Facing sectors 0–7 select 512-unit angle steps; other direction bits are preserved. Height is unchanged.';arrival.append(apply,discard,note);
      arrival.updateState=()=>{const editable=!busy&&canEditDialogue()&&!scriptDrafts.has(entry.semantic_id);arrival.title=scriptDrafts.has(entry.semantic_id)?'Apply or discard the encoded-byte draft before editing arrival coordinates.':'';for(const input of Object.values(fields))input.disabled=!editable;apply.disabled=!editable||!Object.values(fields).every(input=>input.value!==''&&input.checkValidity());discard.disabled=busy;discard.hidden=!scriptDrafts.has(draftKey);};
      discard.onclick=()=>{scriptDrafts.delete(draftKey);for(const [key,input] of Object.entries(fields))input.value=base[key];updateScriptActions();};
      arrival.onsubmit=async event=>{event.preventDefault();if(apply.disabled)return;const values=Object.fromEntries(Object.entries(fields).map(([k,v])=>[k,Number(v.value)]));if(await api('/api/command',{type:'set_transition_arrival',entity_id:scriptEntity.id,transition_id:entry.semantic_id,arrival:values})){scriptDrafts.delete(draftKey);await openActorScript(scriptEntity,true,entry.semantic_id);}else scriptDialog.querySelector('.dialog-error').textContent=$('status').textContent;};
      section.append(arrival);arrival.updateState();
    }
  }
}

function canEditDialogue(){return state.capabilities?.actor_dialogue_authoring===true && (state.project?.mode ?? 'edit').toLowerCase()==='edit';}
function updateScriptActions(){
  $('script-authoring-toolbar').hidden=!state.capabilities?.actor_dialogue_authoring;
  const pending=scriptDrafts.size>0;
  $('script-undo').disabled=busy||pending||!canEditDialogue()||!state.history?.can_undo;
  $('script-redo').disabled=busy||pending||!canEditDialogue()||!state.history?.can_redo;
  $('script-save').disabled=busy||pending||!state.project?.dirty;
  $('script-authoring-status').textContent=pending?`${scriptDrafts.size} unapplied draft(s) · Apply or discard before project actions`:busy?'Verifying…':projectSaveStatus();
  for(const form of scriptDialog.querySelectorAll('.dialogue-run'))updateDialogueRun(form);
  for(const form of scriptDialog.querySelectorAll('.transition-entry'))form.updateState();
  for(const button of scriptDialog.querySelectorAll('[data-clear-unresolved],[data-clear-transition]'))button.disabled=busy||!canEditDialogue();
}
function updateDialogueRun(form){
  const run=form.run,input=form.querySelector('textarea'),text=input.value,capacity=run.max_length;
  const validCapacity=Number.isInteger(capacity)&&capacity>=0&&capacity<=4096;
  const characters=/^[\x20-\x7e]*$/.test(text)&&!text.includes('^');
  const valid=validCapacity&&characters&&text.length<=capacity;
  const error=!validCapacity?'The source capacity is unavailable.':!characters?'Use printable ASCII only. Caret (^), line breaks and control characters are unsupported.':text.length>capacity?`Too long: ${text.length} bytes exceeds ${capacity} source bytes.`:'';
  input.disabled=busy||!canEditDialogue();input.setAttribute('aria-invalid',String(!valid));
  form.querySelector('.run-counter').textContent=error||`${text.length} / ${capacity} bytes · ${capacity-text.length} space padding bytes after Apply`;
  form.querySelector('.run-counter').classList.toggle('invalid',!valid);
  form.querySelector('.run-apply').disabled=busy||!canEditDialogue()||!valid||text===run.authored_text;
  form.querySelector('.run-clear').disabled=busy||!canEditDialogue()||run.authored_text===null||run.authored_text===undefined;
  form.querySelector('.run-discard').hidden=!scriptDrafts.has(run.semantic_id);form.querySelector('.run-discard').disabled=busy;
}
async function scriptProjectAction(route){
  if(busy||scriptDrafts.size)return;
  scriptDialog.querySelector('.dialog-error').textContent='';
  if(await api(route,{}))await openActorScript(scriptEntity,true);
  else scriptDialog.querySelector('.dialog-error').textContent=$('status').textContent;
}
async function dialogueCommand(run,type,text){
  if(busy||!canEditDialogue())return;
  const command={type,entity_id:scriptEntity.id,run_id:run.semantic_id,...(type==='set_dialogue_text'?{text}:{})};
  scriptDialog.querySelector('.dialog-error').textContent='';
  if(await api('/api/command',command)){scriptDrafts.delete(run.semantic_id);await openActorScript(scriptEntity,true,run.semantic_id);}
  else scriptDialog.querySelector('.dialog-error').textContent=$('status').textContent;
}
function renderDialogueAuthoring(){
  const authoring=scriptReport?.dialogue_authoring;
  if(!state.capabilities?.actor_dialogue_authoring||!authoring){updateScriptActions();return;}
  const note=document.createElement('div');note.className='dialogue-authoring-note';
  note.textContent=authoring.supported?'Supported plain-text runs can be replaced within their source byte capacity. Shorter text is padded with spaces; empty text becomes all spaces. Controls and substitutions stay unchanged. Apply each draft before Save; unapplied drafts are discarded when this dialog is reopened.':authoring.reason ?? 'This actor has no supported text runs for authoring.';
  $('script-dialogue').before(note);
  const evidence=document.createElement('details');evidence.className='dialogue-authoring-evidence';evidence.innerHTML='<summary>Text authoring source and limits</summary><pre class="diagnostic-detail"></pre>';evidence.querySelector('pre').textContent=JSON.stringify({source:authoring.source,limitations:authoring.limitations,unresolved_overrides:authoring.unresolved_overrides},null,2);note.after(evidence);
  if(authoring.unresolved_overrides?.length){const warning=document.createElement('div');warning.className='unresolved-dialogue';const text=document.createElement('p');text.className='dialog-error';text.textContent=`${authoring.unresolved_overrides.length} stored text overrides could not be resolved. They can be cleared without changing the imported record.`;warning.append(text);for(const identifier of authoring.unresolved_overrides){const row=document.createElement('div'),label=document.createElement('code'),button=document.createElement('button');label.textContent=identifier;button.textContent='Clear unresolved override';button.dataset.clearUnresolved=identifier;button.onclick=()=>dialogueCommand({semantic_id:identifier},'clear_dialogue_text');row.append(label,button);warning.append(row);}evidence.after(warning);}
  if(!authoring.supported){updateScriptActions();return;}
  for(const run of authoring.runs ?? []){
    const parent=[...$('script-dialogue').querySelectorAll('.script-dialogue-card')].find(card=>card.dataset.dialogueId===run.dialogue_id) ?? $('script-dialogue');
    const form=document.createElement('form');form.className='dialogue-run';form.run=run;
    form.innerHTML=`<h4>Text run ${escapeHTML(scriptOffset(run.pc))} <small>${escapeHTML(run.max_length)} source bytes</small></h4><div class="run-layer"><span>Imported</span><pre class="run-imported"></pre></div><label class="run-layer"><span>Authored replacement</span><textarea rows="2" spellcheck="false" aria-label="Authored text at ${escapeHTML(scriptOffset(run.pc))}" placeholder="No override. Empty text applied here becomes spaces."></textarea></label><div class="run-counter" role="status"></div><div class="run-actions"><button type="submit" class="run-apply accent">Apply text</button><button type="button" class="run-clear">Clear override</button><button type="button" class="run-discard" hidden>Discard draft</button></div><div class="run-layer"><span>Effective after Apply</span><pre class="run-effective"></pre></div><p class="run-effective-note field-note"></p>`;
    form.querySelector('.run-imported').textContent=run.text ?? '';
    const input=form.querySelector('textarea');input.dataset.runInput=run.semantic_id;input.value=scriptDrafts.has(run.semantic_id)?scriptDrafts.get(run.semantic_id):run.authored_text ?? '';
    form.querySelector('.run-effective').textContent=run.effective_text ?? 'Unavailable';
    form.querySelector('.run-effective-note').textContent=run.validation_error ?? (run.authored_text===null?'No authored override; effective text inherits the imported run.':`${Math.max(0,run.max_length-(run.authored_text?.length ?? 0))} trailing spaces are retained in the effective source bytes.`);
    input.oninput=()=>{if(input.value===(run.authored_text ?? ''))scriptDrafts.delete(run.semantic_id);else scriptDrafts.set(run.semantic_id,input.value);updateScriptActions();};
    form.onsubmit=event=>{event.preventDefault();if(!form.querySelector('.run-apply').disabled)dialogueCommand(run,'set_dialogue_text',input.value);};
    form.querySelector('.run-clear').onclick=()=>dialogueCommand(run,'clear_dialogue_text');
    form.querySelector('.run-discard').onclick=()=>{scriptDrafts.delete(run.semantic_id);input.value=run.authored_text ?? '';updateScriptActions();};
    parent.append(form);
  }
  updateScriptActions();
}

function frame(entity){
  const points=entity?[position(entity)]:(sceneLayers.actors?entities().map(position):[]);
  const hasMesh=sceneModelsReady()&&(!entity||sceneRenderer.hasEntity(entity.id));
  if(hasMesh)points.push(...sceneRenderer.bounds(sceneView().positions,entity?.id,hiddenSceneEntities()));
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
function observedCandidatePoints(){
  const epoch=acceptedEpoch(state.runtime),correlation=state.runtime_correlation;
  if(state.project?.mode!=='live'||!epoch||correlation?.available!==true||correlation.epoch_id!==epoch)return [];
  const candidates=selected()?.components?.RuntimeCorrelation?.candidates;
  if(!Array.isArray(candidates))return [];
  return candidates.slice(0,128).filter(candidate=>candidate?.epoch_id===epoch&&['x','y','z'].every(axis=>numeric(candidate.observed_position?.[axis]))).map(candidate=>displayPosition(candidate.observed_position));
}
function drawRuntimeNodeLayer(){
  runtimeNodeHits=[];
  if(!showObservedNodes)return;
  const epoch=acceptedEpoch(state.runtime),correlation=state.runtime_correlation;
  if(state.project?.mode!=='live'||!epoch||correlation?.available!==true||correlation.epoch_id!==epoch)return;
  const nodes=(correlation.runtime_nodes??[]).slice(0,128).filter(node=>node.epoch_id===epoch&&['x','y','z'].every(axis=>numeric(node.observed_position?.[axis])));
  ctx.save();ctx.strokeStyle='#79d5e8';ctx.fillStyle='#79d5e8';ctx.lineWidth=1.5;ctx.font='11px "Segoe UI",sans-serif';
  for(const node of nodes){const point=project(displayPosition(node.observed_position));if(!point||!numeric(point.x)||!numeric(point.y))continue;runtimeNodeHits.push({x:point.x,y:point.y,id:node.runtime_node_id,epoch});ctx.beginPath();ctx.moveTo(point.x,point.y-5);ctx.lineTo(point.x+5,point.y);ctx.lineTo(point.x,point.y+5);ctx.lineTo(point.x-5,point.y);ctx.closePath();ctx.stroke();}
  ctx.fillText(`${nodes.length} sampled runtime positions · Alt-click to inspect · includes occluded nodes`,12,78);ctx.restore();
}
function drawObservedCandidates(){
  const points=observedCandidatePoints();if(!points.length)return;
  ctx.save();ctx.strokeStyle='#cea9fa';ctx.fillStyle='#d7bcfa';ctx.lineWidth=1.5;ctx.font='11px "Segoe UI",sans-serif';
  for(const [index,world] of points.entries()){
    const p=project(world);if(!p||!numeric(p.x)||!numeric(p.y))continue;
    ctx.beginPath();ctx.arc(p.x,p.y,7,0,Math.PI*2);ctx.stroke();ctx.beginPath();ctx.moveTo(p.x-10,p.y);ctx.lineTo(p.x+10,p.y);ctx.moveTo(p.x,p.y-10);ctx.lineTo(p.x,p.y+10);ctx.stroke();
    ctx.fillText(`Observed candidate${points.length>1?` ${index+1}/${points.length} · ambiguous`:''} · sampled`,p.x+13,p.y+13);
  }
  ctx.restore();
}
function drawEnvironmentSelection(){
  const item=selectedEnvironment();
  if(!item||!sceneModelsReady()||hiddenSceneEntities().has(item.entity_id))return;
  const corners=sceneRenderer.bounds(sceneView().positions,item.entity_id);
  if(corners.length!==8)return;
  ctx.save();
  // A dashed bounds overlay identifies the selection without implying that
  // occluded edges are visible surfaces or that this is editable collision.
  ctx.setLineDash([5,3]);
  for(let corner=0;corner<8;corner++)for(const bit of [1,2,4]){
    if(!(corner&bit))line(corners[corner],corners[corner|bit],'#f4ce83',1.5);
  }
  ctx.setLineDash([]);
  const center=corners.reduce((p,c)=>({x:p.x+c.x/8,y:p.y+c.y/8,z:p.z+c.z/8}),{x:0,y:0,z:0});
  const label=project(center);
  if(label){ctx.font='11px "Segoe UI",sans-serif';ctx.fillStyle='#f4ce83';ctx.fillText(item.name,label.x+10,label.y-12);}
  ctx.restore();
}
function draw(){
  if(!ctx)return;ctx.clearRect(0,0,width,height);projected=[];handles=[];
  if(sceneModelsReady()){try{sceneRenderer.draw(sceneView());}catch(error){sceneError=error.message;}}
  updateSceneBadge();frameSamplesButton.disabled=observedCandidatePoints().length===0;
  const runtimeEpoch=acceptedEpoch(state.runtime),runtimeCorrelation=state.runtime_correlation;
  pickRuntimeButton.disabled=state.project?.mode!=='live'||!runtimeEpoch||runtimeCorrelation?.available!==true||runtimeCorrelation.epoch_id!==runtimeEpoch;
  if(pickRuntimeButton.disabled&&pickRuntimeNodes){pickRuntimeNodes=false;pickRuntimeButton.setAttribute('aria-pressed','false');}

  if(grid&&!sceneModelsReady()){const spacing=10**Math.floor(Math.log10(camera.distance/7)),half=spacing*12,cx=Math.round(camera.target.x/spacing)*spacing,cz=Math.round(camera.target.z/spacing)*spacing;for(let i=-12;i<=12;i++){line({x:cx+i*spacing,y:0,z:cz-half},{x:cx+i*spacing,y:0,z:cz+half},i===0?'#39504f88':'#33474c66');line({x:cx-half,y:0,z:cz+i*spacing},{x:cx+half,y:0,z:cz+i*spacing},i===0?'#39504f88':'#33474c66');}}
  drawFieldMap();
  const items=entities().map(entity=>{const world=draft?.id===entity.id?draft.position:position(entity);return {entity,world,p:project(world)};}).filter(item=>item.p).sort((a,b)=>b.p.depth-a.p.depth);
  for(const {entity,world,p} of items){
    if(!sceneLayers.actors)continue;
    const active=!selectedEnvironment()&&entity.id===state.selection?.entity_id,rendered=sceneModelsReady()&&sceneRenderer.hasEntity(entity.id),radius=active?7:4.5;
    if(rendered&&!active)continue;
    projected.push({id:entity.id,x:p.x,y:p.y});ctx.beginPath();ctx.ellipse(p.x,p.y+5,active?12:7,active?4:2.5,0,0,Math.PI*2);ctx.fillStyle='#02090966';ctx.fill();
    ctx.beginPath();ctx.moveTo(p.x,p.y-radius);ctx.lineTo(p.x+radius,p.y);ctx.lineTo(p.x,p.y+radius);ctx.lineTo(p.x-radius,p.y);ctx.closePath();ctx.fillStyle=active?'#c9edce':authored(entity)?'#d2ae70':'#759d8d';ctx.fill();ctx.strokeStyle=active?'#f1fff0':'#a8c6b6';ctx.lineWidth=active?1.5:1;ctx.stroke();
    if(active){
      ctx.font='11px "Segoe UI", sans-serif';ctx.fillStyle='#c8ddd1';ctx.fillText(entity.name ?? entity.id,p.x+12,p.y-10);
      if(Object.keys(entity.components?.Transform?.authored?.position??{}).length||draft?.id===entity.id){
        const original=displayPosition(entity.components?.Transform?.imported?.position),q=project(original);
        if(q&&Math.hypot(q.x-p.x,q.y-p.y)>3){ctx.save();ctx.setLineDash([4,4]);line(original,world,'#d6ad6c',1.5);ctx.setLineDash([]);ctx.strokeStyle='#d6ad6c';ctx.strokeRect(q.x-4,q.y-4,8,8);ctx.fillStyle='#e7c188';ctx.fillText('Imported',q.x+8,q.y+14);ctx.restore();}
      }
      if(canEdit()){const length=camera.distance*.085;for(const [axis,color] of [['x','#e0988a'],['z','#8bbbdc']]){const end={...world,[axis]:world[axis]+length},q=project(end);if(!q)continue;line(world,end,color,2);ctx.fillStyle=color;ctx.beginPath();ctx.arc(q.x,q.y,4,0,Math.PI*2);ctx.fill();ctx.font='bold 10px "Segoe UI",sans-serif';ctx.fillText(axis.toUpperCase(),q.x+7,q.y+3);handles.push({axis,x:q.x,y:q.y,start:p});}}
    }
  }
  drawEnvironmentSelection();drawCoordinateProbe();
  const scenery=selectedEnvironment(),movable=movableSelection();
  if(scenery&&movable&&canEdit()){
    const world=draft?.id===movable.id?draft.position:position(movable),p=project(world),length=camera.distance*.085;
    if(p)for(const [axis,color] of [['x','#e0988a'],['z','#8bbbdc']]){
      const end={...world,[axis]:world[axis]+length},q=project(end);if(!q)continue;
      line(world,end,color,2);ctx.fillStyle=color;ctx.beginPath();ctx.arc(q.x,q.y,4,0,Math.PI*2);ctx.fill();
      ctx.font='bold 10px "Segoe UI",sans-serif';ctx.fillText(axis.toUpperCase(),q.x+7,q.y+3);handles.push({axis,x:q.x,y:q.y,start:p});
    }
  }
  drawRuntimeNodeLayer();drawObservedCandidates();
}
function resize(){const rect=canvas.getBoundingClientRect(),dpr=window.devicePixelRatio||1;width=rect.width;height=rect.height;canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);draw();}
new ResizeObserver(resize).observe(canvas);
function pointer(event){const r=canvas.getBoundingClientRect();return {x:event.clientX-r.left,y:event.clientY-r.top};}
canvas.addEventListener('contextmenu',event=>event.preventDefault());
function cancelViewportGesture(){
  if(!drag)return;
  const pointerId=drag.pointerId;drag=null;draft=null;canvas.classList.remove('dragging');
  if(canvas.hasPointerCapture(pointerId))canvas.releasePointerCapture(pointerId);
  $('transform-drag-status').textContent='Move cancelled';draw();
}
function transformGestureCurrent(gesture){
  const entity=movableSelection();
  return canEdit()&&entity?.id===gesture.entity&&gesture.context===resourceStateKey()&&
    ['x','y','z'].every(axis=>position(entity)[axis]===gesture.original[axis]);
}
window.addEventListener('blur',cancelViewportGesture);
document.addEventListener('visibilitychange',()=>{if(document.hidden)cancelViewportGesture();});
canvas.addEventListener('pointerdown',event=>{
  if(busy||drag)return;const p=pointer(event),entity=movableSelection();canvas.focus();canvas.setPointerCapture(event.pointerId);
  const handle=event.button===0 && entity && canEdit()?handles.find(h=>Math.hypot(h.x-p.x,h.y-p.y)<12):null;
  drag={pointerId:event.pointerId,context:resourceStateKey(),start:p,last:p,moved:false,type:handle?'transform':event.button===2||event.button===1||event.shiftKey?'pan':'orbit',handle,entity:entity?.id,original:entity?position(entity):null,snapStep:$('transform-snap').checked?Number($('transform-snap-step').value):1};
  if(handle)drag.ground=groundAt(p.x,p.y,drag.original.y);
  canvas.classList.add('dragging');
});
canvas.addEventListener('pointermove',event=>{
  if(!drag||event.pointerId!==drag.pointerId)return;const p=pointer(event),dx=p.x-drag.last.x,dy=p.y-drag.last.y;
  if(Math.hypot(p.x-drag.start.x,p.y-drag.start.y)>3)drag.moved=true;
  if(drag.moved){
    if(drag.type==='transform'){const point=groundAt(p.x,p.y,drag.original.y);if(point&&drag.ground){const axis=drag.handle.axis;draft={id:drag.entity,position:{...drag.original,[axis]:snappedTransformCoordinate(drag.original[axis]+point[axis]-drag.ground[axis],drag.snapStep)}};}}
    else if(drag.type==='orbit'){camera.yaw-=dx*.006;camera.pitch=Math.max(.12,Math.min(1.42,camera.pitch+dy*.005));cameraRevision++;}
    else {const b=basis(),scale=camera.distance/Math.max(1,Math.min(width,height)*.9);camera.target.x-=dx*scale*b.right.x;camera.target.z-=dx*scale*b.right.z;camera.target.x-=dy*scale*Math.sin(camera.yaw)/Math.max(.15,Math.sin(camera.pitch));camera.target.z-=dy*scale*Math.cos(camera.yaw)/Math.max(.15,Math.sin(camera.pitch));cameraRevision++;}
    if(draft&&drag.type==='transform')$('transform-drag-status').textContent=`${drag.handle.axis.toUpperCase()} ${format(draft.position[drag.handle.axis])} · ${drag.snapStep>1?`Snap ${drag.snapStep} units`:'Free move'} · Release to apply`;
    draw();
  }
  drag.last=p;
});
canvas.addEventListener('pointerup',async event=>{
  if(!drag||event.pointerId!==drag.pointerId)return;
  if(drag.type==='transform'&&(busy||!transformGestureCurrent(drag))){cancelViewportGesture();return;}
  const finished=drag,p=pointer(event),edit=draft;drag=null;draft=null;canvas.classList.remove('dragging');$('transform-drag-status').textContent='X/Z moves · snap aligns to scene origin';
  if(finished.type==='transform' && edit){const axis=finished.handle.axis;if(edit.position[axis]!==finished.original[axis]){if(finished.entity.startsWith('environment://'))await moveDecoration(finished.entity,axis,edit.position[axis]);else await api('/api/command',{type:'set_transform',entity_id:finished.entity,position:{[axis]:edit.position[axis]}});}}
  else if(!finished.moved && event.button===0){
    if((event.altKey||pickRuntimeNodes)&&showObservedNodes&&state.project?.mode==='live'){
      const epoch=acceptedEpoch(state.runtime),correlation=state.runtime_correlation;
      if(epoch&&correlation?.available===true&&correlation.epoch_id===epoch){
        const hits=runtimeNodeHits.filter(hit=>hit.epoch===epoch&&Math.hypot(hit.x-p.x,hit.y-p.y)<9);
        if(hits.length){renderObservedNodes('',hits.map(hit=>hit.id));draw();return;}
        if(pickRuntimeNodes){notify('No sampled runtime node at this point');draw();return;}
      }
    }

    // Resolve the frontmost visible mesh before overlay markers. Otherwise a
    // projected actor behind scenery steals a click on the scenery surface.
    let hit=null;
    if(sceneModelsReady()){try{hit=sceneRenderer.pick(p.x,p.y,sceneView());}catch(error){notify(error.message,true);}}
    if(!hit)hit=[...projected].reverse().find(item=>Math.hypot(item.x-p.x,item.y-p.y)<12)?.id;
    if(hit){if(environmentEntities().some(e=>e.entity_id===hit))selectEnvironment(hit);else{environmentSelection=null;await api('/api/selection',{entity_id:hit});}}
  }
  draw();
});
canvas.addEventListener('pointercancel',event=>{if(event.pointerId===drag?.pointerId)cancelViewportGesture();});
canvas.addEventListener('lostpointercapture',event=>{if(event.pointerId===drag?.pointerId)cancelViewportGesture();});
canvas.addEventListener('wheel',event=>{event.preventDefault();camera.distance=Math.max(20,Math.min(1e8,camera.distance*Math.exp(event.deltaY*.001)));cameraRevision++;draw();},{passive:false});

// Unposed assets stay object-local. Only decoder-provided frames assemble objects.
const modelCanvas=$('model-canvas'), modelContext=modelCanvas.getContext('2d');
const exportDialog=document.createElement('dialog');document.body.append(exportDialog);
let model=null, modelDrag=null, modelRequest=0;
let modelTextures=new Map();
let modelAssetId=null, modelEntityId=null, animationFrame=0, animationTick=null, animationClock=null;
const modelView={yaw:.55,pitch:-.18,zoom:1,center:[0,0,0],radius:1};
async function openModel(assetId,clipId=null,entityId=null){
  if(busy)return;stopAnimation();setBusy(true);$('model-error').textContent='';$('animation-clip').disabled=true;const request=++modelRequest;
  try{
    const response=await fetch(entityId?(clipId==='authored-appearance'?'/api/actor-appearance-preview':'/api/actor-animation-preview'):clipId?'/api/animation-preview':'/api/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(entityId?{entity_id:entityId,...(clipId==='authored-channels'?{representation:'authored'}:{})}:{asset_id:assetId,...(clipId?{clip_id:clipId}:{})})});
    const data=await response.json();if(!response.ok||data.error)throw new Error(typeof data.error==='string'?data.error:JSON.stringify(data.error ?? data));
    if(!Array.isArray(data.vertices)||!Array.isArray(data.triangles)||!Array.isArray(data.objects))throw new Error('Model service returned no decoded geometry.');
    if(request!==modelRequest)return;
    if(clipId && (!Array.isArray(data.frames) || !data.frames.length || data.frames.length*data.vertices.length>1000000 || data.frames.some(frame=>frame.coordinate_system!=='retail_psx_actor_local_y_down'||!Array.isArray(frame.vertices)||frame.vertices.length!==data.vertices.length||frame.vertices.some(v=>!Array.isArray(v)||v.length!==3||!v.every(numeric)))))throw new Error('Animation service returned an invalid or oversized posed vertex stream.');
    model=data;modelAssetId=assetId;modelEntityId=entityId;animationFrame=0;$('model-dialog').querySelector('h2').textContent=entityId?`${entities().find(entity=>entity.id===entityId)?.name ?? entityId} · ${clipId==='authored-appearance'?'Authored appearance':clipId==='authored-channels'?'Authored animation':'Imported animation'}`:assetId.split('/').slice(-2).join(' / ');
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
$('animation-clip').onchange=()=>{const clip=$('animation-clip').value || null;openModel(modelAssetId,clip,['scene-header','authored-appearance','authored-channels'].includes(clip)?modelEntityId:null);};
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
  const clip=model.animation?.clip_id,payload=modelEntityId?{entity_id:modelEntityId,frame_index:animationFrame,...(clip==='authored-channels'?{representation:'authored'}:{})}:{asset_id:modelAssetId,...(clip?{clip_id:clip,frame_index:animationFrame}:{})};
  try{
    const response=await fetch(modelEntityId?(clip==='authored-appearance'?'/api/export/actor-appearance':'/api/export/actor-animation'):'/api/export/model',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
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
