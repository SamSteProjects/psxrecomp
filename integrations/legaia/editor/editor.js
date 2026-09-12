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
const camera = {projection:'perspective',yaw:-0.65,pitch:0.66,distance:2000,target:{x:0,y:0,z:0}};
let width=1, height=1, projected=[], handles=[], drag=null, draft=null, pendingEntityFrame=null;
let sceneRepresentation="authored";
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

let scenePose=null;
let scriptTargetOverlay=null,scriptTargetHits=[],pickScriptTargets=false;
const scriptTargetTools=document.createElement('div');scriptTargetTools.id='script-target-tools';scriptTargetTools.hidden=true;
scriptTargetTools.innerHTML='<span role="status"></span><select aria-label="Script target instruction"></select><button type="button" data-inspect>Inspect target</button><button type="button" data-pick aria-pressed="false">Pick script target</button><button type="button" data-frame>Frame script targets</button><button type="button" data-clear>Clear script targets</button>';
$('viewport-wrap').before(scriptTargetTools);
scriptTargetTools.querySelector('[data-clear]').onclick=()=>{scriptTargetOverlay=null;draw();};
scriptTargetTools.querySelector('[data-frame]').onclick=()=>frameScriptTargets();
scriptTargetTools.querySelector('[data-inspect]').onclick=()=>inspectScriptTarget(Number(scriptTargetTools.querySelector('select').value));
scriptTargetTools.querySelector('[data-pick]').onclick=()=>{cancelViewportGesture();pickScriptTargets=!pickScriptTargets;draw();};
async function inspectScriptTarget(pc){
  const overlay=currentScriptTargets();if(busy||!overlay||!overlay.targets.some(target=>target.pc===pc))return;
  const id=overlay.identity.replace(/^script:\/\//,'scene://');
  const owner=id.includes('/scripts/man-p2/')?{id,name:overlay.identity,partitionTwo:true}:entities().find(entity=>entity.id===id);
  if(!owner){notify('The source script owner is unavailable. Reopen its script report.',true);return;}
  cancelViewportGesture();await openActorScript(owner,false,null,null,pc);
}
function currentScriptTargets(){
  if(scriptTargetOverlay&&scriptTargetOverlay.key!==resourceStateKey())scriptTargetOverlay=null;
  return scriptTargetOverlay;
}
function frameScriptTargets(){
  const overlay=currentScriptTargets();if(!overlay||busy)return;
  cancelViewportGesture();
  const points=overlay.targets.map(target=>displayPosition({...target.position,y:overlay.height}));
  const min={},max={};for(const axis of ['x','y','z']){min[axis]=Math.min(...points.map(p=>p[axis]));max[axis]=Math.max(...points.map(p=>p[axis]));camera.target[axis]=(min[axis]+max[axis])/2;}
  camera.distance=Math.max(800,Math.hypot(max.x-min.x,max.y-min.y,max.z-min.z)*1.5);cameraRevision++;draw();
}
function drawScriptTargets(){
  scriptTargetHits=[];
  const overlay=currentScriptTargets();scriptTargetTools.hidden=!overlay;
  if(!overlay)pickScriptTargets=false;
  scriptTargetTools.querySelector('[data-pick]').setAttribute('aria-pressed',String(pickScriptTargets));
  if(!overlay)return;
  scriptTargetTools.querySelector('[role="status"]').textContent=`${overlay.identity} · ${overlay.representation??'retail'} targets · ${overlay.targets.length} decoded targets · reference Y ${overlay.height} · ${overlay.partial?'partial paths':'inspected paths'} · execution unknown`;
  const labels=[],markerPoints=overlay.targets.map(target=>project(displayPosition({...target.position,y:overlay.height}))).filter(Boolean);let hiddenLabels=0;
  ctx.save();ctx.strokeStyle='#e9abff';ctx.fillStyle='#e9abff';ctx.lineWidth=2;ctx.font='11px "Segoe UI",sans-serif';
  for(const target of overlay.targets){
    const p=project(displayPosition({...target.position,y:overlay.height}));if(!p)continue;
    const hit={pc:target.pc,x:p.x,y:p.y};scriptTargetHits.push(hit);
    ctx.strokeRect(p.x-6,p.y-6,12,12);
    const context=target.context===null||target.context===undefined?'':` · context ${target.context} unresolved`;
    const title=`${scriptOffset(target.pc)} ${target.mnemonic}${target.parked?' · parked':''}${context}`,coordinates=`X ${target.position.x} · Z ${target.position.z}`;
    const box={x:Math.max(4,Math.min(p.x+10,width-ctx.measureText(title).width-12)),y:p.y-21,w:Math.max(ctx.measureText(title).width,ctx.measureText(coordinates).width)+8,h:32};
    let fits=false;
    for(let attempt=0;attempt<32;attempt++){
      box.y=p.y-21+(attempt===0?0:(attempt%2?1:-1)*Math.ceil(attempt/2)*36);
      if(box.y>=0&&box.y+box.h<=height&&!markerPoints.some(marker=>marker.x+8>box.x&&marker.x-8<box.x+box.w&&marker.y+8>box.y&&marker.y-8<box.y+box.h)&&!labels.some(other=>box.x<other.x+other.w&&box.x+box.w>other.x&&box.y<other.y+other.h&&box.y+box.h>other.y)){fits=true;break;}
    }
    if(!fits){hiddenLabels++;continue;}
    hit.label={...box};
    labels.push(box);ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(box.x,box.y+box.h/2);ctx.stroke();ctx.lineWidth=2;
    ctx.fillStyle='#101b20ed';ctx.fillRect(box.x,box.y,box.w,box.h);ctx.fillStyle='#e9abff';
    ctx.fillText(title,box.x+4,box.y+12);ctx.fillText(coordinates,box.x+4,box.y+27);
  }
  ctx.restore();
  if(hiddenLabels)scriptTargetTools.querySelector('[role="status"]').textContent+=` · ${hiddenLabels} labels hidden at this zoom`;
}
let coordinateProbe=null,locateSample=null,locateGeneration=0;
const locateButton=document.createElement('button');locateButton.textContent='Locate coordinates';$('frame-selected').after(locateButton);
const locateDialog=document.createElement('dialog');locateDialog.className='project-dialog';locateDialog.innerHTML='<form><h2>Locate guest coordinates</h2><p>Place a reference marker using game coordinates. This changes only the editor camera.</p><label>X <input name="x" type="number" step="any" required></label><label>Y <input name="y" type="number" step="any" required value="0"></label><label>Z <input name="z" type="number" step="any" required></label><button type="button" data-surface>Use source surface height</button><p data-surface-status role="status"></p><button type="submit">Locate</button><button type="button" data-clear>Clear marker</button><button type="button" data-close>Cancel</button></form>';document.body.append(locateDialog);
locateButton.onclick=()=>locateDialog.showModal();
locateDialog.addEventListener('close',()=>{locateGeneration++;locateSample=null;locateDialog.querySelector('[data-surface-status]').textContent='';});
locateDialog.querySelectorAll('input').forEach(input=>input.addEventListener('input',()=>{locateGeneration++;locateSample=null;locateDialog.querySelector('[data-surface-status]').textContent='';}));
locateDialog.querySelector('[data-surface]').onclick=async()=>{
  if(busy)return;
  const button=locateDialog.querySelector('[data-surface]'),status=locateDialog.querySelector('[data-surface-status]');
  const x=Number(locateDialog.querySelector('[name="x"]').value),z=Number(locateDialog.querySelector('[name="z"]').value);
  if(['x','z'].some(axis=>!locateDialog.querySelector(`[name="${axis}"]`).value.trim())||![x,z].every(v=>Number.isFinite(v)&&v>=0&&v<=16384)){status.textContent='Enter X/Z from 0 through 16384 to sample the source surface.';return;}
  const generation=++locateGeneration,key=state.scene_preview_source_key,context=JSON.stringify([state.project?.path,state.scene?.id]);
  locateSample=null;setBusy(true);button.disabled=true;status.textContent='Sampling source terrain…';
  try{
    const response=await fetch('/api/terrain-point',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({x,z,source_key:key})}),result=await response.json();
    if(generation!==locateGeneration||!locateDialog.open||context!==JSON.stringify([state.project?.path,state.scene?.id])||key!==state.scene_preview_source_key)return;
    if(!response.ok)throw new Error(result.error||'Terrain sampling failed');
    if(result.source_key!==key||result.scene_id!==state.scene?.id||result.position?.x!==x||result.position?.z!==z)throw new Error('Terrain sample context differs from the requested point');
    if(result.position.y===null){status.textContent='No source surface covers this point. Enter a reference Y manually.';return;}
    if(!Number.isFinite(result.position.y))throw new Error('Invalid source height');
    locateDialog.querySelector('[name="y"]').value=result.position.y;locateSample={x,z,y:result.position.y};
    status.textContent=`Source surface Y ${result.position.y}; runtime elevation is unverified.`;
  }catch(error){if(generation===locateGeneration)status.textContent=error.message;}finally{button.disabled=false;setBusy(false);}
};

locateDialog.querySelector('[data-close]').onclick=()=>locateDialog.close();
locateDialog.querySelector('[data-clear]').onclick=()=>{coordinateProbe=null;locateDialog.close();draw();};
locateDialog.querySelector('form').onsubmit=event=>{
  event.preventDefault();const point={};for(const axis of ['x','y','z']){const input=locateDialog.querySelector(`[name="${axis}"]`);point[axis]=Number(input.value);if(!input.value.trim()||!Number.isFinite(point[axis]))return;}
  coordinateProbe={point,sampleEvidence:!!locateSample&&["x","y","z"].every(axis=>locateSample[axis]===point[axis]),context:JSON.stringify([state.project?.path,state.scene?.id])};cancelViewportGesture();camera.target=displayPosition(point);camera.distance=1000;cameraRevision++;locateDialog.close();draw();
};
function drawCoordinateProbe(){
  if(!coordinateProbe||coordinateProbe.context!==JSON.stringify([state.project?.path,state.scene?.id]))return;
  if(coordinateProbe.epoch&&(state.project?.mode!=='live'||acceptedEpoch(state.runtime)!==coordinateProbe.epoch||state.runtime_correlation?.available!==true||state.runtime_correlation.epoch_id!==coordinateProbe.epoch))return;
  const world=displayPosition(coordinateProbe.point),p=project(world);if(!p)return;
  ctx.save();ctx.strokeStyle='#ffda78';ctx.fillStyle='#ffda78';ctx.lineWidth=2;ctx.beginPath();ctx.arc(p.x,p.y,9,0,Math.PI*2);ctx.moveTo(p.x-15,p.y);ctx.lineTo(p.x+15,p.y);ctx.moveTo(p.x,p.y-15);ctx.lineTo(p.x,p.y+15);ctx.stroke();ctx.font='12px "Segoe UI",sans-serif';const v=coordinateProbe.point;ctx.fillText(`${coordinateProbe.epoch?'Captured node':coordinateProbe.sampleEvidence?'Source surface':'Reference'} X ${v.x} Y ${v.y} Z ${v.z}`,p.x+18,p.y-12);ctx.restore();
}

const frameSamplesButton=document.createElement('button');frameSamplesButton.textContent='Frame live samples';frameSamplesButton.disabled=true;frameSamplesButton.title='Frame all accepted-epoch candidates for the selected actor without changing authored placement';$('frame-selected').after(frameSamplesButton);
frameSamplesButton.onclick=()=>{
  const points=observedCandidatePoints();if(!points.length)return;
  cancelViewportGesture();
  const min={},max={};for(const axis of ['x','y','z']){min[axis]=Math.min(...points.map(p=>p[axis]));max[axis]=Math.max(...points.map(p=>p[axis]));camera.target[axis]=(min[axis]+max[axis])/2;}
  camera.distance=Math.max(800,Math.hypot(max.x-min.x,max.y-min.y,max.z-min.z)*1.5);cameraRevision++;draw();
};

