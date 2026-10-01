export async function openActorPresetReview({template,entity,getState,canEdit,isBusy,setBusy,api}){
  if(!canEdit()||isBusy())return;
  const context=()=>JSON.stringify([getState().project.path,getState().scene.id,getState().selection.entity_id,getState().scene_preview_source_key,getState().actor_templates.find(row=>row.id===template.id)]),key=context();
  const dialog=document.createElement('dialog');dialog.id='actor-preset-review';dialog.className='project-dialog';
  dialog.innerHTML='<h2>Review combined actor preset</h2><p data-summary>Verifying source and target…</p><div data-result></div><p class="dialog-error" role="alert"></p><button data-apply disabled>Apply position and appearance</button><button data-close>Close</button>';
  document.body.append(dialog);const controller=new AbortController();let report=null;
  const current=()=>dialog.open&&canEdit()&&key===context();
  dialog.querySelector('[data-close]').onclick=()=>dialog.close();dialog.addEventListener('close',()=>{controller.abort();dialog.remove();},{once:true});dialog.showModal();setBusy(true);
  try{
    const response=await fetch('/api/actor-preset-review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({template_id:template.id,entity_id:entity.id}),signal:controller.signal}),value=await response.json();
    if(!response.ok||value.error)throw new Error(value.error??'Preset review failed');if(!current())return;
    if(value.schema_version!=='legaia.actor-preset-review.v1'||value.template_id!==template.id||value.entity_id!==entity.id||!/^[0-9a-f]{64}$/.test(value.review_key)||typeof value.changed!=='boolean'||value.layers.proposed_donor!==template.components.ActorAppearance.donor_entity_id||Object.entries(template.components.Transform.position).some(([axis,position])=>value.layers.proposed_position[axis]!==position))throw new Error('Preset review differs from the selected source/target');
    report=value;dialog.querySelector('[data-summary]').textContent=`${template.name} → ${entity.name}: ${value.changed?'one Apply / Undo entry':'already matches; no command needed'}`;
    const table=document.createElement('table'),header=document.createElement('tr');for(const text of ['Property','Imported','Authored','Effective','Proposed']){const cell=document.createElement('th');cell.textContent=text;header.append(cell);}table.append(header);
    for(const axis of ['x','y','z']){const row=document.createElement('tr');for(const text of [axis.toUpperCase(),value.layers.imported_position[axis],value.layers.authored_position[axis],value.layers.effective_position[axis],value.layers.proposed_position[axis]]){const cell=document.createElement('td');cell.textContent=text??'Unknown / inherit';row.append(cell);}table.append(row);}
    const result=dialog.querySelector('[data-result]');result.append(table);const donor=document.createElement('p');donor.textContent=`Authored donor: ${value.layers.authored_donor??'inherit'} → ${value.layers.proposed_donor}`;result.append(donor);
    for(const note of [...value.build_issues,...value.limitations]){const p=document.createElement('p');p.className='field-note';p.textContent=note;result.append(p);}
    dialog.querySelector('[data-apply]').disabled=!value.changed;
  }catch(error){if(error.name!=='AbortError'&&dialog.open)dialog.querySelector('[role="alert"]').textContent=error.message;}
  finally{setBusy(false);}
  dialog.querySelector('[data-apply]')?.addEventListener('click',async()=>{if(!current()||isBusy()||!report?.changed)return;const accepted=report;report=null;dialog.querySelector('[data-apply]').disabled=true;if(await api('/api/command',{type:'apply_actor_template',template_id:template.id,entity_id:entity.id,review_key:accepted.review_key}))dialog.close();else if(dialog.open)dialog.querySelector('[role="alert"]').textContent='Preset or target changed. Close and review again.';});
}
