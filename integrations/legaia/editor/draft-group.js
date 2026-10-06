import {MAX_PREVIEW_ENTITIES} from './scene-limits.js';
import {mixedLayoutPositions} from './scene-placement-group.js';
import {decodeActorPlacementScene} from './actor-placement-batch.js';

export function draftGroupPositions(request,drafts){
  const ids=request.entity_ids,field=Object.hasOwn(request,'remove')?'remove':Object.hasOwn(request,'layout')?'layout':'delta';
  if(!Array.isArray(ids)||ids.length<2||ids.length>128||new Set(ids).size!==ids.length||ids.some(id=>typeof id!=='string'||!drafts[id])||Object.keys(request).sort().join(',')!==['entity_ids',field].sort().join(','))throw new Error('Invalid NPC draft group request.');
  if(field==='remove'){if(request.remove!==true)throw new Error('NPC removal requires remove=true.');return new Map(ids.map(id=>[id,null]));}
  const result=new Map(ids.map(id=>[id,{...drafts[id].position}]));
  if(field==='delta'){
    if(Object.keys(request.delta??{}).sort().join(',')!=='x,z'||Object.values(request.delta).some(n=>!Number.isSafeInteger(n)||n%64||Math.abs(n)>16320))throw new Error('Invalid NPC draft group offset.');
    for(const value of result.values())for(const axis of ['x','z'])value[axis]+=request.delta[axis];
  }else{
    const layout=request.layout,align=layout?.kind==='align',axis=layout?.axis;
    if(['rotate','scale','mirror'].includes(layout?.kind)){
      const positions=mixedLayoutPositions(ids.map(entity_id=>({entity_id,current:drafts[entity_id].position})),layout);
      for(const row of positions)result.set(row.entity_id,row.position);
    }else{
      if(!['align','distribute'].includes(layout?.kind)||!['x','z'].includes(axis)||Object.keys(layout).sort().join(',')!==(align?'anchor_entity_id,axis,kind':'axis,kind')||(align&&!ids.includes(layout.anchor_entity_id)))throw new Error('Invalid NPC draft group layout.');
      if(align){for(const value of result.values())value[axis]=drafts[layout.anchor_entity_id].position[axis];}
      else{
        const ordered=[...ids].sort((a,b)=>drafts[a].position[axis]-drafts[b].position[axis]||(a<b?-1:a>b?1:0)),low=drafts[ordered[0]].position[axis]/64,high=drafts[ordered.at(-1)].position[axis]/64,span=high-low,intervals=ordered.length-1;
        if(!Number.isInteger(low)||!Number.isInteger(high)||span<intervals)throw new Error('NPC distribution requires one64-unit interval per gap.');
        for(const [i,id] of ordered.entries())result.get(id)[axis]=(low+Math.floor((2*span*i+intervals)/(2*intervals)))*64;
      }
    }
  }
  for(const value of result.values())if(Object.keys(value).sort().join(',')!=='x,z'||Object.values(value).some(n=>!Number.isSafeInteger(n)||n%64||n<64||n>16384))throw new Error('NPC draft group position exceeds retail bounds.');
  return result;
}

export function decodeDraftGroupReview(value,request,state){
  const ids=request.entity_ids,drafts=state.actor_drafts??{},positions=draftGroupPositions(request,drafts),field=request.remove?'remove':request.layout?'layout':'delta';
  const operation=v=>Object.fromEntries(Object.entries(v??{}).sort(([a],[b])=>a<b?-1:a>b?1:0));
  if(value?.schema_version!=='legaia.draft-group-review.v1'||value.scene_id!==state.scene?.id||value.scene_preview_source_key!==state.scene_preview_source_key||
     typeof value.project_source_key!=='string'||!/^[a-f0-9]{64}$/.test(value.project_source_key)||typeof value.review_key!=='string'||!/^[a-f0-9]{64}$/.test(value.review_key)||
     Object.keys(value.request??{}).sort().join(',')!==['entity_ids',field].sort().join(',')||JSON.stringify(value.request.entity_ids)!==JSON.stringify(ids)||(field==='remove'?value.request.remove!==true:JSON.stringify(operation(value.request[field]))!==JSON.stringify(operation(request[field])))||!Array.isArray(value.targets)||value.targets.length!==ids.length||
     value.gameplay_verified!==false||value.changed_count!==(request.remove?ids.length:ids.filter(id=>['x','z'].some(axis=>positions.get(id)[axis]!==drafts[id].position[axis])).length)||
     !Array.isArray(value.limitations)||value.limitations.length>32||value.limitations.some(s=>typeof s!=='string'||!s||s.length>2048))throw new Error('NPC draft group report differs from its source/request.');
  for(const [index,row] of value.targets.entries()){
    const draft=drafts[ids[index]];
    if(row.entity_id!==ids[index]||draft.scene_id!==state.scene.id||JSON.stringify(row.draft)!==JSON.stringify(draft)||(request.remove?row.proposed!==null:Object.keys(row.proposed??{}).sort().join(',')!=='x,z'||['x','z'].some(axis=>row.proposed[axis]!==positions.get(ids[index])[axis])))throw new Error('NPC draft group target differs from authored placement.');
  }
  return structuredClone(value);
}

