/** Group placement authoring belongs to the project command service. */
export function mountActorPlacementBatch({getState,getEntities,isBusy,canEdit,setBusy,api,notify,after}){
  const button=document.createElement('button');button.id='actor-batch-button';button.textContent='Actor group offset';after.after(button);
  const dialog=document.createElement('dialog');dialog.id='actor-batch-dialog';document.body.append(dialog);
  let selected=new Set(),preview=null,context=null,generation=0,controller=null;
  const contextKey=()=>{const s=getState();return JSON.stringify([s.project?.path,s.scene?.id,s.scene_preview_source_key]);};
  const payload=()=>({actor_ids:[...selected].sort(),delta:{x:Number(dialog.querySelector('[name="x"]').value),z:Number(dialog.querySelector('[name="z"]').value)}});
  const invalidate=()=>{generation++;preview=null;dialog.querySelector('.batch-result')?.replaceChildren();update();};
  function update(){
    if(!dialog.open)return;
    const busy=isBusy(),valid=dialog.querySelector('form').checkValidity()&&selected.size>=2&&selected.size<=128;
    dialog.querySelectorAll('input,button').forEach(item=>{if(!item.matches('[data-close-batch]'))item.disabled=busy||!canEdit();});
    dialog.querySelector('[data-preview-batch]').disabled=busy||!canEdit()||!valid;
    const delta=payload().delta;
    dialog.querySelector('[data-apply-batch]').disabled=busy||!canEdit()||!valid||!preview||(!delta.x&&!delta.z);
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
    selected=new Set();preview=null;context=contextKey();generation++;
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
    dialog.showModal();renderActors();
  };
  dialog.addEventListener('close',()=>{generation++;controller?.abort();preview=null;selected.clear();});
  return {synchronize(){button.disabled=isBusy()||!canEdit()||getEntities().length<2;if(dialog.open&&context!==contextKey())dialog.close();update();}};
}
