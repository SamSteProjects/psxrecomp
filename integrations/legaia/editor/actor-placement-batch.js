import {rotatePlacementPosition} from './placement-angle.js';
/** Group placement authoring belongs to the project command service. */
export function decodeActorPlacementScene(result,proposal,sourceKey){
  if(result?.schema_version!=='legaia.actor-placement-scene.v1'||result.scene_id!==proposal.scene_id||result.project_source_key!==sourceKey||result.review_key!==proposal.review_key||
    !Array.isArray(result.positions)||result.positions.length!==proposal.targets.length||result.positions.length>128)throw new Error('Invalid or stale actor group scene inspection');
  const expected=new Map(proposal.targets.map(row=>[row.entity_id,row.proposed])),positions=new Map();
  for(const row of result.positions){
    const source=expected.get(row.entity_id),display=row.display_position,preview=row.preview_position;
    if(!source||positions.has(row.entity_id)||['x','y','z'].some(axis=>row.position?.[axis]!==source[axis])||
      !display||['x','y','z'].some(axis=>!Number.isFinite(display[axis]))||
      preview?.x!==source.x||preview?.z!==source.z||display.x!==source.x||display.z!==source.z||
      !['explicit','source_surface','unresolved_no_source_surface'].includes(row.preview_height_status)||
      (row.preview_height_status==='explicit'&&(source.y===null||preview.y!==source.y))||
      (row.preview_height_status==='source_surface'&&(source.y!==null||!Number.isFinite(preview.y)))||
      (row.preview_height_status==='unresolved_no_source_surface'&&(source.y!==null||preview.y!==null))||
      (preview.y!==null&&!Number.isFinite(preview.y))||display.y!==-(preview.y??0))throw new Error('Actor group scene positions differ from the reviewed proposal');
    positions.set(row.entity_id,{x:display.x,y:display.y,z:display.z});
  }
  return positions;
}

export function mergeActorGroupSelection(ids,members,eligible,add=false){
  const allowed=new Set(eligible);
  if(members.some(id=>!allowed.has(id)))throw new Error('Group selection supports imported actors in the active scene');
  const next=new Set(add?ids.filter(id=>allowed.has(id)):[]);for(const id of members)next.add(id);
  if(next.size>128)throw new Error('Actor group selection is limited to 128 actors');
  return [...next].sort();
}
export function actorGroupRange(anchor,target,visible){
  const end=visible.indexOf(target);if(end<0)throw new Error('Range target is outside the visible actor list');
  const start=Math.max(0,visible.indexOf(anchor));
  return visible.indexOf(anchor)<0?[target]:visible.slice(Math.min(start,end),Math.max(start,end)+1);
}

export function toggleActorGroupSelection(ids,id,eligible,primary=null){
  const allowed=new Set(eligible),next=new Set(ids.filter(value=>allowed.has(value)));
  if(!allowed.has(id))throw new Error('Group selection supports imported actors in the active scene');
  if(!next.size&&allowed.has(primary))next.add(primary);
  if(next.has(id))next.delete(id);else next.add(id);
  if(next.size>128)throw new Error('Actor group selection is limited to 128 actors');
  return [...next].sort();
}

export function offsetActorPlacementProposal(proposal,axis,amount){
  if(!['x','z'].includes(axis)||!Number.isInteger(amount)||amount%64||!Array.isArray(proposal?.targets)||proposal.targets.length<2||proposal.targets.length>128)throw new Error('Group drag requires a 64-unit X/Z offset');
  const delta={...proposal.delta,[axis]:(proposal.delta?.[axis]??0)+amount};
  if(!Number.isInteger(delta[axis])||Math.abs(delta[axis])>16320||proposal.targets.some(row=>!Number.isFinite(row.proposed?.[axis])||row.proposed[axis]+amount<64||row.proposed[axis]+amount>16384||(row.proposed[axis]+amount)%64))throw new Error('Group drag exceeds a reviewed actor placement boundary');
  return {actor_ids:proposal.targets.map(row=>row.entity_id).sort(),delta};
}