export function decodeDraftGroupScene(response,report,base){
  const scene=response?.scene;
  if(response?.schema_version!=='legaia.draft-group-scene.v1'||response.project_source_key!==report.project_source_key||response.review_key!==report.review_key||
     response.scene_preview_source_key!==base.source_key||response.scene_id!==base.scene_id||scene?.scene_id!==base.scene_id||scene.schema!=='legaia.scene-preview.v1'||scene.representation!=='authored'||
     !Array.isArray(scene.entities)||scene.entities.length!==base.entities.length-(report.request.remove?report.targets.length:0)||scene.entities.length>MAX_PREVIEW_ENTITIES||JSON.stringify(scene.assets)!==JSON.stringify(base.assets)||JSON.stringify(scene.position_to_display)!==JSON.stringify(base.position_to_display))throw new Error('NPC draft group scene differs from its source/review.');
  const rows=new Map(scene.entities.map(row=>[row.entity_id,row])),targets=new Map(report.targets.map(row=>[row.entity_id,row]));
  if(rows.size!==scene.entities.length)throw new Error('NPC draft group scene identities are ambiguous.');
  const positions=[];
  for(const original of base.entities){
    const row=rows.get(original.entity_id),target=targets.get(original.entity_id);
    if(!target){if(JSON.stringify(row)!==JSON.stringify(original))throw new Error('NPC draft group scene changed unselected content.');continue;}
    if(report.request.remove){if(original.kind!=='actor_draft'||row)throw new Error('NPC removal scene retains a removed draft or targets imported content.');continue;}
    if(original.kind!=='actor_draft'||!row||row.kind!=='actor_draft'||JSON.stringify(row.authored_position)!==JSON.stringify(target.proposed))throw new Error('NPC draft group authored binding differs from review.');
    const unchanged=value=>Object.fromEntries(Object.entries(value).filter(([key])=>!['position','preview_position','preview_ground_sample','display_position','preview_height_status','model_to_scene','authored_position'].includes(key)));
    if(JSON.stringify(unchanged(row))!==JSON.stringify(unchanged(original)))throw new Error('NPC draft group changed donor metadata or appearance.');
    const matrix=[...original.model_to_scene];matrix[3]=row.display_position?.x;matrix[7]=row.display_position?.y;matrix[11]=row.display_position?.z;
    if(JSON.stringify(matrix)!==JSON.stringify(row.model_to_scene))throw new Error('NPC draft group model transform differs from placement.');
    positions.push(row);
  }
  if(!report.request.remove)decodeActorPlacementScene({schema_version:'legaia.actor-placement-scene.v1',scene_id:response.scene_id,project_source_key:base.source_key,review_key:response.review_key,positions},
    {scene_id:report.scene_id,review_key:report.review_key,targets:report.targets.map(row=>({entity_id:row.entity_id,proposed:{...row.proposed,y:null}}))},base.source_key);
  return structuredClone(scene);
}

