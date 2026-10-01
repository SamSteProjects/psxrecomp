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

export function mountActorPlacementBatch({getState,getEntities,isBusy,canEdit,setBusy,api,after,canInspectScene,onSceneInspection,frameGroup}){
  const button=document.createElement('button');button.id='actor-batch-button';button.textContent='Actor group offset';after.after(button);
  const dialog=document.createElement('dialog');dialog.id='actor-batch-dialog';document.body.append(dialog);
  const bar=document.createElement('div');bar.id='actor-batch-scene-bar';bar.hidden=true;
  bar.innerHTML='<span>Actor group proposal · not applied</span><label>Group layer<select aria-label="Actor group inspection layer"><option value="proposed">Proposed · not applied</option><option value="current">Current authored scene</option></select></label><button type="button" data-frame-group>Frame group</button><button type="button" data-return-group>Return to group</button><button type="button" data-restore-group>Restore scene</button>';
  document.getElementById('frame-selected').after(bar);
  let selected=new Set(),preview=null,context=null,generation=0,controller=null,inspection=null,keepClose=false;
  const contextKey=()=>{const s=getState();return JSON.stringify([s.project?.path,s.scene?.id,s.scene_preview_source_key]);};
  const payload=()=>({actor_ids:[...selected].sort(),delta:{x:Number(dialog.querySelector('[name="x"]').value),z:Number(dialog.querySelector('[name="z"]').value)}});
  const clearInspection=()=>{inspection=null;bar.hidden=true;onSceneInspection(null);};
  const invalidate=()=>{generation++;preview=null;clearInspection();dialog.querySelector('.batch-result')?.replaceChildren();update();};
  function update(){
    if(!dialog.open)return;
    const busy=isBusy(),valid=dialog.querySelector('form').checkValidity()&&selected.size>=2&&selected.size<=128;
    dialog.querySelectorAll('input,button').forEach(item=>{if(!item.matches('[data-close-batch]'))item.disabled=busy||!canEdit();});
    dialog.querySelector('[data-preview-batch]').disabled=busy||!canEdit()||!valid;
    const delta=payload().delta;
    dialog.querySelector('[data-apply-batch]').disabled=busy||!canEdit()||!valid||!preview||(!delta.x&&!delta.z);
    dialog.querySelector('[data-inspect-batch]').disabled=busy||!canEdit()||!preview||!canInspectScene();
    dialog.querySelector('.batch-count').textContent=`${selected.size} actors selected · one Undo step`;
  }
  function renderActors(){
    const query=dialog.querySelector('[name="search"]').value.toLowerCase(),list=dialog.querySelector('.batch-actors');list.replaceChildren();
    for(const entity of getEntities().filter(e=>`${e.name} ${e.id}`.toLowerCase().includes(query))){
      const label=document.createElement('label'),check=document.createElement('input'),name=document.createElement('span');
      check.type='checkbox';check.value=entity.id;check.checked=selected.has(entity.id);check.setAttribute('aria-label',`Include ${entity.name??entity.id}`);
      check.onchange=()=>{if(check.checked)selected.add(entity.id);else selected.delete(entity.id);invalidate();};
      name.textContent=entity.name??entity.id;label.title=entity.id;label.append(check,name);list.append(label);
    }
    update();
  }
  button.onclick=()=>{
    if(isBusy()||!canEdit())return;
    clearInspection();selected=new Set();preview=null;context=contextKey();generation++;
    dialog.innerHTML='<div class="dialog-heading"><h2>Offset actor placements</h2><button type="button" data-close-batch aria-label="Close actor group">×</button></div><p>Select imported actors in this scene. Offset their effective X/Z placements together. Proposed coordinates must fit the exact retail 64-unit grid, from 64 through 16384. Source height, facing, scripts and scheduling stay unchanged.</p><form><label>Find actors<input name="search" type="search" aria-label="Find group actors"></label><div class="batch-actors"></div><p class="batch-count" role="status"></p><div class="dialog-actions"><label>X offset<input name="x" type="number" step="64" min="-16320" max="16320" value="0" required></label><label>Z offset<input name="z" type="number" step="64" min="-16320" max="16320" value="0" required></label></div><div class="dialog-actions"><button type="submit" data-preview-batch>Preview group offset</button><button type="button" data-apply-batch disabled>Apply group offset</button></div><p class="dialog-error" role="alert"></p><div class="batch-result"></div></form>';
    dialog.querySelector('[data-close-batch]').onclick=()=>dialog.close();
    dialog.querySelector('[name="search"]').oninput=renderActors;
    for(const input of dialog.querySelectorAll('[name="x"],[name="z"]'))input.oninput=invalidate;
    dialog.querySelector('form').onsubmit=async event=>{
      event.preventDefault();if(dialog.querySelector('[data-preview-batch]').disabled)return;
      const request=payload(),binding=JSON.stringify(request),token=++generation,requestContext=context;
      controller=new AbortController();const active=controller;preview=null;setBusy(true);dialog.querySelector('.dialog-error').textContent='';dialog.querySelector('.batch-result').replaceChildren();
      try{
        const response=await fetch('/api/actor-placement-batch',{method:'POST',headers:{'Content-Type':'application/json'},body:binding,signal:active.signal});
        const report=await response.json();if(!response.ok||report.error)throw new Error(report.error||'Group placement preview failed');
        if(!dialog.open||token!==generation||requestContext!==contextKey()||binding!==JSON.stringify(payload()))return;
        if(report.schema_version!=='legaia.actor-placement-batch.v1'||report.scene_id!==getState().scene?.id||
          !Array.isArray(report.targets)||report.targets.length!==request.actor_ids.length||
          report.targets.some((row,index)=>row.entity_id!==request.actor_ids[index])||
          typeof report.review_key!=='string'||!/^[0-9a-f]{64}$/.test(report.review_key))throw new Error('Invalid or stale group placement preview');
        preview=report;
        const table=document.createElement('table'),head=document.createElement('tr');
        for(const text of ['Actor','Retail X/Z','Authored X/Z','Effective X/Z','Proposed X/Z']){const th=document.createElement('th');th.textContent=text;head.append(th);}table.append(head);
        for(const row of report.targets){const tr=document.createElement('tr');for(const value of [getEntities().find(e=>e.id===row.entity_id)?.name??row.entity_id,...['retail','authored','effective','proposed'].map(layer=>`${row[layer]?.x??'inherit'} / ${row[layer]?.z??'inherit'}`)]){const td=document.createElement('td');td.textContent=value;tr.append(td);}table.append(tr);}
        dialog.querySelector('.batch-result').append(table);
      }catch(error){if(error.name!=='AbortError'&&dialog.open&&token===generation)dialog.querySelector('.dialog-error').textContent=error.message;}
      finally{if(controller===active){controller=null;setBusy(false);}update();}
    };
    dialog.querySelector('[data-apply-batch]').onclick=async()=>{
      if(isBusy()||!canEdit()||!preview||context!==contextKey())return;
      const result=preview,request=payload();
      if(await api('/api/command',{type:'offset_actor_placements',scene_id:result.scene_id,...request,review_key:result.review_key},{success:`Offset ${request.actor_ids.length} actors. Undo restores the group.`})){
        preview=null;if(dialog.open)dialog.close();
      }else{preview=null;dialog.querySelector('.dialog-error').textContent='Group offset was rejected. Preview the current placements again.';update();}
    };
    const inspect=document.createElement('button');inspect.type='button';inspect.dataset.inspectBatch='';inspect.textContent='Inspect group in scene';dialog.querySelector('[data-apply-batch]').after(inspect);
    inspect.onclick=async()=>{
      if(isBusy()||!preview||!canInspectScene()||context!==contextKey())return;
      const proposal=preview,token=++generation,binding=context;controller=new AbortController();const active=controller;setBusy(true);
      try{
        const response=await fetch('/api/actor-placement-batch-scene',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...payload(),review_key:proposal.review_key}),signal:active.signal});
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
  return {synchronize(){button.disabled=isBusy()||!canEdit()||getEntities().length<2;bar.querySelectorAll('button,select').forEach(item=>item.disabled=isBusy());if((dialog.open||inspection)&&(context!==contextKey()||!canEdit())){if(dialog.open)dialog.close();else{clearInspection();preview=null;selected.clear();}}update();},restore(){clearInspection();preview=null;}};
}