let sceneHidden=new Set(),sceneHiddenScope=null;
function hiddenSceneEntities(){
  const scope=JSON.stringify([state.project?.path,state.scene?.id]);
  if(scope!==sceneHiddenScope){sceneHidden.clear();sceneHiddenScope=scope;}
  return new Set([...sceneHidden,...(activeScenePreview()?.entities??[]).filter(e=>!sceneLayers[e.kind!=='environment'?'actors':e.entity_id.endsWith('/ground')?'ground':'scenery']).map(e=>e.entity_id)]);
}
function visibilitySelection(){return environmentSelection??npcDraftSelection??state.selection?.entity_id;}
for(const [id,label,sameModel] of [['hide-selected','Hide selected',false],['hide-model','Hide model instances',true],['show-hidden','Show hidden',null]]){
  const button=document.createElement('button');button.id=id;button.textContent=label;
  button.title='Temporary viewport visibility only; does not edit or export the scene';
  button.onclick=()=>{
    hiddenSceneEntities();
    if(sameModel===null)sceneHidden.clear();
    else{
      const identifier=visibilitySelection();if(!identifier)return;
      const item=activeScenePreview()?.entities.find(e=>e.entity_id===identifier);
      if(sameModel){if(!item?.asset_id)return;for(const e of activeScenePreview().entities)if(e.asset_id===item.asset_id)sceneHidden.add(e.entity_id);}
      else if(sceneHidden.has(identifier))sceneHidden.delete(identifier);else sceneHidden.add(identifier);
    }
    cancelViewportGesture();renderHierarchy();draw();
  };
  $('frame-all').before(button);
}
for(const [layer,label] of Object.entries({actors:'Actors',scenery:'Scenery',ground:'Ground'})){
  const button=document.createElement('button');button.textContent=label;button.className='active';button.setAttribute('aria-pressed','true');button.title=`Show ${label.toLowerCase()} in the scene view`;
  button.onclick=()=>{sceneLayers[layer]=!sceneLayers[layer];button.classList.toggle('active',sceneLayers[layer]);button.setAttribute('aria-pressed',String(sceneLayers[layer]));cancelViewportGesture();renderHierarchy();draw();};
  $('frame-all').before(button);
}
const sceneExportButton=document.createElement('button');sceneExportButton.id='scene-export-glb';sceneExportButton.textContent='Export scene GLB';sceneExportButton.title='Export the complete source scene, including temporarily hidden instances; static reference poses';$('frame-all').after(sceneExportButton);
const selectedExportButton=document.createElement('button');selectedExportButton.id='scene-export-selected';selectedExportButton.textContent='Export selected GLB';selectedExportButton.title='Export one selected instance at its scene position';sceneExportButton.after(selectedExportButton);
sceneExportButton.onclick=()=>exportSceneGlb();
selectedExportButton.onclick=()=>{const id=visibilitySelection();if(!id){notify('Select an actor or scenery instance first.',true);return;}exportSceneGlb(id);};
async function exportSceneGlb(entityId=null){
  if(busy)return;
  if(!scenePreviewCurrent()||!state.scene_preview_source_key){notify('Wait for a current scene preview before exporting.',true);return;}
  if(scenePose||shapeDraft){notify('Restore the scene pose and finish or discard model edits before exporting.',true);return;}
  cancelViewportGesture();const key=sceneRequestKey();setBusy(true);sceneExportButton.disabled=true;selectedExportButton.disabled=true;
  try{
    const response=await fetch('/api/export/scene',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({representation:sceneRepresentation,source_key:state.scene_preview_source_key,...(entityId?{entity_id:entityId}:{})})}),result=await response.json();
    if(!response.ok||result.error)throw new Error(result.error??'Scene export failed');
    if(key!==sceneRequestKey()){notify('Scene export completed for the previous scene; reopen its project Exports folder.');return;}
    exportDialog.innerHTML=`<div class="dialog-heading"><h2>Scene exported</h2><button type="button">Close</button></div><p>${result.audit.entity_count} instances · ${result.audit.geometry_count} shared geometries · ${result.audit.unavailable_entities.length} metadata-only instances</p><p>${result.audit.export_scope==='selected-instance'?'Selected instance at its scene placement.':`Complete ${escapeHTML(result.audit.representation)} scene, including temporarily hidden instances.`} Static reference poses and source units; runtime visibility, lighting and physical scale are unverified.</p><label>Private GLB file<input readonly value="${escapeHTML(result.path)}"></label><details><summary>Source provenance and limitations</summary><pre>${escapeHTML(JSON.stringify(result.audit,null,2))}</pre></details>`;
    exportDialog.querySelector('button').onclick=()=>exportDialog.close();exportDialog.showModal();
  }catch(error){notify(error.message,true);}finally{sceneExportButton.disabled=false;selectedExportButton.disabled=false;setBusy(false);}
};
const projectionSelect=document.createElement('select');projectionSelect.id='scene-projection';projectionSelect.setAttribute('aria-label','Scene projection');projectionSelect.innerHTML='<option value="perspective">Perspective</option><option value="orthographic">Orthographic</option>';$('frame-all').before(projectionSelect);
projectionSelect.onchange=()=>{cancelViewportGesture();pendingEntityFrame=null;camera.projection=projectionSelect.value;document.querySelector('.viewport-type').textContent=projectionSelect.selectedOptions[0].textContent;cameraRevision++;draw();};
const topViewButton=document.createElement('button');topViewButton.id='scene-top-view';topViewButton.textContent='Top (X/Z)';topViewButton.title='Orthographic top view: +X right, +Z down; camera only';$('frame-all').before(topViewButton);
topViewButton.onclick=()=>{cancelViewportGesture();pendingEntityFrame=null;camera.projection='orthographic';projectionSelect.value='orthographic';document.querySelector('.viewport-type').textContent='Orthographic';camera.yaw=0;camera.pitch=Math.PI/2;cameraRevision++;draw();};
const modelToggle=document.createElement('button');modelToggle.id='scene-model-toggle';modelToggle.textContent='Models';modelToggle.className='active';modelToggle.setAttribute('aria-pressed','true');modelToggle.hidden=true;$('frame-all').before(modelToggle);
modelToggle.onclick=()=>{if(sceneError){sceneFailedKey=null;sceneKey=null;scenePreview=null;sceneError=null;modelsEnabled=true;}else modelsEnabled=!modelsEnabled;modelToggle.classList.toggle('active',modelsEnabled);modelToggle.setAttribute('aria-pressed',modelsEnabled);refreshScenePreview();draw();};
const representationSelect=document.createElement('select');representationSelect.id='scene-representation';representationSelect.setAttribute('aria-label','Scene representation');representationSelect.innerHTML='<option value="authored">Authored scene</option><option value="retail">Retail scene · comparison</option>';$('frame-all').before(representationSelect);
representationSelect.onchange=()=>{sceneRepresentation=representationSelect.value;if(sceneRepresentation==='retail'){collisionLayer.value='imported';clearFieldMap();updateFieldToggle();}cancelViewportGesture();pendingEntityFrame=null;npcDraftSelection=null;environmentSelection=null;sceneAbort?.abort();scenePreview=null;sceneKey=null;scenePendingKey=null;sceneFailedKey=null;sceneError=null;sceneRenderer?.clear();renderHierarchy();renderInspector();refreshScenePreview();draw();notify(sceneRepresentation==='retail'?'Retail scene comparison. Viewport movement is disabled; the Inspector retains authored project values.':'Authored scene restored.');};
function sceneRequestKey(){return state.scene_preview_source_key?`${state.scene_preview_source_key}|${sceneRepresentation}`:null;}
const sceneSelect=document.createElement('select');sceneSelect.className='scene-selector';sceneSelect.setAttribute('aria-label','Active scene');$('viewport-title').after(sceneSelect);
sceneSelect.onchange=()=>api('/api/scene',{scene_id:sceneSelect.value});
const comparisonNotice=document.createElement('p');comparisonNotice.id='scene-comparison-note';comparisonNotice.className='field-note';comparisonNotice.textContent='Viewport: retail comparison. Inspector fields remain authored project values; edits appear in Authored scene.';comparisonNotice.hidden=true;$('inspector').before(comparisonNotice);
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
const exportProjectButton=document.createElement('button');exportProjectButton.id='export-project-button';exportProjectButton.textContent='Export disc';exportProjectButton.title='Export supported authored changes as a separate experimental disc';buildButton.after(exportProjectButton);exportProjectButton.onclick=()=>exportNpcDrafts();
const exportHistoryButton=document.createElement('button');exportHistoryButton.id='export-history-button';exportHistoryButton.textContent='Export history';buildReportButton.after(exportHistoryButton);
exportHistoryButton.onclick=async()=>{
  if(busy)return;
  const dialog=document.createElement('dialog');dialog.id='export-history-dialog';dialog.className='project-dialog';
  const heading=document.createElement('h2');heading.textContent='Experimental exports';
  const status=document.createElement('p');status.setAttribute('role','status');status.textContent='Loading saved exports…';
  const list=document.createElement('div');list.style.maxHeight='60vh';list.style.overflow='auto';
  const close=document.createElement('button');close.textContent='Close';close.onclick=()=>dialog.close();
  dialog.append(heading,status,list,close);document.body.append(dialog);dialog.addEventListener('close',()=>dialog.remove(),{once:true});dialog.showModal();
  const request=async(route,body)=>{const response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const result=await response.json();if(!response.ok)throw new Error(result.error||'Export request failed');return result;};
  try{
    const result=await request('/api/exports',{});
    status.textContent=result.exports.length?`${result.exports.length} saved exports${result.truncated?' (newest 256 shown)':''}. File integrity and gameplay acceptance are separate checks.`:'No experimental exports saved in this project yet. Author scene edits or NPC drafts, then choose Export experimental disc.';
    for(const item of result.exports){
      const row=document.createElement('section'),label=document.createElement('h3');label.textContent=item.status==='completed'?`${item.scene_ids.filter(Boolean).map(id=>id.replace('scene://','')).join(', ')} · ${new Date(item.saved_at).toLocaleString()}`:'Incomplete export';row.append(label);
      const details=document.createElement('pre');details.style.whiteSpace='pre-wrap';details.style.overflowWrap='anywhere';row.append(details);
      if(item.status!=='completed'){details.textContent=`Incomplete or invalid export: ${item.error}`;list.append(row);continue;}
      const summary=item.change_summary;
      const changes=summary?`${summary.npc_draft_count===null?'NPC count not recorded':`${summary.npc_draft_count} NPC draft(s)`} · ${summary.categories.length?summary.categories.join(', '):'No categorized changes recorded'}`:'Change summary unavailable';
      details.textContent=`${item.scene_ids.filter(Boolean).join(', ')}
${changes}
${item.matches_current_inputs?'Matches current authored inputs':'Different authored inputs'}`;
      const provenance=document.createElement('details'),provenanceTitle=document.createElement('summary'),paths=document.createElement('pre');
      provenanceTitle.textContent='Saved files and source hashes';paths.style.whiteSpace='pre-wrap';paths.style.overflowWrap='anywhere';
      paths.textContent=`Disc: ${item.disc_path}
Report: ${item.report_path}
SHA-256: ${item.output_sha256}`+(item.input_project_path?`
Saved inputs: ${item.input_project_path}`:`
No saved input snapshot in this older export.`);
      provenance.append(provenanceTitle,paths);row.append(provenance);
      const check=document.createElement('button');check.textContent='Verify saved files';
      const outcome=document.createElement('p');outcome.setAttribute('role','status');outcome.textContent='File integrity not checked. Gameplay unverified.';
      check.onclick=async()=>{check.disabled=true;outcome.textContent='Checking disc and saved input hashes…';try{const verification=await request('/api/exports/verify',{id:item.id});outcome.textContent=`Disc hash verified${verification.snapshot_available?`; ${verification.snapshot_files_verified} saved input files verified`:'. No input snapshot available'}. Gameplay remains unverified.`;}catch(error){outcome.textContent=`Verification failed: ${error.message}`;}finally{check.disabled=false;}};
      row.append(check,outcome);
      if(item.input_project_path){const openCopy=document.createElement('button');openCopy.textContent='Open editable copy';openCopy.onclick=async()=>{if(busy)return;if(await api('/api/exports/open-copy',{id:item.id})){dialog.close();notify('Opened an editable copy. Saved export inputs are preserved.');}};row.append(openCopy);}
      list.append(row);
    }
  }catch(error){status.textContent=`Could not load exports: ${error.message}`;}
};
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
  document.querySelectorAll('.asset-card,.asset-info').forEach(button=>button.disabled=value);
  document.querySelectorAll('.model-preview-button').forEach(button=>button.disabled=value||(button.dataset.animationEdit==='true'&&state.project?.mode!=='edit'));
  if($('inspect-actor-candidate'))$('inspect-actor-candidate').disabled=value;
  if($('npc-drafts-button'))$('npc-drafts-button').disabled=value;
  if($('inspect-npc-draft'))$('inspect-npc-draft').disabled=value;
  if($('export-npc-drafts'))$('export-npc-drafts').disabled=value||!canEdit();
  if($('export-project-button'))$('export-project-button').disabled=value||!canEdit();
  document.querySelectorAll('#draft-inspector-form input,#draft-inspector-form button,#draft-name-form input,#draft-name-form button,#draft-donor-form select,#draft-donor-form button,#duplicate-npc-draft,#delete-npc-draft').forEach(control=>control.disabled=value||!canEdit());
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
    if(path==='/api/selection'){pendingEntityFrame=null;environmentSelection=null;npcDraftSelection=null;}state=data; render();
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
let sharedEnvironmentMove=null;
let npcDraftSelection=null;
function selectedNpcDraft(){const value=state.actor_drafts?.[npcDraftSelection];return value?.scene_id===state.scene?.id?value:null;}
function frameNpcDraft(){
  const value=selectedNpcDraft(),id=npcDraftSelection;if(!value)return;
  if(sceneRepresentation==='retail'){representationSelect.value='authored';representationSelect.onchange();selectNpcDraft(id);}
  frame({id,components:{Transform:{imported:{position:{...value.position,y:null}}}}});
}
function selectNpcDraft(id){pendingEntityFrame=null;npcDraftSelection=id;environmentSelection=null;cancelViewportGesture();renderHierarchy();renderInspector();$("frame-selected").disabled=false;draw();}
function environmentEntities(){return activeScenePreview()?.entities.filter(e=>e.kind==='environment') ?? [];}
function selectedEnvironment(){return environmentEntities().find(e=>e.entity_id===environmentSelection);}
function movableSelection(){
  if(sceneRepresentation!=="authored")return null;
  const npc=selectedNpcDraft();
  if(npc){if(!scenePreviewCurrent()||hiddenSceneEntities().has(npcDraftSelection))return null;return {id:npcDraftSelection,components:{Transform:{effective:{position:{...npc.position,y:null}}}}};}
  const environment=selectedEnvironment();
  if(!environment)return selected();
  if(!scenePreviewCurrent()||hiddenSceneEntities().has(environment.entity_id))return null;
  if(!environment.entity_id.includes('/decorations/')&&!(sharedEnvironmentMove?.id===environment.entity_id&&sharedEnvironmentMove?.key===resourceStateKey()))return null;
  return {id:environment.entity_id,components:{Transform:{effective:{position:environment.position}}}};
}
async function moveDecoration(identifier,axis,worldValue){
  if(sceneRepresentation!=='authored')return;
  const item=selectedEnvironment();if(!scenePreviewCurrent()||!item||item.entity_id!==identifier)return;
  if(!item.entity_id.includes('/decorations/')){await moveSharedEnvironment(item,axis,worldValue);return;}
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
async function moveSharedEnvironment(item,axis,worldValue){
  if(!canEdit()||sharedEnvironmentMove?.id!==item.entity_id||sharedEnvironmentMove?.key!==resourceStateKey())return;
  const source=item.source_record,binding=activeScenePreview()?.environment_authoring;
  if(!source.record_offset||!source.source_record?.map_sha256||!['x','z'].includes(axis))return;
  const edits=structuredClone(binding?.edits??[]),instances=binding?.instances??[];
  let edit=edits.find(e=>e.record_index===source.object_record_index);
  if(!edit){edit={record_index:source.object_record_index};edits.push(edit);}
  const inherited=source.record_offset[axis],current=edit.offset?.[axis]??inherited;
  const value=current+(worldValue-item.position[axis])*(axis==='z'?-1:1);
  if(!Number.isInteger(value)||value < -32768||value > 32767){notify('Move exceeds the supported scenery offset range.',true);return;}
  (edit.offset??={})[axis]=value;
  if(value===inherited){delete edit.offset[axis];if(!Object.keys(edit.offset).length)delete edit.offset;}
  const remaining=edits.filter(e=>e.offset||e.rotation_psx);
  await api('/api/command',remaining.length||instances.length?{type:'set_environment_transforms',entity_id:state.scene.id,value:{source_sha256:source.source_record.map_sha256,edits:remaining,instances}}:{type:'clear_environment_transforms',entity_id:state.scene.id});
}
function selected(){return selectedEnvironment()||selectedNpcDraft()?null:entities().find(e=>e.id===state.selection?.entity_id);}
function selectEnvironment(identifier){pendingEntityFrame=null;npcDraftSelection=null;environmentSelection=identifier;cancelViewportGesture();renderHierarchy();renderInspector();$('frame-selected').disabled=false;draw();}
function frameEnvironment(){const item=selectedEnvironment();if(item)frame({id:item.entity_id,components:{Transform:{imported:{position:item.position}}}});}
function canEditAppearance(){return (state.project?.mode ?? 'edit').toLowerCase()==='edit' && state.capabilities?.actor_appearance===true;}
function canEdit(){return (state.project?.mode ?? 'edit').toLowerCase()==='edit' && state.capabilities?.edit_transform!==false;}
function displayPosition(value){const p={x:numeric(value?.x)?value.x:0,y:numeric(value?.y)?value.y:0,z:numeric(value?.z)?value.z:0},matrix=activeScenePreview()?.position_to_display;return matrix?{x:matrix[0]*p.x+matrix[1]*p.y+matrix[2]*p.z+matrix[3],y:matrix[4]*p.x+matrix[5]*p.y+matrix[6]*p.z+matrix[7],z:matrix[8]*p.x+matrix[9]*p.y+matrix[10]*p.z+matrix[11]}:p;}
function position(entity){
  const source=sceneRepresentation==='retail'?entity.components?.Transform?.imported?.position:entity.components?.Transform?.effective?.position ?? entity.components?.Transform?.imported?.position;
  const preview=scenePreviewCurrent()?activeScenePreview()?.entities.find(item=>item.entity_id===entity.id):null;
  return displayPosition(preview?.preview_position??source);
}
function authored(entity){return !!entity.components?.Animation?.authored_channels || Object.keys(entity.components?.Transform?.authored?.position ?? {}).length>0 || !!entity.components?.ActorAppearance?.authored?.donor_entity_id || Object.keys(entity.components?.Dialogue?.authored?.runs ?? {}).length>0;}
function showDialog(id){const d=$(id);d.querySelector('.dialog-error')?.replaceChildren();d.showModal();}
document.querySelectorAll('[data-close]').forEach(button=>button.addEventListener('click',()=>button.closest('dialog').close()));
$('project-button').onclick=()=>{ $('project-name-input').value=state.project?.name ?? 'Legaia project'; $('project-path-input').value=state.project?.path ?? '';showDialog('project-dialog'); };
for(const id of ['import-button','empty-import']) $(id).onclick=()=>{if(!$('disc-input').value)$('disc-input').value=state.project?.disc_path??'';showDialog('import-dialog');};
$('project-form').onsubmit=async event=>{event.preventDefault();await api('/api/project/new',{name:$('project-name-input').value,path:$('project-path-input').value},{dialog:$('project-dialog'),success:'Project created.'});};
$('open-project').onclick=async()=>{if(!$('project-path-input').reportValidity())return;await api('/api/project/open',{path:$('project-path-input').value},{dialog:$('project-dialog'),success:'Project opened.'});};
const sceneCatalog=document.createElement('section');sceneCatalog.id='import-scene-catalog';
sceneCatalog.innerHTML='<h3>Find a scene</h3><label>Name prefix<input id="catalog-prefix" placeholder="town, dolk, station…" spellcheck="false"></label><div class="dialog-actions"><button type="button" id="catalog-search">Read scene catalog</button><button type="button" id="catalog-previous" disabled>Previous</button><button type="button" id="catalog-next" disabled>Next</button></div><p id="catalog-status" role="status">Scans 16 structural blocks per page. Placement support does not establish complete models or gameplay compatibility.</p><div id="catalog-scenes"></div>';
$('scene-input').parentElement.before(sceneCatalog);
let catalogGeneration=0,catalogOffset=0,catalogNext=null;
function clearSceneCatalog(){catalogGeneration++;catalogOffset=0;catalogNext=null;$('catalog-status').textContent='Read the catalog for the current disc path and name prefix. Placement support does not verify models or gameplay.';$('catalog-scenes').replaceChildren();$('catalog-previous').disabled=true;$('catalog-next').disabled=true;}
$('disc-input').addEventListener('input',clearSceneCatalog);$('catalog-prefix').oninput=clearSceneCatalog;
$('import-dialog').addEventListener('close',clearSceneCatalog);
async function readSceneCatalog(offset=0){
  if(busy)return;
  const disc=$('disc-input').value.trim(),prefix=$('catalog-prefix').value.trim();
  if(!disc){$('catalog-status').textContent='Enter your local disc image path first.';return;}
  const generation=++catalogGeneration;setBusy(true);$('catalog-search').disabled=true;$('catalog-previous').disabled=true;$('catalog-next').disabled=true;$('catalog-scenes').replaceChildren();$('catalog-status').textContent='Reading verified retail scene blocks…';
  try{
    const response=await fetch('/api/scene-catalog',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({disc,prefix,offset})});
    const result=await response.json();if(!response.ok||result.error)throw new Error(result.error||'Scene catalog failed');
    if(generation!==catalogGeneration||!$('import-dialog').open)return;
    if(result.schema_version!=='legaia.scene-catalog.v1'||!Array.isArray(result.scenes)||!Array.isArray(result.unsupported_blocks)||result.scenes.length+result.unsupported_blocks.length>16||(result.next_offset!==null&&(!Number.isInteger(result.next_offset)||result.next_offset<=offset)))throw new Error('Invalid scene catalog response');
    catalogOffset=offset;catalogNext=result.next_offset;
    $('catalog-status').textContent=`${result.scenes.length} placement-readable scenes · ${result.unsupported_blocks.length} unsupported blocks · scanned ${result.scanned_blocks} at offset ${offset} of ${result.total_blocks}. Models and gameplay are not verified by this scan.`;
    for(const scene of result.scenes){
      const button=document.createElement('button');button.type='button';button.className='catalog-scene';button.textContent=`${scene.name} · ${scene.actor_count} actors · ${scene.man_source_kind==='raw_streaming_man'?'Streaming field':scene.man_source_kind==='descriptor_man'?'Compressed field':'Source format unknown'}`;button.title=scene.semantic_id;
      button.onclick=()=>{$('scene-input').value=scene.name;$('catalog-status').textContent=`Selected ${scene.name}. Use Import scene to add it to the project.`;};$('catalog-scenes').append(button);
    }
    if(result.unsupported_blocks.length){const details=document.createElement('details'),summary=document.createElement('summary');summary.textContent='Unsupported structural blocks';details.append(summary);for(const block of result.unsupported_blocks){const row=document.createElement('p');row.textContent=`${block.name}: ${block.reason}`;details.append(row);}$('catalog-scenes').append(details);}
  }catch(error){if(generation===catalogGeneration)$('catalog-status').textContent=String(error.message);}
  finally{setBusy(false);$('catalog-search').disabled=false;$('catalog-previous').disabled=catalogOffset===0;$('catalog-next').disabled=catalogNext===null;}
}
$('catalog-search').onclick=()=>readSceneCatalog();$('catalog-previous').onclick=()=>readSceneCatalog(Math.max(0,catalogOffset-16));$('catalog-next').onclick=()=>{if(catalogNext!==null)readSceneCatalog(catalogNext);};
$('import-form').onsubmit=async event=>{event.preventDefault();$('status').textContent='Importing scene from local disc image…';await api('/api/import',{disc:$('disc-input').value,scene:$('scene-input').value},{dialog:$('import-dialog'),success:'Scene imported.'});};
$('save-button').onclick=()=>api('/api/project/save',{}, {success:'Project saved.'});
const draftsButton=document.createElement('button');draftsButton.id='npc-drafts-button';draftsButton.textContent='NPC drafts';draftsButton.onclick=()=>openNpcDrafts();$('save-button').after(draftsButton);
$('undo-button').onclick=()=>api('/api/undo',{});
$('redo-button').onclick=()=>api('/api/redo',{});
$('edit-mode').onclick=()=>api('/api/mode',{mode:'edit'});
$('live-mode').onclick=()=>api('/api/mode',{mode:'live'});
$('entity-search').oninput=renderHierarchy;
$('frame-all').onclick=()=>frame();
$('frame-selected').onclick=()=>{if(selectedNpcDraft())frameNpcDraft();else if(selectedEnvironment())frameEnvironment();else{const entity=selected();if(entity)frame(entity);}};
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
  if(event.key.toLowerCase()==='f'){if(selectedNpcDraft())frameNpcDraft();else if(selectedEnvironment())frameEnvironment();else if(selected())frame(selected());}
});
window.addEventListener('beforeunload',event=>{if(state.project?.dirty){event.preventDefault();event.returnValue='';}});