export function actorGridSnapLayout(axes,spacing){
  if(![['x'],['z'],['x','z']].some(value=>JSON.stringify(value)===JSON.stringify(axes))||!Number.isSafeInteger(spacing)||spacing<64||spacing>4096||spacing%64)throw Error('Actor snap requires X, Z or X/Z and grid spacing in multiples of 64 from 64 through 4096');
  return {kind:'snap',axes:[...axes],spacing};
}
export function validateActorGridSnapReport(report){
  const layout=actorGridSnapLayout(report?.layout?.axes,report?.layout?.spacing);
  if(JSON.stringify(report.layout)!==JSON.stringify(layout)||!Array.isArray(report.targets)||report.targets.length<2||report.targets.length>128)throw Error('Invalid actor grid snap report');
  let changed=0;
  for(const row of report.targets){let different=false;for(const axis of ['x','z']){const n=row.effective?.[axis];if(!Number.isSafeInteger(n)||n<64||n>16384||n%64)throw Error('Invalid Current actor coordinate');const value=layout.axes.includes(axis)?Math.floor((n+layout.spacing/2)/layout.spacing)*layout.spacing:n;if(value<64||value>16384||row.proposed?.[axis]!==value)throw Error('Actor grid snap proposal differs from native arithmetic');different||=value!==n;}if(row.proposed.y!==row.effective.y)throw Error('Actor grid snap changed source height');changed+=different;}
  if(report.changed_count!==changed)throw Error('Actor grid snap change count differs from proposal');return report;
}
export function validateActorRotationReport(report){
  const layout=report?.layout;
  if(!layout||Object.keys(layout).sort().join()!=='anchor_entity_id,angle_degrees,kind'||layout.kind!=='rotate_angle'||!Array.isArray(report.targets)||report.targets.length<2||report.targets.length>128)throw Error('Invalid actor position rotation report');
  const anchor=report.targets.find(row=>row.entity_id===layout.anchor_entity_id);if(!anchor)throw Error('Rotation anchor must belong to the reviewed group');let changed=0;
  for(const row of report.targets){if(['x','z'].some(a=>!Number.isSafeInteger(row.effective?.[a])||row.effective[a]<64||row.effective[a]>16384||row.effective[a]%64))throw Error('Invalid Current actor coordinate');const point=rotatePlacementPosition(row.effective,anchor.effective,64,layout.angle_degrees);for(const axis of ['x','z'])if(point[axis]<64||point[axis]>16384||row.proposed?.[axis]!==point[axis])throw Error('Actor rotation differs from native arithmetic');if(row.proposed.y!==row.effective.y)throw Error('Actor rotation changed authored height');changed+=point.x!==row.effective.x||point.z!==row.effective.z;}
  if(report.changed_count!==changed)throw Error('Actor rotation change count differs from proposal');return report;
}

