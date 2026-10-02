export function scenePlacementGroupDelta(value){
  if(!value||Object.keys(value).sort().join()!=='x,z'||['x','z'].some(axis=>!Number.isSafeInteger(value[axis])||Math.abs(value[axis])>16320||value[axis]%64))throw new Error('Placement offsets must be multiples of 64 from -16320 through 16320');
  return {x:value.x,z:value.z};
}
function placementIds(ids,scene){
  const match=/^scene:\/\/([^/]+)$/.exec(scene||'');
  if(!match||!Array.isArray(ids)||ids.length<2||ids.length>128||new Set(ids).size!==ids.length||JSON.stringify(ids)!==JSON.stringify([...ids].sort()))throw new Error('Select 2 through 128 distinct placements in the active scene');
  let actors=0,decorations=0;
  for(const id of ids){
    if(typeof id!=='string')throw new Error('Invalid placement selection');
    const actor=/^scene:\/\/([^/]+)\/actors\/man-p[12]\/\d{4}$/.exec(id);
    const decoration=/^environment:\/\/([^/]+)\/field-map\/decorations\/(\d{5})$/.exec(id);
    if(actor&&actor[1]===match[1])actors++;
    else if(decoration&&decoration[1]===match[1]&&Number(decoration[2])<=16383)decorations++;
    else throw new Error('Select imported actors and static decorations from the active scene');
  }
  if(!actors||!decorations)throw new Error('Select at least one imported actor and one static decoration');
  return ids;
}
export function decodeScenePlacementGroup(value,key,scene,ids,delta){
  placementIds(ids,scene);delta=scenePlacementGroupDelta(delta);const hash=x=>typeof x==='string'&&/^[0-9a-f]{64}$/.test(x);
  if(value?.schema_version!=='legaia.scene-placement-group-review.v1'||!hash(key)||value.project_source_key!==key||value.scene_id!==scene||!hash(value.source_sha256)||!hash(value.review_key)||value.scope!=='imported-actor-and-static-decoration-xz-only'||value.gameplay_verified!==false||typeof value.project_change!=='boolean'||JSON.stringify(value.entity_ids)!==JSON.stringify(ids)||JSON.stringify(scenePlacementGroupDelta(value.delta))!==JSON.stringify(delta)||!Array.isArray(value.targets)||value.targets.length!==ids.length||!Number.isInteger(value.affected_count)||value.affected_count<0||value.affected_count>ids.length)throw new Error('Invalid or stale scene placement group review');
  let changed=0;
  for(const [index,row] of value.targets.entries()){
    const isActor=ids[index].startsWith('scene://');
    if(!row||row.entity_id!==ids[index]||row.kind!==(isActor?'actor':'decoration')||(!isActor&&(!Number.isInteger(row.cell_index)||row.cell_index<0||row.cell_index>16383||!row.entity_id.endsWith(`/decorations/${String(row.cell_index).padStart(5,'0')}`)))||(isActor&&Object.hasOwn(row,'cell_index'))||['retail','current','proposed'].some(layer=>!row[layer]||Object.keys(row[layer]).sort().join()!=='x,z'||['x','z'].some(axis=>!Number.isSafeInteger(row[layer][axis])))||['x','z'].some(axis=>!Number.isSafeInteger(row.current[axis]+delta[axis])||row.proposed[axis]!==row.current[axis]+delta[axis]))throw new Error('Invalid reviewed scene placement');
    changed+=row.current.x!==row.proposed.x||row.current.z!==row.proposed.z;
  }
  if(changed!==value.affected_count)throw new Error('Invalid scene placement group change count');
  return structuredClone({...value,delta});
}

