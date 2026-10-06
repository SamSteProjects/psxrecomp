export function draftRepeatPosition(original,request,index){
  if(!Number.isSafeInteger(index)||index<1||index>request.count)throw new Error('Invalid draft copy index.');
  const grid=Object.hasOwn(request,'columns'),columns=request.columns;
  if(grid&&(!Number.isSafeInteger(columns)||columns<2||columns>request.count+1||!request.step.x||(request.count>=columns&&!request.step.z)))throw new Error('Invalid draft grid columns or spacing.');
  return {x:original.position.x+(grid?index%columns:index)*request.step.x,z:original.position.z+(grid?Math.floor(index/columns):index)*request.step.z};
}
export function draftRepeatLimits(value){
  if(!Array.isArray(value?.limitations)||value.limitations.length>32||value.limitations.some(line=>typeof line!=='string'||!line||line.length>2048))throw new Error('Draft repetition requires bounded SDK scope notes.');
  return [...value.limitations];
}
export function decodeDraftRepeatScene(response,report,base){
  const scene=response?.scene,expected=new Map(report.copies.map(row=>[row.entity_id,row.draft]));
  if(response?.schema_version!=='legaia.draft-repeat-scene.v1'||response.project_source_key!==base.source_key||response.review_key!==report.review_key||response.scene_id!==report.scene_id||scene?.scene_id!==base.scene_id||scene.schema!=='legaia.scene-preview.v1'||scene.representation!=='authored'||!Array.isArray(scene.entities)||scene.entities.length!==base.entities.length+expected.size||expected.size!==report.copies.length||scene.entities.length>512||JSON.stringify(scene.assets)!==JSON.stringify(base.assets)||JSON.stringify(scene.position_to_display)!==JSON.stringify(base.position_to_display))throw new Error('Repeated draft scene differs from its source/review');
  const owners=new Map(scene.entities.map(row=>[row.entity_id,row]));if(owners.size!==scene.entities.length)throw new Error('Repeated draft owners are ambiguous');
  for(const row of base.entities)if(JSON.stringify(owners.get(row.entity_id))!==JSON.stringify(row))throw new Error('Repeated draft proposal changed an existing instance');
  for(const [id,draft] of expected){
    if(base.entities.some(row=>row.entity_id===id))throw new Error('Repeated draft identity already exists');
    const row=owners.get(id);
    if(row?.kind!=='actor_draft'||row.donor_entity_id!==draft.donor_entity_id||row.source_actor_id!==draft.donor_entity_id||row.name!==draft.name||row.position?.x!==draft.position.x||row.position?.z!==draft.position.z||row.position?.y!==null||row.display_position?.x!==draft.position.x||row.display_position?.z!==draft.position.z||row.display_position?.y!==-(row.preview_position?.y??0))throw new Error('Repeated draft binding or placement differs from review');
    if(row.renderable&&!scene.assets.some(asset=>asset.geometry_key===row.geometry_key&&asset.asset_id===row.asset_id))throw new Error('Repeated draft geometry is missing');
  }
  return structuredClone(scene);
}