export function draftGroupSelection(entityId,entityIds,state){
  if(typeof state?.scene?.id!=='string'||!state.scene.id)throw new Error('NPC group selection requires an active scene.');
  const selection=entityIds??[],drafts=state.actor_drafts??{};
  if(!Array.isArray(selection)||selection.length>128||new Set(selection).size!==selection.length||selection.some(id=>typeof id!=='string'))throw new Error('NPC group selection must contain at most 128 distinct scene placements.');
  const ids=selection.filter(id=>id.startsWith('authored-actor://'));
  for(const id of ids)if(drafts[id]?.scene_id!==state.scene?.id)throw new Error('Selected NPC draft is unavailable in the active scene.');
  if(ids.length)return {entity_ids:ids.slice().sort(),ignored_count:selection.length-ids.length,from_selection:true};
  if(drafts[entityId]?.scene_id!==state.scene?.id)throw new Error('Focused NPC draft is unavailable in the active scene.');
  return {entity_ids:[entityId],ignored_count:0,from_selection:false};
}

export function openDraftGroup({entityId,entityIds=null,onError=()=>{},getState,isBusy,canEdit,setBusy,api,canInspectScene,getScenePreview,inspectScene}){
  if(isBusy()||!canEdit())return;
  const state=getState(),drafts=Object.entries(state.actor_drafts??{}).filter(([,d])=>d.scene_id===state.scene?.id).sort(([a],[b])=>a.localeCompare(b));
  if(drafts.length<2)return;
  let seed;try{seed=draftGroupSelection(entityId,entityIds,state);}catch(error){onError(error);return;}
  const dialog=document.createElement('dialog');dialog.id='draft-group-dialog';document.body.append(dialog);
  dialog.innerHTML='<h2>Edit NPC draft group</h2><p>Select authored NPC drafts in this scene. Offset, align, distribute, rotate positions, scale spacing or reflect a coordinate about a selected anchor along X/Z on the retail 64-unit grid, from 64 through 16384. Spacing scale accepts 1-1000 percent and rounds final coordinates to the nearest 64 units, with half steps away from zero; rounded placements may coincide. Rotation and reflection change positions while model geometry and facing stay fixed. Removal deletes only reviewed project drafts and preserves unselected content and retail donors. Undo restores identities and metadata. Placement keeps donor binding, names and scripts unchanged. Source elevation is preview only; runtime spawning and gameplay remain unverified.</p><form><label>Placement operation<select name="operation" aria-label="NPC group placement operation"><option value="remove">Remove selected NPC drafts</option><option value="offset" selected>Offset X/Z together</option><option value="align_x">Align X to anchor</option><option value="align_z">Align Z to anchor</option><option value="distribute_x">Distribute along X</option><option value="distribute_z">Distribute along Z</option><option value="rotate_1">Rotate positions +90 degrees</option><option value="rotate_-1">Rotate positions -90 degrees</option><option value="rotate_2">Rotate positions 180 degrees</option><option value="scale">Scale spacing</option><option value="mirror_x">Reflect X about anchor</option><option value="mirror_z">Reflect Z about anchor</option></select></label><label hidden>Layout anchor<select name="anchor" aria-label="NPC group alignment anchor"></select></label><label hidden>Spacing percent<input name="percent" type="number" min="1" max="1000" step="1" value="100" aria-label="NPC group spacing percent"></label><label>Find drafts<input name="search" type="search" aria-label="Find NPC group drafts"></label><div class="dialog-actions"><button type="button" data-select>Select visible drafts</button><button type="button" data-clear>Clear selection</button></div><div class="batch-actors" data-drafts></div><p data-count role="status"></p><label>X offset<input name="x" type="number" step="64" min="-16320" max="16320" value="64" required aria-label="NPC group X offset"></label><label>Z offset<input name="z" type="number" step="64" min="-16320" max="16320" value="0" required aria-label="NPC group Z offset"></label><div class="dialog-actions"><button type="submit" data-preview>Preview group movement</button><button type="button" data-inspect disabled>Inspect group in scene</button><button type="button" data-apply disabled>Apply group movement</button></div></form><p data-error class="dialog-error" role="alert"></p><div data-result></div><button type="button" data-close>Close NPC draft group</button>';
  for(const actions of dialog.querySelectorAll('.dialog-actions')){actions.style.flexWrap='wrap';actions.style.justifyContent='flex-start';}
  const seedNote=document.createElement('p');seedNote.className='field-note';seedNote.dataset.selectionSeed='';seedNote.textContent=seed.from_selection?`Using ${seed.entity_ids.length} NPC drafts from the current selection.${seed.ignored_count?` ${seed.ignored_count} other placement${seed.ignored_count===1?' is':'s are'} excluded from this NPC tool; use mixed scene placements to edit the whole selection.`:''}`:'Select NPC drafts to include in this group.';dialog.querySelector('form').before(seedNote);
  let selected=new Set(seed.entity_ids),report=null,generation=0,controller=null,keepClose=false;
  const key=()=>{const s=getState();return JSON.stringify([s.project.path,s.scene.id,s.scene_preview_source_key,s.actor_drafts]);},context=key(),current=()=>context===key()&&canEdit();
  const request=()=>{
    const entity_ids=[...selected].sort(),mode=dialog.querySelector('[name=operation]').value;
    if(mode==='remove')return {entity_ids,remove:true};
    if(mode==='offset')return {entity_ids,delta:{x:Number(dialog.querySelector('[name=x]').value),z:Number(dialog.querySelector('[name=z]').value)}};
    if(mode==='scale')return {entity_ids,layout:{kind:'scale',anchor_entity_id:dialog.querySelector('[name=anchor]').value,percent:Number(dialog.querySelector('[name=percent]').value)}};
    if(mode.startsWith('rotate_'))return {entity_ids,layout:{kind:'rotate',anchor_entity_id:dialog.querySelector('[name=anchor]').value,quarter_turns:Number(mode.split('_')[1])}};
    const [kind,axis]=mode.split('_');return {entity_ids,layout:{kind,axis,...(['align','mirror'].includes(kind)?{anchor_entity_id:dialog.querySelector('[name=anchor]').value}:{})}};
  };
  const visible=()=>drafts.filter(([id,d])=>(d.name+' '+id).toLowerCase().includes(dialog.querySelector('[name=search]').value.toLowerCase()));
  function update(){
    if(!dialog.open)return;const disabled=isBusy()||!current();for(const control of dialog.querySelectorAll('input,select,button'))if(!control.matches('[data-close]'))control.disabled=disabled;
    const mode=dialog.querySelector('[name=operation]').value,anchor=dialog.querySelector('[name=anchor]'),prior=anchor.value;anchor.replaceChildren();
    for(const [id,draft] of drafts)if(selected.has(id)){const option=document.createElement('option');option.value=id;option.textContent=draft.name;anchor.append(option);}if(selected.has(prior))anchor.value=prior;
    const anchored=mode.startsWith('align_')||mode.startsWith('rotate_')||mode.startsWith('mirror_')||mode==='scale';anchor.parentElement.hidden=!anchored;anchor.disabled=disabled||!anchored;
    const percent=dialog.querySelector('[name=percent]');percent.parentElement.hidden=mode!=='scale';percent.disabled=disabled||mode!=='scale';
    for(const input of dialog.querySelectorAll('[name=x],[name=z]')){input.parentElement.hidden=mode!=='offset';input.disabled=disabled||mode!=='offset';}
    dialog.querySelector('[data-preview]').textContent=mode==='remove'?'Review group removal':mode==='offset'?'Preview group movement':'Preview group layout';dialog.querySelector('[data-apply]').textContent=mode==='remove'?'Remove reviewed drafts':mode==='offset'?'Apply group movement':'Apply group layout';
    dialog.querySelector('[data-count]').textContent=`${selected.size} drafts selected · one Undo step`;
    dialog.querySelector('[data-preview]').disabled=disabled||selected.size<2||!dialog.querySelector('form').checkValidity();
    dialog.querySelector('[data-apply]').disabled=disabled||!report?.changed_count;
    dialog.querySelector('[data-inspect]').disabled=disabled||!report||!canInspectScene();
  }
  function invalidate(){generation++;report=null;dialog.querySelector('[data-result]').replaceChildren();dialog.querySelector('[data-error]').textContent='';update();}
  function render(){
    const list=dialog.querySelector('[data-drafts]');list.replaceChildren();for(const [id,draft] of visible()){
      const label=document.createElement('label'),input=document.createElement('input'),name=document.createElement('span');input.type='checkbox';input.value=id;input.checked=selected.has(id);input.setAttribute('aria-label','Include '+draft.name);name.textContent=draft.name;label.title=id;label.append(input,name);list.append(label);
      input.onchange=()=>{if(!dialog.contains(input)||!dialog.open||isBusy()||!current())return;if(input.checked)selected.add(id);else selected.delete(id);invalidate();};
    }update();
  }
  dialog.querySelector('[name=search]').oninput=render;
  dialog.querySelector('[data-select]').onclick=()=>{if(isBusy()||!current())return;for(const [id] of visible())selected.add(id);invalidate();render();};
  dialog.querySelector('[data-clear]').onclick=()=>{if(isBusy()||!current())return;selected.clear();invalidate();render();};
  for(const input of dialog.querySelectorAll('[name=x],[name=z],[name=operation],[name=anchor],[name=percent]'))input.oninput=invalidate;
  dialog.querySelector('[data-close]').onclick=()=>dialog.close();dialog.addEventListener('close',()=>{if(keepClose){keepClose=false;return;}generation++;controller?.abort();report=null;dialog.remove();});
  async function post(route,body,signal){const r=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal}),v=await r.json();if(!r.ok||v.error)throw new Error(v.error||'NPC draft group request failed.');return v;}
  dialog.querySelector('form').onsubmit=async event=>{
    event.preventDefault();if(dialog.querySelector('[data-preview]').disabled)return;const body=request(),token=++generation,active=new AbortController();controller=active;report=null;setBusy(true);dialog.querySelector('[data-result]').replaceChildren();dialog.querySelector('[data-error]').textContent='';update();
    try{const value=await post('/api/draft-group',body,active.signal);if(!dialog.open||token!==generation||!current()||JSON.stringify(body)!==JSON.stringify(request()))return;
      report=decodeDraftGroupReview(value,body,getState());const table=document.createElement('table');table.style.width='100%';table.innerHTML='<tr><th>Draft</th><th>Current X/Z</th><th>Proposed X/Z</th></tr>';
      for(const row of report.targets){const tr=document.createElement('tr');for(const value of [row.draft.name,`${row.draft.position.x} / ${row.draft.position.z}`,row.proposed===null?'Remove authored draft':`${row.proposed.x} / ${row.proposed.z}`]){const td=document.createElement('td');td.textContent=value;tr.append(td);}table.append(tr);}for(const cell of table.querySelectorAll('th,td')){cell.style.padding='0.35rem';cell.style.textAlign='left';cell.style.overflowWrap='anywhere';}dialog.querySelector('[data-result]').append(table);
      for(const line of report.limitations){const p=document.createElement('p');p.className='field-note';p.textContent=line;dialog.querySelector('[data-result]').append(p);}
    }catch(error){if(error.name!=='AbortError'&&dialog.open&&token===generation)dialog.querySelector('[data-error]').textContent=error.message;}
    finally{if(controller===active){controller=null;setBusy(false);}update();}
  };
  dialog.querySelector('[data-inspect]').onclick=async()=>{
    if(isBusy()||!current()||!report||!canInspectScene())return;const accepted=report,base=getScenePreview(),token=++generation,active=new AbortController();controller=active;setBusy(true);update();
    try{const value=await post('/api/draft-group-scene',{...accepted.request,review_key:accepted.review_key},active.signal);if(!dialog.open||token!==generation||!current()||!canInspectScene()||getScenePreview()!==base)return;
      const scene=decodeDraftGroupScene(value,accepted,base),back=()=>{if(token!==generation||!current()||report!==accepted)return false;dialog.showModal();update();return true;};inspectScene(scene,accepted,back,current);keepClose=true;dialog.close();
    }catch(error){if(error.name!=='AbortError'&&dialog.open&&token===generation)dialog.querySelector('[data-error]').textContent=error.message;}
    finally{if(controller===active){controller=null;setBusy(false);}update();}
  };
  dialog.querySelector('[data-apply]').onclick=async()=>{
    if(isBusy()||!current()||!report?.changed_count)return;const accepted=report;report=null;update();if(await api('/api/command',{type:accepted.request.remove?'delete_actor_drafts':accepted.request.layout?'layout_actor_drafts':'offset_actor_drafts',...accepted.request,review_key:accepted.review_key},{success:`${accepted.request.remove?'Removed':'Updated'} ${accepted.changed_count} NPC drafts. Undo restores the group.`}))dialog.close();else if(dialog.open)dialog.querySelector('[data-error]').textContent='Group rejected. Review current drafts again.';update();
  };
  dialog.showModal();render();
}