export function mountScenePlacementGroup({host,getState,getSelection,busy,setBusy,api,canReview,onInspection,onFrame=()=>{},onError=()=>{}}){
  const button=document.createElement('button');button.id='scene-placement-group-button';button.type='button';button.textContent='Move scene placement group…';host.append(button);
  const strip=document.createElement('div');strip.id='scene-placement-group-preview';strip.hidden=true;
  const note=document.createElement('span');note.textContent='Placement preview · proposal height held · runtime unknown · not applied';
  const returnButton=document.createElement('button');returnButton.type='button';returnButton.textContent='Return to placement review';
  const restoreButton=document.createElement('button');restoreButton.type='button';restoreButton.textContent='Restore placement preview';strip.append(note,returnButton,restoreButton);host.append(strip);
  let dialog=null,report=null,context=null,controller=null,generation=0,inspecting=false,retaining=false;
  const selection=()=>[...new Set(getSelection())].sort();
  const current=()=>{const s=getState();return !!context&&s.project?.mode==='edit'&&s.scene?.id===context.scene&&s.project_copy_source_key===context.key&&JSON.stringify(selection())===JSON.stringify(context.ids)&&canReview();};
  const delta=()=>{
    const values={};for(const axis of ['x','z']){const text=dialog.querySelector(`[name="${axis}"]`).value;if(!text.trim())throw new Error('Enter both placement offsets');values[axis]=Number(text);}return scenePlacementGroupDelta(values);
  };
  const restoreInspection=()=>{if(inspecting){inspecting=false;onInspection(null);}strip.hidden=true;note.textContent='Placement preview · proposal height held · runtime unknown · not applied';};
  const withdraw=()=>{generation++;if(controller){controller.abort();controller=null;setBusy(false);}report=null;restoreInspection();dialog?.querySelector('[data-result]')?.replaceChildren();};
  function restore(){context=null;withdraw();if(dialog){const old=dialog;dialog=null;if(old.open)old.close();old.remove();}refresh();}
  function refresh(){
    let eligible=false;try{placementIds(selection(),getState().scene?.id);eligible=getState().project?.mode==='edit'&&canReview();}catch{}
    button.disabled=busy()||!eligible;
    returnButton.disabled=busy();restoreButton.disabled=busy()&&!controller;
    if(context&&!current()){restore();return;}
    if(!dialog?.open)return;
    let valid=false;try{delta();valid=true;}catch{}
    for(const item of dialog.querySelectorAll('input,[data-review],[data-apply],[data-inspect]'))item.disabled=busy();
    dialog.querySelector('[data-review]').disabled=busy()||!valid||!current();
    dialog.querySelector('[data-apply]').disabled=busy()||!valid||!current()||!report?.project_change;
    for(const item of dialog.querySelectorAll('[data-inspect]'))item.disabled=busy()||!report||!current();
  }
  button.onclick=()=>{
    if(button.disabled||busy())return;restore();
    const s=getState();context={key:s.project_copy_source_key,scene:s.scene.id,ids:selection()};placementIds(context.ids,context.scene);
    dialog=document.createElement('dialog');dialog.id='scene-placement-group-dialog';dialog.className='project-dialog';dialog.style.width='min(800px,90vw)';dialog.style.maxHeight='90vh';dialog.style.overflowY='auto';
    dialog.innerHTML='<h2>Move scene placement group</h2><p>Review X/Z offsets for selected imported actors and static decorations. Apply records the group as one Undo step. Proposal height is held at the current preview height; runtime behavior remains unknown.</p><form><div class="dialog-actions"><label>X offset<input name="x" type="number" step="64" min="-16320" max="16320" value="0" required aria-label="Scene placement group X offset"></label><label>Z offset<input name="z" type="number" step="64" min="-16320" max="16320" value="0" required aria-label="Scene placement group Z offset"></label></div><button data-review type="submit">Review group</button></form><p data-status role="status"></p><div data-result style="max-height:40vh;overflow:auto"></div><div class="dialog-actions"><button data-inspect="proposed" type="button" disabled>Inspect proposed placements</button><button data-inspect="current" type="button" disabled>Inspect current placements</button><button data-apply type="button" disabled>Apply group</button><button data-close type="button">Cancel</button></div>';
    const activeDialog=dialog;
    const status=text=>{if(dialog===activeDialog)activeDialog.querySelector('[data-status]').textContent=text;};
    const render=()=>{
      const output=dialog.querySelector('[data-result]');output.replaceChildren();status(`${report.targets.length} placements reviewed · ${report.affected_count} placements change.`);
      const table=document.createElement('table'),head=document.createElement('tr');table.style.width='100%';table.style.fontSize='.85em';for(const text of ['Placement','Retail X/Z','Current X/Z','Proposed X/Z']){const th=document.createElement('th');th.textContent=text;th.style.padding='8px';th.style.textAlign='left';head.append(th);}table.append(head);
      for(const row of report.targets){const tr=document.createElement('tr');for(const text of [row.entity_id,...['retail','current','proposed'].map(layer=>`${row[layer].x} / ${row[layer].z}`)]){const td=document.createElement('td');td.textContent=text;td.style.padding='8px';td.style.overflowWrap='anywhere';tr.append(td);}table.append(tr);}output.append(table);
    };
    activeDialog.querySelector('form').oninput=()=>{withdraw();status('Offsets changed; review again.');refresh();};
    activeDialog.querySelector('form').onsubmit=async event=>{
      event.preventDefault();if(busy()||!current()||!activeDialog.querySelector('form').reportValidity())return;
      let requested;try{requested=delta();}catch(error){status(error.message);return;}
      withdraw();const token=++generation,binding=context,requestController=new AbortController();controller=requestController;setBusy(true);refresh();
      try{
        const response=await fetch('/api/scene-placement-group-review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({entity_id:binding.scene,entity_ids:binding.ids,delta:requested}),signal:requestController.signal});
        const value=await response.json();if(!response.ok||value.error)throw new Error(value.error||'Scene placement group review failed');
        if(dialog!==activeDialog||!activeDialog.open||generation!==token||context!==binding||!current()||JSON.stringify(delta())!==JSON.stringify(requested))return;
        report=decodeScenePlacementGroup(value,binding.key,binding.scene,binding.ids,requested);render();
      }catch(error){if(error.name!=='AbortError'&&dialog===activeDialog&&activeDialog.open&&generation===token){status(error.message);onError(error.message);}}
      finally{if(controller===requestController){controller=null;setBusy(false);}refresh();}
    };
    activeDialog.querySelector('[data-apply]').onclick=async()=>{
      if(busy()||!current()||!report?.project_change||JSON.stringify(delta())!==JSON.stringify(report.delta))return;
      const reviewed=report;
      if(await api('/api/command',{type:'apply_scene_placement_group',entity_id:context.scene,entity_ids:context.ids,delta:reviewed.delta,review_key:reviewed.review_key}))restore();
      else{withdraw();status('Scene placement group was rejected. Review current placements again.');refresh();}
    };
    for(const item of activeDialog.querySelectorAll('[data-inspect]'))item.onclick=()=>{
      if(busy()||!report||!current()||JSON.stringify(delta())!==JSON.stringify(report.delta))return;
      inspecting=true;note.textContent=item.dataset.inspect==='proposed'?'Proposed placements · height held · runtime unknown · not applied':'Current placements · runtime unknown';strip.hidden=false;retaining=true;activeDialog.close();onInspection(report,item.dataset.inspect);onFrame(report);refresh();
    };
    activeDialog.querySelector('[data-close]').onclick=()=>activeDialog.close();
    activeDialog.addEventListener('close',()=>{if(retaining){retaining=false;return;}if(dialog===activeDialog)restore();});
    document.body.append(activeDialog);activeDialog.showModal();refresh();
  };
  returnButton.onclick=()=>{if(busy()||!report||!current()||!dialog)return;restoreInspection();dialog.showModal();refresh();};
  restoreButton.onclick=()=>{if(!busy()||controller)restore();};
  return {restore,refresh};
}