export function openDraftRepeat({entityId,getState,isBusy,canEdit,setBusy,api,canInspectScene,getScenePreview,inspectScene}){
  if(isBusy()||!canEdit())return;const original=getState().actor_drafts?.[entityId];if(!original||original.scene_id!==getState().scene.id)return;
  const dialog=document.createElement('dialog');dialog.id='draft-repeat-dialog';document.body.append(dialog);
  dialog.innerHTML='<h2>Repeat NPC draft</h2><p>Review independent copies in a line or rectangular grid at source-grid X/Z steps. Grid copies fill across columns, then rows; the original occupies the first cell. The original draft and its donor remain unchanged. Script scheduling, collision, visibility and runtime spawning are unverified; existing experimental export gates still apply.</p><form><label>Pattern<select name="pattern" aria-label="Draft copy pattern"><option value="line">Line</option><option value="grid">Rectangular grid</option></select></label><label>Grid columns, including original<input name="columns" type="number" min="2" max="129" step="1" value="2" required aria-label="Draft grid columns"></label><label>Copy name prefix<input name="name" maxlength="116" required aria-label="Draft copy name prefix"></label><label>Number of copies<input name="count" type="number" min="1" max="128" value="3" step="1" required aria-label="Draft copy count"></label><label>X step<input name="x" type="number" min="-16320" max="16320" step="64" value="64" required aria-label="Draft copy X step"></label><label>Z step<input name="z" type="number" min="-16320" max="16320" step="64" value="0" required aria-label="Draft copy Z step"></label><div class="dialog-actions"><button type="submit" data-preview>Preview draft copies</button><button type="button" data-inspect disabled>Inspect copies in scene</button><button type="button" data-apply disabled>Apply draft copies</button></div></form><p data-error class="dialog-error" role="alert"></p><div data-result></div><button type="button" data-close>Close draft copies</button>';
  dialog.querySelector('[name=name]').value=original.name.slice(0,116);let report=null,generation=0,controller=null,keepClose=false;
  const key=()=>{const s=getState();return JSON.stringify([s.project.path,s.scene.id,s.scene_preview_source_key,s.actor_drafts]);},context=key(),current=()=>context===key()&&canEdit();
  const request=()=>({entity_id:entityId,count:Number(dialog.querySelector('[name=count]').value),name:dialog.querySelector('[name=name]').value.trim(),step:{x:Number(dialog.querySelector('[name=x]').value),z:Number(dialog.querySelector('[name=z]').value)},...(dialog.querySelector('[name=pattern]').value==='grid'?{columns:Number(dialog.querySelector('[name=columns]').value)}:{})});
  function update(){if(!dialog.open)return;for(const control of dialog.querySelectorAll('input,select,button'))if(!control.matches('[data-close]'))control.disabled=isBusy()||!current();dialog.querySelector('[name=columns]').disabled=isBusy()||!current()||dialog.querySelector('[name=pattern]').value!=='grid';dialog.querySelector('[data-preview]').disabled=isBusy()||!current()||!dialog.querySelector('form').checkValidity();dialog.querySelector('[data-apply]').disabled=isBusy()||!current()||!report;dialog.querySelector('[data-inspect]').disabled=isBusy()||!current()||!report||!canInspectScene();}
  async function post(route,body,signal){const response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal}),data=await response.json();if(!response.ok||data.error)throw new Error(data.error||'Draft copy review failed');return data;}
  for(const input of dialog.querySelectorAll('input,select'))input.oninput=()=>{generation++;report=null;dialog.querySelector('[data-result]').replaceChildren();update();};
  dialog.querySelector('[data-close]').onclick=()=>dialog.close();dialog.addEventListener('close',()=>{if(keepClose){keepClose=false;return;}generation++;controller?.abort();report=null;dialog.remove();});
  dialog.querySelector('form').onsubmit=async event=>{
    event.preventDefault();if(isBusy()||!current())return;const body=request(),token=++generation,active=new AbortController();controller=active;report=null;setBusy(true);update();dialog.querySelector('[data-error]').textContent='';
    try{
      const value=await post('/api/draft-repeat',body,active.signal);if(token!==generation||!dialog.open||!current())return;
      if(value.schema_version!=='legaia.draft-repeat.v1'||value.scene_id!==getState().scene.id||value.source_entity_id!==entityId||JSON.stringify(value.source_draft)!==JSON.stringify(original)||value.request.entity_id!==entityId||value.request.count!==body.count||Object.hasOwn(value.request,'columns')!==Object.hasOwn(body,'columns')||value.request.columns!==body.columns||value.request.name!==body.name||value.request.step.x!==body.step.x||value.request.step.z!==body.step.z||value.copies?.length!==body.count||new Set(value.copies.map(row=>row.entity_id)).size!==body.count||value.copies.some((row,index)=>row.copy_index!==index+1||row.draft.scene_id!==original.scene_id||row.draft.donor_entity_id!==original.donor_entity_id||row.draft.name!==`${body.name} ${String(index+1).padStart(3,'0')}`||['x','z'].some(axis=>row.draft.position[axis]!==draftRepeatPosition(original,body,index+1)[axis]))||typeof value.review_key!=='string'||!/^[0-9a-f]{64}$/.test(value.review_key))throw new Error('Draft repetition report differs from the request');
      const limitations=draftRepeatLimits(value);report=value;const result=dialog.querySelector('[data-result]');result.replaceChildren();const table=document.createElement('table');table.innerHTML='<tr><th>Copy</th><th>Name</th><th>X</th><th>Z</th></tr>';for(const row of value.copies){const tr=document.createElement('tr');for(const cell of [row.copy_index,row.draft.name,row.draft.position.x,row.draft.position.z]){const td=document.createElement('td');td.textContent=String(cell);tr.append(td);}table.append(tr);}result.append(table);for(const line of limitations){const note=document.createElement('p');note.className='field-note';note.textContent=line;result.append(note);}
    }catch(error){if(error.name!=='AbortError'&&dialog.open&&token===generation)dialog.querySelector('[data-error]').textContent=error.message;}
    finally{if(controller===active){controller=null;setBusy(false);}update();}
  };
  dialog.querySelector('[data-inspect]').onclick=async()=>{
    if(isBusy()||!current()||!report||!canInspectScene())return;const accepted=report,base=getScenePreview(),token=++generation,active=new AbortController();controller=active;setBusy(true);update();
    try{
      const response=await post('/api/draft-repeat-scene',{...accepted.request,review_key:accepted.review_key},active.signal);
      if(token!==generation||!dialog.open||!current()||!canInspectScene()||getScenePreview()!==base)return;
      const scene=decodeDraftRepeatScene(response,accepted,base),returnToReview=()=>{if(token!==generation||!current()||report!==accepted)return false;dialog.showModal();update();return true;};
      inspectScene(scene,accepted,returnToReview,current);keepClose=true;dialog.close();
    }catch(error){if(error.name!=='AbortError'&&dialog.open&&token===generation)dialog.querySelector('[data-error]').textContent=error.message;}
    finally{if(controller===active){controller=null;setBusy(false);}update();}
  };
  dialog.querySelector('[data-apply]').onclick=async()=>{if(isBusy()||!current()||!report)return;const accepted=report;report=null;update();if(await api('/api/command',{type:'repeat_actor_draft',...accepted.request,review_key:accepted.review_key},{success:`Created ${accepted.copies.length} independent NPC drafts. Undo removes the copies.`}))dialog.close();else if(dialog.open)dialog.querySelector('[data-error]').textContent='Draft copies rejected. Preview the current drafts again.';update();};
  dialog.showModal();update();
}