function render(){
  draftsButton.textContent=`NPC drafts (${Object.keys(state.actor_drafts??{}).length})`;
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
  $('frame-selected').disabled=!selected()&&!selectedEnvironment()&&!selectedNpcDraft();
  $('status').textContent=state.scene?.id ? `${state.scene.name} · ${entities().length} entities · ${state.project?.dirty?'Changes not saved':'Project ready'}` : 'Ready · Create or open a project to begin';
  renderHierarchy();renderAssets();renderInspector();
  templateButton.disabled=!state.capabilities?.authored_transform_templates;
  if(templateDialog.open)renderTemplates();
  renderRunStatus();renderBuildStatus();scheduleRunPoll();
  if(lastSceneId!==state.scene?.id){lastSceneId=state.scene?.id;frame();}else draw();
  refreshScenePreview();
}
function activeScenePreview(){return scenePreview&&state.capabilities?.scene_preview&&state.scene_preview_source_key&&sceneProjectPath===state.project?.path&&scenePreview.scene_id===state.scene?.id&&scenePreview.representation===sceneRepresentation?scenePreview:null;}
function scenePreviewCurrent(){return !!activeScenePreview()&&sceneKey===sceneRequestKey()&&!sceneError;}
function sceneModelsReady(){return modelsEnabled&&activeScenePreview()&&sceneRenderer&&!sceneRenderer.lost&&!sceneError;}
function sceneView(){const positions=new Map(entities().map(entity=>[entity.id,draft?.id===entity.id?draft.position:position(entity)]));if(draft)positions.set(draft.id,draft.position);return {camera,basis:basis(),width,height,grid,hiddenEntities:hiddenSceneEntities(),positions};}
function updateSceneBadge(){
  comparisonNotice.hidden=sceneRepresentation!=='retail';
  const draftCount=Object.values(state.actor_drafts??{}).filter(item=>item.scene_id===state.scene?.id).length;
  $('entity-count').textContent=entities().length+environmentEntities().length+draftCount;
  const ready=sceneModelsReady(),count=ready?sceneRenderer.instances.length:0;
  const hidden=hiddenSceneEntities(),visible=ready?sceneRenderer.instances.filter(instance=>!hidden.has(instance.entity_id)).length:0;
  const visibilityId=visibilitySelection(),visibilityItem=activeScenePreview()?.entities.find(e=>e.entity_id===visibilityId);
  $('hide-selected').disabled=!visibilityId;
  $('hide-selected').textContent=sceneHidden.has(visibilityId)?'Show selected':'Hide selected';
  $('hide-model').disabled=!visibilityItem?.asset_id;
  $('show-hidden').disabled=sceneHidden.size===0;
  $('show-hidden').textContent=sceneHidden.size?`Show hidden (${sceneHidden.size})`:'Show hidden';
  $('scene-models').hidden=!ready;
  modelToggle.hidden=!state.capabilities?.scene_preview;modelToggle.textContent=sceneError?'Retry models':'Models';modelToggle.title=sceneError ?? 'Show supported SDK meshes at authored placements';
  document.querySelector('.preview-badge span').textContent=sceneError?'Models unavailable · placement markers remain usable':scenePendingKey?(ready?'Updating scene · showing previous preview (scenery editing paused)':'Loading supported scene models…'):ready?`${sceneRepresentation==='retail'?'Retail comparison · ':'Authored · '}${count} / ${activeScenePreview()?.entities.length??0} meshes loaded · ${visible} visible · approximate blends`:modelsEnabled?'Placement markers · model data unavailable':'Placement markers · models hidden';
  $('coordinate-note').textContent=environmentEntities().length?'Environment: imported transforms · Actors: unknown height/facing use preview conventions':'Unknown actor heights are shown on the ground plane.';
  $('coordinate-note').title=JSON.stringify(activeScenePreview()?.limits ?? []);
}
async function refreshScenePreview(){
  const key=sceneRequestKey();
  if(!state.capabilities?.scene_preview||!key||!modelsEnabled){sceneAbort?.abort();scenePendingKey=null;updateSceneBadge();return;}
  if(activeScenePreview()&&sceneKey===key){sceneAbort?.abort();sceneAbort=null;scenePendingKey=null;sceneFailedKey=null;sceneError=null;updateSceneBadge();return;}
  if(scenePendingKey===key||sceneFailedKey===key){updateSceneBadge();return;}
  const preserveCamera=sceneLoadedId===state.scene?.id && sceneProjectPath===state.project?.path;
  sceneAbort?.abort();const controller=new AbortController();sceneAbort=controller;scenePendingKey=key;sceneError=null;if(!preserveCamera){scenePreview=null;sceneRenderer?.clear();}
  const expectedScene=state.scene?.id,revision=cameraRevision;updateSceneBadge();draw();
  try{
    if(!sceneRenderer){const module=await import('/scene-renderer.js');if(controller.signal.aborted)return;sceneRenderer=new module.SceneRenderer($('scene-models'),message=>{sceneError=message;updateSceneBadge();draw();});}
    const response=await fetch('/api/scene-preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({representation:sceneRepresentation}),signal:controller.signal});
    const data=await response.json();if(!response.ok||data.error)throw new Error(typeof data.error==='string'?data.error:'Scene preview failed');
    if(controller.signal.aborted||sceneRequestKey()!==key||state.scene?.id!==expectedScene)return;
    if(data.project_source_key!==state.scene_preview_source_key||data.representation!==sceneRepresentation||data.scene_id!==expectedScene)throw new Error('Scene preview source changed while loading; retry models.');
    if(!Array.isArray(data.position_to_display)||data.position_to_display.length!==16||!data.position_to_display.every(numeric))throw new Error('SDK did not provide a valid scene display conversion.');
    clearScenePose(false);const failures=sceneRenderer.load(data);if(!data.entities.some(e=>e.entity_id===environmentSelection))environmentSelection=null;scenePreview=data;sceneProjectPath=state.project?.path;sceneLoadedId=data.scene_id;sceneKey=key;sceneFailedKey=null;scenePendingKey=null;
    if(failures.length)notify(`${failures.length} model assets could not be rendered; their placement markers remain available.`,true);
    renderHierarchy();renderInspector();
    const waiting=pendingEntityFrame;pendingEntityFrame=null;
    if(waiting&&waiting.key===key&&waiting.scene===state.scene?.id&&waiting.project===state.project?.path&&waiting.revision===cameraRevision&&!drag)frame(waiting.entity);
    else if(!preserveCamera&&revision===cameraRevision&&!drag)frame();else draw();
  }catch(error){if(error.name!=='AbortError'&&sceneRequestKey()===key){sceneFailedKey=key;sceneError=error.message;scenePendingKey=null;if(!preserveCamera)sceneRenderer?.clear();renderInspector();notify(error.message,true);}}
  finally{if(sceneAbort===controller){sceneAbort=null;scenePendingKey=null;updateSceneBadge();draw();}}
}
function renderHierarchy(){
  const list=$('hierarchy');list.replaceChildren();
  const filter=$('entity-search').value.toLowerCase();
  for(const entity of entities().filter(e=>`${e.name} ${e.id}`.toLowerCase().includes(filter))){
    const row=document.createElement('button');row.className='entity-row';row.setAttribute('role','treeitem');row.setAttribute('aria-selected',!selectedEnvironment()&&!selectedNpcDraft()&&entity.id===state.selection?.entity_id);row.classList.toggle('selected',!selectedEnvironment()&&!selectedNpcDraft()&&entity.id===state.selection?.entity_id);row.title=entity.id;
    row.innerHTML=`<span class="entity-icon">◇</span><span class="entity-name">${escapeHTML(entity.name ?? entity.id)}</span>${authored(entity)?'<span class="authored-dot" title="Authored override"></span>':''}`;
    row.onclick=()=>{environmentSelection=null;api('/api/selection',{entity_id:entity.id});};row.ondblclick=()=>frame(entity);list.append(row);
  }
  const environment=environmentEntities().filter(e=>`${e.name} ${e.entity_id}`.toLowerCase().includes(filter));
  const npcDrafts=Object.entries(state.actor_drafts??{}).filter(([id,item])=>item.scene_id===state.scene?.id&&`${item.name} ${id}`.toLowerCase().includes(filter));
  if(npcDrafts.length){const heading=document.createElement('div');heading.className='field-note';heading.textContent=`NPC drafts (${npcDrafts.length})`;list.append(heading);}
  for(const [id,item] of npcDrafts){const row=document.createElement('button');row.className='entity-row';row.setAttribute('role','treeitem');row.textContent=`${item.name} · ${sceneRepresentation==='retail'?'Authored only':'Draft'}`;row.title=id;row.onclick=()=>selectNpcDraft(id);row.setAttribute("aria-selected",id===npcDraftSelection);row.classList.toggle("selected",id===npcDraftSelection);list.append(row);}
  if(environment.length){const heading=document.createElement('div');heading.className='field-note';heading.textContent=`Environment (${environment.length})`;list.append(heading);}
  for(const item of environment){const row=document.createElement('button');row.className='entity-row';row.setAttribute('role','treeitem');row.setAttribute('aria-selected',item.entity_id===environmentSelection);row.classList.toggle('selected',item.entity_id===environmentSelection);row.textContent=item.name;row.title=item.entity_id;row.onclick=()=>selectEnvironment(item.entity_id);row.ondblclick=()=>{selectEnvironment(item.entity_id);frameEnvironment();};list.append(row);}
  if(!list.children.length){const p=document.createElement('div');p.className='empty-panel';p.textContent=entities().length?'No matching entities.':'Imported actors will appear here.';list.append(p);}
  const hidden=hiddenSceneEntities();
  for(const row of list.querySelectorAll('.entity-row')){
    if(!hidden.has(row.title))continue;
    row.classList.add('viewport-hidden');
    const badge=document.createElement('small');badge.textContent='Hidden';badge.style.marginLeft='auto';
    row.append(badge);row.setAttribute('aria-label',`${row.textContent} in viewport`);
  }
}
// Search SDK records already present in project state, including their provenance.
const assetTools=document.createElement('div');assetTools.className='asset-tools';
assetTools.innerHTML='<label class="asset-search-label"><input id="asset-search" type="search" placeholder="Search ID, type, scene, provenance…" aria-label="Search asset database"></label><select id="asset-category" aria-label="Asset category"><option value="all">All records</option><option value="authored">Authored assets</option><option value="model">Models</option><option value="actor">Actors in active scene</option><option value="scene">Imported scenes</option><option value="texture">Textures</option><option value="animation">Animations</option><option value="script">Scripts</option><option value="dialogue">Dialogue</option><option value="collision">Collision</option><option value="trigger">Triggers</option><option value="region">Regions</option><option value="worldmap">World-map landmarks</option></select><span id="asset-results" role="status"></span><button id="resource-refresh">Refresh scene resources</button><span id="resource-status" role="status">Resource catalog has not been loaded.</span>';
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
    if(result.scene_id!==sceneId||result.source_key!==sourceKey||!Array.isArray(result.records)||result.records.length>4096||result.records.some(record=>typeof record.semantic_id!=='string'||!['texture','animation','script','dialogue','collision','trigger','region','worldmap'].includes(record.asset_kind)))throw new Error('Resource catalog returned stale or invalid records.');
    resourceLimitations=result.limitations ?? [];resourceRecords=[...new Map(result.records.map(record=>[record.semantic_id,{...record,catalog_limitations:result.limitations}])).values()];resourceKey=key;resourcePendingKey=null;renderAssets();
  }catch(error){if(error.name!=='AbortError'&&key===resourceStateKey()){resourceError=error.message;notify(error.message,true);}}
  finally{if(resourceAbort===controller){resourceAbort=null;resourcePendingKey=null;}setBusy(false);synchronizeResources();}
}
function assetRecords(){
  const records=new Map([
    ...(state.assets ?? []).map(asset=>({id:asset.id,type:asset.kind ?? 'model',label:asset.name ?? asset.label ?? `Model ${asset.id.split('/').at(-1)}`,source:asset.source_record?.prot_entry_name ?? asset.scope ?? 'Imported',data:asset})),
    ...entities().map(actor=>({id:actor.id,type:'actor',label:actor.name ?? actor.id,source:state.scene?.name ?? state.scene?.id,sceneId:state.scene?.id,data:actor})),
    ...(state.scenes ?? []).map(scene=>({id:scene.id,type:'scene',label:scene.name ?? scene.id,source:scene.name ?? scene.id,data:scene})),
    ...resourceRecords.map(record=>({id:record.semantic_id,type:record.asset_kind,label:record.name ?? record.semantic_id,source:record.scope?.startsWith('global-')?record.scope:(record.source_record?.prot_entry_name ?? state.scene?.name),sceneId:state.scene?.id,data:record}))
  ].map(record=>[record.id,record]));
  for(const authored of state.authored_assets ?? []){
    if(typeof authored.id!=='string'||!['actor','model','texture','template','script','scene'].includes(authored.kind))continue;
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
    references.set(ref.source_id,{source_id:ref.source_id,scene_id:ref.scene_id,source_name:ref.source_name,kind:ref.kind,
      imported:!!(imported||previous?.imported),effective:!!(effective||previous?.effective)});
  }
  return [...references.values()];
}
function showAssetDetails(record){
  const isAuthored=!!record.authoredRecord;
  assetDetails.innerHTML=`<div class="dialog-heading"><h2>${escapeHTML(record.label)}</h2><button id="close-asset-details" aria-label="Close asset details">×</button></div>${property('Stable ID',record.id)}${property('Record type',record.type)}${property(record.data?.scope?.startsWith('global-')?'Source scope':'Source scene',record.authoredRecord?.source_scene ?? record.source)}${isAuthored?`<section class="asset-authored-details"><h3>Authored project settings</h3><p>${escapeHTML(record.changes.join(' · ') || 'Authored project metadata')}</p><pre class="diagnostic-detail" id="asset-authored-data"></pre><button id="open-authored-asset">${record.type==='template'?'Open template library':record.type==='texture'?'Inspect texture':record.type==='model'?'Inspect authored model':record.type==='script'?'Open script workspace':record.type==='scene'?'Open scene':'Select actor'}${record.type!=='template'&&record.sceneId!==state.scene?.id?' in source scene':''}</button></section>`:''}<details ${isAuthored?'':'open'}><summary>${isAuthored?'Imported source provenance':'SDK source and provenance'}</summary><pre id="asset-source-data" class="diagnostic-detail"></pre></details>`;
  const source=isAuthored?(record.authoredRecord.source_record ?? record.data?.source_record ?? record.data?.components?.RetailMetadata ?? {note:'No additional imported provenance is attached to this authored record.'}):record.data;
  $('asset-source-data').textContent=JSON.stringify(source,null,2);
  if(record.type==='worldmap'){
    const data=record.data,context=JSON.stringify([state.project?.path,state.project?.disc_path]),section=document.createElement('section');
    section.innerHTML=`<h3>Landmark source record</h3>${property('Destination source',`${data.destination_scene_id}${data.destination_source_label?' · '+data.destination_source_label:''}`)}${property('Menu X / Y',`${data.menu_position.x} / ${data.menu_position.y}`)}${property('Discovery flag index',data.discovery_flag_index)}<p>Menu pixels, not scene coordinates. Current discovery state and gameplay reachability are unobserved.</p>`;
    if(data.destination_source_label){const inspect=document.createElement('button');inspect.textContent='Inspect destination source';inspect.onclick=()=>{if(busy||context!==JSON.stringify([state.project?.path,state.project?.disc_path]))return;assetDetails.close();$('import-button').click();$('catalog-prefix').value=data.destination_source_label;clearSceneCatalog();$('catalog-search').click();};section.append(inspect);}
    const open=document.createElement('button');open.textContent='Open world-map landmarks';open.onclick=()=>{if(busy||context!==JSON.stringify([state.project?.path,state.project?.disc_path]))return;assetDetails.close();worldmapButton.click();};section.append(open);
    $('asset-source-data').parentElement.before(section);$('asset-source-data').parentElement.open=false;
  }
  if(['model','animation'].includes(record.type)){
    const usage=document.createElement('section');usage.innerHTML=`<h3>Used by</h3><p>${record.type==='model'?'Initial model assignments across imported scenes.':'Verified initial animation bindings and authored donor assignments.'} Scripts may change these assignments during gameplay.</p>`;
    const references=initialAssetUsage(record,state.model_references??[]);
    for(const ref of references){const button=document.createElement('button');button.textContent=`${ref.source_name??ref.source_id} · ${ref.kind==='draft_initial_model_assignment'?'NPC draft':`${ref.imported?'Imported':''}${ref.imported&&ref.effective?' + ':''}${ref.effective?'Effective':''}`}`;button.title=ref.source_id;button.onclick=async()=>{if(busy)return;assetDetails.close();if(ref.scene_id!==state.scene?.id&&!await api('/api/scene',{scene_id:ref.scene_id}))return;if(ref.kind==='draft_initial_model_assignment'){selectNpcDraft(ref.source_id);frameNpcDraft();}else if(await api('/api/selection',{entity_id:ref.source_id}))frame(selected());};usage.append(button);}
    if(!references.length){const empty=document.createElement('p');empty.textContent='No imported or effective initial actor assignments in this project.';usage.append(empty);}
    $('asset-source-data').parentElement.before(usage);
  }
  if(isAuthored){$('asset-authored-data').textContent=JSON.stringify(record.authored,null,2);$('open-authored-asset').onclick=()=>{assetDetails.close();activateAsset(record);};}
  if(isAuthored&&record.type==='actor'&&record.authored?.AnimationChannels){
    const actions=document.createElement('div');actions.className='dialog-actions';
    for(const [label,preview] of [['Edit animation channels',false],['Preview authored animation',true]]){
      const button=document.createElement('button');button.textContent=label;button.disabled=busy||(!preview&&state.project.mode!=='edit');
      button.onclick=async()=>{
        if(busy)return;assetDetails.close();
        if(record.sceneId!==state.scene?.id&&!await api('/api/scene',{scene_id:record.sceneId}))return;
        if(!await api('/api/selection',{entity_id:record.id}))return;
        const actor=selected();if(!actor)return;
        if(preview)await openModel(actor.components.ModelRenderer.asset_id,'authored-channels',actor.id);
        else await openAnimationChannels(actor);
      };actions.append(button);
    }
    $('asset-authored-data').before(actions);
  }
  $('close-asset-details').onclick=()=>assetDetails.close();assetDetails.showModal();
}
async function activateAsset(record){
  if(busy)return;
  if(record.type==='template'){showTemplates();return;}
  if(record.authoredRecord&&['actor','texture','script','model'].includes(record.type)&&record.sceneId!==state.scene?.id){
    if(!record.sceneId){notify('This authored item does not identify an imported source scene.',true);return;}
    if(!await api('/api/scene',{scene_id:record.sceneId}))return;
  }
  if(record.type==='script'&&record.authoredRecord){
    await openActorScript({id:record.authoredRecord.id,name:record.label,partitionTwo:true});
  }else if(record.type==='actor'&&record.authoredRecord?.draft){
    selectNpcDraft(record.id);frameNpcDraft();document.querySelector('.workspace-tabs [data-panel="viewport"]').click();
  }else if(record.type==='actor'){
    if(await api('/api/selection',{entity_id:record.id})){frame(selected());document.querySelector('.workspace-tabs [data-panel="viewport"]').click();}
  }else if(record.type==='scene'){
    if(await api('/api/scene',{scene_id:record.id}))document.querySelector('.workspace-tabs [data-panel="viewport"]').click();
  }else if(record.type==='model')openModel(record.id,null,null,record.authoredRecord?'authored':'imported');
  else if(record.type==='texture')openTexture(record);
  else if(record.type==='animation')openAnimationResource(record);
  else if(['collision','trigger','region'].includes(record.type))openFieldResource(record);
  else if(['script','dialogue'].includes(record.type))openScriptResource(record);
  else showAssetDetails(record);
}
function renderAssets(){
  synchronizeResources();
  const list=$('assets'),query=$('asset-search').value.trim().toLowerCase().split(/\s+/).filter(Boolean),category=$('asset-category').value;
  assetScope.querySelector('p').textContent=`Models come from imported scenes; actors come from the active scene. Scenes lists imported scenes. Authored assets gathers project-wide NPC drafts, actor edits, script dialogue edits, model and texture replacements and transform templates without a resource refresh. Refresh adds scene texture candidates, referenced scene-header animations, actor and partition-two scripts, dialogue and supported field-map metadata; it also lists global world-map menu records and eight supported shared field clips, without claiming current actor playback or complete runtime coverage. ${state.capabilities?.actor_script_preview?'Script inspection and supported dialogue text tools are available from an actor’s Inspector.':'Script and dialogue inspection is not available in this service.'} Audio is not cataloged here. ${resourceLimitations.map(limit=>typeof limit==='string'?limit:JSON.stringify(limit)).join(' ')}`;
  const records=assetRecords(),filtered=records.filter(record=>(category==='all'||(category==='authored'?!!record.authoredRecord:record.type===category&&(category!=='actor'||record.sceneId===state.scene?.id)))&&query.every(term=>JSON.stringify(record).toLowerCase().includes(term)));
  list.replaceChildren();$('asset-count').textContent=records.length;$('asset-results').textContent=`${filtered.length} / ${records.length} records`;
  for(const record of filtered){
    const row=document.createElement('div');row.className='asset-result';
    const card=document.createElement('button');card.className='asset-card';card.title=record.id;card.innerHTML=`<strong>${escapeHTML(record.label)}${record.authoredRecord?'<span class="asset-authored-badge">Authored</span>':''}</strong><small>${escapeHTML(record.type)} · ${escapeHTML(record.authoredRecord?.source_scene ?? record.source)}</small>${record.authoredRecord?`<span class="asset-change-summary">${escapeHTML(record.changes.join(' · ') || 'Authored project settings')}</span>`:''}<code>${escapeHTML(record.id)}</code>`;
    card.disabled=busy;card.onclick=()=>activateAsset(record);
    const info=document.createElement('button');info.className='asset-info';info.textContent='ⓘ';info.title='View stable ID, source and provenance';info.setAttribute('aria-label',`Details for ${record.label}`);info.disabled=busy;info.onclick=()=>['script','dialogue'].includes(record.type)?openScriptResource(record):['collision','trigger','region'].includes(record.type)?openFieldResource(record):showAssetDetails(record);row.append(card,info);list.append(row);
  }
  if(!filtered.length){const p=document.createElement('p');p.className='field-note';p.textContent=category==='authored'?(records.some(record=>record.authoredRecord)?'No matching authored assets. Try an actor, texture, scene or change description.':'No authored assets yet. Edit an actor, replace a texture or capture a transform template; project edits appear here across scenes.'):['texture','animation','script','dialogue','collision','trigger','region'].includes(category)&&!resourceKey?(state.capabilities?.resource_catalog?'Use Refresh scene resources to verify and load this category.':'Resource catalogs are unavailable in this service.'):records.length?'No matching records. Try a stable ID, model type, scene name or source term.':'Import a scene to populate the catalog.';list.append(p);}
}
const fieldDialog=document.createElement('dialog');fieldDialog.id='field-map-dialog';document.body.append(fieldDialog);
const fieldToggle=document.createElement('button');fieldToggle.id='field-map-toggle';fieldToggle.textContent='Base collision';fieldToggle.hidden=true;fieldToggle.setAttribute('aria-pressed','false');$('grid-toggle').after(fieldToggle);
const fieldNote=document.createElement('div');fieldNote.className='field-map-note';fieldNote.hidden=true;fieldNote.setAttribute('role','status');document.querySelector('.viewport-toolbar').after(fieldNote);
const collisionLayer=document.createElement('select');collisionLayer.setAttribute('aria-label','Collision preview layer');collisionLayer.innerHTML='<option value="imported">Retail collision</option><option value="effective">Effective collision</option>';fieldToggle.after(collisionLayer);
let fieldMap=null,fieldKey=null,fieldAbort=null,fieldPending=false;
const fieldMapScope='Base blocked grid only · Y = 0 is a display placeholder, not decoded height. Runtime/script paints and actors are excluded. Canonical positive-X range only; wrapping and boundary aliases are not shown. Lines are drawn over models.';
function updateFieldToggle(){
  fieldToggle.hidden=!state.capabilities?.field_map_preview;fieldToggle.disabled=busy||fieldPending;
  collisionLayer.hidden=fieldToggle.hidden;collisionLayer.disabled=busy||fieldPending;
  fieldToggle.classList.toggle('active',!!fieldMap);fieldToggle.setAttribute('aria-pressed',!!fieldMap);fieldToggle.textContent=fieldPending?'Loading collision…':collisionLayer.value==='effective'?'Effective collision':'Base collision';
}
function clearFieldMap(){
  fieldAbort?.abort();fieldAbort=null;fieldMap=null;fieldKey=null;fieldPending=false;fieldNote.hidden=true;updateFieldToggle();
}
function validateFieldMap(result,record,key){
  if(key!==resourceStateKey()||result.source_key!==state.scene_preview_source_key||result.scene_id!==state.scene?.id||result.semantic_id!==record.id||result.asset_kind!=='collision'||result.coordinate_system!=='psx_guest_xz')throw new Error('Field map source changed while loading. Refresh scene resources and retry.');
  if(!Array.isArray(result.rectangles)||result.rectangles.length>65536||result.rectangles.some(r=>!r||![r.x_min,r.x_max,r.z_min,r.z_max].every(numeric)||r.x_min>r.x_max||r.z_min>r.z_max)||!Array.isArray(result.triggers)||result.triggers.length>65536)throw new Error('Field map service returned invalid or oversized geometry.');
  if(result.authored_changes!==undefined&&(!Array.isArray(result.authored_changes)||result.authored_changes.length>4096||result.authored_changes.some(r=>!r||!Number.isInteger(r.row)||r.row<1||r.row>127||!Number.isInteger(r.column)||r.column<0||r.column>127||!Number.isInteger(r.quadrant)||r.quadrant<0||r.quadrant>3||typeof r.before_value!=='boolean'||typeof r.after_value!=='boolean')))throw new Error('Collision service returned invalid authored changes.');
  return result;
}
async function loadFieldMap(record){
  if(busy||!state.capabilities?.field_map_preview||resourceKey!==resourceStateKey())return false;
  clearFieldMap();draw();const key=resourceStateKey(),layer=collisionLayer.value,controller=new AbortController();fieldAbort=controller;fieldPending=true;setBusy(true);
  try{
    const response=await fetch('/api/field-map-preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:record.id,layer}),signal:controller.signal});
    const result=await response.json();if(!response.ok||result.error)throw new Error(typeof result.error==='string'?result.error:'Field map verification failed');
    if(controller.signal.aborted)return false;
    if(result.representation!==layer)throw new Error('Collision service did not return the requested layer.');
    if(fieldDialog.open)fieldDialog.querySelector('.dialog-error').textContent='';
    fieldMap=validateFieldMap(result,record,key);fieldKey=key;const changes=fieldMap.authored_changes??[],added=changes.filter(r=>r.after_value).length,removed=changes.filter(r=>!r.after_value).length;fieldNote.textContent=`${layer==='effective'?'EFFECTIVE source':'RETAIL source'} · ${fieldMap.rectangles.length} blocked rectangles${changes.length?` · Added ${added} (green solid) · Removed ${removed} (pink dashed)`:''} · ${fieldMapScope}`;fieldNote.title=(fieldMap.limitations ?? []).map(value=>typeof value==='string'?value:JSON.stringify(value)).join(' ');fieldNote.hidden=false;return true;
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
collisionLayer.onchange=async()=>{updateFieldToggle();if(busy||!fieldMap)return;const record=assetRecords().find(r=>r.id===fieldMap.semantic_id&&r.type==='collision');if(record)await loadFieldMap(record);else{clearFieldMap();draw();}};
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
  if(collision){
    const editButton=document.createElement('button');editButton.textContent='Edit source wall bits';editButton.disabled=state.project.mode!=='edit';summary.append(editButton);
    editButton.onclick=async()=>{
      if(busy||state.project.mode!=='edit')return;collisionLayer.value='effective';if(!await loadFieldMap(record)||!fieldDialog.open)return;
      editButton.disabled=true;const snapshot=fieldMap,key=resourceStateKey(),scene=state.scene.id;
      const form=document.createElement('form');form.innerHTML='<h3>Source wall edit</h3><p>Only the selected wall bit changes. Floor tiers, runtime actors and script collision paints are separate.</p><label>Grid row<input name="row" type="number" min="1" max="127" step="1" value="1" required></label><label>Grid column<input name="column" type="number" min="0" max="127" step="1" value="0" required></label><label>Quadrant<select name="quadrant"><option value="0">0 · low X / low Z</option><option value="1">1 · high X / low Z</option><option value="2">2 · low X / high Z</option><option value="3">3 · high X / high Z</option></select></label><label><input name="blocked" type="checkbox"> Blocked in source grid</label><p class="collision-cell-status"></p><button type="submit">Apply wall bit</button><button type="button" class="clear-collision">Clear scene wall edits</button>';
      summary.append(form);const status=form.querySelector('.collision-cell-status');
      const cell=()=>({row:Number(form.elements.row.value),column:Number(form.elements.column.value),quadrant:Number(form.elements.quadrant.value)});
      const refresh=()=>{const c=cell(),rectangle=snapshot.rectangles.find(r=>r.row===c.row&&r.column===c.column&&r.quadrant===c.quadrant);form.elements.blocked.checked=!!rectangle;const x=c.column*128+(c.quadrant&1)*64,z=c.row*128-128+(c.quadrant>>1)*64;status.textContent=`Effective: ${rectangle?'blocked':'unblocked'} · integer X (${x}, ${x+64}], Z [${z}, ${z+64})`;};
      let draftCell=cell(),appliedBlocked=false;
      const discard=document.createElement('button');discard.type='button';discard.textContent='Discard unapplied wall change';form.append(discard);
      const appliedLabel=document.createElement('label');appliedLabel.textContent='Applied wall edits';const applied=document.createElement('select');applied.setAttribute('aria-label','Applied wall edits');appliedLabel.append(applied);form.prepend(appliedLabel);
      const placeholder=document.createElement('option');placeholder.value='';placeholder.textContent='Choose an authored cell…';applied.append(placeholder);
      const wallEdits=[...(snapshot.authored?.edits??[])].sort((a,b)=>a.row-b.row||a.column-b.column||a.quadrant-b.quadrant);
      for(const [index,edit] of wallEdits.entries()){const option=document.createElement('option');option.value=String(index);option.textContent=`Row ${edit.row} · column ${edit.column} · quadrant ${edit.quadrant} · ${edit.blocked?'blocked':'unblocked'}`;applied.append(option);}
      const restore=document.createElement('button');restore.type='button';restore.textContent='Restore selected cell to retail';form.append(restore);
      const sameCell=(a,b)=>a.row===b.row&&a.column===b.column&&a.quadrant===b.quadrant;
      const dirty=()=>form.elements.blocked.checked!==appliedBlocked;
      const updateDraft=()=>{discard.disabled=!dirty();for(const name of ['row','column','quadrant'])form.elements[name].disabled=dirty();applied.disabled=dirty()||!wallEdits.length;restore.disabled=dirty()||!wallEdits.some(e=>sameCell(e,cell()));form.querySelector('[type="submit"]').disabled=!dirty();const index=wallEdits.findIndex(e=>sameCell(e,cell()));applied.value=index<0?'':String(index);};
      const selectCell=()=>{draftCell=cell();refresh();appliedBlocked=form.elements.blocked.checked;updateDraft();};
      applied.onchange=()=>{if(dirty()){updateDraft();return;}const edit=wallEdits[Number(applied.value)];if(!edit||applied.value==='')return;for(const name of ['row','column','quadrant'])form.elements[name].value=edit[name];selectCell();};
      for(const name of ['row','column','quadrant'])form.elements[name].oninput=()=>{if(dirty()){for(const axis of ['row','column','quadrant'])form.elements[axis].value=draftCell[axis];return;}selectCell();};
      form.elements.blocked.oninput=updateDraft;discard.onclick=()=>{form.elements.blocked.checked=appliedBlocked;updateDraft();};selectCell();
      const locateCell=document.createElement('button');locateCell.type='button';locateCell.textContent='Locate cell in viewport';form.append(locateCell);
      locateCell.onclick=async()=>{
        if(busy||resourceStateKey()!==key||state.scene.id!==scene||!form.reportValidity())return;
        if(dirty()){fieldDialog.querySelector('.dialog-error').textContent='Apply or discard the wall change before locating its cell.';return;}
        const c=cell(),point={x:c.column*128+(c.quadrant&1)*64+32,y:0,z:c.row*128-128+(c.quadrant>>1)*64+32},sourceKey=state.scene_preview_source_key;
        setBusy(true);locateCell.disabled=true;
        try{
          const response=await fetch('/api/terrain-point',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({x:point.x,z:point.z,source_key:sourceKey})});
          const result=await response.json();if(!response.ok)throw new Error(result.error||'Terrain sampling failed');
          if(resourceStateKey()!==key||state.scene.id!==scene||result.source_key!==state.scene_preview_source_key||result.scene_id!==scene)throw new Error('Scene changed while locating the cell');
          if(result.position?.y!==null&&!numeric(result.position?.y))throw new Error('Terrain sample returned an invalid height');
          point.y=result.position.y??0;
          coordinateProbe={point,context:JSON.stringify([state.project?.path,state.scene?.id])};cancelViewportGesture();camera.target=displayPosition(point);camera.distance=1000;cameraRevision++;
          fieldDialog.close();document.querySelector('.workspace-tabs [data-panel="viewport"]').click();draw();
          notify(result.position.y===null?'No source terrain at this cell; locator uses a Y=0 display placeholder.':'Cell located using source terrain elevation; runtime height remains unverified.');
        }catch(error){fieldDialog.querySelector('.dialog-error').textContent=error.message;}
        finally{locateCell.disabled=false;setBusy(false);}
      };
      const apply=async command=>{if(busy||state.project.mode!=='edit'||resourceStateKey()!==key||state.scene.id!==scene)return;await api('/api/command',command,{dialog:fieldDialog,success:'Source wall edits updated. Save project to persist.'});};
      const applyEdits=edits=>apply(edits.length?{type:'set_collision_walls',entity_id:scene,value:{source_sha256:snapshot.asset.source_record.containing_span_sha256,edits}}:{type:'clear_collision_walls',entity_id:scene});
      restore.onclick=()=>{if(dirty()||!form.reportValidity())return;return applyEdits(wallEdits.filter(e=>!sameCell(e,cell())));};
      form.onsubmit=async event=>{event.preventDefault();if(!dirty()||!form.reportValidity())return;const c=cell(),edits=wallEdits.filter(e=>!sameCell(e,c)),change=snapshot.authored_changes?.find(e=>sameCell(e,c)),retailBlocked=change?change.before_value:appliedBlocked;if(form.elements.blocked.checked!==retailBlocked)edits.push({...c,blocked:form.elements.blocked.checked});await applyEdits(edits);};
      form.querySelector('.clear-collision').disabled=!snapshot.authored?.edits?.length;form.querySelector('.clear-collision').onclick=()=>apply({type:'clear_collision_walls',entity_id:scene});
    };
  }
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
  if(instruction.mnemonic==='SET_ACTOR_MODEL'&&Number.isInteger(operands?.model_selector_signed)){
    const summary=document.createElement('p');summary.textContent=`Model selector ${operands.model_selector_signed} (u16 ${operands.model_selector_u16}). High-pool flag ${operands.high_pool_flag?'set':'clear'}. Runtime pool bases and resolved model asset are unknown; branch execution is not observed.`;cell.append(summary);
  }
  if(['NPC_RUN','MOVE_TO'].includes(instruction.mnemonic)&&Number.isFinite(operands?.target_position?.x)&&Number.isFinite(operands?.target_position?.z)){
    const target=operands.target_position,summary=document.createElement('p');
    summary.textContent=`${instruction.mnemonic==='MOVE_TO'?'Teleport':'Script'} target X ${target.x}, Z ${target.z}. Y is unresolved.${operands.parked_target?' Parked/off-field target.':''} Branch execution and current actor position are not observed.`;
    const locate=document.createElement('button');locate.type='button';locate.className='script-locate-target';locate.textContent='Locate target…';
    const context=JSON.stringify([state.project?.path,state.scene?.id]);
    locate.onclick=()=>{
      if(context!==JSON.stringify([state.project?.path,state.scene?.id]))return;
      cell.closest('dialog')?.close();
      for(const axis of ['x','z'])locateDialog.querySelector(`[name="${axis}"]`).value=target[axis];
      const height=locateDialog.querySelector('[name="y"]');height.value='';height.placeholder='Enter a reference height; script Y is unknown';
      locateDialog.showModal();height.focus();
    };
    cell.append(summary,locate);
  }
  if(instruction.mnemonic==='DIALOGUE_PICKER'&&Array.isArray(operands?.options)){
    const options=document.createElement('ol');
    for(const option of operands.options){const item=document.createElement('li');item.textContent=`${option.label} — encoded target ${scriptOffset(option.encoded_target)}`;options.append(item);}
    const note=document.createElement('p');note.className='field-note';note.textContent='Runtime choice and pager continuation are unresolved. Decoded choice paths can be inspected through the successor links.';
    cell.append(options,note);
  }
  const details=document.createElement('details'),label=document.createElement('summary'),raw=document.createElement('pre');
  label.textContent='Encoded operands';raw.textContent=typeof operands==='string'?operands:JSON.stringify(operands??{},null,2);
  details.open=!['ACTOR_POSITION','DIALOGUE_PICKER','NPC_RUN','MOVE_TO','SET_ACTOR_MODEL'].includes(instruction.mnemonic);details.append(label,raw);cell.append(details);
}
function appendScriptInstructions(host,report,identity=report.semantic_id??report.script_id??'Inspected script',movementAuthoring=report.movement_authoring){
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
  const targets=instructions.filter(row=>['MOVE_TO','NPC_RUN'].includes(row.mnemonic)&&
    row.operands?.coordinate_system==='retail_field_world_units'&&numeric(row.operands?.target_position?.x)&&numeric(row.operands?.target_position?.z))
    .map(row=>({pc:row.pc,mnemonic:row.mnemonic,position:{...row.operands.target_position},context:row.target_context,parked:!!row.operands.parked_target}));
  if(targets.length){
    const tools=document.createElement('div');tools.className='script-target-controls';
    const label=document.createElement('label');label.textContent='Reference Y ';
    const height=document.createElement('input');height.type='number';height.step='any';height.min='-1000000000';height.max='1000000000';height.required=true;height.setAttribute('aria-label','Script targets reference Y');height.placeholder='Script height is unknown';label.append(height);
    const show=document.createElement('button');show.type='button';show.className='script-show-targets';show.textContent=`Show ${targets.length} targets in scene`;show.disabled=targets.length>256;
    const note=document.createElement('p');note.className='field-note';note.textContent=targets.length>256?'This report exceeds the 256-marker overlay limit. Locate individual instructions instead.':'All markers use your reference Y. No movement path, current actor position or executed branch is inferred; parked targets remain included.';
    const layer=document.createElement('select');layer.setAttribute('aria-label','Script target layer');
    const importedOption=document.createElement('option');importedOption.value='retail';importedOption.textContent='Retail source targets';
    const effectiveOption=document.createElement('option');effectiveOption.value='authored';effectiveOption.textContent='Authored effective targets';
    const effective=new Map((movementAuthoring?.targets??[]).map(target=>[target.pc,target]));
    effectiveOption.disabled=movementAuthoring?.supported!==true||!!movementAuthoring?.unresolved_overrides?.length||!targets.every(target=>{const item=effective.get(target.pc);return item?.mnemonic===target.mnemonic&&numeric(item.effective_values?.x)&&numeric(item.effective_values?.z);});
    layer.append(importedOption,effectiveOption);
    const key=resourceStateKey();
    show.onclick=()=>{
      if(busy||key!==resourceStateKey()||!height.reportValidity()||!height.value.trim()||!numeric(Number(height.value)))return;
      if(layer.value==='authored'&&effectiveOption.disabled)return;
      const chosen=layer.value==='authored'?targets.map(target=>({...target,position:{...target.position,...effective.get(target.pc).effective_values},parked:!!effective.get(target.pc).effective_parked_target})):targets;
      scriptTargetOverlay={key,identity,targets:chosen,representation:layer.value,height:Number(height.value),partial:report.status==='partial'};
      const targetSelect=scriptTargetTools.querySelector('select');targetSelect.replaceChildren();
      for(const target of chosen){const option=document.createElement('option');option.value=target.pc;option.textContent=`${scriptOffset(target.pc)} ${target.mnemonic} · X ${target.position.x}, Z ${target.position.z}`;targetSelect.append(option);}
      host.closest('dialog')?.close();frameScriptTargets();
    };
    tools.append(layer,label,show,note);navigation.prepend(tools);
  }
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
  appendScriptInstructions($('trigger-script-instructions'),report,result.script_id,result.movement_authoring);
  host.querySelector('.script-raw pre').textContent=JSON.stringify(result,null,2);
}
function drawFieldMap(){
  if(!fieldMap||fieldKey!==resourceStateKey())return;
  ctx.save();ctx.strokeStyle='#e1ac688f';ctx.fillStyle='#d39d4b10';ctx.lineWidth=1;
  const deltas=(fieldMap.authored_changes??[]).map(change=>{const x=change.column*128+(change.quadrant&1)*64,z=change.row*128-128+(change.quadrant>>1)*64;return {x_min:x,x_max:x+64,z_min:z,z_max:z+64,added:change.after_value};});
  for(const rectangle of [...fieldMap.rectangles,...deltas]){
    if(rectangle.added!==undefined){ctx.strokeStyle=rectangle.added?'#68f0ac':'#ff91b8';ctx.fillStyle=rectangle.added?'#68f0ac30':'#ff91b818';ctx.lineWidth=3;ctx.setLineDash(rectangle.added?[]:[6,4]);}
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
  const data=record.data;
  if(data.scope==='global-field'){
    const preview=data.preview,available=preview&&state.assets.some(asset=>asset.id===preview.asset_id);
    animationResourceDialog.innerHTML=`<div class="dialog-heading"><h2>${escapeHTML(record.label)}</h2><button id="close-animation-resource" aria-label="Close animation resource">×</button></div>${property('Stable ID',record.id)}${property('Frames',data.frame_count)}${property('Rigid channels',data.bone_count)}<p>Shared field clip with a verified reference model association. This does not establish which scene actors are playing it or its current runtime timing.</p><button id="preview-global-animation" ${available?'':'disabled'}>Preview reference clip</button><details class="resource-provenance"><summary>Model association, source and limits</summary><pre></pre></details>`;
    animationResourceDialog.querySelector('pre').textContent=JSON.stringify(data,null,2);
    $('close-animation-resource').onclick=()=>animationResourceDialog.close();
    $('preview-global-animation').onclick=()=>{if(busy||!available)return;animationResourceDialog.close();openModel(preview.asset_id,preview.clip_id);};
    animationResourceDialog.showModal();return;
  }
  const candidates=animationPreviewChoices(record,entities(),state.model_references??[]);
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
  scriptResourceDialog.innerHTML=`<div class="dialog-heading"><h2>${escapeHTML(record.label)}</h2><button id="close-script-resource" aria-label="Close script resource">×</button></div>${property('Stable ID',record.id)}${property(data.partition===2?'Script owner':'Actor',data.owner_semantic_id ?? data.actor_semantic_id)}${property('Source scene',record.source)}${property('Inspection',status)}${dialogue?`${property('Parent script status',data.script_status==='partial'?'Partial inspection':resourceLabel(data.script_status))}${property('Record offset',scriptOffset(data.pc))}${property('Source bytes',data.byte_length)}${property('Tokens',data.token_count)}${property('Text length',data.text_length)}<p>Catalog metadata contains no dialogue text. Open the verified script report to inspect this segment and any supported text runs.</p>`:`<div class="script-resource-counts">${property('Instructions',data.instruction_count)}${property('Dialogue segments',data.dialogue_count)}${property('Option menus',data.menu_count ?? 'Not cataloged')}${property('Opaque bytes',data.opaque_byte_count)}${property('Decoder stops',data.stop_count)}</div><p>Encoded references are read only. Runtime flag values, story-state reachability and actual scene transitions are not established by this catalog.</p><section id="resource-model-selections"><h3>Script model selectors</h3><p>Runtime pool bases and resolved assets are unknown.</p></section><section id="resource-movements"><h3>Movement target references</h3></section><section id="resource-menus"><h3>Dialogue option menus</h3></section><section id="resource-flags"><h3>Flag references</h3></section><section id="resource-transitions"><h3>Encoded transitions</h3></section>`}<div class="dialog-actions"><button id="select-script-resource-actor" ${actor?'':'disabled'}>Select actor</button><button id="inspect-script-resource" class="accent" ${scriptOwner&&state.capabilities?.actor_script_preview?'':'disabled'}>${dialogue?'Inspect dialogue segment':'Inspect script'}</button></div>${scriptOwner?'':'<p class="field-note">The script owner is not available in the active scene.</p>'}<details class="resource-provenance"><summary>Source records, encoded fields and limitations</summary><pre class="diagnostic-detail"></pre></details>`;
  $('close-script-resource').onclick=()=>scriptResourceDialog.close();scriptResourceDialog.querySelector('.resource-provenance pre').textContent=JSON.stringify(data,null,2);
  $('select-script-resource-actor').onclick=async()=>{if(actor&&!busy&&await api('/api/selection',{entity_id:actor.id})){scriptResourceDialog.close();frame(selected());document.querySelector('.workspace-tabs [data-panel="viewport"]').click();}};
  $('inspect-script-resource').onclick=()=>{if(scriptOwner&&!busy){scriptResourceDialog.close();openActorScript(scriptOwner,false,null,dialogue?{semantic_id:record.id,pc:data.pc}:null);}};
  if(dialogue){
    const script=resourceRecords.find(item=>item.asset_kind==='script'&&item.semantic_id===data.script_id);
    if(script){const button=document.createElement('button');button.className='parent-script-button';button.textContent='View parent script metadata';button.onclick=()=>openScriptResource({id:script.semantic_id,type:'script',label:script.name ?? script.semantic_id,source:script.source_record?.prot_entry_name ?? record.source,data:script});scriptResourceDialog.querySelector('.dialog-actions').before(button);}
  }else{
    const movementHost=$('resource-movements'),context=resourceStateKey();
    for(const target of data.movement_targets??[]){
      const button=document.createElement('button');button.textContent=`${target.mnemonic} at ${scriptOffset(target.pc)} · X ${target.target_position.x}, Z ${target.target_position.z} · Y unknown`;
      button.disabled=!scriptOwner||!state.capabilities?.actor_script_preview;
      button.onclick=()=>{if(busy||context!==resourceStateKey()||!scriptOwner)return;scriptResourceDialog.close();openActorScript(scriptOwner,false,null,null,target.pc);};movementHost.append(button);
    }
    if(!data.movement_targets?.length){const note=document.createElement('p');note.textContent=Array.isArray(data.movement_targets)?'No movement targets decoded in inspected paths.':'Refresh resources to discover movement targets.';movementHost.append(note);}
    const modelHost=$('resource-model-selections');
    for(const reference of data.model_selection_references??[]){
      const button=document.createElement('button');button.textContent=`Selector ${reference.model_selector_signed} · pool flag ${reference.high_pool_flag?'set':'clear'} · ${scriptOffset(reference.pc)}`;button.disabled=!scriptOwner||!state.capabilities?.actor_script_preview;
      button.onclick=()=>{if(busy||context!==resourceStateKey()||!scriptOwner)return;scriptResourceDialog.close();openActorScript(scriptOwner,false,null,null,reference.pc);};modelHost.append(button);
    }
    if(!data.model_selection_references?.length){const note=document.createElement('p');note.textContent=Array.isArray(data.model_selection_references)?'No model selectors decoded in inspected paths.':'Refresh resources to discover model selectors.';modelHost.append(note);}
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
async function exportNpcDrafts(entityId){
  if(busy||!canEdit())return;
  const dialog=document.createElement('dialog');dialog.id='draft-export-result';dialog.className='project-dialog';
  const title=document.createElement('h2');title.textContent='Experimental disc export';
  const message=document.createElement('p');message.textContent='Building a separate disc from supported authored changes across this project. This can take a minute.';
  const details=document.createElement('pre');details.style.whiteSpace='pre-wrap';details.style.overflowWrap='anywhere';
  let exporting=true;
  const close=document.createElement('button');close.textContent='Close';close.disabled=true;close.onclick=()=>dialog.close();
  dialog.addEventListener('cancel',event=>{if(exporting)event.preventDefault();});
  dialog.append(title,message,details,close);document.body.append(dialog);dialog.addEventListener('close',()=>dialog.remove(),{once:true});dialog.showModal();
  setBusy(true);
  try{
    if(liveFollow.pending)await liveFollow.pending;
    const response=await fetch(entityId?'/api/export/actor-drafts':'/api/export/project',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(entityId?{entity_id:entityId}:{})});
    const result=await response.json();
    if(!response.ok||result.error)throw new Error(result.error||'Draft export failed');
    if(!result.report_path||!result.disc_path||!result.output_sha256)throw new Error('Export service returned an incomplete report');
    message.textContent='Export complete. Gameplay remains unverified. The game has not been launched.';
    details.textContent=`Disc: ${result.disc_path}\nReport: ${result.report_path}\nSHA-256: ${result.output_sha256}`+(result.input_project_path?`\nSaved export inputs: ${result.input_project_path}`:'');
    notify('Experimental disc exported');
  }catch(error){message.textContent=error.message;notify(error.message,true);}
  finally{exporting=false;close.disabled=false;setBusy(false);}
}
function renderInspector(){
  const npc=selectedNpcDraft();
  if(npc){
    const id=npcDraftSelection;
    $('selection-summary').textContent=`${npc.name} · Authored NPC draft`;
    $('inspector').innerHTML=`<section class="component"><h3>Authored NPC draft</h3>${property('Identity',id)}${property('Retail donor',npc.donor_entity_id)}<p class="field-note">No retail placement or runtime identity exists for this draft. X/Z handles snap to the required 64-unit grid. Preview uses the retail donor assignment; shared authored assets may affect its appearance. Playable creation remains unverified.</p><form id="draft-inspector-form"><label>X <input name="x" type="number" min="64" max="16384" step="64" required></label><label>Z <input name="z" type="number" min="64" max="16384" step="64" required></label><button type="submit">Apply draft position</button></form><button id="frame-npc-draft">Frame draft</button><button id="delete-npc-draft">Delete draft</button></section>`;
    const preview=activeScenePreview()?.entities.find(item=>item.entity_id===id);
    const poseLabel={imported_scene_animation_frame0:'Imported animation · frame 0',authored_scene_animation_frame0:'Authored shared animation · frame 0',reference_party_idle:'Reference party idle · frame 0',reference_global_loop:'Reference shared clip · frame 0',single_object_static:'Static single-object model'}[preview?.pose_kind]??'Pose unavailable in this view';
    const poseNote=document.createElement('p');poseNote.className='field-note';poseNote.id='draft-pose-note';poseNote.textContent=`Preview pose: ${poseLabel}. A sampled frame does not establish an idle stance or runtime playback.`;$('draft-inspector-form').before(poseNote);
    const donor=entities().find(entity=>entity.id===npc.donor_entity_id);
    if(donor?.components?.ModelRenderer?.asset_id&&['imported_scene_animation_frame0','authored_scene_animation_frame0'].includes(preview?.pose_kind)){
      const inspectPose=document.createElement('button');inspectPose.id='inspect-draft-donor-animation';inspectPose.textContent='Inspect donor animation';inspectPose.onclick=()=>openModel(donor.components.ModelRenderer.asset_id,'scene-header',donor.id);poseNote.after(inspectPose);
    }
    const nameForm=document.createElement('form');nameForm.id='draft-name-form';
    const nameLabel=document.createElement('label');nameLabel.textContent='Name ';const nameInput=document.createElement('input');nameInput.name='name';nameInput.required=true;nameInput.maxLength=120;nameInput.value=npc.name;nameLabel.append(nameInput);
    const rename=document.createElement('button');rename.type='submit';rename.textContent='Rename';nameForm.append(nameLabel,rename);$('draft-inspector-form').before(nameForm);
    nameForm.onsubmit=event=>{event.preventDefault();api('/api/command',{type:'rename_actor_draft',entity_id:id,name:nameInput.value});};
    const duplicate=document.createElement('button');duplicate.id='duplicate-npc-draft';duplicate.textContent='Duplicate draft';duplicate.title='Creates an independent draft at the same position, then selects it to move';$('delete-npc-draft').before(duplicate);
    duplicate.onclick=async()=>{const previous=new Set(Object.keys(state.actor_drafts??{}));if(await api('/api/command',{type:'duplicate_actor_draft',entity_id:id,name:npc.name.slice(0,115)+' copy'})){const created=Object.keys(state.actor_drafts??{}).find(key=>!previous.has(key));if(created){selectNpcDraft(created);frameNpcDraft();notify('Draft duplicated at the same position. Move it with X/Z or the viewport handles.');}}};
    for(const control of [nameInput,rename,duplicate])control.disabled=busy||!canEdit();
    const donorForm=document.createElement('form');donorForm.id='draft-donor-form';
    const donorLabel=document.createElement('label');donorLabel.textContent='Retail donor ';const donorSelect=document.createElement('select');donorSelect.name='donor';donorSelect.setAttribute('aria-label','Draft retail donor');
    for(const actor of entities()){const option=document.createElement('option');option.value=actor.id;option.textContent=actor.name??actor.id;donorSelect.append(option);}donorSelect.value=npc.donor_entity_id;donorLabel.append(donorSelect);
    const donorApply=document.createElement('button');donorApply.type='submit';donorApply.textContent='Change donor';const donorNote=document.createElement('p');donorNote.className='field-note';donorNote.textContent='Changes the retail appearance and cloned script used at export. Name, identity and position stay unchanged. Gameplay behavior needs verification.';
    donorForm.append(donorLabel,donorApply,donorNote);nameForm.after(donorForm);donorSelect.disabled=donorApply.disabled=busy||!canEdit();
    donorForm.onsubmit=event=>{event.preventDefault();api('/api/command',{type:'set_actor_draft_donor',entity_id:id,donor_entity_id:donorSelect.value});};
    const form=$('draft-inspector-form');form.elements.x.value=npc.position.x;form.elements.z.value=npc.position.z;
    form.querySelectorAll('input,button').forEach(control=>control.disabled=busy||!canEdit());
    form.onsubmit=event=>{event.preventDefault();api('/api/command',{type:'set_actor_draft_position',entity_id:id,position:{x:Number(form.elements.x.value),z:Number(form.elements.z.value)}});};
    $('frame-npc-draft').textContent=sceneRepresentation==='retail'?'Show in authored scene':'Frame draft';
    $('frame-npc-draft').onclick=frameNpcDraft;
    const inspectDraft=document.createElement('button');inspectDraft.id='inspect-npc-draft';inspectDraft.textContent='Inspect serialized candidate';inspectDraft.disabled=busy;inspectDraft.onclick=()=>openActorCandidate({id,name:npc.name,components:{Transform:{effective:{position:{...npc.position,y:null}}}}});$('inspector').querySelector('section').append(inspectDraft);
    const exportDraft=document.createElement('button');exportDraft.id='export-npc-drafts';exportDraft.textContent='Export experimental disc';exportDraft.disabled=busy||!canEdit();exportDraft.onclick=()=>exportNpcDrafts(id);$('inspector').querySelector('section').append(exportDraft);
    $('delete-npc-draft').disabled=busy||!canEdit();$('delete-npc-draft').onclick=()=>api('/api/command',{type:'delete_actor_draft',entity_id:id});
    return;
  }
  const environment=selectedEnvironment();
  if(environment){
    $('selection-summary').textContent=environment.name;
    const source=environment.source_record,transform=source.imported_transform;
    $('inspector').innerHTML=`<section class="component"><h3>Environment <small>Source and overrides</small></h3>${property('Identity',environment.entity_id)}${property('Model',environment.asset_id ?? 'Unresolved')}${property('Geometry',environment.renderable?environment.pose_kind:environment.reason ?? 'Unavailable')}<button id="frame-environment">Frame object</button></section><section class="component"><h3>Retail transform</h3>${property('Position',JSON.stringify(transform.position))}${property('Rotation · PSX units',JSON.stringify(transform.rotation_psx))}<p class="field-note">4096 angle units equal one turn. Source placement and initial pose; scripts and runtime visibility are not evaluated.</p></section><section class="component"><h3>Source and bindings</h3><pre>${escapeHTML(JSON.stringify({source,evidence:environment.evidence},null,2))}</pre></section>`;
    $('frame-environment').onclick=frameEnvironment;
    if(source.record_offset&&source.source_record?.map_sha256){
      if(!environment.entity_id.includes('/decorations/')){
        const enable=document.createElement('button');enable.id='enable-shared-move';enable.textContent='Enable shared move handles';
        enable.disabled=busy||!canEdit()||sceneRepresentation!=='authored'||!scenePreviewCurrent();
        enable.onclick=()=>{if(!canEdit()||!scenePreviewCurrent()||selectedEnvironment()?.entity_id!==environment.entity_id)return;sharedEnvironmentMove={id:environment.entity_id,key:resourceStateKey()};enable.textContent='Shared move handles enabled';notify('X/Z handles affect every use of this placement record. Undo restores the edit.');draw();};
        $('frame-environment').after(enable);
      }
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
          const input=document.createElement('input');input.type='number';input.step='1';input.min=field==='offset'?'-32768':'0';input.max=field==='offset'?'32767':'4095';input.value=current?.[field]?.[axis]??base[axis];input.setAttribute('aria-label',`${individual?'Individual ':''}${label} ${axis.toUpperCase()}`);input.disabled=state.project?.mode==='live'||sceneRepresentation!=='authored'||!scenePreviewCurrent();row.append(input);section.append(row);inputs.push({field,axis,input,base:base[axis]});
        }
      }
      const effective=document.createElement('p');effective.textContent=`${scenePreviewCurrent()?'Effective position':'Previous preview position (refresh pending)'}: ${JSON.stringify(environment.effective_transform?.position??transform.position)}`;section.append(effective);
      const apply=document.createElement('button');apply.textContent=individual?'Apply individual transform':'Apply shared transform';apply.disabled=state.project?.mode==='live'||sceneRepresentation!=='authored'||!scenePreviewCurrent();
      const inspectorKey=sceneKey;
      apply.onclick=async()=>{
        if(sceneRepresentation!=='authored'||!scenePreviewCurrent()||sceneKey!==inspectorKey)return;
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
  if(state.capabilities?.actor_script_preview)html+=`<section class="component"><h3>Script and dialogue <small>Inspect source</small></h3><p class="field-note">Inspect decoded dialogue and supported instruction paths. ${state.capabilities?.actor_dialogue_authoring?'The inspector checks whether this actor supports text edits.':'Unknown instructions stop decoding.'}</p><button id="inspect-script" class="model-preview-button">Inspect script and dialogue</button></section>`;
  $('inspector').innerHTML=html;
  if($('choose-appearance'))$('choose-appearance').onclick=()=>openAppearanceOptions(entity);
  if($('clear-appearance'))$('clear-appearance').onclick=()=>api('/api/command',{type:'clear_actor_appearance',entity_id:entity.id});
  if($('preview-appearance'))$('preview-appearance').onclick=()=>openModel(components.ActorAppearance.effective.asset_id,'authored-appearance',entity.id);
  if($('inspect-script'))$('inspect-script').onclick=()=>openActorScript(entity);
  if($('inspect-script')&&state.capabilities?.actor_candidate_inspection){const button=document.createElement('button');button.textContent='Inspect NPC creation candidate';button.id='inspect-actor-candidate';button.disabled=busy;button.className='model-preview-button';button.onclick=()=>openActorCandidate(entity);$('inspect-script').after(button);}
  if($('inspect-model'))$('inspect-model').onclick=()=>openModel(components.ModelRenderer.asset_id);
  const animatedAsset=(state.assets ?? []).find(asset=>asset.id===components.ModelRenderer?.asset_id && asset.animation_support?.supported);
  const actorAnimation=components.Animation?.preview_support;
  if(actorAnimation?.supported && $('inspect-model')){const button=document.createElement('button');button.className='model-preview-button';button.textContent='Preview imported scene animation';button.disabled=busy;button.title='Verify and decode this actor’s imported animation association';button.onclick=()=>openModel(components.ModelRenderer.asset_id,'scene-header',entity.id);$('inspect-model').after(button);}
  if(actorAnimation?.supported && $('inspect-model')){const button=document.createElement('button');button.className='model-preview-button';button.dataset.animationEdit='true';button.textContent=components.Animation?.authored_channels?'Edit authored animation channels':'Author animation channels';button.disabled=busy||state.project.mode!=='edit';button.onclick=()=>openAnimationChannels(entity);$('inspect-model').after(button);}
  if(animatedAsset && $('inspect-model')){const button=document.createElement('button');button.className='model-preview-button';button.textContent='Preview reference animation';button.disabled=busy;button.title='Supported reference clips for this model; separate from the placement animation ID';button.onclick=()=>openModel(animatedAsset.id,animatedAsset.animation_support.clips[0].id,null,'imported',entity.id);$('inspect-model').after(button);}
  if($('inspect-templates'))$('inspect-templates').onclick=showTemplates;
  $('inspector').querySelectorAll('[data-axis]').forEach(input=>input.addEventListener('change',async()=>{
    const axis=input.dataset.axis;
    if(input.value===''){await api('/api/command',{type:'clear_transform',entity_id:entity.id,axes:[axis]});return;}
    const value=Number(input.value);if(!Number.isFinite(value)){notify('Transform values must be finite numbers.',true);renderInspector();return;}
    await api('/api/command',{type:'set_transform',entity_id:entity.id,position:{[axis]:value}});
  }));
}

const animationEditDialog=document.createElement('dialog');animationEditDialog.className='project-dialog';document.body.append(animationEditDialog);
async function openAnimationChannels(entity,initialChannel=null){
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
    if(initialChannel&&Number.isInteger(initialChannel.frame)&&Number.isInteger(initialChannel.object)&&initialChannel.frame>=0&&initialChannel.frame<binding.frame_count&&initialChannel.object>=0&&initialChannel.object<binding.bone_count){form.elements.frame.value=initialChannel.frame;form.elements.object.value=initialChannel.object;}
    const clearChannel=document.createElement('button');clearChannel.type='button';clearChannel.textContent='Clear selected channel contribution';clearChannel.className='clear-animation-channel';form.querySelector('.clear-animation').before(clearChannel);
    for(const group of ['translation','rotation_psx'])for(const axis of ['x','y','z']){const limits=result[group],label=document.createElement('label');label.textContent=`${group==='translation'?'Translation':'Rotation (PSX units)'} ${axis.toUpperCase()}`;const input=document.createElement('input');input.name=`${group}_${axis}`;input.type='number';input.min=limits.minimum;input.max=limits.maximum;input.step=limits.step;input.placeholder='Retail';label.append(input);fields.append(label);}
    let channelRequest=0,channelDirty=false,channelFrame=0,channelObject=0;
    const discardChannel=document.createElement('button');discardChannel.type='button';discardChannel.textContent='Discard unapplied channel changes';discardChannel.disabled=true;fields.after(discardChannel);
    fields.querySelectorAll('input').forEach(input=>input.oninput=()=>{channelDirty=true;discardChannel.disabled=false;});
    const retail=document.createElement('p');retail.className='field-note';fields.before(retail);
    const refresh=async()=>{
      if(channelDirty){form.elements.frame.value=channelFrame;form.elements.object.value=channelObject;error.textContent='Apply or discard your channel changes before switching frames or objects.';return;}
      const request=++channelRequest,frame=Number(form.elements.frame.value),object=Number(form.elements.object.value);channelFrame=frame;channelObject=object;
      const edit=edits.find(e=>e.frame_index===frame&&e.object_index===object);
      clearChannel.disabled=!edit;
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
    const apply=async command=>{
      if(busy||!current())return;
      const channel={frame:channelFrame,object:channelObject};
      if(!await api('/api/command',command,{dialog:animationEditDialog,success:'Animation override updated. Save project to persist.'})){error.textContent=$('status').textContent;return;}
      const actor=selected();if(actor?.id===entity.id&&state.project.mode==='edit')await openAnimationChannels(actor,channel);
    };
    clearChannel.onclick=()=>{
      if(channelDirty){error.textContent='Apply or discard unapplied channel changes before clearing the selected contribution.';return;}
      const next=edits.filter(edit=>edit.frame_index!==channelFrame||edit.object_index!==channelObject);
      apply(next.length?{type:'set_animation_channels',entity_id:entity.id,value:{animation_id:binding.semantic_id,source_record_sha256:binding.source_record.record_sha256,edits:next}}:{type:'clear_animation_channels',entity_id:entity.id});
    };
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
function openNpcDrafts(focusId=null){
  if(busy)return;
  const dialog=document.createElement('dialog');dialog.id='npc-drafts-dialog';
  dialog.innerHTML='<h2>NPC drafts</h2><p>Project-local new NPCs. Changes support Undo/Redo; Save persists them. Drafts appear in the viewport; playable builds are not yet available.</p><p class="dialog-error" role="alert"></p><button type="button">Close</button>';
  dialog.querySelector('button').onclick=()=>dialog.close();
  dialog.addEventListener('close',()=>dialog.remove(),{once:true});
  const drafts=Object.entries(state.actor_drafts??{});
  if(!drafts.length){const empty=document.createElement('p');empty.textContent='No drafts. Select an imported actor and use Inspect NPC creation candidate to create one.';dialog.append(empty);}
  for(const [id,draft] of drafts){
    if(focusId&&id!==focusId)continue;
    const form=document.createElement('form');
    form.innerHTML='<h3></h3><p class="field-note"></p><label>X <input name="x" type="number" min="64" max="16384" step="64" required></label><label>Z <input name="z" type="number" min="64" max="16384" step="64" required></label><button type="submit">Apply draft position</button><button type="button">Delete draft</button>';
    form.querySelector('h3').textContent=draft.name;
    form.querySelector('p').textContent=`${id} · Donor: ${draft.donor_entity_id}`;
    form.elements.x.value=draft.position.x;form.elements.z.value=draft.position.z;
    const editable=state.project?.mode==='edit';form.querySelectorAll('input,button').forEach(control=>control.disabled=!editable);
    form.onsubmit=async event=>{event.preventDefault();await api('/api/command',{type:'set_actor_draft_position',entity_id:id,position:{x:Number(form.elements.x.value),z:Number(form.elements.z.value)}},{dialog,success:'Draft position updated.'});};
    form.querySelector('button[type=button]').onclick=()=>api('/api/command',{type:'delete_actor_draft',entity_id:id},{dialog,success:'Draft deleted. Undo restores it.'});
    const focus=document.createElement('button');focus.type='button';focus.textContent='Frame draft';focus.disabled=draft.scene_id!==state.scene?.id;
    focus.onclick=()=>{dialog.close();frame({id,components:{Transform:{imported:{position:{...draft.position,y:null}}}}});};form.append(focus);
    dialog.append(form);
  }
  document.body.append(dialog);dialog.showModal();
}

async function openActorCandidate(entity){
  if(busy)return;
  const sceneId=state.scene?.id,controller=new AbortController();
  const dialog=document.createElement('dialog');
  dialog.innerHTML='<h2>NPC creation candidate</h2><p>Inspecting the retail donor…</p><button>Close</button>';
  dialog.querySelector('button').onclick=()=>dialog.close();
  dialog.addEventListener('close',()=>{controller.abort();dialog.remove();},{once:true});
  document.body.append(dialog);dialog.showModal();
  try{
    const response=await fetch('/api/actor-candidate-inspection',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({entity_id:entity.id}),signal:controller.signal});
    const report=await response.json();if(!response.ok||report.error)throw new Error(report.error||'Candidate inspection failed');
    if(!dialog.open)return;
    if(report.entity_id!==entity.id)throw new Error('Candidate identity mismatch');
    if(state.scene?.id!==sceneId)throw new Error('Active scene changed; inspect this donor again');
    const rows=report.actor.script_coverage.records;
    const containerStatus=report.container.supported===false?`unavailable (${report.container.reason})`:`${report.container.growth_bytes} bytes`;
    dialog.querySelector('p').textContent=`${entity.name}: ${report.includes_project_overrides ? "retail donor with authored X/Z placement" : "retail donor at imported placement"}; other project overrides are excluded. This inspection does not create an NPC. ${report.actor.reached_spawn_changes.length} decoded spawn references need updates; ${rows.filter(row=>row.coverage!=='decoded_supported_paths').length} scripts remain partial. Container growth: ${containerStatus}. Overlapping archive entries: ${report.archive.overlapping_entries.length}. Playable creation remains unavailable until script, scheduling and archive dependencies are resolved.`;
    const placement=document.createElement('p');
    const included=Object.entries(report.included_overrides?.Transform?.position??{}).map(([axis,value])=>`${axis.toUpperCase()}=${value}`);
    const excluded=[...(report.excluded_override_components??[]),...(report.excluded_transform_axes??[]).map(axis=>`Position ${axis.toUpperCase()}`)];
    placement.textContent=`Candidate placement: ${included.length?included.join(', ')+'; remaining axes inherit the donor':'inherited from the retail donor'}.${excluded.length?' Excluded authored values: '+excluded.join(', ')+'.':''}`;
    dialog.append(placement);
    const form=document.createElement('form');
    form.innerHTML='<h3>New NPC draft</h3><label>Name <input name="name" maxlength="120" required></label><label>X <input name="x" type="number" min="64" max="16384" step="64" required></label><label>Z <input name="z" type="number" min="64" max="16384" step="64" required></label><p>Creates a saved-project draft through Undo/Redo. Use Save to persist it. Drafts appear in the viewport but are not yet included in playable builds.</p><p class="dialog-error" role="alert"></p><button type="submit">Create NPC draft</button>';
    form.elements.name.value=`${entity.name} draft`;
    const donorPosition=entity.components.Transform.effective.position;
    form.elements.x.value=donorPosition.x;form.elements.z.value=donorPosition.z;
    form.onsubmit=async event=>{
      event.preventDefault();if(busy)return;
      if(state.scene?.id!==sceneId){form.querySelector('.dialog-error').textContent='Active scene changed; inspect this donor again';return;}
      await api('/api/command',{type:'create_actor_draft',donor_entity_id:entity.id,name:form.elements.name.value,position:{x:Number(form.elements.x.value),z:Number(form.elements.z.value)}},{dialog,success:'NPC draft created. Save persists the draft; playable Build is not yet supported.'});
    };
    if(!state.actor_drafts?.[entity.id])dialog.append(form);
    const details=document.createElement('details'),summary=document.createElement('summary'),pre=document.createElement('pre');summary.textContent='Technical evidence';pre.textContent=JSON.stringify(report,null,2);details.append(summary,pre);dialog.append(details);
    const inspect=document.createElement('button');inspect.textContent='Inspect donor script';
    inspect.onclick=()=>{if(busy)return;if(state.scene?.id!==sceneId){dialog.querySelector('p').textContent='Active scene changed; inspect this donor again';return;}dialog.close();openActorScript(entities().find(item=>item.id===(report.donor_entity_id??entity.id))??entity);};
    dialog.append(inspect);
    const dependencies=report.donor_dependencies;
    if(dependencies){
      const info=document.createElement('p');
      info.textContent=`Donor model: ${dependencies.model?.asset_semantic_id??'unresolved'}. Initial animations: ${(dependencies.animations??[]).map(a=>`${a.semantic_id} (${a.frame_count} frames, ${a.channel_count} channels)`).join(', ')||'unavailable'}. Scripts may select other assets at runtime.`;
      dialog.append(info);
      const assetId=dependencies.model?.asset_semantic_id;
      if(assetId){const model=document.createElement('button');model.textContent='Preview donor model';model.onclick=()=>{if(busy)return;if(state.scene?.id!==sceneId){info.textContent='Active scene changed; inspect this donor again';return;}dialog.close();openModel(assetId);};dialog.append(model);}
    }
  }catch(error){if(dialog.open)dialog.querySelector('p').textContent=String(error.message||error);}
}
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
    scriptReport=report;renderDialogueAuthoring();renderTransitionAuthoring();renderMovementAuthoring();updateScriptActions();
    scriptDialog.scrollTop=scroll;
    if(Number.isInteger(focusInstruction)){
      $('script-report').querySelector('.script-instructions').open=true;
      if(!instructionNavigation.select(focusInstruction))notify('The selected instruction was not found in the verified report.',true);
    }
  }catch(error){if(scriptDialog.open){scriptDialog.querySelector('.dialog-error').textContent=error.message;if(refresh){scriptReport=null;scriptDialog.querySelectorAll('.dialogue-run,.transition-entry,.transition-unresolved,[data-clear-unresolved]').forEach(item=>item.remove());}}}finally{setBusy(false);if(focusRun&&scriptDialog.open){const input=[...scriptDialog.querySelectorAll('[data-run-input]')].find(item=>item.dataset.runInput===focusRun);if(input){if(focusRun.includes('/transition/'))input.scrollIntoView({block:'center'});input.focus({preventScroll:true});}}else if(focusDialogue&&scriptDialog.open){const cards=[...scriptDialog.querySelectorAll('.script-dialogue-card')],card=cards.find(item=>item.dataset.dialogueId===focusDialogue.semantic_id) ?? cards.find(item=>Number.isInteger(focusDialogue.pc)&&Number(item.dataset.dialoguePc)===focusDialogue.pc);if(card){card.classList.add('dialogue-focus');card.tabIndex=-1;card.scrollIntoView({block:'start'});card.focus({preventScroll:true});}else notify('The selected dialogue segment was not found in the verified report.',true);}}
}

function renderMovementAuthoring(){
  const authoring=scriptReport?.movement_authoring;if(!authoring)return;
  const section=document.createElement('section');section.className='movement-authoring';
  section.innerHTML='<h3>Script movement targets</h3><p class="field-note">Edit decoded X/Z targets in exact 64-unit steps. Y, branch execution and runtime actor identity remain unresolved. These edits save to the project. Build supports descriptor MAN scenes; Export disc also supports streaming scenes and NPC drafts. Gameplay remains unverified. The instruction table shows retail coordinates; the target overlay offers retail and authored layers.</p>';
  $('script-report').append(section);
  const owner=scriptEntity.id,key=resourceStateKey(),current=()=>!busy&&canEditDialogue()&&key===resourceStateKey()&&scriptEntity?.id===owner;
  const send=async(id,type,values)=>{
    if(!current())return;
    if(await api('/api/command',{type,entity_id:owner,movement_id:id,...(type==='set_movement_target'?{values}:{})})){
      scriptDrafts.delete(id);await openActorScript(scriptEntity,true);
    }else scriptDialog.querySelector('.dialog-error').textContent=$('status').textContent;
  };
  if(authoring.reason){const note=document.createElement('p');note.textContent=authoring.reason;section.append(note);}
  for(const id of authoring.unresolved_overrides??[]){
    const button=document.createElement('button');button.textContent=`Clear unresolved movement ${id}`;button.dataset.clearMovement=id;
    button.onclick=()=>send(id,'clear_movement_target');section.append(button);
  }
  for(const target of authoring.targets??[]){
    const form=document.createElement('form');form.className='movement-entry';form.dataset.movementId=target.semantic_id;
    const title=document.createElement('h4');title.textContent=`${target.mnemonic} at ${scriptOffset(target.pc)}`;
    const layers=document.createElement('p');layers.className='movement-layers';layers.textContent=`Retail X ${target.values.x}, Z ${target.values.z} · Authored ${Object.keys(target.authored_values).length?Object.entries(target.authored_values).map(([a,v])=>`${a.toUpperCase()} ${v}`).join(', '):'none'} · Effective X ${target.effective_values.x}, Z ${target.effective_values.z}${target.target_context!==null?` · actor context ${target.target_context} unresolved`:''}`;
    form.append(title,layers);const fields={};
    for(const axis of ['x','z']){
      const label=document.createElement('label'),input=document.createElement('input');label.textContent=`Target ${axis.toUpperCase()}`;
      input.type='number';input.required=true;input.min='64';input.max='16384';input.step='64';input.value=scriptDrafts.get(target.semantic_id)?.[axis]??target.effective_values[axis];input.setAttribute('aria-label',`Movement ${axis.toUpperCase()} at ${scriptOffset(target.pc)}`);
      fields[axis]=input;label.append(input);form.append(label);
      input.oninput=()=>{scriptDrafts.set(target.semantic_id,Object.fromEntries(Object.entries(fields).map(([a,i])=>[a,i.value])));updateScriptActions();};
    }
    const apply=document.createElement('button'),clear=document.createElement('button'),discard=document.createElement('button');apply.type='submit';apply.textContent='Apply movement';clear.type=discard.type='button';clear.textContent='Clear movement override';discard.textContent='Discard movement draft';form.append(apply,clear,discard);
    form.updateState=()=>{const editable=current();for(const input of Object.values(fields))input.disabled=!editable;apply.disabled=!editable||!Object.values(fields).every(input=>input.value!==''&&input.checkValidity());clear.disabled=!editable||!Object.keys(target.authored_values).length;discard.disabled=busy;discard.hidden=!scriptDrafts.has(target.semantic_id);};
    form.onsubmit=event=>{event.preventDefault();if(!apply.disabled)send(target.semantic_id,'set_movement_target',Object.fromEntries(Object.entries(fields).map(([a,i])=>[a,Number(i.value)])));};
    clear.onclick=()=>send(target.semantic_id,'clear_movement_target');
    discard.onclick=()=>{scriptDrafts.delete(target.semantic_id);for(const [axis,input] of Object.entries(fields))input.value=target.effective_values[axis];updateScriptActions();};
    section.append(form);form.updateState();
  }
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
  const authoring=scriptReport?.dialogue_authoring;
  $('script-authoring-toolbar').hidden=!state.capabilities?.actor_dialogue_authoring||!(authoring?.supported||authoring?.unresolved_overrides?.length||scriptReport?.transition_authoring?.supported||scriptReport?.movement_authoring?.supported||scriptReport?.movement_authoring?.unresolved_overrides?.length);
  const pending=scriptDrafts.size>0;
  $('script-undo').disabled=busy||pending||!canEditDialogue()||!state.history?.can_undo;
  $('script-redo').disabled=busy||pending||!canEditDialogue()||!state.history?.can_redo;
  $('script-save').disabled=busy||pending||!state.project?.dirty;
  $('script-authoring-status').textContent=pending?`${scriptDrafts.size} unapplied draft(s) · Apply or discard before project actions`:busy?'Verifying…':projectSaveStatus();
  for(const form of scriptDialog.querySelectorAll('.dialogue-run'))updateDialogueRun(form);
  for(const form of scriptDialog.querySelectorAll('.transition-entry'))form.updateState();
  for(const form of scriptDialog.querySelectorAll('.movement-entry'))form.updateState();
  for(const button of scriptDialog.querySelectorAll('[data-clear-movement]'))button.disabled=busy||!canEditDialogue();
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
  pendingEntityFrame=null;
  if(entity&&modelsEnabled&&state.capabilities?.scene_preview&&state.scene_preview_source_key&&!scenePreviewCurrent()&&!sceneError){
    pendingEntityFrame={entity,key:sceneRequestKey(),scene:state.scene?.id,project:state.project?.path,revision:cameraRevision};
    return;
  }
  const points=entity?[position(entity)]:(sceneLayers.actors?entities().filter(e=>!hiddenSceneEntities().has(e.id)).map(position):[]);
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
function project(p){const b=basis(),d={x:p.x-camera.target.x,y:p.y-camera.target.y,z:p.z-camera.target.z},dot=v=>d.x*v.x+d.y*v.y+d.z*v.z,depth=camera.distance+dot(b.forward);if(depth<=camera.distance*.01)return null;const scale=Math.min(width,height)*.9/(camera.projection==='orthographic'?camera.distance:depth);return {x:width/2+dot(b.right)*scale,y:height/2-dot(b.up)*scale,depth,scale};}
function groundAt(x,y,planeY){
  const b=basis(),f=Math.min(width,height)*.9;
  const origin={x:camera.target.x-camera.distance*b.forward.x,y:camera.target.y-camera.distance*b.forward.y,z:camera.target.z-camera.distance*b.forward.z};
  const ray={};for(const axis of ['x','y','z']){const offset=(x-width/2)/f*b.right[axis]-(y-height/2)/f*b.up[axis];if(camera.projection==='orthographic'){origin[axis]+=offset*camera.distance;ray[axis]=b.forward[axis];}else ray[axis]=b.forward[axis]+offset;}
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
  if(scenePose&&(!scenePreviewCurrent()||scenePose.key!==sceneKey||state.project?.mode!=='edit'))clearScenePose();
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
    if(!sceneLayers.actors||hiddenSceneEntities().has(entity.id))continue;
    const active=!selectedEnvironment()&&!selectedNpcDraft()&&entity.id===state.selection?.entity_id,rendered=sceneModelsReady()&&sceneRenderer.hasEntity(entity.id),radius=active?7:4.5;
    if(rendered&&!active)continue;
    projected.push({id:entity.id,x:p.x,y:p.y});ctx.beginPath();ctx.ellipse(p.x,p.y+5,active?12:7,active?4:2.5,0,0,Math.PI*2);ctx.fillStyle='#02090966';ctx.fill();
    ctx.beginPath();ctx.moveTo(p.x,p.y-radius);ctx.lineTo(p.x+radius,p.y);ctx.lineTo(p.x,p.y+radius);ctx.lineTo(p.x-radius,p.y);ctx.closePath();ctx.fillStyle=active?'#c9edce':sceneRepresentation==='authored'&&authored(entity)?'#d2ae70':'#759d8d';ctx.fill();ctx.strokeStyle=active?'#f1fff0':'#a8c6b6';ctx.lineWidth=active?1.5:1;ctx.stroke();
    if(active){
      ctx.font='11px "Segoe UI", sans-serif';ctx.fillStyle='#c8ddd1';ctx.fillText(entity.name ?? entity.id,p.x+12,p.y-10);
      if(sceneRepresentation==='authored'&&(Object.keys(entity.components?.Transform?.authored?.position??{}).length||draft?.id===entity.id)){
        const original=displayPosition(entity.components?.Transform?.imported?.position),q=project(original);
        if(q&&Math.hypot(q.x-p.x,q.y-p.y)>3){ctx.save();ctx.setLineDash([4,4]);line(original,world,'#d6ad6c',1.5);ctx.setLineDash([]);ctx.strokeStyle='#d6ad6c';ctx.strokeRect(q.x-4,q.y-4,8,8);ctx.fillStyle='#e7c188';ctx.fillText('Imported',q.x+8,q.y+14);ctx.restore();}
      }
      if(canEdit()&&sceneRepresentation==='authored'){const length=camera.distance*.085;for(const [axis,color] of [['x','#e0988a'],['z','#8bbbdc']]){const end={...world,[axis]:world[axis]+length},q=project(end);if(!q)continue;line(world,end,color,2);ctx.fillStyle=color;ctx.beginPath();ctx.arc(q.x,q.y,4,0,Math.PI*2);ctx.fill();ctx.font='bold 10px "Segoe UI",sans-serif';ctx.fillText(axis.toUpperCase(),q.x+7,q.y+3);handles.push({axis,x:q.x,y:q.y,start:p});}}
    }
  }
  drawEnvironmentSelection();drawCoordinateProbe();drawScriptTargets();
  const scenery=selectedEnvironment(),movable=movableSelection();
  if((scenery||selectedNpcDraft())&&movable&&canEdit()){
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
  pendingEntityFrame=null;
  if(busy||drag)return;const p=pointer(event),entity=movableSelection();canvas.focus();canvas.setPointerCapture(event.pointerId);
  const handle=event.button===0 && !pickScriptTargets && entity && canEdit()?handles.find(h=>Math.hypot(h.x-p.x,h.y-p.y)<12):null;
  drag={pointerId:event.pointerId,context:resourceStateKey(),start:p,last:p,moved:false,type:handle?'transform':event.button===2||event.button===1||event.shiftKey?'pan':'orbit',handle,entity:entity?.id,original:entity?position(entity):null,snapStep:$('transform-snap').checked?Number($('transform-snap-step').value):1};
  if(handle)drag.ground=groundAt(p.x,p.y,drag.original.y);
  if(handle&&state.actor_drafts?.[entity?.id])drag.snapStep=64;
  canvas.classList.add('dragging');
});
canvas.addEventListener('pointermove',event=>{
  if(!drag||event.pointerId!==drag.pointerId)return;const p=pointer(event),dx=p.x-drag.last.x,dy=p.y-drag.last.y;
  if(Math.hypot(p.x-drag.start.x,p.y-drag.start.y)>3)drag.moved=true;
  if(drag.moved){
    if(drag.type==='transform'){const point=groundAt(p.x,p.y,drag.original.y);if(point&&drag.ground){const axis=drag.handle.axis;draft={id:drag.entity,position:{...drag.original,[axis]:snappedTransformCoordinate(drag.original[axis]+point[axis]-drag.ground[axis],drag.snapStep)}};}}
    else if(drag.type==='orbit'){camera.yaw-=dx*.006;camera.pitch=Math.max(.12,Math.min(Math.PI/2,camera.pitch+dy*.005));cameraRevision++;}
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
  if(finished.type==='transform' && edit){const axis=finished.handle.axis;if(edit.position[axis]!==finished.original[axis]){if(state.actor_drafts?.[finished.entity])await api('/api/command',{type:'set_actor_draft_position',entity_id:finished.entity,position:{...state.actor_drafts[finished.entity].position,[axis]:edit.position[axis]}});else if(finished.entity.startsWith('environment://'))await moveDecoration(finished.entity,axis,edit.position[axis]);else await api('/api/command',{type:'set_transform',entity_id:finished.entity,position:{[axis]:edit.position[axis]}});}}
  else if(!finished.moved && event.button===0){
    if(pickScriptTargets&&currentScriptTargets()&&finished.context===resourceStateKey()){
      const hits=scriptTargetHits.filter(hit=>Math.hypot(hit.x-p.x,hit.y-p.y)<10||(hit.label&&p.x>=hit.label.x&&p.x<=hit.label.x+hit.label.w&&p.y>=hit.label.y&&p.y<=hit.label.y+hit.label.h));
      if(hits.length===1){scriptTargetTools.querySelector('select').value=hits[0].pc;await inspectScriptTarget(hits[0].pc);}
      else if(hits.length>1){notify('Several script targets overlap here. Choose an instruction in the target selector.');scriptTargetTools.querySelector('select').focus();}
      else notify('No script target at this point');
      draw();return;
    }
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
    if(hit){if(state.actor_drafts?.[hit])selectNpcDraft(hit);else if(environmentEntities().some(e=>e.entity_id===hit))selectEnvironment(hit);else{environmentSelection=null;await api('/api/selection',{entity_id:hit});}}
  }
  draw();
});
canvas.addEventListener('pointercancel',event=>{if(event.pointerId===drag?.pointerId)cancelViewportGesture();});
canvas.addEventListener('lostpointercapture',event=>{if(event.pointerId===drag?.pointerId)cancelViewportGesture();});
function zoomSceneAt(x,y,delta){
  const before=groundAt(x,y,camera.target.y);
  camera.distance=Math.max(20,Math.min(1e8,camera.distance*Math.exp(delta*.001)));
  const after=groundAt(x,y,camera.target.y);
  if(before&&after){camera.target.x+=before.x-after.x;camera.target.z+=before.z-after.z;}
  cameraRevision++;
}
canvas.addEventListener('wheel',event=>{pendingEntityFrame=null;event.preventDefault();cancelViewportGesture();const p=pointer(event);zoomSceneAt(p.x,p.y,event.deltaY);draw();},{passive:false});

// Unposed assets stay object-local. Only decoder-provided frames assemble objects.
const modelCanvas=$('model-canvas');let modelRenderer=null,modelRenderSource=null,modelRenderObject=null,modelRenderFrame=null;
const exportDialog=document.createElement('dialog');document.body.append(exportDialog);
let model=null, modelDrag=null, modelRequest=0;
let modelTextures=new Map();
let modelAssetId=null, modelEntityId=null, modelSceneEntityId=null, animationFrame=0, animationTick=null, animationClock=null;
const modelView={yaw:.55,pitch:-.18,zoom:1,center:[0,0,0],radius:1};
let modelSceneContext=null,scenePoseTick=null,scenePoseClock=null;
const scenePoseBar=document.createElement('div');scenePoseBar.hidden=true;scenePoseBar.innerHTML='<span></span> <input type="range" min="0" value="0" aria-label="Scene pose frame"> <button type="button" data-play>Play scene preview</button> <label>Preview fps <select aria-label="Scene preview rate"><option>5</option><option selected>10</option><option>15</option><option>30</option><option>60</option></select></label> <button type="button" data-restore>Restore scene pose</button>';$('frame-selected').after(scenePoseBar);
const showScenePose=document.createElement('button');showScenePose.type='button';showScenePose.id='show-frame-in-scene';showScenePose.textContent='Inspect animation in scene';$('animation-frame-label').after(showScenePose);
function clearScenePose(restore=true){
  stopScenePosePlayback();const previous=scenePose;scenePose=null;scenePoseBar.hidden=true;
  if(restore&&previous&&scenePreviewCurrent()&&sceneRenderer){const failures=sceneRenderer.load(structuredClone(scenePreview));if(failures.length)sceneError=failures.join('; ');}
}
function scenePoseDocument(base,preview,entityId,frame){
  const target=base.entities.find(e=>e.entity_id===entityId);
  if(!target||!Array.isArray(preview.frames?.[frame]?.vertices))throw new Error('Choose a loaded actor animation frame.');
  const key='inspection-pose:'+entityId,geometry={...preview,vertices:preview.frames[frame].vertices};delete geometry.frames;
  const result=structuredClone(base);result.entities.find(e=>e.entity_id===entityId).geometry_key=key;result.entities.find(e=>e.entity_id===entityId).renderable=true;
  const used=new Set(result.entities.map(e=>e.geometry_key));result.assets=result.assets.filter(a=>used.has(a.geometry_key));
  if(result.assets.length>=128)throw new Error('Scene has no spare geometry capacity for isolated animation inspection.');
  result.assets.push({geometry_key:key,asset_id:preview.semantic_id,preview:geometry});
  return {document:result,geometryKey:key};
}
function updateScenePoseFrame(frame){
  if(!scenePose||!scenePreviewCurrent()||scenePose.key!==sceneKey)return;
  if(sceneRenderer.updateVertices(scenePose.geometryKey,scenePose.preview.frames[frame].vertices)){
    scenePose.frame=frame;scenePoseBar.querySelector('span').textContent=`Inspection only · ${scenePose.name} · frame ${frame+1}/${scenePose.preview.frames.length}`;
    scenePoseBar.querySelector('input').value=frame;draw();
  }
}
scenePoseBar.querySelector('[data-restore]').onclick=()=>{clearScenePose();draw();};
scenePoseBar.querySelector('input').oninput=event=>{stopScenePosePlayback();try{updateScenePoseFrame(Number(event.target.value));}catch(error){clearScenePose();notify(error.message,true);draw();}};
function stopScenePosePlayback(){
  if(scenePoseTick!==null)cancelAnimationFrame(scenePoseTick);
  scenePoseTick=null;scenePoseClock=null;scenePoseBar.querySelector('[data-play]').textContent='Play scene preview';
}
scenePoseBar.querySelector('select').onchange=()=>{scenePoseClock=null;};
document.addEventListener('visibilitychange',()=>{if(document.hidden)stopScenePosePlayback();});
scenePoseBar.querySelector('[data-play]').onclick=()=>{
  if(scenePoseTick!==null){stopScenePosePlayback();return;}
  const session=scenePose;if(!session)return;
  scenePoseBar.querySelector('[data-play]').textContent='Pause scene preview';
  const tick=time=>{
    if(scenePose!==session||!scenePreviewCurrent()||session.key!==sceneKey||state.project?.mode!=='edit'||busy||document.hidden||!modelsEnabled||sceneRenderer.lost||$('model-dialog').open){stopScenePosePlayback();return;}
    if(scenePoseClock===null)scenePoseClock=time;
    const step=1000/Number(scenePoseBar.querySelector('select').value),advance=Math.floor((time-scenePoseClock)/step);
    try{if(advance){scenePoseClock+=advance*step;updateScenePoseFrame((session.frame+advance)%session.preview.frames.length);}}
    catch(error){stopScenePosePlayback();notify(error.message,true);return;}
    if(scenePose===session)scenePoseTick=requestAnimationFrame(tick);else stopScenePosePlayback();
  };
  scenePoseTick=requestAnimationFrame(tick);
};
showScenePose.onclick=()=>{
  if(busy||state.project?.mode!=='edit'||!scenePreviewCurrent()||modelSceneContext!==sceneRequestKey()||!modelSceneEntityId||!model?.frames?.length||$('shape-file').files?.length)return;
  try{
    stopScenePosePlayback();const isolated=scenePoseDocument(scenePreview,model,modelSceneEntityId,animationFrame);
    const failures=sceneRenderer.load(isolated.document);if(failures.length)throw new Error(failures.join('; '));
    scenePose={key:sceneKey,geometryKey:isolated.geometryKey,preview:model,frame:animationFrame,name:(modelEntityId?'':'Reference clip · ')+(entities().find(e=>e.id===modelSceneEntityId)?.name??modelSceneEntityId)};
    scenePoseBar.hidden=false;scenePoseBar.querySelector('input').max=model.frames.length-1;
    $('model-dialog').close();updateScenePoseFrame(animationFrame);const actor=entities().find(e=>e.id===modelSceneEntityId);if(actor)frame(actor);
  }catch(error){clearScenePose(false);const failures=sceneRenderer.load(structuredClone(scenePreview));if(failures.length)sceneError=failures.join('; ');notify(error.message,true);draw();}
};

const shapeControls=document.createElement('section');shapeControls.innerHTML='<h3>Model shape</h3><p>Replace object-local vertex and normal coordinates in a same-layout TMD. Topology, materials and object bindings stay fixed. Shape preview is unposed. OBJ must preserve vertex and face order, triangulation and integer source coordinates; normals remain unchanged.</p><button id="shape-source">Download source TMD</button><button id="shape-source-obj">Download shape OBJ</button><button id="shape-download-authored">Download authored OBJ</button><label>Edited TMD or OBJ<input id="shape-file" type="file" accept=".tmd,.obj"></label><button id="shape-upload">Apply shape</button><button id="shape-retail">View retail shape</button><button id="shape-authored">View authored shape</button><button id="shape-clear">Clear shape override</button><p id="shape-status"></p>';$('model-description').after(shapeControls);
async function openModel(assetId,clipId=null,entityId=null,shapeLayer='imported',inspectionEntityId=null){
  if($('model-dialog').open&&$('shape-file').files?.length){$('model-error').textContent='Apply or discard the selected shape file before changing the model view.';$('animation-clip').value=model?.animation?.clip_id??'';return;}
  if(busy)return;stopAnimation();setBusy(true);$('model-error').textContent='';$('animation-clip').disabled=true;const request=++modelRequest,requestedSceneContext=sceneRequestKey();
  try{
    const response=await fetch(shapeLayer==='authored'?'/api/model-shape-preview':entityId?(clipId==='authored-appearance'?'/api/actor-appearance-preview':'/api/actor-animation-preview'):clipId?'/api/animation-preview':'/api/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(entityId?{entity_id:entityId,...(clipId==='authored-channels'?{representation:'authored'}:{})}:{asset_id:assetId,...(clipId?{clip_id:clipId}:{})})});
    const data=await response.json();if(!response.ok||data.error)throw new Error(typeof data.error==='string'?data.error:JSON.stringify(data.error ?? data));
    if(!Array.isArray(data.vertices)||!Array.isArray(data.triangles)||!Array.isArray(data.objects))throw new Error('Model service returned no decoded geometry.');
    if(request!==modelRequest)return;
    if(clipId && (!Array.isArray(data.frames) || !data.frames.length || data.frames.length*data.vertices.length>1000000 || data.frames.some(frame=>frame.coordinate_system!=='retail_psx_actor_local_y_down'||!Array.isArray(frame.vertices)||frame.vertices.length!==data.vertices.length||frame.vertices.some(v=>!Array.isArray(v)||v.length!==3||!v.every(numeric)))))throw new Error('Animation service returned an invalid or oversized posed vertex stream.');
    model=data;modelSceneContext=requestedSceneContext;modelAssetId=assetId;modelEntityId=entityId;modelSceneEntityId=entityId??inspectionEntityId;animationFrame=0;$('model-dialog').querySelector('h2').textContent=entityId?`${entities().find(entity=>entity.id===entityId)?.name ?? entityId} · ${clipId==='authored-appearance'?'Authored appearance':clipId==='authored-channels'?'Authored animation':'Imported animation'}`:assetId.split('/').slice(-2).join(' / ');
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
    $('model-description').textContent=`Drag to orbit · Scroll to zoom · ${clipId?'Decoded rigid animation pose':shapeLayer==='authored'?'Authored object-local shape · Unposed':'Retail object-local geometry · Unposed'} · ${modelTextures.size?(model.texture_scope==='field_party'?'Shared party texture bank':'Static texture address matches'):'Vertex colors'} · Approximate blends; no texture-window or animated palette reconstruction`;
    $('model-object').replaceChildren();
    if(model.frames?.length){const all=document.createElement('option');all.value='all';all.textContent='Animated assembly · supported objects';$('model-object').append(all);}
    for(let index=0;index<model.objects.length;index++){const object=model.objects[index],option=document.createElement('option');option.value=index;option.textContent=`Object ${object.object_index ?? index} · ${object.triangle_count} triangles`;$('model-object').append(option);}
    $('model-diagnostics').textContent=(model.diagnostics ?? []).map(d=>typeof d==='string'?d:d.message ?? (d.kind==='equipment_templates_excluded'?'Equipment template objects 10 and 11 are excluded from this pose.':JSON.stringify(d))).join(' · ');
    configureAnimation(clipId);exportClipControls.hidden=!data.frames?.length;showScenePose.disabled=!modelSceneEntityId||!data.frames?.length||state.project?.mode!=='edit';
    shapeControls.hidden=!state.capabilities?.model_shape_authoring;
    $('shape-file').value='';const shape=state.model_overrides?.[assetId];
    for(const id of ['shape-upload','shape-clear','shape-file'])$(id).disabled=state.project.mode!=='edit';
    $('shape-clear').disabled=state.project.mode!=='edit'||!shape;$('shape-authored').disabled=!shape;
    $('shape-status').textContent=`Viewing ${shapeLayer==='authored'?'AUTHORED object-local shape':clipId==='authored-channels'?'AUTHORED shared animation':clipId==='authored-appearance'?'AUTHORED appearance animation':clipId?'RETAIL assigned animation':'RETAIL object-local shape'} · ${shape?'A persistent shape override exists.':'No shape override.'}`;
    updateShapeDraft();
    if(!modelRenderer){const module=await import('/scene-renderer.js');modelRenderer=new module.SceneRenderer(modelCanvas,message=>{$('model-error').textContent=message??'';if(!message)requestAnimationFrame(drawModel);});}
    if(!$('model-dialog').open)$('model-dialog').showModal();
    fitModelObject();
  }catch(error){if($('model-dialog').open){$('model-error').textContent=error.message;$('animation-clip').value=model?.animation?.clip_id ?? '';}else notify(error.message,true);}finally{$('animation-clip').disabled=false;setBusy(false);}
}
let shapeDraft=null;
const discardShape=document.createElement('button');discardShape.textContent='Discard selected shape file';discardShape.type='button';$('shape-upload').after(discardShape);
function updateShapeDraft(){
  const pending=!!$('shape-file').files?.length,shape=state.model_overrides?.[modelAssetId];
  discardShape.hidden=!pending;
  $('shape-upload').disabled=!pending||state.project?.mode!=='edit';
  $('shape-retail').disabled=pending;$('shape-authored').disabled=pending||!shape;
  $('shape-clear').disabled=pending||!shape||state.project?.mode!=='edit';$('shape-download-authored').disabled=pending||!shape;
  $('model-export').disabled=pending;
}
$('shape-file').onchange=()=>{const file=$('shape-file').files?.[0];shapeDraft=file?{file,asset:modelAssetId,context:JSON.stringify([state.project.path,state.scene.id])}:null;updateShapeDraft();if(file)$('shape-status').textContent=`Selected ${file.name} · not applied. Apply or discard before changing model views.`;};
discardShape.onclick=()=>{$('shape-file').value='';shapeDraft=null;updateShapeDraft();$('model-error').textContent='';$('shape-status').textContent='Selected file discarded; project unchanged.';};
$('model-dialog').addEventListener('close',()=>{$('shape-file').value='';shapeDraft=null;});
$('shape-retail').onclick=()=>openModel(modelAssetId);
$('shape-authored').onclick=()=>openModel(modelAssetId,null,null,'authored');
$('shape-clear').onclick=async()=>{if(!busy&&!shapeDraft&&await api('/api/command',{type:'clear_model_replacement',asset_id:modelAssetId}))await openModel(modelAssetId);};
$('shape-source').onclick=()=>downloadShapeSource('tmd');
$('shape-source-obj').onclick=()=>downloadShapeSource('obj');
$('shape-download-authored').onclick=()=>downloadShapeSource('obj','authored');
async function downloadShapeSource(format,layer='imported'){
  if(busy||!modelAssetId)return;setBusy(true);
  try{const response=await fetch('/api/model-shape-source',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:modelAssetId,format,layer})}),data=await response.json();if(!response.ok)throw new Error(data.error);const encoded=data[format+'_base64'];if(typeof encoded!=='string'||encoded.length>(format==='obj'?22369624:5592408))throw new Error('Invalid model source size');const bytes=Uint8Array.from(atob(encoded),c=>c.charCodeAt(0));if(bytes.length!==data.byte_length)throw new Error('Model source length mismatch');const url=URL.createObjectURL(new Blob([bytes])),link=document.createElement('a');link.href=url;link.download=(layer==='authored'?'authored':'original')+'-model.'+format;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);$('shape-status').textContent=`Downloaded ${layer} ${format.toUpperCase()} · TMD SHA-256 ${data.effective_sha256}`;}catch(error){$('model-error').textContent=error.message;}finally{setBusy(false);}
};
$('shape-upload').onclick=async()=>{
  if(busy||state.project.mode!=='edit')return;const file=$('shape-file').files?.[0];if(!file||file.size<1||file.size>(/\.obj$/i.test(file.name)?16777216:4194304)){$('model-error').textContent='Choose a TMD up to 4 MiB or an ordered OBJ up to 16 MiB.';return;}
  if(!shapeDraft||shapeDraft.file!==file||shapeDraft.asset!==modelAssetId||shapeDraft.context!==JSON.stringify([state.project.path,state.scene.id])){$('model-error').textContent='The selected shape file belongs to an earlier model context. Discard and select it again.';return;}
  const draft=shapeDraft;
  const asset=modelAssetId,context=JSON.stringify([state.project.path,state.scene.id]);setBusy(true);let encoded;
  try{encoded=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(',')[1]);reader.onerror=()=>reject(new Error('Could not read TMD'));reader.readAsDataURL(file);});}catch(error){$('model-error').textContent=error.message;return;}finally{setBusy(false);}
  if(!encoded||shapeDraft!==draft||asset!==modelAssetId||context!==JSON.stringify([state.project.path,state.scene.id])||!$('model-dialog').open)return;
  const obj=/\.obj$/i.test(file.name);if(await api(obj?'/api/model-obj-replacement':'/api/model-shape-replacement',{asset_id:asset,[obj?'obj_base64':'tmd_base64']:encoded})){$('shape-file').value='';shapeDraft=null;await openModel(asset,null,null,state.model_overrides?.[asset]?'authored':'imported');}
};
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
$('animation-clip').onchange=()=>{const clip=$('animation-clip').value || null;openModel(modelAssetId,clip,['scene-header','authored-appearance','authored-channels'].includes(clip)?modelEntityId:null,'imported',modelSceneEntityId);};
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
const exportClipControls=document.createElement('span');exportClipControls.innerHTML='<label>Export fps <input id="clip-export-rate" type="number" min="1" max="120" step="1" value="10" style="width:4em"></label> <button id="model-export-clip" type="button">Export full clip GLB</button>';$('model-export').after(exportClipControls);
$('model-export').onclick=()=>exportModel(false);
$('model-export-clip').onclick=()=>exportModel(true);
async function exportModel(fullClip=false){
  if(modelSceneContext!==sceneRequestKey()){$('model-error').textContent='The scene or model source changed. Reopen the model preview before exporting.';return;}
  if(shapeDraft){$('model-error').textContent='Apply or discard the selected shape file before exporting.';return;}
  if(busy||!modelAssetId)return;const fps=Number($('clip-export-rate').value);if(fullClip&&(!model?.frames?.length||!Number.isFinite(fps)||fps<1||fps>120)){$('model-error').textContent='Load a clip and choose an export rate from 1 to 120 fps.';return;}stopAnimation();setBusy(true);$('model-export').disabled=true;$('model-error').textContent='';
  const clip=model.animation?.clip_id,payload=modelEntityId?{entity_id:modelEntityId,frame_index:animationFrame,...(clip==='authored-channels'?{representation:'authored'}:{})}:{asset_id:modelAssetId,...(clip?{clip_id:clip,frame_index:animationFrame}:{})};
  if(fullClip){delete payload.frame_index;payload.clip_fps=fps;}
  try{
    const response=await fetch(model.representation==='authored-shape'?'/api/export/model-shape':modelEntityId?(clip==='authored-appearance'?'/api/export/actor-appearance':'/api/export/actor-animation'):'/api/export/model',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    const result=await response.json();if(!response.ok||result.error)throw new Error(result.error ?? 'Model export failed');
    exportDialog.innerHTML=`<div class="dialog-heading"><h2>${result.audit.full_clip?'Animation clip exported':result.audit.posed?'Static posed model exported':'Object-local model exported'}</h2><button id="close-export" aria-label="Close">×</button></div><p>${result.audit.object_count} objects · ${result.audit.triangle_count} triangles · ${result.audit.texture_count} embedded textures${result.audit.posed?' · Frame '+(result.audit.frame_index+1):''}</p><label>Private GLB file<input readonly value="${escapeHTML(result.path)}"></label><p>Full model export${result.audit.posed?' with the displayed animation frame baked into geometry':''}. Source units are retained; physical meter scale is unknown. ${result.audit.full_clip?`Rigid animation channels exported at ${result.audit.export_fps} selected fps; ${result.audit.frame_count} decoded frames. Retail timing is unverified; looping is controlled by the receiving application.`:'Animation channels and skin hierarchy are not exported.'}</p><details><summary>Export provenance and limitations</summary><pre class="diagnostic-detail">${escapeHTML(JSON.stringify(result.audit,null,2))}</pre></details>`;
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
  if(!modelRenderer||!$('model-dialog').open)return;
  const rect=modelCanvas.getBoundingClientRect(),w=rect.width,h=rect.height;if(!w||!h)return;
  const object=modelObject();if(!object)return;
  try{
    const choice=$('model-object').value,vertices=frameVertices();
    if(modelRenderSource!==model||modelRenderObject!==choice){
      const start=object.triangle_start,end=start+object.triangle_count;
      const preview={...model,vertices,triangles:model.triangles.slice(start,end),triangle_colors:model.triangle_colors?.slice(start,end),triangle_uvs:model.triangle_uvs?.slice(start,end),triangle_materials:model.triangle_materials?.slice(start,end)};
      const failures=modelRenderer.load({assets:[{geometry_key:'model-view',preview}],entities:[{entity_id:'model-view',geometry_key:'model-view',renderable:true,model_to_scene:[1,0,0,0,0,-1,0,0,0,0,1,0,0,0,0,1]}]});
      if(failures.length)throw new Error(failures.join('; '));
      modelRenderSource=model;modelRenderObject=choice;modelRenderFrame=animationFrame;
    }else if(modelRenderFrame!==animationFrame){if(modelRenderer.updateVertices('model-view',vertices))modelRenderFrame=animationFrame;}
    const c=Math.cos(modelView.yaw),s=Math.sin(modelView.yaw),cp=Math.cos(modelView.pitch),sp=Math.sin(modelView.pitch);
    modelRenderer.draw({width:w,height:h,positions:new Map(),grid:false,camera:{target:{x:modelView.center[0],y:-modelView.center[1],z:modelView.center[2]},distance:modelView.radius*4/modelView.zoom*.9/1.3},basis:{right:{x:c,y:0,z:s},up:{x:sp*s,y:cp,z:-sp*c},forward:{x:-cp*s,y:sp,z:cp*c}}});
  }catch(error){$('model-error').textContent=String(error.message);}
}
new ResizeObserver(drawModel).observe(modelCanvas);
modelCanvas.addEventListener('pointerdown',event=>{modelCanvas.setPointerCapture(event.pointerId);modelDrag={x:event.clientX,y:event.clientY};});
modelCanvas.addEventListener('pointermove',event=>{if(!modelDrag)return;modelView.yaw+=(event.clientX-modelDrag.x)*.009;modelView.pitch+=(event.clientY-modelDrag.y)*.009;modelDrag={x:event.clientX,y:event.clientY};drawModel();});
for(const event of ['pointerup','pointercancel'])modelCanvas.addEventListener(event,()=>{modelDrag=null;});
modelCanvas.addEventListener('wheel',event=>{event.preventDefault();modelView.zoom=Math.max(.15,Math.min(2.5,modelView.zoom*Math.exp(-event.deltaY*.001)));drawModel();},{passive:false});
api('/api/state');

const worldmapButton=document.createElement('button');worldmapButton.textContent='World-map landmarks';$('resource-refresh').after(worldmapButton);
const worldmapDialog=document.createElement('dialog');worldmapDialog.className='project-dialog';document.body.append(worldmapDialog);
worldmapButton.onclick=async()=>{
  if(busy)return;setBusy(true);const context=JSON.stringify([state.project?.path,state.project?.disc_path]);
  try{
    const response=await fetch('/api/worldmap-menu',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'}),report=await response.json();
    if(!response.ok)throw new Error(report.error);
    if(context!==JSON.stringify([state.project?.path,state.project?.disc_path]))return;
    if(report.schema_version!=='legaia.worldmap-menu.v1'||!Array.isArray(report.placements)||report.placements.length>64||!Array.isArray(report.names)||report.names.length!==16)throw new Error('Invalid world-map menu report');
    worldmapDialog.innerHTML='<h2>World-map landmarks</h2><p>Source menu records. Positions are menu pixels; discovery state and destination reachability are not observed.</p><div class="script-table-wrap"><table><thead><tr><th>Landmark</th><th>Destination source</th><th>Menu X / Y</th><th>Discovery flag index</th></tr></thead><tbody></tbody></table></div><details><summary>Names, source and limits</summary><pre></pre></details><button type="button">Close</button>';
    const table=worldmapDialog.querySelector('tbody');
    for(const row of report.placements){const tr=document.createElement('tr');for(const value of [row.name??`Unresolved name ${row.name_index}`,`${row.destination_scene_id}${row.destination_source_label?' · '+row.destination_source_label:''}`,`${row.menu_position.x} / ${row.menu_position.y}`,row.discovery_flag_index]){const td=document.createElement('td');td.textContent=String(value);tr.append(td);}if(row.destination_source_label){const inspect=document.createElement('button');inspect.type='button';inspect.textContent='Inspect source';inspect.title=`Find ${row.destination_source_label} in the scene catalog; import support is checked separately`;inspect.onclick=()=>{if(busy||context!==JSON.stringify([state.project?.path,state.project?.disc_path]))return;worldmapDialog.close();$('import-button').click();$('catalog-prefix').value=row.destination_source_label;clearSceneCatalog();$('catalog-search').click();};tr.children[1].append(document.createElement('br'),inspect);}table.append(tr);}
    worldmapDialog.querySelector('pre').textContent=JSON.stringify(report,null,2);worldmapDialog.querySelector(':scope > button').onclick=()=>worldmapDialog.close();worldmapDialog.showModal();
  }catch(error){notify(error.message,true);}finally{setBusy(false);}
};