export function mountActorPlacementBatch({getState,getEntities,isBusy,canEdit,setBusy,api,after,canInspectScene,onSceneInspection,frameGroup,notify,getSelection=()=>[]}){
  const button=document.createElement('button');button.id='actor-batch-button';button.textContent='Actor group placements';after.after(button);
  const dialog=document.createElement('dialog');dialog.id='actor-batch-dialog';document.body.append(dialog);
  const bar=document.createElement('div');bar.id='actor-batch-scene-bar';bar.hidden=true;
  bar.innerHTML='<span>Actor group proposal · not applied</span><label>Group layer<select aria-label="Actor group inspection layer"><option value="proposed">Proposed · not applied</option><option value="current">Current authored scene</option></select></label><button type="button" data-frame-group>Frame group</button><button type="button" data-return-group>Return to group</button><button type="button" data-restore-group>Restore scene</button>';
  document.getElementById('frame-selected').after(bar);
  let selected=new Set(),preview=null,context=null,generation=0,controller=null,inspection=null,keepClose=false;
  const contextKey=()=>{const s=getState();return JSON.stringify([s.project?.path,s.scene?.id,s.scene_preview_source_key]);};
  const payload=()=>{
    const actor_ids=[...selected].sort(),mode=dialog.querySelector('[name="layout-mode"]').value;
    if(mode==='offset')return {actor_ids,delta:{x:Number(dialog.querySelector('[name="x"]').value),z:Number(dialog.querySelector('[name="z"]').value)}};
    if(mode.startsWith('snap_'))return {actor_ids,layout:{kind:'snap',axes:mode==='snap_xz'?['x','z']:[mode.split('_')[1]],spacing:Number(dialog.querySelector('[name="layout-spacing"]').value)}};
    if(mode==='rotate_angle')return {actor_ids,layout:{kind:'rotate_angle',anchor_entity_id:dialog.querySelector('[name="layout-anchor"]').value,angle_degrees:Number(dialog.querySelector('[name="layout-angle"]').value)}};
    const [kind,axis]=mode.split('_'),layout={kind,axis};if(kind==='align')layout.anchor_entity_id=dialog.querySelector('[name="layout-anchor"]').value;
    return {actor_ids,layout};
  };
  const clearInspection=()=>{inspection=null;bar.hidden=true;onSceneInspection(null);};
  const invalidate=()=>{generation++;preview=null;clearInspection();dialog.querySelector('.batch-result')?.replaceChildren();update();};
  function update(){
    if(!dialog.open)return;
    const busy=isBusy(),request=payload(),layout=!!request.layout;let snapValid=true;if(request.layout?.kind==='snap'){try{actorGridSnapLayout(request.layout.axes,request.layout.spacing);}catch{snapValid=false;}}const angleValid=request.layout?.kind!=='rotate_angle'||dialog.querySelector('[name="layout-angle"]').value.trim()&&Number.isSafeInteger(request.layout.angle_degrees)&&Math.abs(request.layout.angle_degrees)<=359;const valid=snapValid&&angleValid&&(layout||dialog.querySelector('form').checkValidity())&&selected.size>=2&&selected.size<=128&&(!['align','rotate_angle'].includes(request.layout?.kind)||selected.has(request.layout.anchor_entity_id));
    dialog.querySelectorAll('input,button,select').forEach(item=>{if(!item.matches('[data-close-batch]'))item.disabled=busy||!canEdit();});
    dialog.querySelector('[data-preview-batch]').disabled=busy||!canEdit()||!valid;
    for(const input of dialog.querySelectorAll('[name="x"],[name="z"]')){input.parentElement.hidden=layout;input.disabled=busy||!canEdit()||layout;}
    const anchor=dialog.querySelector('[name="layout-anchor"]'),anchored=['align','rotate_angle'].includes(request.layout?.kind);anchor.parentElement.hidden=!anchored;anchor.disabled=busy||!canEdit()||!anchored;
    const angle=dialog.querySelector('[name="layout-angle"]');angle.parentElement.hidden=request.layout?.kind!=='rotate_angle';angle.disabled=busy||!canEdit()||request.layout?.kind!=='rotate_angle';
    const spacing=dialog.querySelector('[name="layout-spacing"]');spacing.parentElement.hidden=request.layout?.kind!=='snap';spacing.disabled=busy||!canEdit()||request.layout?.kind!=='snap';
    dialog.querySelector('[data-preview-batch]').textContent=layout?'Preview group layout':'Preview group offset';dialog.querySelector('[data-apply-batch]').textContent=layout?'Apply group layout':'Apply group offset';
    const delta=request.delta??{};
    dialog.querySelector('[data-apply-batch]').disabled=busy||!canEdit()||!valid||!preview||(layout?!preview?.changed_count:(!delta.x&&!delta.z));
    dialog.querySelector('[data-inspect-batch]').disabled=busy||!canEdit()||!preview||!canInspectScene();
    dialog.querySelector('.batch-count').textContent=`${selected.size} actors selected · one Undo step`;
  }
  function renderPreviewTable(report){
    dialog.querySelector('.batch-result').replaceChildren();
    const note=document.createElement('p');note.textContent=report.layout?`${report.changed_count} actors change. ${report.limitations.join(' ')}`:'Proposed group offset; source height, facing and scripts remain unchanged.';dialog.querySelector('.batch-result').append(note);
    const table=document.createElement('table'),head=document.createElement('tr');
    for(const text of ['Actor','Retail X/Z','Authored X/Z','Effective X/Z','Proposed X/Z']){const th=document.createElement('th');th.textContent=text;head.append(th);}table.append(head);
    for(const row of report.targets){const tr=document.createElement('tr');for(const value of [getEntities().find(e=>e.id===row.entity_id)?.name??row.entity_id,...['retail','authored','effective','proposed'].map(layer=>`${row[layer]?.x??'inherit'} / ${row[layer]?.z??'inherit'}`)]){const td=document.createElement('td');td.textContent=value;tr.append(td);}table.append(tr);}
    dialog.querySelector('.batch-result').append(table);
  }
  function renderActors(){
    const query=dialog.querySelector('[name="search"]').value.toLowerCase(),list=dialog.querySelector('.batch-actors');list.replaceChildren();
    for(const entity of getEntities().filter(e=>`${e.name} ${e.id}`.toLowerCase().includes(query))){
      const label=document.createElement('label'),check=document.createElement('input'),name=document.createElement('span');
      check.type='checkbox';check.value=entity.id;check.checked=selected.has(entity.id);check.setAttribute('aria-label',`Include ${entity.name??entity.id}`);
      check.onchange=()=>{if(check.checked)selected.add(entity.id);else selected.delete(entity.id);invalidate();};
      name.textContent=entity.name??entity.id;label.title=entity.id;label.append(check,name);list.append(label);
    }
    const anchor=dialog.querySelector('[name="layout-anchor"]'),prior=anchor.value;anchor.replaceChildren();
    for(const id of [...selected].sort()){const item=document.createElement('option');item.value=id;item.textContent=getEntities().find(e=>e.id===id)?.name??id;anchor.append(item);}
    const preferred=selected.has(prior)?prior:getState().selection?.entity_id;if(selected.has(preferred))anchor.value=preferred;
    update();
  }
  button.onclick=()=>{
    if(isBusy()||!canEdit())return;
    clearInspection();selected=new Set(getSelection().filter(id=>getEntities().some(entity=>entity.id===id)));preview=null;context=contextKey();generation++;
    dialog.innerHTML='<div class="dialog-heading"><h2>Actor group placements</h2><button type="button" data-close-batch aria-label="Close actor group">×</button></div><p>Select imported actors in this scene. Offset, align, distribute or snap their effective X/Z placements. Grid snap uses scene-origin spacing in multiples of 64 from 64 through 4096, with halfway positions rounded upward; invalid native results reject the entire group. Proposed coordinates must fit the exact retail 64-unit grid, from 64 through 16384. Position rotation uses whole degrees from -359 through 359 about the selected actor and rounds final X/Z to native precision. Source height, facing, scripts and scheduling stay unchanged.</p><form><label>Find actors<input name="search" type="search" aria-label="Find group actors"></label><div class="batch-actors"></div><p class="batch-count" role="status"></p><div class="dialog-actions"><label>X offset<input name="x" type="number" step="64" min="-16320" max="16320" value="0" required></label><label>Z offset<input name="z" type="number" step="64" min="-16320" max="16320" value="0" required></label></div><div class="dialog-actions"><button type="submit" data-preview-batch>Preview group offset</button><button type="button" data-apply-batch disabled>Apply group offset</button></div><p class="dialog-error" role="alert"></p><div class="batch-result"></div></form>';
    const layoutControls=document.createElement('div');layoutControls.className='dialog-actions';layoutControls.innerHTML='<label>Placement operation<select name="layout-mode" aria-label="Group placement operation"><option value="offset">Offset X/Z together</option><option value="align_x">Align X to anchor</option><option value="align_z">Align Z to anchor</option><option value="distribute_x">Distribute along X</option><option value="distribute_z">Distribute along Z</option><option value="snap_x">Snap X to grid</option><option value="snap_z">Snap Z to grid</option><option value="snap_xz">Snap X/Z to grid</option><option value="rotate_angle">Rotate X/Z positions around anchor</option></select></label><label hidden>Grid spacing<input name="layout-spacing" type="number" min="64" max="4096" step="64" value="256" aria-label="Actor group grid spacing"></label><label hidden>Angle degrees<input name="layout-angle" type="number" min="-359" max="359" step="1" value="45" aria-label="Actor group angle degrees"></label><label hidden>Layout anchor<select name="layout-anchor" aria-label="Group alignment anchor"></select></label>';dialog.querySelector('form').prepend(layoutControls);
    for(const control of layoutControls.querySelectorAll('select'))control.onchange=invalidate;layoutControls.querySelector('[name="layout-spacing"]').oninput=invalidate;layoutControls.querySelector('[name="layout-angle"]').oninput=invalidate;
    dialog.querySelector('[data-close-batch]').onclick=()=>dialog.close();
    dialog.querySelector('[name="search"]').oninput=renderActors;
    for(const input of dialog.querySelectorAll('[name="x"],[name="z"]'))input.oninput=invalidate;
    dialog.querySelector('form').onsubmit=async event=>{
      event.preventDefault();if(dialog.querySelector('[data-preview-batch]').disabled)return;
      const request=payload(),binding=JSON.stringify(request),token=++generation,requestContext=context;
      controller=new AbortController();const active=controller;preview=null;setBusy(true);dialog.querySelector('.dialog-error').textContent='';dialog.querySelector('.batch-result').replaceChildren();
      try{
        const response=await fetch(request.layout?'/api/actor-placement-layout':'/api/actor-placement-batch',{method:'POST',headers:{'Content-Type':'application/json'},body:binding,signal:active.signal});
        const report=await response.json();if(!response.ok||report.error)throw new Error(report.error||'Group placement preview failed');
        if(!dialog.open||token!==generation||requestContext!==contextKey()||binding!==JSON.stringify(payload()))return;
        if(report.schema_version!==(request.layout?'legaia.actor-placement-layout.v1':'legaia.actor-placement-batch.v1')||JSON.stringify(report.layout??null)!==JSON.stringify(request.layout??null)||report.scene_id!==getState().scene?.id||
          !Array.isArray(report.targets)||report.targets.length!==request.actor_ids.length||
          report.targets.some((row,index)=>row.entity_id!==request.actor_ids[index])||
          typeof report.review_key!=='string'||!/^[0-9a-f]{64}$/.test(report.review_key))throw new Error('Invalid or stale group placement preview');
        if(request.layout?.kind==='snap')validateActorGridSnapReport(report);
        if(request.layout?.kind==='rotate_angle')validateActorRotationReport(report);
        preview=report;
        renderPreviewTable(report);
      }catch(error){if(error.name!=='AbortError'&&dialog.open&&token===generation)dialog.querySelector('.dialog-error').textContent=error.message;}
      finally{if(controller===active){controller=null;setBusy(false);}update();}
    };
    dialog.querySelector('[data-apply-batch]').onclick=async()=>{
      if(isBusy()||!canEdit()||!preview||context!==contextKey())return;
      const result=preview,request=payload();
      if(await api('/api/command',{type:request.layout?'layout_actor_placements':'offset_actor_placements',scene_id:result.scene_id,...request,review_key:result.review_key},{success:`Updated ${request.layout?result.changed_count:request.actor_ids.length} actor placements. Undo restores the group.`})){
        preview=null;if(dialog.open)dialog.close();
      }else{preview=null;dialog.querySelector('.dialog-error').textContent='Group placement was rejected. Preview the current placements again.';update();}
    };
    const inspect=document.createElement('button');inspect.type='button';inspect.dataset.inspectBatch='';inspect.textContent='Inspect group in scene';dialog.querySelector('[data-apply-batch]').after(inspect);
    inspect.onclick=async()=>{
      if(isBusy()||!preview||!canInspectScene()||context!==contextKey())return;
      const proposal=preview,token=++generation,binding=context;controller=new AbortController();const active=controller;setBusy(true);
      try{
        const response=await fetch(proposal.layout?'/api/actor-placement-layout-scene':'/api/actor-placement-batch-scene',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...payload(),review_key:proposal.review_key}),signal:active.signal});
        const result=await response.json();if(!response.ok||result.error)throw new Error(result.error||'Group scene inspection failed');
        if(!dialog.open||token!==generation||binding!==contextKey()||!canInspectScene())return;
        const positions=decodeActorPlacementScene(result,proposal,getState().scene_preview_source_key);
        inspection={positions,proposal};bar.querySelector('select').value='proposed';bar.hidden=false;bar.querySelector('span').textContent=`${positions.size} actor proposal · not applied · source elevation preview`;
        keepClose=true;dialog.close();onSceneInspection(inspection,'proposed');
      }catch(error){if(error.name!=='AbortError'&&dialog.open&&token===generation)dialog.querySelector('.dialog-error').textContent=error.message;}
      finally{if(controller===active){controller=null;setBusy(false);}update();}
    };
    dialog.showModal();renderActors();
  };
  dialog.addEventListener('close',()=>{if(keepClose){keepClose=false;return;}generation++;controller?.abort();preview=null;selected.clear();clearInspection();});
  bar.querySelector('select').onchange=event=>{if(inspection&&!isBusy())onSceneInspection(inspection,event.target.value);};
  bar.querySelector('[data-frame-group]').onclick=()=>{if(inspection&&!isBusy())frameGroup(inspection);};
  bar.querySelector('[data-return-group]').onclick=()=>{if(!inspection||isBusy())return;clearInspection();dialog.showModal();update();};
  bar.querySelector('[data-restore-group]').onclick=()=>{if(isBusy())return;clearInspection();preview=null;selected.clear();};
  return {synchronize(){button.disabled=isBusy()||!canEdit()||getEntities().length<2;bar.querySelectorAll('button,select').forEach(item=>item.disabled=isBusy());if((dialog.open||inspection)&&(context!==contextKey()||!canEdit())){if(dialog.open)dialog.close();else{clearInspection();preview=null;selected.clear();}}update();},restore(){clearInspection();preview=null;},
    async moveProposal(axis,amount,reviewKey){
      if(isBusy()||!canEdit()||!inspection||!inspection.proposal.delta||inspection.proposal.review_key!==reviewKey||bar.querySelector('select').value!=='proposed'||context!==contextKey()||!amount)return;
      const prior=inspection,token=++generation,binding=context;let request;
      try{request=offsetActorPlacementProposal(prior.proposal,axis,amount);}catch(error){notify(error.message,true);onSceneInspection(prior,'proposed');return;}
      const active=new AbortController();controller=active;setBusy(true);bar.querySelector('span').textContent='Validating group drag · no authored changes';
      try{
        const post=async(url,body)=>{const response=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:active.signal});const result=await response.json();if(!response.ok||result.error)throw new Error(result.error||'Group drag validation failed');return result;};
        const proposal=await post('/api/actor-placement-batch',request);
        if(proposal.scene_id!==prior.proposal.scene_id||JSON.stringify(proposal.delta)!==JSON.stringify(request.delta)||proposal.targets?.length!==request.actor_ids.length||proposal.targets.some((row,index)=>row.entity_id!==request.actor_ids[index]))throw new Error('Invalid group drag preview');
        const result=await post('/api/actor-placement-batch-scene',{...request,review_key:proposal.review_key});
        if(token!==generation||contextKey()!==binding||inspection!==prior||!canInspectScene())return;
        const positions=decodeActorPlacementScene(result,proposal,getState().scene_preview_source_key);
        preview=proposal;inspection={positions,proposal};for(const axis of ['x','z'])dialog.querySelector(`[name="${axis}"]`).value=request.delta[axis];
        renderPreviewTable(proposal);
        bar.querySelector('span').textContent=`${positions.size} actor proposal · not applied · source elevation preview`;notify('Group proposal updated. Return to group to review and Apply.');onSceneInspection(inspection,'proposed');
      }catch(error){if(error.name!=='AbortError'&&token===generation&&inspection===prior){bar.querySelector('span').textContent='Group move rejected · prior proposal restored';notify(error.message,true);onSceneInspection(prior,'proposed');}}
      finally{if(controller===active){controller=null;setBusy(false);}update();}
    }};
}
